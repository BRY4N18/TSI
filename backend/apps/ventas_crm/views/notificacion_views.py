from rest_framework.views import APIView

from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401

from apps.ventas_crm.permissions import IsGerenteOrAdminNotificaciones
from apps.ventas_crm.services.consulta_notificacion_ventas_service import (
    ConsultaNotificacionVentasService,
)
from apps.ventas_crm.views.common import crm_error, roles


class NotificacionVentasListView(APIView):
    permission_classes = [IsAuthenticated401, IsGerenteOrAdminNotificaciones]

    def get(self, request):
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
            cursor_raw = request.query_params.get("cursor")
            cursor = int(cursor_raw) if cursor_raw not in (None, "") else None
            idusuario_raw = request.query_params.get("idusuario")
            idusuario = int(idusuario_raw) if idusuario_raw not in (None, "") else None
            data = ConsultaNotificacionVentasService().listar(
                user_id=request.user.idusuario,
                roles=roles(request),
                idusuario=idusuario,
                regladisparada=request.query_params.get("regladisparada") or None,
                id_prospecto=(
                    int(request.query_params["id_prospecto"])
                    if request.query_params.get("id_prospecto")
                    else None
                ),
                limit=limit,
                cursor=cursor,
            )
            return success_response(
                data,
                meta={
                    "pagination": {
                        "next_cursor": data[-1]["idnotificacion"] if len(data) == limit else None,
                        "limit": limit,
                    }
                },
            )
        except Exception as exc:
            return crm_error(exc)
