from unittest.mock import MagicMock

import pytest

from core.repositories.informes_tacticos.rendimiento_proveedor_repository import (
    RendimientoProveedorRepository,
)


@pytest.mark.repository
class TestRendimientoProveedorRepository:
    def test_returns_rows_distinguishing_providers(self):
        ch = MagicMock()
        filas = [
            {"idcliente": 100, "pct_rechazo": 0.5, "tiempo_llegada_promedio_seg": 60.0, "pct_abortos": 0.0, "total_despachos": 2},
            {"idcliente": 200, "pct_rechazo": 0.0, "tiempo_llegada_promedio_seg": 120.0, "pct_abortos": 0.0, "total_despachos": 1},
        ]
        ch.query.side_effect = [filas, [{"ultima": "2026-08-02 05:00:00"}]]
        pinot = MagicMock()
        pinot.query.return_value = [
            {"idcliente": 100, "nombre": "Proveedor Uno"},
            {"idcliente": 200, "nombre": "Proveedor Dos"},
        ]
        repo = RendimientoProveedorRepository(clickhouse=ch, pinot=pinot)

        rows, ultima = repo.consultar("2026-07-01", "2026-07-31")

        assert {r["idcliente"] for r in rows} == {100, 200}
        assert {r["idcliente"]: r["proveedor_nombre"] for r in rows} == {
            100: "Proveedor Uno",
            200: "Proveedor Dos",
        }

    def test_returns_none_when_never_ran(self):
        ch = MagicMock()
        ch.query.side_effect = [[], [{"ultima": None}]]
        repo = RendimientoProveedorRepository(clickhouse=ch, pinot=MagicMock())

        rows, ultima = repo.consultar("2026-07-01", "2026-07-31")

        assert rows is None
        assert ultima is None
