import pytest

from apps.accidentes.services.enriquecimiento_conductor_service import (
    EnriquecimientoConductorService,
)


@pytest.mark.service
class TestEnriquecimientoConductorService:
    def test_registrar_reuses_identificacion_rn_evi_019(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = EnriquecimientoConductorService()
        payload = {
            "conductor": {
                "identificacion": "0911223344",
                "nombres": "María",
                "apellidos": "López",
            },
            "idestadoconductor": 1,
            "vehiculo": {"tipovehiculo": "Auto"},
        }

        # Act
        first = service.registrar(idaccidente=accidente_activo, idusuario=7, **payload)
        second = service.registrar(
            idaccidente=accidente_activo,
            idusuario=7,
            conductor={
                **payload["conductor"],
                "nombres": "Otro",
            },
            idestadoconductor=2,
            vehiculo={"tipovehiculo": "Bus"},
        )

        # Assert
        assert first["idconductor"] == second["idconductor"]
        assert first["idvehiculo"] != second["idvehiculo"]

    def test_registrar_when_excede_numvehiculos_raises(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange — caso con tope 1 (RN-EVI-022)
        idaccidente = seed_accidente(idaccidente="ACC-TOPE-1", numvehiculos=1)
        service = EnriquecimientoConductorService()
        service.registrar(
            idaccidente=idaccidente,
            idusuario=7,
            conductor={
                "identificacion": "0111222333",
                "nombres": "Uno",
                "apellidos": "Solo",
            },
            idestadoconductor=1,
            vehiculo={"tipovehiculo": "Auto"},
        )

        # Act / Assert
        with pytest.raises(ValueError, match="numvehiculos"):
            service.registrar(
                idaccidente=idaccidente,
                idusuario=7,
                conductor={
                    "identificacion": "0444555666",
                    "nombres": "Dos",
                    "apellidos": "Extra",
                },
                idestadoconductor=1,
                vehiculo={"tipovehiculo": "Moto"},
            )

    def test_listar_and_desactivar_when_valid(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = EnriquecimientoConductorService()
        created = service.registrar(
            idaccidente=accidente_activo,
            idusuario=7,
            conductor={
                "identificacion": "0555011222",
                "nombres": "Eva",
                "apellidos": "Núñez",
            },
            idestadoconductor=1,
            vehiculo={"tipovehiculo": "Moto"},
        )

        # Act
        listed = service.listar(accidente_activo, idusuario=7)
        deleted = service.desactivar(
            idaccidente=accidente_activo,
            idconductoraccidente=created["idconductoraccidente"],
            idusuario=7,
        )
        after = service.listar(accidente_activo, idusuario=7)

        # Assert
        assert len(listed) == 1
        assert deleted["activo"] is False
        assert after == []

    def test_registrar_when_missing_fields_raises(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = EnriquecimientoConductorService()

        # Act / Assert
        with pytest.raises(ValueError, match="requeridos"):
            service.registrar(
                idaccidente=accidente_activo,
                idusuario=7,
                conductor={"identificacion": "", "nombres": "A", "apellidos": "B"},
                idestadoconductor=1,
                vehiculo={"tipovehiculo": "Auto"},
            )
