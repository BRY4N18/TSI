"""T021–T022, T061 — reglas del catálogo de Partners, sobre el **texto**."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "partners"
INFORMES = listar(DEPARTAMENTO)

CON_FINAL = (
    "dim_partner",
    "dim_credencial_api",
    "dim_version_contrato",
    "dim_cliente",
    "hecho_accidente",
)
SIN_FINAL = ("hecho_llamada_api", "hecho_cambio_acceso")

SENSIBLES = (
    "iporigen", "client_secret", "contacto_tecnico", "ejecutado_por",
    "gmail", "hash",
)
CLASES = ("limite_cupo", "autorizacion", "error_servicio")
GEOGRAFIA = ("zona", "zonas_geograficas", "alcance_geografico", "idseveridad")


def cuerpo(nombre: str) -> str:
    return "\n".join(
        l for l in cargar(nombre, departamento=DEPARTAMENTO).splitlines()
        if not l.strip().startswith("--")
    )


def identificadores(sql: str) -> set[str]:
    sin_literales = re.sub(r"'[^']*'", " ", sql)
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sin_literales))


def _apariciones(texto: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", texto)
    ]


def test_el_catalogo_no_esta_vacio():
    assert len(INFORMES) == 13, INFORMES


@pytest.mark.parametrize("informe", INFORMES)
def test_la_regla_de_version_final(informe):
    texto = cuerpo(informe)
    for tabla in CON_FINAL:
        apariciones = _apariciones(texto, tabla)
        if not apariciones:
            continue
        assert all(apariciones), f"'{informe}' toca {tabla} sin FINAL"
    for tabla in SIN_FINAL:
        assert not any(_apariciones(texto, tabla)), (
            f"'{informe}' pide FINAL sobre {tabla}"
        )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_nombra_sensibles(informe):
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    for ident in ids:
        for p in SENSIBLES:
            assert p not in ident, f"'{informe}' nombra '{ident}'"


@pytest.mark.parametrize("informe", INFORMES)
def test_no_suma_clases_de_resultado(informe):
    texto = cuerpo(informe)
    if "clase_resultado" not in texto:
        return
    assert "clase_resultado != 'exito'" in texto or "clase_resultado" in texto
    if "countIf" in texto and all(c in texto for c in CLASES):
        pytest.fail(f"'{informe}' parece sumar las tres clases en un solo recuento")


@pytest.mark.parametrize("informe", INFORMES)
def test_no_hay_alcance_geografico(informe):
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    for ident in ids:
        for g in GEOGRAFIA:
            assert g not in ident, (
                f"'{informe}' nombra '{ident}': el alcance geográfico está fuera"
            )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_forma_de_la_consulta(informe):
    texto = cuerpo(informe)
    assert re.search(r"^ORDER BY", texto, re.MULTILINE), informe
    assert "SELECT *" not in texto.upper()
    assert "{hasta:Date}" in texto
    assert "{desde:Date}" in texto
