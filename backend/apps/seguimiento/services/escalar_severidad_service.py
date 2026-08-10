"""CU-O73 — escalar severidad en sitio; puede disparar CU-O66 (despacho múltiple).

Movido desde `apps/accidentes` (corrección 2026-08-08): el SRS §3.6.4 narra esta
acción dentro de Seguimiento y Cierre de Casos ("ya en el lugar, la Unidad
puede escalar la severidad..."), no en Registro de Accidente.
"""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_ASIGNADO, ESTADO_EN_ATENCION
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.despacho_read_repository import DespachoReadRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.accidentes.nota_accidente_repository import (
    NotaAccidenteRepository,
)
from core.repositories.seguimiento.historial_severidad_repository import (
    HistorialSeveridadRepository,
)


class EscalarSeveridadService:
    ALLOWED_ESTADOS = {ESTADO_ASIGNADO, ESTADO_EN_ATENCION}

    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoReadRepository | None = None,
        nota_repo: NotaAccidenteRepository | None = None,
        historial_severidad: HistorialSeveridadRepository | None = None,
        audit: AuditAccidenteService | None = None,
        coordinacion_factory=None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.despacho_repo = despacho_repo or DespachoReadRepository()
        self.nota_repo = nota_repo or NotaAccidenteRepository()
        self.historial_severidad = historial_severidad or HistorialSeveridadRepository()
        self.audit = audit or AuditAccidenteService()
        self._coordinacion_factory = coordinacion_factory

    def _coordinacion(self):
        if self._coordinacion_factory:
            return self._coordinacion_factory()
        from apps.despacho.services.coordinacion_multiple_service import (
            CoordinacionMultipleService,
        )

        return CoordinacionMultipleService()

    def escalar(self, *, idaccidente: str, data: dict[str, Any], idusuario: int) -> dict:
        estado = self.estado_repo.get_current_estado(idaccidente)
        if estado not in self.ALLOWED_ESTADOS:
            raise ConflictError("Estado no permite escalamiento")
        if not self.despacho_repo.has_active_confirmed(idaccidente):
            raise ConflictError("Sin despacho activo confirmado")

        current = self.accidente_repo.find_by_id(idaccidente)
        if not current:
            raise LookupError("Accidente no encontrado")

        idseveridad_anterior = current.get("idseveridad")
        updates: dict[str, Any] = {"idseveridad": data["idseveridad"]}
        for field in ("numheridos", "numfallecidos"):
            if field in data and data[field] is not None:
                old = current.get(field) or 0
                if data[field] < old:
                    raise ValueError(f"{field} solo puede incrementarse")
                updates[field] = data[field]
        if data.get("descripcion"):
            updates["descripcion"] = data["descripcion"]

        self.accidente_repo.update(idaccidente, updates)
        self.nota_repo.create_escalamiento(
            idaccidente=idaccidente,
            idusuario=idusuario,
            nota=data["nota"],
        )
        # RF-O73.2: conservar la severidad inicial junto a la escalada, sin
        # sobrescribirla — Fact_Accidente.idseveridad solo guarda el valor
        # vigente; el histórico completo vive aquí.
        if idseveridad_anterior is not None and idseveridad_anterior != data["idseveridad"]:
            self.historial_severidad.registrar_escalada(
                idaccidente=idaccidente,
                idseveridadanterior=int(idseveridad_anterior),
                idseveridadnueva=int(data["idseveridad"]),
                idusuario=idusuario,
                motivo=data.get("nota"),
            )
        self.audit.log_action(action="escalar", user_id=idusuario, idaccidente=idaccidente)

        result: dict[str, Any] = {
            "message": "Severidad escalada exitosamente",
            "idaccidente": idaccidente,
            "idseveridad": data["idseveridad"],
            "estado": estado,
            "despacho_adicional": None,
        }

        # CU-O73 → puede disparar CU-O66 si se indica unidad adicional
        idunidad = data.get("idunidademergencia_adicional")
        if idunidad is not None:
            try:
                coord = self._coordinacion().coordinar(
                    idaccidente=idaccidente,
                    idunidademergencia=int(idunidad),
                    idusuario=idusuario,
                )
                result["despacho_adicional"] = coord
                result["message"] = (
                    "Severidad escalada y despacho múltiple coordinado (CU-O66)"
                )
            except ValueError as exc:
                raise ValueError(f"Escalamiento OK pero CU-O66 falló: {exc}") from exc

        return result
