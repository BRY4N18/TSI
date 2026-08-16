"""Un accidente cuya calle no existe **se conserva** (T028, SC-008).

Perder un accidente del análisis porque falta una fila en un catálogo de calles
sería inaceptable: el hecho es el dato valioso, la dimensión es su etiqueta. Y la
ausencia suele ser temporal —el origen tiene retraso de ingesta—, así que
descartar el hecho convertiría un problema pasajero en una pérdida permanente.

La prueba comprueba las dos mitades, porque una sin la otra no sirve de nada:
1. el hecho **se carga**, y
2. su referencia **sí une** con la dimensión, así que el hecho reaparece al
   agrupar en vez de desvanecerse en la unión.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    PARTICION_DE_PRUEBA,
    contar,
    requiere_modelo,
)

from lib.carga_particion import cargar_particiones  # noqa: E402
from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402
from lib.dimensiones.desconocido import ID_DESCONOCIDO  # noqa: E402
from lib.hechos.hecho_accidente import construir  # noqa: E402

AHORA = datetime(2026, 8, 14, 12, 0, 0)
MARCA = "2099-12-01 00:00:00"


class TestSobreLaLogica:
    def test_un_accidente_con_calle_ausente_no_se_descarta(self):
        datos = {
            "accidentes": [
                {"idaccidente": "ACC-HUERFANO", "fechahoraaccidente": 1770000000000, "idcalle": 777}
            ],
            "estados": [],
            "despachos": [],
            "tipos": [],
            "dim_severidad": [],
            "dim_geografia": [{"idcalle": 1, "ciudad": "C", "condado": "K"}],
        }

        filas = construir(datos, AHORA)

        assert len(filas) == 1
        assert filas[0]["idaccidente"] == "ACC-HUERFANO"

    def test_apunta_a_la_fila_desconocida_y_no_a_nulo(self):
        # Con la referencia en nulo el hecho sobreviviría, pero desaparecería en
        # toda unión con la dimensión: el mismo defecto con más pasos
        datos = {
            "accidentes": [
                {"idaccidente": "ACC-HUERFANO", "fechahoraaccidente": 1770000000000, "idcalle": 777}
            ],
            "estados": [],
            "despachos": [],
            "tipos": [],
            "dim_severidad": [],
            "dim_geografia": [{"idcalle": 1, "ciudad": "C", "condado": "K"}],
        }

        assert construir(datos, AHORA)[0]["idcalle"] == ID_DESCONOCIDO


@pytest.fixture
def particion_limpia():
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")
    yield
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


@requiere_modelo
class TestSobreElModeloCargado:
    def test_el_hecho_huerfano_reaparece_al_unir(self, particion_limpia):
        # Arrange: un accidente que apunta a la calle desconocida
        cargar_particiones(
            "hecho_accidente",
            [
                {
                    "idaccidente": "PRUEBA-HUERFANO",
                    "fecha": FECHA_DE_PRUEBA,
                    "fechahora_accidente": MARCA,
                    "franja_horaria": "madrugada",
                    "idcalle": ID_DESCONOCIDO,
                    "fue_descartado": 0,
                    "es_duplicado": 0,
                    "cargado_en": MARCA,
                    "version": MARCA,
                }
            ],
        )

        # Assert: la unión lo devuelve, con el condado etiquetado como desconocido
        assert (
            contar(
                """
                SELECT count() AS n
                FROM hecho_accidente AS h FINAL
                INNER JOIN dim_geografia AS g ON h.idcalle = g.idcalle
                WHERE h.idaccidente = 'PRUEBA-HUERFANO' AND g.condado = 'Desconocido'
                """
            )
            == 1
        )

    def test_la_fila_desconocida_existe_en_cada_dimension_resoluble(self):
        for tabla, clave in (
            ("dim_geografia", "idcalle"),
            ("dim_severidad", "idseveridad"),
            ("dim_origen_despacho", "idorigendespacho"),
        ):
            assert (
                contar(f"SELECT count() AS n FROM {tabla} FINAL WHERE {clave} = {ID_DESCONOCIDO}")
                == 1
            ), f"{tabla} no tiene su fila desconocida"

    def test_ningun_accidente_del_origen_se_perdio(self):
        # La comprobación de fondo, y la única que mira las dos puntas: el modelo
        # debe tener EXACTAMENTE los casos del origen. Contar solo el modelo no
        # detectaría la pérdida silenciosa que esta prueba existe para descartar.
        from lib.pinot_http_client import query_pinot

        try:
            en_origen = query_pinot("SELECT COUNT(*) AS n FROM Fact_Accidente")[0]["n"]
        except Exception:  # noqa: BLE001
            pytest.skip("el origen no está disponible")

        en_modelo = contar(
            "SELECT count() AS n FROM hecho_accidente FINAL "
            f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
        )
        assert en_modelo == en_origen
