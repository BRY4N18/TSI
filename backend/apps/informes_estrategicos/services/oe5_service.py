"""Nueve informes publicados de OE5. E5-01 y E5-11 no están en CATALOGO.

E5-09 / E5-10 / E5-13 / E5-14 viven en OE1 (REFERENCIAS_OE1): 404 aquí.

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

DEPARTAMENTO = "estrategicos/oe5"

UMBRAL_MUESTRA_DEFECTO = 20

ALCANCE_SLA = (
    "Denominador = tickets cerrados con compromiso de tiempo. "
    "Sin compromiso se declara aparte; no infla ni hunde el porcentaje."
)
ALCANCE_NRR = (
    "NRR descompuesto: expansión, contracción y churn. "
    "No hereda el stub de expansión=0 de OT07. Precio congelado en la suscripción."
)
ALCANCE_AGENTE = (
    "Mide carga de trabajo por idagente, no desempeño individual."
)
ALCANCE_RIESGO = (
    "Una cuenta se marca solo con dos o más señales "
    "(API, tickets, cobro, sesiones). Una sola no basta."
)
ALCANCE_ANTIGUEDAD = (
    "Solo relaciones activas (fecha_baja IS NULL). Las cerradas se declaran aparte."
)

CATALOGO: dict[str, str] = {
    "cumplimiento-sla": "e5_04_cumplimiento_sla",
    "evolucion-incumplimiento": "e5_05_evolucion_incumplimiento",
    "sla-por-plan": "e5_07_sla_por_plan",
    "retencion-neta-ingresos": "e5_02_retencion_neta_ingresos",
    "movimientos-de-plan": "e5_03_movimientos_de_plan",
    "rendimiento-por-agente": "e5_06_rendimiento_por_agente",
    "reincidencia-soporte": "e5_08_reincidencia_soporte",
    "cuentas-en-riesgo": "e5_12_cuentas_en_riesgo",
    "antiguedad-de-cuenta": "e5_15_antiguedad_de_cuenta",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

BLOQUEADOS: frozenset[str] = frozenset(
    {"nps-satisfaccion", "reportes-sin-correccion"}
)

REFERENCIAS_OE1: frozenset[str] = frozenset(
    {
        "tasa-renovacion",
        "churn-por-cohorte",
        "tiempo-onboarding",
        "abandono-onboarding",
    }
)

PARAMETROS: dict[str, tuple[Any, ...]] = {}

_CAMPOS_N = (
    "recuento",
    "n",
    "muestra",
    "clientes",
    "con_compromiso",
    "denominador",
    "tickets",
    "asignados",
)


class Oe5Service:
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
        falta: list[str] | None
        if n < umbral:
            cobertura = "parcial"
            falta = [f"muestra n={n} bajo umbral {umbral}"]
        else:
            cobertura = "completa"
            falta = None

        if informe == "cuentas-en-riesgo":
            extra_falta = _faltas_senales(actual)
            if extra_falta:
                cobertura = "parcial"
                falta = (falta or []) + extra_falta

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
        if informe in {"retencion-neta-ingresos", "movimientos-de-plan"}:
            return "moneda"
        if informe == "antiguedad-de-cuenta":
            return "dias"
        return "ratio"

    def _alcance(self, informe: str) -> str | None:
        if informe in {
            "cumplimiento-sla",
            "evolucion-incumplimiento",
            "sla-por-plan",
        }:
            return ALCANCE_SLA
        if informe == "retencion-neta-ingresos":
            return ALCANCE_NRR
        if informe == "rendimiento-por-agente":
            return ALCANCE_AGENTE
        if informe == "cuentas-en-riesgo":
            return ALCANCE_RIESGO
        if informe == "antiguedad-de-cuenta":
            return ALCANCE_ANTIGUEDAD
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


def _faltas_senales(filas: list[dict[str, Any]]) -> list[str]:
    if not filas:
        return [
            "señal API sin filas en el período",
            "señal tickets sin filas en el período",
            "señal cobro sin filas en el período",
            "señal sesiones sin filas en el período",
        ]
    fila = filas[0]
    mapa = (
        ("n_fuente_api", "API"),
        ("n_fuente_tickets", "tickets"),
        ("n_fuente_cobro", "cobro"),
        ("n_fuente_sesiones", "sesiones"),
    )
    falta = []
    for clave, nombre in mapa:
        if clave in fila:
            try:
                if int(fila[clave] or 0) == 0:
                    falta.append(f"señal {nombre} sin filas en el período")
            except (TypeError, ValueError):
                falta.append(f"señal {nombre} sin filas en el período")
    return falta
