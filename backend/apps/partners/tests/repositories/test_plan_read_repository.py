"""Derivacion del cupo desde el plan contratado (RF-PON-003, RN-PON-011).

Este repositorio prefiere fallar visiblemente antes que asumir un cupo: el
cupo es la base del calculo de excedente de CU-O54, y un valor inventado
seria dinero mal cobrado sin que nadie se entere. Casi todos los tests de
aqui comprueban justamente que NO adivina.
"""

from __future__ import annotations

import json

import pytest

from conftest import PINOT_STORE
from core.repositories.partners.plan_read_repository import (
    PlanReadError,
    PlanReadRepository,
)

pytestmark = [pytest.mark.django_db, pytest.mark.repository]

LIMITES_COMPLETOS = json.dumps({"api_calls_mes": 10000, "api_calls_minuto": 120})


def _plan(idplan=940, nombre="Profesional", limites=LIMITES_COMPLETOS):
    PINOT_STORE["Dim_Plan"].append(
        {"idplan": idplan, "nombre": nombre, "limites": limites, "activo": True}
    )


def _suscripcion(idcliente=940, idplan=940, estado="Activa", activo=True, fecha_inicio=1):
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": idcliente,
            "idcliente": idcliente,
            "idplan": idplan,
            "estado": estado,
            "activo": activo,
            "fecha_inicio": fecha_inicio,
        }
    )


class TestCupoDerivado:
    def test_cupo_when_suscripcion_vigente_devuelve_los_limites_del_plan(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _plan()
        _suscripcion()

        # Act
        cupo = PlanReadRepository().cupo_del_cliente(940)

        # Assert — el cupo NO se elige: sale del plan contratado
        assert cupo == {
            "nombre_plan": "Profesional",
            "api_calls_mes": 10000,
            "api_calls_minuto": 120,
        }

    def test_cupo_usa_la_suscripcion_mas_reciente(self, mock_pinot, mock_kafka):
        """Si el cliente cambio de plan, manda el vigente, no el historico."""
        # Arrange
        _plan(idplan=941, nombre="Basico", limites=json.dumps(
            {"api_calls_mes": 100, "api_calls_minuto": 5}
        ))
        _plan(idplan=942, nombre="Empresarial", limites=json.dumps(
            {"api_calls_mes": 50000, "api_calls_minuto": 600}
        ))
        _suscripcion(idcliente=941, idplan=941, estado="Cancelada", fecha_inicio=1)
        _suscripcion(idcliente=941, idplan=942, estado="Activa", fecha_inicio=999)

        # Act
        cupo = PlanReadRepository().cupo_del_cliente(941)

        # Assert
        assert cupo["nombre_plan"] == "Empresarial"


class TestSuscripcionNoVigente:
    def test_cupo_when_sin_suscripcion_raises_sin_suscripcion(self, mock_pinot, mock_kafka):
        # Act / Assert
        with pytest.raises(PlanReadError) as exc:
            PlanReadRepository().cupo_del_cliente(999999)
        assert exc.value.code == "sin_suscripcion"

    def test_cupo_when_suscripcion_cancelada_raises(self, mock_pinot, mock_kafka):
        """RN-PON-011 — una suscripcion cancelada no da derecho a cupo.

        Este es el hueco por el que un cliente sin pagar seguiria consumiendo
        la API si solo se comprobara la existencia de la suscripcion.
        """
        # Arrange
        _plan(idplan=943)
        _suscripcion(idcliente=943, idplan=943, estado="Cancelada")

        # Act / Assert
        with pytest.raises(PlanReadError) as exc:
            PlanReadRepository().cupo_del_cliente(943)
        assert exc.value.code == "sin_suscripcion"

    def test_cupo_when_suscripcion_inactiva_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _plan(idplan=944)
        _suscripcion(idcliente=944, idplan=944, estado="Activa", activo=False)

        # Act / Assert
        with pytest.raises(PlanReadError):
            PlanReadRepository().cupo_del_cliente(944)


class TestPlanIncompleto:
    def test_cupo_when_plan_inexistente_raises_plan_incompleto(self, mock_pinot, mock_kafka):
        # Arrange — suscripcion que apunta a un plan que no existe
        _suscripcion(idcliente=945, idplan=999999)

        # Act / Assert
        with pytest.raises(PlanReadError) as exc:
            PlanReadRepository().cupo_del_cliente(945)
        assert exc.value.code == "plan_incompleto"

    def test_cupo_when_falta_un_limite_raises_en_vez_de_asumirlo(
        self, mock_pinot, mock_kafka
    ):
        """Falta `api_calls_minuto`: se falla, no se inventa un valor."""
        # Arrange
        _plan(idplan=946, limites=json.dumps({"api_calls_mes": 10000}))
        _suscripcion(idcliente=946, idplan=946)

        # Act / Assert
        with pytest.raises(PlanReadError) as exc:
            PlanReadRepository().cupo_del_cliente(946)
        assert exc.value.code == "plan_incompleto"
        assert "api_calls_minuto" in exc.value.detail

    def test_cupo_when_limites_json_invalido_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _plan(idplan=947, limites="esto no es json")
        _suscripcion(idcliente=947, idplan=947)

        # Act / Assert
        with pytest.raises(PlanReadError) as exc:
            PlanReadRepository().cupo_del_cliente(947)
        assert exc.value.code == "plan_incompleto"


class TestSoloLectura:
    def test_el_repositorio_no_expone_escritura(self):
        """`Fact_Suscripcion` y `Dim_Plan` son de subscriptions-and-billing.

        Este modulo los lee y nunca los escribe; la ausencia de metodos de
        escritura es la garantia, no un acuerdo verbal.
        """
        # Act
        metodos = {m for m in dir(PlanReadRepository) if not m.startswith("_")}

        # Assert
        assert metodos == {"suscripcion_vigente", "find_plan", "cupo_del_cliente"}
