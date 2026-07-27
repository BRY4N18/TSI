from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from core.api.response_envelope import success_response

from apps.ventas_crm.authentication import DemoSessionAuthentication
from apps.ventas_crm.services.demo_sesion_service import DemoSesionService
from apps.ventas_crm.services.ingesta_interaccion_demo_service import (
    IngestaInteraccionDemoService,
)
from apps.ventas_crm.throttles import DemoInteraccionTokenThrottle, DemoSesionIpThrottle
from apps.ventas_crm.views.common import crm_error


class DemoSesionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [DemoSesionIpThrottle]

    def post(self, request):
        try:
            data = DemoSesionService().abrir(
                idprospecto=int(request.data.get("idprospecto") or 0),
                demo_grant=str(request.data.get("demo_grant") or ""),
            )
            return success_response(data, status_code=200)
        except Exception as exc:
            return crm_error(exc)


class DemoInteraccionView(APIView):
    authentication_classes = [DemoSessionAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [DemoInteraccionTokenThrottle]

    def post(self, request):
        if not getattr(request.user, "is_demo_session", False):
            from apps.ventas_crm.domain import UnauthorizedError

            return crm_error(UnauthorizedError("se requiere demo session token"))
        try:
            row = IngestaInteraccionDemoService().registrar(
                idprospecto_token=int(request.user.idprospecto),
                data=dict(request.data),
            )
            return success_response(row, status_code=201)
        except Exception as exc:
            return crm_error(exc)
