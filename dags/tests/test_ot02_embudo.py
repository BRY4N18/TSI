"""T031 — el embudo cuadra, con los retrocesos contados como transicion (SC-003)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    ID_PROSPECTO_PRUEBA,
    asegurar_hechos_ventas_crm,
    ejecutar_ventas_crm,
    insertar,
    limpiar_ventas_crm,
    prospecto_de_prueba,
    requiere_modelo,
)


def _tr(idt, idp, nueva, *, anterior, avance=1):
    return {
        "idtransicion": idt,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
        "idprospecto": idp,
        "empresa": "Empresa prueba",
        "canal": "Web",
        "tipo_organizacion": "Privada",
        "etapa_anterior": anterior,
        "etapa_nueva": nueva,
        "es_avance": avance,
        "es_terminal": 0,
        "motivo_perdida": None,
        "segundos_en_etapa_anterior": 60,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    p1, p2, p3 = ID_PROSPECTO_PRUEBA + 1, ID_PROSPECTO_PRUEBA + 2, ID_PROSPECTO_PRUEBA + 3
    insertar("dim_prospecto", [
        prospecto_de_prueba(p1, etapa_actual="Calificado"),
        prospecto_de_prueba(p2, etapa_actual="Contactado"),
        prospecto_de_prueba(p3, etapa_actual="Contactado"),
    ])
    insertar("hecho_transicion_embudo", [
        _tr(1, p1, "Contactado", anterior="Nuevo"),
        _tr(2, p1, "Calificado", anterior="Contactado"),
        _tr(3, p2, "Contactado", anterior="Nuevo"),
        _tr(4, p3, "Contactado", anterior="Calificado", avance=0),
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestElEmbudoCuadra:
    def test_el_retroceso_cuenta_como_transicion(self, escenario):
        filas = ejecutar_ventas_crm("ot02_embudo_conversion")
        retroceso = [
            f for f in filas
            if f["etapa_anterior"] == "Calificado" and f["etapa_nueva"] == "Contactado"
        ]
        assert retroceso, "el retroceso desaparecio: el embudo se midio sobre prospectos unicos"

    def test_pct_por_denominador_reproduce_el_conteo(self, escenario):
        filas = ejecutar_ventas_crm("ot02_embudo_conversion")
        for fila in filas:
            assert fila["denominador"] > 0
            reconstruido = round(fila["pct_paso"] * fila["denominador"])
            assert reconstruido == fila["transiciones"], (
                f"{fila}: pct_paso * denominador no reproduce transiciones; "
                f"el porcentaje no se calculo sobre transiciones"
            )

    def test_salen_mas_permanecen_igualan_a_quienes_entraron_a_contactado(self, escenario):
        """Entran a Contactado = salen de Contactado + se quedan *en el periodo*.

        Tres entran (dos desde Nuevo, uno por retroceso). Uno sale a Calificado.
        Quedan dos. 3 = 1 + 2.

        No se cruza con `abiertos` de permanencia: ese informe es un corte sobre
        `dim_prospecto` y cuenta tambien a quien ya estaba en Contactado antes
        del periodo (los del origen, registrados en 2026).
        """
        filas = ejecutar_ventas_crm("ot02_embudo_conversion")
        hacia = sum(
            f["transiciones"] for f in filas if f["etapa_nueva"] == "Contactado"
        )
        desde = sum(
            f["transiciones"] for f in filas if f["etapa_anterior"] == "Contactado"
        )
        assert hacia == 3
        assert desde == 1
        assert hacia - desde == 2
