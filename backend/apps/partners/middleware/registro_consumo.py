"""Middleware que mide y registra cada llamada a `/datos/*` (RF-APM-004).

Por que un middleware y no una linea en cada vista
--------------------------------------------------
Porque asi **no se puede olvidar**. Una vista nueva de datos queda medida sin
que su autor tenga que acordarse, y las respuestas de error —incluidas las que
DRF genera antes de entrar a la vista, como el 429 del throttle— tambien se
registran. Poner el registro dentro de las vistas dejaria fuera justo esos
casos, que son los que mas le interesan al partner (RN-APM-009).

Fuera del camino critico
------------------------
La medicion envuelve la respuesta pero **nunca la altera**: todo el registro va
en un `try/except` que no propaga (RN-APM-005). El partner ya tiene sus datos;
perder una metrica es un problema de reconciliacion, no motivo para convertir
un 200 en un 500.
"""

from __future__ import annotations

import logging
import time

from apps.partners.authentication import PartnerAPIUser
from apps.partners.services.registro_consumo_service import RegistroConsumoService

logger = logging.getLogger("tsi.partners.consumo")

# Solo se mide la API de datos. Las pantallas de gestion no son consumo del
# partner y no deben ensuciar sus metricas ni su facturacion.
PREFIJO_DATOS = "/api/v1/datos/"


class RegistroConsumoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._servicio: RegistroConsumoService | None = None

    def _registro(self) -> RegistroConsumoService:
        # Perezoso: construirlo en __init__ obligaria a tener Pinot arriba al
        # arrancar Django, incluso para comandos que no tocan la API.
        if self._servicio is None:
            self._servicio = RegistroConsumoService()
        return self._servicio

    def __call__(self, request):
        if not request.path.startswith(PREFIJO_DATOS):
            return self.get_response(request)

        inicio = time.perf_counter()
        respuesta = self.get_response(request)
        latencia_ms = (time.perf_counter() - inicio) * 1000

        try:
            self._registrar(request, respuesta, latencia_ms)
        except Exception:  # noqa: BLE001 — el registro jamas altera la respuesta
            logger.exception("registro_consumo_middleware_fallido", extra={"ruta": request.path})

        return respuesta

    def _registrar(self, request, respuesta, latencia_ms: float) -> None:
        usuario = getattr(request, "user", None)
        if not isinstance(usuario, PartnerAPIUser):
            # Peticion sin credencial valida (401 por cabeceras ausentes o
            # invalidas): no hay partner al que atribuirle la llamada.
            return

        self._registro().registrar_llamada(
            idpartner=usuario.idpartner,
            idcliente=usuario.idcliente,
            idcredencial=usuario.idcredencial,
            entorno=usuario.entorno,
            endpoint=request.path,
            metodohttp=request.method,
            codigohttp=respuesta.status_code,
            latencia_ms=latencia_ms,
            iporigen=self._ip_cliente(request),
        )

    @staticmethod
    def _ip_cliente(request) -> str | None:
        """La IP real del cliente, respetando el proxy si lo hay."""
        reenviada = request.META.get("HTTP_X_FORWARDED_FOR")
        if reenviada:
            return reenviada.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
