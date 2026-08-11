"""Registro de cada llamada en el instante (RF-APM-004).

Dos tablas, dos criterios distintos
-----------------------------------
- `Fact_LogLlamadaAPI` recibe **todas** las peticiones, incluidas 4xx, 5xx y los
  429 del throttle: es el material de autodiagnostico del partner (RN-APM-009).
- `Fact_APIIntegracion` recibe solo las **atendidas**. Un 429 no genera fila:
  no se atendio, no es consumo facturable (§ 15 D2).

Esa asimetria no es un descuido: es la diferencia entre «te limite el ritmo» y
«te cobro esta llamada».

El registro nunca rompe la respuesta
------------------------------------
`registrar_llamada` captura cualquier fallo de publicacion y lo deja en el log
de aplicacion en vez de propagarlo (RN-APM-005). El partner ya recibio sus
datos; perder la metrica es un problema de reconciliacion, no motivo para
convertir un 200 en un 500.
"""

from __future__ import annotations

import logging
from typing import Any

from core.repositories.partners.api_integracion_repository import (
    ApiIntegracionRepository,
)
from core.repositories.partners.estado_integracion_repository import (
    EstadoIntegracionRepository,
)
from core.repositories.partners.log_llamada_repository import LogLlamadaRepository

logger = logging.getLogger("tsi.partners.consumo")

# Codigos en los que la peticion **no se atendio**: se rechazo en la puerta sin
# entregar datos ni hacer trabajo en nombre del partner. No son consumo
# facturable (§ 15 D2, T019).
#
#   401 credencial invalida, revocada o vencida
#   403 partner suspendido, suscripcion no vigente, o alcance no contratado
#   429 throttle: se le limito el ritmo
#
# Un 404 o un 500 SI cuentan: ahi si se proceso la peticion y se le respondio;
# son errores del servicio, no rechazos de acceso, y por eso `errores` los
# distingue dentro de la fila.
CODIGOS_NO_ATENDIDOS = frozenset({401, 403, 429})

HTTP_THROTTLED = 429

# Servicio por defecto cuando la ruta no lo identifica. `Dim_Servicio` 2 es
# «API Registro de accidentes», el unico servicio de datos expuesto hoy.
ID_SERVICIO_DATOS = 2


class RegistroConsumoService:
    def __init__(
        self,
        api_integracion: ApiIntegracionRepository | None = None,
        logs: LogLlamadaRepository | None = None,
        estados: EstadoIntegracionRepository | None = None,
    ):
        self.api_integracion = api_integracion or ApiIntegracionRepository()
        self.logs = logs or LogLlamadaRepository()
        self.estados = estados or EstadoIntegracionRepository()

    def registrar_llamada(
        self,
        *,
        idpartner: int,
        idcliente: int,
        idcredencial: int,
        entorno: str,
        endpoint: str,
        metodohttp: str,
        codigohttp: int,
        latencia_ms: float,
        idservicio: int = ID_SERVICIO_DATOS,
        iporigen: str | None = None,
    ) -> dict[str, Any]:
        """Registra la peticion. **Nunca lanza**: devuelve que se escribio.

        El resultado (`{'log': bool, 'consumo': bool}`) existe para que los
        tests puedan afirmar la regla contable del 429 sin leer el almacen.
        """
        escrito = {"log": False, "consumo": False}

        try:
            self.logs.registrar(
                idpartner=idpartner,
                idcredencialapi=idcredencial,
                endpoint=endpoint,
                metodohttp=metodohttp,
                codigohttp=codigohttp,
                latenciams=latencia_ms,
                iporigen=iporigen,
            )
            escrito["log"] = True
        except Exception:  # noqa: BLE001 — el registro no puede tumbar la respuesta
            logger.exception(
                "consumo_log_fallido",
                extra={"idpartner": idpartner, "endpoint": endpoint},
            )

        if int(codigohttp) in CODIGOS_NO_ATENDIDOS:
            # No se atendio: no es consumo facturable. La fila del log de arriba
            # es la que deja constancia de lo ocurrido —que se le limito el
            # ritmo, o que se le denego el acceso— para que el partner pueda
            # diagnosticarlo (RN-APM-009).
            return escrito

        try:
            self.api_integracion.registrar(
                idpartner=idpartner,
                idcliente=idcliente,
                idservicio=idservicio,
                idestadointegracion=self.estados.estado_para_entorno(entorno),
                entorno=entorno,
                codigohttp=codigohttp,
                latencia=latencia_ms,
            )
            escrito["consumo"] = True
        except Exception:  # noqa: BLE001 — idem: reconciliar despues, no fallar ahora
            logger.exception(
                "consumo_metrica_fallida",
                extra={
                    "idpartner": idpartner,
                    "entorno": entorno,
                    "endpoint": endpoint,
                    "codigohttp": codigohttp,
                },
            )

        return escrito
