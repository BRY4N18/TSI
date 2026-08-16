"""Los informes responden en tiempo aceptable con datos de verdad (T050).

Un modelo en estrella se justifica por el rendimiento: si un informe del catálogo
tardara lo mismo que recalcularlo desde el origen, no habría razón para tenerlo.

**Con al menos tres meses de datos**, para que el particionado se ejercite: una
medición sobre un solo mes no distingue un modelo bien particionado de uno que
recorre la tabla entera, porque la tabla entera es un mes.

El umbral es holgado a propósito. No mide la máquina, mide que **no haya un
recorrido completo escondido** — la diferencia entre responder y recalcular son
órdenes de magnitud, no milisegundos.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

#: Generoso: un fallo aquí significa «esto recorre todo», no «esto va justo».
LIMITE_SEGUNDOS = 5.0

MESES_MINIMOS = 3

CONSULTAS = {
    "casos por severidad y mes": """
        SELECT severidad, toYYYYMM(fecha) AS periodo, count() AS n
        FROM hecho_accidente FINAL GROUP BY severidad, periodo
    """,
    "rendimiento por proveedor": """
        SELECT proveedor, countIf(resultado = 'rechazado') / count() AS pct, count() AS n
        FROM hecho_despacho FINAL GROUP BY proveedor
    """,
    "huecos de señal": """
        SELECT count() AS n FROM hecho_ping_unidad WHERE segundos_desde_anterior > 60
    """,
    "un solo mes, con poda de partición": """
        SELECT count() AS n FROM hecho_accidente FINAL WHERE toYYYYMM(fecha) = 202606
    """,
}


@requiere_modelo
class TestLatencia:
    def test_hay_bastantes_meses_para_que_la_medida_signifique_algo(self):
        meses = contar(
            "SELECT uniqExact(toYYYYMM(fecha)) AS n FROM hecho_accidente FINAL"
        )
        assert meses >= MESES_MINIMOS, f"solo {meses} meses cargados"

    def test_cada_informe_responde_dentro_del_limite(self):
        lentas = []
        for nombre, sql in CONSULTAS.items():
            inicio = time.perf_counter()
            query_clickhouse(sql)
            transcurrido = time.perf_counter() - inicio
            if transcurrido > LIMITE_SEGUNDOS:
                lentas.append(f"{nombre}: {transcurrido:.2f}s")
        assert lentas == [], f"consultas por encima de {LIMITE_SEGUNDOS}s: {lentas}"

    def test_el_hecho_mas_voluminoso_tambien_responde(self):
        # 59 045 posiciones: si algo va a ir lento, es esto
        assert contar("SELECT count() AS n FROM hecho_ping_unidad") > 50_000

        inicio = time.perf_counter()
        query_clickhouse(
            "SELECT toYYYYMM(fecha) AS periodo, count() AS n "
            "FROM hecho_ping_unidad GROUP BY periodo"
        )
        assert time.perf_counter() - inicio < LIMITE_SEGUNDOS

    def test_el_particionado_esta_en_su_sitio(self):
        # La latencia se puede tener por casualidad con pocos datos; que los
        # cuatro hechos estén particionados por mes es lo que la sostiene cuando
        # crezcan
        sin_particion = query_clickhouse(
            "SELECT name FROM system.tables "
            "WHERE database = currentDatabase() AND name LIKE 'hecho%' "
            "AND partition_key != 'toYYYYMM(fecha)'"
        )
        assert sin_particion == []
