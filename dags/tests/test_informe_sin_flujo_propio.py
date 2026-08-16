"""Un informe del catálogo se resuelve con una consulta (T030, SC-001).

Es la tesis del modelo. El diseño anterior creaba **una tabla y un flujo por
informe**: tres informes, tres tablas, tres DAGs. Con ~105 informes compuestos
por delante, eso son ~105 tablas y ~105 flujos, cada uno con su propia forma de
calcular lo mismo y su propia oportunidad de discrepar.

Un modelo en estrella cumple su promesa si un informe nuevo **no necesita nada
nuevo**: solo una consulta. Estas pruebas toman informes reales del catálogo y
comprueban justo eso — que responden, y que no hizo falta crear ninguna tabla
para ello.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

#: Tablas del modelo. Cualquier otra que apareciera sería una tabla por informe,
#: que es exactamente el diseño que este módulo sustituye.
TABLAS_DEL_MODELO = {
    "dim_tiempo", "dim_geografia", "dim_severidad", "dim_origen_despacho",
    "dim_unidad", "hecho_accidente", "hecho_despacho", "hecho_estado_unidad",
    "hecho_ping_unidad", "hecho_evidencia",
    "dim_region",
}

#: Las tres del diseño anterior. Sus flujos y su DDL se retiraron el 2026-08-15
#: (decisión #20, opción B), así que **ya no se refrescan ni se recrean**; las
#: filas que quedan son datos residuales de la última corrida.
#:
#: No se borran desde aquí: destruir datos no es reversible, y la limpieza es una
#: operación de base, no de una prueba. Se restan para que la tesis siga
#: comprobándose mientras las filas sigan ahí.
TABLAS_HEREDADAS = {"perdida_senal_gps", "indice_calidad_historico", "rendimiento_por_proveedor"}

#: Informes reales del catálogo, cada uno una sola consulta.
INFORMES = {
    "casos por severidad y mes": """
        SELECT severidad, toYYYYMM(fecha) AS periodo, count() AS casos
        FROM hecho_accidente FINAL GROUP BY severidad, periodo ORDER BY periodo
    """,
    "casos por condado": """
        SELECT condado, count() AS casos
        FROM hecho_accidente FINAL GROUP BY condado ORDER BY casos DESC
    """,
    "casos por franja horaria": """
        SELECT franja_horaria, count() AS casos
        FROM hecho_accidente FINAL GROUP BY franja_horaria
    """,
    "tiempo medio de llegada": """
        SELECT round(avg(dateDiff('second', fechahora_accidente, hora_primera_llegada)), 2) AS seg
        FROM hecho_accidente FINAL WHERE hora_primera_llegada IS NOT NULL
    """,
    "despachos resueltos al primer intento": """
        SELECT countIf(numero_intento = 1 AND resultado = 'confirmado') / count() AS ratio
        FROM hecho_despacho FINAL
    """,
    "rendimiento por proveedor": """
        SELECT proveedor,
               countIf(resultado = 'rechazado') / count() AS pct_rechazo,
               countIf(resultado = 'abortado') / count() AS pct_abortos,
               round(avg(segundos_transito), 2) AS llegada_media,
               count() AS total
        FROM hecho_despacho FINAL GROUP BY proveedor
    """,
    "impacto humano por mes": """
        SELECT toYYYYMM(fecha) AS periodo, sum(num_heridos) AS heridos,
               sum(num_fallecidos) AS fallecidos
        FROM hecho_accidente FINAL GROUP BY periodo ORDER BY periodo
    """,
    "casos en fin de semana": """
        SELECT t.es_fin_de_semana AS finde, count() AS casos
        FROM hecho_accidente AS h FINAL
        INNER JOIN dim_tiempo AS t FINAL ON h.fecha = t.fecha
        GROUP BY finde
    """,
}


@requiere_modelo
class TestInformesDelCatalogo:
    def test_cada_informe_responde_con_una_sola_consulta(self):
        for nombre, sql in INFORMES.items():
            filas = query_clickhouse(sql)
            assert filas, f"«{nombre}» no devolvió nada"

    def test_ninguno_necesito_una_tabla_propia(self):
        # La comprobación de la tesis: tras responder los ocho informes, el
        # almacén sigue teniendo exactamente las mismas tablas
        presentes = {
            f["name"]
            for f in query_clickhouse(
                "SELECT name FROM system.tables WHERE database = currentDatabase()"
            )
        }
        assert presentes - TABLAS_HEREDADAS == TABLAS_DEL_MODELO

    def test_la_mayoria_no_une_con_nada(self):
        # Es lo que compra la desnormalización: si casi todos los informes
        # tuvieran que unir, el modelo no estaría dando lo que promete
        sin_union = [n for n, sql in INFORMES.items() if "JOIN" not in sql.upper()]
        assert len(sin_union) >= len(INFORMES) - 1
