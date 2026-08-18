"""4xx y 5xx no se suman en un error total."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import Oe2Service


class TestUs14xxVs5xx:
    def test_no_hay_total_que_suma_clases(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {"periodo": "2026-01", "clase_http": "4xx", "llamadas": 3, "denominador": 18, "pct": 0.16},
                {"periodo": "2026-01", "clase_http": "5xx", "llamadas": 1, "denominador": 18, "pct": 0.05},
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "taxonomia-errores",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        clases = {f["clase_http"] for f in resultado.data}
        assert "4xx" in clases and "5xx" in clases
        assert not any("total" in k for fila in resultado.data for k in fila)
