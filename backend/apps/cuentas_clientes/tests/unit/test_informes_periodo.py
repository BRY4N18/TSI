"""T007 — el periodo de los listados, cuyo rango es opcional (research D1).

Es la diferencia deliberada con `apps/informes_tacticos/periodo.py`, que lo
exige. Estas pruebas fijan que la diferencia existe y se comporta como el
contrato dice, no como la copia de la que salio.
"""

from __future__ import annotations

import pytest

from core.informes.periodo import PeriodoInvalido, parse_periodo


class TestRangoOpcional:
    def test_sin_rango_es_valido(self):
        periodo = parse_periodo({})

        assert periodo.vacio
        assert periodo.desde_ms is None
        assert periodo.hasta_ms is None

    def test_sin_rango_no_aporta_filtros_a_meta(self):
        # Un extremo ausente no es un filtro con valor nulo: no esta.
        assert parse_periodo({}).to_meta() == {}

    def test_solo_desde_es_valido(self):
        periodo = parse_periodo({"desde": "2026-01-01"})

        assert periodo.desde_ms is not None
        assert periodo.hasta_ms is None
        assert periodo.to_meta() == {"desde": "2026-01-01"}

    def test_solo_hasta_es_valido(self):
        periodo = parse_periodo({"hasta": "2026-01-31"})

        assert periodo.desde_ms is None
        assert periodo.hasta_ms is not None


class TestHastaEsInclusiva:
    def test_hasta_llega_al_ultimo_milisegundo_del_dia(self):
        periodo = parse_periodo({"desde": "2026-01-01", "hasta": "2026-01-01"})

        # 2026-01-01T00:00:00Z .. 2026-01-01T23:59:59.999Z — un dia completo.
        assert periodo.hasta_ms - periodo.desde_ms == 86_400_000 - 1

    def test_un_hecho_del_ultimo_dia_cae_dentro_del_rango(self):
        # Si 'hasta' fuera exclusiva, los hechos del dia 14 no saldrian y nadie
        # lo notaria hasta cuadrar cifras contra otra fuente.
        periodo = parse_periodo({"desde": "2026-08-01", "hasta": "2026-08-14"})
        ultimo_instante_del_14 = 1_786_751_999_999  # 2026-08-14T23:59:59.999Z

        assert periodo.desde_ms <= ultimo_instante_del_14 <= periodo.hasta_ms


class TestRechazos:
    def test_rango_invertido_falla(self):
        with pytest.raises(PeriodoInvalido, match="posterior"):
            parse_periodo({"desde": "2026-02-01", "hasta": "2026-01-01"})

    @pytest.mark.parametrize("valor", ["01-01-2026", "2026/01/01", "ayer", "2026-13-01"])
    def test_formato_no_iso_falla_nombrando_el_parametro(self, valor):
        with pytest.raises(PeriodoInvalido, match="desde"):
            parse_periodo({"desde": valor})

    def test_granularidad_se_rechaza_no_se_ignora(self):
        # Aceptarla en silencio prometeria un truncado por mes que nadie hace.
        with pytest.raises(PeriodoInvalido, match="granularidad"):
            parse_periodo({"granularidad": "mes"})


class TestListadosDeEstadoActual:
    """`admite_rango=False`: declarar un extremo es 400, no se ignora (FR-012)."""

    def test_sin_rango_es_valido(self):
        assert parse_periodo({}, admite_rango=False).vacio

    @pytest.mark.parametrize("param", ["desde", "hasta"])
    def test_declarar_un_extremo_falla_nombrandolo(self, param):
        with pytest.raises(PeriodoInvalido, match=param):
            parse_periodo({param: "2026-01-01"}, admite_rango=False)

    def test_declarar_ambos_los_nombra_a_los_dos(self):
        with pytest.raises(PeriodoInvalido) as exc:
            parse_periodo(
                {"desde": "2026-01-01", "hasta": "2026-01-31"}, admite_rango=False
            )

        assert "desde" in str(exc.value) and "hasta" in str(exc.value)


def test_no_importa_el_periodo_de_los_informes_agregados():
    """research D1 — los 19 informes en produccion no se tocan.

    Si algun dia este modulo empezara a importar el de la app, la duplicacion
    consciente se habria deshecho sin que nadie lo decidiera, y un cambio aqui
    volveria a alcanzar a esos 19 endpoints.
    """
    import inspect

    import core.informes.periodo as modulo

    assert "apps.informes_tacticos" not in inspect.getsource(modulo)
