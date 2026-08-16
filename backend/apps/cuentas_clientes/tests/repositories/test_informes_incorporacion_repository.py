"""T032 — filtros y orden determinista de los dos listados de OT04."""

from __future__ import annotations

import pytest

from core.informes.paginacion import ASC
from core.repositories.cuentas_clientes.informes_incorporacion_repository import (
    CURSOR_ONBOARDING,
    CURSOR_SOLICITUDES,
    InformesIncorporacionRepository,
)
from apps.cuentas_clientes.tests.conftest import BASE_MS, DIA_MS


@pytest.fixture
def repo(mock_pinot):
    return InformesIncorporacionRepository()


class TestFormaDelCursor:
    def test_ambos_desempatan_por_clave_primaria(self):
        # `fecha_creacion` no es única: dos solicitudes del mismo instante
        # caerían del mismo lado del cursor y una se perdería en el corte.
        assert CURSOR_SOLICITUDES.campos[1].nombre == "idcliente"
        assert CURSOR_ONBOARDING.campos[1].nombre == "id_onboarding"

    def test_el_order_by_es_ascendente_en_los_dos(self):
        assert CURSOR_SOLICITUDES.order_by(ASC) == "fecha_creacion ASC, idcliente ASC"
        assert CURSOR_ONBOARDING.order_by(ASC) == "fecha_actualizacion ASC, id_onboarding ASC"


class TestSolicitudesPendientes:
    def test_solo_las_pendientes(self, repo, solicitudes_pendientes_sembradas):
        ids = [f["idcliente"] for f in repo.solicitudes_pendientes(limit=500)]

        assert set(ids) == {7001, 7002, 7003}
        assert 7004 not in ids, "una cuenta ya activa no es una solicitud pendiente"

    def test_orden_ascendente_por_fecha(self, repo, solicitudes_pendientes_sembradas):
        fechas = [f["fecha_creacion"] for f in repo.solicitudes_pendientes(limit=500)]

        assert fechas == sorted(fechas)

    def test_filtra_por_tipo(self, repo, solicitudes_pendientes_sembradas):
        filas = repo.solicitudes_pendientes(limit=500, tipo="Proveedor")

        assert [f["idcliente"] for f in filas] == [7003]

    def test_la_fecha_de_corte_acota(self, repo, solicitudes_pendientes_sembradas):
        filas = repo.solicitudes_pendientes(
            limit=500, creadas_antes_de=BASE_MS + 5 * DIA_MS
        )

        assert {f["idcliente"] for f in filas} == {7001, 7002}

    def test_pide_una_fila_de_mas(self, repo, solicitudes_pendientes_sembradas):
        assert len(repo.solicitudes_pendientes(limit=2)) == 3

    def test_el_cursor_arranca_despues_de_la_fila_indicada(
        self, repo, solicitudes_pendientes_sembradas
    ):
        primera = repo.solicitudes_pendientes(limit=1)[0]
        cursor = (primera["fecha_creacion"], primera["idcliente"])

        siguientes = repo.solicitudes_pendientes(limit=500, cursor=cursor)

        assert primera["idcliente"] not in [f["idcliente"] for f in siguientes]

    def test_no_trae_columnas_que_el_listado_no_usa(
        self, repo, solicitudes_pendientes_sembradas
    ):
        for fila in repo.solicitudes_pendientes(limit=500):
            assert set(fila) == {"idcliente", "razon_social", "tipo", "fecha_creacion"}


class TestEtapasPendientes:
    def test_solo_las_sin_completar(self, repo, onboarding_sembrado):
        ids = [f["id_onboarding"] for f in repo.etapas_pendientes(limit=500)]

        assert set(ids) == {7101, 7102}
        assert 7103 not in ids

    def test_orden_ascendente_por_fecha(self, repo, onboarding_sembrado):
        fechas = [f["fecha_actualizacion"] for f in repo.etapas_pendientes(limit=500)]

        assert fechas == sorted(fechas)

    def test_filtra_por_etapa(self, repo, onboarding_sembrado):
        filas = repo.etapas_pendientes(limit=500, etapa="configuracion_inicial")

        assert [f["id_onboarding"] for f in filas] == [7102]

    def test_la_fecha_de_corte_acota(self, repo, onboarding_sembrado):
        filas = repo.etapas_pendientes(limit=500, detenidas_antes_de=BASE_MS)

        assert [f["id_onboarding"] for f in filas] == [7101]

    def test_etapas_disponibles_sale_de_los_datos(self, repo, onboarding_sembrado):
        # De los datos y no de una lista fija: una etapa nueva sería filtrable
        # sin tocar código, y ninguna válida se rechazaría con 400.
        assert repo.etapas_disponibles() == [
            "configuracion_inicial",
            "verificacion_documental",
        ]


class TestCatalogo:
    def test_resuelve_razon_social(self, repo, solicitudes_pendientes_sembradas):
        assert repo.razones_sociales([7001]) == {7001: "Aseguradora Norte S.A."}

    def test_sin_ids_no_consulta(self, repo):
        assert repo.razones_sociales([]) == {}

    def test_un_id_inexistente_simplemente_no_aparece(self, repo):
        assert repo.razones_sociales([999999]) == {}
