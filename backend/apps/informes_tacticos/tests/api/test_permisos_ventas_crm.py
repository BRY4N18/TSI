"""T017 — el acotamiento por titularidad de Ventas y CRM (SC-008).

El Director de Marketing ve el departamento entero. El ejecutivo comercial ve
**sus** prospectos, y la meta lo declara. Sin `acotado_a`, los dos verian la
misma pantalla con cifras distintas y ninguno sabria por que.

El permiso demasiado ancho no produce sintoma: por eso se comprueba que quien
no entra recibe 403, y que quien entra acotado **pasa su identificador** a la
consulta — no que el endpoint responda 200.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.permissions import VentasCrmCompuestosPermission
from apps.informes_tacticos.services.ventas_crm_compuestos_service import CATALOGO
from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/ventas-crm"
UN_INFORME = "captacion-por-canal"


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    """La sesion del JWT se valida contra Pinot; sin el doble, todo es 401."""
    return mock_pinot


def _concede(roles):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    peticion = SimpleNamespace(user=usuario)
    vista = SimpleNamespace(kwargs={"informe": UN_INFORME})
    return VentasCrmCompuestosPermission().has_permission(peticion, vista)


def _cliente(roles, user_id=1):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=user_id, roles=roles, session_id=1)}"
        )
    )
    return api


class TestQuienEntraYQuienNo:
    def test_el_director_de_marketing_entra(self):
        assert _concede(["DirectorMarketing"])

    def test_el_ejecutivo_comercial_entra(self):
        assert _concede(["GerenteVentas"])

    def test_el_administrador_entra(self):
        assert _concede(["Administrador"])

    @pytest.mark.parametrize(
        "roles",
        [["Operador"], ["Cliente"], ["DirectorOperaciones"], []],
    )
    def test_quien_no_tiene_nada_que_ver_no_entra(self, roles):
        assert _cliente(roles).get(f"{BASE}/{UN_INFORME}").status_code == 403

    def test_sin_credencial_es_401_y_no_403(self):
        assert APIClient().get(f"{BASE}/{UN_INFORME}").status_code == 401


class TestElAcotamientoSeDeclaraYSeAplica:
    """⚠️ SC-008. El ejecutivo obtiene solo lo suyo, y la meta lo dice."""

    def test_el_ejecutivo_pasa_su_identificador_y_declara_propios(self, monkeypatch):
        capturado: dict = {}

        def fake_ejecutar(self, consulta, *, departamento, parametros):
            capturado.update(parametros)
            capturado["_consulta"] = consulta
            return []

        monkeypatch.setattr(ModeloRepository, "ejecutar", fake_ejecutar)

        respuesta = _cliente(["GerenteVentas"], user_id=1).get(f"{BASE}/{UN_INFORME}")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["meta"]["acotado_a"] == "propios"
        assert capturado["idejecutivo"] == 1
        assert capturado["_consulta"] == CATALOGO[UN_INFORME]

    def test_el_director_no_acota_y_declara_todos(self, monkeypatch):
        capturado: dict = {}

        def fake_ejecutar(self, consulta, *, departamento, parametros):
            capturado.update(parametros)
            return []

        monkeypatch.setattr(ModeloRepository, "ejecutar", fake_ejecutar)

        respuesta = _cliente(["DirectorMarketing"], user_id=1).get(f"{BASE}/{UN_INFORME}")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["meta"]["acotado_a"] == "todos"
        assert capturado["idejecutivo"] == -1

    def test_el_administrador_acota_igual_que_el_ejecutivo(self, monkeypatch):
        capturado: dict = {}

        def fake_ejecutar(self, consulta, *, departamento, parametros):
            capturado.update(parametros)
            return []

        monkeypatch.setattr(ModeloRepository, "ejecutar", fake_ejecutar)

        respuesta = _cliente(["Administrador"], user_id=1).get(f"{BASE}/{UN_INFORME}")

        assert respuesta.status_code == 200
        assert respuesta.json()["meta"]["acotado_a"] == "propios"
        assert capturado["idejecutivo"] == 1

    def test_el_pipeline_declara_que_los_pesos_son_una_convencion(self, monkeypatch):
        monkeypatch.setattr(ModeloRepository, "ejecutar", lambda *a, **k: [])

        respuesta = _cliente(["DirectorMarketing"]).get(f"{BASE}/pipeline-ponderado")

        assert respuesta.status_code == 200
        filtros = respuesta.json()["meta"]["filtros"]
        assert "pesos_etapa" in filtros
        assert "convencion" in filtros["nota_pesos"]
        assert "politica" in filtros["nota_pesos"]
