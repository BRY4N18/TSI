import pytest
from rest_framework.test import APIClient


PAYLOAD = {
    "nombres": "Ana",
    "apellidos": "Perez",
    "gmail": "api.ana@ex.com",
    "empresa": "Demo SA",
    "tipo_organizacion": "Privado",
    "cargo": "Compras",
    "telefono": "0991234567",
    "como_nos_conocio": "web",
}


@pytest.mark.api
def test_registro_publico_201(mock_pinot, mock_kafka):
    client = APIClient()
    res = client.post("/api/v1/ventas-crm/prospectos", PAYLOAD, format="json")
    assert res.status_code == 201
    assert res.data["data"]["etapa_actual"] == "Nuevo"
    assert res.data["data"]["asignacion_automatica"]["ok"] is True


@pytest.mark.api
def test_listado_gerente_solo_propios(mock_pinot, mock_kafka, gerente_ventas_auth_headers):
    client = APIClient()
    client.post("/api/v1/ventas-crm/prospectos", PAYLOAD, format="json")
    res = client.get("/api/v1/ventas-crm/prospectos", **gerente_ventas_auth_headers)
    assert res.status_code == 200
    assert all(p["idusuario"] == 20 for p in res.data["data"])


@pytest.mark.api
def test_pipeline_y_conversion_contract(
    mock_pinot, mock_kafka, gerente_ventas_auth_headers
):
    client = APIClient()
    created = client.post(
        "/api/v1/ventas-crm/prospectos",
        {**PAYLOAD, "gmail": "api.conv@ex.com"},
        format="json",
    ).data["data"]
    pid = created["idprospecto"]
    cur = "Nuevo"
    for nxt in ["Contactado", "Calificado", "Propuesta", "Negociación"]:
        res = client.post(
            f"/api/v1/ventas-crm/prospectos/{pid}/pipeline",
            {"etapa_nueva": nxt, "etapa_actual_esperada": cur},
            format="json",
            **gerente_ventas_auth_headers,
        )
        assert res.status_code == 201
        cur = nxt
    res = client.post(
        f"/api/v1/ventas-crm/prospectos/{pid}/conversion",
        {
            "tipo": "Aseguradora",
            "nit_identificacion": "1790099",
            "etapa_actual_esperada": "Negociación",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="22222222-2222-2222-2222-222222222222",
        **gerente_ventas_auth_headers,
    )
    assert res.status_code == 201
    assert res.data["data"]["cliente"]["estado"] == "Activo"


@pytest.mark.api
def test_entrada_directa_admin_only(
    mock_pinot, mock_kafka, admin_crm_auth_headers, gerente_ventas_auth_headers
):
    client = APIClient()
    body = {
        "nombre": "X",
        "razon_social": "Y",
        "tipo": "Municipio",
        "nit_identificacion": "1760099",
        "admin_local": {"nombres": "Ana", "apellidos": "Admin", "gmail": "entrada.directa.admin@ex.com"},
    }
    denied = client.post(
        "/api/v1/ventas-crm/clientes/entrada-directa",
        body,
        format="json",
        **gerente_ventas_auth_headers,
    )
    assert denied.status_code == 403
    ok = client.post(
        "/api/v1/ventas-crm/clientes/entrada-directa",
        body,
        format="json",
        **admin_crm_auth_headers,
    )
    assert ok.status_code == 201
    assert ok.data["data"]["idprospecto"] is None
