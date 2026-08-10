import pytest

from apps.red_operativa.services.validacion_region_service import ValidacionRegionService

ADMIN = ["Administrador"]
DIRECTOR = ["DirectorTecnologico"]


@pytest.mark.service
class TestValidacionRegionService:
    def test_ejecutar_when_region_nueva_crea_region_en_validacion(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionRegionService()

        # Act
        result = service.ejecutar(
            {"idestado": 2, "nombreregion": "Guadalajara", "resultado": "Rechazada", "motivo": "x"},
            idusuario=9,
            roles=ADMIN,
        )

        # Assert
        assert result["estadoregion_actual"] == "En_Validación"
        region = service.region_repo.find_by_id(result["idregionoperativa"])
        assert region is not None
        puente = service.puente_repo.list_by_region(result["idregionoperativa"])
        assert any(int(p["idestadoregion"]) == 2 for p in puente)

    def test_ejecutar_inserta_validacion_siempre(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionRegionService()

        # Act
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Rechazada", "motivo": "Latencia"},
            idusuario=9,
            roles=ADMIN,
        )

        # Assert
        historial = service.validacion_repo.list_by_region(1)
        assert len(historial) == 1
        assert historial[0]["resultado"] == "Rechazada"
        assert result["idvalidacionregion"] == historial[0]["idvalidacionregion"]

    def test_ejecutar_when_aprobada_actualiza_estadoregion_a_produccion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
        )

        # Assert
        assert result["estadoregion_actual"] == "Producción"

    def test_ejecutar_when_aprobada_por_administrador_raises_permission_error(
        self, mock_pinot, mock_kafka
    ):
        # Arrange — SRS 3.5.2: solo el Director Tecnológico aprueba definitivamente;
        # el Administrador ejecuta el protocolo pero no puede aprobar solo.
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act & Assert
        with pytest.raises(PermissionError):
            service.ejecutar(
                {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=ADMIN
            )
        assert service.region_repo.find_by_id(1)["estadoregion"] == "En_Validación"

    def test_ejecutar_when_rechazada_no_cambia_estadoregion(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Rechazada", "motivo": "x"},
            idusuario=9,
            roles=ADMIN,
        )

        # Assert
        assert result["estadoregion_actual"] == "En_Validación"

    def test_ejecutar_when_rechazada_sin_motivo_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionRegionService()

        # Act & Assert
        with pytest.raises(ValueError):
            service.ejecutar(
                {"idregionoperativa": 1, "resultado": "Rechazada"}, idusuario=9, roles=ADMIN
            )

    def test_ejecutar_when_reingreso_desde_despublicada_actualiza_a_produccion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "Despublicada"})

        # Act
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
        )

        # Assert
        assert result["estadoregion_actual"] == "Producción"

    def test_ejecutar_when_reingreso_desde_en_alerta_actualiza_a_produccion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Alerta"})

        # Act
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
        )

        # Assert
        assert result["estadoregion_actual"] == "Producción"

    def test_ejecutar_concurrencia_ultimo_insert_gana(self, mock_pinot, mock_kafka):
        # Arrange: dos ejecuciones "casi simultáneas" ambas Aprobada — el estadoregion
        # final refleja el resultado de la última escritura procesada (RF-REGON-001.7),
        # y ninguna de las dos filas se pierde en el historial.
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act
        service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
        )
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
        )

        # Assert
        assert result["estadoregion_actual"] == "Producción"
        assert len(service.validacion_repo.list_by_region(1)) == 2

    def test_ejecutar_rechazada_tras_aprobada_no_revierte_estadoregion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange: RF-REGON-001.4 — un resultado Rechazada nunca cambia estadoregion,
        # ni siquiera si la región ya estaba en Producción por una validación previa.
        service = ValidacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})
        service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
        )

        # Act
        result = service.ejecutar(
            {"idregionoperativa": 1, "resultado": "Rechazada", "motivo": "y"},
            idusuario=9,
            roles=ADMIN,
        )

        # Assert
        assert result["estadoregion_actual"] == "Producción"
        assert len(service.validacion_repo.list_by_region(1)) == 2

    def test_ejecutar_when_idregionoperativa_inexistente_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionRegionService()

        # Act & Assert
        with pytest.raises(LookupError):
            service.ejecutar(
                {"idregionoperativa": 999, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
            )

    def test_ejecutar_when_region_inactiva_raises(self, mock_pinot, mock_kafka):
        # Arrange — Session 2026-07-21: reingreso salvo activo=false
        service = ValidacionRegionService()
        service.region_repo.update(1, {"activo": False, "estadoregion": "En_Validación"})

        # Act & Assert
        with pytest.raises(ValueError, match="inactiva"):
            service.ejecutar(
                {"idregionoperativa": 1, "resultado": "Aprobada"}, idusuario=9, roles=DIRECTOR
            )
