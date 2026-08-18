"""Reglas de texto del catálogo OE5: SLA con compromiso, sin prosa, sin E5-01/09/10/11/13/14."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "estrategicos/oe5"
DIMS_CON_FINAL = ("dim_cliente", "dim_plan", "dim_usuario_organizacion")
HECHOS_CON_FINAL = ("hecho_ticket", "hecho_suscripcion")
HECHOS_SIN_FINAL = (
    "hecho_factura",
    "hecho_solicitud_cambio_plan",
    "hecho_accion_ticket",
    "hecho_sesion",
    "hecho_llamada_api",
)
BLOQUEADOS_SQL = ("e5_01", "e5_09", "e5_10", "e5_11", "e5_13", "e5_14")


def consultas():
    return [(n, cargar(n, departamento=DEPARTAMENTO)) for n in listar(DEPARTAMENTO)]


def sin_comentarios(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))


def _apariciones(cuerpo: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", cuerpo, re.I)
    ]


class TestCatalogoOe5:
    def test_son_nueve_consultas(self):
        assert len(listar(DEPARTAMENTO)) == 9

    def test_no_existen_bloqueados(self):
        nombres = listar(DEPARTAMENTO)
        for prefijo in BLOQUEADOS_SQL:
            assert not any(prefijo in n for n in nombres)

    def test_final_en_dims_y_acumulados(self):
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

    def test_sin_prosa_ni_cobro_ni_ddl(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", cuerpo))
            for prohibido in ("asunto", "descripcion", "mensaje", "idmetodopago", "calificacion"):
                assert prohibido not in ids, nombre
            assert "CREATE TABLE" not in cuerpo.upper()
            assert "ALTER TABLE" not in cuerpo.upper()

    def test_sla_usa_compromiso(self):
        sql = sin_comentarios(cargar("e5_04_cumplimiento_sla", departamento=DEPARTAMENTO))
        assert "tiene_compromiso" in sql

    def test_nrr_nombra_expansion(self):
        sql = sin_comentarios(cargar("e5_02_retencion_neta_ingresos", departamento=DEPARTAMENTO))
        assert "expansion" in sql
        assert "contraccion" in sql
        assert "churn" in sql
        assert "dim_plan.precio" not in sql
