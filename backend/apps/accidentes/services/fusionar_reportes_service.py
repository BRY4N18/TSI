"""CU-O57 fusionar reportes."""

from __future__ import annotations

from apps.accidentes.domain_constants import (
    ESTADO_BORRADOR,
    ESTADO_CERRADO,
    ESTADO_DESCARTADO,
    ESTADO_FUSIONADO,
    ESTADO_REPORTADO,
)
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)


class FusionarReportesService:
    # El **duplicado** es un reporte que muere antes de cualquier despacho
    # (SRS §3.6.1: este módulo cubre "todos los caminos que terminan antes de
    # que exista cualquier despacho").
    ALLOWED_DUPLICADO = {ESTADO_BORRADOR, ESTADO_REPORTADO}
    # El **padre**, en cambio, "continúa su flujo normal sin alteración": puede
    # estar ya buscando unidad, asignado o en atención. Exigirle BORRADOR o
    # REPORTADO impedía fusionar en el caso normal —el duplicado llega cuando el
    # caso real ya se está despachando—, que es justo cuando hace falta.
    PROHIBIDOS_PADRE = {ESTADO_CERRADO, ESTADO_DESCARTADO, ESTADO_FUSIONADO}

    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def fusionar(
        self,
        *,
        idaccidente_duplicado: str,
        idaccidente_principal: str,
        idusuario: int,
        confirmacion: bool,
    ) -> dict:
        if not confirmacion:
            raise ValueError("Confirmación requerida")
        if idaccidente_duplicado == idaccidente_principal:
            # Sin esta guarda, un caso podía quedar marcado como duplicado de sí
            # mismo: apuntándose con `idaccidenteorigen`, desactivado y en
            # FUSIONADO. El accidente real desaparecía del flujo.
            raise ValueError("Un caso no puede fusionarse consigo mismo")

        estado_duplicado = self.estado_repo.get_current_estado(idaccidente_duplicado)
        if estado_duplicado not in self.ALLOWED_DUPLICADO:
            raise ConflictError(
                "Solo puede fusionarse un reporte que aún no tiene despacho "
                f"(estado actual: {estado_duplicado})"
            )
        estado_principal = self.estado_repo.get_current_estado(idaccidente_principal)
        if estado_principal in self.PROHIBIDOS_PADRE or estado_principal is None:
            raise ConflictError(
                f"El caso padre no admite fusiones en estado {estado_principal}"
            )

        self.accidente_repo.update(
            idaccidente_duplicado,
            {"idaccidenteorigen": idaccidente_principal, "activo": False},
        )
        self.estado_repo.append_estado(
            idaccidente=idaccidente_duplicado,
            estado=ESTADO_FUSIONADO,
            idusuario=idusuario,
        )
        self.audit.log_action(
            action="fusionar",
            user_id=idusuario,
            idaccidente=idaccidente_duplicado,
            extra={"idaccidente_principal": idaccidente_principal},
        )
        return {
            "message": "Reportes fusionados exitosamente",
            "idaccidente_duplicado": idaccidente_duplicado,
            "idaccidente_principal": idaccidente_principal,
            "estado_duplicado": ESTADO_FUSIONADO,
        }
