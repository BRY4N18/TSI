import pytest

from core.repositories.evidencia.evidencia_foto_repository import (
    EvidenciaFotoRepository,
)


@pytest.mark.repository
class TestEvidenciaFotoRepository:
    def test_create_when_valid_publishes_and_reads_back(self, mock_pinot, mock_kafka):
        # Arrange
        repo = EvidenciaFotoRepository()

        # Act
        created = repo.create(
            idaccidente="ACC-1",
            idusuario=7,
            urlevidenciafoto="https://blob.test/ACC-1/1.jpg",
            fechahora=1_700_000_000_000,
        )
        rows = repo.list_by_accidente("ACC-1")

        # Assert
        assert created["sincronizado"] is True
        assert len(rows) == 1
        assert rows[0]["idevidenciafoto"] == created["idevidenciafoto"]
        assert len(mock_kafka) == 1

    def test_list_by_accidente_when_mas_de_diez_fotos_las_trae_todas(
        self, mock_pinot, mock_kafka
    ):
        # Arrange — más de 10 fotos, para verificar que el filtro/orden viaja en
        # el SQL y no queda a merced del recorte implícito de Pinot.
        repo = EvidenciaFotoRepository()
        for i in range(15):
            repo.create(
                idaccidente="ACC-1",
                idusuario=7,
                urlevidenciafoto=f"https://blob.test/ACC-1/{i}.jpg",
                fechahora=1_700_000_000_000 + i,
            )

        # Act
        rows = repo.list_by_accidente("ACC-1", limit=100)

        # Assert
        assert len(rows) == 15
        assert rows == sorted(rows, key=lambda r: r["fechahora"], reverse=True)

    def test_list_by_accidente_when_cursor_pagina_correctamente(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = EvidenciaFotoRepository()
        for i in range(5):
            repo.create(
                idaccidente="ACC-1",
                idusuario=7,
                urlevidenciafoto=f"https://blob.test/ACC-1/{i}.jpg",
                fechahora=1_700_000_000_000 + i,
            )

        # Act — recorrer con páginas de 2
        vistos: list[int] = []
        cursor = None
        for _ in range(10):
            pagina = repo.list_by_accidente("ACC-1", limit=2, cursor=cursor)
            if not pagina:
                break
            vistos.extend(p["idevidenciafoto"] for p in pagina)
            cursor = pagina[-1]["idevidenciafoto"]

        # Assert — sin repetidos ni faltantes
        assert len(vistos) == len(set(vistos))
        assert len(vistos) == 5
