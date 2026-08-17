"""Acceso de **solo lectura** al modelo analítico para la capa estratégica.

Envuelve `ModeloRepository`: no reimplementa el cliente ni el catálogo. Lo que
añade es la **doble ejecución** de la comparación (research D4): la misma
consulta, dos ventanas, composición en el servicio. Meter las dos ventanas en
un `CASE` duplicaría cada percentil y rompería el contraste fila a fila con la
capa táctica.
"""

from __future__ import annotations

from typing import Any

from core.repositories.informes_tacticos.modelo_repository import ModeloRepository


class ModeloEstrategicoRepository:
    """Ejecuta consultas del catálogo, una o dos veces según haya comparación."""

    def __init__(self, inner: ModeloRepository | None = None):
        self._inner = inner or ModeloRepository()

    def ejecutar(
        self,
        consulta: str,
        *,
        departamento: str,
        parametros: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._inner.ejecutar(
            consulta, departamento=departamento, parametros=parametros
        )

    def ejecutar_con_comparacion(
        self,
        consulta: str,
        *,
        departamento: str,
        parametros: dict[str, Any],
        parametros_anterior: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
        actual = self.ejecutar(
            consulta, departamento=departamento, parametros=parametros
        )
        if parametros_anterior is None:
            return actual, None
        anterior = self.ejecutar(
            consulta, departamento=departamento, parametros=parametros_anterior
        )
        return actual, anterior
