"""RF-PON-010 / RN-PON-010 — la bitacora es inmutable (solo INSERT)."""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import SIN_CREDENCIAL, SIN_MOTIVO
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.repository]


class TestInmutabilidad:
    def test_repositorio_no_expone_update_ni_delete(self):
        """La inmutabilidad no es una convencion que recordar: es una capacidad
        que no existe. Si alguien anadiera `update`, este test lo detecta."""
        # Act
        metodos = {m for m in dir(HistorialAccesoRepository) if not m.startswith("_")}

        # Assert
        assert "update" not in metodos
        assert "delete" not in metodos
        assert "registrar" in metodos

    def test_registrar_dos_veces_crea_dos_filas(self, mock_pinot, mock_kafka):
        """Cada evento es una fila nueva; nunca se sobrescribe la anterior."""
        # Arrange
        repo = HistorialAccesoRepository()

        # Act
        repo.registrar(
            idpartner=1, tipo_cambio="registro", ejecutado_por="Sistema", estado_nuevo="A"
        )
        repo.registrar(
            idpartner=1, tipo_cambio="asignacion_plan", ejecutado_por="Sistema", estado_nuevo="B"
        )

        # Assert
        eventos = PINOT_STORE["Fact_HistorialAccesoPartner"]
        assert len(eventos) == 2
        assert [e["estado_nuevo"] for e in eventos] == ["A", "B"]


class TestCentinelas:
    def test_registrar_sin_credencial_usa_centinela_menos_uno(self, mock_pinot, mock_kafka):
        """Pinot no almacena NULL: un evento del partner lleva -1, no None."""
        # Act
        evento = HistorialAccesoRepository().registrar(
            idpartner=1, tipo_cambio="registro", ejecutado_por="Sistema", estado_nuevo="A"
        )

        # Assert
        assert evento["idcredencial"] == SIN_CREDENCIAL
        assert evento["motivo"] == SIN_MOTIVO
        assert evento["estado_anterior"] == SIN_MOTIVO
        assert None not in evento.values()

    def test_registrar_con_credencial_guarda_su_id(self, mock_pinot, mock_kafka):
        # Act
        evento = HistorialAccesoRepository().registrar(
            idpartner=1,
            tipo_cambio="activacion_sandbox",
            ejecutado_por="Partner",
            estado_nuevo="Pruebas activo",
            idcredencial=77,
        )

        # Assert
        assert evento["idcredencial"] == 77


class TestConsultas:
    def test_ultimo_evento_devuelve_el_mas_reciente(self, mock_pinot, mock_kafka):
        """Con eventos en el mismo milisegundo, desempata `idhistorial`."""
        # Arrange
        repo = HistorialAccesoRepository()
        repo.registrar(
            idpartner=5, tipo_cambio="registro", ejecutado_por="Sistema", estado_nuevo="primero"
        )
        repo.registrar(
            idpartner=5, tipo_cambio="asignacion_plan", ejecutado_por="Sistema", estado_nuevo="ultimo"
        )

        # Act
        ultimo = repo.ultimo_evento(5)

        # Assert
        assert ultimo["estado_nuevo"] == "ultimo"

    def test_existe_evento_filtra_por_tipo_y_motivo(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialAccesoRepository()
        repo.registrar(
            idpartner=6,
            tipo_cambio="aviso_previo_suspension",
            ejecutado_por="Sistema",
            estado_nuevo="x",
            motivo="T-10",
        )

        # Act / Assert
        assert repo.existe_evento(6, "aviso_previo_suspension", motivo="T-10") is True
        assert repo.existe_evento(6, "aviso_previo_suspension", motivo="T-5") is False
        assert repo.existe_evento(6, "suspension_automatica") is False

    def test_list_by_partner_no_mezcla_partners(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialAccesoRepository()
        repo.registrar(idpartner=7, tipo_cambio="registro", ejecutado_por="S", estado_nuevo="a")
        repo.registrar(idpartner=8, tipo_cambio="registro", ejecutado_por="S", estado_nuevo="b")

        # Act
        eventos = repo.list_by_partner(7)

        # Assert
        assert len(eventos) == 1
        assert eventos[0]["idpartner"] == 7
