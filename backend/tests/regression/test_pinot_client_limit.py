"""Regresión: Pinot recorta a 10 filas toda consulta sin LIMIT explícito.

El broker no señala el recorte de ninguna forma, así que un repositorio que
filtre o pagine en Python sobre el resultado devuelve datos incompletos sin
error. `PinotClient` debe garantizar el tope explícito por su cuenta.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.pinot.client import DEFAULT_QUERY_LIMIT, PinotClient


def _sql_enviado(sql: str, params: dict | None = None) -> str:
    """Ejecuta query() con el transporte mockeado y devuelve el SQL emitido."""
    with patch("core.pinot.client.requests.post") as post:
        post.return_value.json.return_value = {"resultTable": None}
        post.return_value.raise_for_status.return_value = None
        PinotClient(broker_url="http://pinot-broker:8099").query(sql, params)
        return post.call_args.kwargs["json"]["sql"]


@pytest.mark.unit
class TestPinotClientLimit:
    def test_query_when_sin_limit_agrega_el_tope_por_defecto(self):
        # Act
        enviado = _sql_enviado("SELECT * FROM Fact_Accidente WHERE activo = true")

        # Assert
        assert enviado.endswith(f"LIMIT {DEFAULT_QUERY_LIMIT}")

    def test_query_when_ya_tiene_limit_lo_respeta(self):
        # Act
        enviado = _sql_enviado("SELECT * FROM Fact_Accidente LIMIT 5")

        # Assert
        assert enviado.endswith("LIMIT 5")
        assert str(DEFAULT_QUERY_LIMIT) not in enviado

    def test_query_when_limit_multilinea_o_con_punto_y_coma_lo_respeta(self):
        # Act
        enviado = _sql_enviado(
            """
            SELECT * FROM Fact_Accidente
            WHERE activo = true
            ORDER BY fechahoraaccidente DESC
            LIMIT 20;
            """
        )

        # Assert
        assert enviado.endswith("LIMIT 20")

    def test_query_when_columna_se_llama_limit_igual_agrega_tope(self):
        # Arrange — "limit" como parte de un identificador no es cláusula LIMIT
        sql = "SELECT limite_unidades FROM Dim_Plan WHERE activo = true"

        # Act
        enviado = _sql_enviado(sql)

        # Assert
        assert enviado.endswith(f"LIMIT {DEFAULT_QUERY_LIMIT}")

    def test_query_when_hay_params_interpola_antes_de_medir_el_limit(self):
        # Act
        enviado = _sql_enviado(
            "SELECT * FROM Fact_Accidente WHERE idcalle = %(idcalle)s",
            {"idcalle": 7},
        )

        # Assert
        assert "idcalle = 7" in enviado
        assert enviado.endswith(f"LIMIT {DEFAULT_QUERY_LIMIT}")
