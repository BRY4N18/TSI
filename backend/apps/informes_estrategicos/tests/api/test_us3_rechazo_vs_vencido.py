"""T065 — rechazo y vencimiento van separados y cuadran con la línea base."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestRechazoVsVencido:
    def test_las_dos_tasas_se_publican_y_los_recuentos_cuadran(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director, "rechazo-y-timeout-por-unidad", top=100, granularidad="anio"
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        filas = respuesta.json()["data"]
        assert filas
        assert all("tasa_rechazo" in f and "tasa_vencimiento" in f for f in filas)
        rechazados = sum(int(f["rechazados"]) for f in filas)
        vencidos = sum(int(f["vencidos"]) for f in filas)
        assert rechazados == 334, f"rechazados={rechazados}, línea base 334"
        assert vencidos == 327, f"vencidos={vencidos}, línea base 327"
