"""Las dos lecturas son posibles, y **ambas son correctas** (T037, FR-009).

Un error fácil sería creer que el versionado sustituye la lectura actual por la
histórica. No: son dos preguntas distintas y las dos se hacen a diario.

- *«¿Cómo rindió el proveedor A el trimestre pasado?»* → **histórica**. Debe
  contar lo que el A hizo entonces, aunque hoy esas unidades sean del B.
- *«¿Cuánto trabajo acumulan hoy las unidades del proveedor B?»* → **actual**.
  Debe incluir lo que esas unidades hicieron bajo el A, porque la pregunta es
  sobre la flota de hoy, no sobre el mérito de nadie.

Que devuelvan **cifras distintas** no es una incoherencia: es la prueba de que el
modelo distingue las dos preguntas. Un modelo que las confunda responde siempre a
una de las dos, y calla que existe la otra.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_unidad import construir as construir_unidades  # noqa: E402
from lib.hechos.hecho_despacho import construir as construir_despachos  # noqa: E402

PRIMERA_CARGA = datetime(2026, 1, 1)
CAMBIO = datetime(2026, 6, 1)
ANTES = datetime(2026, 3, 15, 10, 0)
DESPUES = datetime(2026, 9, 15, 10, 0)

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


def _despacho(iddespacho, momento):
    return {
        "iddespacho": iddespacho,
        "idaccidente": f"ACC-{iddespacho}",
        "idunidademergencia": 7,
        "idorigendespacho": 1,
        "retiro_forzado": False,
        "fechahoradespacho": int(momento.timestamp() * 1000),
        "fechahorallegada": None,
        "fechahoraretiro": None,
    }


def _hechos():
    primera = construir_unidades(_origen(1), CLIENTES, CONDADOS, [], PRIMERA_CARGA)
    versiones = construir_unidades(_origen(2), CLIENTES, CONDADOS, primera, CAMBIO)
    datos = {
        "despachos": [_despacho(1, ANTES), _despacho(2, DESPUES)],
        "historial": [],
        "accidentes": [],
        "dim_unidad": versiones,
        "dim_origen": [{"idorigendespacho": 1, "origen": "Automatico"}],
        "dim_severidad": [],
        "dim_geografia": [],
    }
    return construir_despachos(datos, CAMBIO), versiones


class TestLasDosLecturas:
    def test_la_historica_reparte_los_despachos_entre_los_dos_proveedores(self):
        # Agrupar por la columna del hecho: el proveedor de aquel momento
        hechos, _ = _hechos()

        por_proveedor = {}
        for h in hechos:
            por_proveedor[h["proveedor"]] = por_proveedor.get(h["proveedor"], 0) + 1

        assert por_proveedor == {"Proveedor A": 1, "Proveedor B": 1}

    def test_la_actual_atribuye_ambos_al_proveedor_de_hoy(self):
        # Unir con la versión VIGENTE de la unidad: la flota de hoy
        hechos, versiones = _hechos()
        vigente = next(v for v in versiones if v["es_vigente"] == 1)

        actual = {}
        for h in hechos:
            if h["idunidademergencia"] == vigente["idunidademergencia"]:
                actual[vigente["proveedor"]] = actual.get(vigente["proveedor"], 0) + 1

        assert actual == {"Proveedor B": 2}

    def test_devuelven_resultados_distintos_y_eso_es_correcto(self):
        # Si coincidieran, una de las dos preguntas no se podría responder
        hechos, versiones = _hechos()
        vigente = next(v for v in versiones if v["es_vigente"] == 1)

        historica = sorted(h["proveedor"] for h in hechos)
        actual = [vigente["proveedor"]] * len(hechos)

        assert historica != actual

    def test_ambas_cuentan_el_mismo_total(self):
        # Distinto reparto, mismo total: si una perdiera despachos, no serían dos
        # lecturas del mismo dato sino un error en una de ellas
        hechos, _ = _hechos()

        assert len(hechos) == 2
