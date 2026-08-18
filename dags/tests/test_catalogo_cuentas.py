"""T023–T024 — reglas del catálogo de Cuentas, sobre el **texto**."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "cuentas"
INFORMES = listar(DEPARTAMENTO)

CON_FINAL = (
    "dim_cliente",
    "dim_plan",
    "dim_rol",
    "dim_usuario_rol",
    "dim_usuario_organizacion",
    "dim_etapa_onboarding",
)
SIN_FINAL = ("hecho_onboarding", "hecho_sesion")

IDENTIDAD = (
    "token", "correo", "email", "telefono", "genero", "nacimiento",
    "identificacion", "nit", "razon_social", "nombre_comercial",
    "refresh_token", "admin_local_id",
)


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
    assert INFORMES, "el catálogo de Cuentas está vacío"
    assert len(INFORMES) == 9, (
        f"se esperaban 9 consultas y hay {len(INFORMES)}: {INFORMES}"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_regla_de_version_final(informe):
    texto = cuerpo(informe)
    for tabla in CON_FINAL:
        apariciones = _apariciones(texto, tabla)
        if not apariciones:
            continue
        assert all(apariciones), (
            f"'{informe}' toca {tabla} sin forzar la versión final"
        )
    for tabla in SIN_FINAL:
        assert not any(_apariciones(texto, tabla)), (
            f"'{informe}' pide FINAL sobre {tabla}, que es de transacción"
        )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_nombra_identidad(informe):
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    for ident in ids:
        for prohibida in IDENTIDAD:
            assert prohibida not in ident, (
                f"'{informe}' nombra '{ident}', que contiene '{prohibida}'"
            )


@pytest.mark.parametrize("informe", INFORMES)
def test_idusuario_solo_en_roles(informe):
    """La clave puede usarse al unir; no puede salir salvo en roles."""
    aliases = {
        a.lower()
        for a in re.findall(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", cuerpo(informe), re.I)
    }
    if informe == "ot18_roles_incompatibles":
        assert "idusuario" in identificadores(cuerpo(informe))
        return
    assert "idusuario" not in aliases, (
        f"'{informe}' publica idusuario: solo el informe de roles puede"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_forma_de_la_consulta(informe):
    texto = cuerpo(informe)
    assert re.search(r"^ORDER BY", texto, re.MULTILINE), f"'{informe}' no ordena"
    assert "SELECT *" not in texto.upper()
    assert "{hasta:Date}" in texto
    assert "{desde:Date}" in texto
