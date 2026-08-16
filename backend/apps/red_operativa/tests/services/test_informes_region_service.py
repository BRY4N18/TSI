"""T039 — `dias_sin_cambio` con instante inyectado, y el filtro por antigüedad.

Es el número que decide si una región lleva demasiado tiempo detenida en
validación, que es exactamente lo que OT13 vigila. Con el reloj real esta prueba
solo podría comprobar «que devuelve algún número».
"""

from __future__ import annotations

import pytest

from apps.red_operativa.services.informes_region_service import InformesRegionService
from apps.red_operativa.tests.conftest import AHORA_MS, DIA_MS
from core.repositories.red_operativa.informes_region_repository import (
    ESTADO_EN_ALERTA,
)


@pytest.fixture
def servicio(mock_pinot, reloj_fijo):
    return InformesRegionService(ahora=reloj_fijo)


def _por_nombre(pagina):
    return {f["nombre_region"]: f for f in pagina.filas}


class TestDiasSinCambio:
    def test_es_exacto_para_el_instante_inyectado(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500)
        por_nombre = _por_nombre(pagina)

        assert por_nombre["Norte Operativa"]["dias_sin_cambio"] == 2
        assert por_nombre["Centro Alerta"]["dias_sin_cambio"] == 5
        assert por_nombre["Este Pendiente"]["dias_sin_cambio"] == 60

    def test_no_depende_del_reloj_del_sistema(self, mock_pinot, regiones_sembradas):
        diez_dias_despues = InformesRegionService(ahora=lambda: AHORA_MS + 10 * DIA_MS)

        pagina = diez_dias_despues.regiones(limit=500)

        assert _por_nombre(pagina)["Este Pendiente"]["dias_sin_cambio"] == 70

    def test_una_fecha_ausente_da_none_no_cero(self, mock_pinot, geografia_y_proveedores, reloj_fijo):
        from conftest import PINOT_STORE
        from core.pinot.tiempo import SIN_FECHA
        from apps.red_operativa.tests.conftest import ESTADO_GEO

        PINOT_STORE["Dim_RegionOperativa"].append(
            {"idregionoperativa": 5999, "idestado": ESTADO_GEO,
             "nombreregion": "Sin Fecha", "estadoregion": ESTADO_EN_ALERTA,
             "activo": True, "fecha_actualizacion": SIN_FECHA}
        )

        pagina = InformesRegionService(ahora=reloj_fijo).regiones(limit=500)
        fila = _por_nombre(pagina)["Sin Fecha"]

        # `0` diría «cambió hoy», que es lo contrario de no saber cuándo cambió
        # — y en un listado que detecta regiones detenidas la mandaría al final.
        assert fila["dias_sin_cambio"] is None
        assert fila["fecha_actualizacion"] is None


class TestFiltroPorAntiguedad:
    def test_acota_a_las_detenidas(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500, detenida_mas_de_dias=30)
        nombres = {f["nombre_region"] for f in pagina.filas}

        assert "Este Pendiente" in nombres
        assert "Norte Operativa" not in nombres

    def test_un_corte_amplio_las_incluye_a_todas(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500, detenida_mas_de_dias=0)
        nombres = {f["nombre_region"] for f in pagina.filas}

        assert {"Norte Operativa", "Centro Alerta", "Este Pendiente"} <= nombres

    def test_sin_filtro_no_acota(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500)

        assert len(pagina.filas) >= 4


class TestFormaDeLaFila:
    def test_el_estado_llega_sin_agrupar(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500)
        estados = {f["estado_region"] for f in pagina.filas}

        # Los dos que se confunden llegan **distintos**.
        assert {"En_Alerta", "Despublicada"} <= estados

    def test_resuelve_el_estado_geografico(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500)

        assert _por_nombre(pagina)["Norte Operativa"]["estado_geografico"] == "Provincia Norte"

    def test_no_expone_identificadores(self, servicio, regiones_sembradas):
        pagina = servicio.regiones(limit=500)

        for fila in pagina.filas:
            assert "idregionoperativa" not in fila
            assert "idestado" not in fila


class TestValidaciones:
    def test_resuelve_region_y_ejecutor(self, servicio, validaciones_sembradas):
        pagina = servicio.validaciones(limit=500)

        con_region = [f for f in pagina.filas if f["region"] == "Este Pendiente"]
        assert len(con_region) == 2
        assert all(f["ejecutada_por"] == "Rosa Delgado" for f in con_region)

    def test_conserva_los_dos_motivos(self, servicio, validaciones_sembradas):
        pagina = servicio.validaciones(limit=500)

        motivos = {f["motivo"] for f in pagina.filas if f["motivo"]}
        assert {"cobertura insuficiente", "sin proveedor asignado"} <= motivos

    def test_una_aprobada_sin_motivo_no_se_omite(self, servicio, validaciones_sembradas):
        pagina = servicio.validaciones(limit=500)

        aprobadas = [f for f in pagina.filas if f["resultado"] == "Aprobada"]
        assert len(aprobadas) == 1
        assert aprobadas[0]["motivo"] is None

    def test_no_expone_identificadores(self, servicio, validaciones_sembradas):
        pagina = servicio.validaciones(limit=500)

        for fila in pagina.filas:
            assert "idvalidacionregion" not in fila
            assert "idregionoperativa" not in fila
