"""Mora de excedente: avisos, suspension y fronteras (T034-T038, T060).

Cubre los escenarios F, G y M, y los dos hallazgos que `/speckit-analyze`
encontro antes de implementar (§ 15 D3):

* **Solo `Pendiente` vencida genera mora aqui.** Una `Fallida` es de
  Suscripciones; contarla haria que dos modulos suspendieran por lo mismo.
* **La mora se resuelve por `id_cliente`**, porque `Fact_Factura` no tiene
  `idpartner`. Una consulta contra esa columna devolveria cero morosos **en
  silencio**, y el doble en memoria no lo delataria.
"""

from __future__ import annotations

import pytest

from apps.partners.services.evaluacion_mora_service import EvaluacionMoraService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]


def _partner(idpartner: int = 1) -> dict:
    return next(p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == idpartner)


def _avisos() -> list[dict]:
    return [
        e for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
        if e["tipo_cambio"] == "aviso_previo_suspension"
    ]


class TestQueCuentaComoMora:
    def test_solo_las_facturas_de_excedente_generan_mora(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """T038 / § 15 D2 — una factura de suscripción impagada no suspende al
        partner aquí: eso lo gestiona `subscriptions-and-billing`."""
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=30, tipo="suscripcion")

        # Act
        estado = EvaluacionMoraService().estado_de_mora(_partner())

        # Assert
        assert estado["en_mora"] is False

    def test_una_factura_FALLIDA_no_genera_mora_aqui(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """🎯 § 15 D3. `Fallida` es el disparador de Suscripciones (RF-SUSF-007).

        Si contase también aquí, el mismo impago suspendería la suscripción y al
        partner con umbrales distintos, y la reactivación quedaría en
        contradicción permanente: allá es automática, aquí nunca lo es.
        """
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=30, estado_pago="Fallida")

        # Act
        estado = EvaluacionMoraService().estado_de_mora(_partner())

        # Assert
        assert estado["en_mora"] is False

    def test_una_factura_en_disputa_no_genera_mora(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """T037 / RN-PAC-015 — escenario M. Suspender por una factura que el
        partner está cuestionando lo castigaría por reclamar."""
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=30, estado_pago="En disputa")

        # Act
        estado = EvaluacionMoraService().estado_de_mora(_partner())

        # Assert
        assert estado["en_mora"] is False

    def test_una_pendiente_vencida_SI_genera_mora(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=12)

        # Act
        estado = EvaluacionMoraService().estado_de_mora(_partner())

        # Assert
        assert estado["en_mora"] is True
        assert estado["dias_mora"] == 12

    def test_la_mora_se_resuelve_por_id_cliente_no_por_idpartner(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """🎯 § 15 D3. El partner 1 es el cliente 1. Una factura del cliente 999
        no puede contarle como mora, y —lo importante— la del cliente 1 **sí**
        debe encontrarla: `Fact_Factura` no tiene `idpartner`."""
        # Arrange
        factura_excedente_vencida(idcliente=999, dias_vencida=40, id_factura="AJENA")
        factura_excedente_vencida(idcliente=1, dias_vencida=11, id_factura="PROPIA")

        # Act
        estado = EvaluacionMoraService().estado_de_mora(_partner())

        # Assert
        assert estado["en_mora"] is True
        assert estado["factura"]["id_factura"] == "PROPIA"

    def test_el_ciclo_lo_delimita_la_factura_vencida_mas_antigua(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=3, id_factura="RECIENTE")
        factura_excedente_vencida(idcliente=1, dias_vencida=13, id_factura="ANTIGUA")

        # Act
        estado = EvaluacionMoraService().estado_de_mora(_partner())

        # Assert
        assert estado["factura"]["id_factura"] == "ANTIGUA"
        assert estado["dias_mora"] == 13


class TestAvisos:
    def test_avisa_T10_al_alcanzar_los_cinco_dias_de_mora(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """Con límite 15: a los 5 días de mora faltan 10 para el corte."""
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=6)

        # Act
        resultado = EvaluacionMoraService().evaluar_partner(_partner())

        # Assert
        assert resultado["accion"] == "avisado"
        assert resultado["aviso"] == "T-10"

    def test_avisa_T5_al_acercarse_al_limite(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=11)

        # Act
        resultado = EvaluacionMoraService().evaluar_partner(_partner())

        # Assert
        assert resultado["aviso"] == "T-5"

    def test_no_duplica_el_aviso_al_reejecutar_el_job_el_mismo_dia(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """T034 / RN-PAC-006 — escenario F."""
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=6)
        servicio = EvaluacionMoraService()
        servicio.evaluar_partner(_partner())

        # Act
        segundo = servicio.evaluar_partner(_partner())

        # Assert
        assert segundo["accion"] == "aviso_ya_enviado"
        assert len(_avisos()) == 1

    def test_el_aviso_no_cambia_el_estado_del_partner(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """T035 — avisar no es suspender: el partner sigue activo."""
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=6)

        # Act
        EvaluacionMoraService().evaluar_partner(_partner())

        # Assert
        assert _partner()["activo"] is True
        aviso = _avisos()[0]
        assert aviso["estado_anterior"] == aviso["estado_nuevo"] == "Activo"

    def test_la_regularizacion_entre_avisos_cierra_el_ciclo_sin_cancelar_nada(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """T036 / RN-PAC-007 — escenario G.

        No hay lógica de cancelación y no debe haberla: la factura pagada
        **desaparece de la condición de entrada** y el aviso pendiente
        sencillamente nunca se evalúa. Es una propiedad del diseño.
        """
        # Arrange
        factura = factura_excedente_vencida(idcliente=1, dias_vencida=6)
        servicio = EvaluacionMoraService()
        servicio.evaluar_partner(_partner())

        # Act — el partner paga antes de T-5
        factura["estado_pago"] = "Pagada"
        resultado = servicio.evaluar_partner(_partner())

        # Assert
        assert resultado["accion"] == "sin_mora"
        assert len(_avisos()) == 1
        assert _partner()["activo"] is True


class TestSuspensionPorMora:
    def test_suspende_al_superarse_el_limite(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """CA-PAC-008 — sin intervención humana (escenario H)."""
        # Arrange
        factura_excedente_vencida(idcliente=1, dias_vencida=16)

        # Act
        resultado = EvaluacionMoraService().evaluar_partner(_partner())

        # Assert
        assert resultado["accion"] == "suspendido"
        assert _partner()["activo"] is False
        assert all(
            not c["activo"] for c in PINOT_STORE["Dim_CredencialAPI"]
            if c["idpartner"] == 1
        )

    def test_el_sistema_NO_reactiva_solo_tras_pagar(
        self, partner_suspendido, factura_excedente_vencida
    ):
        """🎯 T027 / RN-PAC-009 — escenario J.

        Protege de un refactor bienintencionado («si ya pagó, ¿por qué no
        reactivarlo?»). La respuesta: chocaría con RN-SUSF-011 de Suscripciones
        y ambos estados quedarían peleados para siempre. Reabrir un acceso es
        una decisión humana.
        """
        # Arrange — deuda pagada, partner ya suspendido
        factura_excedente_vencida(idcliente=1, dias_vencida=20, estado_pago="Pagada")

        # Act — el job completo, que es donde podría colarse la reactivación
        from apps.partners.jobs.evaluacion_mora_job import EvaluacionMoraJob

        EvaluacionMoraJob().ejecutar()

        # Assert
        assert _partner()["activo"] is False, "El sistema reactivó solo (RN-PAC-009)"
        assert not any(
            e["tipo_cambio"] == "reactivacion"
            for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
        )
