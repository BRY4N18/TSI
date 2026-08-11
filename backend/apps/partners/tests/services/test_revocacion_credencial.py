"""Revocacion con reemplazo (T016, T017; CA-PAC-001/002/003/004/005).

Cubre los escenarios A, C, D y E: el reemplazo lleva el MISMO nombre, la
unicidad no da colision falsa, las demas credenciales no se tocan, y los dos
rechazos (ajena -> propiedad, ya inactiva -> conflicto) no escriben nada.
"""

from __future__ import annotations

import pytest

from apps.partners.services.revocar_credencial_service import (
    RevocarCredencialError,
    RevocarCredencialService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

MOTIVO = "credencial expuesta en repositorio público"


def _credencial(idcredencial: int) -> dict:
    return next(
        c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idcredencial"] == idcredencial
    )


class TestReemplazo:
    def test_el_reemplazo_lleva_el_mismo_nombre_y_entorno(self, partner_con_credenciales):
        """RF-O55.1. Renombrarlo obligaría al partner a cambiar configuración
        justo mientras apaga un fuego."""
        # Arrange
        original = _credencial(101)

        # Act
        resultado = RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert
        assert resultado["reemplazo"]["nombre_credencial"] == original["nombre_credencial"]
        assert resultado["reemplazo"]["entorno"] == original["entorno"]

    def test_la_unicidad_no_da_colision_falsa_consigo_misma(
        self, partner_con_credenciales
    ):
        """Escenario E. Si la comprobación releyera Pinot vería la recién
        revocada aún activa y **haría fallar la revocación** — justo la
        operación que no puede fallar (`research.md` Decision 4)."""
        # Act / Assert — que no lance es el aserto
        resultado = RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )
        assert resultado["reemplazo"]["idcredencial"] != 101

    def test_el_secreto_del_reemplazo_viaja_una_sola_vez(self, partner_con_credenciales):
        # Act
        resultado = RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert — en la respuesta sí; en la fila persistida, jamás
        assert resultado["reemplazo"]["client_secret"]
        persistida = _credencial(int(resultado["reemplazo"]["idcredencial"]))
        assert "client_secret" not in persistida
        assert persistida["client_secret_hash"] != resultado["reemplazo"]["client_secret"]

    def test_marca_la_revocada_como_inactiva(self, partner_con_credenciales):
        # Act
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert
        assert _credencial(101)["activo"] is False


class TestNoAfectaALasDemas:
    def test_las_otras_credenciales_siguen_activas(self, partner_con_credenciales):
        """RF-O55.2 — revocar una no interrumpe el resto de la integración."""
        # Act
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert
        assert _credencial(102)["activo"] is True

    def test_no_reactiva_por_accidente_una_ya_inactiva(self, partner_con_credenciales):
        # Act
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert
        assert _credencial(103)["activo"] is False


class TestBitacora:
    def test_registra_la_revocacion_con_el_idcredencial_exacto(
        self, partner_con_credenciales
    ):
        # Act
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert
        eventos = [
            e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == "revocacion_credencial" and e["idcredencial"] == 101
        ]
        assert len(eventos) == 1
        assert eventos[0]["ejecutado_por"] == "Partner"
        assert eventos[0]["motivo"] == MOTIVO

    def test_revocar_no_cambia_el_estado_del_partner(self, partner_con_credenciales):
        """`estado_anterior == estado_nuevo` es la forma de decirlo en la
        bitácora: el partner sigue activo tras revocar una credencial."""
        # Act
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo=MOTIVO
        )

        # Assert
        evento = next(
            e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == "revocacion_credencial" and e["idcredencial"] == 101
        )
        assert evento["estado_anterior"] == evento["estado_nuevo"] == "Activo"


class TestRechazos:
    def test_credencial_ajena_no_modifica_nada(self, partner_con_credenciales):
        """CA-PAC-004 — escenario C."""
        # Act / Assert
        with pytest.raises(RevocarCredencialError) as exc:
            RevocarCredencialService().revocar(
                idcredencial=101, idpartner_actor=999, motivo=MOTIVO
            )
        assert exc.value.code == "propiedad_credencial"
        assert _credencial(101)["activo"] is True

    def test_credencial_ya_inactiva_no_genera_segunda_entrada(
        self, partner_con_credenciales
    ):
        """CA-PAC-005 — escenario D. Una segunda entrada de revocación
        ensuciaría la bitácora, que aquí no es solo auditoría."""
        # Arrange
        antes = len([
            e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == "revocacion_credencial"
        ])

        # Act / Assert
        with pytest.raises(RevocarCredencialError) as exc:
            RevocarCredencialService().revocar(
                idcredencial=103, idpartner_actor=1, motivo=MOTIVO
            )
        assert exc.value.code == "credencial_inactiva"

        despues = len([
            e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == "revocacion_credencial"
        ])
        assert despues == antes

    def test_motivo_vacio_falla(self, partner_con_credenciales):
        with pytest.raises(RevocarCredencialError) as exc:
            RevocarCredencialService().revocar(
                idcredencial=101, idpartner_actor=1, motivo="  "
            )
        assert exc.value.code == "validation_error"
