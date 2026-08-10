"""Dim_CredencialAPI — el secreto nunca sale de la peticion (RNF-PON-002).

La afirmacion central de este archivo es negativa: comprobar que el secreto en
claro **no** aparece en el evento publicado. Un test que solo verifique que el
hash se guarda pasaria igual aunque el secreto viajara al lado.
"""

from __future__ import annotations

import json

import pytest

from apps.partners.domain_constants import NUNCA_EXPIRA
from conftest import PINOT_STORE
from core.repositories.partners.credencial_repository import CredencialRepository

pytestmark = [pytest.mark.django_db, pytest.mark.repository]

SECRETO_EN_CLARO = "secreto-que-jamas-debe-persistirse-42"
HASH = "$2b$12$hashficticiopararepositorio"

BASE = {
    "idpartner": 1,
    "idcliente": 100,
    "client_secret_hash": HASH,
    "nombre_credencial": "plataforma-siniestros",
    "entorno": "Sandbox",
}


class TestElSecretoNoViajaAlEvento:
    def test_create_publica_el_hash_y_no_el_secreto(self, mock_pinot, mock_kafka):
        # Act
        fila = CredencialRepository().create(BASE)

        # Assert
        assert fila["client_secret_hash"] == HASH
        assert "client_secret" not in fila

    def test_create_when_alguien_cuela_el_secreto_no_llega_al_topic(
        self, mock_pinot, mock_kafka
    ):
        """El repositorio construye la fila campo a campo, no con `**data`.

        Por eso una clave extra —aunque la pase quien lo llame— se queda fuera
        del evento en vez de acabar en Kafka para siempre.
        """
        # Act
        CredencialRepository().create({**BASE, "client_secret": SECRETO_EN_CLARO})

        # Assert — el secreto no aparece en NINGUNA fila publicada
        publicado = json.dumps(PINOT_STORE["Dim_CredencialAPI"], default=str)
        assert SECRETO_EN_CLARO not in publicado

    def test_create_el_evento_solo_lleva_las_claves_del_esquema(self, mock_pinot, mock_kafka):
        # Act
        fila = CredencialRepository().create({**BASE, "campo_inventado": "x"})

        # Assert
        assert "campo_inventado" not in fila


class TestVigencia:
    def test_create_when_sin_fecha_usa_el_centinela_de_no_expira(self, mock_pinot, mock_kafka):
        # Act
        fila = CredencialRepository().create(BASE)

        # Assert
        assert fila["fecha_expiracion"] == NUNCA_EXPIRA

    def test_vencidas_no_alcanza_a_las_de_produccion(self, mock_pinot, mock_kafka):
        """El centinela esta en el ano 9999 —en el FUTURO— precisamente para
        que la comparacion `fecha_expiracion < ahora` nunca las devuelva.

        Con el centinela anterior (`Long.MIN_VALUE`) esta consulta habria
        revocado todas las credenciales de produccion del sistema.
        """
        # Arrange
        repo = CredencialRepository()
        repo.create({**BASE, "entorno": "Producción", "fecha_expiracion": NUNCA_EXPIRA})
        vencida = repo.create({**BASE, "nombre_credencial": "vieja", "fecha_expiracion": 1000})

        # Act
        resultado = repo.vencidas(ahora_ms=2000)

        # Assert
        ids = [c["idcredencial"] for c in resultado]
        assert vencida["idcredencial"] in ids
        assert len(ids) == 1

    def test_vencidas_ignora_las_ya_inactivas(self, mock_pinot, mock_kafka):
        """Reprocesar una credencial ya desactivada duplicaria su evento."""
        # Arrange
        repo = CredencialRepository()
        cred = repo.create({**BASE, "fecha_expiracion": 1000})
        repo.desactivar(cred["idcredencial"])

        # Act
        resultado = repo.vencidas(ahora_ms=2000)

        # Assert
        assert resultado == []


class TestNombreUnicoEntreActivas:
    def test_nombre_en_uso_when_activa_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CredencialRepository()
        repo.create(BASE)

        # Act / Assert — RN-PON-014
        assert repo.nombre_en_uso(1, "Sandbox", "plataforma-siniestros") is True

    def test_nombre_en_uso_when_otro_entorno_returns_false(self, mock_pinot, mock_kafka):
        """El nombre es unico por entorno: pruebas y produccion no colisionan."""
        # Arrange
        repo = CredencialRepository()
        repo.create(BASE)

        # Act / Assert
        assert repo.nombre_en_uso(1, "Producción", "plataforma-siniestros") is False

    def test_nombre_en_uso_when_liberado_returns_false(self, mock_pinot, mock_kafka):
        """Un nombre liberado por revocacion puede reutilizarse."""
        # Arrange
        repo = CredencialRepository()
        cred = repo.create(BASE)
        repo.desactivar(cred["idcredencial"])

        # Act / Assert
        assert repo.nombre_en_uso(1, "Sandbox", "plataforma-siniestros") is False

    def test_nombre_en_uso_when_excluida_returns_false(self, mock_pinot, mock_kafka):
        """La revocacion de #09 emite el reemplazo con el MISMO nombre.

        Sin `excluir`, Pinot todavia veria activa la que acaba de desactivarse
        y daria una colision falsa.
        """
        # Arrange
        repo = CredencialRepository()
        cred = repo.create(BASE)

        # Act / Assert
        assert (
            repo.nombre_en_uso(
                1, "Sandbox", "plataforma-siniestros", excluir=cred["idcredencial"]
            )
            is False
        )


class TestListado:
    def test_list_by_partner_no_mezcla_partners(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CredencialRepository()
        repo.create(BASE)
        repo.create({**BASE, "idpartner": 2, "nombre_credencial": "otra"})

        # Act
        resultado = repo.list_by_partner(1)

        # Assert
        assert len(resultado) == 1
        assert resultado[0]["idpartner"] == 1

    def test_list_by_partner_when_solo_activas_excluye_las_desactivadas(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = CredencialRepository()
        viva = repo.create(BASE)
        muerta = repo.create({**BASE, "nombre_credencial": "revocada"})
        repo.desactivar(muerta["idcredencial"])

        # Act
        resultado = repo.list_by_partner(1, solo_activas=True)

        # Assert
        assert [c["idcredencial"] for c in resultado] == [viva["idcredencial"]]

    def test_desactivar_when_inexistente_returns_none(self, mock_pinot, mock_kafka):
        # Act / Assert
        assert CredencialRepository().desactivar(404404) is None
