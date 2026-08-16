"""T022 — el motivo de cancelación solo aparece en las canceladas.

Una suscripción activa no tiene motivo de cancelación porque no se canceló.
Devolver el campo —aunque fuera `null`— sugeriría que la pregunta tiene sentido
para ella, y en un listado que alimenta análisis de bajas eso invita a contar
como «sin motivo declarado» lo que en realidad es «no dada de baja».
"""

from __future__ import annotations

import pytest

from apps.suscripciones.services.informes_suscripcion_service import (
    InformesSuscripcionService,
)
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)


@pytest.fixture
def servicio(mock_pinot):
    return InformesSuscripcionService()


def _por_estado(pagina, estado):
    return [f for f in pagina.filas if f["estado"] == estado]


class TestLaCancelada:
    def test_devuelve_su_motivo(self, servicio, dos_cuentas):
        pagina = servicio.suscripciones(acotamiento=SIN_ACOTAR, limit=500)

        cancelada = _por_estado(pagina, "Cancelada")[0]
        assert cancelada["motivo_cancelacion"] == "precio"

    def test_y_su_fecha(self, servicio, dos_cuentas):
        pagina = servicio.suscripciones(acotamiento=SIN_ACOTAR, limit=500)

        cancelada = _por_estado(pagina, "Cancelada")[0]
        assert cancelada["fecha_cancelacion"] is not None


class TestLasDemas:
    @pytest.mark.parametrize("estado", ["Activa", "Suspendida"])
    def test_no_traen_el_motivo(self, servicio, dos_cuentas, estado):
        pagina = servicio.suscripciones(acotamiento=SIN_ACOTAR, limit=500)

        for fila in _por_estado(pagina, estado):
            assert "motivo_cancelacion" not in fila

    @pytest.mark.parametrize("estado", ["Activa", "Suspendida"])
    def test_ni_la_fecha(self, servicio, dos_cuentas, estado):
        pagina = servicio.suscripciones(acotamiento=SIN_ACOTAR, limit=500)

        for fila in _por_estado(pagina, estado):
            assert "fecha_cancelacion" not in fila


class TestUnaCanceladaSinMotivo:
    def test_devuelve_el_campo_como_ausente_sin_omitir_la_fila(
        self, mock_pinot, cuentas_y_planes
    ):
        """El motivo puede faltar; la baja sigue siendo un hecho."""
        from conftest import PINOT_STORE
        from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A, PLAN_BASICO

        PINOT_STORE["Fact_Suscripcion"].append(
            {
                "id_suscripcion": 7099, "idcliente": CUENTA_A, "idplan": PLAN_BASICO,
                "idplan_programado": 0, "estado": "Cancelada", "activo": False,
                "renovacionautomatica": False, "motivocancelacion": None,
                "periodicidad": "mensual", "nivel": "1", "precio": 100.0,
                "fecha_inicio": AHORA_MS, "fecha_fin": AHORA_MS,
                "fechacancelacion": AHORA_MS, "fecha_actualizacion": AHORA_MS,
            }
        )

        pagina = InformesSuscripcionService().suscripciones(
            acotamiento=SIN_ACOTAR, limit=500
        )
        sin_motivo = [
            f for f in _por_estado(pagina, "Cancelada")
            if f["motivo_cancelacion"] is None
        ]

        assert len(sin_motivo) == 1
        assert sin_motivo[0]["fecha_cancelacion"] is not None
