"""Pruebas de la carga idempotente por partición (T012).

Dos garantías, y la segunda importa tanto como la primera:

1. **Recargar el mismo período deja el mismo número exacto de filas.**
2. **No se emite ningún borrado por condición.** Es una mutación, y con 13
   hechos cargándose con regularidad las mutaciones se acumulan y compiten entre
   sí (research D3). La prueba existe porque la tentación de «solo por esta vez»
   es exactamente cómo volvería.
"""

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.carga_particion import cargar_particiones, particion_de  # noqa: E402


class _AlmacenFalso:
    """Almacén en memoria que recuerda el SQL emitido y las filas insertadas."""

    def __init__(self):
        self.sql: list[str] = []
        self.filas: dict[int, list[dict]] = {}

    def ejecutar(self, sql: str) -> None:
        self.sql.append(sql)
        if "DROP PARTITION" in sql:
            self.filas.pop(int(sql.rsplit(maxsplit=1)[-1]), None)

    def insertar(self, tabla: str, filas: list[dict]) -> None:
        for fila in filas:
            self.filas.setdefault(particion_de(fila["fecha"]), []).append(fila)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.filas.values())


def _filas(cuantas, mes=2):
    return [
        {"fecha": date(2026, mes, 3), "idaccidente": f"ACC-{i:04d}"} for i in range(cuantas)
    ]


class TestParticionDe:
    def test_convierte_fecha_a_particion_mensual(self):
        assert particion_de(date(2026, 2, 3)) == 202602
        assert particion_de(datetime(2026, 12, 31, 23, 59)) == 202612

    def test_acepta_texto_porque_las_filas_ya_serializadas_lo_traen_asi(self):
        assert particion_de("2026-02-03") == 202602
        assert particion_de("2026-02-03T14:00:00") == 202602


class TestIdempotencia:
    def test_recargar_deja_el_mismo_numero_exacto_de_filas(self):
        # Arrange
        almacen = _AlmacenFalso()
        filas = _filas(5)

        # Act: la misma carga, dos veces
        cargar_particiones(
            "hecho_accidente", filas, ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )
        primera = almacen.total
        cargar_particiones(
            "hecho_accidente", filas, ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )

        # Assert: 5, no 10
        assert primera == 5
        assert almacen.total == 5

    def test_descarta_la_particion_antes_de_insertar(self):
        # Arrange
        almacen = _AlmacenFalso()

        # Act
        cargar_particiones(
            "hecho_accidente", _filas(2), ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )

        # Assert: el orden importa — insertar antes de descartar borraría lo recién puesto
        assert almacen.sql == ["ALTER TABLE hecho_accidente DROP PARTITION 202602"]


class TestNingunBorradoPorCondicion:
    def test_no_se_emite_delete_where(self):
        # Arrange
        almacen = _AlmacenFalso()

        # Act
        cargar_particiones(
            "hecho_accidente",
            _filas(3) + _filas(2, mes=3),
            ejecutar=almacen.ejecutar,
            insertar=almacen.insertar,
        )

        # Assert: ni DELETE, ni UPDATE — las dos formas de mutación
        emitido = " ".join(almacen.sql).upper()
        assert "DELETE" not in emitido
        assert "UPDATE" not in emitido
        assert emitido.count("DROP PARTITION") == 2


class TestPeriodoQueSeQuedaVacio:
    def test_sin_nombrarlo_las_filas_viejas_sobrevivirian(self):
        # Arrange: un período cargado que después no trae ninguna fila
        almacen = _AlmacenFalso()
        cargar_particiones(
            "hecho_accidente", _filas(4), ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )
        assert almacen.total == 4

        # Act: recarga sin filas y sin declarar la partición afectada
        cargar_particiones(
            "hecho_accidente", [], ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )

        # Assert: nadie descartó nada — el dato viejo sigue ahí. Es el fallo que
        # `particiones_vacias` existe para evitar, y se documenta ejecutándolo.
        assert almacen.total == 4

    def test_declararlo_vacia_la_particion(self):
        # Arrange
        almacen = _AlmacenFalso()
        cargar_particiones(
            "hecho_accidente", _filas(4), ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )

        # Act
        cargar_particiones(
            "hecho_accidente",
            [],
            particiones_vacias=[202602],
            ejecutar=almacen.ejecutar,
            insertar=almacen.insertar,
        )

        # Assert
        assert almacen.total == 0


class TestVariasParticiones:
    def test_cada_mes_se_recarga_por_separado(self):
        # Arrange
        almacen = _AlmacenFalso()

        # Act
        tocadas = cargar_particiones(
            "hecho_accidente",
            _filas(3) + _filas(2, mes=3),
            ejecutar=almacen.ejecutar,
            insertar=almacen.insertar,
        )

        # Assert
        assert tocadas == [202602, 202603]
        assert len(almacen.filas[202602]) == 3
        assert len(almacen.filas[202603]) == 2

    def test_recargar_un_mes_no_toca_el_otro(self):
        # Arrange
        almacen = _AlmacenFalso()
        cargar_particiones(
            "hecho_accidente",
            _filas(3) + _filas(2, mes=3),
            ejecutar=almacen.ejecutar,
            insertar=almacen.insertar,
        )

        # Act: recarga solo febrero
        cargar_particiones(
            "hecho_accidente", _filas(1), ejecutar=almacen.ejecutar, insertar=almacen.insertar
        )

        # Assert: marzo intacto — es la propiedad que hace barata la recarga parcial
        assert len(almacen.filas[202602]) == 1
        assert len(almacen.filas[202603]) == 2
