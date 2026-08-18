"""E2-08 declara alcance facturable y publica componentes."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import ALCANCE_EXCEDENTE, Oe2Service


class TestUs2AlcanceFacturable:
    def test_meta_alcance_niega_cobro(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {
                    "periodo": "2026-01",
                    "partner": "A",
                    "llamadas": 30,
                    "cupo": 20,
                    "precio_unitario": 0.05,
                    "no_tarificable": 0,
                    "importe_facturable": 0.5,
                }
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "excedente-facturable",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        assert resultado.alcance == ALCANCE_EXCEDENTE
        fila = resultado.data[0]
        assert {"llamadas", "cupo", "precio_unitario", "importe_facturable"} <= set(fila)
        assert "cobrado" not in str(resultado.alcance).lower()
