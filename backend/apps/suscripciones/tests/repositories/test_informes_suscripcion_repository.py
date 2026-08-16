"""T020 — filtros, orden determinista y cursor del listado de suscripciones."""

from __future__ import annotations

import pytest

from core.informes.paginacion import ASC, DESC
from core.repositories.suscripciones.informes_suscripcion_repository import (
    CURSOR_SUSCRIPCIONES,
    ORDEN_SUSCRIPCIONES,
    InformesSuscripcionRepository,
)
from apps.suscripciones.tests.conftest import (
    AHORA_MS,
    CUENTA_A,
    CUENTA_B,
    DIA_MS,
    PLAN_BASICO,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesSuscripcionRepository()


class TestCursorYOrden:
    def test_es_escalar_porque_ordena_por_la_clave(self):
        assert CURSOR_SUSCRIPCIONES.escalar is True

    def test_orden_descendente_por_defecto(self):
        assert ORDEN_SUSCRIPCIONES is DESC
        assert CURSOR_SUSCRIPCIONES.order_by(DESC) == "id_suscripcion DESC"

    def test_la_direccion_del_cursor_sigue_a_la_del_orden(self):
        assert "<" in CURSOR_SUSCRIPCIONES.clausula(DESC)
        assert ">" in CURSOR_SUSCRIPCIONES.clausula(ASC)


class TestFiltros:
    def test_por_cuenta(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, cuenta=CUENTA_B)

        assert [f["id_suscripcion"] for f in filas] == [7003]

    def test_por_estado(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, estado="Cancelada", cuenta=CUENTA_A)

        assert [f["id_suscripcion"] for f in filas] == [7002]

    def test_por_plan(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, idplan=PLAN_BASICO, cuenta=CUENTA_A)

        assert [f["id_suscripcion"] for f in filas] == [7002]

    def test_por_vencimiento(self, repo, dos_cuentas):
        # La 7001 vence en 5 días; la 7003 en 60.
        filas = repo.suscripciones(
            limit=500, vence_antes_de=AHORA_MS + 10 * DIA_MS, cuenta=CUENTA_A
        )

        assert 7001 in {f["id_suscripcion"] for f in filas}
        assert 7003 not in {f["id_suscripcion"] for f in filas}

    def test_los_filtros_se_acumulan_no_se_pisan(self, repo, dos_cuentas):
        solo_cuenta = repo.suscripciones(limit=500, cuenta=CUENTA_A)
        con_estado = repo.suscripciones(limit=500, cuenta=CUENTA_A, estado="Cancelada")

        assert len(con_estado) < len(solo_cuenta)

    def test_una_combinacion_sin_resultados_devuelve_vacio(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, cuenta=CUENTA_B, estado="Cancelada")

        assert filas == []


class TestRangoDeCancelacion:
    """Filtro **de columna**, no el período genérico del contrato."""

    def test_desde_acota_por_abajo(self, repo, dos_cuentas):
        filas = repo.suscripciones(
            limit=500, cuenta=CUENTA_A, cancelada_desde=AHORA_MS - 20 * DIA_MS
        )

        assert [f["id_suscripcion"] for f in filas] == [7002]

    def test_desde_posterior_a_la_cancelacion_la_excluye(self, repo, dos_cuentas):
        filas = repo.suscripciones(
            limit=500, cuenta=CUENTA_A, cancelada_desde=AHORA_MS
        )

        assert 7002 not in {f["id_suscripcion"] for f in filas}

    def test_hasta_excluye_las_no_canceladas(self, repo, dos_cuentas):
        # Una suscripción sin cancelar no tiene fecha: no puede caer dentro de
        # un rango de cancelaciones.
        filas = repo.suscripciones(
            limit=500, cuenta=CUENTA_A, cancelada_hasta=AHORA_MS
        )

        assert 7001 not in {f["id_suscripcion"] for f in filas}


class TestOrdenYPaginacion:
    def test_orden_determinista_descendente(self, repo, dos_cuentas):
        ids = [f["id_suscripcion"] for f in repo.suscripciones(limit=500)]

        assert ids == sorted(ids, reverse=True)

    def test_pide_una_fila_de_mas(self, repo, dos_cuentas):
        assert len(repo.suscripciones(limit=1, cuenta=CUENTA_A)) == 2

    def test_el_cursor_arranca_despues_de_la_fila_indicada(self, repo, dos_cuentas):
        primera = repo.suscripciones(limit=1, cuenta=CUENTA_A)[0]

        siguientes = repo.suscripciones(
            limit=500, cuenta=CUENTA_A, cursor=(primera["id_suscripcion"],)
        )

        assert all(
            f["id_suscripcion"] < primera["id_suscripcion"] for f in siguientes
        )

    def test_el_cursor_respeta_el_acotamiento(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, cuenta=CUENTA_B, cursor=(999999,))

        assert all(f["idcliente"] == CUENTA_B for f in filas)


class TestColumnas:
    def test_trae_lo_necesario_para_resolver_y_decidir(self, repo, dos_cuentas):
        fila = repo.suscripciones(limit=1, cuenta=CUENTA_A)[0]

        assert {"id_suscripcion", "idcliente", "idplan", "idplan_programado"} <= set(fila)

    def test_no_trae_columnas_que_el_listado_no_usa(self, repo, dos_cuentas):
        for fila in repo.suscripciones(limit=500, cuenta=CUENTA_A):
            assert "severidades_desbloqueadas" not in fila
            assert "carga_lote_habilitada" not in fila


class TestCatalogos:
    def test_resuelve_el_nombre_del_plan(self, repo, dos_cuentas):
        from apps.suscripciones.tests.conftest import PLAN_PRO

        assert repo.nombres_de_plan([PLAN_PRO]) == {PLAN_PRO: "Pro"}

    def test_descarta_el_centinela_cero(self, repo, dos_cuentas):
        assert repo.nombres_de_plan([0]) == {}

    def test_sin_ids_no_consulta(self, repo):
        assert repo.nombres_de_plan([]) == {}
        assert repo.razones_sociales([]) == {}

    def test_resuelve_la_razon_social(self, repo, dos_cuentas):
        assert repo.razones_sociales([CUENTA_A]) == {CUENTA_A: "Aseguradora Torres S.A."}
