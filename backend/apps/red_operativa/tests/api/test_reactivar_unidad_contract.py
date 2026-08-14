import pytest


@pytest.mark.api
class TestReactivarUnidadContract:
    def test_post_reactivar_when_sin_conflicto_returns_200(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        # Arrange
        api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {"motivo": "Baja"},
            format="json",
            **proveedor_auth_headers,
        )

        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/reactivar",
            {},
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is True

    def test_no_se_puede_ocupar_la_placa_de_una_unidad_dada_de_baja(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        """El conflicto de placa se corta al registrar, no al reactivar.

        Antes, registrar una unidad con la placa de una dada de baja devolvía 201 y el
        choque solo se detectaba si alguien intentaba reactivar la antigua. Como la
        reactivación es opcional, lo normal era quedarse con dos unidades compartiendo
        el identificador único de negocio. Ahora el alta la rechaza (SRS §3.5.1) y la
        reactivación de la original sigue siendo posible.
        """
        # Arrange — la unidad se da de baja, conservando su placa
        api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {"motivo": "Baja"},
            format="json",
            **proveedor_auth_headers,
        )

        # Act — intentar registrar otra unidad con esa misma placa
        alta = api_client.post(
            "/api/v1/red-operativa/unidades",
            {
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": mock_unidad_emergencia["placa"],
                "contactoproveedor": "555",
                "unidademergencia": "Otra unidad",
                "tipounidademergencia": "Patrulla",
                "gmail": "otra-reactivar@test.com",
            },
            format="json",
            **proveedor_auth_headers,
        )

        # Assert — rechazada, y la original puede reactivarse sin conflicto
        assert alta.status_code == 409
        reactivar = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/reactivar",
            {},
            format="json",
            **proveedor_auth_headers,
        )
        assert reactivar.status_code == 200
        assert reactivar.json()["data"]["activo"] is True
