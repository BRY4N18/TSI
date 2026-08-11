"""Consulta del estado de acceso y cola del Administrador (T046, T062).

Escenarios N y P. Dos lecturas con dos audiencias y dos permisos distintos.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.api]

ESTADO = "/api/v1/partners/1/estado-acceso"
COLA = "/api/v1/partners/cola-acceso"


class TestEstadoDeUnPartner:
    def test_el_partner_SUSPENDIDO_puede_consultar_el_suyo(
        self, api_client, partner_suspendido, partner_auth_headers
    ):
        """🎯 RN-PAC-016 — escenario N. Bloquearlo convertiría la suspensión en
        un callejón sin salida: no sabría ni por qué se le cortó ni cuánto debe."""
        # Act
        respuesta = api_client.get(ESTADO, **partner_auth_headers)

        # Assert
        assert respuesta.status_code == 200
        data = respuesta.json()["data"]
        assert data["activo"] is False
        assert data["motivo_suspension"]
        assert data["fecha_suspension"]

    def test_incluye_su_historial_para_que_entienda_el_corte(
        self, api_client, partner_suspendido, partner_auth_headers
    ):
        # Act
        data = api_client.get(ESTADO, **partner_auth_headers).json()["data"]

        # Assert
        tipos = {e["tipo_cambio"] for e in data["historial"]}
        assert "suspension_automatica" in tipos
        assert "desactivacion_por_cascada" in tipos

    def test_lista_sus_credenciales_sin_secretos(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        # Act
        data = api_client.get(ESTADO, **partner_auth_headers).json()["data"]

        # Assert
        assert len(data["credenciales"]) == 3
        for credencial in data["credenciales"]:
            assert "client_secret" not in credencial
            assert "client_secret_hash" not in credencial

    def test_consultar_el_estado_de_otro_partner_returns_403(
        self, api_client, partner_con_credenciales, partner_ajeno_auth_headers
    ):
        assert api_client.get(ESTADO, **partner_ajeno_auth_headers).status_code == 403

    def test_el_administrador_puede_consultar_cualquiera(
        self, api_client, partner_con_credenciales, admin_auth_headers
    ):
        assert api_client.get(ESTADO, **admin_auth_headers).status_code == 200

    def test_sin_autenticacion_returns_401(self, api_client, partner_con_credenciales):
        assert api_client.get(ESTADO).status_code == 401


class TestColaDelAdministrador:
    def test_incluye_a_los_suspendidos(
        self, api_client, partner_suspendido, admin_auth_headers
    ):
        # Act
        respuesta = api_client.get(COLA, **admin_auth_headers)

        # Assert
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert any(i["idpartner"] == 1 and i["activo"] is False for i in cuerpo["data"])
        assert cuerpo["meta"]["suspendidos"] == 1

    def test_incluye_a_los_avisados_con_sus_dias_de_mora(
        self, api_client, partner_con_credenciales, factura_excedente_vencida,
        admin_auth_headers,
    ):
        # Arrange — en mora y ya avisado
        from apps.partners.services.evaluacion_mora_service import EvaluacionMoraService
        from conftest import PINOT_STORE

        factura_excedente_vencida(idcliente=1, dias_vencida=11)
        partner = next(p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == 1)
        EvaluacionMoraService().evaluar_partner(partner)

        # Act
        cuerpo = api_client.get(COLA, **admin_auth_headers).json()

        # Assert
        item = next(i for i in cuerpo["data"] if i["idpartner"] == 1)
        assert item["dias_mora"] == 11
        assert item["ultimo_aviso"] == "T-5"
        assert cuerpo["meta"]["en_mora"] == 1

    def test_un_partner_en_mora_SIN_aviso_aun_no_entra_en_la_cola(
        self, api_client, partner_con_credenciales, factura_excedente_vencida,
        admin_auth_headers,
    ):
        """La cola es de trabajo: un moroso al que aún no toca avisar no
        requiere ninguna decisión humana todavía."""
        # Arrange — 2 días de mora: aún no llega a T-10
        factura_excedente_vencida(idcliente=1, dias_vencida=2)

        # Act
        cuerpo = api_client.get(COLA, **admin_auth_headers).json()

        # Assert
        assert cuerpo["data"] == []

    def test_un_partner_no_puede_ver_la_cola_returns_403(
        self, api_client, partner_suspendido, partner_auth_headers
    ):
        """Es la vista de trabajo del Administrador, no la del partner."""
        assert api_client.get(COLA, **partner_auth_headers).status_code == 403

    def test_filtra_por_estado(
        self, api_client, partner_suspendido, admin_auth_headers
    ):
        # Act
        solo_mora = api_client.get(f"{COLA}?estado=en_mora", **admin_auth_headers)

        # Assert — el suspendido no aparece bajo el filtro de mora
        assert solo_mora.json()["data"] == []
