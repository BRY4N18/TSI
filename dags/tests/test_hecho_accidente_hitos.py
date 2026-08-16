"""Un hito no alcanzado se guarda **ausente**, nunca cero (T025, SC-007).

Por qué merece una prueba propia: un caso abierto guardado con hora de cierre
igual a la fecha cero **no rompe nada**. La carga funciona, el informe responde,
y el promedio de duración queda destruido en silencio — con casos que aparecen
cerrados en 1970 o cerrados el mismo día que se cargaron.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.hechos.hecho_accidente import construir  # noqa: E402

HITOS = ("hora_confirmacion", "hora_primera_asignacion", "hora_primera_llegada", "hora_cierre")

AHORA = datetime(2026, 8, 14, 12, 0, 0)


class TestSobreLaLogica:
    def _datos(self, estados):
        return {
            "accidentes": [
                {
                    "idaccidente": "ACC-1",
                    "fechahoraaccidente": 1770000000000,
                    "idcalle": 1,
                    "idseveridad": 1,
                }
            ],
            "estados": estados,
            "despachos": [],
            "tipos": [],
            "dim_severidad": [{"idseveridad": 1, "severidad": "Leve"}],
            "dim_geografia": [{"idcalle": 1, "ciudad": "C", "condado": "K"}],
        }

    def test_un_caso_sin_transiciones_deja_los_cuatro_hitos_ausentes(self):
        fila = construir(self._datos([]), AHORA)[0]
        for hito in HITOS:
            assert fila[hito] is None, f"{hito} debería estar ausente"

    def test_un_caso_abierto_no_recibe_hora_de_cierre(self):
        # Arrange: reportado y asignado, pero nunca cerrado
        estados = [
            {"idaccidente": "ACC-1", "idtipoestadoincidente": 2, "fechahoramodificado": 1770000100000},
            {"idaccidente": "ACC-1", "idtipoestadoincidente": 4, "fechahoramodificado": 1770000200000},
        ]

        # Act
        fila = construir(self._datos(estados), AHORA)[0]

        # Assert: los alcanzados están, el no alcanzado no se inventa
        assert fila["hora_confirmacion"] is not None
        assert fila["hora_primera_asignacion"] is not None
        assert fila["hora_cierre"] is None

    def test_se_toma_el_primer_cierre_y_no_el_ultimo(self):
        # Arrange: un caso reabierto y vuelto a cerrar
        estados = [
            {"idaccidente": "ACC-1", "idtipoestadoincidente": 6, "fechahoramodificado": 1770000300000},
            {"idaccidente": "ACC-1", "idtipoestadoincidente": 6, "fechahoramodificado": 1770009000000},
        ]

        # Act
        fila = construir(self._datos(estados), AHORA)[0]

        # Assert: "cuánto se tardó en cerrar" es la primera vez; la última mide
        # cuándo dejó de dar problemas, que es otra pregunta
        assert fila["hora_cierre"] == "2026-02-02 02:45:00"


@requiere_modelo
class TestSobreElModeloCargado:
    def test_ningun_hito_cayo_en_la_fecha_cero(self):
        for hito in HITOS:
            assert contar(
                f"SELECT count() AS n FROM hecho_accidente FINAL WHERE {hito} = toDateTime(0)"
            ) == 0, f"{hito} tiene filas en la época cero"

    def test_hay_casos_con_hitos_ausentes(self):
        # Si TODOS los hitos estuvieran presentes, la prueba anterior pasaría
        # trivialmente y no probaría nada: haría falta que existan casos abiertos
        assert contar(
            "SELECT count() AS n FROM hecho_accidente FINAL WHERE hora_cierre IS NULL"
        ) > 0

    def test_ningun_hito_es_anterior_al_accidente(self):
        # Un hito anterior al suceso delataría una conversión de época mal hecha
        assert contar(
            "SELECT count() AS n FROM hecho_accidente FINAL "
            "WHERE hora_cierre IS NOT NULL AND hora_cierre < fechahora_accidente"
        ) == 0
