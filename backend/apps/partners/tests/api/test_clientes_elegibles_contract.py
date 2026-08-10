"""BE-DELTA-03 — `GET /api/v1/partners/clientes-elegibles` (FR-UI-004).

Detectado al ejecutar el quickstart contra la app real: el formulario de alta
elige el cliente por nombre legible, pero **no existía ningún endpoint que
expusiera clientes**, así que el combobox quedaba vacío y el registro era
inalcanzable desde la UI. Los tests de componente no lo cazaron porque solo
comprobaban que el control fuera un `<select>`.

Devuelve solo los elegibles, de modo que el usuario no pueda provocar el 422
de «sin suscripción» ni el 409 de duplicado: prevenir el error es mejor que
explicarlo (Principio IV).
"""

from __future__ import annotations

import json

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/partners/clientes-elegibles"

LIMITES = json.dumps({"api_calls_mes": 10000, "api_calls_minuto": 120})


def _cliente(idcliente, nombre, estado="Activo"):
    # `Dim_Cliente` NO tiene columna `activo`: la baja se expresa en `estado`.
    # Verificado contra el esquema real en Pinot.
    PINOT_STORE["Dim_Cliente"].append(
        {"idcliente": idcliente, "nombre": nombre, "estado": estado}
    )


def _suscripcion(idcliente, estado="Activa", activo=True):
    PINOT_STORE["Dim_Plan"].append(
        {"idplan": idcliente, "nombre": "Profesional", "limites": LIMITES, "activo": True}
    )
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": idcliente,
            "idcliente": idcliente,
            "idplan": idcliente,
            "estado": estado,
            "activo": activo,
            "fecha_inicio": 1,
        }
    )


def _partner(idpartner, idcliente):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": idpartner,
            "idcliente": idcliente,
            "nombrepartner": "Ya registrado",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "",
            "limitellamadasmes": -1,
            "limitellamadasminuto": -1,
            "sandbox_activado": 0,
            "sandbox_expiracion": 0,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )


class TestElegibilidad:
    def test_devuelve_cliente_con_suscripcion_y_sin_partner(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        # Arrange
        _cliente(970, "Aseguradora Elegible")
        _suscripcion(970)

        # Act
        response = api_client.get(URL, **devapis_auth_headers)

        # Assert
        assert response.status_code == 200
        assert {"idcliente": 970, "nombre": "Aseguradora Elegible"} in response.json()["data"]

    def test_excluye_al_cliente_que_ya_tiene_partner(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        """Evita que el usuario pueda provocar el 409 `partner_duplicado`."""
        # Arrange
        _cliente(971, "Ya tiene partner")
        _suscripcion(971)
        _partner(9710, 971)

        # Act
        ids = [c["idcliente"] for c in api_client.get(URL, **devapis_auth_headers).json()["data"]]

        # Assert
        assert 971 not in ids

    def test_excluye_al_cliente_sin_suscripcion_vigente(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        """Evita que el usuario pueda provocar el 422 `sin_suscripcion`."""
        # Arrange
        _cliente(972, "Sin suscripción")
        _suscripcion(972, estado="Cancelada")

        # Act
        ids = [c["idcliente"] for c in api_client.get(URL, **devapis_auth_headers).json()["data"]]

        # Assert
        assert 972 not in ids

    def test_excluye_al_cliente_dado_de_baja(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        # Arrange
        _cliente(973, "Cliente de baja", estado="Inactivo")
        _suscripcion(973)

        # Act
        ids = [c["idcliente"] for c in api_client.get(URL, **devapis_auth_headers).json()["data"]]

        # Assert
        assert 973 not in ids

    def test_devuelve_una_lista_aunque_no_haya_nada_que_anadir(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        """Sin candidatos propios responde 200 con lista, nunca un error."""
        # Act
        response = api_client.get(URL, **devapis_auth_headers)

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    def test_ordena_alfabeticamente_por_nombre(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        """Una lista larga sin orden obliga al usuario a buscar a ojo."""
        # Arrange
        _cliente(975, "Zeta Seguros")
        _suscripcion(975)
        _cliente(976, "Alfa Seguros")
        _suscripcion(976)

        # Act
        nombres = [c["nombre"] for c in api_client.get(URL, **devapis_auth_headers).json()["data"]]

        # Assert
        assert nombres == sorted(nombres, key=str.lower)


class TestAcceso:
    def test_sin_token_returns_401(self, api_client, mock_pinot, mock_kafka):
        # Act / Assert
        assert api_client.get(URL).status_code == 401

    def test_partner_no_puede_listar_clientes(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """Es una pantalla de gestor: el partner no enumera clientes ajenos."""
        # Act / Assert
        assert api_client.get(URL, **partner_auth_headers).status_code == 403

    def test_solo_expone_id_y_nombre(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        """Nada de datos del cliente que la pantalla no necesite."""
        # Arrange
        _cliente(974, "Aseguradora Sur")
        _suscripcion(974)

        # Act
        data = api_client.get(URL, **devapis_auth_headers).json()["data"]

        # Assert
        assert all(set(c.keys()) == {"idcliente", "nombre"} for c in data)
