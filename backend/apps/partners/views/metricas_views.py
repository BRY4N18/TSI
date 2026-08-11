"""Lectura del consumo: metricas, consola de logs y reporte (CU-O52).

Las tres vistas usan **JWT humano**, no credencial de API: son pantallas, no la
API de datos. Esa separacion de superficies es deliberada (RF-APM-001).

Una regla que sorprende y es correcta
-------------------------------------
Un partner **suspendido si puede consultar sus metricas** (RN-APM-017). Es una
lectura que no afecta al estado y le sirve precisamente para entender por que
se le suspendio. Negarsela seria castigarlo dos veces y generar un ticket.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.permissions import (
    EsDesarrolladorAPIs,
    EsPartnerOGestor,
    PropiedadPartnerError,
    verificar_propiedad,
)
from apps.partners.services.metricas_consumo_service import (
    MetricasConsumoError,
    MetricasConsumoService,
)
from core.api.response_envelope import error_response, success_response
from core.repositories.partners.log_llamada_repository import LogLlamadaRepository
from core.repositories.partners.partner_repository import PartnerRepository

ENTORNOS_VALIDOS = ("Sandbox", "Producción")


def _entorno_de(request) -> str | None:
    """`Producción` por defecto: es lo que se factura (RN-APM-001)."""
    entorno = request.query_params.get("entorno", "Producción")
    return entorno if entorno in ENTORNOS_VALIDOS else None


class MetricasPartnerView(APIView):
    """GET /api/v1/partners/{idpartner}/metricas — consumo frente al cupo."""

    permission_classes = [EsPartnerOGestor]

    def get(self, request, idpartner: int):
        entorno = _entorno_de(request)
        if entorno is None:
            return error_response(
                "bad_request",
                f"entorno debe ser uno de {ENTORNOS_VALIDOS}",
                "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        partner = PartnerRepository().find_by_id(int(idpartner))
        try:
            # Control de propiedad: un partner no ve las metricas de otro. NO se
            # comprueba `activo`: un suspendido si puede leer las suyas.
            verificar_propiedad(request, partner)
        except PropiedadPartnerError as exc:
            return error_response(
                "forbidden", str(exc), "propiedad_partner",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        try:
            metricas = MetricasConsumoService().metricas_del_partner(
                int(idpartner), entorno=entorno
            )
        except MetricasConsumoError as exc:
            return error_response(
                "not_found", exc.detail, exc.code, status_code=status.HTTP_404_NOT_FOUND
            )
        return success_response(metricas)


class ConsolaLogsView(APIView):
    """GET /api/v1/logs-api — detalle tecnico de cada peticion.

    `idpartner` es **obligatorio**: se consulta partner por partner, no hay
    vista global.

    Quien puede consultarla (BE-DELTA-07, 2026-08-10)
    -------------------------------------------------
    Gestores sobre cualquier partner, y **el partner sobre el suyo**. Hasta esta
    fecha era exclusiva del Desarrollador de APIs, y eso **contradecia
    RN-APM-009**: la regla dice que los errores se registran con su codigo
    *«para que el partner pueda diagnosticar sus propios fallos sin escalar a un
    Administrador»*, y el permiso le impedia justamente eso. Se detecto al
    verificar el panel de consumo contra la app real: su bloque de errores
    recibia 403 y quedaba vacio.

    La propiedad se comprueba con `verificar_propiedad`, asi que un partner
    sigue sin poder leer los registros de otro.

    Filtros disponibles, **todos resueltos en la base**: `solo_errores`,
    `codigohttp`, `desde`, `hasta`, `idcredencialapi` y `endpoint`. Y paginacion
    real por `cursor`, que es el `idlogllamadaapi` de la ultima fila anterior.

    Los seis los declaraba ya el contrato OpenAPI; hasta 2026-08-10 la
    implementacion solo honraba `solo_errores`, asi que el contrato prometia mas
    de lo que el codigo daba.
    """

    permission_classes = [EsPartnerOGestor]

    def get(self, request):
        idpartner = request.query_params.get("idpartner")
        if not idpartner:
            return error_response(
                "bad_request",
                "idpartner es obligatorio: la consola se consulta por partner",
                "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        def _entero(nombre: str) -> int | None:
            valor = request.query_params.get(nombre)
            return int(valor) if valor not in (None, "") else None

        try:
            limit = max(1, min(int(request.query_params.get("limit", 50)), 500))
            idpartner = int(idpartner)
            codigohttp = _entero("codigohttp")
            desde_ms = _entero("desde")
            hasta_ms = _entero("hasta")
            cursor = _entero("cursor")
            cursor_fecha = _entero("cursor_fecha")
            idcredencialapi = _entero("idcredencialapi")
        except (TypeError, ValueError):
            return error_response(
                "bad_request",
                "idpartner, limit, codigohttp, desde, hasta, cursor e "
                "idcredencialapi deben ser enteros",
                "validation_error", status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Un partner solo ve SUS registros; los gestores, los de cualquiera.
        partner = PartnerRepository().find_by_id(idpartner)
        if partner is None:
            # 404, no 403: que el partner no exista no es un problema de
            # permisos, y `verificar_propiedad` confunde los dos casos al
            # tratar `None` como propiedad ajena.
            return error_response(
                "not_found", "Partner no encontrado", "not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        try:
            verificar_propiedad(request, partner)
        except PropiedadPartnerError as exc:
            return error_response(
                "forbidden", str(exc), "propiedad_partner",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        solo_errores = request.query_params.get("solo_errores", "false").lower() == "true"
        # TODOS los filtros van a la base. La consola no guarda una ventana en
        # memoria para filtrarla despues: cada cambio es una consulta, como en
        # el resto del sistema. Ademas es lo unico coherente con la paginacion,
        # porque filtrar en cliente descuadraria el recuento de cada pagina.
        filas = LogLlamadaRepository().list_by_partner(
            idpartner,
            limit=limit + 1,
            solo_errores=solo_errores,
            codigohttp=codigohttp,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
            cursor=cursor,
            cursor_fecha=cursor_fecha,
            idcredencialapi=idcredencialapi,
            endpoint=request.query_params.get("endpoint") or None,
        )

        # Paginacion por cursor: se pide uno de mas para saber si hay siguiente.
        hay_mas = len(filas) > limit
        pagina = filas[:limit]
        # El cursor es COMPUESTO —los dos campos del ORDER BY— porque el id no
        # ordena necesariamente igual que la fecha. Con solo el id, la pagina
        # siguiente repite o se salta filas en silencio.
        ultimo = pagina[-1] if hay_mas and pagina else None
        return success_response(
            pagina,
            meta={
                "pagination": {
                    "next_cursor": ultimo["idlogllamadaapi"] if ultimo else None,
                    "next_cursor_fecha": ultimo["fechallamada"] if ultimo else None,
                    "limit": limit,
                }
            },
        )


class ReporteConsumoView(APIView):
    """GET /api/v1/reportes-consumo — reporte mensual del partner.

    Un mes sin consumo devuelve **ceros**, no un 404: que el partner no
    consumiera es una respuesta valida, no la ausencia del reporte.
    """

    permission_classes = [EsPartnerOGestor]

    def get(self, request):
        try:
            idpartner = int(request.query_params["idpartner"])
            anio = int(request.query_params["anio"])
            mes = int(request.query_params["mes"])
        except (KeyError, TypeError, ValueError):
            return error_response(
                "bad_request",
                "idpartner, anio y mes son obligatorios y deben ser enteros",
                "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not 1 <= mes <= 12:
            return error_response(
                "bad_request", "mes debe estar entre 1 y 12", "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        partner = PartnerRepository().find_by_id(idpartner)
        try:
            verificar_propiedad(request, partner)
        except PropiedadPartnerError as exc:
            return error_response(
                "forbidden", str(exc), "propiedad_partner",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        try:
            reporte = MetricasConsumoService().reporte_mensual(
                idpartner, anio=anio, mes=mes
            )
        except MetricasConsumoError as exc:
            return error_response(
                "not_found", exc.detail, exc.code, status_code=status.HTTP_404_NOT_FOUND
            )
        return success_response(reporte)
