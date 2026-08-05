import pytest

BASE = "/api/v1/informes-tacticos/despacho"
PERIODO = {"desde": "2026-07-01", "hasta": "2026-07-31"}
JUL_1 = 1782_864_000_000


@pytest.mark.api
class TestAsignacionAutomaticaVsManualView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Despacho"].append(
            {"iddespacho": 1, "idorigendespacho": 1, "idunidademergencia": 10, "fechahoradespacho": JUL_1}
        )
        response = api_client.get(f"{BASE}/asignacion-automatica-vs-manual", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"idorigendespacho": 1, "origen_nombre": None, "pct_total": 1.0}
        ]

    def test_returns_401_without_token(self, api_client):
        response = api_client.get(f"{BASE}/asignacion-automatica-vs-manual", PERIODO)
        assert response.status_code == 401


@pytest.mark.api
class TestTiempoReportadoConfirmadoView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_AccidenteTipoEstadoAccidente"].extend(
            [
                {"idaccidente": "A1", "idtipoestadoincidente": 2, "fechahoramodificado": JUL_1},
                {"idaccidente": "A1", "idtipoestadoincidente": 4, "fechahoramodificado": JUL_1 + 30_000},
            ]
        )
        response = api_client.get(f"{BASE}/tiempo-reportado-confirmado", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == {"promedio_segundos": 30.0}


@pytest.mark.api
class TestTiempoRespuestaPorSeveridadView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Despacho"].append(
            {
                "iddespacho": 1,
                "idaccidente": "A1",
                "idunidademergencia": 10,
                "fechahoradespacho": JUL_1,
                "fechahorallegada": JUL_1 + 60_000,
            }
        )
        pinot_store["Fact_Accidente"].append({"idaccidente": "A1", "idseveridad": 2})
        response = api_client.get(f"{BASE}/tiempo-respuesta-por-severidad", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [{"idseveridad": 2, "promedio_segundos": 60.0}]


@pytest.mark.api
class TestRechazoTimeoutPorUnidadView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Despacho"].append({"iddespacho": 1, "idunidademergencia": 10})
        pinot_store["Fact_HistorialDespachoUnidad"].append(
            {"idhistorialdespachounidad": 1, "iddespacho": 1, "estadonuevo": "Timeout", "fechahora": JUL_1}
        )
        response = api_client.get(f"{BASE}/rechazo-timeout-por-unidad", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"idunidademergencia": 10, "unidad_nombre": None, "unidad_placa": None, "pct_rechazo_timeout": 1.0}
        ]


@pytest.mark.api
class TestCargaPorUnidadView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Despacho"].append(
            {"iddespacho": 1, "idunidademergencia": 10, "fechahoradespacho": JUL_1}
        )
        response = api_client.get(f"{BASE}/carga-por-unidad", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"idunidademergencia": 10, "total_despachos": 1, "unidad_nombre": None, "unidad_placa": None}
        ]


@pytest.mark.api
class TestRatioDemandaCapacidadView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "A1", "idcalle": 9002, "fechahoraaccidente": JUL_1}
        )
        pinot_store["Dim_Calle"].append({"idcalle": 9002, "idciudad": 9051})
        pinot_store["Dim_Ciudad"].append({"idciudad": 9051, "idcondado": 9101})
        pinot_store["Dim_UnidadEmergencia"].append(
            {"idunidademergencia": 9011, "idcondado": 9101, "activo": True}
        )
        response = api_client.get(f"{BASE}/ratio-demanda-capacidad", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert {
            "idcondado": 9101,
            "condado_nombre": None,
            "total_accidentes": 1,
            "unidades_activas": 1,
            "ratio": 1.0,
        } in response.json()["data"]
