"""Nueve informes publicados de OE4. Los seis bloqueados no están en CATALOGO.

Todas las metas son CALIBRAR: `cumple` nunca es booleano.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.informes_estrategicos.objetivo import objetivo_calibrar
from apps.informes_estrategicos.periodo_estrategico import (
    MOTIVO_SIN_VENTANA_ANTERIOR,
    PeriodoEstrategico,
)
from apps.informes_estrategicos.services.oe3_service import ResultadoInforme
from apps.informes_estrategicos.services.oe6_service import (
    InformeDesconocido,
    ParametroBooleano,
    _variacion,
)
from apps.informes_tacticos.services.emergencias_compuestos_service import Parametro
from core.repositories.informes_estrategicos.modelo_estrategico_repository import (
    ModeloEstrategicoRepository,
)

DEPARTAMENTO = "estrategicos/oe4"

ALCANCE_INDICE = (
    "Media sin ponderar de las cuatro componentes, heredada del legado. "
    "Cobertura de evidencia = foto o nota en el hecho."
)
ALCANCE_CLIMA = (
    "La mitad climática se declara parcial mientras haya menos casos con "
    "condicion_clima que muestra_minima (hoy son 3)."
)
ALCANCE_VIAL = (
    "casos_con_duracion y casos_con_distancia son denominadores distintos. "
    "NULL de distancia no es cero kilómetros."
)

CATALOGO: dict[str, str] = {
    "indice-calidad-historico": "e4_01_indice_calidad_historico",
    "completitud-campos-criticos": "e4_02_completitud_campos_criticos",
    "campos-mas-ausentes": "e4_03_campos_mas_ausentes",
    "calidad-por-origen": "e4_04_calidad_por_origen",
    "concentracion-siniestralidad": "e4_05_concentracion_siniestralidad",
    "patron-horario-climatico": "e4_06_patron_horario_climatico",
    "impacto-humano-por-zona": "e4_12_impacto_humano_por_zona",
    "impacto-vial-por-zona": "e4_13_impacto_vial_por_zona",
    "cobertura-del-historico": "e4_15_cobertura_del_historico",
}

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

BLOQUEADOS: frozenset[str] = frozenset(
    {
        "precision-del-modelo",
        "contraste-prediccion-ocurrencia",
        "unidades-preposicionadas",
        "versiones-del-modelo",
        "productos-de-inteligencia",
        "latencia-de-ingesta",
    }
)

PARAMETROS: dict[str, tuple[Any, ...]] = {
    "completitud-campos-criticos": (ParametroBooleano("por_condado"),),
    "concentracion-siniestralidad": (
        Parametro("top", defecto=10, minimo=1, maximo=100),
    ),
    "patron-horario-climatico": (
        Parametro("muestra_minima", defecto=20, minimo=1, maximo=10_000),
    ),
    "cobertura-del-historico": (
        Parametro("umbral_casos", defecto=500, minimo=1, maximo=1_000_000),
    ),
}

CON_CONDADO = frozenset({"completitud-campos-criticos"})


class Oe4Service:
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
        if informe == "concentracion-siniestralidad":
            parametros.setdefault("nivel", dados.get("nivel", "condado"))
            parametros.setdefault("top", dados.get("top", 10))

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

        cobertura = "completa"
        if informe == "patron-horario-climatico" and any(
            f.get("cobertura") == "parcial" for f in actual
        ):
            cobertura = "parcial"

        return ResultadoInforme(
            data=actual,
            comparacion=self._armar_comparacion(
                comparacion, periodo, ventana_prev, actual, anterior
            ),
            objetivo=objetivo_calibrar(valor=None, unidad=self._unidad(informe)),
            cobertura=cobertura,
            falta=None,
            alcance=self._alcance(informe),
        )

    def _unidad(self, informe: str) -> str:
        if informe in {"indice-calidad-historico", "completitud-campos-criticos"}:
            return "ratio"
        if "impacto" in informe:
            return "casos"
        return "%"

    def _alcance(self, informe: str) -> str | None:
        return {
            "indice-calidad-historico": ALCANCE_INDICE,
            "patron-horario-climatico": ALCANCE_CLIMA,
            "impacto-vial-por-zona": ALCANCE_VIAL,
        }.get(informe)

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
