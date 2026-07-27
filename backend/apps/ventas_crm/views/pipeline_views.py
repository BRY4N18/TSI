from rest_framework.views import APIView
from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401
from apps.ventas_crm.permissions import IsCRMUser
from apps.ventas_crm.services.pipeline_service import PipelineService
from apps.ventas_crm.views.common import crm_error, roles
class PipelineView(APIView):
    permission_classes = [IsAuthenticated401, IsCRMUser]
    def post(self, request, idprospecto):
        try: return success_response(PipelineService().transicionar(idprospecto, dict(request.data), user_id=request.user.idusuario, roles=roles(request)), status_code=201)
        except Exception as exc: return crm_error(exc)
