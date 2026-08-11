"""Fact_LogLlamadaAPI — detalle tecnico de TODAS las peticiones (RF-APM-004).

Diferencia con `Fact_APIIntegracion`
------------------------------------
Aquella registra solo lo **atendido y facturable**. Esta registra **todo lo que
llego**, incluidas las rechazadas: 4xx, 5xx y los 429 del throttle. Es el
material con el que el partner se autodiagnostica (RN-APM-009) y con el que el
Desarrollador de APIs vigila la plataforma.

Que un 429 aparezca aqui y no alli no es una inconsistencia: es la distincion
entre «te limite el ritmo» y «te cobro esta llamada» (§ 15 D2).

Append-only, sin excepciones
----------------------------
No expone `update` ni `delete` (RNF-APM-005). No es una convencion que haya que
recordar: son capacidades que no existen, igual que en
`HistorialAccesoRepository` de #07.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter

# `iporigen` es INT (IPv4 numerica) conforme al esquema existente, no STRING.
SIN_IP = 0


class LogLlamadaRepository:
    TOPIC = settings.KAFKA_TOPICS["log_llamada_api"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        filas = self.pinot.query(
            "SELECT MAX(idlogllamadaapi) AS max_id FROM Fact_LogLlamadaAPI LIMIT 1", {}
        )
        return int(filas[0]["max_id"] or 0) + 1 if filas else 1

    @staticmethod
    def ip_a_entero(ip: str | None) -> int:
        """IPv4 en notacion decimal -> INT. Devuelve el centinela si no es valida."""
        if not ip:
            return SIN_IP
        partes = str(ip).split(".")
        if len(partes) != 4:
            return SIN_IP
        try:
            octetos = [int(p) for p in partes]
        except ValueError:
            return SIN_IP
        if any(o < 0 or o > 255 for o in octetos):
            return SIN_IP
        return (octetos[0] << 24) + (octetos[1] << 16) + (octetos[2] << 8) + octetos[3]

    # --- Escritura (solo INSERT) ---------------------------------------------

    def registrar(
        self,
        *,
        idpartner: int,
        idcredencialapi: int,
        endpoint: str,
        metodohttp: str,
        codigohttp: int,
        latenciams: float,
        iporigen: str | int | None = None,
        fechallamada: int | None = None,
    ) -> dict[str, Any]:
        """Registra una peticion, se haya atendido o no.

        Los 4xx/5xx se registran igual que los 200: son el material de
        autodiagnostico del partner (RN-APM-009).
        """
        ahora = self._now_ms()
        ip = iporigen if isinstance(iporigen, int) else self.ip_a_entero(iporigen)
        fila = {
            "idlogllamadaapi": self._next_id(),
            "idpartner": int(idpartner),
            "idcredencialapi": int(idcredencialapi),
            "endpoint": endpoint,
            "metodohttp": metodohttp,
            "codigohttp": int(codigohttp),
            "latenciams": float(latenciams),
            "iporigen": ip,
            "fechallamada": fechallamada if fechallamada is not None else ahora,
            "fecha_actualizacion": ahora,
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila

    # --- Lecturas -------------------------------------------------------------

    def list_by_partner(
        self,
        idpartner: int,
        *,
        limit: int = 200,
        solo_errores: bool = False,
        codigohttp: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        cursor: int | None = None,
        cursor_fecha: int | None = None,
        idcredencialapi: int | None = None,
        endpoint: str | None = None,
    ) -> list[dict[str, Any]]:
        """Historial del partner, mas reciente primero.

        Desempate por `idlogllamadaapi`: dos peticiones pueden caer en el mismo
        milisegundo y entonces la fecha sola no basta para ordenarlas.

        **Todo se filtra aqui, contra la base.** La consola no guarda una
        ventana en memoria para filtrarla despues: cada cambio de filtro es una
        consulta nueva, igual que en el resto del sistema. Filtrar en cliente
        daria una falsa sensacion de exhaustividad —el usuario creeria que no
        hay ningun 500 en su historia cuando solo no lo hay en la ultima
        pagina— y ademas rompe la paginacion, porque el recuento de la pagina
        dejaria de coincidir con lo que el servidor devolvio.

        Paginacion por cursor COMPUESTO
        --------------------------------
        El cursor son los **dos** campos por los que se ordena: `cursor_fecha`
        (`fechallamada`) y `cursor` (`idlogllamadaapi`) de la ultima fila
        devuelta. La condicion replica exactamente el `ORDER BY`:

            fechallamada < cf  OR  (fechallamada = cf AND idlogllamadaapi < c)

        **Por que compuesto y no solo el id.** La primera version usaba solo
        `idlogllamadaapi < cursor`, dando por hecho que el id ordena igual que
        la fecha. Esa suposicion **no esta garantizada por nada**: en cuanto los
        ids no descienden con la fecha —datos sembrados, un backfill, una
        reingesta— el cursor salta a un punto que no corresponde y la pagina
        siguiente **repite filas o se salta otras, en silencio**. Se detecto
        paginando contra Pinot real: la segunda pagina repitio 4 de 5 filas.

        Paginar por la misma clave por la que se ordena elimina la suposicion en
        vez de confiar en ella.
        """
        filtros = ["idpartner = %(idpartner)s"]
        params: dict[str, Any] = {"idpartner": idpartner, "limit": limit}

        if solo_errores:
            filtros.append("codigohttp >= 400")
        if codigohttp is not None:
            # Un codigo concreto manda sobre `solo_errores`: pedir 200 con el
            # conmutador puesto no debe devolver vacio de forma silenciosa.
            filtros = [f for f in filtros if f != "codigohttp >= 400"]
            filtros.append("codigohttp = %(codigohttp)s")
            params["codigohttp"] = int(codigohttp)
        if desde_ms is not None:
            filtros.append("fechallamada >= %(desde)s")
            params["desde"] = int(desde_ms)
        if hasta_ms is not None:
            filtros.append("fechallamada < %(hasta)s")
            params["hasta"] = int(hasta_ms)
        if idcredencialapi is not None:
            filtros.append("idcredencialapi = %(idcredencialapi)s")
            params["idcredencialapi"] = int(idcredencialapi)
        if endpoint:
            filtros.append("endpoint = %(endpoint)s")
            params["endpoint"] = endpoint
        if cursor is not None and cursor_fecha is not None:
            # Replica exacta del ORDER BY: sin el parentesis, el OR se mezclaria
            # con los demas filtros y devolveria filas de otros partners.
            filtros.append(
                "(fechallamada < %(cursor_fecha)s "
                "OR (fechallamada = %(cursor_fecha)s AND idlogllamadaapi < %(cursor)s))"
            )
            params["cursor"] = int(cursor)
            params["cursor_fecha"] = int(cursor_fecha)

        return self.pinot.query(
            "SELECT * FROM Fact_LogLlamadaAPI WHERE "
            + " AND ".join(filtros)
            + " ORDER BY fechallamada DESC, idlogllamadaapi DESC LIMIT %(limit)s",
            params,
        )

    def contar_por_codigo(
        self, idpartner: int, *, desde_ms: int, hasta_ms: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Distribucion de codigos HTTP — incluye los 429 del throttle."""
        return self.pinot.query(
            "SELECT codigohttp, COUNT(*) AS total FROM Fact_LogLlamadaAPI "
            "WHERE idpartner = %(idpartner)s AND fechallamada >= %(desde)s "
            "AND fechallamada < %(hasta)s "
            "GROUP BY codigohttp ORDER BY total DESC LIMIT %(limit)s",
            {"idpartner": idpartner, "desde": desde_ms, "hasta": hasta_ms, "limit": limit},
        )
