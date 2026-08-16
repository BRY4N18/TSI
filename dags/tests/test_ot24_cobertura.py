"""T066 y T067 — cobertura de evidencia y latencia de sincronización.

⚠️ **Con datos sintéticos, y es obligatorio.** El origen tiene 3 fotos y 51
notas: con esas cifras una consulta rota y una fuente pobre dan el mismo
resultado —casi cero— y la prueba no distinguiría entre las dos.
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
    cargar_casos,
    caso,
    ejecutar_informe,
    limpiar_particion,
    requiere_modelo,
)

from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402


def evidencia(
    idevidencia: int,
    idaccidente: str,
    *,
    tipo: str = "foto",
    segundos_hasta_sincronia: int | None = None,
    idunidad: int = 7,
) -> dict:
    captura = f"{FECHA_DE_PRUEBA} 10:00:00"
    sincronia = None
    if segundos_hasta_sincronia is not None:
        minutos, segundos = divmod(segundos_hasta_sincronia, 60)
        sincronia = f"{FECHA_DE_PRUEBA} 10:{minutos:02d}:{segundos:02d}"
    return {
        "idevidencia": idevidencia,
        "tipo": tipo,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_captura": captura,
        "fechahora_sincronia": sincronia,
        "idaccidente": idaccidente,
        "sk_unidad": 900000 + idunidad,
        "idunidademergencia": idunidad,
        "proveedor": "Proveedor de prueba",
        "idseveridad": 1,
        "severidad": "Leve",
        "condado": "Cuauhtemoc",
        "segundos_hasta_sincronia": segundos_hasta_sincronia,
        "categoria_nota": "Condiciones del sitio" if tipo == "nota" else None,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cargar_evidencias(filas: list[dict]) -> None:
    payload = "\n".join(json.dumps(f) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_evidencia FORMAT JSONEachRow\n{payload}")


def limpiar_evidencias() -> None:
    execute_clickhouse(
        f"ALTER TABLE hecho_evidencia DROP PARTITION {PARTICION_DE_PRUEBA}"
    )


@pytest.fixture
def escenario():
    limpiar_particion()
    limpiar_evidencias()
    yield
    limpiar_particion()
    limpiar_evidencias()


def _cobertura() -> dict:
    filas = ejecutar_informe("ot24_cobertura_evidencia")
    return filas[0] if filas else {}


def _latencia(tipo: str) -> dict:
    filas = [f for f in ejecutar_informe("ot24_latencia_sincronizacion") if f["tipo"] == tipo]
    return filas[0] if filas else {}


@requiere_modelo
class TestLaCoberturaRepartelosCuatroGrupos:
    def test_cuatro_casos_uno_de_cada_se_reparten_como_corresponde(self, escenario):
        cargar_casos([
            caso("T066-foto"), caso("T066-nota"), caso("T066-ambas"), caso("T066-nada"),
        ])
        cargar_evidencias([
            evidencia(1, "T066-foto", tipo="foto"),
            evidencia(2, "T066-nota", tipo="nota"),
            evidencia(3, "T066-ambas", tipo="foto"),
            evidencia(4, "T066-ambas", tipo="nota"),
        ])

        fila = _cobertura()

        assert fila["casos"] == 4
        assert fila["solo_foto"] == 1
        assert fila["solo_nota"] == 1
        assert fila["foto_y_nota"] == 1
        assert fila["sin_evidencia"] == 1

    def test_los_cuatro_grupos_suman_el_total(self, escenario):
        # Si un caso cayera en dos grupos, los porcentajes sumarían más de 100 %
        # y el reparto dejaría de leerse.
        cargar_casos([caso(f"T066-{i}") for i in range(4)])
        cargar_evidencias([
            evidencia(1, "T066-0", tipo="foto"),
            evidencia(2, "T066-0", tipo="nota"),
            evidencia(3, "T066-1", tipo="foto"),
        ])

        fila = _cobertura()
        suma = fila["solo_foto"] + fila["solo_nota"] + fila["foto_y_nota"] + fila["sin_evidencia"]

        assert suma == fila["casos"]

    def test_un_caso_sin_ninguna_evidencia_aparece(self, escenario):
        """⚠️ Es el motivo del informe, y el fallo más fácil de cometer.

        Partiendo de las evidencias en vez de los casos, un caso sin ninguna no
        aparecería en ninguna fila y la cobertura saldría del 100 % siempre: el
        informe diría que todo está documentado justamente porque no ve lo que
        falta.
        """
        cargar_casos([caso("T066-solo")])

        fila = _cobertura()

        assert fila["casos"] == 1, "el caso sin evidencia desapareció del informe"
        assert fila["sin_evidencia"] == 1
        assert fila["pct_con_alguna"] == 0.0

    def test_varias_fotos_del_mismo_caso_no_lo_cuentan_varias_veces(self, escenario):
        cargar_casos([caso("T066-uno")])
        cargar_evidencias([evidencia(i, "T066-uno", tipo="foto") for i in range(1, 6)])

        fila = _cobertura()

        assert fila["casos"] == 1
        assert fila["solo_foto"] == 1


@requiere_modelo
class TestLaLatenciaDeSincronizacion:
    def test_una_evidencia_sin_sincronizar_no_cuenta_como_latencia_cero(self, escenario):
        """⚠️ T067. Si contara como cero, **cuanto peor fuera la sincronización
        mejor saldría la latencia**: cada evidencia atascada bajaría la mediana.
        """
        cargar_casos([caso("T067-a")])
        cargar_evidencias([
            evidencia(1, "T067-a", tipo="foto", segundos_hasta_sincronia=600),
            evidencia(2, "T067-a", tipo="foto", segundos_hasta_sincronia=None),
        ])

        fila = _latencia("foto")

        assert fila["evidencias"] == 2
        assert fila["pendientes"] == 1
        assert fila["sincronizadas"] == 1
        assert fila["mediana_seg"] == 600, (
            f"la mediana salió {fila['mediana_seg']}: la pendiente entró en el "
            f"cálculo como cero en vez de quedarse fuera"
        )

    def test_los_pendientes_se_publican_junto_a_la_mediana(self, escenario):
        # Las dos cifras juntas son lo que permite leer la latencia: una mediana
        # excelente sobre dos evidencias de mil no dice nada de las novecientas
        # noventa y ocho que faltan.
        cargar_casos([caso("T067-a")])
        cargar_evidencias([evidencia(1, "T067-a", segundos_hasta_sincronia=None)])

        fila = _latencia("foto")

        assert fila["pendientes"] == 1
        assert fila["mediana_seg"] is None, (
            "sin ninguna evidencia sincronizada la mediana es ausente, no cero"
        )

    def test_las_notas_se_desglosan_aparte_de_las_fotos(self, escenario):
        """El origen no tiene sincronización para las notas, así que **todas**
        son pendientes. Sin el desglose por tipo esa cifra escondería la de las
        fotos y el informe parecería decir que la sincronización va fatal.
        """
        cargar_casos([caso("T067-a")])
        cargar_evidencias([
            evidencia(1, "T067-a", tipo="foto", segundos_hasta_sincronia=60),
            evidencia(2, "T067-a", tipo="nota", segundos_hasta_sincronia=None),
            evidencia(3, "T067-a", tipo="nota", segundos_hasta_sincronia=None),
        ])

        assert _latencia("foto")["mediana_seg"] == 60
        assert _latencia("nota")["pendientes"] == 2
        assert _latencia("nota")["mediana_seg"] is None
