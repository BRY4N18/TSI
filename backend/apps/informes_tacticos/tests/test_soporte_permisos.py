"""T038, T039 — quién entra a Soporte y qué no se le muestra."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.permissions import SoporteCompuestosPermission
from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte"
UN_INFORME = "cumplimiento-sla"
TEXTO_PROHIBIDO = ("asunto", "descripcion", "mensaje", "es_nota_interna", "nombre_agente")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def _concede(roles):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    peticion = SimpleNamespace(user=usuario)
    vista = SimpleNamespace(kwargs={"informe": UN_INFORME})
    return SoporteCompuestosPermission().has_permission(peticion, vista)


def _cliente(roles, user_id=1):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=user_id, roles=roles, session_id=1)}"
        )
    )
    return api


class TestQuienEntraYQuienNo:
    def test_el_gerente_de_exito_entra(self):
        assert _concede(["GerenteExitoCliente"])

    def test_el_agente_entra(self):
        assert _concede(["Soporte"])

    def test_el_administrador_no_lee_gestion(self):
        """Decisión del 2026-08-19: el `Administrador` opera, no lee gestión.

        Sigue entrando a los listados simples, que son trabajo operativo.
        """
        assert not _concede(["Administrador"])

    def test_un_cliente_recibe_403(self):
        assert _cliente(["Cliente"]).get(f"{BASE}/{UN_INFORME}").status_code == 403

    def test_sin_credencial_es_401(self):
        assert APIClient().get(f"{BASE}/{UN_INFORME}").status_code == 401


class TestAcotamientoYExencion:
    def test_el_agente_pasa_su_identificador(self, monkeypatch):
        capturado: dict = {}

        def fake_ejecutar(self, consulta, *, departamento, parametros):
            capturado.update(parametros)
            return []

        monkeypatch.setattr(ModeloRepository, "ejecutar", fake_ejecutar)
        respuesta = _cliente(["Soporte"], user_id=7).get(f"{BASE}/{UN_INFORME}")
        assert respuesta.status_code == 200
        assert respuesta.json()["meta"]["acotado_a"] == "propios"
        assert capturado["idagente"] == 7

    def test_el_gerente_no_acota(self, monkeypatch):
        capturado: dict = {}

        def fake_ejecutar(self, consulta, *, departamento, parametros):
            capturado.update(parametros)
            return []

        monkeypatch.setattr(ModeloRepository, "ejecutar", fake_ejecutar)
        respuesta = _cliente(["GerenteExitoCliente"]).get(f"{BASE}/{UN_INFORME}")
        assert respuesta.status_code == 200
        assert respuesta.json()["meta"]["acotado_a"] == "todos"
        assert capturado["idagente"] == -1

    def test_el_gerente_no_recibe_texto_de_tickets(self, monkeypatch):
        monkeypatch.setattr(
            ModeloRepository,
            "ejecutar",
            lambda *a, **k: [{"periodo": "2026-08-01", "tickets": 1, "con_compromiso": 1,
                               "sin_compromiso": 0, "cumplidos": 1, "incumplidos": 0,
                               "pct_cumplimiento": 100.0, "pct_sin_compromiso": 0.0,
                               "motivo_pendiente_clasificar": 0, "motivo_sin_compromiso": 0,
                               "motivo_sin_config": 0}],
        )
        cuerpo = _cliente(["GerenteExitoCliente"]).get(f"{BASE}/{UN_INFORME}").json()
        for fila in cuerpo["data"]["resultados"]:
            for campo in TEXTO_PROHIBIDO:
                assert campo not in fila
        assert "nombre_agente" not in cuerpo["data"]
