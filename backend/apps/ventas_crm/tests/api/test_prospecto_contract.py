import pytest

pytestmark = pytest.mark.api

def test_registrar_prospecto_publico_asigna_gerente_ventas(api_client, mock_kafka):
    response = api_client.post("/api/v1/ventas-crm/prospectos", {
        "nombres": "Laura", "apellidos": "Comercial", "gmail": "laura@example.com",
        "empresa": "Acme", "tipo_organizacion": "Privado", "cargo": "Compras",
        "telefono": "3000000000", "como_nos_conocio": "web",
    }, format="json")
    assert response.status_code == 201
    assert response.data["data"]["idusuario"] == 20

def test_listado_gerente_requiere_autenticacion(api_client):
    assert api_client.get("/api/v1/ventas-crm/prospectos").status_code == 401
