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
import re

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
            version_contrato=self._version_declarada(request),
        )

    #: `/api/v1/...` -> `v1`. Es la misma forma que el modelo analítico deducía
    #: al cargar; lo que cambia es **cuándo** se resuelve.
    _VERSION = re.compile(r"^/api/(v\d+)/")

    #: Cabecera con la que un partner **declara** contra qué versión integra.
    #: Es lo único que convierte la versión en un hecho en vez de una lectura
    #: del path: `Dim_CredencialAPI` no guarda ninguna versión de contrato.
    CABECERA_VERSION = "HTTP_X_TSI_API_VERSION"

    @classmethod
    def _version_declarada(cls, request) -> str | None:
        """La versión que el partner declara, y si no, la del path.

        ⚠️ **Las dos no valen lo mismo, y el modelo lo distingue**: solo la
        declarada llega con `version_es_derivada = 0`. La del path se guarda
        igualmente —así una fila conserva la versión que era cierta cuando
        ocurrió la llamada, aunque el path cambie de forma después— pero sigue
        marcada como derivada, porque lo es.

        El prefijo `declarada:` es la marca que el cargador lee. Se eligió un
        prefijo y no una columna aparte para no volver a tocar el esquema de una
        tabla que recibe **todas** las peticiones.
        """
        declarada = (request.META.get(cls.CABECERA_VERSION) or "").strip()
        if declarada:
            return f"declarada:{declarada}"
        return cls._version_del_path(request.path)

    @classmethod
    def _version_del_path(cls, path: str) -> str | None:
        """La versión de contrato que sirvió esta petición, o ausente.

        ⚠️ Ausente y no `'desconocida'`: una ruta que no encaja con el patrón no
        es una versión rara, es que no la sabemos. El modelo ya distingue las
        dos cosas y rellenar aquí borraría la diferencia.
        """
        m = cls._VERSION.match(path or "")
        return m.group(1) if m else None

    @staticmethod
    def _ip_cliente(request) -> str | None:
        """La IP real del cliente, respetando el proxy si lo hay."""
        reenviada = request.META.get("HTTP_X_FORWARDED_FOR")
        if reenviada:
            return reenviada.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
