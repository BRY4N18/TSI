"""La dimensión guarda **dos versiones** de la unidad que cambió (T035).

Complementa al caso ancla mirando la otra punta: aquella comprobaba que los
hechos conservan su atribución; esta, que la dimensión tiene de qué. Una sola
fila vigente y una cerrada, sin huecos ni solapes en su vigencia.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_unidad import construir  # noqa: E402

PRIMERA_CARGA = datetime(2026, 1, 1)
CAMBIO = datetime(2026, 6, 1)

CLIENTES = [
    {"idcliente": 1, "nombre": "Proveedor A", "razon_social": "A"},
    {"idcliente": 2, "nombre": "Proveedor B", "razon_social": "B"},
]
CONDADOS = [{"idcondado": 1, "condado": "Cuauhtemoc"}]


def _origen(idcliente):
    return [
        {
            "idunidademergencia": 7,
            "unidademergencia": "Ambulancia 7",
            "placa": "ABC-123",
            "tipounidademergencia": "Ambulancia",
            "capacidad": "4",
            "idcliente": idcliente,
            "idcondado": 1,
            "zonacobertura": "Norte",
        }
    ]


def _tras_el_cambio():
    primera = construir(_origen(1), CLIENTES, CONDADOS, [], PRIMERA_CARGA)
    return primera, construir(_origen(2), CLIENTES, CONDADOS, primera, CAMBIO)


class TestDosVersiones:
    def test_la_primera_carga_produce_una_sola_version_vigente(self):
        primera, _ = _tras_el_cambio()

        assert len(primera) == 1
        assert primera[0]["es_vigente"] == 1
        assert primera[0]["valido_hasta"] is None

    def test_el_cambio_produce_exactamente_dos_filas(self):
        _, cambio = _tras_el_cambio()

        assert len(cambio) == 2

    def test_una_queda_cerrada_y_la_otra_vigente(self):
        _, cambio = _tras_el_cambio()

        cerradas = [f for f in cambio if f["es_vigente"] == 0]
        vigentes = [f for f in cambio if f["es_vigente"] == 1]

        assert len(cerradas) == 1
        assert len(vigentes) == 1
        assert cerradas[0]["proveedor"] == "Proveedor A"
        assert vigentes[0]["proveedor"] == "Proveedor B"

    def test_la_cerrada_tiene_fin_de_vigencia_y_la_vigente_no(self):
        _, cambio = _tras_el_cambio()

        cerrada = next(f for f in cambio if f["es_vigente"] == 0)
        vigente = next(f for f in cambio if f["es_vigente"] == 1)

        assert cerrada["valido_hasta"] is not None
        assert vigente["valido_hasta"] is None

    def test_la_vigencia_es_continua(self):
        # Un hueco perdería los despachos de ese intervalo; un solape los contaría
        # dos veces. Ninguno de los dos fallos avisa.
        _, cambio = _tras_el_cambio()

        cerrada = next(f for f in cambio if f["es_vigente"] == 0)
        vigente = next(f for f in cambio if f["es_vigente"] == 1)

        assert cerrada["valido_hasta"] == vigente["valido_desde"]

    def test_ambas_conservan_la_misma_clave_de_negocio(self):
        # Son dos versiones de LA MISMA unidad, no dos unidades
        _, cambio = _tras_el_cambio()

        assert {f["idunidademergencia"] for f in cambio} == {7}
        assert len({f["sk_unidad"] for f in cambio}) == 2
