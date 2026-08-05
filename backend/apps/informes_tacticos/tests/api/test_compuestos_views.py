from unittest.mock import patch

import pytest

URL = "/api/v1/informes-tacticos/compuestos/perdida-senal"
PERIODO = {"desde": "2026-07-01", "hasta": "2026-07-31"}


@pytest.mark.api
class TestPerdidaSenalView:
    def test_returns_200_materializado_with_data(self, api_client, admin_auth_headers):
        fila = {"idunidademergencia": 1, "idaccidente": "A1", "duracion_seg": 200}
        with patch(
            "apps.informes_tacticos.services.informes_compuestos_service.PerdidaSenalRepository.consultar",
            return_value=([fila], "2026-08-02 04:15:15"),
        ):
            response = api_client.get(URL, PERIODO, **admin_auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == [fila]
        assert body["meta"]["materializado"] is True
        assert body["meta"]["ultima_corrida"] == "2026-08-02 04:15:15"

    def test_returns_200_no_materializado_with_null_data(self, api_client, admin_auth_headers):
        with patch(
            "apps.informes_tacticos.services.informes_compuestos_service.PerdidaSenalRepository.consultar",
            return_value=(None, None),
        ):
            response = api_client.get(URL, PERIODO, **admin_auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["data"] is None
        assert body["meta"]["materializado"] is False

    def test_returns_403_with_operador_role(self, api_client, operador_auth_headers):
        response = api_client.get(URL, PERIODO, **operador_auth_headers)
        assert response.status_code == 403

    def test_returns_401_without_token(self, api_client):
        response = api_client.get(URL, PERIODO)
        assert response.status_code == 401


@pytest.mark.api
class TestIndiceCalidadView:
    URL = "/api/v1/informes-tacticos/compuestos/indice-calidad"

    def test_returns_200_with_series(self, api_client, admin_auth_headers):
        serie = [{"periodo": "2026-07-01", "indice_consolidado": 0.9}]
        with patch(
            "apps.informes_tacticos.services.informes_compuestos_service.IndiceCalidadRepository.consultar",
            return_value=(serie, "2026-08-02 05:00:00"),
        ):
            response = api_client.get(self.URL, PERIODO, **admin_auth_headers)

        assert response.status_code == 200
        assert response.json()["data"] == serie

    def test_returns_403_with_operador_role(self, api_client, operador_auth_headers):
        response = api_client.get(self.URL, PERIODO, **operador_auth_headers)
        assert response.status_code == 403


@pytest.mark.api
class TestRendimientoProveedorView:
    URL = "/api/v1/informes-tacticos/compuestos/rendimiento-proveedor"

    def test_returns_200_distinguishing_providers(self, api_client, admin_auth_headers):
        filas = [
            {"idcliente": 100, "pct_rechazo": 0.5, "total_despachos": 2},
            {"idcliente": 200, "pct_rechazo": 0.0, "total_despachos": 1},
        ]
        with patch(
            "apps.informes_tacticos.services.informes_compuestos_service.RendimientoProveedorRepository.consultar",
            return_value=(filas, "2026-08-02 05:00:00"),
        ):
            response = api_client.get(self.URL, PERIODO, **admin_auth_headers)

        assert response.status_code == 200
        assert response.json()["data"] == filas

    def test_returns_403_with_operador_role(self, api_client, operador_auth_headers):
        response = api_client.get(self.URL, PERIODO, **operador_auth_headers)
        assert response.status_code == 403
