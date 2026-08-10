"""RF-PON-006 — expira la credencial, no el partner (CU-O49)."""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import (
    CAMBIO_EXPIRACION_SANDBOX,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    NUNCA_EXPIRA,
)
from apps.partners.jobs.expiracion_credenciales_job import (
    run_expiracion_credenciales_job,
)
from apps.partners.services.expiracion_credencial_service import (
    AVISO_PREVIO,
    ExpiracionCredencialService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 907
AHORA = 1_800_000_000_000
UN_DIA = 86_400_000


def _partner() -> None:
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": 907,
            "nombrepartner": "Demo",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "Profesional",
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 1,
            "sandbox_expiracion": 1,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )


def _credencial(idcredencial: int, expira: int, entorno: str = ENTORNO_SANDBOX) -> dict:
    fila = {
        "idcredencial": idcredencial,
        "idpartner": ID_PARTNER,
        "idcliente": 907,
        "client_secret_hash": "$2b$12$x",
        "nombre_credencial": f"cred-{idcredencial}",
        "entorno": entorno,
        "activo": True,
        "fecha_creacion": 1,
        "fecha_expiracion": expira,
        "fecha_actualizacion": 1,
    }
    PINOT_STORE["Dim_CredencialAPI"].append(fila)
    return fila


class TestVigenciaDerivada:
    def test_esta_vencida_when_fecha_pasada_returns_true(self, mock_pinot, mock_kafka):
        """La vigencia se DERIVA: no hace falta que el job haya corrido."""
        # Arrange
        cred = _credencial(1, expira=AHORA - UN_DIA)

        # Act / Assert
        assert ExpiracionCredencialService().esta_vencida(cred, AHORA) is True

    def test_esta_vencida_when_produccion_returns_false(self, mock_pinot, mock_kafka):
        """RF-PON-008 — el centinela del ano 9999 nunca es alcanzado.

        Con 0 o Long.MIN_VALUE, TODA credencial de produccion figuraria vencida.
        """
        # Arrange
        cred = _credencial(2, expira=NUNCA_EXPIRA, entorno=ENTORNO_PRODUCCION)

        # Act / Assert
        assert ExpiracionCredencialService().esta_vencida(cred, AHORA) is False

    def test_esta_utilizable_when_activa_y_no_vencida(self, mock_pinot, mock_kafka):
        # Arrange
        cred = _credencial(3, expira=AHORA + UN_DIA)

        # Act / Assert
        assert ExpiracionCredencialService().esta_utilizable(cred, AHORA) is True

    def test_esta_utilizable_when_vencida_pero_aun_marcada_activa(self, mock_pinot, mock_kafka):
        """Fail-safe: si el job no ha corrido, la credencial YA no sirve."""
        # Arrange — activo=true pero con la fecha pasada
        cred = _credencial(4, expira=AHORA - 1)

        # Act / Assert
        assert cred["activo"] is True
        assert ExpiracionCredencialService().esta_utilizable(cred, AHORA) is False


class TestProcesarVencidas:
    def test_procesar_when_vencida_desactiva_solo_la_credencial(self, mock_pinot, mock_kafka):
        """RN-PON-006 — expira la CREDENCIAL, no el partner."""
        # Arrange
        _partner()
        _credencial(10, expira=AHORA - UN_DIA)

        # Act
        resultado = ExpiracionCredencialService().procesar_vencidas(AHORA)

        # Assert
        assert resultado["total"] == 1
        cred = next(c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idcredencial"] == 10)
        assert cred["activo"] is False
        # El partner conserva su estado y su plan
        partner = next(p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == ID_PARTNER)
        assert partner["activo"] is True
        assert partner["planapi"] == "Profesional"

    def test_procesar_when_vencida_registra_expiracion(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        _credencial(11, expira=AHORA - UN_DIA)

        # Act
        ExpiracionCredencialService().procesar_vencidas(AHORA)

        # Assert
        evento = PINOT_STORE["Fact_HistorialAccesoPartner"][-1]
        assert evento["tipo_cambio"] == CAMBIO_EXPIRACION_SANDBOX
        assert evento["idcredencial"] == 11
        assert evento["ejecutado_por"] == "Sistema"

    def test_procesar_when_produccion_no_la_toca(self, mock_pinot, mock_kafka):
        """El job de expiracion NUNCA debe alcanzar a produccion."""
        # Arrange
        _partner()
        _credencial(12, expira=NUNCA_EXPIRA, entorno=ENTORNO_PRODUCCION)

        # Act
        resultado = ExpiracionCredencialService().procesar_vencidas(AHORA)

        # Assert
        assert resultado["total"] == 0
        cred = next(c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idcredencial"] == 12)
        assert cred["activo"] is True

    def test_procesar_when_vigente_no_la_toca(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        _credencial(13, expira=AHORA + UN_DIA)

        # Act
        resultado = ExpiracionCredencialService().procesar_vencidas(AHORA)

        # Assert
        assert resultado["total"] == 0


class TestAvisoPrevio:
    def test_avisar_when_proxima_a_vencer_avisa_una_vez(self, mock_pinot, mock_kafka):
        # Arrange — vence en 3 dias, dentro del umbral de 7
        _partner()
        _credencial(20, expira=AHORA + 3 * UN_DIA)
        servicio = ExpiracionCredencialService()

        # Act — dos pasadas del job
        primera = servicio.avisar_proximas_a_vencer(AHORA)
        segunda = servicio.avisar_proximas_a_vencer(AHORA)

        # Assert — se avisa una sola vez (RF-PON-006)
        assert primera["total"] == 1
        assert segunda["total"] == 0
        avisos = [
            e
            for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == AVISO_PREVIO
        ]
        assert len(avisos) == 1

    def test_avisar_no_cambia_el_estado_del_partner(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        _credencial(21, expira=AHORA + 2 * UN_DIA)

        # Act
        ExpiracionCredencialService().avisar_proximas_a_vencer(AHORA)

        # Assert
        evento = PINOT_STORE["Fact_HistorialAccesoPartner"][-1]
        assert evento["estado_anterior"] == evento["estado_nuevo"]

    def test_avisar_when_lejos_de_vencer_no_avisa(self, mock_pinot, mock_kafka):
        # Arrange — vence en 20 dias
        _partner()
        _credencial(22, expira=AHORA + 20 * UN_DIA)

        # Act
        resultado = ExpiracionCredencialService().avisar_proximas_a_vencer(AHORA)

        # Assert
        assert resultado["total"] == 0

    def test_avisar_when_produccion_no_avisa(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        _credencial(23, expira=NUNCA_EXPIRA, entorno=ENTORNO_PRODUCCION)

        # Act
        resultado = ExpiracionCredencialService().avisar_proximas_a_vencer(AHORA)

        # Assert
        assert resultado["total"] == 0


class TestJob:
    def test_job_ejecuta_aviso_y_expiracion(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        _credencial(30, expira=AHORA - UN_DIA)  # ya vencida

        # Act
        resultado = run_expiracion_credenciales_job()

        # Assert — el job corre sin errores y devuelve el resumen
        assert "avisadas" in resultado
        assert "expiradas" in resultado
