"""T030 — solo se devuelven métodos de pago **vigentes** (FR-007).

Reemplazar un método desactiva el anterior sin borrarlo, así que el registro del
retirado sigue existiendo. El filtro `activo = true` es lo que distingue el
medio de cobro **real** de su historial.

Sin él, el listado mostraría tarjetas retiradas como si aún se pudieran cobrar
—y en un informe cuyo propósito es prevenir el cobro fallido, eso es justo lo
contrario de lo que se pide.
"""

from __future__ import annotations

import pytest

from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A, DIA_MS
from core.repositories.suscripciones.informes_facturacion_repository import (
    InformesFacturacionRepository,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesFacturacionRepository()


class TestSoloVigentes:
    def test_el_reemplazado_no_aparece(self, repo, metodos_pago_sembrados):
        filas = repo.metodos_de_pago(limit=500, cuenta=CUENTA_A)

        assert 7602 not in {f["idmetodopago"] for f in filas}

    def test_el_vigente_si(self, repo, metodos_pago_sembrados):
        filas = repo.metodos_de_pago(limit=500, cuenta=CUENTA_A)

        assert [f["idmetodopago"] for f in filas] == [7601]

    def test_el_reemplazado_sigue_existiendo_en_la_tabla(
        self, repo, metodos_pago_sembrados
    ):
        """Si no existiera, la prueba de arriba no demostraría nada."""
        from conftest import PINOT_STORE

        retirado = [m for m in PINOT_STORE["Dim_MetodoPago"] if m["idmetodopago"] == 7602]
        assert retirado and retirado[0]["activo"] is False

    def test_el_filtro_esta_en_la_consulta_no_en_python(self):
        # Filtrar después de paginar devolvería páginas incompletas: el `LIMIT`
        # ya habría recortado antes de descartar el retirado.
        import inspect

        from core.repositories.suscripciones import informes_facturacion_repository

        fuente = inspect.getsource(
            informes_facturacion_repository.InformesFacturacionRepository.metodos_de_pago
        )
        assert 'condiciones = ["activo = true"]' in fuente


class TestFiltroDeCaducidad:
    def test_acota_por_fecha_de_corte(self, repo, metodos_pago_sembrados):
        # El de la cuenta A caduca en 10 días; el de la B, en 200.
        filas = repo.metodos_de_pago(
            limit=500, caduca_antes_de=AHORA_MS + 30 * DIA_MS
        )

        assert {f["idmetodopago"] for f in filas} == {7601}

    def test_un_corte_amplio_los_incluye_a_los_dos(self, repo, metodos_pago_sembrados):
        filas = repo.metodos_de_pago(
            limit=500, caduca_antes_de=AHORA_MS + 365 * DIA_MS
        )

        assert {7601, 7603} <= {f["idmetodopago"] for f in filas}

    def test_la_comparacion_va_entera_a_la_base(self):
        """research D5 — la columna es `LONG`, no texto.

        En Ventas y CRM la columna equivalente era texto con formatos mixtos y
        obligó a un filtro en dos pasos. Aquí no hace falta, y comprobar el tipo
        antes de diseñar es lo que evitó arrastrar esa complejidad.
        """
        import json

        esquemas = json.load(
            open("../database/esquemas.json", encoding="utf-8")
        )
        metodo = next(t for t in esquemas if t["schemaName"] == "Dim_MetodoPago")
        columnas = {
            s["name"]: s["dataType"]
            for k in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
            for s in metodo.get(k, [])
        }

        assert columnas["fechaexpiracion"] == "LONG"


class TestOrdenYAcotamiento:
    def test_orden_ascendente_lo_que_antes_caduca_primero(
        self, repo, metodos_pago_sembrados
    ):
        fechas = [f["fechaexpiracion"] for f in repo.metodos_de_pago(limit=500)]

        assert fechas == sorted(fechas)

    def test_acota_por_cuenta(self, repo, metodos_pago_sembrados):
        filas = repo.metodos_de_pago(limit=500, cuenta=CUENTA_A)

        assert all(f["idcliente"] == CUENTA_A for f in filas)

    def test_no_trae_el_identificador_de_cobro(self, repo, metodos_pago_sembrados):
        for fila in repo.metodos_de_pago(limit=500):
            assert "tokenpasarela" not in fila
