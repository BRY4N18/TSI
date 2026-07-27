"""Job tests split per task files."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from apps.suscripciones.jobs.dunning_job import run_dunning
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service
TZ = ZoneInfo("America/Guayaquil")


class TestDunningJobDedicated:
    def test_no_intenta_si_reintentos_cero(self, mock_pinot, mock_kafka):
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        fac = FacturaRepository().create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "periodo": "2026-07",
                "monto_base": 10.0,
            }
        )
        emision = (datetime.now(TZ) - timedelta(days=4)).isoformat()
        FacturaRepository().update(fac["id_factura"], {"reintentos": 0, "fecha_emision": emision})
        assert run_dunning()["intentos"] == 0
