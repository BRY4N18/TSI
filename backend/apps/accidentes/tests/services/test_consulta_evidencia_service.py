import pytest

from apps.accidentes.services.consulta_evidencia_service import ConsultaEvidenciaService
from core.repositories.evidencia.evidencia_foto_repository import EvidenciaFotoRepository
from core.repositories.evidencia.nota_campo_repository import NotaCampoRepository


@pytest.mark.service
class TestConsultaEvidenciaService:
    def test_listar_when_items_exist_returns_merged_sorted(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        EvidenciaFotoRepository().create(
            idaccidente=accidente_activo,
            idusuario=7,
            urlevidenciafoto="https://blob/1.jpg",
            fechahora=2_000,
        )
        NotaCampoRepository().create_campo(
            idaccidente=accidente_activo,
            idusuario=7,
            nota="Nota",
            tipo="Observación general",
            fechahora=3_000,
        )
        service = ConsultaEvidenciaService()

        # Act
        items, _ = service.listar(accidente_activo)

        # Assert
        assert len(items) == 2
        assert items[0]["fechahora"] == 3_000
        assert items[0].get("tipo_evidencia") == "nota" or items[0].get("tipo") == "foto"
