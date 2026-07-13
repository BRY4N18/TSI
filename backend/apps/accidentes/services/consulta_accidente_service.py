"""RF-REG-005 consulta y edición."""

from __future__ import annotations

from typing import Any

from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.accidentes.ubicacion_catalogo_repository import UbicacionCatalogoRepository


class ConsultaAccidenteService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
        catalogo_repo: UbicacionCatalogoRepository | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()
        self.catalogo_repo = catalogo_repo or UbicacionCatalogoRepository()

    def listar(self, *, estado: str | None = None, **filters) -> list[dict[str, Any]]:
        rows = self.accidente_repo.list_activos(**filters)
        for row in rows:
            row["estado_actual"] = self.estado_repo.get_current_estado(row["idaccidente"])
        if estado is not None:
            rows = [r for r in rows if r["estado_actual"] == estado]

        ubicaciones = self.catalogo_repo.resolver_calles([r.get("idcalle") for r in rows])
        for row in rows:
            row["ubicacion"] = ubicaciones.get(row.get("idcalle"))
        return rows

    def detalle(self, idaccidente: str) -> dict[str, Any] | None:
        row = self.accidente_repo.find_by_id(idaccidente)
        if not row:
            return None
        row["estado_actual"] = self.estado_repo.get_current_estado(idaccidente)
        row["historial_estados"] = self.estado_repo.get_history(idaccidente)
        ubicaciones = self.catalogo_repo.resolver_calles([row.get("idcalle")])
        row["ubicacion"] = {"idcalle": row.get("idcalle"), **(ubicaciones.get(row.get("idcalle")) or {})}
        return row

    def actualizar(self, idaccidente: str, fields: dict[str, Any], *, idusuario: int) -> dict:
        current = self.accidente_repo.find_by_id(idaccidente)
        if not current:
            raise LookupError("Accidente no encontrado")

        critical = {"latitudinicio", "longitudinicio", "fechahoraaccidente", "idseveridad"}
        if critical.intersection(fields.keys()) and not fields.get("confirmacion_campos_criticos"):
            raise ValueError("Confirmación requerida para campos críticos")

        for metric in ("numheridos", "numfallecidos", "numvehiculos", "numvictimas"):
            if metric in fields and fields[metric] is not None:
                old = current.get(metric) or 0
                if fields[metric] < old:
                    raise ValueError(f"{metric} solo puede incrementarse")

        updated = self.accidente_repo.update(idaccidente, {k: v for k, v in fields.items() if k != "confirmacion_campos_criticos"})
        modified = list(fields.keys())
        self.audit.log_action(
            action="editar",
            user_id=idusuario,
            idaccidente=idaccidente,
            fields_modified=modified,
            old_values={k: current.get(k) for k in modified},
            new_values={k: updated.get(k) for k in modified},
        )
        return {
            "message": "Accidente actualizado",
            "idaccidente": idaccidente,
            "campos_modificados": modified,
        }
