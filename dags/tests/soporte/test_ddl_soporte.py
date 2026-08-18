"""T008, T009 — las cinco tablas de Soporte y la exclusión de texto."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib import ddl  # noqa: E402

PROHIBIDAS = ("asunto", "descripcion", "mensaje", "es_nota_interna", "nombre_agente")

REPLACING = (
    ddl.ensure_dim_sla_config,
    ddl.ensure_dim_servicio,
    ddl.ensure_dim_estado_soporte,
    ddl.ensure_hecho_ticket,
)
MERGE = (ddl.ensure_hecho_accion_ticket,)


def _sql_de(fn) -> str:
    src = inspect.getsource(fn)
    inicio = src.find("CREATE TABLE")
    return src[inicio:] if inicio >= 0 else src


def test_las_cinco_tablas_existen_en_el_ddl():
    for tabla in (
        "dim_sla_config", "dim_servicio", "dim_estado_soporte",
        "hecho_ticket", "hecho_accion_ticket",
    ):
        src = inspect.getsource(getattr(ddl, f"ensure_{tabla}"))
        assert f"CREATE TABLE IF NOT EXISTS {tabla}" in src


def test_hecho_accion_es_mergetree_y_el_resto_replacing():
    for fn in REPLACING:
        assert "ReplacingMergeTree(version)" in _sql_de(fn)
    src = _sql_de(ddl.ensure_hecho_accion_ticket)
    assert "ENGINE = MergeTree()" in src
    assert "ReplacingMergeTree" not in src


def test_ninguna_tabla_de_hechos_declara_texto_de_ticket():
    for fn in (ddl.ensure_hecho_ticket, ddl.ensure_hecho_accion_ticket):
        src = _sql_de(fn).lower()
        for columna in PROHIBIDAS:
            assert columna not in src, f"{fn.__name__} declara {columna}"
