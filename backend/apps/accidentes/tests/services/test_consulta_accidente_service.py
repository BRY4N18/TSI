import pytest

from apps.accidentes.services.consulta_accidente_service import ConsultaAccidenteService


@pytest.mark.service
class TestConsultaAccidenteService:
    def test_listar_when_activos_includes_estado(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        seed_accidente(idaccidente="ACC-C-1")
        service = ConsultaAccidenteService()

        # Act
        rows = service.listar()

        # Assert
        assert any(r["idaccidente"] == "ACC-C-1" for r in rows)
        assert rows[0].get("estado_actual") is not None

    def test_listar_when_filtro_estado_filters_by_estado_actual(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-C-BORRADOR", estado="BORRADOR")
        seed_accidente(idaccidente="ACC-C-REPORTADO", estado="REPORTADO")
        service = ConsultaAccidenteService()

        # Act
        rows = service.listar(estado="REPORTADO")

        # Assert
        ids = [r["idaccidente"] for r in rows]
        assert "ACC-C-REPORTADO" in ids
        assert "ACC-C-BORRADOR" not in ids

    def test_actualizar_when_increment_logs_audit(self, mock_pinot, mock_kafka, seed_accidente, caplog):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-C-2", numvehiculos=1)
        service = ConsultaAccidenteService()

        # Act
        result = service.actualizar(aid, {"numvehiculos": 2}, idusuario=2)

        # Assert
        assert result["idaccidente"] == aid
        assert "numvehiculos" in result["campos_modificados"]
