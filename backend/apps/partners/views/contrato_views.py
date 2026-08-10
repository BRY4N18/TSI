"""Vista del contrato de integracion versionado (CU-O50, RF-PON-011)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.permissions import EsPartnerOGestor
from apps.partners.services.contrato_integracion_service import (
    ContratoIntegracionError,
    ContratoIntegracionService,
)
from core.api.response_envelope import error_response, success_response


class ContratoIntegracionView(APIView):
    """GET: version vigente (o la pedida) y el listado del servicio."""

    permission_classes = [EsPartnerOGestor]

    def get(self, request):
        id_servicio = request.query_params.get("id_servicio")
        if not id_servicio:
            return error_response(
                "bad_request",
                "id_servicio es obligatorio: el contrato se versiona por servicio",
                "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            contrato = ContratoIntegracionService().consultar(
                id_servicio=int(id_servicio),
                version=request.query_params.get("version"),
            )
        except (TypeError, ValueError):
            return error_response(
                "bad_request", "id_servicio debe ser un entero", "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except ContratoIntegracionError as exc:
            http = (
                status.HTTP_404_NOT_FOUND
                if exc.code == "not_found"
                else status.HTTP_409_CONFLICT
            )
            return error_response(
                "not_found" if http == 404 else "conflict", exc.detail, exc.code, status_code=http
            )
        return success_response(contrato)
