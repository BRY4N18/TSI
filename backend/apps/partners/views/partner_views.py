"""Vistas de registro, consulta y asignacion de plan (CU-O48, RF-PON-012)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.domain_constants import EJECUTADO_POR_ADMINISTRADOR
from apps.partners.idempotency import (
    SCOPE_PLAN,
    SCOPE_REGISTRO,
    get_cached_response,
    store_response,
)
from apps.partners.permissions import (
    EsDesarrolladorAPIs,
    EsPartnerOGestor,
    PropiedadPartnerError,
    verificar_propiedad,
)
from apps.partners.services.audit_partner_service import AuditPartnerService
from apps.partners.services.asignar_plan_acceso_service import (
    AsignarPlanAccesoService,
    AsignarPlanError,
)
from apps.partners.services.consulta_partner_service import (
    ConsultaPartnerError,
    ConsultaPartnerService,
)
from apps.partners.services.registro_partner_service import (
    RegistroPartnerError,
    RegistroPartnerService,
)
from apps.soporte_cliente.services.cliente_lookup_service import ClienteLookupService
from core.api.response_envelope import error_response, success_response
from core.pinot.client import PinotClient
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.partners.plan_read_repository import PlanReadRepository

# Mapa unico codigo de dominio -> HTTP. Centralizado para que dos endpoints no
# devuelvan codigos distintos ante el mismo fallo.
_HTTP_POR_CODIGO = {
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "not_found": status.HTTP_404_NOT_FOUND,
    "partner_duplicado": status.HTTP_409_CONFLICT,
    "partner_suspendido": status.HTTP_409_CONFLICT,
    "sin_suscripcion": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "plan_incompleto": status.HTTP_422_UNPROCESSABLE_ENTITY,
}
_ERROR_POR_HTTP = {400: "bad_request", 404: "not_found", 409: "conflict", 422: "unprocessable_entity"}


def idusuario_de(request) -> int | None:
    """El actor autenticado, para la auditoria. None si no se puede resolver."""
    return getattr(getattr(request, "user", None), "idusuario", None)


def _fallo(exc) -> "object":
    code = getattr(exc, "code", "validation_error")
    http = _HTTP_POR_CODIGO.get(code, status.HTTP_400_BAD_REQUEST)
    cuerpo = error_response(_ERROR_POR_HTTP.get(http, "bad_request"), exc.detail, code, status_code=http)
    for clave, valor in getattr(exc, "extra", {}).items():
        cuerpo.data[clave] = valor
    return cuerpo


class PartnersView(APIView):
    """POST registra un partner (CU-O48); GET lista (RF-PON-012)."""

    permission_classes = [EsDesarrolladorAPIs]

    def post(self, request):
        if (cacheada := get_cached_response(request, SCOPE_REGISTRO)) is not None:
            return cacheada
        datos = request.data
        faltan = [
            c
            for c in ("idcliente", "nombrepartner", "contacto_tecnico_nombre", "contacto_tecnico_gmail")
            if datos.get(c) in (None, "")
        ]
        if faltan:
            return error_response(
                "bad_request", f"Faltan campos obligatorios: {', '.join(faltan)}",
                "validation_error", status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            partner = RegistroPartnerService().registrar(
                idcliente=int(datos["idcliente"]),
                nombrepartner=str(datos["nombrepartner"]),
                contacto_tecnico_nombre=str(datos["contacto_tecnico_nombre"]),
                contacto_tecnico_gmail=str(datos["contacto_tecnico_gmail"]),
                ejecutado_por=EJECUTADO_POR_ADMINISTRADOR,
            )
        except (ValueError, TypeError):
            return error_response(
                "bad_request", "idcliente debe ser un entero", "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except RegistroPartnerError as exc:
            return _fallo(exc)
        AuditPartnerService().log_registro(
            idpartner=int(partner["idpartner"]),
            idusuario=idusuario_de(request),
            campos={
                "idcliente": partner.get("idcliente"),
                "nombrepartner": partner.get("nombrepartner"),
                "contacto_tecnico_gmail": partner.get("contacto_tecnico_gmail"),
            },
        )
        respuesta = success_response(partner, status_code=status.HTTP_201_CREATED)
        store_response(request, SCOPE_REGISTRO, respuesta)
        return respuesta

    def get(self, request):
        cursor = request.query_params.get("cursor")
        resultado = ConsultaPartnerService().listar(
            limit=max(1, min(int(request.query_params.get("limit", 20)), 100)),
            cursor=int(cursor) if cursor else None,
            estado=request.query_params.get("estado"),
        )
        return success_response(
            resultado["items"],
            meta={
                "pagination": {
                    "next_cursor": resultado["next_cursor"],
                    "limit": resultado["limit"],
                }
            },
        )


class PartnerDetalleView(APIView):
    """GET detalle con credenciales e historial. Nunca expone el secreto."""

    permission_classes = [EsPartnerOGestor]

    def get(self, request, idpartner: int):
        servicio = ConsultaPartnerService()
        try:
            detalle = servicio.detalle(int(idpartner))
        except ConsultaPartnerError as exc:
            return _fallo(exc)
        try:
            verificar_propiedad(request, detalle)
        except PropiedadPartnerError as exc:
            AuditPartnerService().log_denegacion(
                idpartner=int(idpartner), idusuario=idusuario_de(request), motivo=str(exc)
            )
            return error_response(
                "forbidden", str(exc), "propiedad_partner", status_code=status.HTTP_403_FORBIDDEN
            )
        return success_response(detalle)


class ClientesElegiblesView(APIView):
    """GET /partners/clientes-elegibles — clientes sobre los que SE PUEDE registrar.

    BE-DELTA-03. El formulario de alta debe dejar elegir el cliente por nombre
    legible; pedir el `idcliente` a mano esta prohibido (design-system § 5), y
    no existia ningun endpoint que expusiera clientes. Sin esto el combobox
    queda vacio y el registro es inalcanzable desde la UI.

    Devuelve solo los ELEGIBLES —suscripcion vigente y sin partner previo—, de
    modo que dos rechazos del backend (`sin_suscripcion` 422 y
    `partner_duplicado` 409) dejan de poder ocurrir por eleccion del usuario.
    Prevenir el error es mejor que explicarlo (Principio IV).
    """

    permission_classes = [EsDesarrolladorAPIs]

    def get(self, request):
        pinot = PinotClient()
        # Se ordena en Python y no con ORDER BY: el orden alfabetico es una
        # decision de presentacion, y asi la consulta se mantiene trivial.
        clientes = pinot.query("SELECT * FROM Dim_Cliente LIMIT 1000", {})
        if not clientes:
            return success_response([])

        con_partner = {
            int(fila["idcliente"])
            for fila in pinot.query(
                "SELECT idcliente FROM Dim_Partner LIMIT 10000", {}
            )
        }

        plan_read = PlanReadRepository(pinot=pinot)
        elegibles = []
        for cliente in clientes:
            # `Dim_Cliente` no tiene columna `activo`: la baja se expresa en
            # `estado`. Verificado contra el esquema real, no supuesto.
            if str(cliente.get("estado", "Activo")).strip().lower() not in ("activo", ""):
                continue
            idcliente = int(cliente["idcliente"])
            if idcliente in con_partner:
                continue
            if plan_read.suscripcion_vigente(idcliente) is None:
                continue
            elegibles.append({"idcliente": idcliente, "nombre": cliente.get("nombre", "")})

        elegibles.sort(key=lambda c: str(c["nombre"]).lower())
        return success_response(elegibles)


class MiPartnerView(APIView):
    """GET /partners/me — el perfil del partner del usuario autenticado.

    BE-DELTA-01. Sin este endpoint el portal del partner es inalcanzable: el
    token de sesion solo lleva `idusuario`, y todos los demas endpoints del
    modulo exigen `{idpartner}` en la ruta. Un partner no tiene forma de
    averiguar su propio id, porque `GET /partners` es de gestores.

    No relaja ningun control: resuelve el partner a partir del cliente del
    propio usuario, asi que por construccion solo puede devolver el suyo.
    """

    permission_classes = [EsPartnerOGestor]

    def get(self, request):
        idusuario = idusuario_de(request)
        if idusuario is None:
            return error_response(
                "unauthorized", "No se pudo resolver el usuario autenticado",
                "no_autenticado", status_code=status.HTTP_401_UNAUTHORIZED,
            )

        idcliente = ClienteLookupService().resolve_idcliente(int(idusuario))
        if idcliente is None:
            return error_response(
                "not_found",
                "Tu usuario no está asociado a ningún cliente",
                "sin_cliente",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        partner = PartnerRepository().find_by_cliente(int(idcliente))
        if not partner:
            return error_response(
                "not_found",
                "Tu usuario aún no tiene un perfil de partner asociado",
                "sin_partner",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            detalle = ConsultaPartnerService().detalle(int(partner["idpartner"]))
        except ConsultaPartnerError as exc:
            return _fallo(exc)
        return success_response(detalle)


class AsignarPlanAccesoView(APIView):
    """POST asigna el plan derivando el cupo del contratado (RF-PON-003)."""

    permission_classes = [EsDesarrolladorAPIs]

    def post(self, request, idpartner: int):
        if (cacheada := get_cached_response(request, SCOPE_PLAN)) is not None:
            return cacheada
        try:
            partner = AsignarPlanAccesoService().asignar(
                idpartner=int(idpartner), ejecutado_por=EJECUTADO_POR_ADMINISTRADOR
            )
        except AsignarPlanError as exc:
            return _fallo(exc)
        AuditPartnerService().log_asignacion_plan(
            idpartner=int(idpartner),
            idusuario=idusuario_de(request),
            plan=str(partner.get("planapi", "")),
            limite_mes=int(partner.get("limitellamadasmes", 0)),
        )
        respuesta = success_response(partner)
        store_response(request, SCOPE_PLAN, respuesta)
        return respuesta
