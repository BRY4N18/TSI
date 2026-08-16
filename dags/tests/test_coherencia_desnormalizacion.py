"""Las dos formas de medir lo mismo dan lo mismo (T026, SC-004). ⚠️

La desnormalización es lo que hace rápido a este modelo: el hecho lleva copiadas
severidad, ciudad y condado, y así la mayoría de los informes no une con nada.

Y es también su punto débil. Si la copia del hecho se desincroniza de su
dimensión, **dos informes que preguntan lo mismo empiezan a discrepar** y nadie
sabe cuál creer. No hay error, no hay aviso: solo dos cifras distintas para la
misma pregunta.

Esta prueba compara las dos rutas. Que coincidan es la única evidencia de que la
optimización no está mintiendo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

POR_COLUMNA = """
    SELECT severidad, toYYYYMM(fecha) AS periodo, count() AS n
    FROM hecho_accidente FINAL
    WHERE severidad IS NOT NULL
    GROUP BY severidad, periodo
    ORDER BY severidad, periodo
"""

POR_UNION = """
    SELECT d.severidad AS severidad, toYYYYMM(h.fecha) AS periodo, count() AS n
    FROM hecho_accidente AS h FINAL
    INNER JOIN dim_severidad AS d ON h.idseveridad = d.idseveridad
    GROUP BY d.severidad, periodo
    ORDER BY severidad, periodo
"""


@requiere_modelo
class TestCasosPorSeveridadYMes:
    def test_las_dos_rutas_devuelven_lo_mismo(self):
        assert query_clickhouse(POR_COLUMNA) == query_clickhouse(POR_UNION)

    def test_la_comparacion_no_es_trivial(self):
        # Si no hubiera filas, la prueba anterior pasaría comparando dos listas
        # vacías y no probaría absolutamente nada
        assert len(query_clickhouse(POR_COLUMNA)) > 1


@requiere_modelo
class TestCondadoDelHechoContraSuDimension:
    def test_ningun_condado_copiado_contradice_a_la_dimension(self):
        # La copia salió de la dimensión al cargar; si difieren, alguien cargó el
        # hecho sin recargar la dimensión, o al revés
        assert contar(
            """
            SELECT count() AS n
            FROM hecho_accidente AS h FINAL
            INNER JOIN dim_geografia AS g ON h.idcalle = g.idcalle
            WHERE h.condado != g.condado
            """
        ) == 0

    def test_ninguna_severidad_copiada_contradice_a_la_dimension(self):
        assert contar(
            """
            SELECT count() AS n
            FROM hecho_accidente AS h FINAL
            INNER JOIN dim_severidad AS d ON h.idseveridad = d.idseveridad
            WHERE h.severidad != d.severidad
            """
        ) == 0


@requiere_modelo
class TestProveedorDelDespacho:
    def test_coincide_con_la_version_de_unidad_a_la_que_apunta(self):
        # Es la copia más delicada del modelo: no es "el proveedor de la unidad"
        # sino "el de la versión vigente al despachar"
        assert contar(
            """
            SELECT count() AS n
            FROM hecho_despacho AS h FINAL
            INNER JOIN dim_unidad AS u FINAL ON h.sk_unidad = u.sk_unidad
            WHERE h.proveedor != u.proveedor
            """
        ) == 0
