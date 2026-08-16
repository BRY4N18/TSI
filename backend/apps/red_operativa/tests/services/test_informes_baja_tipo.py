"""T028 — la baja forzada trae su caso afectado; la normal, no (SC-004, research D5).

Los dos tipos significan cosas muy distintas:

* **`Normal`** — salida ordenada de la flota;
* **`Forzada_con_reasignación`** — **la unidad atendía un caso** y hubo que
  reasignar.

El caso afectado no es una etiqueta descriptiva: es la **traza de impacto** que
el SRS exige. Un listado que sumara ambos tipos convertiría un incidente
operativo —un accidente que se quedó sin su unidad— en una estadística de
rotación de flota.
"""

from __future__ import annotations

import pytest

from apps.red_operativa.services.informes_baja_service import InformesBajaService
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento
from core.repositories.red_operativa.informes_baja_repository import (
    TIPO_BAJA_FORZADA,
    TIPO_BAJA_NORMAL,
    InformesBajaRepository,
)

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)


@pytest.fixture
def servicio(mock_pinot):
    return InformesBajaService()


@pytest.fixture
def repo(mock_pinot):
    return InformesBajaRepository()


def _por_placa(pagina):
    return {f["placa"]: f for f in pagina.filas}


class TestLaBajaForzada:
    def test_trae_su_caso_afectado(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)

        forzada = _por_placa(pagina)["GRUA-01"]
        assert forzada["caso_afectado"] == "ACC-2026-000123"

    def test_su_tipo_lo_declara(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)

        assert _por_placa(pagina)["GRUA-01"]["tipo_baja"] == TIPO_BAJA_FORZADA


class TestLaBajaNormal:
    def test_no_trae_caso_afectado(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)

        # La clave **falta**, no vale `None`: «baja sin caso registrado» sería
        # una anomalía distinta, y aquí no la hay.
        assert "caso_afectado" not in _por_placa(pagina)["BAJA-01"]

    def test_ni_cero_ni_cadena_vacia(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)
        normal = _por_placa(pagina)["BAJA-01"]

        assert normal.get("caso_afectado") not in (0, "", "0")

    def test_pero_si_su_motivo(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)

        assert _por_placa(pagina)["BAJA-01"]["motivo"] == "fin de vida util"


class TestLosDosFiltrosSonDisjuntos:
    def test_forzadas_devuelve_solo_la_forzada(self, repo, bajas_sembradas):
        filas = repo.bajas(limit=500, tipo_baja=TIPO_BAJA_FORZADA)

        assert [f["idbajaunidad"] for f in filas] == [5102]

    def test_normales_devuelve_solo_las_normales(self, repo, bajas_sembradas):
        filas = repo.bajas(limit=500, tipo_baja=TIPO_BAJA_NORMAL)

        assert {f["idbajaunidad"] for f in filas} == {5101, 5103}

    def test_los_conjuntos_no_se_solapan(self, repo, bajas_sembradas):
        forzadas = {f["idbajaunidad"] for f in repo.bajas(limit=500, tipo_baja=TIPO_BAJA_FORZADA)}
        normales = {f["idbajaunidad"] for f in repo.bajas(limit=500, tipo_baja=TIPO_BAJA_NORMAL)}

        assert not (forzadas & normales)

    def test_y_juntos_son_todas(self, repo, bajas_sembradas):
        forzadas = {f["idbajaunidad"] for f in repo.bajas(limit=500, tipo_baja=TIPO_BAJA_FORZADA)}
        normales = {f["idbajaunidad"] for f in repo.bajas(limit=500, tipo_baja=TIPO_BAJA_NORMAL)}
        todas = {f["idbajaunidad"] for f in repo.bajas(limit=500)}

        assert forzadas | normales == todas


class TestLosTiposNoDivergenDelOperativo:
    def test_coinciden_con_los_que_escribe_el_servicio_de_bajas(self):
        """`core/` no importa de `apps/`, así que se comprueba aquí.

        Si el operativo cambiara un tipo, el filtro devolvería vacío con `200`
        y nadie lo notaría — el mismo modo de fallo que "ACTIVA" contra "Activo".
        """
        from apps.red_operativa.services import baja_unidad_service

        assert TIPO_BAJA_NORMAL == baja_unidad_service.TIPO_BAJA_NORMAL
        assert TIPO_BAJA_FORZADA == baja_unidad_service.TIPO_BAJA_FORZADA


class TestFormaDeLaFila:
    def test_resuelve_placa_proveedor_y_ejecutor(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)
        fila = _por_placa(pagina)["GRUA-01"]

        assert fila["proveedor"] == "Gruas Delgado S.A."
        assert fila["ejecutada_por"] == "Rosa Delgado"

    def test_no_expone_identificadores(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)

        for fila in pagina.filas:
            assert "idbajaunidad" not in fila
            assert "idunidademergencia" not in fila
            assert "idusuario" not in fila

    def test_orden_descendente_lo_mas_reciente_primero(self, servicio, bajas_sembradas):
        pagina = servicio.bajas(acotamiento=SIN_ACOTAR, limit=500)
        fechas = [f["fecha"] for f in pagina.filas]

        assert fechas == sorted(fechas, reverse=True)
