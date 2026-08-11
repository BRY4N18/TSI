"""Dim_EstadoIntegracion — catálogo de la foto congelada (RF-APM-005).

Solo hay **dos estados alcanzables**, y coinciden con el entorno de la
credencial. `Suspendido` quedó desactivado por inalcanzable: un partner
suspendido recibe 403 y su llamada no genera fila.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE
from core.repositories.partners.estado_integracion_repository import (
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    ESTADO_SUSPENDIDO_INALCANZABLE,
    EstadoIntegracionError,
    EstadoIntegracionRepository,
)

pytestmark = [pytest.mark.django_db, pytest.mark.repository]


@pytest.fixture
def catalogo(mock_pinot, mock_kafka):
    """El catálogo tal como lo deja `database/seed_estado_integracion.py`."""
    PINOT_STORE["Dim_EstadoIntegracion"].extend([
        {
            "idestadointegracion": 1,
            "nombre": "Pruebas activo",
            "descripcion": "Sandbox",
            "activo": True,
        },
        {
            "idestadointegracion": 2,
            "nombre": "Producción activa",
            "descripcion": "Producción",
            "activo": True,
        },
        {
            "idestadointegracion": 3,
            "nombre": "Suspendido",
            "descripcion": "INALCANZABLE",
            "activo": False,
        },
    ])


class TestSoloLectura:
    def test_el_repositorio_no_escribe_el_catalogo(self):
        """El catálogo lo siembra un script; en runtime solo se lee."""
        # Act
        metodos = {m for m in dir(EstadoIntegracionRepository) if not m.startswith("_")}

        # Assert
        assert metodos == {"listar", "find_by_id", "estado_para_entorno"}


class TestCatalogo:
    def test_listar_excluye_los_inactivos_por_defecto(self, catalogo):
        """`Suspendido` está desactivado: no debe ofrecerse como opción."""
        # Act
        estados = EstadoIntegracionRepository().listar()

        # Assert
        assert [e["idestadointegracion"] for e in estados] == [1, 2]

    def test_listar_puede_incluir_los_inactivos_para_histórico(self, catalogo):
        # Act
        estados = EstadoIntegracionRepository().listar(solo_activos=False)

        # Assert
        assert len(estados) == 3

    def test_find_by_id_devuelve_el_estado(self, catalogo):
        # Act
        estado = EstadoIntegracionRepository().find_by_id(2)

        # Assert
        assert estado["nombre"] == "Producción activa"

    def test_find_by_id_inexistente_devuelve_none(self, catalogo):
        # Act / Assert
        assert EstadoIntegracionRepository().find_by_id(99) is None


class TestResolucionPorEntorno:
    def test_sandbox_congela_pruebas_activo(self):
        # Act / Assert
        assert (
            EstadoIntegracionRepository.estado_para_entorno("Sandbox")
            == ESTADO_PRUEBAS_ACTIVO
        )

    def test_produccion_congela_produccion_activa(self):
        # Act / Assert
        assert (
            EstadoIntegracionRepository.estado_para_entorno("Producción")
            == ESTADO_PRODUCCION_ACTIVA
        )

    def test_nunca_resuelve_al_estado_suspendido(self):
        """Ninguna llamada atendida puede llevarlo: si el partner estuviera
        suspendido, la petición no habría llegado a registrarse."""
        # Act
        resueltos = {
            EstadoIntegracionRepository.estado_para_entorno(e)
            for e in ("Sandbox", "Producción")
        }

        # Assert
        assert ESTADO_SUSPENDIDO_INALCANZABLE not in resueltos

    def test_un_entorno_desconocido_lanza_en_vez_de_adivinar(self):
        """Escribir un estado equivocado falsearía el histórico de consumo."""
        # Act / Assert
        with pytest.raises(EstadoIntegracionError):
            EstadoIntegracionRepository.estado_para_entorno("Staging")

    def test_el_entorno_vacio_tambien_lanza(self):
        # Act / Assert
        with pytest.raises(EstadoIntegracionError):
            EstadoIntegracionRepository.estado_para_entorno("")
