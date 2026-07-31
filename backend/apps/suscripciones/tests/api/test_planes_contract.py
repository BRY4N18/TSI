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
        body = response.json()
        assert len(body["data"]) >= 3
        assert all(p["activo"] for p in body["data"])
        pagination = body["meta"]["pagination"]
        assert pagination["limit"] == 20
        assert "next_cursor" in pagination

    def test_list_planes_paginado_y_filtros(
        self, api_client, director_estrategia_billing_auth_headers, pinot_store
    ):
        for i in range(5, 30):
            pinot_store["Dim_Plan"].append(
                {
                    "idplan": i,
                    "nombre": f"Extra {i}",
                    "nivel": "Profesional" if i % 2 == 0 else "Básico",
                    "limites": '{"unidades_max": 1, "usuarios_max": 1, "api_calls_mes": 1}',
                    "activo": True,
                    "precio": 10.0,
                    "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
                }
            )

        r1 = api_client.get(
            "/api/v1/suscripciones/planes?limit=5",
            **director_estrategia_billing_auth_headers,
        )
        assert r1.status_code == 200
        body1 = r1.json()
        assert len(body1["data"]) == 5
        next_cursor = body1["meta"]["pagination"]["next_cursor"]
        assert next_cursor is not None

        r2 = api_client.get(
            f"/api/v1/suscripciones/planes?limit=5&cursor={next_cursor}",
            **director_estrategia_billing_auth_headers,
        )
        assert r2.status_code == 200
        ids1 = {p["idplan"] for p in body1["data"]}
        ids2 = {p["idplan"] for p in r2.json()["data"]}
        assert ids1.isdisjoint(ids2)

        rq = api_client.get(
            "/api/v1/suscripciones/planes?q=Profesional&limit=20",
            **director_estrategia_billing_auth_headers,
        )
        assert rq.status_code == 200
        assert all("profes" in p["nombre"].lower() for p in rq.json()["data"])

        rn = api_client.get(
            "/api/v1/suscripciones/planes?nivel=Empresarial&limit=20",
            **director_estrategia_billing_auth_headers,
        )
        assert rn.status_code == 200
        assert all(p["nivel"] == "Empresarial" for p in rn.json()["data"])

        rain = api_client.get(
            "/api/v1/suscripciones/planes?activo=false&limit=20",
            **director_estrategia_billing_auth_headers,
        )
        assert rain.status_code == 200
        assert all(p["activo"] is False for p in rain.json()["data"])

        # Director omite activo/solo_activos → todas (activos + inactivos)
        rtodas = api_client.get(
            "/api/v1/suscripciones/planes?limit=20",
            **director_estrategia_billing_auth_headers,
        )
        assert rtodas.status_code == 200
        estados = {p["activo"] for p in rtodas.json()["data"]}
        assert True in estados and False in estados

        ract = api_client.get(
            "/api/v1/suscripciones/planes?activo=true&limit=20",
            **director_estrategia_billing_auth_headers,
        )
        assert ract.status_code == 200
        assert all(p["activo"] is True for p in ract.json()["data"])

    def test_list_planes_proveedor_no_ve_inactivos(
        self, api_client, proveedor_billing_auth_headers
    ):
        response = api_client.get(
            "/api/v1/suscripciones/planes?activo=false&limit=20",
            **proveedor_billing_auth_headers,
        )
        assert response.status_code == 200
        assert all(p["activo"] for p in response.json()["data"])

    def test_list_planes_invalid_limit(
        self, api_client, director_estrategia_billing_auth_headers
    ):
        response = api_client.get(
            "/api/v1/suscripciones/planes?limit=0",
            **director_estrategia_billing_auth_headers,
        )
        assert response.status_code == 400

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
