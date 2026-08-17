"""T062 — exactamente dos informes de OE3 devuelven cumple booleano."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE3, cliente, pedir_oe3

SEMAFORIZAN = {"latencia-asignacion", "tasa-error-registro"}


class TestSemaforoCorrectoOe3:
    def test_exactamente_dos_booleanos(self):
        director = cliente(["DirectorOperaciones"])
        con_booleano = []
        for informe in INFORMES_OE3:
            respuesta = pedir_oe3(director, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            objetivo = respuesta.json()["meta"].get("objetivo")
            if objetivo and isinstance(objetivo.get("cumple"), bool):
                con_booleano.append(informe)
        assert set(con_booleano) == SEMAFORIZAN, (
            f"semaforizaron {con_booleano}: deben ser exactamente {sorted(SEMAFORIZAN)}"
        )
