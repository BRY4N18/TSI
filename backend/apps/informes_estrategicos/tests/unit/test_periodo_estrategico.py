"""T022 — período obligatorio, ventanas de igual longitud, parcial."""

from datetime import date, timedelta

import pytest

from apps.informes_estrategicos.periodo_estrategico import (
    PeriodoEstrategicoInvalido,
    parse_comparacion,
    parse_periodo_estrategico,
)


class TestParametrosObligatorios:
    def test_falta_desde_lo_nombra(self):
        with pytest.raises(PeriodoEstrategicoInvalido, match="'desde'"):
            parse_periodo_estrategico({"hasta": "2026-03-31", "granularidad": "mes"})

    def test_falta_hasta_lo_nombra(self):
        with pytest.raises(PeriodoEstrategicoInvalido, match="'hasta'"):
            parse_periodo_estrategico({"desde": "2026-01-01", "granularidad": "mes"})

    def test_falta_granularidad_la_nombra(self):
        with pytest.raises(PeriodoEstrategicoInvalido, match="'granularidad'"):
            parse_periodo_estrategico({"desde": "2026-01-01", "hasta": "2026-03-31"})

    def test_granularidad_desconocida_lista_las_validas(self):
        with pytest.raises(PeriodoEstrategicoInvalido, match="mes") as exc:
            parse_periodo_estrategico({
                "desde": "2026-01-01",
                "hasta": "2026-03-31",
                "granularidad": "semana",
            })
        assert "trimestre" in str(exc.value)
        assert "anio" in str(exc.value)


class TestVentanasDeIgualLongitud:
    def test_mom_conserva_la_longitud(self):
        periodo = parse_periodo_estrategico({
            "desde": "2026-07-01",
            "hasta": "2026-09-30",
            "granularidad": "trimestre",
        })
        anterior = periodo.ventana_anterior("mom")

        assert anterior.longitud_dias == periodo.longitud_dias
        assert anterior.hasta == date(2026, 6, 30)
        # Jul–Sep tiene 92 días; el trimestre civil anterior (Abr–Jun) tiene 91.
        # Se conserva la longitud, no el calendario: 31 mar – 30 jun.
        assert anterior.desde == date(2026, 3, 31)

    def test_yoy_conserva_la_longitud(self):
        periodo = parse_periodo_estrategico({
            "desde": "2026-07-01",
            "hasta": "2026-09-30",
            "granularidad": "trimestre",
        })
        anterior = periodo.ventana_anterior("yoy")

        assert anterior.longitud_dias == periodo.longitud_dias
        assert anterior.desde.year == 2025


class TestParcial:
    def test_periodo_en_curso_es_parcial(self):
        hoy = date(2026, 8, 16)
        periodo = parse_periodo_estrategico(
            {
                "desde": "2026-07-01",
                "hasta": "2026-09-30",
                "granularidad": "trimestre",
            },
            hoy=hoy,
        )
        assert periodo.parcial is True

    def test_periodo_cerrado_no_es_parcial(self):
        periodo = parse_periodo_estrategico(
            {
                "desde": "2026-04-01",
                "hasta": "2026-06-30",
                "granularidad": "trimestre",
            },
            hoy=date(2026, 8, 16),
        )
        assert periodo.parcial is False

    def test_comparacion_por_defecto_es_ninguna(self):
        assert parse_comparacion({}) == "ninguna"
