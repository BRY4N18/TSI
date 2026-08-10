"""RNF-PON-002 — generacion y hash de secretos (RF-O49.2)."""

from __future__ import annotations

import pytest

from apps.partners.services.secreto_service import BCRYPT_ROUNDS, SecretoService

pytestmark = [pytest.mark.unit]


class TestGeneracion:
    def test_generar_produce_secretos_distintos(self):
        # Arrange
        servicio = SecretoService()

        # Act
        secretos = {servicio.generar() for _ in range(50)}

        # Assert — ninguna colision en 50 generaciones
        assert len(secretos) == 50

    def test_generar_tiene_entropia_suficiente(self):
        """32 bytes -> ~43 caracteres en base64 url-safe."""
        # Act
        secreto = SecretoService().generar()

        # Assert
        assert len(secreto) >= 40

    def test_generar_es_url_safe(self):
        """Debe poder viajar en cabeceras y copiarse sin escapes."""
        # Act
        secreto = SecretoService().generar()

        # Assert
        assert all(c.isalnum() or c in "-_" for c in secreto)


class TestHash:
    def test_hash_no_es_el_secreto(self):
        """Lo unico que se persiste es el hash."""
        # Arrange
        servicio = SecretoService()
        secreto = servicio.generar()

        # Act
        hashed = servicio.hash(secreto)

        # Assert
        assert hashed != secreto
        assert hashed.startswith("$2b$")

    def test_hash_usa_el_factor_de_coste_acordado(self):
        """No bajarlo para ganar latencia: la mitigacion es cachear, no debilitar."""
        # Act
        hashed = SecretoService().hash("secreto-de-prueba")

        # Assert
        assert f"${BCRYPT_ROUNDS}$" in hashed

    def test_dos_hashes_del_mismo_secreto_son_distintos(self):
        """bcrypt sala cada hash: sin sal, dos iguales revelarian que lo son."""
        # Arrange
        servicio = SecretoService()

        # Act
        a = servicio.hash("mismo-secreto")
        b = servicio.hash("mismo-secreto")

        # Assert
        assert a != b


class TestVerificacion:
    def test_verificar_when_correcto_returns_true(self):
        # Arrange
        servicio = SecretoService()
        secreto = servicio.generar()
        hashed = servicio.hash(secreto)

        # Act / Assert
        assert servicio.verificar(secreto, hashed) is True

    def test_verificar_when_incorrecto_returns_false(self):
        # Arrange
        servicio = SecretoService()
        hashed = servicio.hash(servicio.generar())

        # Act / Assert
        assert servicio.verificar("secreto-equivocado", hashed) is False

    def test_verificar_when_hash_malformado_returns_false_sin_excepcion(self):
        """Un hash corrupto no debe filtrar detalle del almacenamiento."""
        # Act / Assert
        assert SecretoService().verificar("x", "esto-no-es-un-hash") is False
        assert SecretoService().verificar("x", "") is False


class TestClientId:
    def test_client_id_no_revela_el_secreto(self):
        """El client_id viaja en cada peticion y puede acabar en logs."""
        # Arrange
        servicio = SecretoService()
        secreto = servicio.generar()

        # Act
        client_id = servicio.generar_client_id(12, 88)

        # Assert
        assert secreto not in client_id
        assert client_id == "tsi-p12-c88"
