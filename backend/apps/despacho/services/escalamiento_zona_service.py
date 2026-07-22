"""CU-O34 — escalamiento a condados vecinos."""

from __future__ import annotations

from typing import Any

from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.nota_accidente_repository import (
    NotaAccidenteRepository,
)


class EscalamientoZonaService:
    def __init__(
        self,
        asignacion: AsignacionInteligenteService | None = None,
        nota_repo: NotaAccidenteRepository | None = None,
        accidente_repo: AccidenteRepository | None = None,
    ):
        self.asignacion = asignacion or AsignacionInteligenteService()
        self.notas = nota_repo or NotaAccidenteRepository()
        self.accidentes = accidente_repo or AccidenteRepository()

    def escalar(self, *, idaccidente: str, idusuario: int) -> dict[str, Any]:
        if not self.accidentes.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        from apps.despacho.services.consulta_candidatas_service import (
            ConsultaCandidatasService,
        )

        candidatas = ConsultaCandidatasService().listar_puntuadas(
            idaccidente, incluir_vecinos=True
        )
        if not candidatas:
            self.notas.create_escalamiento(
                idaccidente=idaccidente,
                idusuario=idusuario,
                nota="Escalamiento a zona vecina sin unidades disponibles.",
            )
            return {
                "message": "Sin unidades en condados vecinos",
                "idaccidente": idaccidente,
                "alerta_registrada": True,
                "nota": "Escalamiento registrado",
            }
        result = self.asignacion.ejecutar(
            idaccidente=idaccidente,
            idusuario=idusuario,
            idorigendespacho="Escalado_zona",
            incluir_vecinos=True,
            idunidademergencia=candidatas[0]["idunidademergencia"],
        )
        if result is None:
            self.notas.create_escalamiento(
                idaccidente=idaccidente,
                idusuario=idusuario,
                nota="Escalamiento sin despacho creado.",
            )
            return {
                "message": "Sin unidades en condados vecinos",
                "idaccidente": idaccidente,
                "alerta_registrada": True,
            }
        return {
            "message": "Despacho escalado a zona vecina",
            **result,
            "origen": "Escalado_zona",
            "estado_caso": "BUSCANDO_UNIDAD",
        }
