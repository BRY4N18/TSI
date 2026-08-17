"""Pruebas de la fila desconocida (T013).

La garantía: **un hecho cuya dimensión no existe se carga igualmente**,
apuntando a la fila desconocida. Perder un accidente del análisis porque falta
una calle en un catálogo sería inaceptable — el hecho es el dato valioso, la
dimensión es su etiqueta.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.desconocido import (  # noqa: E402
    ETIQUETA_DESCONOCIDA,
    FILAS_DESCONOCIDAS,
    ID_DESCONOCIDO,
    SK_DESCONOCIDO,
    resolver_o_desconocido,
)

AHORA = datetime(2026, 8, 14, 12, 0, 0)


class TestResolucion:
    def test_una_clave_conocida_se_resuelve(self):
        assert resolver_o_desconocido(5, {5: 5, 6: 6}) == 5

    def test_devuelve_la_clave_y_no_la_fila_de_la_dimension(self):
        # El caso real: `conocidas` es el índice de la dimensión, clave -> fila
        # entera. Devolver el valor metería la fila completa dentro de una
        # columna del hecho, y la inserción fallaría con un error de tipo que no
        # menciona la causa. La prueba anterior no lo veía porque usaba un mapa
        # donde clave y valor coincidían.
        indice = {5: {"idcalle": 5, "condado": "Cuauhtemoc"}}
        assert resolver_o_desconocido(5, indice) == 5

    def test_una_clave_ausente_cae_en_la_desconocida(self):
        # El hecho NO se pierde: obtiene una referencia válida
        assert resolver_o_desconocido(99, {5: 5}) == ID_DESCONOCIDO

    def test_una_clave_nula_cae_en_la_desconocida(self):
        # El origen usa centinelas y nulos según la tabla; ambos son "no sé"
        assert resolver_o_desconocido(None, {5: 5}) == ID_DESCONOCIDO

    def test_nunca_lanza_ni_devuelve_nulo(self):
        # Es lo que evita que cada flujo decida por su cuenta qué hacer ante una
        # dimensión que falta, y que la respuesta dependa de quién lo escribió
        for clave in (None, 0, -7, "inexistente"):
            assert resolver_o_desconocido(clave, {}) is not None

    def test_la_clave_desconocida_de_una_dimension_versionada_es_la_sustituta(self):
        assert resolver_o_desconocido(99, {}, desconocida=SK_DESCONOCIDO) == SK_DESCONOCIDO


class TestFilasDesconocidas:
    def test_las_dimensiones_resolubles_tienen_su_fila(self):
        # dim_tiempo no aparece a propósito: se genera completa, no puede faltarle
        # una fila, y un hecho sin fecha no es un hecho
        assert set(FILAS_DESCONOCIDAS) == {
            "dim_geografia",
            "dim_severidad",
            "dim_origen_despacho",
            "dim_unidad",
            "dim_region",
            # Ventas y CRM. `dim_prospecto` no la necesita: un prospecto
            # sin canal cae en la fila desconocida del canal, no en una suya.
            "dim_canal",
            "dim_canal",
            "dim_condado_vecino",
        }

    def test_todas_se_etiquetan_igual(self):
        # Que aparezca "Desconocido" en un informe ES información, no un fallo
        assert FILAS_DESCONOCIDAS["dim_geografia"](AHORA)["condado"] == ETIQUETA_DESCONOCIDA
        assert FILAS_DESCONOCIDAS["dim_severidad"](AHORA)["severidad"] == ETIQUETA_DESCONOCIDA
        assert FILAS_DESCONOCIDAS["dim_origen_despacho"](AHORA)["origen"] == ETIQUETA_DESCONOCIDA
        assert FILAS_DESCONOCIDAS["dim_unidad"](AHORA)["proveedor"] == ETIQUETA_DESCONOCIDA

    def test_la_geografia_desconocida_lo_es_en_todos_sus_niveles(self):
        # Agrupar por condado no debe inventar un condado real para una calle
        # que no se pudo resolver
        fila = FILAS_DESCONOCIDAS["dim_geografia"](AHORA)
        for campo in ("idcalle", "idciudad", "idcondado", "idestado", "idpais"):
            assert fila[campo] == ID_DESCONOCIDO

    def test_la_severidad_desconocida_no_finge_una_gravedad(self):
        # Orden alto: queda al final al ordenar por gravedad, en vez de colarse
        # entre lo crítico y lo leve
        assert FILAS_DESCONOCIDAS["dim_severidad"](AHORA)["orden"] == 255

    def test_la_unidad_desconocida_usa_la_sustituta_cero(self):
        # La columna es UInt64 y no admite -1
        assert FILAS_DESCONOCIDAS["dim_unidad"](AHORA)["sk_unidad"] == SK_DESCONOCIDO

    def test_la_unidad_desconocida_no_declara_un_inicio_real(self):
        # No se sabe nada de ella, y menos aún desde cuándo
        assert FILAS_DESCONOCIDAS["dim_unidad"](AHORA)["inicio_es_real"] == 0


class TestUnHechoHuerfanoSobrevive:
    def test_se_carga_apuntando_a_la_fila_desconocida(self):
        # Arrange: un accidente cuya calle no está en el catálogo
        calles_conocidas = {1: 1, 2: 2}
        accidente = {"idaccidente": "ACC-0001", "idcalle": 777}

        # Act: es lo que hará el cargador del hecho
        resuelto = {
            **accidente,
            "idcalle": resolver_o_desconocido(accidente["idcalle"], calles_conocidas),
        }

        # Assert: el accidente sigue existiendo, con una referencia que SÍ une
        assert resuelto["idaccidente"] == "ACC-0001"
        assert resuelto["idcalle"] == ID_DESCONOCIDO
        assert resuelto["idcalle"] in {f["idcalle"] for f in [FILAS_DESCONOCIDAS["dim_geografia"](AHORA)]}
