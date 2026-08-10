"""Vistas de emision y listado de credenciales (CU-O49, RF-PON-004/005)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.domain_constants import (
    EJECUTADO_POR_PARTNER,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    ESTADO_PRODUCCION_ACTIVA,
)
from apps.partners.idempotency import (
    SCOPE_EMISION,
    get_cached_response,
    store_response,
)
from apps.partners.permissions import (
    EsPartnerOGestor,
    PropiedadPartnerError,
    verificar_propiedad,
)
from apps.partners.services.audit_partner_service import AuditPartnerService
from apps.partners.services.consulta_partner_service import ConsultaPartnerService
from apps.partners.services.emitir_credencial_service import (
    EmitirCredencialError,
    EmitirCredencialService,
)
from core.repositories.partners.partner_repository import PartnerRepository
from core.api.response_envelope import error_response, success_response

_HTTP_POR_CODIGO = {
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "not_found": status.HTTP_404_NOT_FOUND,
    "sin_plan": status.HTTP_409_CONFLICT,
    "nombre_duplicado": status.HTTP_409_CONFLICT,
    "partner_suspendido": status.HTTP_409_CONFLICT,
}
_ERROR_POR_HTTP = {400: "bad_request", 404: "not_found", 409: "conflict"}


class CredencialesView(APIView):
    """POST emite una credencial de pruebas; GET lista (sin secretos)."""

    permission_classes = [EsPartnerOGestor]

    def _partner_o_403(self, request, idpartner: int):
        partner = PartnerRepository().find_by_id(int(idpartner))
        verificar_propiedad(request, partner)
        return partner

    @staticmethod
    def _promocion_aprobada(idpartner: int) -> bool:
        """True solo si el estado derivado ya es «Producción activa».

        Se apoya en el estado derivado —no en un flag propio— porque es la
        misma fuente que usa el resto del modulo: la aprobacion del
        Administrador es lo unico que puede producirlo (RF-PON-008).
        """
        try:
            detalle = ConsultaPartnerService().detalle(int(idpartner))
        except Exception:  # noqa: BLE001 — ante la duda, se deniega (fail-closed)
            return False
        return detalle.get("estado") == ESTADO_PRODUCCION_ACTIVA

    def post(self, request, idpartner: int):
        # Antes de cualquier efecto: un reintento con la misma clave debe
        # devolver el MISMO secreto, no emitir una credencial nueva y perder
        # el secreto anterior para siempre (RN-PON-005).
        if (cacheada := get_cached_response(request, SCOPE_EMISION)) is not None:
            return cacheada
        entorno = str(request.data.get("entorno") or ENTORNO_SANDBOX)

        # BE-DELTA-02 — produccion sigue exigiendo aprobacion previa
        # (RN-PON-004); lo que cambia es DONDE se comprueba. Antes era un 403
        # incondicional, y el secreto productivo acababa en manos del
        # Administrador que aprobaba, sin canal seguro para entregarlo. Ahora
        # la guarda se condiciona al estado derivado que produjo esa misma
        # aprobacion, de modo que emite —y ve el secreto— quien debe
        # custodiarlo (RN-PON-005).
        if entorno == ENTORNO_PRODUCCION and not self._promocion_aprobada(idpartner):
            return error_response(
                "forbidden",
                "Las credenciales de producción requieren una promoción aprobada "
                "por un Administrador",
                "produccion_requiere_aprobacion",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        try:
            self._partner_o_403(request, idpartner)
        except PropiedadPartnerError as exc:
            AuditPartnerService().log_denegacion(
                idpartner=int(idpartner),
                idusuario=getattr(getattr(request, "user", None), "idusuario", None),
                motivo=str(exc),
            )
            return error_response(
                "forbidden", str(exc), "propiedad_partner", status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            credencial = EmitirCredencialService().emitir(
                idpartner=int(idpartner),
                nombre_credencial=str(request.data.get("nombre_credencial") or ""),
                entorno=entorno,
                ejecutado_por=EJECUTADO_POR_PARTNER,
            )
        except EmitirCredencialError as exc:
            http = _HTTP_POR_CODIGO.get(exc.code, status.HTTP_400_BAD_REQUEST)
            return error_response(
                _ERROR_POR_HTTP.get(http, "bad_request"), exc.detail, exc.code, status_code=http
            )

        # Se audita QUE credencial se emitio; el saneado de AuditPartnerService
        # garantiza que `client_secret` no pueda acabar en el log (RN-PON-005).
        AuditPartnerService().log_emision_credencial(
            idpartner=int(idpartner),
            idusuario=getattr(getattr(request, "user", None), "idusuario", None),
            idcredencial=int(credencial.get("idcredencial", -1)),
            nombre_credencial=str(credencial.get("nombre_credencial", "")),
            entorno=str(credencial.get("entorno", "")),
        )
        respuesta = success_response(credencial, status_code=status.HTTP_201_CREATED)
        store_response(request, SCOPE_EMISION, respuesta)
        return respuesta

    def get(self, request, idpartner: int):
        try:
            self._partner_o_403(request, idpartner)
        except PropiedadPartnerError as exc:
            return error_response(
                "forbidden", str(exc), "propiedad_partner", status_code=status.HTTP_403_FORBIDDEN
            )

        filtros = {}
        if request.query_params.get("entorno"):
            filtros["entorno"] = request.query_params["entorno"]
        if request.query_params.get("solo_activas", "true").lower() == "true":
            filtros["solo_activas"] = True

        return success_response(
            ConsultaPartnerService().credenciales_de(int(idpartner), **filtros)
        )
