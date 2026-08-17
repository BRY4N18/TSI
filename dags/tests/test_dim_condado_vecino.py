"""T010, T011 — dim_condado_vecino es aditiva, simétrica y tiene fila desconocida."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.desconocido import (  # noqa: E402
    ETIQUETA_DESCONOCIDA,
    FILAS_DESCONOCIDAS,
    ID_DESCONOCIDO,
)
from lib.dimensiones.dim_condado_vecino import construir  # noqa: E402
from tests.almacen import contar, requiere_modelo  # noqa: E402

AHORA = datetime(2026, 8, 16, 12, 0, 0)
PARTICION_DE_PRUEBA = 209912


def _reales(tabla: str) -> int:
    return contar(
        f"SELECT count() AS n FROM {tabla} FINAL "
        f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
    )


class TestConstruir:
    def test_resuelve_nombres_y_es_simetrica(self):
        pares = construir(
            [{"idcondado": 1, "idcondadovecino": 2}, {"idcondado": 2, "idcondadovecino": 1}],
            [{"idcondado": 1, "condado": "A"}, {"idcondado": 2, "condado": "B"}],
            AHORA,
        )
        assert len(pares) == 2
        ids = {(p["idcondado"], p["idcondadovecino"]) for p in pares}
        assert ids == {(1, 2), (2, 1)}
        assert {p["condado"] for p in pares} == {"A", "B"}

    def test_un_vecino_sin_catalogo_cae_en_desconocido(self):
        pares = construir(
            [{"idcondado": 1, "idcondadovecino": 99}],
            [{"idcondado": 1, "condado": "A"}],
            AHORA,
        )
        assert pares[0]["idcondadovecino"] == ID_DESCONOCIDO
        assert pares[0]["condado_vecino"] == ETIQUETA_DESCONOCIDA

    def test_la_fila_desconocida_existe(self):
        fila = FILAS_DESCONOCIDAS["dim_condado_vecino"](AHORA)
        assert fila["idcondado"] == ID_DESCONOCIDO
        assert fila["idcondadovecino"] == ID_DESCONOCIDO
        assert fila["condado"] == ETIQUETA_DESCONOCIDA


@requiere_modelo
class TestCrecimientoAditivo:
    """T010 — cargar la dimensión no mueve hecho_accidente ni hecho_despacho."""

    def test_los_casos_siguen_igual(self):
        from lib.ddl import ensure_dim_condado_vecino

        antes = _reales("hecho_accidente")
        ensure_dim_condado_vecino()
        assert _reales("hecho_accidente") == antes

    def test_los_despachos_siguen_igual(self):
        from lib.ddl import ensure_dim_condado_vecino

        antes = _reales("hecho_despacho")
        ensure_dim_condado_vecino()
        assert _reales("hecho_despacho") == antes


@requiere_modelo
class TestDimensionCargada:
    """T011 — 2 filas simétricas en la línea base, más la desconocida."""

    def test_es_simetrica_en_el_almacen(self):
        from lib.clickhouse_http_client import query_clickhouse

        filas = query_clickhouse(
            "SELECT idcondado, idcondadovecino FROM dim_condado_vecino FINAL "
            "WHERE idcondado != -1 ORDER BY idcondado"
        )
        if not filas:
            pytest.skip("dim_condado_vecino aún no está cargada")
        pares = {(int(f["idcondado"]), int(f["idcondadovecino"])) for f in filas}
        assert pares == {(1, 2), (2, 1)}
