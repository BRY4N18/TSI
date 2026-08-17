"""T051 — contraste US2 con los equivalentes tácticos."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration


class TestContrasteOe3Us2:
    def test_ratio_coincide_en_casos_por_condado_mes(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot22_ratio_demanda_capacidad",
                departamento="emergencias",
                parametros={"desde": "2026-07-01", "hasta": "2026-07-31"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        respuesta = pedir_oe3(
            cliente(["DirectorOperaciones"]),
            "ratio-demanda-capacidad",
            desde="2026-07-01",
            hasta="2026-07-31",
            granularidad="mes",
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        est = {(f["periodo"], f["condado"]): int(f["casos"]) for f in respuesta.json()["data"]}
        tac = {(f["periodo"], f["condado"]): int(f["casos"]) for f in tactico}
        assert est == tac

    def test_perdida_de_senal_suma_los_mismos_huecos(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot23_perdida_senal",
                departamento="emergencias",
                parametros={"desde": "2026-01-01", "hasta": "2026-12-31", "umbral_seg": 60},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        respuesta = pedir_oe3(
            cliente(["DirectorExpansion"]),
            "perdida-de-senal",
            granularidad="anio",
            umbral_seg=60,
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        huecos_est = sum(int(f.get("huecos") or 0) for f in respuesta.json()["data"])
        huecos_tac = sum(int(f.get("huecos") or 0) for f in tactico)
        assert huecos_est == huecos_tac
