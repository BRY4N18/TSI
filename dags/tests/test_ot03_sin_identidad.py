"""T057 — ningún informe de OT03 devuelve identidad del prospecto."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    ID_PROSPECTO_PRUEBA,
    asegurar_hechos_ventas_crm,
    ejecutar_ventas_crm,
    insertar,
    limpiar_ventas_crm,
    prospecto_de_prueba,
    requiere_modelo,
)

INFORMES = [n for n in listar("ventas_crm") if n.startswith("ot03_")]

DE_PERSONA = (
    "nombres", "apellidos", "gmail", "correo", "telefono", "cargo",
    "idusuario", "usuario",
)


def _cuerpo(nombre: str) -> str:
    return "\n".join(
        l for l in cargar(nombre, departamento="ventas_crm").splitlines()
        if not l.strip().startswith("--")
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_el_texto_no_nombra_identidad(informe):
    ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", re.sub(r"'[^']*'", " ", _cuerpo(informe))))
    for identificador in ids:
        bajo = identificador.lower()
        for prohibida in DE_PERSONA:
            assert prohibida not in bajo, f"'{informe}' nombra '{identificador}'"


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [prospecto_de_prueba(ID_PROSPECTO_PRUEBA + 100)])
    insertar("hecho_interaccion_demo", [
        {
            "idinteraccion": 1,
            "fecha": FECHA_DE_PRUEBA,
            "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
            "idprospecto": ID_PROSPECTO_PRUEBA + 100,
            "empresa": "Empresa prueba",
            "canal": "Web",
            "tipo_evento": "visita",
            "seccion": "planes",
            "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        }
    ])
    insertar("hecho_notificacion_ventas", [
        {
            "idnotificacion": 1,
            "fecha": FECHA_DE_PRUEBA,
            "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
            "idprospecto": ID_PROSPECTO_PRUEBA + 100,
            "empresa": "Empresa prueba",
            "regla_disparada": "inactividad",
            "canal_aviso": "email",
            "hubo_avance": 0,
            "segundos_a_reaccion": None,
            "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        }
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
@pytest.mark.parametrize("informe", INFORMES)
def test_el_resultado_no_identifica_a_una_persona(escenario, informe):
    filas = ejecutar_ventas_crm(informe)
    if not filas:
        pytest.skip(f"'{informe}' no devolvio filas en el escenario")
    for columna in filas[0]:
        bajo = columna.lower()
        for prohibida in DE_PERSONA:
            assert prohibida not in bajo, f"'{informe}' devuelve '{columna}'"
