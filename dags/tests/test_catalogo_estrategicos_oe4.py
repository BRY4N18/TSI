"""Reglas de texto del catálogo OE4: FINAL, sin región, sin SELECT *, sin coordenadas."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "estrategicos/oe4"
TABLAS_CON_FINAL = ("hecho_accidente", "dim_severidad", "dim_geografia")
TABLAS_SIN_FINAL = ("hecho_evidencia",)


def consultas():
    return [(n, cargar(n, departamento=DEPARTAMENTO)) for n in listar(DEPARTAMENTO)]


def sin_comentarios(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))


def _apariciones(cuerpo: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", cuerpo)
    ]


class TestCatalogoOe4:
    def test_son_nueve_consultas(self):
        assert len(listar(DEPARTAMENTO)) == 9

    def test_final_en_acumulados(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_CON_FINAL:
                if re.search(rf"\b{tabla}\b", cuerpo):
                    assert all(_apariciones(cuerpo, tabla)), f"{nombre} {tabla} sin FINAL"

    def test_sin_final_en_evidencia(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            for tabla in TABLAS_SIN_FINAL:
                assert not any(_apariciones(cuerpo, tabla)), f"{nombre} FINAL sobre {tabla}"

    def test_sin_dim_region(self):
        for nombre, sql in consultas():
            for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sin_comentarios(sql)):
                assert ident.lower() != "dim_region", nombre
                assert "region" not in ident.lower(), f"{nombre} {ident}"

    def test_forma(self):
        for nombre, sql in consultas():
            cuerpo = sin_comentarios(sql)
            assert "SELECT *" not in cuerpo.upper()
            assert re.search(r"^ORDER BY", cuerpo, re.MULTILINE | re.IGNORECASE)
            assert "{desde:Date}" in cuerpo and "{hasta:Date}" in cuerpo

    def test_sin_coordenadas(self):
        prohibidas = {"latitud", "longitud", "idusuario", "nombres", "apellidos"}
        for nombre, sql in consultas():
            ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sin_comentarios(sql)))
            assert not (ids & prohibidas), nombre
