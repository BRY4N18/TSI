"""Reglas de texto del catálogo OE1: mensualizado, sin geografía, sin cobro, sin E1-05/07/08."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "estrategicos/oe1"
DIMS_CON_FINAL = ("dim_cliente", "dim_plan", "dim_etapa_onboarding")
HECHOS_CON_FINAL = ("hecho_suscripcion",)
HECHOS_SIN_FINAL = ("hecho_factura", "hecho_transicion_embudo", "hecho_onboarding")
PROHIBIDOS = (
    "idpais",
    "idestado",
    "tiene_metodo_pago",
    "metodo_pago_caduca",
    "CREATE TABLE",
    "ALTER TABLE",
)
BLOQUEADOS_SQL = ("e1_05", "e1_07", "e1_08")


def consultas():
    return [(n, cargar(n, departamento=DEPARTAMENTO)) for n in listar(DEPARTAMENTO)]


def sin_comentarios(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))


def _apariciones(cuerpo: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", cuerpo, re.I)
    ]


class TestCatalogoOe1:
    def test_son_diez_consultas(self):
        assert len(listar(DEPARTAMENTO)) == 10

    def test_no_existen_bloqueados(self):
        nombres = listar(DEPARTAMENTO)
        for prefijo in BLOQUEADOS_SQL:
            assert not any(prefijo in n for n in nombres)

    def test_final_en_dimensiones_y_suscripcion(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in DIMS_CON_FINAL + HECHOS_CON_FINAL:
                if re.search(rf"\b{tabla}\b", cuerpo):
                    assert all(_apariciones(cuerpo, tabla)), f"{nombre} {tabla} sin FINAL"

    def test_sin_final_en_hechos_de_flujo(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in HECHOS_SIN_FINAL:
                assert not any(_apariciones(cuerpo, tabla)), f"{nombre} FINAL sobre {tabla}"

    def test_forma(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            assert "SELECT *" not in cuerpo.upper()
            assert re.search(r"ORDER BY", cuerpo, re.IGNORECASE)
            assert "{desde:Date}" in cuerpo and "{hasta:Date}" in cuerpo
            assert "{granularidad:String}" in cuerpo

    def test_sin_geografia_ni_cobro_ni_ddl(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", cuerpo))
            for prohibido in ("idpais", "idestado", "tiene_metodo_pago", "metodo_pago_caduca"):
                assert prohibido not in ids, nombre
            assert "CREATE TABLE" not in cuerpo.upper()
            assert "ALTER TABLE" not in cuerpo.upper()

    def test_mrr_usa_precio_mensualizado(self):
        sql = sin_comentarios(cargar("e1_01_mrr_mensual", departamento=DEPARTAMENTO))
        assert "precio_mensualizado" in sql
        assert re.search(r"sum\s*\(\s*s\.precio\s*\)", sql, re.I) is None
