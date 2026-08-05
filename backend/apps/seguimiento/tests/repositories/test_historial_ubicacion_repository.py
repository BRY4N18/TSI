import pytest

from core.repositories.seguimiento.historial_ubicacion_repository import (
    HistorialUbicacionRepository,
)


@pytest.mark.repository
class TestHistorialUbicacionRepository:
    def test_publish_when_valid_persists_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialUbicacionRepository()

        # Act
        record = repo.publish(
            idunidademergencia=1,
            idaccidente="ACC-1",
            latitud=19.43,
            longitud=-99.13,
            fechahora=1_700_000_000_000,
        )

        # Assert
        assert record["idhistorialunidademergencia"] == 1
        assert len(mock_kafka) == 1
        assert mock_kafka[0]["topic"].endswith("Dim_HistorialUbicacionUnidadEmergencia_topic")

    def test_list_by_unidad_when_multiple_returns_ordered(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialUbicacionRepository()
        repo.publish(
            idunidademergencia=1,
            idaccidente="ACC-1",
            latitud=1.0,
            longitud=2.0,
            fechahora=100,
        )
        repo.publish(
            idunidademergencia=1,
            idaccidente="ACC-1",
            latitud=3.0,
            longitud=4.0,
            fechahora=200,
        )

        # Act
        rows, next_cursor = repo.list_by_unidad(1)

        # Assert
        assert len(rows) == 2
        assert rows[0]["fechahora"] <= rows[1]["fechahora"]
        assert next_cursor is None

    def test_list_by_unidad_when_hay_mas_paginas_devuelve_cursor(self, mock_pinot, mock_kafka):
        # Arrange — 5 puntos de traza
        repo = HistorialUbicacionRepository()
        for i in range(5):
            repo.publish(
                idunidademergencia=1,
                idaccidente="ACC-1",
                latitud=1.0 + i,
                longitud=2.0,
                fechahora=100 + i,
            )

        # Act — recorrer con páginas de 2
        vistos: list[int] = []
        cursor = None
        for _ in range(10):
            pagina, cursor = repo.list_by_unidad(1, limit=2, cursor=cursor)
            vistos.extend(int(p["idhistorialunidademergencia"]) for p in pagina)
            if cursor is None:
                break

        # Assert — sin repetidos ni faltantes
        assert sorted(vistos) == list(range(1, 6))
        assert len(vistos) == len(set(vistos))

    def test_iter_by_unidad_recorre_toda_la_traza(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialUbicacionRepository()
        for i in range(12):
            repo.publish(
                idunidademergencia=1,
                idaccidente="ACC-1",
                latitud=1.0,
                longitud=2.0,
                fechahora=100 + i,
            )

        # Act
        puntos = list(repo.iter_by_unidad(1))

        # Assert — antes esto se recortaba a 10 por el LIMIT implícito de Pinot
        assert len(puntos) == 12

    def test_list_by_unidad_filtra_la_ventana_temporal_en_sql(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialUbicacionRepository()
        for fecha in (100, 200, 300, 400):
            repo.publish(
                idunidademergencia=1,
                idaccidente="ACC-1",
                latitud=1.0,
                longitud=2.0,
                fechahora=fecha,
            )

        # Act
        rows, _ = repo.list_by_unidad(1, desde=200, hasta=300)

        # Assert
        assert sorted(r["fechahora"] for r in rows) == [200, 300]
