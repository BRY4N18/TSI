from rest_framework.views import APIView
from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401
from apps.ventas_crm.permissions import IsCRMUser
from apps.ventas_crm.services.asignacion_manual_service import AsignacionManualService
from apps.ventas_crm.views.common import crm_error, roles
class AsignacionView(APIView):
    permission_classes = [IsAuthenticated401, IsCRMUser]
    def patch(self, request, idprospecto):
        try: return success_response(AsignacionManualService().asignar(idprospecto, dict(request.data), user_id=request.user.idusuario, roles=roles(request)))
        except Exception as exc: return crm_error(exc)
