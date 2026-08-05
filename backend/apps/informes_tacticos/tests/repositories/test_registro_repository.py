from datetime import datetime, timezone

import pytest

from core.repositories.informes_tacticos.registro_repository import RegistroRepository


def _ms(year, month, day, hour=0) -> int:
    return int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp() * 1000)


JUL_1 = _ms(2026, 7, 1)
JUL_2 = _ms(2026, 7, 2)
JUL_3 = _ms(2026, 7, 3)


@pytest.mark.repository
class TestRegistroRepositoryVolumenCasos:
    def test_volumen_casos_groups_by_day(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": JUL_1, "activo": True},
                {"idaccidente": "A2", "fechahoraaccidente": JUL_1 + 3600_000, "activo": True},
                {"idaccidente": "A3", "fechahoraaccidente": JUL_2, "activo": True},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.volumen_casos(JUL_1, JUL_3 - 1, "day")

        # Assert
        assert {r["periodo"]: r["total_casos"] for r in result} == {
            "2026-07-01": 2,
            "2026-07-02": 1,
        }

    def test_volumen_casos_excludes_rows_outside_range(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "OLD", "fechahoraaccidente": JUL_1 - 1, "activo": True},
                {"idaccidente": "IN", "fechahoraaccidente": JUL_1, "activo": True},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.volumen_casos(JUL_1, JUL_3 - 1, "day")

        # Assert
        assert len(result) == 1
        assert result[0]["total_casos"] == 1

    def test_volumen_casos_with_no_data_returns_empty_list(self, mock_pinot, pinot_store):
        # Arrange
        repo = RegistroRepository()

        # Act
        result = repo.volumen_casos(JUL_1, JUL_3, "day")

        # Assert
        assert result == []


@pytest.mark.repository
class TestRegistroRepositoryDistribucionSeveridad:
    def test_groups_by_idseveridad(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": JUL_1, "idseveridad": 1},
                {"idaccidente": "A2", "fechahoraaccidente": JUL_1, "idseveridad": 1},
                {"idaccidente": "A3", "fechahoraaccidente": JUL_1, "idseveridad": 2},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.distribucion_severidad(JUL_1, JUL_3)

        # Assert
        assert {r["idseveridad"]: r["total_casos"] for r in result} == {1: 2, 2: 1}


@pytest.mark.repository
class TestRegistroRepositoryDistribucionZona:
    def test_groups_by_idcalle(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": JUL_1, "idcalle": 10},
                {"idaccidente": "A2", "fechahoraaccidente": JUL_1, "idcalle": 10},
                {"idaccidente": "A3", "fechahoraaccidente": JUL_1, "idcalle": 20},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.distribucion_zona(JUL_1, JUL_3)

        # Assert
        assert result == [
            {"idcalle": 10, "total_casos": 2, "calle_nombre": None},
            {"idcalle": 20, "total_casos": 1, "calle_nombre": None},
        ]

    def test_resolves_real_calle_name(self, mock_pinot, pinot_store):
        # Arrange: idcalle=1 ya sembrado en Dim_Calle como "Av. Reforma"
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "A1", "fechahoraaccidente": JUL_1, "idcalle": 1}
        )
        repo = RegistroRepository()

        # Act
        result = repo.distribucion_zona(JUL_1, JUL_3)

        # Assert
        assert result == [{"idcalle": 1, "total_casos": 1, "calle_nombre": "Av. Reforma"}]


@pytest.mark.repository
class TestRegistroRepositoryCompletitudCamposCriticos:
    def test_computes_pct_completos_per_day(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": JUL_1, "idseveridad": 1, "idcalle": 10},
                {"idaccidente": "A2", "fechahoraaccidente": JUL_1, "idseveridad": None, "idcalle": 10},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.completitud_campos_criticos(JUL_1, JUL_3, "day")

        # Assert
        assert result == [{"periodo": "2026-07-01", "pct_completos": 0.5}]

    def test_returns_zero_pct_when_no_rows_in_period(self, mock_pinot, pinot_store):
        # Arrange
        repo = RegistroRepository()

        # Act
        result = repo.completitud_campos_criticos(JUL_1, JUL_3, "day")

        # Assert
        assert result == []


@pytest.mark.repository
class TestRegistroRepositoryDescarteFusion:
    def test_computes_pct_descarte_y_fusion_per_day(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": JUL_1},
                {"idaccidente": "A2", "fechahoraaccidente": JUL_1},
                {"idaccidente": "A3", "fechahoraaccidente": JUL_1},
                {"idaccidente": "A4", "fechahoraaccidente": JUL_1},
            ]
        )
        pinot_store["Fact_AccidenteTipoEstadoAccidente"].extend(
            [
                {"idaccidente": "A1", "fechahoramodificado": JUL_1, "idtipoestadoincidente": 7},
                {"idaccidente": "A2", "fechahoramodificado": JUL_1, "idtipoestadoincidente": 8},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.descarte_fusion(JUL_1, JUL_3 - 1, "day")

        # Assert
        assert result == [{"periodo": "2026-07-01", "pct_descarte": 0.25, "pct_fusion": 0.25}]

    def test_returns_zero_pct_when_no_estados_registrados(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].append({"idaccidente": "A1", "fechahoraaccidente": JUL_1})
        repo = RegistroRepository()

        # Act
        result = repo.descarte_fusion(JUL_1, JUL_3 - 1, "day")

        # Assert
        assert result == [{"periodo": "2026-07-01", "pct_descarte": 0.0, "pct_fusion": 0.0}]


@pytest.mark.repository
class TestRegistroRepositoryRankingUbicaciones:
    def test_orders_by_total_casos_desc_and_respects_top(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": JUL_1, "idcalle": 10},
                {"idaccidente": "A2", "fechahoraaccidente": JUL_1, "idcalle": 10},
                {"idaccidente": "A3", "fechahoraaccidente": JUL_1, "idcalle": 20},
                {"idaccidente": "A4", "fechahoraaccidente": JUL_1, "idcalle": 30},
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.ranking_ubicaciones(JUL_1, JUL_3, top=2)

        # Assert
        assert result == [
            {"idcalle": 10, "total_casos": 2, "calle_nombre": None},
            {"idcalle": 20, "total_casos": 1, "calle_nombre": None},
        ]


@pytest.mark.repository
class TestRegistroRepositoryImpactoHumano:
    def test_sums_victimas_heridos_fallecidos_by_idcalle(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {
                    "idaccidente": "A1",
                    "fechahoraaccidente": JUL_1,
                    "idcalle": 10,
                    "numvictimas": 2,
                    "numheridos": 1,
                    "numfallecidos": 0,
                },
                {
                    "idaccidente": "A2",
                    "fechahoraaccidente": JUL_1,
                    "idcalle": 10,
                    "numvictimas": 1,
                    "numheridos": 0,
                    "numfallecidos": 1,
                },
            ]
        )
        repo = RegistroRepository()

        # Act
        result = repo.impacto_humano(JUL_1, JUL_3)

        # Assert
        assert result == [
            {
                "idcalle": 10,
                "total_victimas": 3,
                "total_heridos": 1,
                "total_fallecidos": 1,
                "calle_nombre": None,
            }
        ]
