import pytest
from rest_framework.test import APIClient


@pytest.mark.api
def test_planes_publicos_sin_jwt_200(mock_pinot, mock_kafka):
    # Arrange
    client = APIClient()
    # Act
    res = client.get("/api/v1/ventas-crm/planes")
    # Assert
    assert res.status_code == 200
    data = res.data["data"]
    assert isinstance(data, list)
    assert all("severidades_desbloqueadas" in p for p in data)
    assert not any(p.get("nombre") == "Legacy Off" for p in data)
    profesional = next(p for p in data if p["nivel"] == "Profesional")
    assert profesional["severidades_desbloqueadas"] == ["Leve", "Moderado"]


@pytest.mark.api
def test_planes_publicos_lista_vacia_200(mock_pinot, mock_kafka):
    # Arrange
    from conftest import PINOT_STORE

    PINOT_STORE["Dim_Plan"] = [
        {
            "idplan": 1,
            "nombre": "Off",
            "nivel": "Básico",
            "limites": "{}",
            "activo": False,
            "precio": 1.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    ]
    client = APIClient()
    # Act
    res = client.get("/api/v1/ventas-crm/planes")
    # Assert
    assert res.status_code == 200
    assert res.data["data"] == []
