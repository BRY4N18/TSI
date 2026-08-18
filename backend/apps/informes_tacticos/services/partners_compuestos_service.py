"""Servicio de los informes compuestos de Partners y API.

El Director Tecnológico y el Administrador entran. Un rol de partner no:
son cifras comparadas de todos los partners.
"""

from __future__ import annotations

from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "partners"

NOTA_MUESTRAS = (
    "Hay medidas calculadas sobre pocas llamadas; "
    "el percentil no es fiable por debajo del mínimo declarado."
)


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


CATALOGO: dict[str, str] = {
    "metricas-consumo": "ot09_metricas_consumo",
    "reporte-mensual-consumo": "ot09_reporte_mensual",
    "consumo-por-endpoint": "ot09_consumo_por_endpoint",
    "latencia-p95": "ot09_latencia_p95",
    "taxonomia-errores": "ot09_taxonomia_errores",
    "comparativa": "ot09_comparativa_partners",
    "participacion-ingresos-api": "ot09_participacion_ingresos_api",
    "motivo-credencial-inactiva": "ot08_motivo_credencial_inactiva",
    "tiempo-incorporacion": "ot08_tiempo_incorporacion",
    "adopcion-versiones": "ot08_adopcion_versiones",
    "tasa-rechazo-produccion": "ot08_tasa_rechazo_produccion",
    "clientes-integracion-activa": "ot10_clientes_integracion_activa",
    "volumen-expedientes": "ot10_volumen_expedientes",
}

INFORMES_MUESTRAS = frozenset({
    "latencia-p95",
    "metricas-consumo",
    "comparativa",
    "consumo-por-endpoint",
    "reporte-mensual-consumo",
})

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)


class PartnersCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def calcular(
        self,
        informe: str,
        periodo: Periodo,
        *,
        extra: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        extra = dict(extra or {})
        muestra_minima = extra.get("muestra_minima", 20)
        parametros: dict[str, Any] = {
            "desde": periodo.desde,
            "hasta": periodo.hasta,
            "percentil": extra.get("percentil", 95),
            "muestra_minima": muestra_minima,
            "mes": extra.get("mes") or "",
            "dias_aviso_expiracion": extra.get("dias_aviso_expiracion", 30),
        }
        filas = self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
        notas: dict[str, str] = {}
        if informe in INFORMES_MUESTRAS and any(
            int(f.get("percentil_fiable") or 1) == 0
            or int(f.get("muestras") or 0) < int(muestra_minima)
            for f in filas
        ):
            notas["nota_muestras"] = NOTA_MUESTRAS
        cuerpo = {
            "periodo": {"desde": periodo.desde, "hasta": periodo.hasta},
            "resultados": list(filas),
        }
        return cuerpo, notas
