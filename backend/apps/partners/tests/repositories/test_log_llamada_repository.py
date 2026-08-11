"""Fact_LogLlamadaAPI — append-only y registro de TODO lo que llega (RNF-APM-005).

La diferencia con `Fact_APIIntegracion` es el punto entero de esta tabla: aqui
se registran tambien las peticiones **rechazadas** —4xx, 5xx y los 429 del
throttle—, porque son el material con el que el partner se autodiagnostica
(RN-APM-009).
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE
from core.repositories.partners.log_llamada_repository import (
    SIN_IP,
    LogLlamadaRepository,
)

pytestmark = [pytest.mark.django_db, pytest.mark.repository]

ID_PARTNER = 810


def _registrar(repo, **over):
    base = {
        "idpartner": ID_PARTNER,
        "idcredencialapi": 1,
        "endpoint": "/api/v1/datos/accidentes",
        "metodohttp": "GET",
        "codigohttp": 200,
        "latenciams": 85.0,
    }
    return repo.registrar(**{**base, **over})


class TestAppendOnly:
    def test_el_repositorio_no_expone_update_ni_delete(self):
        """RNF-APM-005: capacidades que no existen, no reglas que recordar."""
        # Act
        metodos = {m for m in dir(LogLlamadaRepository) if not m.startswith("_")}

        # Assert
        assert "update" not in metodos
        assert "delete" not in metodos
        assert "registrar" in metodos

    def test_cada_peticion_es_una_fila_nueva(self, mock_pinot, mock_kafka):
        # Arrange
        repo = LogLlamadaRepository()

        # Act
        _registrar(repo)
        _registrar(repo)

        # Assert
        assert len(PINOT_STORE["Fact_LogLlamadaAPI"]) == 2


class TestRegistraTodoLoQueLlega:
    def test_registra_las_respuestas_correctas(self, mock_pinot, mock_kafka):
        # Act
        fila = _registrar(LogLlamadaRepository(), codigohttp=200)

        # Assert
        assert fila["codigohttp"] == 200

    def test_registra_los_errores_del_cliente(self, mock_pinot, mock_kafka):
        """RN-APM-009: los 4xx son material de autodiagnóstico del partner."""
        # Act
        fila = _registrar(LogLlamadaRepository(), codigohttp=422)

        # Assert
        assert fila["codigohttp"] == 422

    def test_registra_los_429_del_throttle(self, mock_pinot, mock_kafka):
        """El 429 sí va aquí, aunque NO vaya a `Fact_APIIntegracion`: es la
        distinción entre «te limité el ritmo» y «te cobro esta llamada»."""
        # Act
        _registrar(LogLlamadaRepository(), codigohttp=429)

        # Assert
        assert PINOT_STORE["Fact_LogLlamadaAPI"][0]["codigohttp"] == 429
        assert PINOT_STORE["Fact_APIIntegracion"] == []

    def test_no_publica_ningun_none(self, mock_pinot, mock_kafka):
        # Act
        fila = _registrar(LogLlamadaRepository())

        # Assert
        assert None not in fila.values()


class TestIpOrigen:
    def test_convierte_ipv4_a_entero(self):
        """El esquema declara `iporigen` como INT, no STRING."""
        # Act / Assert
        assert LogLlamadaRepository.ip_a_entero("192.168.1.1") == 3232235777
        assert LogLlamadaRepository.ip_a_entero("0.0.0.0") == 0
        assert LogLlamadaRepository.ip_a_entero("255.255.255.255") == 4294967295

    def test_una_ip_invalida_usa_el_centinela_en_vez_de_reventar(self):
        """Una IP mal formada no puede tumbar el registro de la llamada."""
        # Act / Assert
        assert LogLlamadaRepository.ip_a_entero("no-es-una-ip") == SIN_IP
        assert LogLlamadaRepository.ip_a_entero("999.1.1.1") == SIN_IP
        assert LogLlamadaRepository.ip_a_entero("1.2.3") == SIN_IP
        assert LogLlamadaRepository.ip_a_entero(None) == SIN_IP

    def test_acepta_un_entero_ya_convertido(self, mock_pinot, mock_kafka):
        # Act
        fila = _registrar(LogLlamadaRepository(), iporigen=3232235777)

        # Assert
        assert fila["iporigen"] == 3232235777


class TestConsultas:
    def test_list_by_partner_no_mezcla_partners(self, mock_pinot, mock_kafka):
        # Arrange
        repo = LogLlamadaRepository()
        _registrar(repo, idpartner=ID_PARTNER)
        _registrar(repo, idpartner=999)

        # Act
        filas = repo.list_by_partner(ID_PARTNER)

        # Assert
        assert len(filas) == 1
        assert filas[0]["idpartner"] == ID_PARTNER

    def test_solo_errores_filtra_los_200(self, mock_pinot, mock_kafka):
        # Arrange
        repo = LogLlamadaRepository()
        _registrar(repo, codigohttp=200)
        _registrar(repo, codigohttp=500)

        # Act
        filas = repo.list_by_partner(ID_PARTNER, solo_errores=True)

        # Assert
        assert [f["codigohttp"] for f in filas] == [500]

    def test_contar_por_codigo_agrupa_incluidos_los_429(self, mock_pinot, mock_kafka):
        # Arrange
        repo = LogLlamadaRepository()
        _registrar(repo, codigohttp=200, fechallamada=100)
        _registrar(repo, codigohttp=429, fechallamada=200)
        _registrar(repo, codigohttp=429, fechallamada=300)

        # Act
        conteo = repo.contar_por_codigo(ID_PARTNER, desde_ms=0, hasta_ms=1000)

        # Assert — el 429 es lo primero, y es lo que el partner necesita ver
        assert conteo[0] == {"codigohttp": 429, "total": 2}

    def test_contar_por_codigo_respeta_la_ventana(self, mock_pinot, mock_kafka):
        # Arrange
        repo = LogLlamadaRepository()
        _registrar(repo, codigohttp=200, fechallamada=100)
        _registrar(repo, codigohttp=500, fechallamada=9999)

        # Act
        conteo = repo.contar_por_codigo(ID_PARTNER, desde_ms=0, hasta_ms=1000)

        # Assert
        assert conteo == [{"codigohttp": 200, "total": 1}]
