"""🎯 El test mas importante del departamento (T026, CA-PAC-009, escenario I).

Un partner tiene A y B activas, y C que **el mismo revoco por seguridad**. Se le
suspende (las tres quedan inactivas) y luego un Administrador lo reactiva.

**Si C vuelve activa, se ha resucitado una credencial comprometida.** No es un
fallo cosmetico: esa credencial esta en manos de alguien mas, y la API entrega
geolocalizacion e identidad de personas involucradas en accidentes.
"""

from __future__ import annotations

import pytest

from apps.partners.services.reactivar_partner_service import (
    ReactivarPartnerError,
    ReactivarPartnerService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]


def _credencial(idcredencial: int) -> dict:
    return next(
        c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idcredencial"] == idcredencial
    )


class TestReactivacionSelectiva:
    def test_restituye_las_de_la_cascada_y_no_la_revocada(self, partner_suspendido):
        # Arrange — 101 y 102 desactivadas por cascada; 103 revocada antes
        idpartner = partner_suspendido["idpartner"]

        # Act
        resultado = ReactivarPartnerService().reactivar(idpartner=idpartner)

        # Assert
        assert _credencial(101)["activo"] is True
        assert _credencial(102)["activo"] is True
        assert _credencial(103)["activo"] is False, (
            "Se resucitó una credencial que el partner había revocado por "
            "seguridad: fallo grave de seguridad (RN-PAC-011)"
        )
        assert resultado["credenciales_restituidas"] == 2
        assert resultado["credenciales_no_restituidas"] == 1

    def test_la_revocada_no_esta_en_la_lista_de_la_cascada(self, partner_suspendido):
        """La garantia es ESTRUCTURAL: no es que se filtre, es que no está.

        Si algún día alguien añadiera una fila de cascada para una credencial ya
        inactiva, este test caería antes que el de arriba y diría por qué.
        """
        from core.repositories.partners.historial_acceso_repository import (
            HistorialAccesoRepository,
        )

        # Act
        ids = HistorialAccesoRepository().credenciales_de_la_ultima_cascada(
            partner_suspendido["idpartner"]
        )

        # Assert
        assert sorted(ids) == [101, 102]
        assert 103 not in ids

    def test_el_partner_vuelve_a_activo_con_el_snapshot_limpio(self, partner_suspendido):
        # Act
        ReactivarPartnerService().reactivar(idpartner=partner_suspendido["idpartner"])

        # Assert — centinelas vacios, nunca NULL (RN-PAC-014)
        partner = next(
            p for p in PINOT_STORE["Dim_Partner"]
            if p["idpartner"] == partner_suspendido["idpartner"]
        )
        assert partner["activo"] is True
        assert partner["fecha_suspension"] == ""
        assert partner["motivo_suspension"] == ""

    def test_registra_el_evento_de_reactivacion(self, partner_suspendido):
        # Act
        ReactivarPartnerService().reactivar(
            idpartner=partner_suspendido["idpartner"], motivo="deuda regularizada"
        )

        # Assert
        eventos = [
            e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == "reactivacion"
        ]
        assert len(eventos) == 1
        assert eventos[0]["ejecutado_por"] == "Administrador"
        assert eventos[0]["estado_anterior"] == "Suspendido"
        assert eventos[0]["estado_nuevo"] == "Activo"


class TestReactivacionRedundante:
    def test_reactivar_un_partner_no_suspendido_falla_sin_escribir(
        self, partner_con_credenciales
    ):
        """CA-PAC-011 — 409 y sin entrada en la bitácora (escenario K)."""
        # Arrange
        antes = len(PINOT_STORE["Fact_HistorialAccesoPartner"])

        # Act / Assert
        with pytest.raises(ReactivarPartnerError) as exc:
            ReactivarPartnerService().reactivar(
                idpartner=partner_con_credenciales["idpartner"]
            )

        assert exc.value.code == "partner_no_suspendido"
        assert len(PINOT_STORE["Fact_HistorialAccesoPartner"]) == antes
