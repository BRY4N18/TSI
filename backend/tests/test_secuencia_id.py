"""La secuencia de identificadores no retrocede aunque Pinot vaya por detrás."""

from __future__ import annotations

import threading

import pytest

from core.pinot.secuencia import reiniciar_para_pruebas, siguiente_id


class PinotCongelado:
    """Simula la ingesta asíncrona: devuelve siempre el mismo máximo.

    Es exactamente lo que hacía Pinot el 2026-08-23 cuando 34 inicios de sesión
    recibieron el id 985: las escrituras salían, y la lectura no las veía.
    """

    def __init__(self, maximo: int):
        self.maximo = maximo
        self.consultas = 0

    def query(self, sql, params=None):
        self.consultas += 1
        return [{"max_id": self.maximo}]


class PinotCaido:
    def query(self, sql, params=None):
        raise RuntimeError("Pinot no responde")


@pytest.fixture(autouse=True)
def _limpio():
    reiniciar_para_pruebas()
    yield
    reiniciar_para_pruebas()


class TestLaSecuenciaNoRetrocede:
    def test_pinot_congelado_when_pide_varios_no_repite_ninguno(self):
        """⛔ El defecto original: con el máximo congelado, todos valían igual."""
        pinot = PinotCongelado(984)

        ids = [siguiente_id(pinot, "Fact_Session", "idsession") for _ in range(34)]

        assert ids == list(range(985, 985 + 34))
        assert len(set(ids)) == 34

    def test_tabla_vacia_when_pide_el_primero_es_uno(self):
        class Vacio:
            def query(self, sql, params=None):
                return []

        assert siguiente_id(Vacio(), "Dim_Plan", "idplan") == 1

    def test_pinot_avanza_when_supera_la_marca_manda_pinot(self):
        """Un proceso nuevo continúa donde lo dejó el anterior."""
        pinot = PinotCongelado(10)
        assert siguiente_id(pinot, "Dim_Rol", "idrol") == 11

        # La ingesta se pone al día y adelanta a lo entregado en memoria.
        pinot.maximo = 500
        assert siguiente_id(pinot, "Dim_Rol", "idrol") == 501

    def test_tablas_distintas_when_conviven_no_comparten_contador(self):
        pinot = PinotCongelado(7)

        assert siguiente_id(pinot, "Dim_Rol", "idrol") == 8
        assert siguiente_id(pinot, "Dim_Plan", "idplan") == 8

    def test_pinot_caido_when_no_responde_sigue_entregando_sin_repetir(self):
        """⚠️ Una lectura fallida no puede impedir escribir.

        Devolver 0 es seguro porque la marca en memoria sigue mandando; propagar
        el error dejaría al sistema sin poder crear nada cada vez que la consulta
        analítica tiene un mal momento.
        """
        caido = PinotCaido()

        ids = [siguiente_id(caido, "Fact_Despacho", "iddespacho") for _ in range(5)]

        assert ids == [1, 2, 3, 4, 5]

    def test_hilos_simultaneos_when_piden_a_la_vez_no_colisionan(self):
        """El servidor de desarrollo atiende en hilos: dos logins entran a la vez."""
        pinot = PinotCongelado(0)
        obtenidos: list[int] = []
        cerrojo = threading.Lock()

        def pedir():
            valor = siguiente_id(pinot, "Fact_Session", "idsession")
            with cerrojo:
                obtenidos.append(valor)

        hilos = [threading.Thread(target=pedir) for _ in range(50)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        assert len(set(obtenidos)) == 50

    @pytest.mark.parametrize("nombre", ["Dim_Rol; DROP TABLE x", "id-rol", ""])
    def test_nombre_raro_when_llega_se_rechaza(self, nombre):
        """Son literales del código, pero uno que viniera de fuera sería inyección."""
        with pytest.raises(ValueError):
            siguiente_id(PinotCongelado(1), nombre, "idrol")
