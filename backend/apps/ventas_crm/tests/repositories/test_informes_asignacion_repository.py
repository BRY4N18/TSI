"""T029 — filtros, orden determinista y cursor compuesto de las reasignaciones."""

from __future__ import annotations

import pytest

from core.informes.paginacion import DESC
from core.repositories.ventas_crm.informes_asignacion_repository import (
    CURSOR_ASIGNACIONES,
    InformesAsignacionRepository,
)
from apps.ventas_crm.tests.conftest import AHORA_MS, DIA_MS


@pytest.fixture
def repo(mock_pinot):
    return InformesAsignacionRepository()


class TestCursorCompuesto:
    def test_desempata_por_clave_primaria(self):
        # Dos reasignaciones del mismo instante caerían del mismo lado del
        # cursor sin el desempate, y una se perdería en el corte de página.
        assert CURSOR_ASIGNACIONES.campos[0].nombre == "fechahoraasignacion"
        assert CURSOR_ASIGNACIONES.campos[1].nombre == "idasignacion"

    def test_el_order_by_nombra_los_dos_campos(self):
        assert (
            CURSOR_ASIGNACIONES.order_by(DESC)
            == "fechahoraasignacion DESC, idasignacion DESC"
        )

    def test_la_clausula_anida_el_desempate(self):
        clausula = CURSOR_ASIGNACIONES.clausula(DESC)

        assert "fechahoraasignacion < %(cursor_0)s" in clausula
        assert "fechahoraasignacion = %(cursor_0)s" in clausula
        assert "idasignacion < %(cursor_1)s" in clausula


class TestRangoOpcional:
    def test_sin_rango_devuelve_el_historico_completo(self, repo, asignaciones_sembradas):
        ids = [f["idasignacion"] for f in repo.reasignaciones(limit=500)]

        assert set(ids) == {8501, 8502, 8503}

    def test_solo_desde_acota_por_abajo(self, repo, asignaciones_sembradas):
        filas = repo.reasignaciones(limit=500, desde_ms=AHORA_MS - 5 * DIA_MS)

        assert {f["idasignacion"] for f in filas} == {8502, 8503}

    def test_solo_hasta_acota_por_arriba(self, repo, asignaciones_sembradas):
        filas = repo.reasignaciones(limit=500, hasta_ms=AHORA_MS - 5 * DIA_MS)

        assert {f["idasignacion"] for f in filas} == {8501, 8502}

    def test_ambos_extremos_acotan_el_intervalo(self, repo, asignaciones_sembradas):
        filas = repo.reasignaciones(
            limit=500, desde_ms=AHORA_MS - 6 * DIA_MS, hasta_ms=AHORA_MS - 2 * DIA_MS
        )

        assert [f["idasignacion"] for f in filas] == [8502]

    def test_el_extremo_es_inclusivo(self, repo, asignaciones_sembradas):
        filas = repo.reasignaciones(limit=500, desde_ms=AHORA_MS - DIA_MS)

        assert [f["idasignacion"] for f in filas] == [8503]


class TestFiltros:
    def test_por_prospecto(self, repo, asignaciones_sembradas):
        filas = repo.reasignaciones(limit=500, idprospecto=8201)

        assert [f["idasignacion"] for f in filas] == [8502]

    def test_por_tipo_de_asignacion(self, repo, asignaciones_sembradas):
        filas = repo.reasignaciones(limit=500, tipo_asignacion="automatica")

        assert [f["idasignacion"] for f in filas] == [8501]

    def test_tipos_disponibles_sale_de_los_datos(self, repo, asignaciones_sembradas):
        assert repo.tipos_disponibles() == ["automatica", "manual"]


class TestOrdenYPaginacion:
    def test_orden_descendente_lo_mas_reciente_primero(self, repo, asignaciones_sembradas):
        fechas = [f["fechahoraasignacion"] for f in repo.reasignaciones(limit=500)]

        assert fechas == sorted(fechas, reverse=True)

    def test_pide_una_fila_de_mas(self, repo, asignaciones_sembradas):
        assert len(repo.reasignaciones(limit=2)) == 3

    def test_el_cursor_arranca_despues_de_la_fila_indicada(
        self, repo, asignaciones_sembradas
    ):
        primera = repo.reasignaciones(limit=1)[0]
        cursor = (primera["fechahoraasignacion"], primera["idasignacion"])

        siguientes = repo.reasignaciones(limit=500, cursor=cursor)

        assert primera["idasignacion"] not in [f["idasignacion"] for f in siguientes]

    def test_dos_filas_del_mismo_instante_no_se_pierden(self, repo, mock_pinot, dos_carteras):
        """Es justo para esto que el cursor es compuesto."""
        from conftest import PINOT_STORE

        for i in (8701, 8702, 8703):
            PINOT_STORE["Fact_Asignacion"].append(
                {
                    "idasignacion": i,
                    "idprospecto": 8101,
                    "idusuariogerenteanterior": None,
                    "idusuariogerenteactual": 8801,
                    "tipoasignacion": "manual",
                    "motivo": None,
                    "fechahoraasignacion": AHORA_MS,  # el MISMO instante
                    "fecha_actualizacion": AHORA_MS,
                }
            )

        vistas: list[int] = []
        cursor = None
        for _ in range(6):
            filas = repo.reasignaciones(limit=1, cursor=cursor)
            if not filas:
                break
            fila = filas[0]
            vistas.append(fila["idasignacion"])
            cursor = (fila["fechahoraasignacion"], fila["idasignacion"])

        assert len(vistas) == len(set(vistas)), "una fila se repitio entre paginas"
        assert {8701, 8702, 8703} <= set(vistas)


class TestCatalogos:
    def test_resuelve_la_empresa(self, repo, asignaciones_sembradas):
        assert repo.empresas_de_prospecto([8101]) == {8101: "Alfa Seguros"}

    def test_sin_ids_no_consulta(self, repo):
        assert repo.empresas_de_prospecto([]) == {}
        assert repo.nombres_de_usuario([]) == {}

    def test_descarta_los_nulos(self, repo):
        assert repo.nombres_de_usuario([None]) == {}
