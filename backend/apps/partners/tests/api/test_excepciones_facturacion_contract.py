"""Contrato de `GET /facturacion/excepciones` (T052, BE-DELTA-04/05).

Los dos tipos de excepcion son problemas distintos con soluciones distintas, y
la respuesta debe permitir distinguirlos: si se presentaran juntos sin marca, el
Administrador buscaria una factura que en el caso `no_tarificable` **no existe**.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/facturacion/excepciones"

# 2026-07-10, dentro del período que piden los tests. Calculado, no adivinado:
# la primera versión usó un timestamp de julio de **2025** y el consumo quedaba
# fuera de la ventana, así que no había excedente y la excepción no aparecía.
JULIO_2026 = 1_783_641_600_000


@pytest.fixture
def partner_con_excedente(mock_pinot, mock_kafka):
    """Partner 770 con 15 000 llamadas contra un cupo de 10 000."""
    PINOT_STORE["Dim_Partner"].append({
        "idpartner": 770,
        "idcliente": 770,
        "nombrepartner": "Integradora Sin Tarifa",
        "planapi": "Profesional",
        "contacto_tecnico_nombre": "Ana",
        "contacto_tecnico_gmail": "ana@demo.com",
        "limitellamadasmes": 10,
        "limitellamadasminuto": 120,
        "sandbox_activado": 1,
        "sandbox_expiracion": 253402300799000,
        "fecha_suspension": "",
        "motivo_suspension": "",
        "activo": True,
        "fecha_actualizacion": 1,
    })
    return 770


def _consumo(idpartner: int, cuantas: int, fechahora: int) -> None:
    for i in range(cuantas):
        PINOT_STORE["Fact_APIIntegracion"].append({
            "idapiintegracion": 770_000 + i,
            "idpartner": idpartner,
            "idcliente": idpartner,
            "idservicio": 1,
            "idestadointegracion": 2,
            "entorno": "Producción",
            "llamadas": 1,
            "errores": 0,
            "latencia": 90.0,
            "activo": True,
            "fechahora": fechahora,
            "fecha_actualizacion": fechahora,
        })


class TestPermisos:
    def test_sin_autenticacion_returns_401(self, api_client):
        assert api_client.get(URL).status_code == 401

    def test_un_partner_no_puede_consultarla(self, api_client, partner_auth_headers):
        """Es una vista de gestión que cruza datos de varios partners."""
        assert api_client.get(URL, **partner_auth_headers).status_code == 403

    def test_el_administrador_si(self, api_client, admin_auth_headers):
        assert api_client.get(URL, **admin_auth_headers).status_code == 200

    def test_el_desarrollador_de_apis_tambien(self, api_client, devapis_auth_headers):
        assert api_client.get(URL, **devapis_auth_headers).status_code == 200


class TestReintentosAgotados:
    def test_lista_la_factura_con_sus_tres_intentos(
        self, api_client, partner_con_excedente, admin_auth_headers
    ):
        # Arrange — así la deja `programar_reintento` al agotarlos
        PINOT_STORE["Fact_Factura"].append({
            "id_factura": "FAC-AGOTADA",
            "id_cliente": 770,
            "tipo": "excedente_api",
            "periodo": "2026-07",
            # `monto_total`, la columna que existe de verdad: publicar `monto`
            # era el bug que Pinot descartaba en silencio.
            "monto_base": 42.0,
            "monto_total": 42.0,
            "estado_pago": "Pendiente",
            "reintentos": 4,
            "resultado_ultimo_reintento": "agotados: timeout del emisor",
            "proximo_reintento": 0,
            "activo": True,
            "fecha_emision": 1,
            "fecha_actualizacion": 1,
        })

        # Act
        data = api_client.get(
            f"{URL}?anio=2026&mes=7", **admin_auth_headers
        ).json()["data"]

        # Assert
        agotada = next(e for e in data if e["tipo"] == "reintentos_agotados")
        assert agotada["id_factura"] == "FAC-AGOTADA"
        assert agotada["importe"] == 42.0
        assert agotada["intentos"] == 4
        assert "timeout" in agotada["ultimo_resultado"]

    def test_una_factura_con_reintentos_pendientes_NO_es_excepcion(
        self, api_client, partner_con_excedente, admin_auth_headers
    ):
        """Todavía se va a reintentar sola: no requiere acción humana."""
        # Arrange
        PINOT_STORE["Fact_Factura"].append({
            "id_factura": "FAC-EN-CURSO",
            "id_cliente": 770,
            "tipo": "excedente_api",
            "periodo": "2026-07",
            "monto_base": 10.0,
            "monto_total": 10.0,
            "estado_pago": "Pendiente",
            "reintentos": 1,
            "resultado_ultimo_reintento": "timeout del emisor",
            "proximo_reintento": 999,
            "activo": True,
            "fecha_emision": 1,
            "fecha_actualizacion": 1,
        })

        # Act
        data = api_client.get(f"{URL}?anio=2026&mes=7", **admin_auth_headers).json()["data"]

        # Assert
        assert all(e.get("id_factura") != "FAC-EN-CURSO" for e in data)


class TestNoTarificables:
    def test_un_partner_sin_tarifa_aparece_aunque_NO_haya_factura(
        self, api_client, partner_con_excedente, admin_auth_headers
    ):
        """🎯 BE-DELTA-05 — antes este caso solo existía como un correo.

        Es el que RN-APM-014 más teme: ingreso real no cobrado **en silencio**.
        """
        # Arrange — excedente real, plan sin `precio_excedente_llamada`
        _consumo(770, 15, JULIO_2026)

        # Act
        data = api_client.get(f"{URL}?anio=2026&mes=7", **admin_auth_headers).json()["data"]

        # Assert
        sin_tarifa = [e for e in data if e["tipo"] == "no_tarificable"]
        assert len(sin_tarifa) == 1
        assert sin_tarifa[0]["idpartner"] == 770

    def test_el_no_tarificable_NO_lleva_importe_cero(
        self, api_client, partner_con_excedente, admin_auth_headers
    ):
        """🎯 Un `0.0` diría «se facturó nada»; la verdad es que no se pudo calcular."""
        # Arrange
        _consumo(770, 15, JULIO_2026)

        # Act
        data = api_client.get(f"{URL}?anio=2026&mes=7", **admin_auth_headers).json()["data"]

        # Assert
        sin_tarifa = next(e for e in data if e["tipo"] == "no_tarificable")
        assert sin_tarifa["importe"] is None
        assert sin_tarifa["importe"] != 0.0
        assert sin_tarifa["id_factura"] is None

    def test_un_partner_sin_excedente_no_aparece(
        self, api_client, partner_con_excedente, admin_auth_headers
    ):
        # Arrange — 5 llamadas contra un cupo de 10: no hay excedente
        _consumo(770, 5, JULIO_2026)

        # Act
        data = api_client.get(f"{URL}?anio=2026&mes=7", **admin_auth_headers).json()["data"]

        # Assert
        assert [e for e in data if e["tipo"] == "no_tarificable"] == []


class TestMeta:
    def test_el_meta_cuenta_cada_tipo_por_separado(
        self, api_client, partner_con_excedente, admin_auth_headers
    ):
        # Arrange
        _consumo(770, 15, JULIO_2026)

        # Act
        meta = api_client.get(f"{URL}?anio=2026&mes=7", **admin_auth_headers).json()["meta"]

        # Assert
        assert meta["no_tarificables"] == 1
        assert meta["reintentos_agotados"] == 0

    def test_mes_invalido_returns_400(self, api_client, admin_auth_headers):
        assert api_client.get(f"{URL}?anio=2026&mes=13", **admin_auth_headers).status_code == 400
