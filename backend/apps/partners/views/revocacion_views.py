"""Revocacion de credencial comprometida (CU-O55, RF-PAC-001/002).

**Solo JWT.** Esta vista NO acepta autenticacion por credencial de API, y no es
un descuido de configuracion: si se pudiera revocar con una credencial, el
atacante que ya robo una podria revocar las demas del partner y dejarlo fuera de
su propia integracion. Le estariamos dando la herramienta de sabotaje
(`research.md` Decision 1).

El `Idempotency-Key` usa el ambito de emision porque la respuesta **lleva el
secreto del reemplazo**: TTL de 60 s en vez de 300 (`idempotency.py`).
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.idempotency import (
    SCOPE_EMISION,
    get_cached_response,
    store_response,
)
from apps.partners.permissions import EsPartnerOGestor, verificar_propiedad
from apps.partners.permissions import PropiedadPartnerError
from apps.partners.services.audit_partner_service import AuditPartnerService
from apps.partners.services.emitir_credencial_service import EmitirCredencialError
from apps.partners.services.revocar_credencial_service import (
    RevocarCredencialError,
    RevocarCredencialService,
)
from core.api.response_envelope import error_response, success_response
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.partner_repository import PartnerRepository

_HTTP_POR_CODIGO = {
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "not_found": status.HTTP_404_NOT_FOUND,
    "propiedad_credencial": status.HTTP_403_FORBIDDEN,
    "credencial_inactiva": status.HTTP_409_CONFLICT,
}
_ERROR_POR_HTTP = {
    400: "bad_request",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
}


class RevocarCredencialView(APIView):
    """POST /api/v1/credenciales/{idcredencial}/revocar"""

    permission_classes = [EsPartnerOGestor]

    def post(self, request, idcredencial: int):
        # Antes de cualquier efecto: un reintento de red no puede revocar dos
        # veces ni perder el secreto del primer reemplazo.
        if (cacheada := get_cached_response(request, SCOPE_EMISION)) is not None:
            return cacheada

        credencial = CredencialRepository().find_by_id(int(idcredencial))
        if not credencial:
            return error_response(
                "not_found",
                "Credencial no encontrada",
                "not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Doble guarda de propiedad. La del servicio compara el `idpartner` de la
        # credencial con el del actor; esta comprueba que el actor pueda operar
        # sobre ese partner en absoluto (un partner de OTRO cliente ni siquiera
        # debe llegar a la comparacion).
        partner = PartnerRepository().find_by_id(int(credencial["idpartner"]))
        try:
            verificar_propiedad(request, partner)
        except PropiedadPartnerError as exc:
            AuditPartnerService().log_denegacion(
                idpartner=int(credencial["idpartner"]),
                idusuario=getattr(getattr(request, "user", None), "idusuario", None),
                motivo=str(exc),
            )
            return error_response(
                "forbidden", str(exc), "propiedad_partner",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        try:
            resultado = RevocarCredencialService().revocar(
                idcredencial=int(idcredencial),
                idpartner_actor=int(credencial["idpartner"]),
                motivo=str(request.data.get("motivo") or ""),
            )
        except RevocarCredencialError as exc:
            http = _HTTP_POR_CODIGO.get(exc.code, status.HTTP_400_BAD_REQUEST)
            return error_response(
                _ERROR_POR_HTTP.get(http, "bad_request"), exc.detail, exc.code,
                status_code=http,
            )
        except EmitirCredencialError as exc:
            # El reemplazo fallo DESPUES de desactivar la original. Se informa
            # con claridad en vez de fingir exito: la credencial comprometida ya
            # esta cortada (que es lo urgente), pero el partner necesita saber
            # que debe emitir el reemplazo a mano.
            return error_response(
                "conflict",
                f"Credencial revocada, pero el reemplazo no pudo emitirse: {exc.detail}",
                "reemplazo_fallido",
                status_code=status.HTTP_409_CONFLICT,
            )

        AuditPartnerService().log_emision_credencial(
            idpartner=int(credencial["idpartner"]),
            idusuario=getattr(getattr(request, "user", None), "idusuario", None),
            idcredencial=int(resultado["reemplazo"]["idcredencial"]),
            nombre_credencial=str(resultado["reemplazo"].get("nombre_credencial", "")),
            entorno=str(resultado["reemplazo"].get("entorno", "")),
        )
        respuesta = success_response(resultado)
        store_response(request, SCOPE_EMISION, respuesta)
        return respuesta
