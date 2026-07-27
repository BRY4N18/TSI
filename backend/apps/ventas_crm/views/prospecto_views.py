from rest_framework.views import APIView

from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401

from apps.ventas_crm.permissions import IsCRMUser
from apps.ventas_crm.services.consulta_prospecto_service import ConsultaProspectoService
from apps.ventas_crm.services.registro_prospecto_service import RegistroProspectoService
from apps.ventas_crm.throttles import ProspectoRegistroThrottle
from apps.ventas_crm.views.common import crm_error, roles


class ProspectoListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated401(), IsCRMUser()]
        return []

    def get_throttles(self):
        if self.request.method == "POST":
            return [ProspectoRegistroThrottle()]
        return []

    def post(self, request):
        try:
            return success_response(
                RegistroProspectoService().registrar(dict(request.data)),
                status_code=201,
            )
        except Exception as exc:
            return crm_error(exc)

    def get(self, request):
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
            cursor_raw = request.query_params.get("cursor")
            activo_raw = request.query_params.get("activo")
            activo = None if activo_raw in (None, "") else str(activo_raw).lower() == "true"
            cursor = int(cursor_raw) if cursor_raw not in (None, "") else None
            data = ConsultaProspectoService().listar(
                user_id=request.user.idusuario,
                roles=roles(request),
                activo=activo,
                etapa_actual=request.query_params.get("etapa_actual") or None,
                limit=limit,
                cursor=cursor,
            )
            return success_response(
                data,
                meta={
                    "pagination": {
                        "next_cursor": data[-1]["idprospecto"] if len(data) == limit else None,
                        "limit": limit,
                    }
                },
            )
        except Exception as exc:
            return crm_error(exc)


class ProspectoDetailView(APIView):
    permission_classes = [IsAuthenticated401, IsCRMUser]

    def get(self, request, idprospecto):
        try:
            return success_response(
                ConsultaProspectoService().detalle(
                    idprospecto,
                    user_id=request.user.idusuario,
                    roles=roles(request),
                )
            )
        except Exception as exc:
            return crm_error(exc)
