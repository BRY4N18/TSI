from rest_framework.request import Request
from rest_framework.response import Response

from apps.informes_tacticos.envelope import informe_response
from apps.informes_tacticos.services.seguimiento_informes_service import SeguimientoInformesService
from apps.informes_tacticos.views.base import InformeTacticoBaseView


class TiempoAsignadoCerradoView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = SeguimientoInformesService().tiempo_asignado_cerrado(periodo)
        return informe_response(data, periodo)


class CierresForzadosView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = SeguimientoInformesService().cierres_forzados(periodo)
        return informe_response(data, periodo)


class AbortosPerdidasView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = SeguimientoInformesService().abortos_perdidas(periodo)
        return informe_response(data, periodo)
