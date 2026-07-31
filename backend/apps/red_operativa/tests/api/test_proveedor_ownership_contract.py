"""API ownership: Proveedor JWT, Admin sin override, unidad ajena 403."""

from __future__ import annotations

import pytest


@pytest.fixture
def mock_unidad_ajena(mock_pinot, mock_kafka, pinot_store):
    """Unidad perteneciente a otro cliente (idcliente=99)."""
    pinot_store["Dim_Cliente"].append(
        {
            "idcliente": 99,
            "nombre": "Otro Proveedor",
            "razon_social": "Otro S.A.",
            "tipo": "Corporativo",
            "nit_identificacion": "999",
            "logo_url": None,
            "admin_local_id": 999,
            "estado": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    unidad = {
        "idunidademergencia": 599,
        "idcliente": 99,
        "idcondado": 1,
        "tipopropiedad": "Externa",
        "placa": "AJENA-99",
        "capacidad": "2",
        "contactoproveedor": "111",
        "unidademergencia": "Unidad Ajena",
        "tipounidademergencia": "Patrulla",
        "activo": True,
        "latitud": 19.0,
        "longitud": -99.0,
        "fecha_actualizacion": "2026-07-21T00:00:00+00:00",
    }
    pinot_store["Dim_UnidadEmergencia"].append(unidad)
    return unidad


@pytest.mark.api
class TestProveedorOwnershipContract:
    def test_post_sin_idcliente_body_asigna_cliente_jwt(
        self, api_client, proveedor_auth_headers, pinot_store
    ):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            {
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": "OWN-001",
                "contactoproveedor": "555",
                "unidademergencia": "Own Unit",
                "tipounidademergencia": "Ambulancia",
                "gmail": "own-unit@test.com",
            },
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        created = next(
            u for u in pinot_store["Dim_UnidadEmergencia"] if u.get("placa") == "OWN-001"
        )
        assert created["idcliente"] == 1

    def test_get_unidad_ajena_returns_403(
        self, api_client, proveedor_auth_headers, mock_unidad_ajena
    ):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_ajena['idunidademergencia']}",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_admin_override_returns_403(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.patch(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            {"capacidad": "99"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 403
