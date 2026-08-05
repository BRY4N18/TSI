from rest_framework.request import Request
from rest_framework.response import Response

from apps.informes_tacticos.envelope import informe_response
from apps.informes_tacticos.services.despacho_informes_service import DespachoInformesService
from apps.informes_tacticos.views.base import InformeTacticoBaseView
from core.api.response_envelope import error_response


def _parse_idcondado(request: Request) -> tuple[int | None, Response | None]:
    raw = request.query_params.get("idcondado")
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, error_response("bad_request", "'idcondado' debe ser un entero.", "400", status_code=400)


class AsignacionAutomaticaVsManualView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        idcondado, error = _parse_idcondado(request)
        if error:
            return error
        data = DespachoInformesService().asignacion_automatica_vs_manual(periodo, idcondado)
        return informe_response(data, periodo, filtros={"idcondado": idcondado})


class TiempoReportadoConfirmadoView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = DespachoInformesService().tiempo_reportado_confirmado(periodo)
        return informe_response(data, periodo)


class TiempoRespuestaPorSeveridadView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        idcondado, error = _parse_idcondado(request)
        if error:
            return error
        data = DespachoInformesService().tiempo_respuesta_por_severidad(periodo, idcondado)
        return informe_response(data, periodo, filtros={"idcondado": idcondado})


class RechazoTimeoutPorUnidadView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = DespachoInformesService().rechazo_timeout_por_unidad(periodo)
        return informe_response(data, periodo)


class CargaPorUnidadView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = DespachoInformesService().carga_por_unidad(periodo)
        return informe_response(data, periodo)


class RatioDemandaCapacidadView(InformeTacticoBaseView):
    def get(self, request: Request) -> Response:
        periodo, error = self._parse_periodo_or_error(request)
        if error:
            return error
        data = DespachoInformesService().ratio_demanda_capacidad(periodo)
        return informe_response(data, periodo)
