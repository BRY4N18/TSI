"""Throttle por minuto de la API de datos (§ 15 D2).

Lo que se prueba aquí es una distinción, no un número: este throttle es
**protección de plataforma**, no la aplicación de la cuota comercial. El cupo
mensual no bloquea nunca (RN-APM-002); esto limita el *ritmo* instantáneo.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.core.cache import cache

from apps.partners.authentication import PartnerAPIUser
from apps.partners.throttling import SIN_CUPO, PartnerRateThrottle

pytestmark = [pytest.mark.unit]


def _usuario(limite_minuto=60, idpartner=12):
    partner = {
        "idpartner": idpartner,
        "idcliente": 100,
        "activo": True,
        "limitellamadasminuto": limite_minuto,
    }
    credencial = {"idcredencial": 88, "entorno": "Producción"}
    return PartnerAPIUser(partner, credencial)


def _peticion(usuario):
    return SimpleNamespace(user=usuario, META={})


@pytest.fixture(autouse=True)
def _limpiar_cache():
    cache.clear()
    yield
    cache.clear()


class TestLimitePorPartner:
    def test_usa_el_limite_del_partner_y_no_el_del_scope(self):
        """El rate del scope existe solo porque DRF exige uno declarado."""
        # Arrange
        throttle = PartnerRateThrottle()

        # Act
        throttle.get_cache_key(_peticion(_usuario(limite_minuto=25)), None)

        # Assert
        assert throttle.num_requests == 25
        assert throttle.duration == 60

    def test_dos_partners_no_comparten_contador(self):
        """Si compartieran clave, el consumo de uno limitaría al otro."""
        # Arrange
        throttle = PartnerRateThrottle()

        # Act
        clave_a = throttle.get_cache_key(_peticion(_usuario(idpartner=1)), None)
        clave_b = throttle.get_cache_key(_peticion(_usuario(idpartner=2)), None)

        # Assert
        assert clave_a != clave_b

    def test_permite_hasta_el_limite_y_rechaza_la_siguiente(self):
        # Arrange
        throttle = PartnerRateThrottle()
        peticion = _peticion(_usuario(limite_minuto=3))

        # Act
        permitidas = [throttle.allow_request(peticion, None) for _ in range(3)]
        siguiente = throttle.allow_request(peticion, None)

        # Assert
        assert permitidas == [True, True, True]
        assert siguiente is False


class TestCentinelaSinCupo:
    def test_cupo_menos_uno_no_throttlea(self):
        """`-1` es el centinela de «sin cupo asignado», no un límite de -1
        llamadas. Bloquear por un centinela sería un defecto silencioso."""
        # Arrange
        throttle = PartnerRateThrottle()

        # Act
        clave = throttle.get_cache_key(_peticion(_usuario(limite_minuto=SIN_CUPO)), None)

        # Assert — sin clave, DRF no aplica el throttle
        assert clave is None

    def test_cupo_cero_si_es_un_limite_real(self):
        """0 no es el centinela: es un partner al que se le limitó a cero."""
        # Arrange
        throttle = PartnerRateThrottle()

        # Act
        clave = throttle.get_cache_key(_peticion(_usuario(limite_minuto=0)), None)

        # Assert
        assert clave is not None
        assert throttle.num_requests == 0


class TestNoAplicaFueraDeLaApiDeDatos:
    def test_un_usuario_humano_no_se_throttlea_por_aqui(self):
        # Arrange
        throttle = PartnerRateThrottle()
        humano = SimpleNamespace(is_authenticated=True, roles=["Administrador"])

        # Act / Assert
        assert throttle.get_cache_key(_peticion(humano), None) is None

    def test_una_peticion_anonima_tampoco(self):
        # Arrange
        throttle = PartnerRateThrottle()

        # Act / Assert
        assert throttle.get_cache_key(SimpleNamespace(user=None, META={}), None) is None


class TestRetryAfter:
    def test_devuelve_espera_para_que_drf_emita_retry_after(self):
        # Arrange
        throttle = PartnerRateThrottle()
        peticion = _peticion(_usuario(limite_minuto=1))
        throttle.allow_request(peticion, None)
        throttle.allow_request(peticion, None)

        # Act
        espera = throttle.wait()

        # Assert
        assert espera is not None
        assert espera >= 1

    def test_nunca_devuelve_cero(self):
        """Un `Retry-After: 0` invita a reintentar de inmediato y volver a
        chocar contra el mismo límite."""
        # Arrange
        throttle = PartnerRateThrottle()
        throttle.num_requests = 1000
        throttle.duration = 60
        throttle.history = []
        throttle.now = 0

        # Act
        espera = throttle.wait()

        # Assert
        assert espera is None or espera >= 1
