"""T039 — filtro por estado, orden ascendente y cursor compuesto de la bandeja."""

from __future__ import annotations

import pytest

from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A, CUENTA_B
from core.informes.paginacion import ASC
from core.repositories.suscripciones.informes_cambio_plan_repository import (
    CURSOR_SOLICITUDES,
    ORDEN_SOLICITUDES,
    InformesCambioPlanRepository,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesCambioPlanRepository()


class TestCursorYOrden:
    def test_desempata_por_clave_primaria(self):
        assert CURSOR_SOLICITUDES.campos[0].nombre == "fecha_solicitud"
        assert CURSOR_SOLICITUDES.campos[1].nombre == "idsolicitud"

    def test_orden_ascendente_por_defecto(self):
        assert ORDEN_SOLICITUDES is ASC
        assert (
            CURSOR_SOLICITUDES.order_by(ASC)
            == "fecha_solicitud ASC, idsolicitud ASC"
        )

    def test_la_clausula_anida_el_desempate(self):
        clausula = CURSOR_SOLICITUDES.clausula(ASC)

        assert "fecha_solicitud > %(cursor_0)s" in clausula
        assert "fecha_solicitud = %(cursor_0)s" in clausula
        assert "idsolicitud > %(cursor_1)s" in clausula


class TestFiltros:
    def test_por_cuenta(self, repo, solicitudes_sembradas):
        filas = repo.solicitudes(limit=500, cuenta=CUENTA_B)

        assert [f["idsolicitud"] for f in filas] == [7503]

    def test_por_estado(self, repo, solicitudes_sembradas):
        filas = repo.solicitudes(limit=500, estado="Pendiente")

        assert {f["idsolicitud"] for f in filas} == {7501, 7503}

    def test_combinados(self, repo, solicitudes_sembradas):
        filas = repo.solicitudes(limit=500, cuenta=CUENTA_A, estado="Rechazada")

        assert [f["idsolicitud"] for f in filas] == [7502]

    def test_sin_resultados_devuelve_vacio(self, repo, solicitudes_sembradas):
        assert repo.solicitudes(limit=500, cuenta=CUENTA_B, estado="Rechazada") == []


class TestOrdenYPaginacion:
    def test_orden_ascendente_lo_mas_antiguo_primero(self, repo, solicitudes_sembradas):
        fechas = [f["fecha_solicitud"] for f in repo.solicitudes(limit=500)]

        assert fechas == sorted(fechas)

    def test_pide_una_fila_de_mas(self, repo, solicitudes_sembradas):
        assert len(repo.solicitudes(limit=1, cuenta=CUENTA_A)) == 2

    def test_el_cursor_arranca_despues_de_la_fila_indicada(
        self, repo, solicitudes_sembradas
    ):
        primera = repo.solicitudes(limit=1)[0]
        cursor = (primera["fecha_solicitud"], primera["idsolicitud"])

        siguientes = repo.solicitudes(limit=500, cursor=cursor)

        assert primera["idsolicitud"] not in {f["idsolicitud"] for f in siguientes}

    def test_dos_del_mismo_instante_no_se_pierden(self, repo, mock_pinot, dos_cuentas):
        """Para esto el cursor es compuesto."""
        from conftest import PINOT_STORE
        from apps.suscripciones.tests.conftest import PLAN_BASICO, PLAN_PRO

        for i in (7601, 7602, 7603):
            PINOT_STORE["Fact_Solicitud_Cambio_Plan"].append(
                {"idsolicitud": i, "idcliente": CUENTA_A, "idplanactual": PLAN_BASICO,
                 "idplansolicitado": PLAN_PRO, "estado": "Pendiente", "motivo": "x",
                 "idadminaprobador": None, "motivo_rechazo": None,
                 "fecha_solicitud": AHORA_MS, "fecha_resolucion": None,
                 "fecha_actualizacion": AHORA_MS}
            )

        vistas: list[int] = []
        cursor = None
        for _ in range(8):
            filas = repo.solicitudes(limit=1, cuenta=CUENTA_A, cursor=cursor)
            if not filas:
                break
            fila = filas[0]
            vistas.append(fila["idsolicitud"])
            cursor = (fila["fecha_solicitud"], fila["idsolicitud"])

        assert len(vistas) == len(set(vistas)), "una fila se repitio entre paginas"
        assert {7601, 7602, 7603} <= set(vistas)


class TestCatalogo:
    def test_resuelve_el_resolutor(self, repo, solicitudes_sembradas):
        from apps.suscripciones.tests.conftest import ADMIN_A

        assert repo.nombres_de_usuario([ADMIN_A]) == {ADMIN_A: "Ana Torres"}

    def test_descarta_los_nulos(self, repo):
        assert repo.nombres_de_usuario([None]) == {}
        assert repo.nombres_de_usuario([]) == {}
