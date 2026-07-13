import json
import queue
import threading

import pytest

from apps.seguimiento.services.seguimiento_sse_service import SeguimientoSseService


@pytest.mark.service
class TestSeguimientoSseService:
    def test_publish_when_subscriber_receives_event(self):
        # Arrange
        svc = SeguimientoSseService()
        received: queue.Queue[str] = queue.Queue()
        stream = svc.stream_events()

        def reader():
            next(stream)  # drain ": connected"
            received.put(next(stream))

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        thread.join(timeout=2)

        payload = {"idunidademergencia": 1, "latitud": 19.43, "longitud": -99.13}

        # Act
        svc.publish("seguimiento.posicion", payload)

        # Assert
        message = received.get(timeout=2)
        assert "seguimiento.posicion" in message
        assert json.loads(message.split("data: ", 1)[1].strip()) == payload

    def test_stream_events_yields_connected_comment(self):
        # Arrange
        svc = SeguimientoSseService()
        stream = svc.stream_events()

        # Act
        first = next(stream)

        # Assert
        assert "connected" in first
