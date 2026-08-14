"""CU-O80 — cierre multi-despacho con auto-retiro."""

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
from core.repositories.seguimiento.cierre_accidente_repository import (
    CierreAccidenteRepository,
)


class CerrarCasoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        retiro: RetiroDespachoService | None = None,
        cierre_repo: CierreAccidenteRepository | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.retiro = retiro or RetiroDespachoService()
        self.cierre_repo = cierre_repo or CierreAccidenteRepository()

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

        # SRS §3.6.4, la regla más estricta del departamento: "un caso solo pasa
        # a cerrado cuando **todas** las unidades despachadas se han retirado.
        # No existe el cierre parcial". Antes esta operación retiraba por su
        # cuenta a las unidades que siguieran trabajando, y además las
        # registraba como retiro **normal**: la regla no llegaba a aplicarse
        # nunca y se perdía la distinción entre una finalización y un cierre
        # decidido desde central. Quien no ha terminado se retira por su propia
        # vía, o el Operador fuerza su retiro y eso queda marcado como tal.
        sin_retirar = [
            int(d["iddespacho"])
            for d in self.despachos.list_by_accidente(idaccidente)
            if self.historial.get_current_estado(int(d["iddespacho"]))[0]
            not in (ESTADO_RETIRADO, ESTADO_ABORTADO)
        ]
        if sin_retirar:
            raise ValueError(
                "No se puede cerrar: "
                f"{len(sin_retirar)} unidad(es) siguen sin retirarse. "
                "Espera a que finalicen o fuerza su retiro desde central."
            )

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        horainicio = acc.get("horainicio") or acc.get("fechahoraaccidente") or now
        duracion = max(1, int((now - int(horainicio)) / 60_000))

        update_fields = {
            "horafin": now,
            "duracionminutos": duracion,
            "activo": False,
        }
        for key in ("numvehiculos", "numvictimas", "numheridos", "numfallecidos"):
            if key in payload and payload[key] is not None:
                update_fields[key] = payload[key]

        self.accidentes.update(idaccidente, update_fields)
        # RF-SEG-004: resultado/calificación/observaciones no existen en el
        # esquema real de Fact_Accidente — se guardan en la tabla auxiliar
        # Fact_CierreAccidente (corrección 2026-08-08).
        self.cierre_repo.registrar(
            idaccidente=idaccidente,
            resultado_atencion=payload["resultado_atencion"],
            calificacion=payload.get("calificacion"),
            observaciones_finales=payload.get("observaciones_finales"),
        )
        self.estado.append_estado(idaccidente=idaccidente, estado=ESTADO_CERRADO, idusuario=idusuario)

        return {
            "idaccidente": idaccidente,
            "estado_caso": ESTADO_CERRADO,
            "horafin": now,
            "duracionminutos": duracion,
            "tiempos": {"duracionminutos": duracion},
            "despachos_retirados": [],
        }
