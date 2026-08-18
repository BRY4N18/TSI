"""E2-01 y E2-02 salen parciales y nombran el precio que falta."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import FALTA_PRECIO_PLAN, Oe2Service


class TestUs2Parciales:
    def test_participacion_es_parcial(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = ([{"periodo": "2026-01", "llamadas": 18}], None)
        resultado = Oe2Service(repositorio=repo).calcular(
            "participacion-ingresos-api",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        assert resultado.cobertura == "parcial"
        assert resultado.falta == FALTA_PRECIO_PLAN

    def test_mrr_es_parcial(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = ([{"periodo": "2026-01", "linea": "plataforma", "monto": 10}], None)
        resultado = Oe2Service(repositorio=repo).calcular(
            "mrr-por-linea",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        assert resultado.cobertura == "parcial"
        assert any("precio" in f.lower() for f in resultado.falta)
