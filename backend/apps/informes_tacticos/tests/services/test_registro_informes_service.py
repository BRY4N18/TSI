from unittest.mock import MagicMock

import pytest

from apps.informes_tacticos.periodo import parse_periodo
from apps.informes_tacticos.services.registro_informes_service import RegistroInformesService
from django.http import QueryDict


def _periodo():
    qd = QueryDict(mutable=True)
    qd["desde"] = "2026-07-01"
    qd["hasta"] = "2026-07-31"
    return parse_periodo(qd)


@pytest.mark.service
class TestRegistroInformesServiceVolumenCasos:
    def test_volumen_casos_delegates_to_repository_with_periodo_fields(self):
        # Arrange
        repo = MagicMock()
        repo.volumen_casos.return_value = [{"periodo": "2026-07-01", "total_casos": 3}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        # Act
        result = service.volumen_casos(periodo)

        # Assert
        repo.volumen_casos.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, "day")
        assert result == [{"periodo": "2026-07-01", "total_casos": 3}]


@pytest.mark.service
class TestRegistroInformesServiceOtrosInformes:
    def test_distribucion_severidad_delegates_to_repository(self):
        repo = MagicMock()
        repo.distribucion_severidad.return_value = [{"idseveridad": 1, "total_casos": 2}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        result = service.distribucion_severidad(periodo)

        repo.distribucion_severidad.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idseveridad": 1, "total_casos": 2}]

    def test_distribucion_zona_delegates_to_repository(self):
        repo = MagicMock()
        repo.distribucion_zona.return_value = [{"idcalle": 10, "total_casos": 2}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        result = service.distribucion_zona(periodo)

        repo.distribucion_zona.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idcalle": 10, "total_casos": 2}]

    def test_completitud_campos_criticos_delegates_to_repository(self):
        repo = MagicMock()
        repo.completitud_campos_criticos.return_value = [{"periodo": "2026-07-01", "pct_completos": 1.0}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        result = service.completitud_campos_criticos(periodo)

        repo.completitud_campos_criticos.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, "day")
        assert result == [{"periodo": "2026-07-01", "pct_completos": 1.0}]

    def test_descarte_fusion_delegates_to_repository(self):
        repo = MagicMock()
        repo.descarte_fusion.return_value = [{"periodo": "2026-07-01", "pct_descarte": 0.1, "pct_fusion": 0.0}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        result = service.descarte_fusion(periodo)

        repo.descarte_fusion.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, "day")
        assert result == [{"periodo": "2026-07-01", "pct_descarte": 0.1, "pct_fusion": 0.0}]

    def test_ranking_ubicaciones_delegates_to_repository_with_default_top(self):
        repo = MagicMock()
        repo.ranking_ubicaciones.return_value = [{"idcalle": 10, "total_casos": 5}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        result = service.ranking_ubicaciones(periodo)

        repo.ranking_ubicaciones.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, 10)
        assert result == [{"idcalle": 10, "total_casos": 5}]

    def test_ranking_ubicaciones_respects_custom_top(self):
        repo = MagicMock()
        repo.ranking_ubicaciones.return_value = []
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        service.ranking_ubicaciones(periodo, top=25)

        repo.ranking_ubicaciones.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms, 25)

    def test_impacto_humano_delegates_to_repository(self):
        repo = MagicMock()
        repo.impacto_humano.return_value = [{"idcalle": 10, "total_victimas": 1}]
        service = RegistroInformesService(repository=repo)
        periodo = _periodo()

        result = service.impacto_humano(periodo)

        repo.impacto_humano.assert_called_once_with(periodo.desde_ms, periodo.hasta_ms)
        assert result == [{"idcalle": 10, "total_victimas": 1}]
