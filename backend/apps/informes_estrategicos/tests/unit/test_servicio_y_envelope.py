"""Cobertura del envelope y del servicio con el repositorio simulado."""

from datetime import date
from unittest.mock import MagicMock

from apps.informes_estrategicos.envelope import informe_estrategico_response
from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from apps.informes_estrategicos.services.oe6_service import Oe6Service


def _periodo():
    return PeriodoEstrategico(
        date(2026, 4, 1), date(2026, 6, 30), "trimestre", parcial=False
    )


class TestEnvelope:
    def test_no_emite_acotado_a(self):
        periodo = _periodo()
        respuesta = informe_estrategico_response([], periodo, cobertura="completa")
        assert "acotado_a" not in respuesta.data["meta"]

    def test_declara_periodo_y_cobertura(self):
        meta = informe_estrategico_response([], _periodo()).data["meta"]
        assert meta["periodo"]["granularidad"] == "trimestre"
        assert meta["periodo"]["parcial"] is False
        assert meta["cobertura"] == "completa"


class TestServicioConRepositorioSimulado:
    def test_yoy_sin_filas_anteriores_declara_ausencia(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [{"periodo": "2026-04", "casos_con_llegada": 10}],
            [],
        )
        resultado = Oe6Service(repo).calcular(
            "tiempo-respuesta-global",
            _periodo(),
            comparacion="yoy",
            extra={"muestra_minima": 5, "por_condado": 0},
        )
        assert resultado.comparacion["ventana_anterior"] is None
        assert resultado.comparacion["motivo_ausencia"]
        assert resultado.comparacion["variacion"] is None

    def test_mom_con_datos_declara_dos_ventanas_de_igual_longitud(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [{"periodo": "2026-04", "casos_con_llegada": 10}],
            [{"periodo": "2026-01", "casos_con_llegada": 8}],
        )
        resultado = Oe6Service(repo).calcular(
            "tiempo-respuesta-global",
            _periodo(),
            comparacion="mom",
            extra={"muestra_minima": 5, "por_condado": 0},
        )
        actual = resultado.comparacion["ventana_actual"]
        anterior = resultado.comparacion["ventana_anterior"]
        d_act = date.fromisoformat(actual["hasta"]) - date.fromisoformat(actual["desde"])
        d_ant = date.fromisoformat(anterior["hasta"]) - date.fromisoformat(anterior["desde"])
        assert d_act == d_ant
        assert resultado.comparacion["variacion"]["casos_con_llegada"] == 2

    def test_cierres_forzados_siempre_parcial(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = (
            [{"periodo": "2026-04", "forzados": 1, "despachos_confirmados": 100}],
            None,
        )
        resultado = Oe6Service(repo).calcular("cierres-forzados", _periodo())
        assert resultado.cobertura == "parcial"
        assert "retiro manual desde central" in resultado.falta
        assert resultado.alcance

    def test_objetivo_calibrar_en_todos(self):
        repo = MagicMock()
        repo.ejecutar_con_comparacion.return_value = ([], None)
        resultado = Oe6Service(repo).calcular(
            "tiempo-respuesta-global",
            _periodo(),
            extra={"muestra_minima": 5, "por_condado": 0},
        )
        assert resultado.objetivo["tipo"] == "CALIBRAR"
        assert resultado.objetivo["cumple"] is None
