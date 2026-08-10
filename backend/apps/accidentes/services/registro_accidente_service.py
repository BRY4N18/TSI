"""CU-O56 registro de accidente (Fase 1 — solo datos a distancia)."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_REPORTADO
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.validacion_accidente_service import (
    ValidacionAccidenteService,
)
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)


class RegistroAccidenteService:
    def __init__(
        self,
        validacion: ValidacionAccidenteService | None = None,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.validacion = validacion or ValidacionAccidenteService()
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def registrar(
        self,
        data: dict[str, Any],
        *,
        idusuario: int,
        forzar_advertencias: bool = False,
    ) -> dict[str, Any]:
        validation = self.validacion.validate_registro(data)
        if validation.is_blocked:
            error = validation.blocking_errors[0]
            raise BlockingValidationError(error["code"], error["detail"])

        if validation.has_advertencias and not forzar_advertencias:
            parent = self.validacion.suggest_parent_id(validation.duplicate_candidates)
            raise DuplicateConflictError(
                validation.advertencias,
                validation.duplicate_candidates,
                parent,
            )

        idaccidente = self.accidente_repo.generate_id()
        payload = {
            "idaccidente": idaccidente,
            "latitudinicio": data["latitudinicio"],
            "longitudinicio": data["longitudinicio"],
            "fechahoraaccidente": data["fechahoraaccidente"],
            "idseveridad": data["idseveridad"],
            "descripcion": data["descripcion"],
            "idcalle": data["idcalle"],
            "idusuario": idusuario,
            "codigopostal": data.get("codigopostal"),
            "horainicio": data.get("horainicio"),
            "idtiporeportado": data.get("idtiporeportado"),
            "idreferenciaestacion": data.get("idreferenciaestacion"),
            "numvehiculos": data.get("numvehiculos"),
            "numvictimas": data.get("numvictimas"),
            "numheridos": data.get("numheridos"),
            "numfallecidos": data.get("numfallecidos"),
            "distanciamillas": data.get("distanciamillas"),
            "duracionminutos": data.get("duracionminutos"),
            "activo": True,
        }
        record = self.accidente_repo.create(payload)
        self.estado_repo.append_estado(idaccidente=idaccidente, estado=ESTADO_BORRADOR, idusuario=idusuario)

        estado_final = ESTADO_BORRADOR
        if not validation.has_advertencias:
            self.estado_repo.append_estado(
                idaccidente=idaccidente, estado=ESTADO_REPORTADO, idusuario=idusuario
            )
            estado_final = ESTADO_REPORTADO

        # Clima / elementos físicos / conductores / implicados: solo Técnico en sitio
        # (evidencia-unidad CU-O75/CU-O76). No se escriben en CU-O56.

        # RN-REG-004/RNF-REG-004: el registro retrospectivo (>24h) exige
        # justificacionRetrospectiva y debe quedar auditado — antes se validaba
        # pero nunca se pasaba al log, perdiéndose tras cumplir su único uso.
        audit_extra: dict[str, Any] = {}
        if data.get("registroRetrospectivo"):
            audit_extra["registroRetrospectivo"] = True
            audit_extra["justificacionRetrospectiva"] = data.get("justificacionRetrospectiva")
        self.audit.log_action(
            action="crear",
            user_id=idusuario,
            idaccidente=idaccidente,
            extra=audit_extra or None,
        )

        return {
            "message": "Accidente registrado exitosamente",
            "idaccidente": idaccidente,
            "estado": estado_final,
            "advertencias": validation.advertencias,
            "fechahoramodificado": record["fecha_actualizacion"],
        }


class DuplicateConflictError(Exception):
    def __init__(self, advertencias, candidates, parent_suggested):
        super().__init__("Posible duplicado")
        self.advertencias = advertencias
        self.candidates = candidates
        self.parent_suggested = parent_suggested


# RF-REG-003 / sección 8: campos_obligatorios y gps_invalido -> 400; retrospectivo_requerido -> 422.
BAD_REQUEST_CODES = {"campos_obligatorios", "gps_invalido", "fecha_futura"}


class BlockingValidationError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail

    @property
    def status_code(self) -> int:
        return 400 if self.code in BAD_REQUEST_CODES else 422
