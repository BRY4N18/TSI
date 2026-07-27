import pytest


@pytest.mark.api
class TestAprobacionProveedorContract:
    def _crear_solicitud(self, api_client):
        payload = {
            "razon_social": "Rescate Express CIA",
            "nombre": "Rescate Express",
            "tipo": "Proveedor",
            "nit_identificacion": "830444555-7",
            "admin_local": {
                "nombres": "Luis",
                "apellidos": "Rescate",
                "gmail": "luis.rescate@tsi.com",
            },
        }
        response = api_client.post(
            "/api/v1/cuentas-clientes/autorregistro",
            payload,
            format="json",
        )
        assert response.status_code == 201
        return response.json()["data"]["idcliente"]

    def test_listar_and_aprobar(self, api_client, auth_headers, mock_pinot, mock_kafka):
        # Arrange
        idcliente = self._crear_solicitud(api_client)

        # Act
        list_resp = api_client.get(
            "/api/v1/cuentas-clientes/solicitudes",
            **auth_headers,
        )
        approve_resp = api_client.post(
            f"/api/v1/cuentas-clientes/{idcliente}/aprobacion",
            {"decision": "aprobar"},
            format="json",
            **auth_headers,
        )

        # Assert
        assert list_resp.status_code == 200
        assert any(r["idcliente"] == idcliente for r in list_resp.json()["data"])
        assert approve_resp.status_code == 200
        assert approve_resp.json()["data"]["estado"] == "Activo"
        assert approve_resp.json()["data"]["estado_onboarding"] == "Pendiente"

    def test_rechazar_without_motivo_returns_400(
        self, api_client, auth_headers, mock_pinot, mock_kafka
    ):
        # Arrange
        idcliente = self._crear_solicitud(api_client)

        # Act
        response = api_client.post(
            f"/api/v1/cuentas-clientes/{idcliente}/aprobacion",
            {"decision": "rechazar"},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_anular_rechazo_libera_nit(
        self, api_client, auth_headers, mock_pinot, mock_kafka
    ):
        # Arrange
        idcliente = self._crear_solicitud(api_client)
        reject = api_client.post(
            f"/api/v1/cuentas-clientes/{idcliente}/aprobacion",
            {"decision": "rechazar", "motivo": "Docs incompletos"},
            format="json",
            **auth_headers,
        )
        assert reject.status_code == 200

        # Act
        anular = api_client.post(
            f"/api/v1/cuentas-clientes/{idcliente}/anular-rechazo",
            {},
            format="json",
            **auth_headers,
        )
        reintento = api_client.post(
            "/api/v1/cuentas-clientes/autorregistro",
            {
                "razon_social": "Rescate Express CIA 2",
                "nombre": "Rescate Express 2",
                "tipo": "Proveedor",
                "nit_identificacion": "830444555-7",
                "admin_local": {
                    "nombres": "Luis",
                    "apellidos": "Rescate",
                    "gmail": "luis.rescate@tsi.com",
                },
            },
            format="json",
        )

        # Assert
        assert anular.status_code == 200
        assert anular.json()["data"]["estado"] == "Rechazado_Anulado"
        assert reintento.status_code == 201
        assert reintento.json()["data"]["estado"] == "Pendiente_Aprobación"
        assert reintento.json()["data"]["idcliente"] != idcliente

    def test_anular_rechazo_when_pendiente_returns_409(
        self, api_client, auth_headers, mock_pinot, mock_kafka
    ):
        # Arrange
        idcliente = self._crear_solicitud(api_client)

        # Act
        response = api_client.post(
            f"/api/v1/cuentas-clientes/{idcliente}/anular-rechazo",
            {},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 409
