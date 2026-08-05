from unittest.mock import MagicMock

import pytest
from django.http import QueryDict

from apps.informes_tacticos.periodo import parse_periodo
from apps.informes_tacticos.services.despacho_informes_service import DespachoInformesService


def _periodo():
    qd = QueryDict(mutable=True)
    qd["desde"] = "2026-07-01"
    qd["hasta"] = "2026-07-31"
    return parse_periodo(qd)


@pytest.mark.service
class TestDespachoInformesService:
    def test_asignacion_automatica_vs_manual_delegates_with_idcondado(self):
        repo = MagicMock()
        repo.asignacion_automatica_vs_manual.return_value = [{"idorigendespacho": 1, "pct_total": 1.0}]
        service = DespachoInformesService(repository=repo)
        periodo = _periodo()

        result = service.asignacion_automatica_vs_manual(periodo, idcondado=5)

        repo.asignacion_automatica_vs_manual.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, 5)
        assert result == [{"idorigendespacho": 1, "pct_total": 1.0}]

    def test_tiempo_reportado_confirmado_delegates(self):
        repo = MagicMock()
        repo.tiempo_reportado_confirmado.return_value = {"promedio_segundos": 30.0}
        service = DespachoInformesService(repository=repo)
        periodo = _periodo()

        result = service.tiempo_reportado_confirmado(periodo)

        repo.tiempo_reportado_confirmado.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == {"promedio_segundos": 30.0}

    def test_tiempo_respuesta_por_severidad_delegates(self):
        repo = MagicMock()
        repo.tiempo_respuesta_por_severidad.return_value = [{"idseveridad": 1, "promedio_segundos": 10.0}]
        service = DespachoInformesService(repository=repo)
        periodo = _periodo()

        result = service.tiempo_respuesta_por_severidad(periodo)

        repo.tiempo_respuesta_por_severidad.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, None)
        assert result == [{"idseveridad": 1, "promedio_segundos": 10.0}]

    def test_rechazo_timeout_por_unidad_delegates(self):
        repo = MagicMock()
        repo.rechazo_timeout_por_unidad.return_value = [{"idunidademergencia": 1, "pct_rechazo_timeout": 0.1}]
        service = DespachoInformesService(repository=repo)
        periodo = _periodo()

        result = service.rechazo_timeout_por_unidad(periodo)

        repo.rechazo_timeout_por_unidad.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idunidademergencia": 1, "pct_rechazo_timeout": 0.1}]

    def test_carga_por_unidad_delegates(self):
        repo = MagicMock()
        repo.carga_por_unidad.return_value = [{"idunidademergencia": 1, "total_despachos": 5}]
        service = DespachoInformesService(repository=repo)
        periodo = _periodo()

        result = service.carga_por_unidad(periodo)

        repo.carga_por_unidad.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idunidademergencia": 1, "total_despachos": 5}]

    def test_ratio_demanda_capacidad_delegates(self):
        repo = MagicMock()
        repo.ratio_demanda_capacidad.return_value = [{"idcondado": 1, "ratio": 2.0}]
        service = DespachoInformesService(repository=repo)
        periodo = _periodo()

        result = service.ratio_demanda_capacidad(periodo)

        repo.ratio_demanda_capacidad.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idcondado": 1, "ratio": 2.0}]
