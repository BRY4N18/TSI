from datetime import datetime, timezone

import pytest

from core.repositories.informes_tacticos.despacho_repository import DespachoRepository


def _ms(year, month, day, hour=0) -> int:
    return int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp() * 1000)


JUL_1 = _ms(2026, 7, 1)
JUL_3 = _ms(2026, 7, 3)


@pytest.mark.repository
class TestDespachoRepositoryAsignacionAutomaticaVsManual:
    def test_groups_by_origen_with_pct(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Despacho"].extend(
            [
                {"iddespacho": 1, "idorigendespacho": 1, "idunidademergencia": 10, "fechahoradespacho": JUL_1},
                {"iddespacho": 2, "idorigendespacho": 1, "idunidademergencia": 10, "fechahoradespacho": JUL_1},
                {"iddespacho": 3, "idorigendespacho": 2, "idunidademergencia": 20, "fechahoradespacho": JUL_1},
            ]
        )
        pinot_store["Dim_OrigenDespacho"].extend(
            [
                {"idorigendespacho": 1, "origendespacho": "Automatico"},
                {"idorigendespacho": 2, "origendespacho": "Manual"},
            ]
        )
        repo = DespachoRepository()

        # Act
        result = repo.asignacion_automatica_vs_manual(JUL_1, JUL_3)

        # Assert
        assert result == [
            {"idorigendespacho": 1, "origen_nombre": "Automatico", "pct_total": 0.6667},
            {"idorigendespacho": 2, "origen_nombre": "Manual", "pct_total": 0.3333},
        ]

    def test_filters_by_idcondado_when_provided(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Despacho"].extend(
            [
                {"iddespacho": 1, "idorigendespacho": 1, "idunidademergencia": 10, "fechahoradespacho": JUL_1},
                {"iddespacho": 2, "idorigendespacho": 2, "idunidademergencia": 20, "fechahoradespacho": JUL_1},
            ]
        )
        pinot_store["Dim_UnidadEmergencia"].extend(
            [
                {"idunidademergencia": 10, "idcondado": 100, "activo": True},
                {"idunidademergencia": 20, "idcondado": 200, "activo": True},
            ]
        )
        repo = DespachoRepository()

        # Act
        result = repo.asignacion_automatica_vs_manual(JUL_1, JUL_3, idcondado=100)

        # Assert
        assert result == [{"idorigendespacho": 1, "origen_nombre": None, "pct_total": 1.0}]


@pytest.mark.repository
class TestDespachoRepositoryTiempoReportadoConfirmado:
    def test_averages_diff_between_reportado_and_asignado(self, mock_pinot, pinot_store):
        # Arrange: REPORTADO=2, ASIGNADO=4 (ver ESTADO_IDS)
        pinot_store["Fact_AccidenteTipoEstadoAccidente"].extend(
            [
                {"idaccidente": "A1", "idtipoestadoincidente": 2, "fechahoramodificado": JUL_1},
                {"idaccidente": "A1", "idtipoestadoincidente": 4, "fechahoramodificado": JUL_1 + 60_000},
            ]
        )
        repo = DespachoRepository()

        # Act
        result = repo.tiempo_reportado_confirmado(JUL_1, JUL_3)

        # Assert
        assert result == {"promedio_segundos": 60.0}

    def test_returns_zero_when_no_pairs(self, mock_pinot, pinot_store):
        # Arrange
        repo = DespachoRepository()

        # Act
        result = repo.tiempo_reportado_confirmado(JUL_1, JUL_3)

        # Assert
        assert result == {"promedio_segundos": 0.0}


