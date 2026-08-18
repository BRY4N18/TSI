"""E2-03: acceso concedido en el denominador; sin llamada no entra al numerador."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import Oe2Service


class TestUs1DenominadorAcceso:
    def test_partners_con_acceso_es_el_denominador(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {
                    "periodo": "2026-01",
                    "partners_con_acceso": 4,
                    "partners_con_llamada": 2,
                    "pct_adopcion": 0.5,
                }
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "integraciones-activas",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        fila = resultado.data[0]
        assert fila["partners_con_acceso"] == 4
        assert fila["partners_con_llamada"] == 2
        assert fila["partners_con_llamada"] < fila["partners_con_acceso"]
