import pytest


@pytest.mark.api
class TestRolesContract:
    def test_list_roles_when_admin_returns_envelope(self, api_client, auth_headers):
        # Arrange / Act
        response = api_client.get("/api/v1/roles", **auth_headers)

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert len(body["data"]) >= 2

    def test_create_role_when_admin_succeeds(self, api_client, auth_headers):
        # Arrange
        payload = {"rol": "Coordinador", "descripcion": "Coordinador regional"}

        # Act
        response = api_client.post("/api/v1/roles", payload, format="json", **auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["rol"] == "Coordinador"

    def test_assign_role_when_admin_succeeds(self, api_client, auth_headers):
        # Arrange
        payload = {"idusuario": 2, "idrol": 1}

        # Act
        response = api_client.post(
            "/api/v1/usuarios/roles/asignar", payload, format="json", **auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["idusuario"] == 2
