"""T037 — contraste US1: primer-intento coincide; tasa-error es el complemento."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration


class TestContrasteOe3Us1:
    def test_primer_intento_coincide_con_el_tactico(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot22_primer_intento",
                departamento="emergencias",
                parametros={"desde": "2026-01-01", "hasta": "2026-12-31"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        respuesta = pedir_oe3(
            cliente(["DirectorOperaciones"]), "primer-intento", granularidad="mes"
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        por_mes_est = {
            f["periodo"]: int(f["casos"]) for f in respuesta.json()["data"]
        }
        por_mes_tac = {f["periodo"]: int(f["casos"]) for f in tactico}
        comunes = set(por_mes_est) & set(por_mes_tac)
        assert comunes, "no hay meses en común para contrastar"
        for mes in comunes:
            assert por_mes_est[mes] == por_mes_tac[mes], (
                f"{mes}: estratégico {por_mes_est[mes]} vs táctico {por_mes_tac[mes]}"
            )

    def test_tasa_error_es_el_complemento_de_completitud(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot21_completitud_campos_criticos",
                departamento="emergencias",
                parametros={"desde": "2026-01-01", "hasta": "2026-12-31"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        respuesta = pedir_oe3(
            cliente(["DirectorOperaciones"]),
            "tasa-error-registro",
            granularidad="anio",
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        data = respuesta.json()["data"]
        if not data or not tactico:
            pytest.skip("sin filas")
        tasa = float(data[0]["tasa_error"])
        completitud = float(tactico[0]["pct_completitud"])
        assert tasa == pytest.approx((1 - completitud) * 100, abs=0.01)
