from unittest.mock import MagicMock

import pytest
from django.http import QueryDict

from apps.informes_tacticos.periodo import parse_periodo
from apps.informes_tacticos.services.seguimiento_informes_service import SeguimientoInformesService


def _periodo():
    qd = QueryDict(mutable=True)
    qd["desde"] = "2026-07-01"
    qd["hasta"] = "2026-07-31"
    return parse_periodo(qd)


@pytest.mark.service
class TestSeguimientoInformesService:
    def test_tiempo_asignado_cerrado_delegates(self):
        repo = MagicMock()
        repo.tiempo_asignado_cerrado.return_value = [{"idunidademergencia": 1, "promedio_segundos": 5.0}]
        service = SeguimientoInformesService(repository=repo)
        periodo = _periodo()

        result = service.tiempo_asignado_cerrado(periodo)

        repo.tiempo_asignado_cerrado.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idunidademergencia": 1, "promedio_segundos": 5.0}]

    def test_cierres_forzados_delegates(self):
        repo = MagicMock()
        repo.cierres_forzados.return_value = [{"periodo": "2026-07-01", "pct_cierres_forzados": 0.2}]
        service = SeguimientoInformesService(repository=repo)
        periodo = _periodo()

        result = service.cierres_forzados(periodo)

        repo.cierres_forzados.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, "day")
        assert result == [{"periodo": "2026-07-01", "pct_cierres_forzados": 0.2}]

    def test_abortos_perdidas_delegates(self):
        repo = MagicMock()
        repo.abortos_perdidas.return_value = [{"idunidademergencia": 1, "pct_abortos_perdidas": 0.1}]
        service = SeguimientoInformesService(repository=repo)
        periodo = _periodo()

        result = service.abortos_perdidas(periodo)

        repo.abortos_perdidas.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idunidademergencia": 1, "pct_abortos_perdidas": 0.1}]
