from datetime import datetime, timezone

import pytest

from core.repositories.informes_tacticos.seguimiento_repository import SeguimientoRepository


def _ms(year, month, day, hour=0) -> int:
    return int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp() * 1000)


JUL_1 = _ms(2026, 7, 1)
JUL_3 = _ms(2026, 7, 3)


@pytest.mark.repository
class TestSeguimientoRepositoryTiempoAsignadoCerrado:
    def test_averages_diff_grouped_by_unidad(self, mock_pinot, pinot_store):
        # Arrange: ASIGNADO=4, CERRADO=6
        pinot_store["Fact_AccidenteTipoEstadoAccidente"].extend(
            [
                {"idaccidente": "A1", "idtipoestadoincidente": 4, "fechahoramodificado": JUL_1},
                {"idaccidente": "A1", "idtipoestadoincidente": 6, "fechahoramodificado": JUL_1 + 120_000},
            ]
        )
        pinot_store["Fact_Despacho"].append({"idaccidente": "A1", "idunidademergencia": 10})
        pinot_store["Dim_UnidadEmergencia"].append(
            {"idunidademergencia": 10, "unidademergencia": "AlzaCarros", "placa": "SMTP2-48993"}
        )
        repo = SeguimientoRepository()

        # Act
        result = repo.tiempo_asignado_cerrado(JUL_1, JUL_3)

        # Assert
        assert result == [
            {
                "idunidademergencia": 10,
                "unidad_nombre": "AlzaCarros",
                "unidad_placa": "SMTP2-48993",
                "promedio_segundos": 120.0,
            }
        ]

    def test_returns_empty_when_no_pairs(self, mock_pinot, pinot_store):
        repo = SeguimientoRepository()
        result = repo.tiempo_asignado_cerrado(JUL_1, JUL_3)
        assert result == []


@pytest.mark.repository
class TestSeguimientoRepositoryCierresForzados:
    def test_computes_pct_retirado_over_terminal_states(self, mock_pinot, pinot_store):
        pinot_store["Fact_HistorialDespachoUnidad"].extend(
            [
                {
                    "idhistorialdespachounidad": 1,
                    "iddespacho": 1,
                    "estadonuevo": "Retirado",
                    "fechahora": JUL_1,
                    "idusuario": 5,
                },
                {"idhistorialdespachounidad": 2, "iddespacho": 2, "estadonuevo": "Cerrado", "fechahora": JUL_1},
                {"idhistorialdespachounidad": 3, "iddespacho": 3, "estadonuevo": "Abortado", "fechahora": JUL_1},
            ]
        )
        repo = SeguimientoRepository()

        result = repo.cierres_forzados(JUL_1, JUL_3 - 1, "day")

        assert result == [{"periodo": "2026-07-01", "pct_cierres_forzados": 0.5}]

    def test_retirado_sin_idusuario_no_cuenta_como_forzado(self, mock_pinot, pinot_store):
        # Arrange: retiro automático por vencimiento — sin idusuario
        pinot_store["Fact_HistorialDespachoUnidad"].extend(
            [
                {"idhistorialdespachounidad": 1, "iddespacho": 1, "estadonuevo": "Retirado", "fechahora": JUL_1},
                {"idhistorialdespachounidad": 2, "iddespacho": 2, "estadonuevo": "Cerrado", "fechahora": JUL_1},
            ]
        )
        repo = SeguimientoRepository()

        result = repo.cierres_forzados(JUL_1, JUL_3 - 1, "day")

        assert result == [{"periodo": "2026-07-01", "pct_cierres_forzados": 0.0}]


@pytest.mark.repository
class TestSeguimientoRepositoryAbortosPerdidas:
    def test_computes_pct_abortado_via_despacho_join(self, mock_pinot, pinot_store):
        pinot_store["Fact_Despacho"].append({"iddespacho": 1, "idunidademergencia": 10})
        pinot_store["Fact_HistorialDespachoUnidad"].extend(
            [
                {"idhistorialdespachounidad": 1, "iddespacho": 1, "estadonuevo": "Abortado", "fechahora": JUL_1},
                {"idhistorialdespachounidad": 2, "iddespacho": 1, "estadonuevo": "Confirmado", "fechahora": JUL_1},
            ]
        )
        pinot_store["Dim_UnidadEmergencia"].append(
            {"idunidademergencia": 10, "unidademergencia": "AlzaCarros", "placa": "SMTP2-48993"}
        )
        repo = SeguimientoRepository()

        result = repo.abortos_perdidas(JUL_1, JUL_3)

        assert result == [
            {
                "idunidademergencia": 10,
                "unidad_nombre": "AlzaCarros",
                "unidad_placa": "SMTP2-48993",
                "pct_abortos_perdidas": 0.5,
            }
        ]

    def test_returns_empty_list_when_no_historial(self, mock_pinot, pinot_store):
        repo = SeguimientoRepository()
        result = repo.abortos_perdidas(JUL_1, JUL_3)
        assert result == []
