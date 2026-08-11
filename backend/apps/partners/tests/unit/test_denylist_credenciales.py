"""Lista de denegacion: alta, consulta, retirada y TTL (T007, T008).

El test de ORDEN (`TestOrdenFrenteALaCache`) es el que mas importa: fija el
contrato para el dia en que #08 anada la cache positiva de bcrypt que su
Decision 2 contempla y que **no llego a implementarse**. Si esa cache se
consultara ANTES que esta lista, una optimizacion de rendimiento pasaria a
*alargar* la ventana de exposicion en vez de cerrarla.
"""

from __future__ import annotations

import pytest

from apps.partners.services.denylist_credenciales import DenylistCredenciales

pytestmark = pytest.mark.unit


class TestAltaYConsulta:
    def test_una_credencial_denegada_esta_en_la_lista(self):
        # Arrange
        denylist = DenylistCredenciales()

        # Act
        denylist.denegar(101)

        # Assert
        assert denylist.contiene(101) is True

    def test_una_credencial_que_nadie_denego_no_esta(self):
        assert DenylistCredenciales().contiene(999) is False

    def test_denegar_varias_de_golpe(self):
        """Lo usa la cascada de suspensión: N credenciales a la vez (§ 15 D4)."""
        # Arrange
        denylist = DenylistCredenciales()

        # Act
        total = denylist.denegar_varias([101, 102, 103])

        # Assert
        assert total == 3
        assert all(denylist.contiene(i) for i in (101, 102, 103))

    def test_retirar_levanta_la_denegacion(self):
        """La reactivación lo necesita: sin esto el partner reactivado seguiría
        rechazado hasta que caducase el TTL."""
        # Arrange
        denylist = DenylistCredenciales()
        denylist.denegar(101)

        # Act
        denylist.retirar(101)

        # Assert
        assert denylist.contiene(101) is False


class TestTTL:
    def test_la_entrada_caduca(self):
        """Pasado el TTL, Pinot ya refleja la revocación y la lista sobra: es un
        puente, no una fuente de verdad paralela (RN-PAC-012)."""
        # Arrange — TTL de 0 s: caduca de inmediato, sin `sleep` en el test
        denylist = DenylistCredenciales(ttl_segundos=0)

        # Act
        denylist.denegar(101)

        # Assert
        assert denylist.contiene(101) is False

    def test_el_ttl_es_configurable_sin_tocar_codigo(self, settings):
        # Arrange
        settings.PARTNERS_DENYLIST_TTL_SEGUNDOS = 120

        # Act / Assert
        assert DenylistCredenciales().ttl_segundos == 120

    def test_el_ttl_por_defecto_supera_la_ventana_de_ingesta(self):
        """Pinot tarda 5-15 s. Un TTL menor dejaría un hueco entre que la lista
        olvida y la base se entera — exactamente lo que hay que evitar."""
        assert DenylistCredenciales().ttl_segundos > 15


class TestOrdenFrenteALaCache:
    def test_la_denegacion_gana_a_una_credencial_valida_en_la_base(
        self, db, api_client, credencial_produccion_headers
    ):
        """🎯 T008 — la credencial es válida y está activa en Pinot, y aun así
        se rechaza. Es el orden que cierra la ventana.

        Cuando #08 añada su caché positiva de bcrypt, debe colocarse DESPUÉS de
        esta comprobación. Este test caería si alguien la pusiera delante.
        """
        # Arrange — nada la ha revocado en la base: sigue activo=true
        assert api_client.get(
            "/api/v1/datos/accidentes", **credencial_produccion_headers
        ).status_code != 401

        # Act
        DenylistCredenciales().denegar(8802)

        # Assert
        assert api_client.get(
            "/api/v1/datos/accidentes", **credencial_produccion_headers
        ).status_code == 401
