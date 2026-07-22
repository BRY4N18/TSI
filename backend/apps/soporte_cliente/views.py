"""DRF views for gestión de tickets de soporte."""

from __future__ import annotations

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.soporte_cliente.domain_constants import ROL_CLIENTE
from apps.soporte_cliente.permissions import (
    IsAdministradorSLA,
    IsSoporteAgente,
    IsSoporteAgenteOrCliente,
    IsSoporteAgenteOrNivelEscalado,
)
from apps.soporte_cliente.services.cliente_lookup_service import ClienteLookupService
from apps.soporte_cliente.services.comentar_ticket_service import ComentarTicketService
from apps.soporte_cliente.services.configurar_sla_service import ConfigurarSLAService
from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.dashboard_soporte_service import DashboardSoporteService
from apps.soporte_cliente.services.escalar_ticket_service import EscalarTicketService
from apps.soporte_cliente.services.reabrir_ticket_service import ReabrirTicketService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.repositories.soporte.reclamo_repository import ReclamoRepository


class TicketsView(APIView):
    """GET lista tickets (Cliente ve solo los suyos); POST registra (CU-O91)."""

    permission_classes = [IsAuthenticated401, IsSoporteAgenteOrCliente]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request: Request) -> Response:
        limit = min(int(request.query_params.get("limit", 20)), 100)
        cursor = request.query_params.get("cursor")
        cursor_int = int(cursor) if cursor else None

        idcliente = None
        if set(getattr(request.user, "roles", [])) == {ROL_CLIENTE}:
            idcliente = ClienteLookupService().resolve_idcliente(request.user.idusuario)

        items = ReclamoRepository().list(
            idestadosoporte=request.query_params.get("idestadosoporte"),
            prioridad=request.query_params.get("prioridad"),
            idcliente=idcliente,
            limit=limit,
            cursor=cursor_int,
        )
        return success_response(
            {"items": items},
            meta={"pagination": {"next_cursor": None, "limit": limit}},
        )

    def post(self, request: Request) -> Response:
        idcliente = request.data.get("idcliente")
        asunto = request.data.get("asunto")
        descripcion = request.data.get("descripcion")
        tipo = request.data.get("tipo")
        if not all([idcliente, asunto, descripcion, tipo]):
            return error_response(
                "bad_request",
                "idcliente, asunto, descripcion y tipo son requeridos",
                "400",
                status_code=400,
            )

        archivos = [
            (f.read(), f.content_type or "image/jpeg")
            for f in request.FILES.getlist("adjuntos")
        ]

        data = RegistrarTicketService().registrar(
            idcliente=int(idcliente),
            asunto=str(asunto),
            descripcion=str(descripcion),
            tipo=str(tipo),
            idaccidente=request.data.get("idaccidente"),
            idusuario=request.user.idusuario,
            adjuntos=archivos,
        )
        return success_response(data, status_code=status.HTTP_201_CREATED)


class TicketDetalleView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgenteOrCliente]

    def get(self, request: Request, id_reclamo: int) -> Response:
        reclamo = ReclamoRepository().find_by_id(id_reclamo)
        if not reclamo:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)

        roles = set(getattr(request.user, "roles", []))
        es_solo_cliente = roles == {ROL_CLIENTE}
        if es_solo_cliente:
            idcliente = ClienteLookupService().resolve_idcliente(request.user.idusuario)
            if idcliente != reclamo.get("idcliente"):
                return error_response("forbidden", "Ticket no pertenece al cliente", "403", status_code=403)

        historial = ComentarTicketService().listar_para_rol(
            id_reclamo, ocultar_notas_internas=es_solo_cliente
        )
        return success_response({"ticket": reclamo, "historial": historial})


class ClasificarTicketManualView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgente]
    parser_classes = [JSONParser]

    def post(self, request: Request, id_reclamo: int) -> Response:
        tipo_incidencia = request.data.get("tipo_incidencia")
        prioridad = request.data.get("prioridad")
        if not tipo_incidencia or not prioridad:
            return error_response(
                "bad_request", "tipo_incidencia y prioridad son requeridos", "400", status_code=400
            )
        try:
            data = RegistrarTicketService().clasificar_manual(
                id_reclamo,
                tipo_incidencia=str(tipo_incidencia),
                prioridad=str(prioridad),
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)


class DashboardSoporteView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgente]

    def get(self, request: Request) -> Response:
        return success_response(DashboardSoporteService().metricas())


