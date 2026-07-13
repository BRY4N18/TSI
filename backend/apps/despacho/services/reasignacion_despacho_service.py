from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.repositories.accidentes.nota_accidente_repository import NotaAccidenteRepository
from apps.despacho.services.consulta_candidatas_service import ConsultaCandidatasService

if TYPE_CHECKING:
    from apps.despacho.services.asignacion_inteligente_service import AsignacionInteligenteService


class ReasignacionDespachoService:
    def __init__(
        self,
        asignacion: AsignacionInteligenteService | None = None,
        candidatas: ConsultaCandidatasService | None = None,
        nota_repo: NotaAccidenteRepository | None = None,
    ):
        self._asignacion = asignacion
        self.candidatas = candidatas or ConsultaCandidatasService()
        self.notas = nota_repo or NotaAccidenteRepository()

    @property
    def asignacion(self) -> AsignacionInteligenteService:
        if self._asignacion is None:
            from apps.despacho.services.asignacion_inteligente_service import (
                AsignacionInteligenteService,
            )

            self._asignacion = AsignacionInteligenteService()
        return self._asignacion

    def ejecutar(
        self,
        *,
        idaccidente: str,
        idusuario: int = 0,
        incluir_vecinos: bool = False,
        sincrono: bool = True,
    ) -> dict[str, Any]:
        ranked = self.candidatas.listar_puntuadas(
            idaccidente, incluir_vecinos=incluir_vecinos
        )
        if not ranked:
            if incluir_vecinos:
                self._alerta_critica(idaccidente, idusuario)
                return {"reasignacion_iniciada": False, "alerta": True}
            return self.ejecutar(
                idaccidente=idaccidente,
                idusuario=idusuario,
                incluir_vecinos=True,
                sincrono=sincrono,
            )
        result = self.asignacion.ejecutar(
            idaccidente=idaccidente,
            idusuario=idusuario,
            incluir_vecinos=incluir_vecinos,
            idunidademergencia=ranked[0]["idunidademergencia"],
        )
        return {"reasignacion_iniciada": result is not None, "despacho": result}

    def _alerta_critica(self, idaccidente: str, idusuario: int) -> None:
        self.notas.create_alerta(
            idaccidente=idaccidente,
            idusuario=idusuario,
            nota="Sin unidades disponibles. Requiere intervención manual.",
        )
