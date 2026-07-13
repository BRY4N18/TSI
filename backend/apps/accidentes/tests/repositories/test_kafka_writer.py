import pytest

from core.repositories.accidentes.kafka_writer import KafkaWriter


@pytest.mark.repository
class TestAccidentesKafkaWriter:
    def test_publish_when_called_stores_message(self, mock_kafka):
        # Arrange
        writer = KafkaWriter()

        # Act
        writer.publish("Fact_Accidente_topic", {"idaccidente": "ACC-1", "activo": True})

        # Assert
        assert len(mock_kafka) == 1
        assert mock_kafka[0]["topic"] == "Fact_Accidente_topic"
        assert mock_kafka[0]["payload"]["idaccidente"] == "ACC-1"
