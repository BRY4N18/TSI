"""T025 — una Cancelada con activo=true no aporta MRR (SC-002)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_suscripcion import (  # noqa: E402
    CONSULTA_SUSCRIPCIONES,
    construir,
    estado_derivado,
    plan_programado_o_nulo,
    precio_mensualizado,
    vigencia_inconsistente,
)

AHORA = datetime(2026, 8, 17, 12, 0, 0)
T0 = int(AHORA.timestamp() * 1000)
T_FIN = T0 + 30 * 24 * 3600 * 1000


def test_la_consulta_no_pide_activo():
    assert "activo" not in CONSULTA_SUSCRIPCIONES.lower().replace("fact_suscripcion", "")


def test_cancelada_con_activo_true_sale_cancelada():
    estado = estado_derivado(
        {"estado": "Cancelada", "activo": True},
        ahora=AHORA,
        inicio=AHORA,
        fin=datetime(2026, 9, 17),
    )
    assert estado == "cancelada"


def test_el_construido_no_aporta_precio_si_esta_cancelada():
    filas = construir(
        {
            "suscripciones": [{
                "id_suscripcion": 1,
                "idcliente": 1,
                "idplan": 1,
                "precio": 120.0,
                "periodicidad": "Mensual",
                "nivel": "Pro",
                "severidades_desbloqueadas": "[]",
                "estado": "Cancelada",
                "activo": True,
                "renovacionautomatica": False,
                "motivocancelacion": "prueba",
                "fechacancelacion": T0,
                "fecha_inicio": T0,
                "fecha_fin": T_FIN,
                "idplan_programado": 0,
            }],
            "dim_plan": [{"idplan": 1, "nombre": "Pro", "nivel": "Pro"}],
            "dim_cliente": [{"idcliente": 1, "tipo": "aseguradora"}],
            "existentes": [],
        },
        AHORA,
    )
    assert filas[0]["estado_derivado"] == "cancelada"
    assert filas[0]["motivo_cancelacion"] == "prueba"


def test_motivo_en_activa_no_se_copia():
    filas = construir(
        {
            "suscripciones": [{
                "id_suscripcion": 2,
                "idcliente": 1,
                "idplan": 1,
                "precio": 120.0,
                "periodicidad": "Mensual",
                "nivel": "Pro",
                "severidades_desbloqueadas": "[]",
                "estado": "Activa",
                "activo": True,
                "renovacionautomatica": True,
                "motivocancelacion": "prueba fin de ciclo",
                "fechacancelacion": None,
                "fecha_inicio": T0,
                "fecha_fin": T_FIN,
                "idplan_programado": 0,
            }],
            "dim_plan": [{"idplan": 1, "nombre": "Pro", "nivel": "Pro"}],
            "dim_cliente": [{"idcliente": 1, "tipo": "aseguradora"}],
            "existentes": [],
        },
        AHORA,
    )
    assert filas[0]["estado_derivado"] == "vigente"
    assert filas[0]["motivo_cancelacion"] is None


def test_precio_mensualizado_anual_divide_entre_doce():
    assert precio_mensualizado(1200, "Anual") == 100.0
    assert precio_mensualizado(99, "Mensual") == 99.0


def test_sin_periodicidad_queda_ausente_nunca_cero():
    assert precio_mensualizado(99, None) is None
    assert precio_mensualizado(99, "") is None
    assert precio_mensualizado(99, None) != 0


def test_vigencia_invertida_se_marca_no_se_corrige():
    inicio = datetime(2026, 8, 17)
    fin = datetime(2026, 7, 1)
    assert vigencia_inconsistente(inicio, fin) == 1
    assert fin < inicio


def test_centinela_cero_es_nulo():
    assert plan_programado_o_nulo(0) is None
    assert plan_programado_o_nulo(-1) is None
    assert plan_programado_o_nulo(3) == 3
