"""El versionado **no penaliza el caso común** (T036).

La inmensa mayoría de las entidades no cambian nunca. Si el mecanismo que existe
para las que sí cambian volviera más caro o más confuso el caso normal, sería un
mal negocio: se paga todos los días por una propiedad que se usa raras veces.

Estas pruebas fijan que una entidad que nunca cambió se comporta como si el
versionado no existiera — una sola fila, siempre vigente, y ninguna escritura en
las recargas.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_unidad import construir  # noqa: E402
from lib.dimensiones.versionado import version_vigente_en  # noqa: E402

CLIENTES = [{"idcliente": 1, "nombre": "Proveedor A", "razon_social": "A"}]
CONDADOS = [{"idcondado": 1, "condado": "Cuauhtemoc"}]

ORIGEN = [
    {
        "idunidademergencia": 7,
        "unidademergencia": "Ambulancia 7",
        "placa": "ABC-123",
        "tipounidademergencia": "Ambulancia",
        "capacidad": "4",
        "idcliente": 1,
        "idcondado": 1,
        "zonacobertura": "Norte",
    }
]


class TestEntidadQueNuncaCambia:
    def test_la_primera_carga_escribe_una_fila(self):
        filas = construir(ORIGEN, CLIENTES, CONDADOS, [], datetime(2026, 1, 1))

        assert len(filas) == 1

    def test_las_recargas_siguientes_no_escriben_nada(self):
        primera = construir(ORIGEN, CLIENTES, CONDADOS, [], datetime(2026, 1, 1))

        for dia in range(2, 8):
            siguiente = construir(ORIGEN, CLIENTES, CONDADOS, primera, datetime(2026, 1, dia))
            assert siguiente == [], f"la recarga del día {dia} escribió filas"

    def test_tras_muchas_recargas_sigue_habiendo_una_sola_version(self):
        # Si cada corrida abriera versión, un año de cargas diarias dejaría 365
        # filas por unidad y toda consulta histórica tendría que recorrerlas
        acumulado = construir(ORIGEN, CLIENTES, CONDADOS, [], datetime(2026, 1, 1))
        for dia in range(2, 30):
            acumulado += construir(ORIGEN, CLIENTES, CONDADOS, acumulado, datetime(2026, 1, dia))

        assert len(acumulado) == 1

    def test_cualquier_instante_resuelve_a_esa_unica_version(self):
        # El comportamiento observable es idéntico al de una dimensión sin
        # versionar: siempre se obtiene la misma fila
        unica = construir(ORIGEN, CLIENTES, CONDADOS, [], datetime(2026, 1, 1))[0]
        # La fila serializada trae texto; se compara sobre la versión en memoria
        from lib.dimensiones.versionado import INICIO_DESCONOCIDO

        en_memoria = [
            {**unica, "valido_desde": INICIO_DESCONOCIDO, "valido_hasta": None}
        ]

        for instante in (datetime(2020, 1, 1), datetime(2026, 6, 1), datetime(2030, 1, 1)):
            assert version_vigente_en(en_memoria, instante) is en_memoria[0]
