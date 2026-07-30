import pytest

from apps.accidentes.services.enriquecimiento_implicado_service import (
    EnriquecimientoImplicadoService,
)
from core.repositories.evidencia.implicado_repository import PAYLOAD_KEYS


@pytest.mark.service
class TestEnriquecimientoImplicadoService:
    def test_registrar_and_listar_when_valid(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = EnriquecimientoImplicadoService()

        # Act
        created = service.registrar(
            idaccidente=accidente_activo,
            idusuario=7,
            tipoimplicado="Pasajero",
            estadoimplicado="Lesionado",
            genero="F",
            edad=28,
        )
        items = service.listar(accidente_activo, idusuario=7)

        # Assert
        assert created["tipoimplicado"] == "Pasajero"
        assert created["estadoimplicado"] == "Lesionado"
        assert created["edad"] == 28
        assert "identificacion" not in created
        assert set(created.keys()) <= PAYLOAD_KEYS
        assert len(items) == 1

    def test_registrar_when_tipo_invalido_raises(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        service = EnriquecimientoImplicadoService()
        with pytest.raises(ValueError, match="tipoimplicado"):
            service.registrar(
                idaccidente=accidente_activo,
                idusuario=7,
                tipoimplicado="Conductor",
                estadoimplicado="Ileso",
            )

    def test_registrar_when_estado_invalido_raises(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        service = EnriquecimientoImplicadoService()
        with pytest.raises(ValueError, match="estadoimplicado"):
            service.registrar(
                idaccidente=accidente_activo,
                idusuario=7,
                tipoimplicado="Peaton",
                estadoimplicado="Herido",
            )

    def test_desactivar_when_valid_sets_inactivo(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        service = EnriquecimientoImplicadoService()
        created = service.registrar(
            idaccidente=accidente_activo,
            idusuario=7,
            tipoimplicado="Otro",
            estadoimplicado="Ileso",
        )

        result = service.desactivar(
            idaccidente=accidente_activo,
            idimplicado=created["idimplicado"],
            idusuario=7,
        )

        assert result["activo"] is False
        assert service.listar(accidente_activo) == []
