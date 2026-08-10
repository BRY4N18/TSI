"""Dim_VersionContratoAPI — el versionado es POR SERVICIO (CU-O50, D1).

Sin la FK `id_servicio`, los servicios del catalogo colapsarian en una sola
linea temporal y publicar la v2 de «API Despacho» degradaria la v1 de «API
Registro de accidentes». El aislamiento por servicio es lo que mas se prueba.
"""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import SIN_FECHA_RETIRO, SIN_URL
from core.repositories.partners.version_contrato_repository import (
    VersionContratoRepository,
)

pytestmark = [pytest.mark.django_db, pytest.mark.repository]

DESPACHO = 1
ACCIDENTES = 2


class TestCentinelas:
    def test_upsert_when_sin_url_ni_retiro_usa_centinelas(self, mock_pinot, mock_kafka):
        """Pinot no almacena NULL: la ausencia se materializa como centinela."""
        # Act
        fila = VersionContratoRepository().upsert(
            {"id_servicio": DESPACHO, "version": "v1", "estado": "vigente"}
        )

        # Assert
        assert fila["spec_url"] == SIN_URL
        assert fila["fecha_retiro"] == SIN_FECHA_RETIRO
        assert None not in fila.values()


class TestAislamientoPorServicio:
    def test_vigente_when_dos_servicios_devuelve_la_de_cada_uno(self, mock_pinot, mock_kafka):
        # Arrange
        repo = VersionContratoRepository()
        repo.upsert({"id_servicio": DESPACHO, "version": "v3", "estado": "vigente"})
        repo.upsert({"id_servicio": ACCIDENTES, "version": "v1", "estado": "vigente"})

        # Act / Assert — cada servicio lleva su propio ciclo
        assert repo.vigente(DESPACHO)["version"] == "v3"
        assert repo.vigente(ACCIDENTES)["version"] == "v1"

    def test_list_by_servicio_no_mezcla_servicios(self, mock_pinot, mock_kafka):
        # Arrange
        repo = VersionContratoRepository()
        repo.upsert({"id_servicio": DESPACHO, "version": "v1", "estado": "vigente"})
        repo.upsert({"id_servicio": ACCIDENTES, "version": "v1", "estado": "vigente"})

        # Act
        versiones = repo.list_by_servicio(DESPACHO)

        # Assert
        assert len(versiones) == 1
        assert versiones[0]["id_servicio"] == DESPACHO

    def test_find_version_when_misma_version_en_otro_servicio_no_la_confunde(
        self, mock_pinot, mock_kafka
    ):
        """Dos servicios pueden tener ambos una «v1» sin ser la misma cosa."""
        # Arrange
        repo = VersionContratoRepository()
        repo.upsert({"id_servicio": DESPACHO, "version": "v1", "estado": "vigente"})

        # Act / Assert
        assert repo.find_version(DESPACHO, "v1") is not None
        assert repo.find_version(ACCIDENTES, "v1") is None


class TestVigencia:
    def test_vigente_when_solo_hay_soportadas_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = VersionContratoRepository()
        repo.upsert({"id_servicio": DESPACHO, "version": "v1", "estado": "soportada"})

        # Act / Assert
        assert repo.vigente(DESPACHO) is None

    def test_list_by_servicio_excluye_las_inactivas(self, mock_pinot, mock_kafka):
        # Arrange
        repo = VersionContratoRepository()
        repo.upsert(
            {"id_servicio": DESPACHO, "version": "v0", "estado": "retirada", "activo": False}
        )

        # Act / Assert
        assert repo.list_by_servicio(DESPACHO) == []

    def test_find_version_when_no_existe_returns_none(self, mock_pinot, mock_kafka):
        # Act / Assert
        assert VersionContratoRepository().find_version(DESPACHO, "v99") is None
