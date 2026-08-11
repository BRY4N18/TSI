"""Cascada directa de la suspension (T025, CA-PAC-008, escenario H).

Dos cosas que deben pasar a la vez, y que son distintas entre si:

1. **Todas** las credenciales quedan inactivas, de pruebas y de produccion.
2. Se escribe **una fila de bitacora por cada una** — y esa lista es lo que
   permitira reactivar selectivamente despues.

Lo segundo es lo que suele olvidarse, porque el sistema "funciona" sin ello:
hasta que alguien reactiva y resucita una credencial comprometida.
"""

from __future__ import annotations

import pytest

from apps.partners.services.suspender_partner_service import (
    SuspenderPartnerError,
    SuspenderPartnerService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

MOTIVO = "Mora de 16 días en facturas de excedente de API"


def _cascada() -> list[dict]:
    return [
        e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
        if e["tipo_cambio"] == "desactivacion_por_cascada"
    ]


class TestCascadaDirecta:
    def test_desactiva_todas_las_credenciales_de_ambos_entornos(
        self, partner_con_credenciales
    ):
        # Act
        SuspenderPartnerService().suspender(
            idpartner=partner_con_credenciales["idpartner"],
            motivo=MOTIVO,
            automatica=True,
        )

        # Assert — ninguna activa, ni Sandbox ni Producción (RN-PAC-010)
        activas = [c for c in PINOT_STORE["Dim_CredencialAPI"] if c.get("activo")]
        assert activas == []

    def test_escribe_una_fila_de_cascada_por_credencial_ACTIVA(
        self, partner_con_credenciales
    ):
        """Dos filas, no tres: la revocada ya estaba inactiva.

        Esa ausencia no es una optimización — es lo que hace imposible que la
        reactivación la encuentre (§ 15 D1).
        """
        # Act
        SuspenderPartnerService().suspender(
            idpartner=partner_con_credenciales["idpartner"],
            motivo=MOTIVO,
            automatica=True,
        )

        # Assert
        ids = sorted(e["idcredencial"] for e in _cascada())
        assert ids == [101, 102]
        assert 103 not in ids

    def test_cada_fila_lleva_su_idcredencial_no_el_centinela(
        self, partner_con_credenciales
    ):
        """Con `-1` la lista sería inservible para restituir."""
        # Act
        SuspenderPartnerService().suspender(
            idpartner=partner_con_credenciales["idpartner"],
            motivo=MOTIVO,
            automatica=True,
        )

        # Assert
        assert all(e["idcredencial"] != -1 for e in _cascada())

    def test_deja_el_snapshot_de_suspension_en_dim_partner(
        self, partner_con_credenciales
    ):
        # Act
        resultado = SuspenderPartnerService().suspender(
            idpartner=partner_con_credenciales["idpartner"],
            motivo=MOTIVO,
            automatica=True,
        )

        # Assert
        partner = next(
            p for p in PINOT_STORE["Dim_Partner"]
            if p["idpartner"] == partner_con_credenciales["idpartner"]
        )
        assert partner["activo"] is False
        assert partner["motivo_suspension"] == MOTIVO
        assert partner["fecha_suspension"] != ""
        assert resultado["credenciales_desactivadas"] == 2

    def test_el_evento_de_suspension_automatica_lo_firma_el_sistema(
        self, partner_con_credenciales
    ):
        # Act
        SuspenderPartnerService().suspender(
            idpartner=partner_con_credenciales["idpartner"],
            motivo=MOTIVO,
            automatica=True,
        )

        # Assert
        evento = next(
            e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == "suspension_automatica"
        )
        assert evento["ejecutado_por"] == "Sistema"
        assert evento["idcredencial"] == -1
        assert evento["estado_nuevo"] == "Suspendido"

    def test_la_manual_se_distingue_de_la_automatica(self, partner_con_credenciales):
        """Son `tipo_cambio` distintos: la auditoría debe poder separarlas."""
        # Act
        SuspenderPartnerService().suspender(
            idpartner=partner_con_credenciales["idpartner"],
            motivo="contrato vencido",
            automatica=False,
        )

        # Assert
        tipos = {e["tipo_cambio"] for e in PINOT_STORE["Fact_HistorialAccesoPartner"]}
        assert "suspension_manual" in tipos
        assert "suspension_automatica" not in tipos


class TestRechazos:
    def test_suspender_sin_motivo_falla(self, partner_con_credenciales):
        """CA-PAC-011 — la bitácora sin motivo no explica nada."""
        with pytest.raises(SuspenderPartnerError) as exc:
            SuspenderPartnerService().suspender(
                idpartner=partner_con_credenciales["idpartner"],
                motivo="   ",
                automatica=False,
            )
        assert exc.value.code == "validation_error"

    def test_suspender_uno_ya_suspendido_falla_sin_escribir(self, partner_suspendido):
        # Arrange
        antes = len(PINOT_STORE["Fact_HistorialAccesoPartner"])

        # Act / Assert
        with pytest.raises(SuspenderPartnerError) as exc:
            SuspenderPartnerService().suspender(
                idpartner=partner_suspendido["idpartner"],
                motivo=MOTIVO,
                automatica=True,
            )
        assert exc.value.code == "partner_ya_suspendido"
        assert len(PINOT_STORE["Fact_HistorialAccesoPartner"]) == antes
