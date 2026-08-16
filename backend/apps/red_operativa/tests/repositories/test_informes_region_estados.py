"""T037 y T038 — los cinco estados de región, y el historial completo de validación.

⚠️ **`En_Alerta` no se agrupa con `Despublicada`** (research D4).

`En_Alerta` es una región **operativa** cuya cobertura se degradó: es candidata a
despublicarse, **no despublicada**. Agruparlas ocultaría exactamente la ventana
en la que OT13 puede actuar — retirar una región *antes* de que se quede sin
continuidad.

Es la misma clase de error que confundir «en disputa» con «impaga» en
Suscripciones, y produce el mismo tipo de daño: una cifra plausible que induce a
no actuar cuando todavía se puede.
"""

from __future__ import annotations

import pytest

from apps.red_operativa.tests.conftest import (
    REGION_ALERTA,
    REGION_DESPUBLICADA,
    REGION_PROD,
    REGION_VALIDACION,
)
from core.repositories.red_operativa.informes_region_repository import (
    ESTADO_DESPUBLICADA,
    ESTADO_EN_ALERTA,
    ESTADOS_OPERATIVOS,
    ESTADOS_REGION,
    InformesRegionRepository,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesRegionRepository()


class TestEnAlertaYDespublicadaSonDisjuntos:
    def test_el_filtro_de_alerta_devuelve_solo_la_alerta(self, repo, regiones_sembradas):
        filas = repo.regiones(limit=500, estado_region=ESTADO_EN_ALERTA)

        assert [f["idregionoperativa"] for f in filas] == [REGION_ALERTA]

    def test_el_filtro_de_despublicada_devuelve_solo_la_despublicada(
        self, repo, regiones_sembradas
    ):
        filas = repo.regiones(limit=500, estado_region=ESTADO_DESPUBLICADA)

        assert [f["idregionoperativa"] for f in filas] == [REGION_DESPUBLICADA]

    def test_la_alerta_nunca_aparece_entre_las_despublicadas(
        self, repo, regiones_sembradas
    ):
        despublicadas = {
            f["idregionoperativa"]
            for f in repo.regiones(limit=500, estado_region=ESTADO_DESPUBLICADA)
        }

        assert REGION_ALERTA not in despublicadas, (
            "una region En_Alerta sigue operando: agruparla con las retiradas "
            "oculta la ventana en la que OT13 puede actuar"
        )

    def test_la_despublicada_si_aparece_en_el_listado_completo(
        self, repo, regiones_sembradas
    ):
        # No se esconde: se muestra con su estado propio.
        ids = {f["idregionoperativa"] for f in repo.regiones(limit=500)}

        assert REGION_DESPUBLICADA in ids


class TestLosCincoEstadosEstanDeclarados:
    def test_son_cinco(self):
        assert len(ESTADOS_REGION) == 5

    def test_ninguno_falta(self):
        assert set(ESTADOS_REGION) == {
            "En_Validación", "Producción", "En_Alerta", "Despublicada", "Rechazada",
        }

    def test_en_alerta_cuenta_como_operativa(self):
        """Opera con cobertura degradada — sigue atendiendo."""
        assert ESTADO_EN_ALERTA in ESTADOS_OPERATIVOS

    def test_despublicada_no(self):
        assert ESTADO_DESPUBLICADA not in ESTADOS_OPERATIVOS

    def test_coinciden_con_los_que_escribe_el_operativo(self):
        import inspect

        from apps.red_operativa.services import despublicacion_automatica_service

        fuente = inspect.getsource(despublicacion_automatica_service)

        # Si el operativo cambiara un estado, el filtro devolvería vacío con
        # `200` y nadie lo notaría.
        assert ESTADO_EN_ALERTA in fuente


class TestFiltroSinFiltro:
    def test_sin_filtro_salen_los_cuatro_sembrados(self, repo, regiones_sembradas):
        ids = {f["idregionoperativa"] for f in repo.regiones(limit=500)}

        assert {REGION_PROD, REGION_ALERTA, REGION_DESPUBLICADA, REGION_VALIDACION} <= ids

    def test_el_filtro_por_antiguedad_acota(self, repo, regiones_sembradas):
        from apps.red_operativa.tests.conftest import AHORA_MS, DIA_MS

        # Detenidas desde hace más de 10 días: la despublicada y la de validación.
        # Subconjunto y no igualdad: el store base ya trae una región propia.
        ids = {f["idregionoperativa"] for f in repo.regiones(
            limit=500, sin_cambio_desde=AHORA_MS - 10 * DIA_MS
        )}

        assert {REGION_DESPUBLICADA, REGION_VALIDACION} <= ids
        assert REGION_PROD not in ids
        assert REGION_ALERTA not in ids


class TestHistorialDeValidacion:
    """T038 — se conservan **todos** los intentos (FR-005)."""

    def test_dos_rechazos_producen_dos_entradas(self, repo, validaciones_sembradas):
        filas = repo.validaciones(limit=500, idregion=REGION_VALIDACION)

        assert len(filas) == 2, (
            "el segundo rechazo sustituyo al primero: el historial de por que se "
            "rechazo una region es lo que permite ajustar los criterios"
        )

    def test_cada_uno_conserva_su_motivo(self, repo, validaciones_sembradas):
        filas = repo.validaciones(limit=500, idregion=REGION_VALIDACION)
        motivos = {f["motivo"] for f in filas}

        assert motivos == {"cobertura insuficiente", "sin proveedor asignado"}

    def test_ninguno_sustituye_al_otro(self, repo, validaciones_sembradas):
        filas = repo.validaciones(limit=500, idregion=REGION_VALIDACION)
        ids = [f["idvalidacionregion"] for f in filas]

        assert set(ids) == {5201, 5202}
        assert len(ids) == len(set(ids))

    def test_orden_descendente_lo_mas_reciente_primero(self, repo, validaciones_sembradas):
        fechas = [f["fechahora"] for f in repo.validaciones(limit=500)]

        assert fechas == sorted(fechas, reverse=True)

    def test_filtra_por_resultado(self, repo, validaciones_sembradas):
        filas = repo.validaciones(limit=500, resultado="Aprobada")

        assert [f["idvalidacionregion"] for f in filas] == [5203]

    def test_el_rango_es_opcional(self, repo, validaciones_sembradas):
        from apps.red_operativa.tests.conftest import AHORA_MS, DIA_MS

        sin_rango = repo.validaciones(limit=500)
        con_rango = repo.validaciones(limit=500, desde_ms=AHORA_MS - 30 * DIA_MS)

        assert len(sin_rango) == 3
        assert len(con_rango) == 1
