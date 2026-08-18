"""Cobertura, alcance y 404 de OE5 con repositorio simulado."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe5_service import Oe5Service
from apps.informes_estrategicos.services.oe6_service import InformeDesconocido


def _periodo():
    return PeriodoEstrategico(
        date(2026, 1, 1), date(2026, 3, 31), "trimestre", parcial=False
    )


def test_nps_es_desconocido():
    with pytest.raises(InformeDesconocido):
        Oe5Service(MagicMock()).calcular("nps-satisfaccion", _periodo())


def test_referencia_oe1_es_desconocida():
    with pytest.raises(InformeDesconocido):
        Oe5Service(MagicMock()).calcular("tasa-renovacion", _periodo())


def test_sla_cobertura_parcial_bajo_umbral():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"periodo": "2026-01", "con_compromiso": 14, "pct_cumplimiento": 0.9}],
        None,
    )
    resultado = Oe5Service(repo).calcular("cumplimiento-sla", _periodo())
    assert resultado.cobertura == "parcial"
    assert any("muestra" in f for f in resultado.falta)
    assert "compromiso" in (resultado.alcance or "").lower()
    assert resultado.objetivo["cumple"] is None


def test_nrr_alcance_nombra_descomposicion():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"expansion": 10, "contraccion": 2, "churn": 1, "nrr": 1.05, "recuento": 4}],
        None,
    )
    resultado = Oe5Service(repo).calcular("retencion-neta-ingresos", _periodo())
    assert "expansi" in (resultado.alcance or "").lower()
    assert resultado.objetivo["cumple"] is None


def test_riesgo_falta_si_fuente_vacia():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [
            {
                "idcliente": 1,
                "n_senales": 2,
                "n_fuente_api": 0,
                "n_fuente_tickets": 14,
                "n_fuente_cobro": 6,
                "n_fuente_sesiones": 0,
            }
        ],
        None,
    )
    resultado = Oe5Service(repo).calcular("cuentas-en-riesgo", _periodo())
    assert resultado.cobertura == "parcial"
    assert any("API" in f for f in resultado.falta)
    assert any("sesiones" in f for f in resultado.falta)
    assert "dos" in (resultado.alcance or "").lower()


def test_agente_alcance_es_carga():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"idagente": 3, "asignados": 4}],
        None,
    )
    resultado = Oe5Service(repo).calcular("rendimiento-por-agente", _periodo())
    assert "carga" in (resultado.alcance or "").lower()
