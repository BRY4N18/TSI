"""T024 — la prueba que justifica migrar la completitud (SC-002).

Es la razón de ser del módulo, así que conviene decir con precisión qué demuestra
y qué no.

El endpoint que sirve hoy este informe agrega **contra Pinot** y comprueba la
completitud con `idseveridad IS NOT NULL AND idcalle IS NOT NULL`. En Pinot no
hay nulos: una severidad ausente se guarda como el centinela `-2147483648`. La
condición es por tanto **siempre cierta**, y el informe responde `100 %` pase lo
que pase. Se comprobó empíricamente sobre los datos reales:

    SELECT COUNT(*), SUM(CASE WHEN idreferenciaestacion IS NOT NULL THEN 1 ELSE 0 END),
           MIN(idreferenciaestacion) FROM Fact_Accidente
    → 4252, 4252, -2147483648

Las 4252 filas cuentan como «no nulas» aunque el mínimo de la columna sea el
centinela. Ese es el defecto.

⚠️ **Con los datos de hoy el endpoint acierta por casualidad.** No hay ningún
caso al que le falte severidad o condado, así que la respuesta correcta *es*
100 %. El defecto está latente: no se manifiesta, y por eso no basta con comparar
las dos cifras — coinciden. La única forma de demostrarlo es **fabricar el caso
incompleto**, que es lo que hace esta prueba.

Escribe en una partición muy posterior a cualquier dato real y la descarta al
terminar, para no mover nunca las cifras que otra prueba está comprobando.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    PARTICION_DE_PRUEBA,
    requiere_modelo,
)

from lib.clickhouse_http_client import execute_clickhouse, query_clickhouse  # noqa: E402
from lib.consultas import cargar  # noqa: E402

CONSULTA = cargar("ot21_completitud_campos_criticos", departamento="emergencias")


def _caso(idaccidente: str, *, severidad: bool = True, ubicacion: bool = True) -> dict:
    """Un caso del período de prueba, al que se le puede quitar cada campo crítico."""
    return {
        "idaccidente": idaccidente,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_accidente": f"{FECHA_DE_PRUEBA} 10:00:00",
        "franja_horaria": "manana",
        "idcalle": 1 if ubicacion else None,
        "condado": "Cuauhtemoc" if ubicacion else None,
        "ciudad": "Ciudad de Mexico" if ubicacion else None,
        "idseveridad": 1 if severidad else None,
        "severidad": "Leve" if severidad else None,
        "fue_descartado": 0,
        "es_duplicado": 0,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def _cargar(casos: list[dict]) -> None:
    import json

    payload = "\n".join(json.dumps(c) for c in casos)
    execute_clickhouse(f"INSERT INTO hecho_accidente FORMAT JSONEachRow\n{payload}")


def _limpiar() -> None:
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


def _completitud() -> dict:
    filas = query_clickhouse(
        CONSULTA, params={"desde": FECHA_DE_PRUEBA, "hasta": FECHA_DE_PRUEBA}
    )
    return filas[0] if filas else {}


@pytest.fixture
def particion_limpia():
    _limpiar()
    yield
    _limpiar()


@requiere_modelo
class TestLaCompletitudPuedeBajarDelCienPorCiento:
    """SC-002. Si el porcentaje se quedara en 1.0000, la consulta heredó el defecto."""

    def test_un_caso_sin_severidad_baja_el_porcentaje(self, particion_limpia):
        _cargar([
            _caso("T024-completo-1"),
            _caso("T024-completo-2"),
            _caso("T024-sin-severidad", severidad=False),
        ])

        resultado = _completitud()

        assert resultado["casos"] == 3
        assert resultado["completos"] == 2
        # La afirmación que da nombre al módulo: **no** es 1.0000.
        assert resultado["pct_completitud"] == pytest.approx(2 / 3, abs=1e-4), (
            "la completitud no bajó del 100 % con un caso sin severidad: "
            "la consulta heredó el defecto que este módulo existe para corregir"
        )

    def test_un_caso_sin_ubicacion_tambien_baja_el_porcentaje(self, particion_limpia):
        # Los dos campos críticos cuentan. Comprobar solo la severidad dejaría
        # pasar una consulta que ignorase la ubicación.
        _cargar([_caso("T024-completo"), _caso("T024-sin-ubicacion", ubicacion=False)])

        resultado = _completitud()

        assert resultado["completos"] == 1
        assert resultado["pct_completitud"] == pytest.approx(0.5, abs=1e-4)

    def test_un_caso_al_que_le_faltan_los_dos_cuenta_una_sola_vez(self, particion_limpia):
        # Incompleto es incompleto: que falten dos campos no lo hace contar dos
        # veces contra el total, que es lo que pasaría si la consulta sumara una
        # condición por campo en vez de exigirlas juntas.
        _cargar([_caso("T024-completo"), _caso("T024-vacio", severidad=False, ubicacion=False)])

        resultado = _completitud()

        assert resultado["casos"] == 2
        assert resultado["completos"] == 1
        assert resultado["pct_completitud"] == pytest.approx(0.5, abs=1e-4)

    def test_una_calle_no_resoluble_cuenta_como_incompleto(self, particion_limpia):
        """La ubicación se juzga por `condado`, no por `idcalle`.

        Un caso puede traer una calle que **no está** en el catálogo geográfico:
        el modelo lo conserva, con `idcalle` puesto y la ubicación sin resolver.
        Ese caso no está completo, y comprobar `idcalle` lo daría por bueno —
        tendría un número donde hace falta un lugar.

        Sin esta prueba la distinción no está cubierta: en todos los demás casos
        de este fichero los dos campos van juntos, así que una consulta que
        mirara `idcalle` pasaría igual.
        """
        caso = _caso("T024-calle-huerfana")
        caso["idcalle"] = 999999  # existe en el hecho, no en la dimensión
        caso["condado"] = None
        caso["ciudad"] = None
        _cargar([_caso("T024-completo"), caso])

        resultado = _completitud()

        assert resultado["completos"] == 1, (
            "un caso con calle no resoluble se contó como completo: "
            "la consulta está mirando 'idcalle' en vez de 'condado'"
        )

    def test_todos_completos_sigue_dando_cien_por_ciento(self, particion_limpia):
        # La comprobación simétrica. Una consulta que devolviera siempre menos de
        # 1 pasaría todas las anteriores y estaría igual de rota, solo que hacia
        # el otro lado: daría una alarma permanente que nadie tardaría en ignorar.
        _cargar([_caso("T024-a"), _caso("T024-b")])

        assert _completitud()["pct_completitud"] == pytest.approx(1.0, abs=1e-4)


@requiere_modelo
class TestPeriodoSinCasos:
    def test_sin_casos_la_completitud_es_nula_y_no_cero(self, particion_limpia):
        """FR-017. Un período sin casos no tiene una completitud del 0 %.

        No tiene completitud. La diferencia no es sutil en pantalla: `0 %` es una
        alarma —hubo casos y ninguno estaba completo— y el nulo es un hueco. Un
        denominador cero que devolviera `0` convertiría cada día tranquilo en una
        emergencia de calidad de datos.
        """
        resultado = _completitud()

        assert resultado == {} or resultado.get("pct_completitud") is None
