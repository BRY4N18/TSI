"""Cobro tests live alongside generacion; marker service file for T039."""

# Re-export pattern: tests in test_generacion_factura_service.py::TestCobroService
# Additional edge cases:

import pytest

from apps.suscripciones.services.cobro_service import CobroService
from apps.suscripciones.services.generacion_factura_service import GeneracionFacturaService
from conftest import PINOT_STORE
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service


class TestCobroServiceIdempotencia:
    def test_pagada_no_recobra(self, mock_pinot, mock_kafka):
        # Arrange
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        fac = GeneracionFacturaService().para_suscripcion(PINOT_STORE["Fact_Suscripcion"][0])
        CobroService().intentar(fac["id_factura"])
        # Act
        again = CobroService().intentar(fac["id_factura"], force_fail=True)
        # Assert
        assert again["estado_pago"] == "Pagada"
