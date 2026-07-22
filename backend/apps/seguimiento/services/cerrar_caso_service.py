"""CU-O28 — cierre multi-despacho con auto-retiro."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.accidentes.domain_constants import (
    ESTADO_ASIGNADO,
    ESTADO_CERRADO,
    ESTADO_EN_ATENCION,
)
from apps.seguimiento.services.retiro_despacho_service import RetiroDespachoService
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_ABORTADO,
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)


class CerrarCasoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        retiro: RetiroDespachoService | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.retiro = retiro or RetiroDespachoService()

    def cerrar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        acc = self.accidentes.find_by_id(idaccidente)
        if not acc:
            raise LookupError("Accidente no encontrado")
        estado_actual = self.estado.get_current_estado(idaccidente)
        if estado_actual == ESTADO_CERRADO:
            raise ValueError("Caso ya cerrado")
        if estado_actual not in (ESTADO_EN_ATENCION, ESTADO_ASIGNADO):
            raise ValueError(f"Estado inválido para cierre: {estado_actual}")

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

        update_fields = {
            "horafin": now,
            "duracionminutos": duracion,
            "resultado_atencion": payload["resultado_atencion"],
            "activo": False,
        }
        for key in ("numvehiculos", "numvictimas", "numheridos", "numfallecidos", "calificacion"):
            if key in payload and payload[key] is not None:
                update_fields[key] = payload[key]
        if payload.get("observaciones_finales"):
            update_fields["observaciones_finales"] = payload["observaciones_finales"]

        self.accidentes.update(idaccidente, update_fields)
        self.estado.append_estado(idaccidente=idaccidente, estado=ESTADO_CERRADO, idusuario=idusuario)

        return {
            "idaccidente": idaccidente,
            "estado_caso": ESTADO_CERRADO,
            "horafin": now,
            "duracionminutos": duracion,
            "tiempos": {"duracionminutos": duracion},
            "despachos_retirados": auto_retirados,
        }
