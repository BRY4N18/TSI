"""T008 — paginacion keyset por cursor (research D2).

Lo que se prueba aqui no es "que pagine": es que **no repita ni salte filas**,
que es lo unico que distingue el keyset de un `OFFSET` y la razon de haberlo
elegido (SC-005).
"""

from __future__ import annotations

import pytest

from core.informes.paginacion import (
    LIMIT_DEFECTO,
    LIMIT_MAXIMO,
    CampoCursor,
    Cursor,
    CursorInvalido,
    LimiteInvalido,
    parse_limit,
)

CURSOR_ESCALAR = Cursor(CampoCursor("idcliente"))
CURSOR_COMPUESTO = Cursor(CampoCursor("fecha_creacion"), CampoCursor("idcliente"))


class TestParseLimit:
    def test_por_defecto_50(self):
        assert parse_limit({}) == LIMIT_DEFECTO == 50

    def test_valor_declarado_se_respeta(self):
        assert parse_limit({"limit": "120"}) == 120

    def test_el_maximo_es_500_y_se_admite(self):
        assert parse_limit({"limit": str(LIMIT_MAXIMO)}) == 500

    def test_sobre_el_maximo_falla_no_se_recorta(self):
        # Recortar callando le haria creer al consumidor que recibio todo.
        with pytest.raises(LimiteInvalido, match="500"):
            parse_limit({"limit": "5000"})

    @pytest.mark.parametrize("valor", ["0", "-1"])
    def test_no_positivo_falla(self, valor):
        with pytest.raises(LimiteInvalido):
            parse_limit({"limit": valor})

    @pytest.mark.parametrize("valor", ["muchos", "50.5", ""])
    def test_no_entero(self, valor):
        if valor == "":
            assert parse_limit({"limit": valor}) == LIMIT_DEFECTO
        else:
            with pytest.raises(LimiteInvalido):
                parse_limit({"limit": valor})


class TestCursorEscalar:
    def test_ausente_arranca_desde_el_principio(self):
        assert CURSOR_ESCALAR.decodificar(None) is None
        assert CURSOR_ESCALAR.decodificar("") is None

    def test_ida_y_vuelta(self):
        texto = CURSOR_ESCALAR.codificar({"idcliente": 42, "razon_social": "ACME"})

        assert texto == "42"
        assert CURSOR_ESCALAR.decodificar(texto) == (42,)

    def test_es_escalar(self):
        assert CURSOR_ESCALAR.escalar is True


class TestCursorCompuesto:
    def test_ida_y_vuelta_conserva_el_orden_de_los_campos(self):
        fila = {"fecha_creacion": 1_786_569_480_560, "idcliente": 42}

        texto = CURSOR_COMPUESTO.codificar(fila)

        assert texto == "1786569480560|42"
        assert CURSOR_COMPUESTO.decodificar(texto) == (1_786_569_480_560, 42)

    def test_numero_de_componentes_equivocado_falla(self):
        # Devolver la primera pagina ante un cursor corrupto haria que el
        # consumidor recorriera en bucle las mismas filas creyendo que avanza.
        with pytest.raises(CursorInvalido, match="2 componente"):
            CURSOR_COMPUESTO.decodificar("42")

    def test_componente_no_numerico_falla(self):
        with pytest.raises(CursorInvalido):
            CURSOR_COMPUESTO.decodificar("ayer|42")

    def test_columna_de_orden_ausente_falla_ruidosamente(self):
        # Un centinela coercionado a None emitiria un cursor que no localiza
        # ninguna fila: la paginacion se detendria sin error visible.
        with pytest.raises(CursorInvalido, match="fecha_creacion"):
            CURSOR_COMPUESTO.codificar({"fecha_creacion": None, "idcliente": 42})


class TestRecorte:
    """Se piden `limit + 1` filas; la sobrante es la senal de pagina siguiente."""

    @staticmethod
    def _filas(n: int) -> list[dict]:
        return [{"idcliente": i} for i in range(1, n + 1)]

    def test_menos_filas_que_el_limite_no_hay_siguiente(self):
        pagina = CURSOR_ESCALAR.recortar(self._filas(3), limit=5)

        assert len(pagina.filas) == 3
        assert pagina.cursor is None
        assert pagina.has_next is False

    def test_exactamente_el_limite_no_hay_siguiente(self):
        # El caso frontera: 5 filas con limit=5 significa que no sobro ninguna.
        pagina = CURSOR_ESCALAR.recortar(self._filas(5), limit=5)

        assert len(pagina.filas) == 5
        assert pagina.cursor is None

    def test_una_de_mas_hay_siguiente_y_la_sobrante_no_se_devuelve(self):
        pagina = CURSOR_ESCALAR.recortar(self._filas(6), limit=5)

        assert len(pagina.filas) == 5
        assert pagina.has_next is True
        assert pagina.cursor == "5", "el cursor sale de la ultima fila DEVUELTA, no de la sobrante"

    def test_pagina_vacia(self):
        pagina = CURSOR_ESCALAR.recortar([], limit=5)

        assert pagina.filas == []
        assert pagina.cursor is None

    def test_cursor_null_en_la_ultima_pagina(self):
        assert CURSOR_ESCALAR.recortar(self._filas(2), limit=5).to_meta() == {
            "cursor": None,
            "limit": 5,
            "has_next": False,
        }


class TestRecorridoCompleto:
    """SC-005 — recorrer por paginas devuelve cada fila exactamente una vez."""

    def test_ninguna_fila_se_repite_ni_se_salta(self):
        todas = [{"idcliente": i} for i in range(1, 24)]
        limit = 5

        vistas: list[int] = []
        cursor = None
        for _ in range(10):  # tope de seguridad frente a un bucle infinito
            arranque = CURSOR_ESCALAR.decodificar(cursor)
            restantes = (
                [f for f in todas if f["idcliente"] > arranque[0]] if arranque else todas
            )
            pagina = CURSOR_ESCALAR.recortar(restantes[: limit + 1], limit)
            vistas.extend(f["idcliente"] for f in pagina.filas)
            cursor = pagina.cursor
            if cursor is None:
                break

        assert cursor is None, "el recorrido no termino"
        assert vistas == [f["idcliente"] for f in todas]
        assert len(vistas) == len(set(vistas)), "hay filas repetidas entre paginas"

    def test_una_fila_nueva_a_mitad_de_recorrido_no_desplaza_las_pendientes(self):
        """Es justo lo que `OFFSET` no puede garantizar, y Kafka escribe en continuo."""
        todas = [{"idcliente": i} for i in range(1, 11)]

        primera = CURSOR_ESCALAR.recortar(todas[:6], limit=5)
        assert [f["idcliente"] for f in primera.filas] == [1, 2, 3, 4, 5]

        # Entra una fila nueva ANTES del cursor mientras el consumidor pagina.
        todas.insert(0, {"idcliente": 0})

        arranque = CURSOR_ESCALAR.decodificar(primera.cursor)
        restantes = [f for f in todas if f["idcliente"] > arranque[0]]
        segunda = CURSOR_ESCALAR.recortar(restantes[:6], limit=5)

        assert [f["idcliente"] for f in segunda.filas] == [6, 7, 8, 9, 10]
