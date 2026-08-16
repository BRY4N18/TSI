"""T015 — el repositorio ejecuta, parametriza y no escribe nunca.

Las tres propiedades se comprueban sobre lo que el repositorio **le pide al
cliente**, no sobre el resultado: un repositorio que concatenara el rango en el
SQL devolvería exactamente las mismas filas que uno que lo parametriza. La
diferencia solo se ve en la llamada.
"""

from __future__ import annotations

import pytest

from core.repositories.informes_tacticos.catalogo_consultas import ConsultaNoEncontrada
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "emergencias"
UNA_CONSULTA = "ot21_distribucion_severidad"


class ClienteFalso:
    """Registra la llamada en vez de ejecutarla."""

    def __init__(self, filas=None):
        self.filas = filas if filas is not None else []
        self.llamadas = []

    def query(self, sql, params=None, settings=None):
        self.llamadas.append({"sql": sql, "params": params, "settings": settings})
        return self.filas

    @property
    def ultima(self):
        return self.llamadas[-1]


@pytest.fixture
def cliente():
    return ClienteFalso()


class TestEjecuta:
    def test_carga_el_sql_del_catalogo_y_lo_pasa_tal_cual(self, cliente):
        ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert "FROM hecho_accidente FINAL" in cliente.ultima["sql"]

    def test_devuelve_las_filas_del_almacen(self):
        cliente = ClienteFalso([{"severidad": "Leve", "casos": 1664}])

        filas = ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert filas == [{"severidad": "Leve", "casos": 1664}]

    def test_un_nombre_fuera_del_catalogo_no_llega_al_almacen(self, cliente):
        # El catálogo es el conjunto cerrado de lo que se puede preguntar. Un
        # nombre que no está en él tiene que morir **antes** de la conexión.
        with pytest.raises(ConsultaNoEncontrada):
            ModeloRepository(cliente).ejecutar("no_existe", departamento=DEPARTAMENTO)

        assert cliente.llamadas == []


class TestParametriza:
    def test_el_rango_viaja_como_parametro_y_no_dentro_del_sql(self, cliente):
        ModeloRepository(cliente).ejecutar(
            UNA_CONSULTA,
            departamento=DEPARTAMENTO,
            parametros={"desde": "2026-01-01", "hasta": "2026-12-31"},
        )

        assert cliente.ultima["params"] == {"desde": "2026-01-01", "hasta": "2026-12-31"}
        # Y, sobre todo, que el valor **no** acabó pegado a la consulta: si lo
        # estuviera, un valor que contenga SQL sería SQL.
        assert "2026-01-01" not in cliente.ultima["sql"]

    def test_la_consulta_declara_el_tipo_del_parametro(self, cliente):
        # `{desde:Date}` y no `{desde}`: es el tipo lo que hace que el servidor
        # rechace un valor que no sea una fecha, en vez de interpretarlo.
        ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert "{desde:Date}" in cliente.ultima["sql"]


class TestNoEscribe:
    def test_toda_consulta_va_con_readonly(self, cliente):
        # La garantía la impone el servidor, no la buena voluntad de quien añada
        # la siguiente consulta: con `readonly=1` un INSERT falla en ClickHouse.
        ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert cliente.ultima["settings"]["readonly"] == "1"

    def test_toda_consulta_lleva_tope_de_tiempo(self, cliente):
        ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert int(cliente.ultima["settings"]["max_execution_time"]) > 0

    def test_ninguna_consulta_del_catalogo_es_de_escritura(self):
        # Lo anterior comprueba el ajuste; esto comprueba el catálogo. Las dos
        # hacen falta: `readonly` protege de lo que se añada mañana, y esto de lo
        # que ya está escrito.
        from core.repositories.informes_tacticos.catalogo_consultas import cargar, listar

        prohibidas = ("INSERT", "ALTER", "DROP", "TRUNCATE", "CREATE", "OPTIMIZE")
        for nombre in listar(DEPARTAMENTO):
            cuerpo = "\n".join(
                l for l in cargar(nombre, departamento=DEPARTAMENTO).splitlines()
                if not l.strip().startswith("--")
            ).upper()
            for palabra in prohibidas:
                assert palabra not in cuerpo, f"'{nombre}' contiene '{palabra}'"


class TestTiposDeSalida:
    """Un conteo tiene que llegar como número, no como su texto.

    ⚠️ Esta prueba va **contra ClickHouse de verdad**, y es deliberado: el
    defecto que vigila lo introduce el serializador del almacén, no el
    repositorio. Un cliente de mentira devuelve el tipo que decida quien escribe
    la prueba, así que aquí un doble solo comprobaría mis suposiciones.

    Fue así como se encontró: `count()` es `UInt64`, ClickHouse entrecomilla los
    enteros de 64 bits por defecto, y el conteo llegaba como `"1664"`. No falla
    en ninguna parte —la pantalla pinta igual un número que su texto— hasta que
    algo los suma y JavaScript los concatena.
    """

    @pytest.mark.integration
    def test_los_conteos_llegan_como_numeros(self):
        cliente = _cliente_real()
        if cliente is None:
            pytest.skip("ClickHouse no disponible")

        filas = ModeloRepository(cliente).ejecutar(
            UNA_CONSULTA,
            departamento=DEPARTAMENTO,
            parametros={"desde": "2026-01-01", "hasta": "2026-12-31"},
        )
        if not filas:
            pytest.skip("el almacén no tiene datos en el período de prueba")

        assert isinstance(filas[0]["casos"], int), (
            f"'casos' llegó como {type(filas[0]['casos']).__name__}: "
            f"sumarlo en el navegador concatenaría en vez de sumar"
        )


def _cliente_real():
    from requests.exceptions import RequestException

    from core.clickhouse.client import ClickHouseClient

    cliente = ClickHouseClient()
    try:
        cliente.query("SELECT 1")
    except RequestException:
        return None
    return cliente


class TestAusenciaNoEsCero:
    def test_un_nulo_del_almacen_sigue_siendo_nulo(self):
        # FR-017. Un porcentaje nulo es "no hay dato"; un 0 es "hubo casos y
        # ninguno cumplía". Rellenar el nulo con cero convierte silencio en
        # catástrofe.
        cliente = ClienteFalso([{"casos": 0, "pct_completitud": None}])

        filas = ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert filas[0]["pct_completitud"] is None

    def test_un_cero_legitimo_sigue_siendo_cero(self):
        # La comprobación simétrica: convertir el cero en nulo "por si acaso"
        # esconde la alarma en vez de darla.
        cliente = ClienteFalso([{"casos": 12, "pct_completitud": 0.0}])

        filas = ModeloRepository(cliente).ejecutar(UNA_CONSULTA, departamento=DEPARTAMENTO)

        assert filas[0]["pct_completitud"] == 0.0
