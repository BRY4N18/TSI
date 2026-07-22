import pytest

from apps.accidentes.services.consulta_accidente_service import ConsultaAccidenteService
from apps.accidentes.services.registro_accidente_service import RegistroAccidenteService


@pytest.mark.critical_path
@pytest.mark.integration
class TestRegistroCriticalPath:
    def test_registro_list_detalle_patch_flow(self, mock_pinot, mock_kafka, accidente_payload):
        # Arrange
        registro = RegistroAccidenteService()
        consulta = ConsultaAccidenteService()

        # Act — registrar
        created = registro.registrar(accidente_payload, idusuario=2)
        aid = created["idaccidente"]

        # Act — listar y detalle
        lista = consulta.listar()
        detalle = consulta.detalle(aid)

        # Act — editar métrica
        patch = consulta.actualizar(aid, {"numvehiculos": 2}, idusuario=2)

        # Assert
        assert created["estado"] == "REPORTADO"
        assert any(r["idaccidente"] == aid for r in lista)
        assert detalle is not None
        assert detalle["estado_actual"] == "REPORTADO"
        assert "numvehiculos" in patch["campos_modificados"]
