"""T008 — `meta.acotado_a` refleja el acotamiento realmente aplicado.

Sin este campo, un resultado vacío es ambiguo: un Gerente no puede distinguir
«no hay prospectos perdidos» de «no hay prospectos perdidos **míos**». Es la
misma ambigüedad que la negativa explícita del acotamiento evita en el otro
extremo — pedir lo ajeno—, aplicada al caso en que la petición fue legítima.

La otra mitad de la prueba es que la ampliación **fue aditiva**: los ocho
listados del módulo piloto no acotan, no declaran el campo, y su respuesta no
cambió.
"""

from __future__ import annotations

from core.informes.acotamiento import ACOTADO_PROPIOS, ACOTADO_TODOS
from core.informes.envelope import listado_response
from core.informes.paginacion import CampoCursor, Cursor

CURSOR = Cursor(CampoCursor("idprospecto"))


def _pagina(n=2, limit=50):
    return CURSOR.recortar([{"idprospecto": i} for i in range(1, n + 1)], limit)


class TestCampoPresente:
    def test_propios_cuando_el_resultado_esta_acotado(self):
        respuesta = listado_response(_pagina(), acotado_a=ACOTADO_PROPIOS)

        assert respuesta.data["meta"]["acotado_a"] == "propios"

    def test_todos_cuando_no_lo_esta(self):
        respuesta = listado_response(_pagina(), acotado_a=ACOTADO_TODOS)

        assert respuesta.data["meta"]["acotado_a"] == "todos"

    def test_convive_con_pagination_y_filtros(self):
        respuesta = listado_response(
            _pagina(), {"estado": "perdido"}, acotado_a=ACOTADO_PROPIOS
        )

        assert set(respuesta.data["meta"]) == {"pagination", "filtros", "acotado_a"}
        assert respuesta.data["meta"]["filtros"] == {"estado": "perdido"}

    def test_un_listado_vacio_sigue_declarando_su_alcance(self):
        # Es justo el caso que el campo existe para desambiguar.
        respuesta = listado_response(CURSOR.recortar([], 50), acotado_a=ACOTADO_PROPIOS)

        assert respuesta.data["data"] == []
        assert respuesta.data["meta"]["acotado_a"] == "propios"


class TestLaAmpliacionEsAditiva:
    """Los listados que no acotan no declaran el campo y no cambiaron."""

    def test_sin_el_argumento_el_campo_no_aparece(self):
        respuesta = listado_response(_pagina())

        assert "acotado_a" not in respuesta.data["meta"]

    def test_la_forma_del_piloto_no_cambio(self):
        respuesta = listado_response(_pagina(), {"tipo": "Corporativo"})

        assert set(respuesta.data["meta"]) == {"pagination", "filtros"}

    def test_emitirlo_siempre_obligaria_a_inventar_un_valor(self):
        """Por eso es opcional y no tiene defecto.

        Un listado sin eje de titularidad —los ocho del piloto— no puede decir
        honestamente ni `propios` ni `todos`.
        """
        respuesta = listado_response(_pagina(), acotado_a=None)

        assert "acotado_a" not in respuesta.data["meta"]
