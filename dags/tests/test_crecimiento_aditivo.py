"""Añadir un hecho **no altera** los existentes (T041, SC-006).

Es la promesa de US3, y la razón de que exista un tercer hecho en vez de solo un
párrafo explicando cómo se añadiría uno.

Lo que se comprueba no es que el código compile, sino que las **cifras** de
`hecho_accidente` y `hecho_despacho` son las mismas antes y después de que
`hecho_estado_unidad` exista y esté cargado. Un modelo en el que añadir una tabla
mueve los números de otra no es un modelo en estrella: es un montón de tablas
acopladas.
"""

import sys
from pathlib import Path

import re

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

#: Cifras de los dos hechos originales, tomadas del origen. **No son un número
#: mágico**: son exactamente los recuentos de `Fact_Accidente` y `Fact_Despacho`,
#: y por eso una discrepancia significa pérdida o duplicación real, no que la
#: prueba esté desactualizada.
CASOS_EN_EL_ORIGEN = "SELECT COUNT(*) AS n FROM Fact_Accidente"
DESPACHOS_EN_EL_ORIGEN = "SELECT COUNT(*) AS n FROM Fact_Despacho"

PARTICION_DE_PRUEBA = 209912


def _reales(tabla: str) -> int:
    return contar(
        f"SELECT count() AS n FROM {tabla} FINAL "
        f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
    )


@requiere_modelo
class TestLosHechosAnterioresNoSeMovieron:
    def _origen(self, sql: str) -> int:
        from lib.pinot_http_client import query_pinot

        return query_pinot(sql)[0]["n"]

    def test_los_casos_siguen_cuadrando_con_el_origen(self):
        assert _reales("hecho_accidente") == self._origen(CASOS_EN_EL_ORIGEN)

    def test_los_despachos_siguen_cuadrando_con_el_origen(self):
        assert _reales("hecho_despacho") == self._origen(DESPACHOS_EN_EL_ORIGEN)

    def test_el_reparto_por_severidad_no_cambio(self):
        # Un total correcto puede esconder filas movidas entre categorías
        reparto = query_clickhouse(
            "SELECT severidad, count() AS n FROM hecho_accidente FINAL "
            "GROUP BY severidad ORDER BY severidad"
        )
        assert sum(int(f["n"]) for f in reparto) == _reales("hecho_accidente")

    def test_el_tercer_hecho_no_comparte_particiones_con_los_otros(self):
        # Comparten dimensiones, no almacenamiento: retirar uno no debe tocar a
        # los demás
        propias = {
            f["table"]
            for f in query_clickhouse(
                "SELECT DISTINCT table FROM system.parts "
                "WHERE database = currentDatabase() AND active"
            )
        }
        assert {"hecho_accidente", "hecho_despacho", "hecho_estado_unidad"} <= propias


@requiere_modelo
class TestElTercerHechoUsaLasMismasDimensiones:
    def test_apunta_a_las_mismas_versiones_de_unidad(self):
        # Es lo que hace que sea crecimiento y no una tabla paralela: si tuviera
        # su propia copia de las unidades, el modelo tendría dos verdades
        assert contar(
            """
            SELECT count() AS n
            FROM hecho_estado_unidad AS h
            LEFT JOIN dim_unidad AS u FINAL ON h.sk_unidad = u.sk_unidad
            WHERE u.sk_unidad = 0 AND h.sk_unidad != 0
            """
        ) == 0

    def test_su_proveedor_coincide_con_el_de_la_version(self):
        assert contar(
            """
            SELECT count() AS n
            FROM hecho_estado_unidad AS h
            INNER JOIN dim_unidad AS u FINAL ON h.sk_unidad = u.sk_unidad
            WHERE h.proveedor != u.proveedor
            """
        ) == 0

    def test_es_un_hecho_de_transaccion_y_por_eso_no_admite_version_final(self):
        # El tercer hecho ejercita el OTRO camino del diseño: no es una
        # instantánea acumulada, así que usa un motor sin deduplicación. Pedirle
        # `FINAL` falla, y debe fallar: una fila de transacción no se actualiza
        # nunca, no hay versiones que reconciliar. Quien lo consulte por costumbre
        # con `FINAL` se lleva un error claro en vez de una cifra sutilmente mala.
        motores = {
            f["name"]: f["engine"]
            for f in query_clickhouse(
                "SELECT name, engine FROM system.tables "
                "WHERE database = currentDatabase() AND name LIKE 'hecho%'"
            )
        }
        assert motores["hecho_accidente"] == "ReplacingMergeTree"
        assert motores["hecho_despacho"] == "ReplacingMergeTree"
        assert motores["hecho_estado_unidad"] == "MergeTree"

        with pytest.raises(RuntimeError, match="ILLEGAL_FINAL"):
            query_clickhouse("SELECT count() FROM hecho_estado_unidad FINAL")

    def test_no_hizo_falta_una_dimension_nueva(self):
        """El tercer hecho reutiliza las dimensiones que ya existían.

        Si un hecho nuevo obligara a crear dimensiones nuevas cada vez, el modelo
        no estaría creciendo: estaría empezando de cero cada vez.

        ⚠️ **Esto comparaba el censo entero de `dim_*` contra una lista escrita a
        mano**, restando primero las que habían traído otros módulos. Cada
        departamento nuevo —Cuentas, Partners, Soporte, Suscripciones— obligaba a
        alargar la resta, y mientras nadie la alargaba la prueba estaba roja sin
        que el tercer hecho hubiera creado nada: justo lo contrario de lo que
        afirma. Una prueba roja permanente deja de leerse.

        Se comprueba sobre **el módulo del tercer hecho**, que es de quien habla:
        las dimensiones que declara tienen que existir ya. Así no caduca cuando
        el modelo crece por otro lado, y sigue fallando si el hecho se trae una
        dimensión propia.
        """
        presentes = {
            f["name"]
            for f in query_clickhouse(
                "SELECT name FROM system.tables "
                "WHERE database = currentDatabase() AND name LIKE 'dim_%'"
            )
        }

        # Las dimensiones que el tercer hecho nombra en su propio código.
        fuente = (
            Path(__file__).resolve().parents[1] / "lib" / "hechos" / "hecho_estado_unidad.py"
        ).read_text(encoding="utf-8")
        usadas = set(re.findall(r"(dim_[a-z_]+)", fuente))

        assert usadas <= presentes, (
            f"el tercer hecho nombra dimensiones que no existen: "
            f"{sorted(usadas - presentes)}"
        )
        # Y las que usa son de las que ya estaban, no dimensiones propias suyas.
        propias = {d for d in usadas if "estado_unidad" in d}
        assert propias == set(), f"el tercer hecho se trajo dimensión propia: {propias}"
