"""Comparacion del consumo contra el cupo y sus avisos (CU-O53, RF-APM-010).

ESTE SERVICIO NO RESTRINGE NADA. NUNCA.
---------------------------------------
Compara y avisa; no bloquea (RN-APM-002). El SRS es explicito y la spec dice
que lo documenta *«precisamente para que nadie la corrija asumiendo que deberia
bloquear»*. Superar el cupo genera **excedente facturable**, no un corte.

Si alguna vez ves aqui un `raise` o un `return False` que impida una llamada,
es un defecto: el corte del ritmo instantaneo vive en `throttling.py` y es otra
cosa (§ 15 D2).

Los avisos no se duplican
-------------------------
Se emite **uno por umbral y periodo** (RN-APM-010). Sin esa comprobacion, el
job —que corre periodicamente— avisaria en cada ejecucion desde que se cruza el
umbral, y el partner acabaria ignorando los correos justo antes de que le
importen.
"""

from __future__ import annotations

from typing import Any

from core.repositories.partners.api_integracion_repository import (
    ApiIntegracionRepository,
)
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository

ENTORNO_PRODUCCION = "Producción"

# Centinela de `limitellamadasmes`: sin cupo asignado. Un 0 seria un cupo real
# de cero llamadas, por eso el centinela es -1.
SIN_CUPO = -1

UMBRAL_AVISO = 0.80
UMBRAL_ALCANZADO = 1.00

# Tipos de evento en la bitacora, que es donde se comprueba la no duplicacion.
AVISO_CUOTA_80 = "aviso_cuota_80"
AVISO_CUOTA_100 = "aviso_cuota_100"


class LimitesConsumoService:
    def __init__(
        self,
        api_integracion: ApiIntegracionRepository | None = None,
        partners: PartnerRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
    ):
        self.api_integracion = api_integracion or ApiIntegracionRepository()
        self.partners = partners or PartnerRepository()
        self.historial = historial or HistorialAccesoRepository()

    def evaluar(
        self,
        idpartner: int,
        *,
        desde_ms: int,
        hasta_ms: int,
        entorno: str = ENTORNO_PRODUCCION,
    ) -> dict[str, Any]:
        """Estado del consumo frente al cupo. **Nunca decide bloquear.**

        Devuelve `umbral_alcanzado` con el aviso que TOCARIA emitir, sin mirar
        si ya se emitio: de eso se encarga `debe_avisar`.
        """
        partner = self.partners.find_by_id(idpartner)
        if not partner:
            return {"aplica": False, "motivo": "partner_inexistente"}

        cupo = int(partner.get("limitellamadasmes", SIN_CUPO))
        if cupo == SIN_CUPO:
            # Sin cupo asignado no hay nada contra que comparar. Tratar el -1
            # como un limite haria que el partner recibiera un aviso de «has
            # superado tu cupo» en su primera llamada.
            return {"aplica": False, "motivo": "sin_cupo_asignado", "cupo": cupo}

        llamadas = self.api_integracion.llamadas_del_periodo(
            idpartner, entorno=entorno, desde_ms=desde_ms, hasta_ms=hasta_ms
        )
        proporcion = (llamadas / cupo) if cupo > 0 else 0.0

        umbral = None
        if proporcion >= UMBRAL_ALCANZADO:
            umbral = AVISO_CUOTA_100
        elif proporcion >= UMBRAL_AVISO:
            umbral = AVISO_CUOTA_80

        return {
            "aplica": True,
            "idpartner": idpartner,
            "cupo": cupo,
            "llamadas": llamadas,
            "proporcion": round(proporcion, 4),
            "umbral_alcanzado": umbral,
            "excedentes": max(0, llamadas - cupo),
            # Se deja explicito para que nadie lo interprete al reves al leer
            # el diccionario en otro sitio.
            "servicio_interrumpido": False,
        }

    def debe_avisar(self, idpartner: int, umbral: str, *, desde_ms: int) -> bool:
        """`True` si ese aviso aun no se emitio en el periodo (RN-APM-010)."""
        return not self.historial.existe_evento(
            idpartner, umbral, desde_ms=desde_ms
        )

    def registrar_aviso(self, idpartner: int, umbral: str, llamadas: int, cupo: int) -> None:
        """Deja constancia del aviso en la bitacora inmutable.

        Se registra ahi y no en una tabla propia porque es la misma bitacora
        que ya responde «que le paso a este partner y cuando» (RF-PON-010), y
        porque es append-only: un aviso no se puede borrar ni reescribir.
        """
        self.historial.registrar(
            idpartner=idpartner,
            tipo_cambio=umbral,
            ejecutado_por="Sistema",
            estado_nuevo=f"{llamadas}/{cupo}",
            motivo=umbral,
        )
