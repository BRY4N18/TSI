from rest_framework.views import APIView
from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401
from apps.ventas_crm.permissions import IsCRMUser
from apps.ventas_crm.services.conversion_cliente_service import ConversionClienteService
from apps.ventas_crm.views.common import crm_error, roles
class ConversionView(APIView):
    permission_classes = [IsAuthenticated401, IsCRMUser]
    def post(self, request, idprospecto):
        try: return success_response(ConversionClienteService().convertir(idprospecto, dict(request.data), user_id=request.user.idusuario, roles=roles(request), idempotency_key=request.headers.get("Idempotency-Key")), status_code=201)
        except Exception as exc: return crm_error(exc)
