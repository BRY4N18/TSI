"""p95 nulo bajo muestra_minima=20; aparece si el umbral baja a 1."""

from __future__ import annotations

from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import Oe2Service

from datetime import date


def _periodo():
    return PeriodoEstrategico(
        date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False
    )


class TestUs1P95Ausente:
    def test_el_servicio_publica_la_fila_con_p95_nulo(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {
                    "periodo": "2026-01",
                    "endpoint_path": "/v1/accidentes",
                    "muestras": 2,
                    "latencia_media_ms": 40.0,
                    "latencia_p95_ms": None,
                    "percentil_fiable": 0,
                }
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "latencia-por-endpoint", _periodo(), extra={"muestra_minima": 20}
        )
        assert resultado.data[0]["latencia_p95_ms"] is None
        assert resultado.data[0]["percentil_fiable"] == 0
        assert repo.ejecutar_con_comparacion.call_args.kwargs["parametros"][
            "muestra_minima"
        ] == 20
