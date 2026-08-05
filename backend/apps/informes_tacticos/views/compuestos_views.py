from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_compuesto_response
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo
from apps.informes_tacticos.permissions import InformesTacticosCompuestosPermission
from apps.informes_tacticos.services.informes_compuestos_service import InformesCompuestosService
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class _InformeCompuestoBaseView(APIView):
    permission_classes = [IsAuthenticated401, InformesTacticosCompuestosPermission]

    def _parse_periodo_or_error(self, request: Request):
        try:
            return parse_periodo(request.query_params), None
        except PeriodoInvalido as exc:
            return None, error_response("bad_request", str(exc), "400", status_code=400)


class PerdidaSenalView(_InformeCompuestoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data, ultima_corrida = InformesCompuestosService().perdida_senal(periodo)
        return informe_compuesto_response(
            data, periodo, materializado=data is not None, ultima_corrida=ultima_corrida
        )


class IndiceCalidadView(_InformeCompuestoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data, ultima_corrida = InformesCompuestosService().indice_calidad(periodo)
        return informe_compuesto_response(
            data, periodo, materializado=data is not None, ultima_corrida=ultima_corrida
        )


class RendimientoProveedorView(_InformeCompuestoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data, ultima_corrida = InformesCompuestosService().rendimiento_proveedor(periodo)
        return informe_compuesto_response(
            data, periodo, materializado=data is not None, ultima_corrida=ultima_corrida
        )
