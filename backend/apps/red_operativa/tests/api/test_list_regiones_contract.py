import pytest


@pytest.mark.api
class TestListRegionesContract:
    def test_get_regiones_when_admin_returns_200(
        self, api_client, admin_auth_headers, director_tecnologico_auth_headers
    ):
        # Seed via O55 (aprobación exclusiva de Director Tecnológico)
        api_client.post(
            "/api/v1/red-operativa/regiones/validaciones",
            {"idestado": 1, "nombreregion": "CDMX List", "resultado": "Aprobada"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        response = api_client.get(
            "/api/v1/red-operativa/regiones",
            **admin_auth_headers,
        )

        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert isinstance(items, list)
        assert len(items) >= 1

    def test_get_region_detalle_when_exists_returns_200(
        self, api_client, admin_auth_headers, director_tecnologico_auth_headers
    ):
        create = api_client.post(
            "/api/v1/red-operativa/regiones/validaciones",
            {"idestado": 2, "nombreregion": "Jalisco Detalle", "resultado": "Aprobada"},
            format="json",
            **director_tecnologico_auth_headers,
        )
        assert create.status_code == 200
        rid = create.json()["data"]["idregionoperativa"]

        response = api_client.get(
            f"/api/v1/red-operativa/regiones/{rid}",
            **admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["idregionoperativa"] == rid

    def test_get_regiones_when_proveedor_returns_403(self, api_client, proveedor_auth_headers):
        response = api_client.get(
            "/api/v1/red-operativa/regiones",
            **proveedor_auth_headers,
        )
        assert response.status_code == 403
