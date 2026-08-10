"""RF-PON-003 — el cupo se deriva del plan contratado y se congela (CU-O48)."""

from __future__ import annotations

import json

import pytest

from apps.partners.domain_constants import (
    CAMBIO_ASIGNACION_PLAN,
    ESTADO_PLAN_ASIGNADO,
)
from apps.partners.services.asignar_plan_acceso_service import (
    AsignarPlanAccesoService,
    AsignarPlanError,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]


def _sembrar(limites: dict | None, *, idcliente: int = 901, idplan: int = 901) -> None:
    """Ids altos a proposito: el doble precarga Dim_Plan y Dim_Cliente con ids bajos."""
    PINOT_STORE["Dim_Cliente"].append({"idcliente": idcliente, "nombre": "Demo"})
    PINOT_STORE["Dim_Plan"].append(
        {
            "idplan": idplan,
            "nombre": "Profesional",
            "limites": json.dumps(limites) if limites is not None else "{}",
            "activo": True,
        }
    )
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": 1,
            "idcliente": idcliente,
            "idplan": idplan,
            "estado": "Activa",
            "activo": True,
            "fecha_inicio": 1,
        }
    )


def _partner(idpartner: int = 901, idcliente: int = 901, activo: bool = True) -> None:
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": idpartner,
            "idcliente": idcliente,
            "nombrepartner": "Demo",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "",
            "limitellamadasmes": -1,
            "limitellamadasminuto": -1,
            "sandbox_activado": 0,
            "sandbox_expiracion": 0,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": activo,
            "fecha_actualizacion": 1,
        }
    )


LIMITES_OK = {
    "unidades_max": 25,
    "usuarios_max": 10,
    "api_calls_mes": 10000,
    "api_calls_minuto": 120,
}


class TestAsignacionExitosa:
    def test_asignar_when_plan_completo_congela_el_cupo(self, mock_pinot, mock_kafka):
        # Arrange
        _sembrar(LIMITES_OK)
        _partner()

        # Act
        resultado = AsignarPlanAccesoService().asignar(
            idpartner=901, ejecutado_por="Administrador"
        )

        # Assert — el cupo sale del plan, no del cuerpo de la peticion
        assert resultado["estado"] == ESTADO_PLAN_ASIGNADO
        assert resultado["planapi"] == "Profesional"
        assert resultado["limitellamadasmes"] == 10000
        assert resultado["limitellamadasminuto"] == 120

    def test_asignar_when_plan_cambia_despues_el_partner_conserva_su_cupo(
        self, mock_pinot, mock_kafka
    ):
        """RN-PON-003 — el cupo queda CONGELADO en el partner.

        Es lo que hace reproducible el calculo de excedente de CU-O54: editar el
        catalogo no puede reescribir retroactivamente lo que se factura.
        """
        # Arrange
        _sembrar(LIMITES_OK)
        _partner()
        AsignarPlanAccesoService().asignar(idpartner=901, ejecutado_por="Administrador")

        # Act — el Director de Estrategia recorta el plan despues
        PINOT_STORE["Dim_Plan"][-1]["limites"] = json.dumps(
            {**LIMITES_OK, "api_calls_mes": 50, "api_calls_minuto": 1}
        )

        # Assert — el partner sigue con lo que se le congelo
        partner = PINOT_STORE["Dim_Partner"][-1]
        assert partner["limitellamadasmes"] == 10000
        assert partner["limitellamadasminuto"] == 120

    def test_asignar_when_exitosa_escribe_bitacora(self, mock_pinot, mock_kafka):
        # Arrange
        _sembrar(LIMITES_OK)
        _partner()

        # Act
        AsignarPlanAccesoService().asignar(idpartner=901, ejecutado_por="Administrador")

        # Assert
        eventos = PINOT_STORE["Fact_HistorialAccesoPartner"]
        assert [e["tipo_cambio"] for e in eventos] == [CAMBIO_ASIGNACION_PLAN]
        assert eventos[0]["estado_nuevo"] == ESTADO_PLAN_ASIGNADO


class TestAsignacionRechazada:
    def test_asignar_when_limites_sin_api_calls_minuto_raises_plan_incompleto(
        self, mock_pinot, mock_kafka
    ):
        """Se prefiere fallar visible antes que asumir un cupo.

        Un limite inventado se convertiria en dinero mal cobrado en CU-O54 sin
        que nadie lo note.
        """
        # Arrange — plan al que le falta el limite por minuto
        _sembrar({"unidades_max": 5, "usuarios_max": 3, "api_calls_mes": 1000})
        _partner()

        # Act / Assert
        with pytest.raises(AsignarPlanError) as exc:
            AsignarPlanAccesoService().asignar(idpartner=901, ejecutado_por="Administrador")
        assert exc.value.code == "plan_incompleto"
        assert PINOT_STORE["Fact_HistorialAccesoPartner"] == []

    def test_asignar_when_partner_suspendido_raises_conflicto(self, mock_pinot, mock_kafka):
        """RN-PON-013 — ninguna accion de habilitacion sobre un suspendido."""
        # Arrange
        _sembrar(LIMITES_OK)
        _partner(activo=False)

        # Act / Assert
        with pytest.raises(AsignarPlanError) as exc:
            AsignarPlanAccesoService().asignar(idpartner=901, ejecutado_por="Administrador")
        assert exc.value.code == "partner_suspendido"

    def test_asignar_when_partner_inexistente_raises_not_found(self, mock_pinot, mock_kafka):
        # Act / Assert
        with pytest.raises(AsignarPlanError) as exc:
            AsignarPlanAccesoService().asignar(idpartner=404, ejecutado_por="Administrador")
        assert exc.value.code == "not_found"

    def test_asignar_when_suscripcion_no_vigente_raises(self, mock_pinot, mock_kafka):
        # Arrange — suscripcion suspendida
        _sembrar(LIMITES_OK)
        PINOT_STORE["Fact_Suscripcion"][-1]["estado"] = "Suspendida"
        _partner()

        # Act / Assert
        with pytest.raises(AsignarPlanError) as exc:
            AsignarPlanAccesoService().asignar(idpartner=901, ejecutado_por="Administrador")
        assert exc.value.code == "sin_suscripcion"
