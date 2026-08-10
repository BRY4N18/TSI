"""Dim_Partner — centinelas, unicidad por cliente y upsert FULL (RF-PON-001).

Los centinelas no son un detalle de estilo: `planapi = 'null'` (el centinela
implicito que Pinot ponia antes de la migracion) dejaba SIEMPRE cierta la
guarda de RF-PON-004, y un partner sin plan podia emitir credenciales.
"""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import SIN_ACTIVACION, SIN_CUPO, SIN_PLAN, SIN_SUSPENSION
from conftest import PINOT_STORE
from core.repositories.partners.partner_repository import PartnerRepository

pytestmark = [pytest.mark.django_db, pytest.mark.repository]


DATOS = {
    "idcliente": 910,
    "nombrepartner": "Aseguradora Norte",
    "contacto_tecnico_nombre": "Ana Torres",
    "contacto_tecnico_gmail": "ana@norte.com",
}


class TestCreacionConCentinelas:
    def test_create_when_nuevo_nace_sin_plan_ni_cupo(self, mock_pinot, mock_kafka):
        # Act
        fila = PartnerRepository().create(DATOS)

        # Assert — RF-PON-001: el plan se asigna despues, en un paso aparte
        assert fila["planapi"] == SIN_PLAN
        assert fila["limitellamadasmes"] == SIN_CUPO
        assert fila["limitellamadasminuto"] == SIN_CUPO

    def test_create_no_publica_ningun_none(self, mock_pinot, mock_kafka):
        """Pinot convertiria un None en un centinela propio que rompe las guardas."""
        # Act
        fila = PartnerRepository().create(DATOS)

        # Assert
        assert None not in fila.values()

    def test_create_when_nuevo_nace_sin_activacion_ni_suspension(self, mock_pinot, mock_kafka):
        # Act
        fila = PartnerRepository().create(DATOS)

        # Assert
        assert fila["sandbox_activado"] == SIN_ACTIVACION
        assert fila["sandbox_expiracion"] == SIN_ACTIVACION
        assert fila["fecha_suspension"] == SIN_SUSPENSION
        assert fila["motivo_suspension"] == SIN_SUSPENSION
        assert fila["activo"] is True

    def test_create_when_sin_plan_la_guarda_de_emision_lo_excluye(self, mock_pinot, mock_kafka):
        """El centinela debe ser distinto de cualquier plan real.

        Esta es la comparacion exacta que hace `EmitirCredencialService`.
        """
        # Act
        fila = PartnerRepository().create(DATOS)

        # Assert
        assert not fila["planapi"]  # falsy -> la guarda `if not planapi` lo bloquea
        assert fila["planapi"] != "null"  # el centinela viejo era este string

    def test_create_asigna_ids_incrementales(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PartnerRepository()

        # Act
        primero = repo.create(DATOS)
        segundo = repo.create({**DATOS, "idcliente": 911})

        # Assert
        assert segundo["idpartner"] == primero["idpartner"] + 1


class TestUnicidadPorCliente:
    def test_find_by_cliente_when_existe_lo_encuentra(self, mock_pinot, mock_kafka):
        """RN-PON-002 — Pinot no soporta UNIQUE; la unicidad se valida aqui."""
        # Arrange
        repo = PartnerRepository()
        creado = repo.create(DATOS)

        # Act
        encontrado = repo.find_by_cliente(910)

        # Assert
        assert encontrado is not None
        assert encontrado["idpartner"] == creado["idpartner"]

    def test_find_by_cliente_when_no_existe_returns_none(self, mock_pinot, mock_kafka):
        # Act / Assert
        assert PartnerRepository().find_by_cliente(999999) is None


class TestUpsertFull:
    def test_update_republica_la_fila_completa(self, mock_pinot, mock_kafka):
        """Publicar solo lo cambiado borraria el resto: el upsert es por PK."""
        # Arrange
        repo = PartnerRepository()
        creado = repo.create(DATOS)

        # Act
        actualizado = repo.update(creado["idpartner"], {"planapi": "Profesional"})

        # Assert — cambia lo pedido y conserva lo demas
        assert actualizado["planapi"] == "Profesional"
        assert actualizado["nombrepartner"] == DATOS["nombrepartner"]
        assert actualizado["contacto_tecnico_gmail"] == DATOS["contacto_tecnico_gmail"]

    def test_update_avanza_fecha_actualizacion(self, mock_pinot, mock_kafka):
        """Es el `comparisonColumn` del upsert: si no avanza, Pinot puede
        descartar la mutacion."""
        # Arrange
        repo = PartnerRepository()
        creado = repo.create(DATOS)

        # Act
        actualizado = repo.update(creado["idpartner"], {"planapi": "Basico"})

        # Assert
        assert actualizado["fecha_actualizacion"] >= creado["fecha_actualizacion"]

    def test_update_when_inexistente_returns_none(self, mock_pinot, mock_kafka):
        # Act / Assert
        assert PartnerRepository().update(404404, {"planapi": "X"}) is None


class TestPaginacionPorCursor:
    def test_list_when_hay_mas_devuelve_next_cursor(self, mock_pinot, mock_kafka):
        # Arrange — 3 partners, se piden de 2 en 2
        repo = PartnerRepository()
        for i in range(3):
            repo.create({**DATOS, "idcliente": 920 + i})

        # Act
        pagina, next_cursor = repo.list(limit=2)

        # Assert
        assert len(pagina) == 2
        assert next_cursor is not None

    def test_list_when_ultima_pagina_next_cursor_es_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PartnerRepository()
        repo.create(DATOS)

        # Act
        pagina, next_cursor = repo.list(limit=20)

        # Assert
        assert len(pagina) == 1
        assert next_cursor is None

    def test_list_no_devuelve_mas_del_limite_pedido(self, mock_pinot, mock_kafka):
        """Pinot aplica un LIMIT 10 implicito y silencioso; el limite debe ser
        el que pide quien llama, no el que Pinot decida."""
        # Arrange
        repo = PartnerRepository()
        for i in range(5):
            repo.create({**DATOS, "idcliente": 930 + i})

        # Act
        pagina, _ = repo.list(limit=3)

        # Assert
        assert len(pagina) == 3
