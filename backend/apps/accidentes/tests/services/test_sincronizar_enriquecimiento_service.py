import json

import pytest

from apps.accidentes.services.sincronizar_evidencia_service import (
    SincronizarEvidenciaService,
)


@pytest.mark.service
class TestSincronizarEnriquecimientoService:
    def test_sincronizar_enriquecimiento_when_valid_counts(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = SincronizarEvidenciaService()
        enriquecimiento = json.dumps(
            {
                "clima": {
                    "local_id": "local-clima",
                    "idperiododia": 1,
                    "idestadoclima": 2,
                },
                "elementos_fisicos": [
                    {"local_id": "local-fisico", "idelementofisico": 1}
                ],
                "conductores": [
                    {
                        "local_id": "local-cond",
                        "conductor": {
                            "identificacion": "0555666777",
                            "nombres": "Pedro",
                            "apellidos": "Sanz",
                        },
                        "idestadoconductor": 1,
                        "vehiculo": {"tipovehiculo": "Taxi"},
                    }
                ],
                "implicados": [
                    {
                        "local_id": "local-imp",
                        "identificacion": "0444555666",
                        "nombres": "Lucía",
                        "apellidos": "Rey",
                        "tipoimplicado": "Peaton",
                    }
                ],
            }
        )

        # Act
        result = service.sincronizar(
            idaccidente=accidente_activo,
            idusuario=7,
            notas_json=None,
            fotos_metadata_json=None,
            fotos_archivos=[],
            enriquecimiento_json=enriquecimiento,
        )

        # Assert
        assert result["sincronizados"] == 4
        assert result["pendientes"] == 0
        assert all(r["sincronizado"] for r in result["resultados"])
