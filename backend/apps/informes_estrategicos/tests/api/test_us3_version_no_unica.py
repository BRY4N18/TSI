"""Dos servicios con v1 son dos agrupaciones."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe2_service import Oe2Service


class TestUs3VersionNoUnica:
    def test_dos_filas_v1(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [
                {"servicio": "accidentes", "version": "v1", "llamadas": 10, "version_es_derivada": 1},
                {"servicio": "despacho", "version": "v1", "llamadas": 8, "version_es_derivada": 1},
            ],
            None,
        )
        resultado = Oe2Service(repositorio=repo).calcular(
            "adopcion-versiones",
            PeriodoEstrategico(date(2026, 1, 1), date(2026, 1, 31), "mes", parcial=False),
        )
        assert len(resultado.data) == 2
        assert {f["servicio"] for f in resultado.data} == {"accidentes", "despacho"}
