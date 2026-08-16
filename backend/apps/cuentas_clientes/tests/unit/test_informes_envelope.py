"""T009 — forma del envelope `{data, meta:{pagination, filtros}}`.

Los 64 listados de los 8 departamentos responden con esta forma. Si diverge,
diverge para todos a la vez, y un consumidor no puede escribir un cliente unico.
"""

from __future__ import annotations

from core.informes.envelope import listado_response
from core.informes.paginacion import CampoCursor, Cursor

CURSOR = Cursor(CampoCursor("idcliente"))


def _pagina(n_filas: int = 3, limit: int = 5):
    filas = [{"idcliente": i, "razon_social": f"Cuenta {i}"} for i in range(1, n_filas + 1)]
    return CURSOR.recortar(filas, limit)


class TestForma:
    def test_claves_de_primer_nivel(self):
        cuerpo = listado_response(_pagina()).data

        assert set(cuerpo) == {"data", "meta"}
        assert set(cuerpo["meta"]) == {"pagination", "filtros"}

    def test_data_lleva_las_filas(self):
        cuerpo = listado_response(_pagina(2)).data

        assert len(cuerpo["data"]) == 2
        assert cuerpo["data"][0]["razon_social"] == "Cuenta 1"

    def test_pagination_declara_cursor_limit_y_has_next(self):
        meta = listado_response(_pagina()).data["meta"]["pagination"]

        assert set(meta) == {"cursor", "limit", "has_next"}
        assert meta["limit"] == 5

    def test_cursor_null_cuando_no_hay_siguiente(self):
        meta = listado_response(_pagina(3, limit=5)).data["meta"]["pagination"]

        assert meta["cursor"] is None
        assert meta["has_next"] is False

    def test_cursor_presente_cuando_hay_siguiente(self):
        meta = listado_response(_pagina(6, limit=5)).data["meta"]["pagination"]

        assert meta["cursor"] == "5"
        assert meta["has_next"] is True


class TestFiltros:
    def test_refleja_los_filtros_aplicados_ya_normalizados(self):
        # `dias_minimo` llega como entero, no como el texto que vino en la URL:
        # es la unica forma de que el consumidor confirme como se interpreto.
        respuesta = listado_response(_pagina(), {"tipo": "aseguradora", "dias_minimo": 7})

        assert respuesta.data["meta"]["filtros"] == {"tipo": "aseguradora", "dias_minimo": 7}

    def test_un_filtro_no_declarado_no_aparece(self):
        # `{"tipo": null}` sugeriria que se filtro por un tipo nulo.
        respuesta = listado_response(_pagina(), {"tipo": None, "dias_minimo": 7})

        assert respuesta.data["meta"]["filtros"] == {"dias_minimo": 7}

    def test_sin_filtros_es_diccionario_vacio_no_null(self):
        assert listado_response(_pagina()).data["meta"]["filtros"] == {}

    def test_un_filtro_falso_si_aparece(self):
        # `activo=false` es un filtro aplicado con valor False, no una ausencia.
        respuesta = listado_response(_pagina(), {"activo": False})

        assert respuesta.data["meta"]["filtros"] == {"activo": False}


class TestListadoVacio:
    def test_sin_filas_es_200_con_data_vacia_nunca_404(self):
        """SC-007 — la ausencia de resultados es una respuesta valida."""
        respuesta = listado_response(CURSOR.recortar([], limit=50))

        assert respuesta.status_code == 200
        assert respuesta.data["data"] == []
        assert respuesta.data["meta"]["pagination"]["has_next"] is False
