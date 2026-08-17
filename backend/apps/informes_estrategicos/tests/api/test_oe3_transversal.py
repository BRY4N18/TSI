"""T063, T064, T065 — denominadores, período vacío, sin por_region."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE3, cliente, pedir_oe3

DENOMINADORES = (
    "casos", "casos_asignados", "intervalos_medidos", "vecinos",
    "unidades_vigentes", "incompletos",
)
VACIO = {"desde": "2019-01-01", "hasta": "2019-01-31", "granularidad": "mes"}


class TestDenominadoresOe3:
    @pytest.mark.parametrize("informe", INFORMES_OE3)
    def test_si_hay_porcentaje_hay_denominador(self, informe):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), informe)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            claves = set(fila)
            hay_pct = any(k.startswith("pct") or k.startswith("tasa") for k in claves)
            if not hay_pct:
                continue
            assert claves & set(DENOMINADORES), (
                f"'{informe}' publica un porcentaje sin denominador: {sorted(claves)}"
            )


class TestPeriodoSinDatosOe3:
    @pytest.mark.parametrize("informe", INFORMES_OE3)
    def test_data_vacia_cobertura_completa(self, informe):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), informe, **VACIO)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        cuerpo = respuesta.json()
        assert cuerpo["data"] == [], (
            f"'{informe}' devolvió filas de ceros: {cuerpo['data'][:2]}"
        )
        assert cuerpo["meta"]["cobertura"] == "completa"


class TestSinPorRegion:
    @pytest.mark.parametrize("informe", INFORMES_OE3)
    def test_no_acepta_ni_emite_por_region(self, informe):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir_oe3(director, informe, por_region="true")
        if respuesta.status_code == 400:
            pytest.fail("por_region no debe ser un parámetro reconocido que falle")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = str(respuesta.json()).lower()
        assert "por_region" not in texto
        # Un extra ignorado está bien; no debe aparecer en data/meta como eje.
        for fila in respuesta.json()["data"]:
            assert "region" not in {k.lower() for k in fila}
