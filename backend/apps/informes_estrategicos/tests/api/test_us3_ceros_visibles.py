"""Comparativa incluye partners en cero."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import Oe2Service


class TestUs3CerosVisibles:
    def test_partner_en_cero_no_se_omite(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {"partner": "Activo", "llamadas": 10, "pct_error": 0.1, "errores": 1, "denominador": 10},
                {"partner": "Silencio", "llamadas": 0, "pct_error": None, "errores": 0, "denominador": 0},
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "comparativa-partners",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        assert any(f["llamadas"] == 0 for f in resultado.data)
