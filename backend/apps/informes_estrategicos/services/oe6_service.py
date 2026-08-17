"""Servicio de los doce informes de OE6.

Enlaza **nombre de informe → consulta del catálogo → respuesta**, y nada más.
Un informe existe si está en `CATALOGO`. Se publica como endpoint si está en
`PUBLICADOS`. Estar en el disco no basta: un fichero de pruebas no debe
convertirse en endpoint sin que nadie lo decida.

Los parámetros de período y la comparación se resuelven aquí, no en SQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.informes_estrategicos.objetivo import objetivo_calibrar
from apps.informes_estrategicos.periodo_estrategico import (
    MOTIVO_SIN_VENTANA_ANTERIOR,
    PeriodoEstrategico,
)
from apps.informes_tacticos.services.emergencias_compuestos_service import (
    Parametro,
    ParametroTramos,
)
from core.repositories.informes_estrategicos.modelo_estrategico_repository import (
    ModeloEstrategicoRepository,
)

DEPARTAMENTO = "estrategicos/oe6"

ALCANCE_DESVIACION = (
    "La referencia es el histórico comparable, no un ETA estimado."
)
ALCANCE_RECHAZO = (
    "El denominador son intentos ofrecidos, no transiciones de estado."
)
ALCANCE_CIERRES = (
    "Mide el indicador retiro_forzado del despacho, no el retiro manual desde "
    "central. Las dos definiciones difieren; ver decisión #36."
)


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


class ParametroBooleano:
    """`por_condado` y similares: se traducen a 0/1 para ClickHouse."""

    def __init__(self, nombre: str, defecto: bool = False):
        self.nombre = nombre
        self.defecto = defecto

    def leer(self, crudo: str | None) -> int:
        if crudo is None:
            return int(self.defecto)
        valor = str(crudo).strip().lower()
        if valor in {"1", "true", "yes", "si", "sí"}:
            return 1
        if valor in {"0", "false", "no"}:
            return 0
        raise ValueError(f"'{self.nombre}' debe ser verdadero o falso.")


CATALOGO: dict[str, str] = {
    "tiempo-respuesta-global": "e6_01_tiempo_respuesta_global",
    "tiempo-respuesta-por-severidad": "e6_02_tiempo_respuesta_por_severidad",
    "tramos-del-ciclo": "e6_03_tramos_del_ciclo",
    "origen-de-asignacion": "e6_04_origen_de_asignacion",
    "rechazo-y-timeout-por-unidad": "e6_05_rechazo_y_timeout_por_unidad",
    "abortos-y-misiones-fallidas": "e6_06_abortos_y_misiones_fallidas",
    "desviacion-de-llegada": "e6_07_desviacion_de_llegada",
    "impacto-humano": "e6_08_impacto_humano",
    "cierres-forzados": "e6_09_cierres_forzados",
    "envejecimiento-de-casos-abiertos": "e6_10_envejecimiento_casos_abiertos",
    "escaladas-de-severidad": "e6_11_escaladas_de_severidad",
    "cobertura-de-evidencia": "e6_12_cobertura_de_evidencia",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

PARAMETROS: dict[str, tuple[Any, ...]] = {
    "tiempo-respuesta-global": (
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
        ParametroBooleano("por_condado"),
    ),
    "tiempo-respuesta-por-severidad": (
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
    ),
    "origen-de-asignacion": (ParametroBooleano("por_condado"),),
    "desviacion-de-llegada": (
        Parametro("ventana_dias", defecto=90, minimo=7, maximo=730),
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
    ),
    "rechazo-y-timeout-por-unidad": (
        Parametro("top", defecto=10, minimo=1, maximo=100),
    ),
    "envejecimiento-de-casos-abiertos": (ParametroTramos(),),
    "impacto-humano": (ParametroBooleano("por_condado"),),
    "escaladas-de-severidad": (
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
    ),
}

OBJETIVOS: dict[str, dict[str, Any]] = {
    nombre: {"valor": None, "unidad": unidad}
    for nombre, unidad in {
        "tiempo-respuesta-global": "min",
        "tiempo-respuesta-por-severidad": "min",
        "tramos-del-ciclo": "min",
        "origen-de-asignacion": "%",
        "rechazo-y-timeout-por-unidad": "%",
        "abortos-y-misiones-fallidas": "%",
        "desviacion-de-llegada": "s",
        "impacto-humano": "personas",
        "cierres-forzados": "%",
        "envejecimiento-de-casos-abiertos": "casos",
        "escaladas-de-severidad": "%",
        "cobertura-de-evidencia": "%",
    }.items()
}

ALCANCE: dict[str, str] = {
    "desviacion-de-llegada": ALCANCE_DESVIACION,
    "rechazo-y-timeout-por-unidad": ALCANCE_RECHAZO,
    "cierres-forzados": ALCANCE_CIERRES,
}

_CLAVES_NO_MEDIDA = frozenset({
    "periodo", "severidad", "orden", "condado", "unidad", "origen", "tramo",
    "causa", "proveedor", "corte", "tramo_dias", "severidad_inicial",
    "severidad_final",
})
_NO_SUMABLES = (
    "mediana", "p95", "promedio", "tasa", "pct", "desviacion",
    "referencia", "segundos", "antiguedad",
)


@dataclass
class ResultadoInforme:
    data: list[dict[str, Any]]
    comparacion: dict[str, Any] | None
    objetivo: dict[str, Any]
    cobertura: str
    falta: list[str] | None
    alcance: str | None


class Oe6Service:
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

        if informe in {"tiempo-respuesta-global", "origen-de-asignacion", "impacto-humano"}:
            if not dados.get("por_condado"):
                for fila in actual:
                    fila.pop("condado", None)
                if anterior:
                    for fila in anterior:
                        fila.pop("condado", None)

        meta_comparacion = self._armar_comparacion(
            comparacion, periodo, ventana_prev, actual, anterior
        )
        cobertura, falta = self._cobertura(informe, actual, dados)
        meta_objetivo = OBJETIVOS[informe]
        return ResultadoInforme(
            data=actual,
            comparacion=meta_comparacion,
            objetivo=objetivo_calibrar(
                valor=meta_objetivo["valor"], unidad=meta_objetivo["unidad"]
            ),
            cobertura=cobertura,
            falta=falta,
            alcance=ALCANCE.get(informe),
        )

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

    def _cobertura(
        self,
        informe: str,
        data: list[dict[str, Any]],
        extra: dict[str, Any],
    ) -> tuple[str, list[str] | None]:
        if informe == "cierres-forzados":
            return "parcial", ["retiro manual desde central"]
        if informe == "escaladas-de-severidad":
            if not data:
                return "completa", None
            muestra = extra.get("muestra_minima", 5)
            con_escalada = sum(int(f.get("con_escalada") or 0) for f in data)
            if con_escalada < muestra:
                return "parcial", ["muestra de escaladas por debajo del mínimo"]
        return "completa", None


def _variacion(
    actual: list[dict[str, Any]], anterior: list[dict[str, Any]]
) -> dict[str, Any] | None:
    def _sumas(filas: list[dict[str, Any]]) -> dict[str, float]:
        acc: dict[str, float] = {}
        for fila in filas:
            for clave, valor in fila.items():
                if clave in _CLAVES_NO_MEDIDA or valor is None:
                    continue
                if not isinstance(valor, (int, float)):
                    continue
                if any(marca in clave for marca in _NO_SUMABLES):
                    continue
                acc[clave] = acc.get(clave, 0) + valor
        if len(filas) == 1:
            for clave, valor in filas[0].items():
                if clave in _CLAVES_NO_MEDIDA or valor is None:
                    continue
                if isinstance(valor, (int, float)) and any(
                    marca in clave for marca in _NO_SUMABLES
                ):
                    acc[clave] = valor
        return acc

    a, b = _sumas(actual), _sumas(anterior)
    out: dict[str, Any] = {}
    for clave, valor in a.items():
        if clave in b:
            out[clave] = round(valor - b[clave], 4)
    return out or None
