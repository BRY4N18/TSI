import pytest

from conftest import PINOT_STORE

pytestmark = pytest.mark.api


class TestPlanesContract:
    def test_list_planes(self, api_client, proveedor_billing_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/suscripciones/planes", **proveedor_billing_auth_headers
        )
        # Assert
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 3

    def test_create_plan_director(self, api_client, director_estrategia_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones/planes",
            {
                "nombre": "Nuevo",
                "precio": 55,
                "nivel": "Básico",
                "limites": {
                    "unidades_max": 2,
                    "usuarios_max": 2,
                    "api_calls_mes": 100,
                },
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="plan-1",
            **director_estrategia_billing_auth_headers,
        )
        assert response.status_code == 201

    def test_create_plan_admin_forbidden(self, api_client, admin_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones/planes",
            {
                "nombre": "Bloqueado",
                "precio": 55,
                "nivel": "Básico",
                "limites": {
                    "unidades_max": 2,
                    "usuarios_max": 2,
                    "api_calls_mes": 100,
                },
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="plan-admin-forbid",
            **admin_billing_auth_headers,
        )
        assert response.status_code == 403


class TestAltaSuscripcionContract:
    def test_alta_conflict(self, api_client, proveedor_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones",
            {"idplan": 2},
            format="json",
            HTTP_IDEMPOTENCY_KEY="alta-1",
            **proveedor_billing_auth_headers,
        )
        assert response.status_code == 409

    def test_mi_suscripcion(self, api_client, proveedor_billing_auth_headers):
        response = api_client.get(
            "/api/v1/suscripciones/mia", **proveedor_billing_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "Activa"
        assert "acceso_permitido" in response.json()["data"]


class TestMetodoPagoContract:
    def test_registrar(self, api_client, proveedor_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones/metodos-pago",
            {"tipo": "tarjeta", "datos_pasarela": {"numero": "4111111111111111"}},
            format="json",
            HTTP_IDEMPOTENCY_KEY="mp-1",
            **proveedor_billing_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["ultimosdigitos"] == "1111"


class TestReintentarCobroContract:
    def test_conflict_sin_suspendida(self, api_client, proveedor_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones/mia/reintentar-cobro",
            format="json",
            HTTP_IDEMPOTENCY_KEY="rc-1",
            **proveedor_billing_auth_headers,
        )
        assert response.status_code == 409


class TestCambioPlanContract:
    def test_solicitar(self, api_client, proveedor_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones/solicitudes-cambio-plan",
            {"idplansolicitado": 2, "motivo": "upgrade"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="cp-1",
            **proveedor_billing_auth_headers,
        )
        assert response.status_code == 201


class TestCancelacionContract:
    def test_cancelar(self, api_client, proveedor_billing_auth_headers):
        response = api_client.post(
            "/api/v1/suscripciones/mia/cancelar",
            {"motivocancelacion": "fin"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="can-1",
            **proveedor_billing_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "Cancelada"


class TestFacturasContract:
    def test_list_empty(self, api_client, proveedor_billing_auth_headers):
        response = api_client.get(
            "/api/v1/suscripciones/facturas", **proveedor_billing_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"] == []


class TestIdempotencyKeyContract:
    def test_replay_returns_cached(
        self, api_client, director_estrategia_billing_auth_headers
    ):
        payload = {
            "nombre": "Idem",
            "precio": 12,
            "nivel": "Básico",
            "limites": {
                "unidades_max": 1,
                "usuarios_max": 1,
                "api_calls_mes": 1,
            },
        }
        r1 = api_client.post(
            "/api/v1/suscripciones/planes",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="idem-plan",
            **director_estrategia_billing_auth_headers,
        )
        r2 = api_client.post(
            "/api/v1/suscripciones/planes",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="idem-plan",
            **director_estrategia_billing_auth_headers,
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["data"]["idplan"] == r2.json()["data"]["idplan"]
