import json

import pytest

from core.repositories.suscripciones.factura_repository import FacturaRepository

pytestmark = pytest.mark.repository


class TestFacturaRepository:
    def test_create_numero_factura_seq(self, mock_pinot, mock_kafka):
        # Arrange
        repo = FacturaRepository()
        # Act
        fac = repo.create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
            }
        )
        # Assert
        assert fac["numero_factura"].startswith("FAC-202607-")
        assert fac["impuestos"] == 0.0
        assert fac["estado_pago"] == "Pendiente"
        assert fac["monto_total"] == 49.0

    def test_desglose_se_publica_como_json_y_se_lee_como_lista(
        self, mock_pinot, mock_kafka
    ):
        """`desglose_cargos` es una columna STRING de valor único.

        Publicar la lista de conceptos tal cual hacía que Pinot descartara la fila
        entera (`Cannot read single-value from Collection`): el job de facturación
        informaba una factura creada que no existía. Se guarda como JSON, pero quien la
        consume la recibe como lista.
        """
        # Arrange
        repo = FacturaRepository()
        cargos = [{"concepto": "Suscripcion plan Básico", "monto": 49.0}]
        # Act
        fac = repo.create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
                "desglose_cargos": cargos,
            }
        )
        # Assert — a Pinot va texto, al llamador le llega la lista
        publicado = mock_kafka[-1]["payload"]["desglose_cargos"]
        assert isinstance(publicado, str)
        assert json.loads(publicado) == cargos
        assert fac["desglose_cargos"] == cargos

    def test_update_no_devuelve_la_lista_a_pinot(self, mock_pinot, mock_kafka):
        """La tabla es upsert: al republicar la fila el desglose vuelve a serializarse."""
        # Arrange
        repo = FacturaRepository()
        fac = repo.create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
                "desglose_cargos": [{"concepto": "Plan", "monto": 49.0}],
            }
        )
        # Act — `fac` viene hidratado, con el desglose como lista
        repo.update_from(fac, {"estado_pago": "Pagada"})
        # Assert
        assert isinstance(mock_kafka[-1]["payload"]["desglose_cargos"], str)
