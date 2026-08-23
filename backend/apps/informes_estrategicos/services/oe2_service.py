"""Diez informes publicados de OE2. E2-06 no está en CATALOGO.

Metas de consumo en CALIBRAR. E2-01 y E2-02 salen con cobertura parcial.
E2-08 declara alcance facturable, no cobrado.
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

DEPARTAMENTO = "estrategicos/oe2"

ALCANCE_EXCEDENTE = (
    "Importe facturable por exceso de cupo. No afirma cobro."
)
FALTA_PRECIO_PLAN = ["precio del plan de API"]

CATALOGO: dict[str, str] = {
    "integraciones-activas": "e2_03_integraciones_activas",
    "consumo-por-partner": "e2_04_consumo_por_partner",
    "latencia-por-endpoint": "e2_05_latencia_por_endpoint",
    "taxonomia-errores": "e2_07_taxonomia_errores",
    "excedente-facturable": "e2_08_excedente_facturable",
    "participacion-ingresos-api": "e2_01_participacion_ingresos_api",
    "mrr-por-linea": "e2_02_mrr_por_linea",
    "adopcion-versiones": "e2_09_adopcion_versiones",
    "comparativa-partners": "e2_10_comparativa_partners",
    "crecimiento-ecosistema": "e2_11_crecimiento_ecosistema",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

#: Informes que cuentan el **numerador dentro del período** y el **denominador
#: sobre el estado de hoy**.
#:
#: ⚠️ Pedido enero de 2019, `integraciones-activas` respondía «3 partners con
#: acceso, 0 % de adopción». Los tres partners son de hoy: en 2019 no existía
#: ninguno. La cifra no decía «no sabemos», decía 0 % — una cifra inventada con
#: forma de medición, y la más difícil de descubrir porque es plausible.
#:
#: Se **declara** en vez de corregirse (decisión del usuario, opción C): acotar
#: el denominador exige historizar `dim_partner` y cambiaría lo que el informe
#: mide. Mismo patrón que `umbral_aplicado` o `medida_exacta_desde`: la
#: convención que no se deduce del número viaja con el número.
DENOMINADOR_ACTUAL = frozenset({
    "integraciones-activas",
    "consumo-por-partner",
    "excedente-facturable",
    "comparativa-partners",
})

NOTA_DENOMINADOR_ACTUAL = (
    "El denominador (partners y cuentas) se cuenta sobre el estado actual, no "
    "sobre el período pedido: un período anterior al alta de un partner lo "
    "incluye igual en el total."
)

BLOQUEADOS: frozenset[str] = frozenset({"disponibilidad-api"})

PARCIALES: frozenset[str] = frozenset(
    {"participacion-ingresos-api", "mrr-por-linea"}
)

PARAMETROS: dict[str, tuple[Any, ...]] = {
    "latencia-por-endpoint": (
        Parametro("muestra_minima", defecto=20, minimo=1, maximo=10_000),
    ),
}


class Oe2Service:
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
        parametros: dict[str, Any] = {**periodo.to_params(), **dados}

        parametros_anterior = None
        ventana_prev = None
        if comparacion in {"mom", "yoy"}:
            ventana_prev = periodo.ventana_anterior(comparacion)
            parametros_anterior = {**parametros, **ventana_prev.to_params()}
            parametros_anterior.update(dados)

        actual, anterior = self._repositorio.ejecutar_con_comparacion(
            consulta,
            departamento=DEPARTAMENTO,
            parametros=parametros,
            parametros_anterior=parametros_anterior,
        )

        cobertura = "parcial" if informe in PARCIALES else "completa"
        denominador = (
            NOTA_DENOMINADOR_ACTUAL if informe in DENOMINADOR_ACTUAL else None
        )
        falta = list(FALTA_PRECIO_PLAN) if informe in PARCIALES else None
        alcance = ALCANCE_EXCEDENTE if informe == "excedente-facturable" else None

        return ResultadoInforme(
            data=actual,
            comparacion=self._armar_comparacion(
                comparacion, periodo, ventana_prev, actual, anterior
            ),
            objetivo=objetivo_calibrar(valor=None, unidad=self._unidad(informe)),
            cobertura=cobertura,
            falta=falta,
            alcance=alcance,
            denominador_actual=denominador,
        )

    def _unidad(self, informe: str) -> str:
        if informe in PARCIALES or informe == "excedente-facturable":
            return "moneda"
        if informe == "latencia-por-endpoint":
            return "ms"
        return "llamadas"

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
