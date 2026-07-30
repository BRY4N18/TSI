"""RF-EVI-009 — conductores y vehículos involucrados."""

from __future__ import annotations

from typing import Any

from core.audit.evidencia_service import AuditEvidenciaService
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository
from core.repositories.evidencia.catalogo_enriquecimiento_repository import (
    CatalogoEnriquecimientoRepository,
)
from core.repositories.evidencia.conductor_accidente_repository import (
    ConductorAccidenteRepository,
)
from core.repositories.evidencia.conductor_repository import ConductorRepository
from core.repositories.evidencia.vehiculo_repository import VehiculoRepository


class EnriquecimientoConductorService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        conductor_repo: ConductorRepository | None = None,
        vehiculo_repo: VehiculoRepository | None = None,
        vinculo_repo: ConductorAccidenteRepository | None = None,
        catalogo_repo: CatalogoEnriquecimientoRepository | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.conductor_repo = conductor_repo or ConductorRepository()
        self.vehiculo_repo = vehiculo_repo or VehiculoRepository()
        self.vinculo_repo = vinculo_repo or ConductorAccidenteRepository()
        self.catalogo_repo = catalogo_repo or CatalogoEnriquecimientoRepository()
        self.audit = audit or AuditEvidenciaService()

    def _conductor_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "identificacion": row.get("identificacion"),
            "nombres": row.get("nombres"),
            "apellidos": row.get("apellidos"),
            "genero": row.get("genero"),
            "tipolicencia": row.get("tipolicencia"),
            "estadolicencia": row.get("estadolicencia"),
            "ciudadresidencia": row.get("ciudadresidencia"),
            "aniosexperiencia": row.get("aniosexperiencia"),
        }

    def _vehiculo_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "idvehiculo": row.get("idvehiculo"),
            "tipovehiculo": row.get("tipovehiculo"),
            "modelovehiculo": row.get("modelovehiculo"),
            "categoriausovehiculo": row.get("categoriausovehiculo"),
            "mercanciapeligrosa": row.get("mercanciapeligrosa"),
            "ejes": row.get("ejes"),
        }

    def _enrich_vinculo(self, vinculo: dict[str, Any]) -> dict[str, Any]:
        conductor = self.conductor_repo.find_by_id(int(vinculo["idconductor"])) or {}
        vehiculo = self.vehiculo_repo.find_by_id(int(vinculo["idvehiculo"])) or {}
        return {
            **vinculo,
            "conductor": self._conductor_payload(conductor),
            "vehiculo": self._vehiculo_payload(vehiculo),
        }

    def listar(self, idaccidente: str, *, idusuario: int | None = None) -> list[dict[str, Any]]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        items = [
            self._enrich_vinculo(r)
            for r in self.vinculo_repo.list_activos_by_accidente(idaccidente)
        ]
        if idusuario is not None:
            self.audit.log_consultar_conductores_accidente(
                user_id=idusuario, idaccidente=idaccidente, count=len(items)
            )
        return items

    def registrar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        conductor: dict[str, Any],
        idestadoconductor: int,
        vehiculo: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        if not self.catalogo_repo.find_estado_conductor(idestadoconductor):
            raise ValueError("idestadoconductor inválido")

        identificacion = str(conductor.get("identificacion") or "").strip()
        if not identificacion or not conductor.get("nombres") or not conductor.get("apellidos"):
            raise ValueError("conductor.identificacion, nombres y apellidos son requeridos")
        if not vehiculo.get("tipovehiculo"):
            raise ValueError("vehiculo.tipovehiculo es requerido")

        # RN-EVI-022 — tope = Fact_Accidente.numvehiculos
        accidente = self.accidente_repo.find_by_id(idaccidente)
        assert accidente is not None
        numvehiculos = accidente.get("numvehiculos")
        try:
            tope = int(numvehiculos) if numvehiculos is not None else 0
        except (TypeError, ValueError):
            tope = 0
        if tope < 1:
            raise ValueError(
                "El caso no tiene numvehiculos definido; actualice el accidente antes de registrar"
            )
        activos = self.vinculo_repo.list_activos_by_accidente(idaccidente)
        if len(activos) >= tope:
            raise ValueError(
                f"No se pueden registrar más de {tope} conductor(es)/vehículo(s) "
                f"(numvehiculos del caso)"
            )

        # RN-EVI-019 — reutilizar por identificación
        existing = self.conductor_repo.find_by_identificacion(identificacion)
        if existing:
            conductor_row = existing
        else:
            conductor_row = self.conductor_repo.create(
                {
                    "identificacion": identificacion,
                    "nombres": conductor["nombres"],
                    "apellidos": conductor["apellidos"],
                    "genero": conductor.get("genero"),
                    "tipolicencia": conductor.get("tipolicencia"),
                    "estadolicencia": conductor.get("estadolicencia"),
                    "ciudadresidencia": conductor.get("ciudadresidencia"),
                    "aniosexperiencia": conductor.get("aniosexperiencia"),
                }
            )

        idvehiculo = vehiculo.get("idvehiculo")
        if idvehiculo:
            vehiculo_row = self.vehiculo_repo.find_by_id(int(idvehiculo))
            if not vehiculo_row:
                raise ValueError("idvehiculo inválido")
        else:
            vehiculo_row = self.vehiculo_repo.create(
                {
                    "tipovehiculo": vehiculo["tipovehiculo"],
                    "modelovehiculo": vehiculo.get("modelovehiculo"),
                    "categoriausovehiculo": vehiculo.get("categoriausovehiculo"),
                    "mercanciapeligrosa": vehiculo.get("mercanciapeligrosa"),
                    "ejes": vehiculo.get("ejes"),
                }
            )

        vinculo = self.vinculo_repo.create(
            idaccidente=idaccidente,
            idconductor=int(conductor_row["idconductor"]),
            idestadoconductor=idestadoconductor,
            idvehiculo=int(vehiculo_row["idvehiculo"]),
            idusuario=idusuario,
        )
        self.audit.log_registrar_conductor_accidente(
            user_id=idusuario,
            idaccidente=idaccidente,
            idconductoraccidente=vinculo["idconductoraccidente"],
        )
        return self._enrich_vinculo(vinculo)

    def desactivar(
        self, *, idaccidente: str, idconductoraccidente: int, idusuario: int
    ) -> dict[str, Any]:
        current = self.vinculo_repo.find_by_id(idconductoraccidente)
        if not current or current.get("idaccidente") != idaccidente:
            raise LookupError("Vínculo conductor no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        record = self.vinculo_repo.soft_delete(
            idconductoraccidente=idconductoraccidente, idusuario=idusuario
        )
        assert record is not None
        self.audit.log_desactivar_conductor_accidente(
            user_id=idusuario,
            idaccidente=idaccidente,
            idconductoraccidente=idconductoraccidente,
        )
        return self._enrich_vinculo(record)
