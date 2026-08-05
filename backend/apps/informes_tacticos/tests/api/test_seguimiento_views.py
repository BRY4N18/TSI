import pytest

BASE = "/api/v1/informes-tacticos/seguimiento"
PERIODO = {"desde": "2026-07-01", "hasta": "2026-07-31"}
JUL_1 = 1782_864_000_000


@pytest.mark.api
class TestTiempoAsignadoCerradoView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_AccidenteTipoEstadoAccidente"].extend(
            [
                {"idaccidente": "A1", "idtipoestadoincidente": 4, "fechahoramodificado": JUL_1},
                {"idaccidente": "A1", "idtipoestadoincidente": 6, "fechahoramodificado": JUL_1 + 60_000},
            ]
        )
        pinot_store["Fact_Despacho"].append({"idaccidente": "A1", "idunidademergencia": 10})
        response = api_client.get(f"{BASE}/tiempo-asignado-cerrado", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"idunidademergencia": 10, "unidad_nombre": None, "unidad_placa": None, "promedio_segundos": 60.0}
        ]

    def test_returns_401_without_token(self, api_client):
        response = api_client.get(f"{BASE}/tiempo-asignado-cerrado", PERIODO)
        assert response.status_code == 401


@pytest.mark.api
class TestCierresForzadosView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_HistorialDespachoUnidad"].append(
            {
                "idhistorialdespachounidad": 1,
                "iddespacho": 1,
                "estadonuevo": "Retirado",
                "fechahora": JUL_1,
                "idusuario": 5,
            }
        )
        response = api_client.get(f"{BASE}/cierres-forzados", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [{"periodo": "2026-07-01", "pct_cierres_forzados": 1.0}]


@pytest.mark.api
class TestAbortosPerdidasView:
    def test_returns_200(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Despacho"].append({"iddespacho": 1, "idunidademergencia": 10})
        pinot_store["Fact_HistorialDespachoUnidad"].append(
            {"idhistorialdespachounidad": 1, "iddespacho": 1, "estadonuevo": "Abortado", "fechahora": JUL_1}
        )
        response = api_client.get(f"{BASE}/abortos-perdidas", PERIODO, **operador_auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"idunidademergencia": 10, "unidad_nombre": None, "unidad_placa": None, "pct_abortos_perdidas": 1.0}
        ]
