"""T029 — la autoridad repartida de Suscripciones (FR-038, FR-039)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.services.suscripciones_compuestos_service import (
    CATALOGO,
    MATERIA_CATALOGO,
    MATERIA_FINANZAS,
    MATERIAS,
)
from core.jwt_utils import create_access_token

BASE = "/api/v1/informes-tacticos/suscripciones"

DE_FINANZAS = sorted(i for i, m in MATERIAS.items() if m == MATERIA_FINANZAS)
DE_CATALOGO = sorted(i for i, m in MATERIAS.items() if m == MATERIA_CATALOGO)


def _concede(roles, informe):
    from apps.informes_tacticos.permissions import SuscripcionesCompuestosPermission

    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    peticion = SimpleNamespace(user=usuario)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return SuscripcionesCompuestosPermission().has_permission(peticion, vista)


def _cliente(roles):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=roles, session_id=1)}"
    )
    return api


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


class TestCadaDirectorSeQuedaFueraDeLaMateriaAjena:
    @pytest.mark.parametrize("informe", DE_CATALOGO)
    def test_el_financiero_no_entra_a_catalogo(self, informe):
        respuesta = _cliente(["DirectorFinanciero"]).get(f"{BASE}/{informe}")
        assert respuesta.status_code == 403, (
            f"el Director Financiero accede a '{informe}', que es de catálogo"
        )

    @pytest.mark.parametrize("informe", DE_FINANZAS)
    def test_estrategia_no_entra_a_finanzas(self, informe):
        respuesta = _cliente(["DirectorEstrategia"]).get(f"{BASE}/{informe}")
        assert respuesta.status_code == 403, (
            f"el Director de Estrategia accede a '{informe}', que es de cobro"
        )


class TestQuienSiEntra:
    @pytest.mark.parametrize("informe", DE_FINANZAS)
    def test_el_financiero_entra_a_finanzas(self, informe):
        assert _concede(["DirectorFinanciero"], informe)

    @pytest.mark.parametrize("informe", DE_CATALOGO)
    def test_estrategia_entra_a_catalogo(self, informe):
        assert _concede(["DirectorEstrategia"], informe)

    @pytest.mark.parametrize("informe", sorted(CATALOGO))
    def test_el_administrador_no_lee_gestion(self, informe):
        """Decisión del 2026-08-19: el `Administrador` opera, no lee gestión.

        Antes entraba a todo. Sigue entrando a los listados simples, que son
        trabajo operativo; lo que se le retiró es la lectura de gestión.
        """
        assert not _concede(["Administrador"], informe)

    def test_un_cliente_no_entra(self):
        respuesta = _cliente(["Cliente"]).get(f"{BASE}/mrr")
        assert respuesta.status_code == 403

    def test_todo_informe_tiene_materia(self):
        sin_materia = set(CATALOGO) - set(MATERIAS)
        assert not sin_materia
