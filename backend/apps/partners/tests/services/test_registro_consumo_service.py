"""Registro de consumo — dos tablas con criterios distintos (RF-APM-004).

Incluye la **regla contable del 429** (T022) y la garantía de que un fallo de
registro **no altera la respuesta al partner** (T023): están aquí y no en
archivos aparte porque son propiedades del mismo servicio y separarlas obligaría
a duplicar todo el montaje.
"""

from __future__ import annotations

import pytest

from apps.partners.services.registro_consumo_service import RegistroConsumoService
from conftest import PINOT_STORE
from core.repositories.partners.estado_integracion_repository import (
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
)

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 820
ID_CLIENTE = 820


def _registrar(servicio, **over):
    base = {
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "idcredencial": 5,
        "entorno": "Producción",
        "endpoint": "/api/v1/datos/accidentes",
        "metodohttp": "GET",
        "codigohttp": 200,
        "latencia_ms": 95.0,
    }
    return servicio.registrar_llamada(**{**base, **over})


class TestEscribeEnLasDosTablas:
    def test_una_llamada_atendida_deja_una_fila_en_cada_tabla(
        self, mock_pinot, mock_kafka
    ):
        # Act
        escrito = _registrar(RegistroConsumoService())

        # Assert
        assert escrito == {"log": True, "consumo": True}
        assert len(PINOT_STORE["Fact_LogLlamadaAPI"]) == 1
        assert len(PINOT_STORE["Fact_APIIntegracion"]) == 1

    def test_errores_se_deriva_del_codigo_http(self, mock_pinot, mock_kafka):
        # Act
        _registrar(RegistroConsumoService(), codigohttp=500)

        # Assert
        assert PINOT_STORE["Fact_APIIntegracion"][0]["errores"] == 1

    def test_un_4xx_atendido_si_cuenta_como_consumo(self, mock_pinot, mock_kafka):
        """Un 404 se atendió: se procesó la petición y se le respondió.

        Es la diferencia con un 401/403/429, que se rechazan en la puerta sin
        hacer trabajo alguno en nombre del partner.
        """
        # Act
        escrito = _registrar(RegistroConsumoService(), codigohttp=404)

        # Assert
        assert escrito["consumo"] is True
        assert PINOT_STORE["Fact_APIIntegracion"][0]["errores"] == 1

    def test_un_500_tambien_cuenta_como_consumo(self, mock_pinot, mock_kafka):
        """Un fallo nuestro no deja de ser una petición procesada."""
        # Act
        escrito = _registrar(RegistroConsumoService(), codigohttp=500)

        # Assert
        assert escrito["consumo"] is True


class TestEstadoCongelado:
    def test_produccion_congela_el_estado_dos(self, mock_pinot, mock_kafka):
        # Act
        _registrar(RegistroConsumoService(), entorno="Producción")

        # Assert
        assert (
            PINOT_STORE["Fact_APIIntegracion"][0]["idestadointegracion"]
            == ESTADO_PRODUCCION_ACTIVA
        )

    def test_sandbox_congela_el_estado_uno(self, mock_pinot, mock_kafka):
        # Act
        _registrar(RegistroConsumoService(), entorno="Sandbox")

        # Assert
        assert (
            PINOT_STORE["Fact_APIIntegracion"][0]["idestadointegracion"]
            == ESTADO_PRUEBAS_ACTIVO
        )

    def test_nunca_congela_el_estado_suspendido(self, mock_pinot, mock_kafka):
        """El 3 es inalcanzable: si el partner estuviera suspendido, la petición
        no habría llegado a registrarse."""
        # Act
        _registrar(RegistroConsumoService(), entorno="Sandbox")
        _registrar(RegistroConsumoService(), entorno="Producción")

        # Assert
        estados = {f["idestadointegracion"] for f in PINOT_STORE["Fact_APIIntegracion"]}
        assert 3 not in estados


