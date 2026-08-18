"""Cobertura, alcance y objetivo de OE1 con repositorio simulado."""

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe1_service import Oe1Service
from apps.informes_estrategicos.services.oe6_service import InformeDesconocido
import pytest


def _periodo():
    return PeriodoEstrategico(
        date(2026, 1, 1), date(2026, 3, 31), "trimestre", parcial=False
    )


def test_informe_bloqueado_es_desconocido():
    with pytest.raises(InformeDesconocido):
        Oe1Service(MagicMock()).calcular("cac-por-canal", _periodo())


def test_mrr_cobertura_parcial_bajo_umbral():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"periodo": "2026-01", "mrr": 400.0, "recuento": 4}],
        None,
    )
    resultado = Oe1Service(repo).calcular("mrr-mensual", _periodo())
    assert resultado.cobertura == "parcial"
    assert any("muestra" in f for f in resultado.falta)
    assert "cierre" in (resultado.alcance or "").lower()
    assert resultado.objetivo["cumple"] is None
    assert resultado.objetivo["tipo"] == "CALIBRAR"


def test_arr_alcance_nombra_extrapolacion():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"periodo": "2026-01", "mrr": 100.0, "arr": 1200.0, "recuento": 4}],
        None,
    )
    resultado = Oe1Service(repo).calcular("arr-proyeccion", _periodo())
    assert "extrapol" in (resultado.alcance or "").lower()
    assert resultado.objetivo["cumple"] is None


def test_churn_cobertura_completa_si_n_supera_umbral():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"cohorte_alta": "2025-01", "n": 40, "bajas": 2, "pct_churn": 0.05}],
        None,
    )
    resultado = Oe1Service(repo).calcular(
        "churn-por-cohorte", _periodo(), extra={"umbral_muestra": 20}
    )
    assert resultado.cobertura == "completa"
    assert resultado.falta is None


def test_mom_declara_dos_ventanas():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"periodo": "2026-01", "mrr": 100.0, "recuento": 4}],
        [{"periodo": "2025-10", "mrr": 80.0, "recuento": 4}],
    )
    resultado = Oe1Service(repo).calcular(
        "mrr-mensual", _periodo(), comparacion="mom"
    )
    assert resultado.comparacion["tipo"] == "mom"
    assert resultado.comparacion["ventana_anterior"] is not None


def test_embudo_alcance_nombra_transiciones():
    repo = MagicMock()
    repo.ejecutar_con_comparacion.return_value = (
        [{"etapa": "lead", "transiciones": 0}],
        None,
    )
    resultado = Oe1Service(repo).calcular("embudo-conversion", _periodo())
    assert "transicion" in (resultado.alcance or "").lower()
    assert resultado.cobertura == "parcial"
