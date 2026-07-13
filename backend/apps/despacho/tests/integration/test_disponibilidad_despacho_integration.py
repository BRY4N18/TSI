import pytest


@pytest.mark.critical_path
class TestDisponibilidadDespachoIntegration:
    def test_flujo_disponibilidad_reflejado_en_flota(
        self, api_client, unidad_auth_headers, admin_auth_headers, unidad_con_estado_activa
    ):
        # Act — unidad declara Ocupada
        declare = api_client.post(
            "/api/v1/mi-unidad-emergencia/disponibilidad",
            {"estadonuevo": "Ocupada"},
            format="json",
            **unidad_auth_headers,
        )
        flota = api_client.get("/api/v1/unidades-emergencia", **admin_auth_headers)
        mi_estado = api_client.get(
            "/api/v1/mi-unidad-emergencia/disponibilidad",
            **unidad_auth_headers,
        )

        # Assert
        assert declare.status_code == 201
        assert mi_estado.json()["data"]["estado_actual"] == "Ocupada"
        assert mi_estado.json()["data"]["incluido_en_despacho"] is False
        unit = next(
            u for u in flota.json()["data"]["items"] if u["idunidademergencia"] == 1
        )
        assert unit["estado_actual"] == "Ocupada"
        assert unit["incluido_en_despacho"] is False
