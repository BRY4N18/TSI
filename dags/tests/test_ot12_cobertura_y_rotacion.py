"""T037 y T038 — la cobertura crítica y la rotación de flota.

Las dos vigilan el mismo error con dos caras: **omitir el caso peor**.

* Un condado sin vecinos declarados es la situación más grave que la cobertura
  crítica puede reportar, y es la que desaparece si se une con la vecindad en vez
  de leerla como atributo.
* Una unidad dada de baja a mitad de período cuenta **hasta su baja**: ni el
  período entero, que diría que estuvo disponible todo el mes, ni cero, que la
  borraría del mes en que sí trabajó.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    PARTICION_DE_PRUEBA,
    ejecutar_red_operativa,
    requiere_modelo,
)

from lib.clickhouse_http_client import execute_clickhouse, query_clickhouse  # noqa: E402

#: Condados propios de la prueba, fuera del rango de los reales (1 y 2).
CON_VECINOS = 9001
SIN_VECINOS = 9002


def _calle(idcalle: int, idcondado: int, condado: str, vecinos: list[int]) -> dict:
    return {
        "idcalle": idcalle,
        "calle": f"Calle {idcalle}",
        "idciudad": idcalle,
        "ciudad": "Ciudad de prueba",
        "idcondado": idcondado,
        "condado": condado,
        "idestado": 99,
        "estado": "Estado de prueba",
        "idpais": 99,
        "pais": "Pais de prueba",
        "condados_vecinos": vecinos,
        "idregionoperativa": None,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def _unidad(idunidad: int, idcondado: int) -> dict:
    return {
        "sk_unidad": 980000 + idunidad,
        "idunidademergencia": idunidad,
        "placa": f"COB-{idunidad}",
        "idcliente": 1,
        "proveedor": "Proveedor de prueba",
        "idcondado": idcondado,
        "condado": "X",
        "fecha_alta": None,
        "tuvo_primer_acceso": 1,
        "valido_desde": "1970-01-01 00:00:00",
        "valido_hasta": None,
        "es_vigente": 1,
        "inicio_es_real": 0,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def _insertar(tabla: str, filas: list[dict]) -> None:
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in filas)
    execute_clickhouse(f"INSERT INTO {tabla} FORMAT JSONEachRow\n{payload}")


def _limpiar() -> None:
    for tabla, condicion in (
        ("dim_geografia", "idcalle >= 9000"),
        ("dim_unidad", "idunidademergencia >= 9000"),
    ):
        execute_clickhouse(
            f"ALTER TABLE {tabla} DELETE WHERE {condicion} SETTINGS mutations_sync = 2"
        )
    execute_clickhouse(
        f"ALTER TABLE hecho_baja_unidad DROP PARTITION {PARTICION_DE_PRUEBA}"
    )


@pytest.fixture
def escenario():
    _limpiar()
    yield
    _limpiar()


@requiere_modelo
class TestUnCondadoSinVecinosAparece:
    """T037 — es la situación más grave, no un caso a omitir (SC-008)."""

    def test_el_condado_sin_vecinos_sale_en_el_informe_y_marcado(self, escenario):
        """⚠️ El fallo que esto impide.

        La versión natural de la consulta une con la vecindad y se queda con lo
        que casa. Eso hace desaparecer justamente el condado que no tiene ninguno
        — el informe de cobertura crítica dejaría fuera la cobertura más crítica.

        Por eso `condados_vecinos` es un **atributo** de `dim_geografia` y no una
        unión: un array vacío es un valor, no una fila que falta.
        """
        _insertar("dim_geografia", [
            _calle(9001, CON_VECINOS, "Con vecinos", [SIN_VECINOS]),
            _calle(9002, SIN_VECINOS, "Sin vecinos", []),
        ])

        filas = {
            f["condado"]: f
            for f in ejecutar_red_operativa("ot12_condados_cobertura_critica", umbral_unidades=5)
        }

        assert "Sin vecinos" in filas, (
            "el condado sin vecinos desapareció del informe: la consulta está "
            "uniendo con la vecindad en vez de leerla como atributo"
        )
        assert filas["Sin vecinos"]["sin_alternativas"] == 1
        assert filas["Con vecinos"]["sin_alternativas"] == 0

    def test_cero_unidades_vecinas_no_es_lo_mismo_que_no_tener_vecinos(self, escenario):
        """Con vecinos declarados y ninguna unidad en ellos, hay a quién llamar.

        Sin vecinos, no. Las dos situaciones dan `unidades_vecinas = 0` y son
        distintas: por eso se publica `sin_alternativas` aparte y no se deduce
        del conteo.
        """
        _insertar("dim_geografia", [
            _calle(9001, CON_VECINOS, "Con vecinos vacios", [SIN_VECINOS]),
            _calle(9002, SIN_VECINOS, "Sin vecinos", []),
        ])

        filas = {
            f["condado"]: f
            for f in ejecutar_red_operativa("ot12_condados_cobertura_critica", umbral_unidades=5)
        }

        assert filas["Con vecinos vacios"]["unidades_vecinas"] == 0
        assert filas["Con vecinos vacios"]["sin_alternativas"] == 0
        assert filas["Sin vecinos"]["sin_alternativas"] == 1

    def test_el_umbral_aplicado_viaja_en_la_respuesta(self, escenario):
        """No es decoración: el origen no define ningún umbral.

        Quien lea «2 condados críticos» tiene que poder ver contra qué número se
        midió, o esa cifra pasaría por una política de la empresa.
        """
        _insertar("dim_geografia", [_calle(9001, CON_VECINOS, "Uno", [])])

        fila = ejecutar_red_operativa("ot12_condados_cobertura_critica", umbral_unidades=7)[0]

        assert fila["umbral_aplicado"] == 7

    def test_un_condado_con_bastantes_unidades_no_es_critico(self, escenario):
        _insertar("dim_geografia", [_calle(9001, CON_VECINOS, "Cubierto", [])])
        _insertar("dim_unidad", [_unidad(9001 + i, CON_VECINOS) for i in range(6)])

        criticos = {
            f["condado"]
            for f in ejecutar_red_operativa("ot12_condados_cobertura_critica", umbral_unidades=5)
        }

        assert "Cubierto" not in criticos


@requiere_modelo
class TestLaRotacionCuentaHastaLaBaja:
    """T038 — ni el período entero ni cero (FR-012)."""

    def _baja(self, idbaja: int, tipo: str = "Normal", dias: int | None = None) -> dict:
        return {
            "idbaja": idbaja,
            "fecha": FECHA_DE_PRUEBA,
            "fechahora": f"{FECHA_DE_PRUEBA} 12:00:00",
            "sk_unidad": 0,
            "idunidademergencia": 9001,
            "unidad": "ROT-1",
            "proveedor": "Proveedor de prueba",
            "tipo_baja": tipo,
            "motivo": "prueba",
            "con_caso_en_curso": 0,
            "dias_en_flota": dias,
            "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        }

    def test_la_baja_cuenta_en_el_periodo_en_que_ocurrio(self, escenario):
        _insertar("hecho_baja_unidad", [self._baja(1, dias=30)])

        fila = ejecutar_red_operativa("ot12_rotacion_flota")[0]

        assert fila["bajas"] == 1
        assert fila["mediana_dias_en_flota"] == 30

    def test_una_antiguedad_desconocida_es_ausente_y_no_cero(self, escenario):
        """Un cero afirmaría que se dio de baja el mismo día que entró.

        Es una anomalía operativa digna de mirarse, y fabricarla llenaría el
        informe de unidades fantasma con vida de un día.
        """
        _insertar("hecho_baja_unidad", [self._baja(1, dias=None)])

        fila = ejecutar_red_operativa("ot12_rotacion_flota")[0]

        assert fila["bajas"] == 1
        assert fila["con_antiguedad_conocida"] == 0
        assert fila["mediana_dias_en_flota"] is None

    def test_los_tres_desenlaces_se_distinguen(self, escenario):
        """`Forzada` dejó un caso sin unidad; `Forzada_con_reasignación` lo pasó.

        Agruparlas haría que un proveedor con buena reasignación pareciera igual
        de malo que uno que abandona casos.
        """
        _insertar("hecho_baja_unidad", [
            self._baja(1, "Normal"),
            self._baja(2, "Forzada"),
            self._baja(3, "Forzada_con_reasignación"),
        ])

        fila = {
            f["motivo"]: f for f in ejecutar_red_operativa("ot12_bajas_forzadas")
        }["prueba"]

        assert fila["normales"] == 1
        assert fila["forzadas"] == 1
        assert fila["forzadas_con_reasignacion"] == 1
        assert fila["pct_forzadas"] == pytest.approx(2 / 3, abs=1e-3)
