"""El servicio de crecimiento no consulta hecho_cambio_acceso."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import CATALOGO, Oe2Service


class TestUs3CrecimientoPrimera2xx:
    def test_consulta_es_crecimiento_no_acceso(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = ([{"periodo": "2026-01", "partners_nuevos": 1}], None)
        Oe2Service(repositorio=repo).calcular(
            "crecimiento-ecosistema",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        consulta = repo.ejecutar_con_comparacion.call_args.args[0]
        assert consulta == CATALOGO["crecimiento-ecosistema"]
        assert "cambio_acceso" not in consulta
