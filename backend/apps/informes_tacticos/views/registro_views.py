from rest_framework.request import Request
from rest_framework.response import Response

from apps.informes_tacticos.envelope import informe_response
from apps.informes_tacticos.services.registro_informes_service import (
    DEFAULT_TOP,
    RegistroInformesService,
)
from apps.informes_tacticos.views.base import InformeTacticoBaseView
from core.api.response_envelope import error_response


class VolumenCasosView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = RegistroInformesService().volumen_casos(periodo)
        return informe_response(data, periodo)


class DistribucionSeveridadView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = RegistroInformesService().distribucion_severidad(periodo)
        return informe_response(data, periodo)


class DistribucionZonaView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = RegistroInformesService().distribucion_zona(periodo)
        return informe_response(data, periodo)


class CompletitudCamposCriticosView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = RegistroInformesService().completitud_campos_criticos(periodo)
        return informe_response(data, periodo)


class DescarteFusionView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = RegistroInformesService().descarte_fusion(periodo)
        return informe_response(data, periodo)


class RankingUbicacionesView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        try:
            top = int(request.query_params.get("top", DEFAULT_TOP))
        except ValueError:
            return error_response("bad_request", "'top' debe ser un entero.", "400", status_code=400)
        if top < 1 or top > 100:
            return error_response("bad_request", "'top' debe estar entre 1 y 100.", "400", status_code=400)
        data = RegistroInformesService().ranking_ubicaciones(periodo, top)
        return informe_response(data, periodo, filtros={"top": top})


class ImpactoHumanoView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = RegistroInformesService().impacto_humano(periodo)
        return informe_response(data, periodo)
