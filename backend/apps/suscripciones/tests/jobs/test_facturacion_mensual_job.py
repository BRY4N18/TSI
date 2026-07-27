from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from apps.suscripciones.jobs.dunning_job import run_dunning
from apps.suscripciones.jobs.facturacion_mensual_job import run_facturacion_mensual
from apps.suscripciones.jobs.mantenimiento_activo_job import run_mantenimiento_activo
from apps.suscripciones.jobs.renovacion_job import run_renovacion
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service
TZ = ZoneInfo("America/Guayaquil")


class TestFacturacionMensualJob:
    def test_run(self, mock_pinot, mock_kafka):
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        result = run_facturacion_mensual()
        assert result["facturas"] >= 1


class TestDunningJob:
    def test_d_plus_3(self, mock_pinot, mock_kafka):
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
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
            }
        )
        emision = (datetime.now(TZ) - timedelta(days=3)).isoformat()
        FacturaRepository().update(
            fac["id_factura"], {"reintentos": 1, "fecha_emision": emision}
        )
        result = run_dunning()
        assert result["intentos"] >= 1


class TestRenovacionJob:
    def test_run(self, mock_pinot, mock_kafka):
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 1000
        assert run_renovacion()["renovadas"] == 1


class TestMantenimientoActivoJob:
    def test_desactiva_post_fin(self, mock_pinot, mock_kafka):
        PINOT_STORE["Fact_Suscripcion"][0]["estado"] = "Cancelada"
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 1000
        assert run_mantenimiento_activo()["desactivadas"] == 1
        assert PINOT_STORE["Fact_Suscripcion"][0]["activo"] is False
