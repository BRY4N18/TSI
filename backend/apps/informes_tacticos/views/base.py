"""Base view compartida por los 16 informes: parsea período, aplica permisos."""

from rest_framework.request import Request
from rest_framework.views import APIView

from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo
from apps.informes_tacticos.permissions import InformesTacticosLecturaPermission
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class InformeTacticoBaseView(APIView):
    """Base: parsea período, delega al servicio, arma el envelope estándar."""

    permission_classes = [IsAuthenticated401, InformesTacticosLecturaPermission]

    def _parse_periodo_or_error(self, request: Request):
        try:
            return parse_periodo(request.query_params), None
        except PeriodoInvalido as exc:
            return None, error_response("bad_request", str(exc), "400", status_code=400)
