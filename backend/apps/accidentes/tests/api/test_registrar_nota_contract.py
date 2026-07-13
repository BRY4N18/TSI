import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


@pytest.mark.api
class TestRegistrarNotaContract:
    def test_registrar_when_valid_returns_201(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/evidencias/notas",
            {
                "nota": "Testigo indica semáforo en rojo",
                "tipo": "Declaración de testigo",
            },
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["sincronizado"] is True

    def test_registrar_when_caso_cerrado_returns_422(
        self, api_client, tecnico_auth_headers, mock_pinot, mock_kafka
    ):
        # Arrange
        AccidenteRepository().create({"idaccidente": "ACC-CERRADO", "activo": True})
        EstadoAccidenteRepository().append_estado(
            idaccidente="ACC-CERRADO", estado=ESTADO_CERRADO, idusuario=2
        )

        # Act
        response = api_client.post(
            "/api/v1/accidentes/ACC-CERRADO/evidencias/notas",
            {"nota": "x", "tipo": "Observación general"},
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 422
