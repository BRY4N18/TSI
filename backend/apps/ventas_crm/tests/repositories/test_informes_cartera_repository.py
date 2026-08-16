"""T017 — filtros, orden determinista y cursor de la cartera."""

from __future__ import annotations

import pytest

from core.informes.paginacion import ASC, DESC
from core.repositories.ventas_crm.informes_cartera_repository import (
    CURSOR_CARTERA,
    ORDEN_CARTERA,
    InformesCarteraRepository,
)
from apps.ventas_crm.tests.conftest import GERENTE_A, GERENTE_B


@pytest.fixture
def repo(mock_pinot):
    return InformesCarteraRepository()


class TestCursorYOrden:
    def test_es_escalar_porque_ordena_por_la_clave(self):
        assert CURSOR_CARTERA.escalar is True

    def test_orden_descendente_por_defecto(self):
        assert ORDEN_CARTERA is DESC
        assert CURSOR_CARTERA.order_by(DESC) == "idprospecto DESC"

    def test_la_direccion_del_cursor_sigue_a_la_del_orden(self):
        assert "<" in CURSOR_CARTERA.clausula(DESC)
        assert ">" in CURSOR_CARTERA.clausula(ASC)


class TestFiltrosPorSeparado:
    def test_por_titular(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, titular=GERENTE_B)

        assert {f["idprospecto"] for f in filas} == {8201, 8202}

    def test_por_canal(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, canal="Referido")

        assert [f["idprospecto"] for f in filas] == [8101]

    def test_por_tipo_de_organizacion(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, tipo_organizacion="Público")

        assert [f["idprospecto"] for f in filas] == [8103]

    def test_por_etapa(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, etapa="Propuesta")

        assert [f["idprospecto"] for f in filas] == [8202]

    def test_sin_filtros_devuelve_todo(self, repo, dos_carteras):
        assert len(repo.prospectos(limit=500)) == 5


class TestFiltrosCombinados:
    def test_titular_y_estado(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, titular=GERENTE_A, estado="perdido")

        assert [f["idprospecto"] for f in filas] == [8102]

    def test_titular_y_etapa(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, titular=GERENTE_B, etapa="Propuesta")

        assert [f["idprospecto"] for f in filas] == [8202]

    def test_una_combinacion_sin_resultados_devuelve_vacio(self, repo, dos_carteras):
        # Vacío, no todo: un filtro que no encaja no puede ensanchar el conjunto.
        filas = repo.prospectos(limit=500, titular=GERENTE_B, estado="perdido")

        assert filas == []

    def test_los_filtros_se_acumulan_no_se_pisan(self, repo, dos_carteras):
        solo_titular = repo.prospectos(limit=500, titular=GERENTE_A)
        con_etapa = repo.prospectos(limit=500, titular=GERENTE_A, etapa="Negociación")

        assert len(con_etapa) < len(solo_titular)


class TestOrdenYPaginacion:
    def test_orden_determinista_descendente(self, repo, dos_carteras):
        ids = [f["idprospecto"] for f in repo.prospectos(limit=500)]

        assert ids == sorted(ids, reverse=True)

    def test_pide_una_fila_de_mas(self, repo, dos_carteras):
        assert len(repo.prospectos(limit=2)) == 3

    def test_el_cursor_arranca_despues_de_la_fila_indicada(self, repo, dos_carteras):
        primera = repo.prospectos(limit=1)[0]

        siguientes = repo.prospectos(limit=500, cursor=(primera["idprospecto"],))

        assert all(f["idprospecto"] < primera["idprospecto"] for f in siguientes)

    def test_el_cursor_respeta_el_acotamiento(self, repo, dos_carteras):
        # El acotamiento no puede perderse al pasar de página.
        filas = repo.prospectos(limit=500, titular=GERENTE_B, cursor=(8203,))

        assert all(f["idusuario"] == GERENTE_B for f in filas)


class TestColumnas:
    def test_no_trae_datos_de_contacto(self, repo, dos_carteras):
        for fila in repo.prospectos(limit=500):
            assert "gmail" not in fila
            assert "telefono" not in fila

    def test_trae_lo_necesario_para_resolver_y_presentar(self, repo, dos_carteras):
        fila = repo.prospectos(limit=1)[0]

        # `idusuario` y `motivo_inactividad` son de uso interno —resolver el
        # ejecutivo y decidir el estado— y el servicio los retira después.
        assert {"idprospecto", "idusuario", "motivo_inactividad", "activo"} <= set(fila)


class TestMotivosDePerdida:
    def test_resuelve_el_motivo_desde_la_transicion(self, repo, dos_carteras):
        assert repo.motivos_de_perdida([8102]) == {8102: "eligio a un competidor"}

    def test_un_prospecto_sin_transicion_no_aparece(self, repo, dos_carteras):
        assert repo.motivos_de_perdida([8101]) == {}

    def test_sin_prospectos_no_consulta(self, repo):
        assert repo.motivos_de_perdida([]) == {}

    def test_con_varias_transiciones_gana_la_mas_reciente(self, repo, dos_carteras):
        from conftest import PINOT_STORE
        from apps.ventas_crm.tests.conftest import AHORA_MS

        PINOT_STORE["Fact_Pipeline"].append(
            {
                "id_transicion": 8199,
                "id_prospecto": 8102,
                "etapa_anterior": "Propuesta",
                "etapa_nueva": "Perdido",
                "motivo_perdida": "presupuesto insuficiente",
                "gerente_id": GERENTE_A,
                "fecha_transicion": AHORA_MS,  # más reciente
                "fecha_actualizacion": AHORA_MS,
            }
        )

        # Sin el desempate por fecha el resultado dependería del orden de llegada.
        assert repo.motivos_de_perdida([8102]) == {8102: "presupuesto insuficiente"}


class TestCatalogoDeUsuarios:
    def test_resuelve_el_nombre_del_ejecutivo(self, repo, dos_carteras):
        assert repo.nombres_de_usuario([GERENTE_A]) == {GERENTE_A: "Lucia Ramos"}

    def test_descarta_los_nulos_sin_consultar(self, repo):
        assert repo.nombres_de_usuario([None, None]) == {}

    def test_un_usuario_inexistente_no_aparece(self, repo):
        assert repo.nombres_de_usuario([999999]) == {}
