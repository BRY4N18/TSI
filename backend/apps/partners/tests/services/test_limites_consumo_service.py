"""Límites de consumo y sus avisos (CU-O53, RF-APM-010).

Reúne T040, T041 y T042. La propiedad que sostiene el archivo es **negativa**:
este servicio compara y avisa, pero **nunca interrumpe el servicio**. El SRS
dice que lo documenta «para que nadie la corrija asumiendo que debería
bloquear», así que aquí queda como test.
"""

from __future__ import annotations

import pytest

from apps.partners.jobs.alertas_cuota_job import AlertasCuotaJob
from apps.partners.services.limites_consumo_service import (
    AVISO_CUOTA_80,
    AVISO_CUOTA_100,
    SIN_CUPO,
    LimitesConsumoService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 860
ID_CLIENTE = 860
DESDE, HASTA = 1000, 999_999


def _partner(cupo=100, idpartner=ID_PARTNER):
    PINOT_STORE["Dim_Partner"].append({
        "idpartner": idpartner,
        "idcliente": ID_CLIENTE,
        "nombrepartner": "Demo Cuota",
        "contacto_tecnico_nombre": "Ana",
        "contacto_tecnico_gmail": "ana@demo.com",
        "planapi": "Profesional",
        "limitellamadasmes": cupo,
        "limitellamadasminuto": 120,
        "sandbox_activado": 1,
        "sandbox_expiracion": 253402300799000,
        "fecha_suspension": "",
        "motivo_suspension": "",
        "activo": True,
        "fecha_actualizacion": 1,
    })


def _consumo(cuantas, idpartner=ID_PARTNER, entorno="Producción"):
    for i in range(cuantas):
        PINOT_STORE["Fact_APIIntegracion"].append({
            "idapiintegracion": len(PINOT_STORE["Fact_APIIntegracion"]) + 1,
            "idpartner": idpartner,
            "idcliente": ID_CLIENTE,
            "idservicio": 1,
            "idestadointegracion": 2,
            "entorno": entorno,
            "llamadas": 1,
            "errores": 0,
            "latencia": 90.0,
            "activo": True,
            "fechahora": DESDE + 1 + i,
            "fecha_actualizacion": DESDE + 1 + i,
        })


def _evaluar(idpartner=ID_PARTNER):
    return LimitesConsumoService().evaluar(idpartner, desde_ms=DESDE, hasta_ms=HASTA)


class TestNuncaInterrumpeElServicio:
    """RN-APM-002 — superar el cupo genera excedente facturable, no un corte."""

    def test_al_superar_el_cupo_el_servicio_sigue(self, mock_pinot, mock_kafka):
        # Arrange — 150 llamadas contra un cupo de 100
        _partner(cupo=100)
        _consumo(150)

        # Act
        estado = _evaluar()

        # Assert
        assert estado["servicio_interrumpido"] is False
        assert estado["excedentes"] == 50

    def test_el_servicio_no_expone_ninguna_forma_de_bloquear(self):
        """Guardián: si alguien añade un método que sugiera restricción, se ve
        aquí antes que en producción."""
        # Act
        metodos = {m for m in dir(LimitesConsumoService) if not m.startswith("_")}

        # Assert
        assert metodos == {"evaluar", "debe_avisar", "registrar_aviso"}
        assert not any(
            p in m for m in metodos for p in ("bloquear", "restringir", "cortar", "denegar")
        )


class TestUmbrales:
    def test_por_debajo_del_80_no_hay_aviso(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _consumo(79)

        # Act / Assert
        assert _evaluar()["umbral_alcanzado"] is None

    def test_al_80_avisa_de_aproximacion(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _consumo(80)

        # Act / Assert
        assert _evaluar()["umbral_alcanzado"] == AVISO_CUOTA_80

    def test_al_100_avisa_de_cupo_alcanzado(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _consumo(100)

        # Act / Assert
        assert _evaluar()["umbral_alcanzado"] == AVISO_CUOTA_100

    def test_por_encima_del_100_sigue_siendo_el_aviso_de_alcanzado(
        self, mock_pinot, mock_kafka
    ):
        """No hay un tercer umbral: pasado el cupo, el mensaje es el mismo."""
        # Arrange
        _partner(cupo=100)
        _consumo(300)

        # Act / Assert
        assert _evaluar()["umbral_alcanzado"] == AVISO_CUOTA_100

    def test_solo_cuenta_produccion(self, mock_pinot, mock_kafka):
        """Contar sandbox dispararía avisos por consumo que no se factura."""
        # Arrange
        _partner(cupo=100)
        _consumo(500, entorno="Sandbox")

        # Act / Assert
        assert _evaluar()["umbral_alcanzado"] is None


class TestCupoSinAsignar:
    """El centinela `-1` no es un límite de -1 llamadas."""

    def test_un_partner_sin_cupo_no_dispara_alertas(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=SIN_CUPO)
        _consumo(1000)

        # Act
        estado = _evaluar()

        # Assert — tratarlo como límite avisaría «superaste tu cupo» en la
        # primera llamada
        assert estado["aplica"] is False
        assert estado["motivo"] == "sin_cupo_asignado"

    def test_un_partner_inexistente_no_revienta(self, mock_pinot, mock_kafka):
        # Act
        estado = _evaluar(idpartner=404404)

        # Assert
        assert estado == {"aplica": False, "motivo": "partner_inexistente"}


class _Notificaciones:
    def __init__(self):
        self.enviados = []

    def notificar_cuota(self, *, partner, asunto, cuerpo):
        self.enviados.append({"asunto": asunto, "cuerpo": cuerpo})
        return 1


class TestNoDuplicacionDeAvisos:
    """RN-APM-010 — un aviso por umbral y período.

    Sin esto, el job avisaría en cada ejecución desde que se cruza el umbral y
    el partner acabaría ignorando los correos justo antes de que le importen.
    """

    def _job(self):
        notif = _Notificaciones()
        return AlertasCuotaJob(notificaciones=notif), notif

    def test_el_primer_pase_avisa(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _consumo(85)
        job, notif = self._job()

        # Act
        resumen = job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Assert
        assert resumen["avisados"] == 1
        assert len(notif.enviados) == 1

    def test_el_segundo_pase_no_repite_el_mismo_aviso(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(cupo=100)
        _consumo(85)
        job, notif = self._job()
        job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Act — el job vuelve a correr sin que nada haya cambiado
        resumen = job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Assert
        assert resumen["avisados"] == 0
        assert len(notif.enviados) == 1

    def test_cruzar_el_100_si_emite_un_aviso_nuevo(self, mock_pinot, mock_kafka):
        """Son dos umbrales distintos: haber avisado del 80 no consume el 100."""
        # Arrange
        _partner(cupo=100)
        _consumo(85)
        job, notif = self._job()
        job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Act — el consumo sigue subiendo
        _consumo(20)
        resumen = job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Assert
        assert resumen["avisados"] == 1
        assert len(notif.enviados) == 2

    def test_el_aviso_no_menciona_interrupcion_del_servicio(
        self, mock_pinot, mock_kafka
    ):
        """Un aviso que sugiera corte haría que el partner desconectara su
        integración por su cuenta."""
        # Arrange
        _partner(cupo=100)
        _consumo(100)
        job, notif = self._job()

        # Act
        job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Assert
        cuerpo = notif.enviados[0]["cuerpo"].lower()
        assert "no se interrumpe" in cuerpo or "sigue funcionando" in cuerpo
        assert "suspend" not in cuerpo
        assert "bloque" not in cuerpo


class TestJobFailOpen:
    def test_un_partner_que_falla_no_impide_avisar_a_los_demas(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _partner(cupo=100, idpartner=861)
        _consumo(90, idpartner=861)
        _partner(cupo=100, idpartner=862)
        _consumo(90, idpartner=862)

        class _LimitesQueFallaCon861(LimitesConsumoService):
            def evaluar(self, idpartner, **kwargs):
                if idpartner == 861:
                    raise RuntimeError("Pinot caído")
                return super().evaluar(idpartner, **kwargs)

        job = AlertasCuotaJob(
            limites=_LimitesQueFallaCon861(), notificaciones=_Notificaciones()
        )

        # Act
        resumen = job.ejecutar(desde_ms=DESDE, hasta_ms=HASTA)

        # Assert
        assert resumen["fallidos"] == 1
        assert resumen["avisados"] == 1