class TestRechazosDeAccesoNoSeFacturan:
    """T019 — un 401 o un 403 se rechazan en la puerta: no hubo servicio.

    Se detectó implementando: el middleware los registraba como consumo porque
    la autenticación había tenido éxito y solo falló el permiso. Cobrar por una
    llamada denegada sería cobrar por un servicio que no se prestó.
    """

    @pytest.mark.parametrize("codigo", [401, 403])
    def test_un_rechazo_de_acceso_no_deja_consumo(
        self, codigo, mock_pinot, mock_kafka
    ):
        # Act
        escrito = _registrar(RegistroConsumoService(), codigohttp=codigo)

        # Assert
        assert escrito == {"log": True, "consumo": False}
        assert PINOT_STORE["Fact_APIIntegracion"] == []

    @pytest.mark.parametrize("codigo", [401, 403])
    def test_el_rechazo_si_queda_en_el_log(self, codigo, mock_pinot, mock_kafka):
        """El partner necesita verlo para saber por qué le deniegan."""
        # Act
        _registrar(RegistroConsumoService(), codigohttp=codigo)

        # Assert
        assert PINOT_STORE["Fact_LogLlamadaAPI"][0]["codigohttp"] == codigo


class TestReglaContableDel429:
    """§ 15 D2 — la asimetría que distingue «te limité» de «te cobro»."""

    def test_un_429_deja_log_pero_no_consumo(self, mock_pinot, mock_kafka):
        # Act
        escrito = _registrar(RegistroConsumoService(), codigohttp=429)

        # Assert
        assert escrito == {"log": True, "consumo": False}
        assert len(PINOT_STORE["Fact_LogLlamadaAPI"]) == 1
        assert PINOT_STORE["Fact_APIIntegracion"] == []

    def test_el_429_queda_visible_para_el_partner(self, mock_pinot, mock_kafka):
        """Tiene que poder verlo para ajustar su cliente (RN-APM-009)."""
        # Act
        _registrar(RegistroConsumoService(), codigohttp=429)

        # Assert
        assert PINOT_STORE["Fact_LogLlamadaAPI"][0]["codigohttp"] == 429

    def test_muchos_429_no_generan_ni_una_llamada_facturable(
        self, mock_pinot, mock_kafka
    ):
        """Si el throttle contara como consumo, limitar a un partner le saldría
        caro justo cuando el sistema lo está protegiendo."""
        # Arrange
        servicio = RegistroConsumoService()

        # Act
        for _ in range(10):
            _registrar(servicio, codigohttp=429)

        # Assert
        assert PINOT_STORE["Fact_APIIntegracion"] == []
        assert len(PINOT_STORE["Fact_LogLlamadaAPI"]) == 10


class _RepoQueFalla:
    def registrar(self, **_kwargs):
        raise RuntimeError("Kafka caído")


class TestElRegistroNoRompeLaRespuesta:
    """RN-APM-005 — el partner ya tiene sus datos; perder la métrica es un
    problema de reconciliación, no motivo para convertir un 200 en un 500."""

    def test_un_fallo_al_publicar_el_consumo_no_propaga(self, mock_pinot, mock_kafka):
        # Arrange
        servicio = RegistroConsumoService(api_integracion=_RepoQueFalla())

        # Act — no lanza
        escrito = _registrar(servicio)

        # Assert
        assert escrito["consumo"] is False
        assert escrito["log"] is True

    def test_un_fallo_al_publicar_el_log_tampoco_propaga(self, mock_pinot, mock_kafka):
        # Arrange
        servicio = RegistroConsumoService(logs=_RepoQueFalla())

        # Act — no lanza
        escrito = _registrar(servicio)

        # Assert
        assert escrito["log"] is False
        assert escrito["consumo"] is True

    def test_si_fallan_las_dos_tampoco_propaga(self, mock_pinot, mock_kafka):
        # Arrange
        servicio = RegistroConsumoService(
            api_integracion=_RepoQueFalla(), logs=_RepoQueFalla()
        )

        # Act / Assert — no lanza
        assert _registrar(servicio) == {"log": False, "consumo": False}

    def test_el_fallo_queda_registrado_para_reconciliacion(
        self, mock_pinot, mock_kafka, caplog
    ):
        """Silencioso no: sin rastro, nadie sabría que faltan métricas."""
        # Arrange
        import logging

        caplog.set_level(logging.ERROR, logger="tsi.partners.consumo")
        servicio = RegistroConsumoService(api_integracion=_RepoQueFalla())

        # Act
        _registrar(servicio)

        # Assert
        assert "consumo_metrica_fallida" in caplog.text
