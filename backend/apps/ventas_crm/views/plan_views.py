from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from core.api.response_envelope import success_response

from apps.ventas_crm.services.consulta_planes_publicos_service import (
    ConsultaPlanesPublicosService,
)
from apps.ventas_crm.views.common import crm_error


class PlanListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            return success_response(ConsultaPlanesPublicosService().listar())
        except Exception as exc:
            return crm_error(exc)
