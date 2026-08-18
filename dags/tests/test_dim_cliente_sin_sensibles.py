"""T008 — `dim_cliente` no contiene medios de cobro ni dato fiscal (SC-009)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_cliente import (  # noqa: E402
    CONSULTA_CLIENTES,
    CONSULTA_METODOS,
    CONSULTA_ONBOARDING,
    construir,
)


PROHIBIDAS = (
    "nit", "token", "ultimosdigitos", "ultimos_digitos", "idmetodopago",
    "tokenpasarela", "tarjeta", "nit_identificacion",
)


def test_las_consultas_no_piden_dato_sensible():
    texto = CONSULTA_CLIENTES + CONSULTA_METODOS + CONSULTA_ONBOARDING
    bajo = texto.lower().replace("_", "")
    for prohibida in PROHIBIDAS:
        assert prohibida.replace("_", "") not in bajo, prohibida


def test_el_construido_no_lleva_columnas_sensibles():
    ahora = datetime(2026, 8, 17, 12, 0, 0)
    filas = construir(
        {
            "clientes": [{
                "idcliente": 1,
                "razon_social": "Acme",
                "nombre": "Acme",
                "tipo": "aseguradora",
                "estado": "Activo",
                "estado_onboarding": "Completado",
                "fecha_inicio_contrato": 1786622400000,
            }],
            "metodos": [{
                "idcliente": 1,
                "fechaexpiracion": 1786622400000,
                "activo": True,
            }],
        },
        ahora,
    )
    claves = set(filas[0])
    for prohibida in PROHIBIDAS:
        assert prohibida not in claves
    assert filas[0]["tiene_metodo_pago"] == 1
    assert filas[0]["metodo_pago_caduca"] is not None
    assert "tokenpasarela" not in claves
    assert filas[0]["cohorte_alta"] is not None
    assert filas[0]["motivo_baja"] is None
    assert "nit_identificacion" not in claves
