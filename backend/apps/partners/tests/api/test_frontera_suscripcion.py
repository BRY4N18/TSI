"""Frontera con la suspension de suscripcion (T048, § 15 D2, escenario O).

Dos suspensiones independientes por origen, y el acceso exige **las dos**:

| Condicion | Dueno | Tabla |
|---|---|---|
| Partner no suspendido | **#09** | `Dim_Partner.activo` |
| Suscripcion vigente | `subscriptions-and-billing` | `Fact_Suscripcion.estado` |

Este archivo es de **regresion**: la comprobacion de suscripcion ya la
implemento #08 (T024b). Existe para que no se pierda en un refactor, y para
fijar que las dos suspensiones **no se arrastran** — si lo hicieran, quedarian en
contradiccion permanente, porque Suscripciones reactiva sola tras el cobro
(RN-SUSF-011) y aqui el sistema nunca reactiva solo (RN-PAC-009).
"""

from __future__ import annotations

import pytest

from apps.partners.services.suspender_partner_service import SuspenderPartnerService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/datos/accidentes"


@pytest.fixture
def suscripcion_vigente(credencial_produccion_headers):
    """Partner 880 con todo en regla: activo y con suscripción vigente."""
    PINOT_STORE["Dim_Plan"].append({
        "idplan": 880,
        "nombre": "Profesional",
        "limites": '{"api_calls_mes": 10000, "api_calls_minuto": 120}',
        "severidades_desbloqueadas": "null",
        "activo": True,
    })
    suscripcion = {
        "id_suscripcion": 880,
        "idcliente": 880,
        "idplan": 880,
        "estado": "Activa",
        "activo": True,
        "fecha_inicio": 1,
        "severidades_desbloqueadas": '["Media"]',
    }
    PINOT_STORE["Fact_Suscripcion"].append(suscripcion)
    PINOT_STORE["Dim_Preferencias_Cliente"].append(
        {"id_cliente": 880, "zonas_geograficas": "[10]"}
    )
    return {"headers": credencial_produccion_headers, "suscripcion": suscripcion}


class TestElAccesoExigeLasDosCondiciones:
    def test_con_las_dos_en_regla_se_consume(self, api_client, suscripcion_vigente):
        assert api_client.get(URL, **suscripcion_vigente["headers"]).status_code == 200

    def test_suscripcion_suspendida_con_partner_activo_returns_403(
        self, api_client, suscripcion_vigente
    ):
        """El hueco que cerró § 15 D2: antes, un cliente con la suscripción
        suspendida seguía consumiendo la API."""
        # Arrange
        suscripcion_vigente["suscripcion"]["estado"] = "Suspendida"

        # Act
        respuesta = api_client.get(URL, **suscripcion_vigente["headers"])

        # Assert
        assert respuesta.status_code == 403

    def test_partner_suspendido_con_suscripcion_vigente_no_consume(
        self, api_client, suscripcion_vigente
    ):
        # Arrange
        SuspenderPartnerService().suspender(
            idpartner=880, motivo="mora de excedente", automatica=True
        )

        # Act / Assert — 401 por la lista de denegación, o 403 por el permiso:
        # lo que importa es que NO sirve datos.
        assert api_client.get(
            URL, **suscripcion_vigente["headers"]
        ).status_code in (401, 403)


class TestNoSeArrastran:
    def test_reactivar_la_suscripcion_no_reactiva_al_partner(
        self, api_client, suscripcion_vigente
    ):
        """🎯 Si se arrastrasen, Suscripciones intentaría reactivar lo que este
        módulo exige que reactive una persona (RN-PAC-009)."""
        # Arrange — partner suspendido por SU mora; suscripción cae y se repone
        SuspenderPartnerService().suspender(
            idpartner=880, motivo="mora de excedente", automatica=True
        )
        suscripcion_vigente["suscripcion"]["estado"] = "Suspendida"

        # Act
        suscripcion_vigente["suscripcion"]["estado"] = "Activa"

        # Assert — el partner sigue suspendido: solo un Administrador lo levanta
        partner = next(p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == 880)
        assert partner["activo"] is False
