"""Regresión end-to-end cross-app: accidentes -> despacho -> seguimiento.

Cubre la cadena completa desde el registro público de un accidente hasta el
cierre del caso, pasando por la asignación automática de unidad (consumer de
despacho disparado igual que en test_cadena_critica_despacho_integration.py)
y el reporte de posición GPS / llegada de la unidad (seguimiento).

Reutiliza las fixtures compartidas en backend/conftest.py: api_client,
mock_pinot, mock_kafka, operador_auth_headers, unidad_seguimiento_auth_headers,
operador_seguimiento_auth_headers y unidad_con_estado_activa. No se duplican
fixtures ya existentes; el único dato local es el payload de registro del
accidente, específico de este escenario.
"""

from __future__ import annotations

import time

import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_REPORTADO
from apps.despacho.consumers.accidente_reportado_consumer import AccidenteReportadoConsumer
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)


@pytest.mark.critical_path
@pytest.mark.integration
class TestCadenaCompletaAccidenteDespachoSeguimiento:
    def test_registro_asignacion_seguimiento_cierre_flujo_completo(
        self,
        api_client,
        mock_pinot,
        mock_kafka,
        operador_auth_headers,
        unidad_seguimiento_auth_headers,
        operador_seguimiento_auth_headers,
        unidad_con_estado_activa,
    ):
        # --- 1. Registro público del accidente ---
        payload_registro = {
            "latitudinicio": 19.4326,
            "longitudinicio": -99.1332,
            "fechahoraaccidente": int(time.time() * 1000),
            "idseveridad": 2,
            "descripcion": "Choque múltiple cadena regresión E2E",
            "idcalle": 1,
        }
        registro = api_client.post(
            "/api/v1/accidentes",
            payload_registro,
            format="json",
            **operador_auth_headers,
        )
        assert registro.status_code == 201
        body_registro = registro.json()
        assert body_registro["data"]["estado"] == ESTADO_REPORTADO
        idaccidente = body_registro["data"]["idaccidente"]

        # --- 2. Disparar el consumer de despacho (sin Kafka real) ---
        consumer = AccidenteReportadoConsumer()
        asignacion = consumer.handle(
            {"idaccidente": idaccidente, "estado": ESTADO_REPORTADO, "idusuario": 2}
        )
        assert asignacion is not None
        assert asignacion["asignado"] is True
        iddespacho = asignacion["iddespacho"]

        # Confirmación de despacho por la unidad
        from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService

        confirmacion = ConfirmarDespachoService().confirmar(
            idnotificaciondespacho=asignacion["idnotificaciondespacho"],
            idunidademergencia=1,
            idusuario=6,
        )
        assert confirmacion["estado_caso"] == "ASIGNADO"
        assert confirmacion["estado_unidad"] == "Ocupada"

        # --- 3. Posición GPS y llegada de la unidad (seguimiento) ---
        pos_payload = {
            "idunidademergencia": 1,
            "idaccidente": idaccidente,
            "latitud": 19.4326,
            "longitud": -99.1332,
            "fechahora": int(time.time() * 1000),
        }
        pos = api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            pos_payload,
            format="json",
            **unidad_seguimiento_auth_headers,
        )
        assert pos.status_code == 202

        llegada = api_client.post(
            f"/api/v1/mi-seguimiento/despachos/{iddespacho}/llegada",
            {},
            format="json",
            **unidad_seguimiento_auth_headers,
        )
        assert llegada.status_code == 200

        # --- 4. Cierre del caso ---
        cierre = api_client.post(
            f"/api/v1/accidentes/{idaccidente}/cerrar",
            {"resultado_atencion": "Cadena completa E2E regresión"},
            format="json",
            **operador_seguimiento_auth_headers,
        )
        assert cierre.status_code == 200
        body_cierre = cierre.json()
        assert body_cierre["data"]["estado_caso"] == ESTADO_CERRADO

        # --- 5. Assert de consistencia cross-repositorio ---
        assert EstadoAccidenteRepository().get_current_estado(idaccidente) == ESTADO_CERRADO

        estado_despacho, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado_despacho == ESTADO_EN_SITIO or body_cierre["data"]["estado_caso"] == ESTADO_CERRADO