class ReabrirTicketView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgenteOrCliente]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request: Request, id_reclamo: int) -> Response:
        archivos = [
            (f.read(), f.content_type or "image/jpeg")
            for f in request.FILES.getlist("adjuntos")
        ]
        try:
            data = ReabrirTicketService().reabrir(
                id_reclamo,
                idusuario=request.user.idusuario,
                motivo=request.data.get("motivo"),
                adjuntos=archivos,
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)


class SLAConfigView(APIView):
    """GET lista configuraciones; POST crea nueva regla (CU-O95)."""

    permission_classes = [IsAuthenticated401, IsAdministradorSLA]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        return success_response({"items": ConfigurarSLAService().listar()})

    def post(self, request: Request) -> Response:
        campos = ("idplan", "tipoincidencia", "prioridad", "tiemporespuestamax", "tiemporesolucionmax")
        if not all(request.data.get(c) is not None for c in campos):
            return error_response(
                "bad_request", f"{', '.join(campos)} son requeridos", "400", status_code=400
            )
        try:
            data = ConfigurarSLAService().crear(
                idplan=int(request.data["idplan"]),
                tipoincidencia=str(request.data["tipoincidencia"]),
                prioridad=str(request.data["prioridad"]),
                tiemporespuestamax=int(request.data["tiemporespuestamax"]),
                tiemporesolucionmax=int(request.data["tiemporesolucionmax"]),
            )
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class SLAConfigDetalleView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorSLA]
    parser_classes = [JSONParser]

    def patch(self, request: Request, idslaconfig: int) -> Response:
        tiemporespuestamax = request.data.get("tiemporespuestamax")
        tiemporesolucionmax = request.data.get("tiemporesolucionmax")
        if tiemporespuestamax is None or tiemporesolucionmax is None:
            return error_response(
                "bad_request",
                "tiemporespuestamax y tiemporesolucionmax son requeridos",
                "400",
                status_code=400,
            )
        try:
            data = ConfigurarSLAService().modificar(
                idslaconfig,
                tiemporespuestamax=int(tiemporespuestamax),
                tiemporesolucionmax=int(tiemporesolucionmax),
            )
        except LookupError:
            return error_response(
                "not_found", "Configuración SLA no encontrada", "404", status_code=404
            )
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class TomarTicketView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgente]
    parser_classes = [JSONParser]

    def post(self, request: Request, id_reclamo: int) -> Response:
        try:
            data = TomarTicketService().tomar(
                id_reclamo, id_agente_asignado=request.user.idusuario
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)


class ComentarTicketView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgenteOrCliente]
    parser_classes = [JSONParser]

    def post(self, request: Request, id_reclamo: int) -> Response:
        mensaje = request.data.get("mensaje")
        if not mensaje:
            return error_response("bad_request", "mensaje requerido", "400", status_code=400)

        # RN-TIC-002: solo agentes/admin pueden crear notas internas.
        es_nota_interna = bool(request.data.get("es_nota_interna", False))
        if ROL_CLIENTE in getattr(request.user, "roles", []) and not (
            set(getattr(request.user, "roles", [])) - {ROL_CLIENTE}
        ):
            es_nota_interna = False

        try:
            data = ComentarTicketService().comentar(
                id_reclamo,
                mensaje=str(mensaje),
                es_nota_interna=es_nota_interna,
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class EscalarTicketView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgente]
    parser_classes = [JSONParser]

    def post(self, request: Request, id_reclamo: int) -> Response:
        id_rol_escalar = request.data.get("id_rol_escalar")
        id_agente_asignado = request.data.get("id_agente_asignado")
        if not id_rol_escalar or not id_agente_asignado:
            return error_response(
                "bad_request",
                "id_rol_escalar y id_agente_asignado son requeridos",
                "400",
                status_code=400,
            )
        try:
            data = EscalarTicketService().escalar(
                id_reclamo,
                id_rol_escalar=str(id_rol_escalar),
                id_agente_asignado=int(id_agente_asignado),
                mensaje=request.data.get("mensaje"),
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)


class ResolverTicketView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgenteOrNivelEscalado]
    parser_classes = [JSONParser]

    def post(self, request: Request, id_reclamo: int) -> Response:
        try:
            data = ResolverTicketService().resolver(
                id_reclamo,
                mensaje=request.data.get("mensaje"),
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)


class ConfirmarCierreTicketView(APIView):
    permission_classes = [IsAuthenticated401, IsSoporteAgenteOrCliente]

    def post(self, request: Request, id_reclamo: int) -> Response:
        try:
            data = ConfirmarCierreService().confirmar(
                id_reclamo, idusuario=request.user.idusuario
            )
        except LookupError:
            return error_response("not_found", "Ticket no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)
