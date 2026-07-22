"""CU-O42 — cancelación falsa alarma (solo motivo + tiempos SLA)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.accidentes.domain_constants import ESTADO_CERRADO
from apps.seguimiento.services.retiro_despacho_service import RetiroDespachoService
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.accidentes.nota_accidente_repository import (
    NotaAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_ABORTADO,
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)


class CancelarCasoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        nota_repo: NotaAccidenteRepository | None = None,
        retiro: RetiroDespachoService | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.notas = nota_repo or NotaAccidenteRepository()
        self.retiro = retiro or RetiroDespachoService()

    def cancelar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        motivo: str,
    ) -> dict[str, Any]:
        if not motivo or not motivo.strip():
            raise ValueError("Motivo requerido")
        acc = self.accidentes.find_by_id(idaccidente)
        if not acc:
            raise LookupError("Accidente no encontrado")
        if self.estado.get_current_estado(idaccidente) == ESTADO_CERRADO:
            raise ValueError("Caso ya cerrado")

        auto_retirados: list[int] = []
        for d in self.despachos.list_by_accidente(idaccidente):
            idd = int(d["iddespacho"])
            est, _ = self.historial.get_current_estado(idd)
            if est not in (ESTADO_RETIRADO, ESTADO_ABORTADO):
                self.retiro.retirar(iddespacho=idd, idusuario=idusuario)
                auto_retirados.append(idd)

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        horainicio = acc.get("horainicio") or acc.get("fechahoraaccidente") or now
        duracion = max(1, int((now - int(horainicio)) / 60_000))

        self.notas.create_motivo(idaccidente=idaccidente, idusuario=idusuario, nota=motivo.strip())
        self.accidentes.update(
            idaccidente,
            {"horafin": now, "duracionminutos": duracion, "activo": False},
        )
        self.estado.append_estado(idaccidente=idaccidente, estado=ESTADO_CERRADO, idusuario=idusuario)

        return {
            "idaccidente": idaccidente,
            "estado_caso": ESTADO_CERRADO,
            "horafin": now,
            "duracionminutos": duracion,
            "tiempos": {"duracionminutos": duracion},
            "despachos_retirados": auto_retirados,
        }
