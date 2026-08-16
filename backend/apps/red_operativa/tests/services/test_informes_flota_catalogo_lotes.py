"""T023 y T022 — la geografía se resuelve por lotes, y la unidad sin condado aparece.

**Un número fijo de consultas por página, independiente del número de filas**
(research D3). Con una consulta por fila, una flota de 500 unidades cuesta 500
consultas y el objetivo de 2 s deja de ser alcanzable.

El defecto no se nota con datos de prueba: con diez unidades las dos
implementaciones parecen igual de rápidas. Por eso esta prueba **cuenta
consultas** en vez de medir tiempo, y compara dos tamaños de página muy
distintos.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.red_operativa.services.informes_flota_service import InformesFlotaService
from apps.red_operativa.tests.conftest import CONDADO, PROVEEDOR_A, _unidad
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)


def _contar_consultas(fn):
    """Cuenta las consultas a Pinot que hace `fn()`."""
    from conftest import _pinot_query_impl

    contador = {"n": 0}

    def contando(self, sql, params=None):
        contador["n"] += 1
        return _pinot_query_impl(sql, params)

    with patch("core.pinot.client.PinotClient.query", contando):
        fn()
    return contador["n"]


@pytest.fixture
def flota_grande(mock_pinot, geografia_y_proveedores):
    """Cien unidades del mismo proveedor y condado.

    Cien y no diez: es el volumen en el que una consulta por fila se distingue
    de una por página.
    """
    from conftest import PINOT_STORE

    for i in range(100):
        PINOT_STORE["Dim_UnidadEmergencia"].append(
            _unidad(5300 + i, placa=f"LOTE-{i:03d}", idcliente=PROVEEDOR_A)
        )


@pytest.fixture
def servicio(mock_pinot):
    return InformesFlotaService()


class TestElCosteNoCreceConLasFilas:
    def test_una_pagina_de_100_cuesta_lo_mismo_que_una_de_5(
        self, servicio, flota_grande
    ):
        pocas = _contar_consultas(
            lambda: servicio.flota(acotamiento=SIN_ACOTAR, limit=5)
        )
        muchas = _contar_consultas(
            lambda: servicio.flota(acotamiento=SIN_ACOTAR, limit=100)
        )

        assert muchas == pocas, (
            f"100 filas cuestan {muchas} consultas y 5 cuestan {pocas}: "
            "la geografia se esta resolviendo fila a fila"
        )

    def test_son_cuatro_consultas_en_total(self, servicio, flota_grande):
        """Unidades, condados, estados y proveedores. Ni una más."""
        consultas = _contar_consultas(
            lambda: servicio.flota(acotamiento=SIN_ACOTAR, limit=100)
        )

        assert consultas == 4

    def test_una_pagina_vacia_no_consulta_catalogos(self, servicio, flota_grande):
        # Sin filas no hay geografía que resolver: solo la consulta principal.
        consultas = _contar_consultas(
            lambda: servicio.flota(acotamiento=SIN_ACOTAR, limit=50, idcondado=999999)
        )

        assert consultas == 1

    def test_la_geografia_llega_resuelta(self, servicio, flota_grande):
        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=100)

        assert all(f["condado"] == "Canton Central" for f in pagina.filas)
        assert all(f["estado_geografico"] == "Provincia Norte" for f in pagina.filas)


class TestUnidadSinCondado:
    """T022 — aparece con la ubicación ausente, **no se omite** (FR-023)."""

    def test_aparece_en_el_listado(self, servicio, dos_flotas, unidad_sin_condado):
        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=500)

        assert "SINCOND-01" in {f["placa"] for f in pagina.filas}

    def test_su_ubicacion_se_marca_como_ausente(
        self, servicio, dos_flotas, unidad_sin_condado
    ):
        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["placa"] == "SINCOND-01")
        # Sin condado no puede ser candidata en un despacho: es justo la
        # anomalía que la supervisión busca, y ocultarla la escondería.
        assert fila["condado"] is None
        assert fila["estado_geografico"] is None

    def test_las_claves_estan_presentes(self, servicio, dos_flotas, unidad_sin_condado):
        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["placa"] == "SINCOND-01")
        assert "condado" in fila and "estado_geografico" in fila

    def test_el_resto_de_la_fila_llega_completo(
        self, servicio, dos_flotas, unidad_sin_condado
    ):
        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["placa"] == "SINCOND-01")
        assert fila["tipo_unidad"] and fila["proveedor"]

    def test_no_rompe_la_resolucion_de_las_demas(
        self, servicio, dos_flotas, unidad_sin_condado
    ):
        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=500)

        con_condado = [f for f in pagina.filas if f["placa"] == "GRUA-01"]
        assert con_condado[0]["condado"] == "Canton Central"


class TestUnCondadoSinEstado:
    def test_conserva_su_propio_nombre(self, servicio, mock_pinot, geografia_y_proveedores):
        """Media ubicación es más útil que ninguna."""
        from conftest import PINOT_STORE

        PINOT_STORE["Dim_Condado"].append(
            {"idcondado": 5799, "condado": "Canton Huerfano", "idestado": 999999,
             "activo": True, "fecha_actualizacion": 0}
        )
        PINOT_STORE["Dim_UnidadEmergencia"].append(
            _unidad(5399, placa="HUERF-01", idcliente=PROVEEDOR_A, idcondado=5799)
        )

        pagina = servicio.flota(acotamiento=SIN_ACOTAR, limit=500)
        fila = next(f for f in pagina.filas if f["placa"] == "HUERF-01")

        assert fila["condado"] == "Canton Huerfano"
        assert fila["estado_geografico"] is None