@pytest.mark.repository
class TestDespachoRepositoryTiempoRespuestaPorSeveridad:
    def test_groups_by_severidad_via_accidente_join(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Despacho"].append(
            {
                "iddespacho": 1,
                "idaccidente": "A1",
                "idunidademergencia": 10,
                "fechahoradespacho": JUL_1,
                "fechahorallegada": JUL_1 + 120_000,
            }
        )
        pinot_store["Fact_Accidente"].append({"idaccidente": "A1", "idseveridad": 3})
        repo = DespachoRepository()

        # Act
        result = repo.tiempo_respuesta_por_severidad(JUL_1, JUL_3)

        # Assert
        assert result == [{"idseveridad": 3, "promedio_segundos": 120.0}]


@pytest.mark.repository
class TestDespachoRepositoryRechazoTimeoutPorUnidad:
    def test_computes_pct_via_despacho_join(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Despacho"].append({"iddespacho": 1, "idunidademergencia": 10})
        pinot_store["Fact_HistorialDespachoUnidad"].extend(
            [
                {"idhistorialdespachounidad": 1, "iddespacho": 1, "estadonuevo": "Rechazado", "fechahora": JUL_1},
                {"idhistorialdespachounidad": 2, "iddespacho": 1, "estadonuevo": "Confirmado", "fechahora": JUL_1},
            ]
        )
        pinot_store["Dim_UnidadEmergencia"].append(
            {"idunidademergencia": 10, "unidademergencia": "AlzaCarros", "placa": "SMTP2-48993"}
        )
        repo = DespachoRepository()

        # Act
        result = repo.rechazo_timeout_por_unidad(JUL_1, JUL_3)

        # Assert
        assert result == [
            {
                "idunidademergencia": 10,
                "unidad_nombre": "AlzaCarros",
                "unidad_placa": "SMTP2-48993",
                "pct_rechazo_timeout": 0.5,
            }
        ]


@pytest.mark.repository
class TestDespachoRepositoryCargaPorUnidad:
    def test_groups_by_unidad(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Despacho"].extend(
            [
                {"iddespacho": 1, "idunidademergencia": 10, "fechahoradespacho": JUL_1},
                {"iddespacho": 2, "idunidademergencia": 10, "fechahoradespacho": JUL_1},
            ]
        )
        pinot_store["Dim_UnidadEmergencia"].append(
            {"idunidademergencia": 10, "unidademergencia": "AlzaCarros", "placa": "SMTP2-48993"}
        )
        repo = DespachoRepository()

        # Act
        result = repo.carga_por_unidad(JUL_1, JUL_3)

        # Assert
        assert result == [
            {
                "idunidademergencia": 10,
                "total_despachos": 2,
                "unidad_nombre": "AlzaCarros",
                "unidad_placa": "SMTP2-48993",
            }
        ]


@pytest.mark.repository
class TestDespachoRepositoryRatioDemandaCapacidad:
    def test_resolves_calle_to_condado_and_computes_ratio(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "idcalle": 9001, "fechahoraaccidente": JUL_1},
                {"idaccidente": "A2", "idcalle": 9001, "fechahoraaccidente": JUL_1},
            ]
        )
        pinot_store["Dim_Calle"].append({"idcalle": 9001, "idciudad": 9050})
        pinot_store["Dim_Ciudad"].append({"idciudad": 9050, "idcondado": 9100})
        pinot_store["Dim_UnidadEmergencia"].append(
            {"idunidademergencia": 9010, "idcondado": 9100, "activo": True}
        )
        pinot_store["Dim_Condado"].append({"idcondado": 9100, "condado": "Cuauhtemoc"})
        repo = DespachoRepository()

        # Act
        result = repo.ratio_demanda_capacidad(JUL_1, JUL_3)

        # Assert
        assert {
            "idcondado": 9100,
            "condado_nombre": "Cuauhtemoc",
            "total_accidentes": 2,
            "unidades_activas": 1,
            "ratio": 2.0,
        } in result

    def test_returns_empty_list_when_no_accidentes_in_range(self, mock_pinot, pinot_store):
        # Arrange
        repo = DespachoRepository()

        # Act
        result = repo.ratio_demanda_capacidad(JUL_1, JUL_3)

        # Assert
        assert result == []
