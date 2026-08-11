"""Metricas de consumo del partner (CU-O52, RF-APM-006 a RF-APM-009).

Tres decisiones que no son obvias
---------------------------------
1. **Solo produccion.** Las metricas y el reporte hablan del entorno productivo
   (RN-APM-001). Mezclar el consumo de pruebas inflaria las cifras que el
   partner usa para dimensionar su plan, y falsearia el excedente que se le
   factura. `Sandbox` se consulta aparte, pidiendolo explicitamente.

2. **`datos_hasta`.** Las escrituras van por Kafka y Pinot tarda ~5-15 s en
   ingerirlas. Devolver «0 llamadas» sin decir hasta cuando son fiables los
   datos haria que el partner creyera que su ultima peticion no se conto. Se
   declara el corte en vez de prometer tiempo real.

3. **Un mes sin consumo devuelve ceros, no un error.** Es una respuesta valida:
   el partner no consumio. Un 404 le haria pensar que el reporte no existe.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from core.repositories.partners.api_integracion_repository import (
    ApiIntegracionRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.partners.plan_read_repository import PlanReadRepository

ENTORNO_PRODUCCION = "Producción"

# Margen de la ventana de ingesta de Kafka -> Pinot. Se resta del «ahora» para
# no afirmar que los ultimos segundos ya estan contados.
RETRASO_INGESTA_SEGUNDOS = 15

SIN_CUPO = -1
# `Dim_Plan.precio_excedente_llamada` sin tarifa configurada.
SIN_TARIFA = -1.0


class MetricasConsumoError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class MetricasConsumoService:
    def __init__(
        self,
        api_integracion: ApiIntegracionRepository | None = None,
        partners: PartnerRepository | None = None,
        planes: PlanReadRepository | None = None,
    ):
        self.api_integracion = api_integracion or ApiIntegracionRepository()
        self.partners = partners or PartnerRepository()
        self.planes = planes or PlanReadRepository()

    # --- Ventanas temporales -------------------------------------------------

    @staticmethod
    def _ahora() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def periodo_actual(cls) -> tuple[int, int]:
        """Del dia 1 del mes en curso hasta ahora, en epoch ms."""
        ahora = cls._ahora()
        inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return int(inicio.timestamp() * 1000), int(ahora.timestamp() * 1000)

    @staticmethod
    def periodo_mensual(anio: int, mes: int) -> tuple[int, int]:
        """Mes natural completo [inicio, fin) en epoch ms."""
        inicio = datetime(anio, mes, 1, tzinfo=timezone.utc)
        fin = (
            datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
            if mes == 12
            else datetime(anio, mes + 1, 1, tzinfo=timezone.utc)
        )
        return int(inicio.timestamp() * 1000), int(fin.timestamp() * 1000)

    @classmethod
    def datos_hasta(cls) -> int:
        """Momento hasta el que los datos son fiables (ver decision 2)."""
        return int(
            (cls._ahora() - timedelta(seconds=RETRASO_INGESTA_SEGUNDOS)).timestamp() * 1000
        )

    # --- Metricas ------------------------------------------------------------

    def metricas_del_partner(
        self,
        idpartner: int,
        *,
        entorno: str = ENTORNO_PRODUCCION,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> dict[str, Any]:
        """Consumo del periodo frente al cupo contratado.

        Por defecto **solo produccion**: es lo que se factura y lo que sirve
        para dimensionar el plan.
        """
        partner = self.partners.find_by_id(idpartner)
        if not partner:
            raise MetricasConsumoError("not_found", "Partner no encontrado")

        if desde_ms is None or hasta_ms is None:
            desde_ms, hasta_ms = self.periodo_actual()

        consumo = self.api_integracion.consumo_del_partner(
            idpartner, entorno=entorno, desde_ms=desde_ms, hasta_ms=hasta_ms
        )
        cupo = int(partner.get("limitellamadasmes", SIN_CUPO))
        llamadas = consumo["llamadas"]

        return {
            "idpartner": idpartner,
            "entorno": entorno,
            "periodo": {"desde": desde_ms, "hasta": hasta_ms},
            "llamadas": llamadas,
            "errores": consumo["errores"],
            "latencia_media_ms": round(consumo["latencia_media"], 2),
            "cupo_mensual": cupo,
            # Con el centinela no hay cupo contra el que comparar: ni porcentaje
            # ni excedente. Inventar un 0 % seria peor que decir «no aplica».
            "porcentaje_consumido": self._porcentaje(llamadas, cupo),
            "llamadas_excedentes": self._excedente(llamadas, cupo),
            "excedente_estimado": self._importe_excedente(partner, llamadas, cupo),
            "datos_hasta": self.datos_hasta(),
        }

    @staticmethod
    def _porcentaje(llamadas: int, cupo: int) -> float | None:
        if cupo == SIN_CUPO or cupo <= 0:
            return None
        return round(llamadas * 100 / cupo, 2)

    @staticmethod
    def _excedente(llamadas: int, cupo: int) -> int:
        if cupo == SIN_CUPO or cupo < 0:
            return 0
        return max(0, llamadas - cupo)

    def _importe_excedente(
        self, partner: dict[str, Any], llamadas: int, cupo: int
    ) -> float | None:
        """Estimacion, no factura. `None` si no hay tarifa configurada.

        Devolver 0.0 sin tarifa haria creer al partner que su exceso es gratis.
        """
        excedentes = self._excedente(llamadas, cupo)
        if excedentes == 0:
            return 0.0
        try:
            suscripcion = self.planes.suscripcion_vigente(int(partner["idcliente"]))
            plan = (
                self.planes.find_plan(int(suscripcion["idplan"])) if suscripcion else None
            )
        except Exception:  # noqa: BLE001 — una estimacion no puede tumbar la consulta
            return None
        if not plan:
            return None
        precio = float(plan.get("precio_excedente_llamada", SIN_TARIFA))
        if precio == SIN_TARIFA or precio < 0:
            return None
        return round(excedentes * precio, 2)

    # --- Reporte mensual -----------------------------------------------------

    def reporte_mensual(
        self, idpartner: int, *, anio: int, mes: int, entorno: str = ENTORNO_PRODUCCION
    ) -> dict[str, Any]:
        """Reporte de un mes natural. Sin consumo devuelve **ceros**, no error."""
        desde_ms, hasta_ms = self.periodo_mensual(anio, mes)
        metricas = self.metricas_del_partner(
            idpartner, entorno=entorno, desde_ms=desde_ms, hasta_ms=hasta_ms
        )
        metricas["por_servicio"] = self.api_integracion.consumo_por_servicio(
            idpartner, entorno=entorno, desde_ms=desde_ms, hasta_ms=hasta_ms
        )
        metricas["anio"] = anio
        metricas["mes"] = mes
        return metricas
