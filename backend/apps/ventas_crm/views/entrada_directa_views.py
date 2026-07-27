from rest_framework.views import APIView

from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401

from apps.ventas_crm.permissions import IsAdministradorCrm
from apps.ventas_crm.services.entrada_directa_service import EntradaDirectaService
from apps.ventas_crm.views.common import crm_error


class EntradaDirectaView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorCrm]

    def post(self, request):
        try:
            return success_response(
                EntradaDirectaService().registrar(dict(request.data)),
                status_code=201,
            )
        except Exception as exc:
            return crm_error(exc)
