"""Invariantes transversales del módulo (T059, T060).

Dos propiedades que ningún test de historia protege por sí solo, porque son
del módulo entero y se rompen al **añadir** algo nuevo:

1. Las dos tablas de consumo son append-only (RNF-APM-005).
2. Las dos superficies de autenticación no se mezclan (RF-APM-001).

Son guardianes, no verificaciones de funcionalidad: su valor está en fallar el
día que alguien introduzca un `update` o cruce las puertas de autenticación.
"""

from __future__ import annotations

import pytest

from core.repositories.partners.api_integracion_repository import (
    ApiIntegracionRepository,
)
from core.repositories.partners.log_llamada_repository import LogLlamadaRepository

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL_DATOS = "/api/v1/datos/accidentes"
URL_METRICAS = "/api/v1/partners/880/metricas"


class TestAppendOnly:
    """RNF-APM-005 — el detalle es el respaldo de la tarificación.

    Si una fila de consumo pudiera modificarse, una factura discutida no
    tendría contra qué contrastarse.
    """

    @pytest.mark.parametrize(
        "repositorio", [ApiIntegracionRepository, LogLlamadaRepository]
    )
    def test_ningun_repositorio_de_consumo_expone_escritura_destructiva(
        self, repositorio
    ):
        # Act
        metodos = {m for m in dir(repositorio) if not m.startswith("_")}

        # Assert
        prohibidos = {"update", "delete", "desactivar", "borrar", "modificar"}
        assert not (metodos & prohibidos), (
            f"{repositorio.__name__} expone escritura destructiva sobre una tabla "
            f"append-only: {metodos & prohibidos}"
        )

    @pytest.mark.parametrize(
        "repositorio", [ApiIntegracionRepository, LogLlamadaRepository]
    )
    def test_el_unico_camino_de_escritura_es_registrar(self, repositorio):
        # Act
        escrituras = {
            m
            for m in dir(repositorio)
            if not m.startswith("_") and m.startswith(("registrar", "crear", "guardar"))
        }

        # Assert
        assert escrituras == {"registrar"}


class TestSeparacionDeSuperficies:
    """RF-APM-001 — dos poblaciones, dos puertas, sin cruces.

    Un JWT humano no debe abrir la API de datos, y una credencial de máquina no
    debe abrir las pantallas. Cruzarlas daría a un cliente de API acceso a
    datos de gestión, o a un humano una vía sin throttle ni medición.
    """

    def test_un_jwt_humano_no_entra_en_la_api_de_datos(
        self, api_client, devapis_auth_headers
    ):
        # Act
        response = api_client.get(URL_DATOS, **devapis_auth_headers)

        # Assert
        assert response.status_code == 401

    def test_una_credencial_de_maquina_no_entra_en_las_pantallas(
        self, api_client, credencial_produccion_headers
    ):
        """Las métricas son una pantalla: exigen JWT, no `X-Client-Id`."""
        # Act
        response = api_client.get(URL_METRICAS, **credencial_produccion_headers)

        # Assert
        assert response.status_code in (401, 403)

    def test_la_api_de_datos_declara_su_propio_esquema_de_autenticacion(self):
        """Sin `authenticate_header`, DRF respondería 403 en vez de 401 cuando
        faltan credenciales, y el partner no sabría que debe autenticarse."""
        # Arrange
        from apps.partners.views.datos_views import ConsultarAccidentesView
        from apps.partners.authentication import CredencialAPIAuthentication

        # Act / Assert
        assert ConsultarAccidentesView.authentication_classes == [
            CredencialAPIAuthentication
        ]

    def test_la_api_de_datos_lleva_throttle_y_las_pantallas_no(self):
        """El throttle protege la plataforma del consumo de máquina; aplicarlo
        a las pantallas limitaría a un operador por mirar sus métricas."""
        # Arrange
        from apps.partners.views.datos_views import ConsultarAccidentesView
        from apps.partners.views.metricas_views import MetricasPartnerView
        from apps.partners.throttling import PartnerRateThrottle

        # Act / Assert
        assert PartnerRateThrottle in ConsultarAccidentesView.throttle_classes
        assert not getattr(MetricasPartnerView, "throttle_classes", [])
