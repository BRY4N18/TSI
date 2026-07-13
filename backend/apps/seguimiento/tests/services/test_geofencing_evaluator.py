import pytest

from apps.seguimiento.services.geofencing_evaluator import GeofencingEvaluator


@pytest.mark.service
class TestGeofencingEvaluator:
    def test_dentro_radio_when_at_destination_returns_true(self):
        # Arrange
        ev = GeofencingEvaluator()

        # Act
        inside = ev.dentro_radio(19.4326, -99.1332, 19.4326, -99.1332, 100.0)

        # Assert
        assert inside is True

    def test_evaluar_llegada_when_hysteresis_not_met_returns_false(self):
        # Arrange
        ev = GeofencingEvaluator()

        # Act
        first = ev.evaluar_llegada(
            iddespacho=1,
            lat=19.4326,
            lon=-99.1332,
            dest_lat=19.4326,
            dest_lon=-99.1332,
            fechahora_ms=1_000_000,
            histéresis_seg=30,
        )
        second = ev.evaluar_llegada(
            iddespacho=1,
            lat=19.4326,
            lon=-99.1332,
            dest_lat=19.4326,
            dest_lon=-99.1332,
            fechahora_ms=1_020_000,
            histéresis_seg=30,
        )

        # Assert
        assert first is False
        assert second is False

    def test_evaluar_llegada_desde_puntos_when_hysteresis_met_returns_true(self):
        # Arrange
        ev = GeofencingEvaluator()
        base = 1_000_000
        puntos = [
            (19.4326, -99.1332, base),
            (19.4326, -99.1332, base + 31_000),
        ]

        # Act
        arrived = ev.evaluar_llegada_desde_puntos(
            puntos=puntos,
            dest_lat=19.4326,
            dest_lon=-99.1332,
            fechahora_ms=base + 31_000,
            histéresis_seg=30,
        )

        # Assert
        assert arrived is True
