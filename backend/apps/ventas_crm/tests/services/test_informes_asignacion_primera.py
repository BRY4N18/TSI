"""T027 — la primera asignación se devuelve con el responsable anterior **ausente**.

No es un caso raro: **toda la cartera pasó por ahí**. Un prospecto que se crea y
se asigna por primera vez no venía de nadie.

Por qué `null` y no `0` ni cadena vacía
---------------------------------------
Un `0` crearía un ejecutivo fantasma. En un listado de *movimientos de cartera*,
«pasó del usuario 0 a Lucía» se lee como un traspaso que nunca ocurrió — el
informe inventaría un movimiento. Y una cadena vacía es peor todavía, porque
sobrevive a cualquier comprobación de presencia y se imprime como un nombre en
blanco (research D7).
"""

from __future__ import annotations

import pytest

from apps.ventas_crm.services.informes_asignacion_service import (
    InformesAsignacionService,
)


@pytest.fixture
def servicio(mock_pinot):
    return InformesAsignacionService()


class TestPrimeraAsignacion:
    def test_el_responsable_anterior_es_none(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        primera = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert primera["ejecutivo_anterior"] is None

    def test_no_es_cero(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        primera = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert primera["ejecutivo_anterior"] != 0
        assert primera["ejecutivo_anterior"] != "0"

    def test_no_es_cadena_vacia(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        primera = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert primera["ejecutivo_anterior"] != ""

    def test_la_clave_esta_presente(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        primera = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert "ejecutivo_anterior" in primera

    def test_la_fila_no_se_omite(self, servicio, asignaciones_sembradas):
        # Omitirla escondería el alta de cada prospecto de la cartera.
        pagina = servicio.reasignaciones(limit=500)

        assert any(f["empresa"] == "Alfa Seguros" for f in pagina.filas)

    def test_el_ejecutivo_nuevo_si_resuelve(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        primera = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert primera["ejecutivo_nuevo"] == "Lucia Ramos"


class TestReasignacionReal:
    """El contraste: una con responsable anterior sí lo trae."""

    def test_los_dos_extremos_resuelven(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Delta Transportes")
        assert fila["ejecutivo_anterior"] == "Lucia Ramos"
        assert fila["ejecutivo_nuevo"] == "Pablo Andrade"

    def test_trae_su_motivo(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Delta Transportes")
        assert fila["motivo"] == "reparto de cartera"

    def test_una_primera_asignacion_no_tiene_motivo_y_eso_es_valido(
        self, servicio, asignaciones_sembradas
    ):
        pagina = servicio.reasignaciones(limit=500)

        primera = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert primera["motivo"] is None


class TestFormaDeLaFila:
    def test_no_expone_identificadores(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        for fila in pagina.filas:
            assert "idasignacion" not in fila
            assert "idprospecto" not in fila
            assert "idusuariogerenteanterior" not in fila

    def test_resuelve_la_empresa_del_prospecto(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        assert all(f["empresa"] for f in pagina.filas)

    def test_la_fecha_llega_en_iso(self, servicio, asignaciones_sembradas):
        pagina = servicio.reasignaciones(limit=500)

        assert all(f["fecha"].endswith("+00:00") for f in pagina.filas)
