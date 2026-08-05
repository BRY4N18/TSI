import pytest

URL = "/api/v1/informes-tacticos/registro/volumen-casos"
BASE = "/api/v1/informes-tacticos/registro"


@pytest.mark.api
class TestVolumenCasosView:
    def test_returns_200_with_aggregated_data(self, api_client, operador_auth_headers, pinot_store):
        # Arrange
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": 1782_864_000_000, "activo": True},
            ]
        )

        # Act
        response = api_client.get(
            URL, {"desde": "2026-07-01", "hasta": "2026-07-31"}, **operador_auth_headers
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["periodo"] == {
            "desde": "2026-07-01",
            "hasta": "2026-07-31",
            "granularidad": "dia",
        }
        assert body["data"] == [{"periodo": "2026-07-01", "total_casos": 1}]

    def test_returns_200_with_empty_data_when_no_rows_in_range(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            URL, {"desde": "1999-01-01", "hasta": "1999-01-31"}, **operador_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_returns_400_when_periodo_is_missing(self, api_client, operador_auth_headers):
        # Act
        response = api_client.get(URL, **operador_auth_headers)

        # Assert
        assert response.status_code == 400

    def test_returns_401_without_token(self, api_client):
        # Act
        response = api_client.get(URL, {"desde": "2026-07-01", "hasta": "2026-07-31"})

        # Assert
        assert response.status_code == 401

    def test_admin_role_also_allowed(self, api_client, admin_auth_headers):
        # Act
        response = api_client.get(
            URL, {"desde": "2026-07-01", "hasta": "2026-07-31"}, **admin_auth_headers
        )

        # Assert
        assert response.status_code == 200


@pytest.mark.api
class TestDistribucionSeveridadView:
    def test_returns_200_grouped_by_severidad(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "A1", "fechahoraaccidente": 1782_864_000_000, "idseveridad": 1}
        )
        response = api_client.get(
            f"{BASE}/distribucion-severidad",
            {"desde": "2026-07-01", "hasta": "2026-07-31"},
            **operador_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == [{"idseveridad": 1, "total_casos": 1}]

    def test_returns_401_without_token(self, api_client):
        response = api_client.get(
            f"{BASE}/distribucion-severidad", {"desde": "2026-07-01", "hasta": "2026-07-31"}
        )
        assert response.status_code == 401


@pytest.mark.api
class TestDistribucionZonaView:
    def test_returns_200_grouped_by_idcalle(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "A1", "fechahoraaccidente": 1782_864_000_000, "idcalle": 10}
        )
        response = api_client.get(
            f"{BASE}/distribucion-zona",
            {"desde": "2026-07-01", "hasta": "2026-07-31"},
            **operador_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"idcalle": 10, "total_casos": 1, "calle_nombre": None}
        ]


@pytest.mark.api
class TestCompletitudCamposCriticosView:
    def test_returns_200_with_pct_completos(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].append(
            {
                "idaccidente": "A1",
                "fechahoraaccidente": 1782_864_000_000,
                "idseveridad": 1,
                "idcalle": 10,
            }
        )
        response = api_client.get(
            f"{BASE}/completitud-campos-criticos",
            {"desde": "2026-07-01", "hasta": "2026-07-31"},
            **operador_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == [{"periodo": "2026-07-01", "pct_completos": 1.0}]


@pytest.mark.api
class TestDescarteFusionView:
    def test_returns_200_with_pct_descarte_y_fusion(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "A1", "fechahoraaccidente": 1782_864_000_000}
        )
        pinot_store["Fact_AccidenteTipoEstadoAccidente"].append(
            {
                "idaccidente": "A1",
                "fechahoramodificado": 1782_864_000_000,
                "idtipoestadoincidente": 7,
            }
        )
        response = api_client.get(
            f"{BASE}/descarte-fusion",
            {"desde": "2026-07-01", "hasta": "2026-07-31"},
            **operador_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == [
            {"periodo": "2026-07-01", "pct_descarte": 1.0, "pct_fusion": 0.0}
        ]


@pytest.mark.api
class TestRankingUbicacionesView:
    def test_returns_200_ordered_desc(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].extend(
            [
                {"idaccidente": "A1", "fechahoraaccidente": 1782_864_000_000, "idcalle": 10},
                {"idaccidente": "A2", "fechahoraaccidente": 1782_864_000_000, "idcalle": 10},
                {"idaccidente": "A3", "fechahoraaccidente": 1782_864_000_000, "idcalle": 20},
            ]
        )
        response = api_client.get(
            f"{BASE}/ranking-ubicaciones",
            {"desde": "2026-07-01", "hasta": "2026-07-31", "top": "1"},
            **operador_auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == [
            {"idcalle": 10, "total_casos": 2, "calle_nombre": None}
        ]
        assert body["meta"]["filtros"] == {"top": 1}

    def test_returns_400_when_top_out_of_range(self, api_client, operador_auth_headers):
        response = api_client.get(
            f"{BASE}/ranking-ubicaciones",
            {"desde": "2026-07-01", "hasta": "2026-07-31", "top": "500"},
            **operador_auth_headers,
        )
        assert response.status_code == 400


@pytest.mark.api
class TestImpactoHumanoView:
    def test_returns_200_summed_by_idcalle(self, api_client, operador_auth_headers, pinot_store):
        pinot_store["Fact_Accidente"].append(
            {
                "idaccidente": "A1",
                "fechahoraaccidente": 1782_864_000_000,
                "idcalle": 10,
                "numvictimas": 2,
                "numheridos": 1,
                "numfallecidos": 0,
            }
        )
        response = api_client.get(
            f"{BASE}/impacto-humano",
            {"desde": "2026-07-01", "hasta": "2026-07-31"},
            **operador_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == [
            {
                "idcalle": 10,
                "total_victimas": 2,
                "total_heridos": 1,
                "total_fallecidos": 0,
                "calle_nombre": None,
            }
        ]
