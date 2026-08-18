"""Partner sin precio de excedente se declara, no desaparece."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import Oe2Service


class TestUs2NoTarificables:
    def test_fila_no_tarificable_presente(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {
                    "partner": "SinPlan",
                    "llamadas": 5,
                    "cupo": 100,
                    "precio_unitario": None,
                    "no_tarificable": 1,
                    "importe_facturable": None,
                }
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "excedente-facturable",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        assert resultado.data[0]["no_tarificable"] == 1
        assert resultado.data[0]["partner"] == "SinPlan"
