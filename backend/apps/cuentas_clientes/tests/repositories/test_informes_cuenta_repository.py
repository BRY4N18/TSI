"""T041 — filtros, orden determinista y rango opcional de los listados de OT17."""

from __future__ import annotations

import pytest

from core.informes.paginacion import DESC
from core.repositories.cuentas_clientes.cliente_repository import (
    ESTADO_CLIENTE_ACTIVO,
    ESTADO_CLIENTE_BAJA,
)
from core.repositories.cuentas_clientes.informes_cuenta_repository import (
    CURSOR_CUENTAS,
    CURSOR_TRANSFERENCIAS,
    InformesCuentaRepository,
)
from apps.cuentas_clientes.tests.conftest import BASE_MS, DIA_MS


@pytest.fixture
def repo(mock_pinot):
    return InformesCuentaRepository()


class TestFormaDelCursor:
    def test_cuentas_es_escalar_porque_ordena_por_la_clave(self):
        assert CURSOR_CUENTAS.escalar is True

    def test_transferencias_desempata_por_clave(self):
        # Dos transferencias del mismo instante caerían del mismo lado sin él.
        assert CURSOR_TRANSFERENCIAS.campos[1].nombre == "idhistorialtransferencia"

    def test_el_order_by_de_transferencias_es_descendente(self):
        assert (
            CURSOR_TRANSFERENCIAS.order_by(DESC)
            == "fechahora DESC, idhistorialtransferencia DESC"
        )


class TestCuentas:
    def test_sin_filtro_devuelve_todos_los_estados(self, repo, cuentas_sembradas):
        estados = {f["estado"] for f in repo.cuentas(limit=500)}

        assert ESTADO_CLIENTE_ACTIVO in estados
        assert ESTADO_CLIENTE_BAJA in estados, (
            "un listado de ciclo de vida que esconda el final del ciclo no sirve"
        )

    def test_filtra_por_estado(self, repo, cuentas_sembradas):
        filas = repo.cuentas(limit=500, estado=ESTADO_CLIENTE_BAJA)

        assert [f["idcliente"] for f in filas] == [8002]

    def test_filtra_por_tipo(self, repo, cuentas_sembradas):
        filas = repo.cuentas(limit=500, tipo="Proveedor")

        assert 8003 in [f["idcliente"] for f in filas]

    def test_orden_descendente_por_defecto(self, repo, cuentas_sembradas):
        ids = [f["idcliente"] for f in repo.cuentas(limit=500)]

        assert ids == sorted(ids, reverse=True)

    def test_el_cursor_arranca_despues_de_la_fila_indicada(self, repo, cuentas_sembradas):
        primera = repo.cuentas(limit=1)[0]

        siguientes = repo.cuentas(limit=500, cursor=(primera["idcliente"],))

        assert all(f["idcliente"] < primera["idcliente"] for f in siguientes)

    def test_trae_admin_local_id_para_resolver_pero_no_mas(self, repo, cuentas_sembradas):
        for fila in repo.cuentas(limit=500):
            assert "admin_local_id" in fila
            assert "nit_identificacion" not in fila


class TestTransferencias:
    def test_sin_rango_devuelve_el_historico_completo(self, repo, transferencias_sembradas):
        # FR-013: omitir el rango no es una petición incompleta.
        ids = [f["idhistorialtransferencia"] for f in repo.transferencias(limit=500)]

        assert set(ids) == {8101, 8102, 8103}

    def test_orden_descendente_lo_mas_reciente_primero(
        self, repo, transferencias_sembradas
    ):
        fechas = [f["fechahora"] for f in repo.transferencias(limit=500)]

        assert fechas == sorted(fechas, reverse=True)

    def test_solo_desde_acota_por_abajo(self, repo, transferencias_sembradas):
        filas = repo.transferencias(limit=500, desde_ms=BASE_MS + 5 * DIA_MS)

        assert {f["idhistorialtransferencia"] for f in filas} == {8102, 8103}

    def test_solo_hasta_acota_por_arriba(self, repo, transferencias_sembradas):
        filas = repo.transferencias(limit=500, hasta_ms=BASE_MS + 5 * DIA_MS)

        assert {f["idhistorialtransferencia"] for f in filas} == {8101, 8102}

    def test_ambos_extremos_acotan_el_intervalo(self, repo, transferencias_sembradas):
        filas = repo.transferencias(
            limit=500, desde_ms=BASE_MS + DIA_MS, hasta_ms=BASE_MS + 10 * DIA_MS
        )

        assert [f["idhistorialtransferencia"] for f in filas] == [8102]

    def test_el_extremo_es_inclusivo(self, repo, transferencias_sembradas):
        # `desde` justo en la fecha de una transferencia debe incluirla.
        filas = repo.transferencias(limit=500, desde_ms=BASE_MS + 20 * DIA_MS)

        assert [f["idhistorialtransferencia"] for f in filas] == [8103]

    def test_filtra_por_cliente(self, repo, transferencias_sembradas):
        filas = repo.transferencias(limit=500, idcliente=8002)

        assert [f["idhistorialtransferencia"] for f in filas] == [8103]


class TestCatalogos:
    def test_resuelve_nombres_de_usuario(self, repo, cuentas_sembradas):
        assert repo.nombres_de_usuario([1]) == {1: "Admin Sistema"}

    def test_un_usuario_inexistente_no_aparece(self, repo):
        assert repo.nombres_de_usuario([88888]) == {}

    def test_descarta_los_nulos_sin_consultar_por_ellos(self, repo):
        assert repo.nombres_de_usuario([None, None]) == {}

    def test_resuelve_razones_sociales(self, repo, cuentas_sembradas):
        assert repo.razones_sociales([8001]) == {8001: "Cuenta Viva S.A."}
