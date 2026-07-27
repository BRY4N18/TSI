import pytest

from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.asignacion_repository import AsignacionRepository
from core.repositories.ventas_crm.pipeline_repository import PipelineRepository


@pytest.mark.repository
class TestProspectoRepository:
    def test_create_and_find_by_gmail(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ProspectoRepository()
        # Act
        created = repo.create(
            {
                "nombres": "A",
                "apellidos": "B",
                "gmail": "a@ex.com",
                "empresa": "E",
                "tipo_organizacion": "Privado",
                "cargo": "C",
                "telefono": "1",
                "como_nos_conocio": "web",
            }
        )
        found = repo.find_by_gmail("a@ex.com")
        # Assert
        assert created["etapa_actual"] == "Nuevo"
        assert found["idprospecto"] == created["idprospecto"]
        assert any(m["topic"].endswith("Dim_Prospecto_topic") for m in mock_kafka)


@pytest.mark.repository
class TestAsignacionRepository:
    def test_create_is_insert_only(self, mock_pinot, mock_kafka):
        repo = AsignacionRepository()
        assert not hasattr(repo, "update") or not callable(getattr(repo, "delete", None))
        row = repo.create(
            {
                "idprospecto": 1,
                "idusuariogerenteanterior": None,
                "idusuariogerenteactual": 20,
                "tipoasignacion": "automatica",
                "motivo": None,
            }
        )
        assert row["idasignacion"] >= 1
        assert any(m["topic"].endswith("Fact_Asignacion_topic") for m in mock_kafka)


@pytest.mark.repository
class TestPipelineRepository:
    def test_create_publishes(self, mock_pinot, mock_kafka):
        repo = PipelineRepository()
        row = repo.create(
            {
                "id_prospecto": 1,
                "etapa_anterior": "Nuevo",
                "etapa_nueva": "Contactado",
                "notas": None,
                "motivo_perdida": None,
                "gerente_id": 20,
            }
        )
        assert row["id_transicion"] >= 1
        assert any(m["topic"].endswith("Fact_Pipeline_topic") for m in mock_kafka)
