"""Reglas de texto del catálogo OE2: detalle, no agregado; sin secretos; sin E2-06."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "estrategicos/oe2"
DIMS_CON_FINAL = ("dim_partner", "dim_plan", "dim_version_contrato")
HECHOS_SIN_FINAL = ("hecho_llamada_api", "hecho_factura")
AGREGADOS_PROHIBIDOS = (
    "hecho_api_agregado",
    "hecho_consumo_api_agregado",
    "fact_apiintegracion",
    "fact_consumoapi",
)
SECRETOS = ("ip", "client_secret", "hash", "contacto_tecnico", "latitud", "longitud")


def consultas():
    return [(n, cargar(n, departamento=DEPARTAMENTO)) for n in listar(DEPARTAMENTO)]


def sin_comentarios(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))


def _apariciones(cuerpo: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", cuerpo, re.I)
    ]


class TestCatalogoOe2:
    def test_son_diez_consultas(self):
        assert len(listar(DEPARTAMENTO)) == 10

    def test_no_existe_e2_06(self):
        nombres = listar(DEPARTAMENTO)
        assert not any("e2_06" in n for n in nombres)
        assert not any("disponibilidad" in n for n in nombres)

    def test_final_en_dimensiones(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in DIMS_CON_FINAL:
                if re.search(rf"\b{tabla}\b", cuerpo):
                    assert all(_apariciones(cuerpo, tabla)), f"{nombre} {tabla} sin FINAL"

    def test_sin_final_en_hechos(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in HECHOS_SIN_FINAL:
                assert not any(_apariciones(cuerpo, tabla)), f"{nombre} FINAL sobre {tabla}"

    def test_no_usa_agregado_de_consumo(self):
        for nombre, sql in consultas():
            bajo = sin_comentarios(sql).lower()
            for prohibida in AGREGADOS_PROHIBIDOS:
                assert prohibida not in bajo, f"{nombre} nombra {prohibida}"

    def test_forma(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            assert "SELECT *" not in cuerpo.upper()
            assert re.search(r"ORDER BY", cuerpo, re.IGNORECASE)
            assert "{desde:Date}" in cuerpo and "{hasta:Date}" in cuerpo

    def test_sin_secretos(self):
        for nombre, sql in consultas():
            ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sin_comentarios(sql)))
            assert not (ids & set(SECRETOS)), nombre

    def test_e2_09_agrupa_servicio_y_version(self):
        sql = sin_comentarios(cargar("e2_09_adopcion_versiones", departamento=DEPARTAMENTO))
        assert "GROUP BY periodo, servicio, version" in sql.replace("\n", " ")
