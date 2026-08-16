"""El caso ancla: **el pasado no se reescribe** (T034, SC-003). ⚠️

Es la única prueba de la serie que valida una **tesis de diseño** y no un
requisito. Si falla, el modelo no ha resuelto nada y es el diseño anterior con
más pasos.

El defecto que reproduce
------------------------
El origen guarda el proveedor **actual** de cada unidad y nada historiza su
cambio. Con ese dato, un informe de rendimiento por proveedor atribuye al
proveedor de hoy todo el trabajo de ayer: cambiar de proveedor **reescribe seis
meses de historia**, y la cifra parece correcta.

Por qué la unidad es sintética
------------------------------
El origen tiene **un solo proveedor**: las 18 unidades son de `idcliente = 1`.
Una prueba escrita contra los datos reales pasaría **en vacío** —no habría dos
proveedores que distinguir— y daría una confianza falsa sobre justo la propiedad
que más importa.

Así que la prueba fabrica el escenario y lo hace pasar por **la tubería real**:
el mismo versionado, la misma resolución histórica y el mismo constructor del
hecho que usa la carga de producción. Lo sintético son los datos, no el camino.

Escribe en una partición muy posterior a cualquier dato real y la descarta al
terminar.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import PARTICION_DE_PRUEBA, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import (  # noqa: E402
    execute_clickhouse,
    insert_rows,
    query_clickhouse,
)
from lib.dimensiones.dim_unidad import construir as construir_unidades  # noqa: E402
from lib.hechos.hecho_despacho import construir as construir_despachos  # noqa: E402
from lib.tipos_almacen import ajustar_tipos  # noqa: E402

#: Fuera del rango de identificadores reales del origen (18 unidades).
UNIDAD = 9001

# ⚠️ Todas las fechas caen dentro de la partición de prueba, y no es cosmético:
# con fechas de 2026 los despachos sintéticos aterrizan en particiones REALES, la
# limpieza —que descarta la de prueba— no los alcanza, y la prueba deja dos filas
# falsas en el hecho para siempre. Ocurrió: el recuento pasó de 4 314 a 4 316.
PRIMERA_CARGA = datetime(2099, 12, 1, 0, 0, 0)
CAMBIO_DE_PROVEEDOR = datetime(2099, 12, 15, 0, 0, 0)

ANTES_DEL_CAMBIO = datetime(2099, 12, 5, 10, 0, 0)
DESPUES_DEL_CAMBIO = datetime(2099, 12, 25, 10, 0, 0)

PROVEEDOR_A = "Proveedor Antiguo"
PROVEEDOR_B = "Proveedor Nuevo"


def _unidad_origen(idcliente):
    return [
        {
            "idunidademergencia": UNIDAD,
            "unidademergencia": "Ambulancia de prueba",
            "placa": "TEST-001",
            "tipounidademergencia": "Ambulancia",
            "capacidad": "4",
            "idcliente": idcliente,
            "idcondado": 1,
            "zonacobertura": "Norte",
        }
    ]


CLIENTES = [
    {"idcliente": 9001, "nombre": PROVEEDOR_A, "razon_social": PROVEEDOR_A},
    {"idcliente": 9002, "nombre": PROVEEDOR_B, "razon_social": PROVEEDOR_B},
]

CONDADOS = [{"idcondado": 1, "condado": "Cuauhtemoc"}]


def _despacho(iddespacho, momento):
    return {
        "iddespacho": iddespacho,
        "idaccidente": f"PRUEBA-ANCLA-{iddespacho}",
        "idunidademergencia": UNIDAD,
        "idorigendespacho": 1,
        "retiro_forzado": False,
        "fechahoradespacho": int(momento.timestamp() * 1000),
        "fechahorallegada": None,
        "fechahoraretiro": None,
    }


def _datos_del_hecho(versiones):
    return {
        "despachos": [_despacho(90001, ANTES_DEL_CAMBIO), _despacho(90002, DESPUES_DEL_CAMBIO)],
        "historial": [],
        "accidentes": [],
        "dim_unidad": versiones,
        "dim_origen": [{"idorigendespacho": 1, "origen": "Automatico"}],
        "dim_severidad": [],
        "dim_geografia": [],
    }


@pytest.fixture
def escenario_limpio():
    def limpiar():
        execute_clickhouse(f"ALTER TABLE hecho_despacho DROP PARTITION {PARTICION_DE_PRUEBA}")
        # Borrado por condición, que la carga tiene prohibido. Aquí es la única
        # vía: las dimensiones no están particionadas, y limpiar una unidad de
        # prueba sin arrasar la tabla entera no tiene otra forma. Es una mutación
        # sobre 2 filas en una prueba, no un patrón de carga.
        #
        # `mutations_sync = 2` no es opcional: sin él la mutación es asíncrona y
        # la prueba insertaría sus filas mientras el borrado aún no ha ocurrido.
        # Pasaría casi siempre y fallaría de vez en cuando, que es la peor clase
        # de prueba: la que entrena a reejecutar en vez de investigar.
        execute_clickhouse(
            f"ALTER TABLE dim_unidad DELETE WHERE idunidademergencia = {UNIDAD} "
            "SETTINGS mutations_sync = 2"
        )

    limpiar()
    yield
    limpiar()


class TestSobreLaLogica:
    """Sin almacén: es donde vive la tesis, y debe poder comprobarse siempre."""

    def _versiones_tras_el_cambio(self):
        primera = construir_unidades(
            _unidad_origen(9001), CLIENTES, CONDADOS, [], PRIMERA_CARGA
        )
        tras_cambio = construir_unidades(
            _unidad_origen(9002), CLIENTES, CONDADOS, primera, CAMBIO_DE_PROVEEDOR
        )
        # La versión cerrada sustituye a la que estaba abierta.
        return [tras_cambio[0], tras_cambio[1]]

    def test_el_despacho_anterior_conserva_su_proveedor(self):
        # Arrange: la unidad cambia de proveedor DESPUÉS del primer despacho
        versiones = self._versiones_tras_el_cambio()

        # Act
        filas = {f["iddespacho"]: f for f in construir_despachos(_datos_del_hecho(versiones), CAMBIO_DE_PROVEEDOR)}

        # Assert: ⚠️ si esto sale «Proveedor Nuevo», el modelo no resolvió nada
        assert filas[90001]["proveedor"] == PROVEEDOR_A

    def test_el_despacho_posterior_usa_el_proveedor_nuevo(self):
        versiones = self._versiones_tras_el_cambio()

        filas = {f["iddespacho"]: f for f in construir_despachos(_datos_del_hecho(versiones), CAMBIO_DE_PROVEEDOR)}

        assert filas[90002]["proveedor"] == PROVEEDOR_B

    def test_los_dos_despachos_apuntan_a_versiones_distintas(self):
        # Es el mecanismo que hace posible lo anterior: no es que el proveedor se
        # copie bien, es que cada hecho apunta a una fila distinta de la dimensión
        versiones = self._versiones_tras_el_cambio()

        filas = {f["iddespacho"]: f for f in construir_despachos(_datos_del_hecho(versiones), CAMBIO_DE_PROVEEDOR)}

        assert filas[90001]["sk_unidad"] != filas[90002]["sk_unidad"]

    def test_sin_versionado_ambos_verian_el_proveedor_actual(self):
        # Reproduce el defecto para que la prueba anterior signifique algo: con
        # una sola versión —el estado actual— los dos despachos se atribuyen al
        # proveedor nuevo, incluido el de marzo. Es lo que hoy hace el informe.
        solo_actual = construir_unidades(
            _unidad_origen(9002), CLIENTES, CONDADOS, [], PRIMERA_CARGA
        )

        filas = {f["iddespacho"]: f for f in construir_despachos(_datos_del_hecho(solo_actual), CAMBIO_DE_PROVEEDOR)}

        assert filas[90001]["proveedor"] == PROVEEDOR_B
        assert filas[90002]["proveedor"] == PROVEEDOR_B


@requiere_modelo
class TestSobreElAlmacen:
    def test_el_pasado_sigue_atribuido_al_proveedor_anterior(self, escenario_limpio):
        # Arrange: primera carga, con el proveedor A
        primera = construir_unidades(
            _unidad_origen(9001), CLIENTES, CONDADOS, [], PRIMERA_CARGA
        )
        insert_rows("dim_unidad", ajustar_tipos("dim_unidad", primera))

        vigentes = query_clickhouse(
            f"SELECT * FROM dim_unidad FINAL WHERE idunidademergencia = {UNIDAD} AND es_vigente = 1"
        )
        despachos = construir_despachos(_datos_del_hecho(vigentes), PRIMERA_CARGA)
        insert_rows("hecho_despacho", ajustar_tipos("hecho_despacho", despachos))

        # Act: cambia el proveedor en el origen y se recarga todo
        tras_cambio = construir_unidades(
            _unidad_origen(9002), CLIENTES, CONDADOS, vigentes, CAMBIO_DE_PROVEEDOR
        )
        insert_rows("dim_unidad", ajustar_tipos("dim_unidad", tras_cambio))

        versiones = query_clickhouse(
            f"SELECT * FROM dim_unidad FINAL WHERE idunidademergencia = {UNIDAD}"
        )
        execute_clickhouse(f"ALTER TABLE hecho_despacho DROP PARTITION {PARTICION_DE_PRUEBA}")
        recargados = construir_despachos(_datos_del_hecho(versiones), CAMBIO_DE_PROVEEDOR)
        insert_rows("hecho_despacho", ajustar_tipos("hecho_despacho", recargados))

        # Assert: tras la recarga, el despacho de marzo NO se movió al proveedor nuevo
        atribucion = {
            f["iddespacho"]: f["proveedor"]
            for f in query_clickhouse(
                "SELECT iddespacho, proveedor FROM hecho_despacho FINAL "
                f"WHERE idunidademergencia = {UNIDAD}"
            )
        }
        assert atribucion[90001] == PROVEEDOR_A
        assert atribucion[90002] == PROVEEDOR_B

    def test_no_deja_filas_sinteticas_fuera_de_la_particion_de_prueba(self, escenario_limpio):
        # La prueba anterior escribe en el hecho de producción. Si sus fechas
        # cayeran fuera de la partición de prueba, la limpieza no las alcanzaría
        # y el hecho quedaría con filas falsas **de forma permanente** — un
        # informe contaría despachos de una unidad que no existe. Pasó, con
        # fechas de 2026, y por eso esta comprobación está aquí.
        insert_rows(
            "hecho_despacho",
            ajustar_tipos(
                "hecho_despacho",
                construir_despachos(
                    _datos_del_hecho(
                        construir_unidades(_unidad_origen(9001), CLIENTES, CONDADOS, [], PRIMERA_CARGA)
                    ),
                    PRIMERA_CARGA,
                ),
            ),
        )

        fuera = query_clickhouse(
            "SELECT count() AS n FROM hecho_despacho "
            f"WHERE idunidademergencia = {UNIDAD} AND toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
        )
        assert int(fuera[0]["n"]) == 0
