"""CU-O44 — forzar retiro unitario desde central."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_EN_ATENCION
from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.retiro_despacho_service import RetiroDespachoService
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.despacho.despacho_repository import DespachoRepository


class ForzarRetiroService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        retiro: RetiroDespachoService | None = None,
        cierre: CerrarCasoService | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.retiro = retiro or RetiroDespachoService()
        self.cierre = cierre or CerrarCasoService()

    def forzar(self, *, iddespacho: int, idusuario: int) -> dict[str, Any]:
        despacho = self.despachos.find_by_id(iddespacho)
        if not despacho:
            raise LookupError("Despacho no encontrado")
        result = self.retiro.retirar(iddespacho=iddespacho, idusuario=idusuario)
        idaccidente = despacho["idaccidente"]
        caso_cerrado = False
        estado_caso = self.estado.get_current_estado(idaccidente) or ESTADO_EN_ATENCION
        if self.retiro.todos_retirados_o_abortados(idaccidente):
            cierre = self.cierre.cerrar(
                idaccidente=idaccidente,
                idusuario=idusuario,
                payload={"resultado_atencion": "Cierre automático tras retiro forzado"},
            )
            caso_cerrado = True
            estado_caso = cierre["estado_caso"]
        return {
            "iddespacho": iddespacho,
            "fechahoraretiro": result["fechahoraretiro"],
            "idusuario_operador": str(idusuario),
            "caso_cerrado": caso_cerrado,
            "estado_caso": estado_caso,
        }
