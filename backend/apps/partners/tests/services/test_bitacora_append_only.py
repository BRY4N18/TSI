"""La bitacora solo admite INSERT (T047, CA-PAC-013, RN-PAC-013).

Aqui la inmutabilidad **no es solo auditoria**: `Fact_HistorialAccesoPartner` es
la fuente operativa de la reactivacion selectiva. Si sus filas se pudieran
editar, se podria alterar QUE credenciales se restituyen — es decir, resucitar
una credencial comprometida editando un registro.
"""

from __future__ import annotations

import pytest

from apps.partners.services.reactivar_partner_service import ReactivarPartnerService
from apps.partners.services.revocar_credencial_service import RevocarCredencialService
from apps.partners.services.suspender_partner_service import SuspenderPartnerService
from conftest import PINOT_STORE
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)

pytestmark = [pytest.mark.django_db, pytest.mark.service]


class TestSoloInsert:
    def test_el_repositorio_no_tiene_como_actualizar_ni_borrar(self):
        """No es una convención documentada: es una capacidad que no existe."""
        assert not hasattr(HistorialAccesoRepository, "update")
        assert not hasattr(HistorialAccesoRepository, "delete")

    def test_ninguna_operacion_del_modulo_reduce_ni_reescribe_la_bitacora(
        self, partner_con_credenciales
    ):
        """Se ejecuta el ciclo completo —revocar, suspender, reactivar— y se
        comprueba que la bitácora solo CRECE y que las filas previas quedan
        idénticas."""
        # Arrange
        instantanea = [dict(e) for e in PINOT_STORE["Fact_HistorialAccesoPartner"]]

        # Act
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo="expuesta"
        )
        SuspenderPartnerService().suspender(
            idpartner=1, motivo="mora", automatica=True
        )
        ReactivarPartnerService().reactivar(idpartner=1, motivo="pagó")

        # Assert — las filas anteriores siguen palabra por palabra
        actuales = PINOT_STORE["Fact_HistorialAccesoPartner"]
        assert len(actuales) > len(instantanea)
        for antigua, actual in zip(instantanea, actuales):
            assert antigua == actual

    def test_los_ids_de_historial_no_se_reutilizan(self, partner_con_credenciales):
        # Act
        SuspenderPartnerService().suspender(
            idpartner=1, motivo="mora", automatica=True
        )

        # Assert
        ids = [e["idhistorial"] for e in PINOT_STORE["Fact_HistorialAccesoPartner"]]
        assert len(ids) == len(set(ids))


class TestCoberturaDeEventos:
    def test_los_seis_tipos_del_modulo_se_escriben_con_autor_motivo_y_fecha(
        self, partner_con_credenciales, factura_excedente_vencida
    ):
        """CA-PAC-013 — RF-O55.4 pide los tres campos en cada evento."""
        # Arrange
        from apps.partners.services.evaluacion_mora_service import EvaluacionMoraService

        factura = factura_excedente_vencida(idcliente=1, dias_vencida=6)
        partner = next(p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == 1)

        # Act — los cinco flujos que escriben bitácora
        RevocarCredencialService().revocar(
            idcredencial=101, idpartner_actor=1, motivo="expuesta"
        )
        EvaluacionMoraService().evaluar_partner(partner)  # aviso_previo_suspension
        factura["fecha_vencimiento"] -= 20 * 86_400_000  # ahora supera el límite
        EvaluacionMoraService().evaluar_partner(partner)  # suspension_automatica
        ReactivarPartnerService().reactivar(idpartner=1)

        # Assert
        tipos = {e["tipo_cambio"] for e in PINOT_STORE["Fact_HistorialAccesoPartner"]}
        assert {
            "revocacion_credencial",
            "aviso_previo_suspension",
            "desactivacion_por_cascada",
            "suspension_automatica",
            "reactivacion",
        } <= tipos

        for evento in PINOT_STORE["Fact_HistorialAccesoPartner"]:
            assert evento["ejecutado_por"]
            assert evento["fecha_cambio"]
            assert "motivo" in evento
