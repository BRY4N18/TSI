"""T026–T028 — reglas del catálogo de Suscripciones, sobre el **texto**."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "suscripciones"
INFORMES = listar(DEPARTAMENTO)

CON_FINAL = ("dim_plan", "dim_cliente", "hecho_suscripcion")
SIN_FINAL = ("hecho_factura", "hecho_solicitud_cambio_plan")

SENSIBLES = (
    "token", "tokenpasarela", "ultimosdigitos", "nit", "nit_identificacion",
    "idadminaprobador", "idadmin", "desglose_cargos", "motivo_anulacion",
    "motivo_rechazo", "idmetodopago",
)
API = ("llamadas", "api_calls", "api_call")


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
    assert INFORMES, "el catálogo de Suscripciones está vacío"
    assert len(INFORMES) == 13, (
        f"se esperaban 13 consultas y hay {len(INFORMES)}: {INFORMES}"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_lee_activo(informe):
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    assert "activo" not in ids, (
        f"'{informe}' nombra 'activo': esa columna no dice si está vigente"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_suma_monto_total_sin_signo(informe):
    texto = cuerpo(informe)
    if "monto_total" not in texto:
        return
    assert "monto_con_signo" in texto or "es_nota_credito" in texto, (
        f"'{informe}' nombra monto_total sin usar el signo ni separar notas"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_nombra_medio_fiscal_ni_admin(informe):
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    permitidos = {
        "tiene_metodo_pago", "metodo_pago_caduca", "caduca_en_dias",
        "nota_dimension_pendiente",
    }
    for ident in ids:
        if ident in permitidos:
            continue
        for prohibida in SENSIBLES:
            assert prohibida not in ident, (
                f"'{informe}' nombra '{ident}', que contiene '{prohibida}'"
            )


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_nombra_llamadas_api(informe):
    ids = {i.lower() for i in identificadores(cuerpo(informe))}
    for ident in ids:
        for prohibida in API:
            assert prohibida not in ident, (
                f"'{informe}' nombra '{ident}': el consumo de API es de Partners"
            )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_regla_de_version_final(informe):
    texto = cuerpo(informe)
    for tabla in CON_FINAL:
        apariciones = _apariciones(texto, tabla)
        assert all(apariciones), (
            f"'{informe}' toca {tabla} sin forzar la versión final"
        )
    for tabla in SIN_FINAL:
        assert not any(_apariciones(texto, tabla)), (
            f"'{informe}' pide FINAL sobre {tabla}, que es de transacción"
        )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_forma_de_la_consulta(informe):
    texto = cuerpo(informe)
    assert re.search(r"^ORDER BY", texto, re.MULTILINE), f"'{informe}' no ordena"
    assert "SELECT *" not in texto.upper()
    assert "{hasta:Date}" in texto
    assert "{desde:Date}" in texto
