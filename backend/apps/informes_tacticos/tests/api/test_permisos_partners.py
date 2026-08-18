"""T023 — un rol de partner no accede a los compuestos (FR-034)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.services.partners_compuestos_service import CATALOGO
from core.jwt_utils import create_access_token

BASE = "/api/v1/informes-tacticos/partners"


def _concede(roles, informe):
    from apps.informes_tacticos.permissions import PartnersCompuestosPermission

    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    peticion = SimpleNamespace(user=usuario)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return PartnersCompuestosPermission().has_permission(peticion, vista)


def _cliente(roles):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=roles, session_id=1)}"
    )
    return api


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


class TestElPartnerNoEntra:
    @pytest.mark.parametrize("informe", sorted(CATALOGO))
    def test_partner_integracion_fuera(self, informe):
        respuesta = _cliente(["PartnerIntegracion"]).get(f"{BASE}/{informe}")
        assert respuesta.status_code == 403, informe


class TestQuienSiEntra:
    @pytest.mark.parametrize("informe", sorted(CATALOGO))
    def test_tecnologico_entra(self, informe):
        assert _concede(["DirectorTecnologico"], informe)

    @pytest.mark.parametrize("informe", sorted(CATALOGO))
    def test_administrador_entra(self, informe):
        assert _concede(["Administrador"], informe)
