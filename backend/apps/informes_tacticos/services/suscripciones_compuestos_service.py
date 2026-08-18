"""Servicio de los informes compuestos de Suscripciones y Facturación.

Mismo patrón que Red Operativa: un `modelo_repository`, un catálogo de ficheros
SQL y **autoridad repartida por materia**. El Financiero cubre cobro y
movimientos; el de Estrategia, el catálogo. Ninguno cubre la materia del otro.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "suscripciones"

MATERIA_FINANZAS = "finanzas"
MATERIA_CATALOGO = "catalogo"

MES_RE = re.compile(r"^\d{4}-\d{2}$")


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


CATALOGO: dict[str, str] = {
    # OT06 — ciclo de cobro
    "mrr": "ot06_mrr",
    "ingresos": "ot06_ingresos",
    "tasa-renovacion": "ot06_tasa_renovacion",
    "cobro-primer-intento": "ot06_cobro_primer_intento",
    "efectividad-dunning": "ot06_efectividad_dunning",
    "clientes-sin-metodo-pago": "ot06_clientes_sin_metodo_pago",
    # OT07 — movimientos
    "movimientos-plan": "ot07_movimientos_plan",
    "nrr": "ot07_nrr",
    "suspension-reactivacion": "ot07_suspension_reactivacion",
    "tiempo-resolucion-solicitudes": "ot07_tiempo_resolucion",
    # OT05 — catálogo
    "distribucion-cartera": "ot05_distribucion_cartera",
    "utilizacion-limites": "ot05_utilizacion_limites",
    "severidades-habilitadas-vs-usadas": "ot05_severidades_habilitadas_vs_usadas",
}

MATERIAS: dict[str, str] = {
    "distribucion-cartera": MATERIA_CATALOGO,
    "utilizacion-limites": MATERIA_CATALOGO,
    "severidades-habilitadas-vs-usadas": MATERIA_CATALOGO,
    **{
        informe: MATERIA_FINANZAS
        for informe in CATALOGO
        if informe
        not in (
            "distribucion-cartera",
            "utilizacion-limites",
            "severidades-habilitadas-vs-usadas",
        )
    },
}

INFORMES_MES_NATURAL = frozenset({"mrr", "nrr"})

PARAMETROS: dict[str, dict[str, Any]] = {
    "efectividad-dunning": {"escalones_dunning": "3,5"},
    "clientes-sin-metodo-pago": {"dias_aviso_caducidad": 30},
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

NOTA_MES_PARAMETRO = "Se mide por mes natural; se aplicó el parámetro mes."
NOTA_MES_RESUELTO = (
    "Se mide por mes natural; un rango arbitrario se resuelve al mes que lo contiene."
)


def mes_natural_de(periodo: Periodo, mes_param: str | None) -> tuple[str, str]:
    """Mes `YYYY-MM` efectivo y la nota que lo declara."""
    if mes_param and MES_RE.match(mes_param.strip()):
        return mes_param.strip(), NOTA_MES_PARAMETRO
    hasta = date.fromisoformat(periodo.hasta)
    return f"{hasta.year:04d}-{hasta.month:02d}", NOTA_MES_RESUELTO


class SuscripcionesCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def materia_de(self, informe: str) -> str | None:
        return MATERIAS.get(informe)

    def calcular(
        self, informe: str, periodo: Periodo, *, extra: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        parametros: dict[str, Any] = {"desde": periodo.desde, "hasta": periodo.hasta}
        parametros.update(PARAMETROS.get(informe, {}))
        parametros.update(extra or {})
        if informe in INFORMES_MES_NATURAL and "mes" not in parametros:
            mes, _ = mes_natural_de(periodo, None)
            parametros["mes"] = mes
        return self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
