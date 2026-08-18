"""Diez informes publicados de OE1. E1-05, E1-07 y E1-08 no están en CATALOGO.

Dueño de E1-06 / E1-09 / E1-10 / E1-11: OE5 los referencia, no los reimplementa.

`cumple` del objetivo es siempre null (CALIBRAR). La cobertura es parcial
mientras la muestra n esté bajo el umbral (defecto 20).
"""

from __future__ import annotations

from typing import Any

from apps.informes_estrategicos.objetivo import objetivo_calibrar
from apps.informes_estrategicos.periodo_estrategico import (
    MOTIVO_SIN_VENTANA_ANTERIOR,
    PeriodoEstrategico,
)
from apps.informes_estrategicos.services.oe3_service import ResultadoInforme
from apps.informes_estrategicos.services.oe6_service import InformeDesconocido, _variacion
from apps.informes_tacticos.services.emergencias_compuestos_service import Parametro
from core.repositories.informes_estrategicos.modelo_estrategico_repository import (
    ModeloEstrategicoRepository,
)

DEPARTAMENTO = "estrategicos/oe1"

UMBRAL_MUESTRA_DEFECTO = 20

ALCANCE_CIERRE = (
    "Vigente al cierre del período: fecha_alta ≤ hasta y no cancelada ni "
    "vencida en esa fecha. Suma precio_mensualizado; no divide precio."
)
ALCANCE_ARR = (
    "Extrapolación de MRR × 12; no es ingreso comprometido."
)
ALCANCE_EMBUDO = (
    "Grano = transiciones del embudo. Etapas sin movimiento aparecen en cero. "
    "El cruce con Cuentas no aplica a este embudo comercial."
)

CATALOGO: dict[str, str] = {
    "mrr-mensual": "e1_01_mrr_mensual",
    "arr-proyeccion": "e1_02_arr_proyeccion",
    "mrr-por-segmento": "e1_03_mrr_por_segmento",
    "cartera-por-plan": "e1_12_cartera_por_plan",
    "embudo-conversion": "e1_04_embudo_conversion",
    "velocidad-ciclo-venta": "e1_13_velocidad_ciclo_venta",
    "tasa-renovacion": "e1_06_tasa_renovacion",
    "tiempo-onboarding": "e1_09_tiempo_onboarding",
    "abandono-onboarding": "e1_10_abandono_onboarding",
    "churn-por-cohorte": "e1_11_churn_por_cohorte",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

BLOQUEADOS: frozenset[str] = frozenset(
    {"cac-por-canal", "mercados-activos", "cartera-mrr-por-mercado"}
)

PARAMETROS: dict[str, tuple[Any, ...]] = {
    "churn-por-cohorte": (
        Parametro("umbral_muestra", defecto=UMBRAL_MUESTRA_DEFECTO, minimo=1, maximo=10_000),
    ),
}

_CAMPOS_N = (
    "recuento",
    "n",
    "muestra",
    "clientes",
    "suscripciones",
    "vencidas",
    "denominador",
    "clientes_iniciales",
    "completados",
    "transiciones",
)


class Oe1Service:
    def __init__(self, repositorio: ModeloEstrategicoRepository | None = None):
        self._repositorio = repositorio or ModeloEstrategicoRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def parametros_de(self, informe: str) -> tuple[Any, ...]:
        return PARAMETROS.get(informe, ())

    def calcular(
        self,
        informe: str,
        periodo: PeriodoEstrategico,
        *,
        comparacion: str = "ninguna",
        extra: dict[str, Any] | None = None,
        publicado: bool = True,
    ) -> ResultadoInforme:
        if publicado and informe not in PUBLICADOS:
            raise InformeDesconocido(informe)
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        dados = extra or {}
        umbral = int(dados.get("umbral_muestra", UMBRAL_MUESTRA_DEFECTO))
        parametros: dict[str, Any] = {
            **periodo.to_params(),
            "umbral_muestra": umbral,
            **dados,
        }

        parametros_anterior = None
        ventana_prev = None
        if comparacion in {"mom", "yoy"}:
            ventana_prev = periodo.ventana_anterior(comparacion)
            parametros_anterior = {**parametros, **ventana_prev.to_params()}
            parametros_anterior.update(dados)
            parametros_anterior["umbral_muestra"] = umbral

        actual, anterior = self._repositorio.ejecutar_con_comparacion(
            consulta,
            departamento=DEPARTAMENTO,
            parametros=parametros,
            parametros_anterior=parametros_anterior,
        )

        n = _muestra(actual)
        if n < umbral:
            cobertura = "parcial"
            falta = [f"muestra n={n} bajo umbral {umbral}"]
        else:
            cobertura = "completa"
            falta = None

        return ResultadoInforme(
            data=actual,
            comparacion=self._armar_comparacion(
                comparacion, periodo, ventana_prev, actual, anterior
            ),
            objetivo=objetivo_calibrar(valor=None, unidad=self._unidad(informe)),
            cobertura=cobertura,
            falta=falta,
            alcance=self._alcance(informe),
        )

    def _unidad(self, informe: str) -> str:
        if informe in {
            "mrr-mensual",
            "arr-proyeccion",
            "mrr-por-segmento",
            "cartera-por-plan",
        }:
            return "moneda"
        if informe in {"tiempo-onboarding", "velocidad-ciclo-venta"}:
            return "dias"
        return "ratio"

    def _alcance(self, informe: str) -> str | None:
        if informe in {"mrr-mensual", "mrr-por-segmento", "cartera-por-plan"}:
            return ALCANCE_CIERRE
        if informe == "arr-proyeccion":
            return ALCANCE_ARR
        if informe == "embudo-conversion":
            return ALCANCE_EMBUDO
        return None

    def _armar_comparacion(
        self,
        tipo: str,
        periodo: PeriodoEstrategico,
        ventana_prev: PeriodoEstrategico | None,
        actual: list[dict[str, Any]],
        anterior: list[dict[str, Any]] | None,
    ) -> dict[str, Any] | None:
        if tipo == "ninguna" or ventana_prev is None:
            return None
        ventana_actual = {
            "desde": periodo.desde.isoformat(),
            "hasta": periodo.hasta.isoformat(),
        }
        if not anterior:
            return {
                "tipo": tipo,
                "ventana_actual": ventana_actual,
                "ventana_anterior": None,
                "variacion": None,
                "motivo_ausencia": MOTIVO_SIN_VENTANA_ANTERIOR,
            }
        return {
            "tipo": tipo,
            "ventana_actual": ventana_actual,
            "ventana_anterior": {
                "desde": ventana_prev.desde.isoformat(),
                "hasta": ventana_prev.hasta.isoformat(),
            },
            "variacion": _variacion(actual, anterior),
        }


def _muestra(filas: list[dict[str, Any]]) -> int:
    if not filas:
        return 0
    total = 0
    hallado = False
    for fila in filas:
        for clave in _CAMPOS_N:
            if clave in fila and fila[clave] is not None:
                try:
                    total += int(fila[clave])
                except (TypeError, ValueError):
                    continue
                hallado = True
                break
    return total if hallado else len(filas)
