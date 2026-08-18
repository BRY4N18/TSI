"""T025 — la autoridad limitada de Cuentas (FR-030)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.services.cuentas_compuestos_service import (
    CATALOGO,
    MATERIA_ACCESO,
    MATERIA_CICLO,
    MATERIA_INCORPORACION,
    MATERIAS,
)
from core.jwt_utils import create_access_token

BASE = "/api/v1/informes-tacticos/cuentas"

DE_ACCESO = sorted(i for i, m in MATERIAS.items() if m == MATERIA_ACCESO)
DE_CICLO = sorted(i for i, m in MATERIAS.items() if m == MATERIA_CICLO)
DE_INCORPORACION = sorted(i for i, m in MATERIAS.items() if m == MATERIA_INCORPORACION)
FUERA_DE_OT18 = DE_CICLO + DE_INCORPORACION


def _concede(roles, informe):
    from apps.informes_tacticos.permissions import CuentasCompuestosPermission

    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    peticion = SimpleNamespace(user=usuario)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return CuentasCompuestosPermission().has_permission(peticion, vista)


def _cliente(roles):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=roles, session_id=1)}"
    )
    return api


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


class TestElTecnologicoSeQuedaFueraDelCicloYLaIncorporacion:
    @pytest.mark.parametrize("informe", FUERA_DE_OT18)
    def test_tecnologico_no_entra_fuera_de_ot18(self, informe):
        respuesta = _cliente(["DirectorTecnologico"]).get(f"{BASE}/{informe}")
        assert respuesta.status_code == 403, (
            f"el Director Tecnológico accede a '{informe}', que no es de acceso"
        )


class TestQuienSiEntra:
    @pytest.mark.parametrize("informe", DE_ACCESO)
    def test_tecnologico_entra_a_ot18(self, informe):
        assert _concede(["DirectorTecnologico"], informe)

    @pytest.mark.parametrize("informe", sorted(CATALOGO))
    def test_el_administrador_entra_a_los_nueve(self, informe):
        assert _concede(["Administrador"], informe)

    def test_un_cliente_no_entra(self):
        respuesta = _cliente(["Cliente"]).get(f"{BASE}/churn-por-cohorte")
        assert respuesta.status_code == 403

    def test_todo_informe_tiene_materia(self):
        sin_materia = set(CATALOGO) - set(MATERIAS)
        assert not sin_materia
