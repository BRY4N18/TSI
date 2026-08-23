"""Servicio de los siete informes publicados de OE3.

Un informe existe si está en `CATALOGO`. Se publica si está en `PUBLICADOS`.
Los siete bloqueados no entran: un fichero suelto en el disco no debe
convertirse en endpoint. E3-04 publicado compararía contra 1970.

Reutiliza el armazón de OE6 (período, envelope, repositorio). Lo que este
módulo aporta es el permiso por informe y el `cumple` booleano.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.informes_estrategicos.objetivo import (
    objetivo_calibrar,
    objetivo_normativo,
)
from apps.informes_estrategicos.periodo_estrategico import (
    MOTIVO_SIN_VENTANA_ANTERIOR,
    PeriodoEstrategico,
)
from apps.informes_tacticos.services.emergencias_compuestos_service import Parametro
from apps.informes_estrategicos.services.oe6_service import (
    InformeDesconocido,
    ParametroBooleano,
    _variacion,
)
from core.repositories.informes_estrategicos.modelo_estrategico_repository import (
    ModeloEstrategicoRepository,
)

DEPARTAMENTO = "estrategicos/oe3"

ALCANCE_LATENCIA = (
    "Mide el proceso operativo registro→asignación (meta RNF-DES-001, "
    "<2 min p95), no la latencia técnica del algoritmo."
)
ALCANCE_CAPACIDAD = (
    "La atribución unidad-proveedor es exacta desde la primera carga del "
    "modelo. El origen no historiza el cambio de proveedor."
)

CATALOGO: dict[str, str] = {
    "latencia-asignacion": "e3_02_latencia_asignacion",
    "evolucion-latencia": "e3_03_evolucion_latencia",
    "tasa-error-registro": "e3_10_tasa_error_registro",
    "primer-intento": "e3_11_primer_intento",
    "ratio-demanda-capacidad": "e3_07_ratio_demanda_capacidad",
    "cobertura-de-respaldo": "e3_08_cobertura_de_respaldo",
    "perdida-de-senal": "e3_13_perdida_de_senal",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

BLOQUEADOS: frozenset[str] = frozenset(
    {
        "uptime-por-region",
        "tiempo-puesta-operacion",
        "curva-maduracion",
        "cohorte-region",
        "margen-operativo",
        "reasignacion-manual",
        "cobertura-pruebas",
    }
)

PARAMETROS: dict[str, tuple[Any, ...]] = {
    "latencia-asignacion": (
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
        ParametroBooleano("por_condado"),
    ),
    "evolucion-latencia": (
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
    ),
    "tasa-error-registro": (ParametroBooleano("por_condado"),),
    "primer-intento": (ParametroBooleano("por_condado"),),
    "perdida-de-senal": (
        Parametro("umbral_seg", defecto=60, minimo=1, maximo=86_400),
    ),
}

CON_CONDADO = frozenset(
    {"latencia-asignacion", "tasa-error-registro", "primer-intento"}
)


@dataclass
class ResultadoInforme:
    data: list[dict[str, Any]]
    comparacion: dict[str, Any] | None
    objetivo: dict[str, Any] | None
    cobertura: str
    falta: list[str] | None
    alcance: str | None
    #: Declara que el denominador se cuenta sobre el estado **actual**, no sobre
    #: el período pedido. `None` cuando el informe no tiene ese sesgo.
    denominador_actual: str | None = None


class Oe3Service:
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

        if informe in CON_CONDADO and not dados.get("por_condado"):
            for fila in actual:
                fila.pop("condado", None)
            if anterior:
                for fila in anterior:
                    fila.pop("condado", None)

        if informe == "ratio-demanda-capacidad":
            for fila in actual:
                fila["sin_capacidad"] = bool(int(fila.get("sin_capacidad") or 0))
            if anterior:
                for fila in anterior:
                    fila["sin_capacidad"] = bool(int(fila.get("sin_capacidad") or 0))

        meta_comparacion = self._armar_comparacion(
            comparacion, periodo, ventana_prev, actual, anterior
        )
        return ResultadoInforme(
            data=actual,
            comparacion=meta_comparacion,
            objetivo=self._objetivo(informe, actual),
            cobertura="completa",
            falta=None,
            alcance=self._alcance(informe),
        )

    def _alcance(self, informe: str) -> str | None:
        if informe == "latencia-asignacion":
            return ALCANCE_LATENCIA
        if informe == "ratio-demanda-capacidad":
            return ALCANCE_CAPACIDAD
        return None

    def _objetivo(self, informe: str, data: list[dict[str, Any]]) -> dict[str, Any] | None:
        if informe == "latencia-asignacion":
            medidos = [f.get("p95_min") for f in data if f.get("p95_min") is not None]
            medido = max(medidos) if medidos else None
            return objetivo_normativo(
                valor=2, unidad="min", medido=medido, umbral="lt"
            )
        if informe == "tasa-error-registro":
            medidos = [f.get("tasa_error") for f in data if f.get("tasa_error") is not None]
            medido = max(medidos) if medidos else None
            return objetivo_normativo(
                valor=1, unidad="%", medido=medido, umbral="lt"
            )
        if informe == "primer-intento":
            return objetivo_calibrar(valor=90, unidad="%")
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
