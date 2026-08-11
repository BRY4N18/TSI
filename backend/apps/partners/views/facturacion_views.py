"""Excepciones de facturacion de excedente (BE-DELTA-04, BE-DELTA-05).

Delta abierto por la capa frontend de #08: la cuarta superficie de su spec
—la cola de trabajo del Administrador— **no tenia de donde leer**. Los datos ya
se escribian; lo que faltaba era poder consultarlos.

No expone accion de emision: no existe endpoint que emita una factura a mano, y
ofrecerlo desde la UI sin backend seria peor que decir cual es el siguiente paso.
"""

from __future__ import annotations

from datetime import datetime, timezone

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.permissions import EsDesarrolladorAPIs
from apps.partners.services.excepciones_facturacion_service import (
    ExcepcionesFacturacionService,
)
from core.api.response_envelope import error_response, success_response


class ExcepcionesFacturacionView(APIView):
    """GET /api/v1/facturacion/excepciones?anio&mes

    Administrador y Desarrollador de APIs. Un partner **no** entra: es una vista
    de gestion que cruza datos de varios partners.
    """

    permission_classes = [EsDesarrolladorAPIs]

    def get(self, request):
        ahora = datetime.now(timezone.utc)
        try:
            anio = int(request.query_params.get("anio", ahora.year))
            mes = int(request.query_params.get("mes", ahora.month))
        except (TypeError, ValueError):
            return error_response(
                "bad_request", "anio y mes deben ser enteros", "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not 1 <= mes <= 12:
            return error_response(
                "bad_request", "mes debe estar entre 1 y 12", "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        excepciones = ExcepcionesFacturacionService().listar(anio=anio, mes=mes)
        return success_response(
            excepciones,
            meta={
                "reintentos_agotados": sum(
                    1 for e in excepciones if e["tipo"] == "reintentos_agotados"
                ),
                "no_tarificables": sum(
                    1 for e in excepciones if e["tipo"] == "no_tarificable"
                ),
            },
        )
