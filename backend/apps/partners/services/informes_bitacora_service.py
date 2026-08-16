"""Servicio de cambios de acceso — L3 de OT08/OT09.

**Cada tipo de cambio conserva su valor propio.** En particular, la revocación
decidida por el partner y la desactivación en cascada por suspensión llegan con
tipos distintos.

Agruparlas pondría en la misma línea una **decisión de seguridad** y un **impago
administrativo**. Quien reactivara guiándose por un listado así resucitaría una
credencial comprometida — exactamente lo que la regla de reactivación selectiva
previene.

Y **la reactivación sin motivo es correcta** (research D6): el SRS exige motivo
al cortar el acceso, no al devolverlo.
"""

from __future__ import annotations

from typing import Any

from apps.partners.domain_constants import SIN_CREDENCIAL, SIN_MOTIVO
from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.partners.informes_bitacora_repository import (
    CURSOR_BITACORA,
    ORDEN_BITACORA,
    InformesBitacoraRepository,
)


class InformesBitacoraService:
    def __init__(self, repo: InformesBitacoraRepository | None = None):
        self.repo = repo or InformesBitacoraRepository()

    def cambios(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_BITACORA,
        idpartner: int | None = None,
        tipo_cambio: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        # La bitácora guarda el partner, no el cliente: cuando hay acotamiento
        # por cuenta hay que resolver sus partners antes. **Una** consulta
        # adicional por petición, no una por fila.
        idpartners = (
            self.repo.partners_de_cuenta(acotamiento.titular)
            if acotamiento.acotado
            else None
        )

        crudas = self.repo.cambios(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idpartners=idpartners,
            idpartner=idpartner,
            tipo_cambio=tipo_cambio,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_BITACORA.recortar(crudas, limit)

        partners = self.repo.nombres_de_partner(
            [f.get("idpartner") for f in pagina.filas]
        )
        credenciales = self.repo.nombres_de_credencial(
            [f.get("idcredencial") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "partner": partners.get(fila.get("idpartner")),
                    # `-1` marca un evento del partner que no afecta a ninguna
                    # credencial concreta: se presenta ausente, no como «-1».
                    "credencial": _credencial(fila, credenciales),
                    # **Su valor propio**, sin agrupar con ningún otro.
                    "tipo_cambio": fila.get("tipo_cambio"),
                    "ejecutado_por": fila.get("ejecutado_por"),
                    # Ausente en una reactivación, y eso es correcto: el SRS
                    # exige motivo al cortar el acceso, no al devolverlo.
                    "motivo": _sin_centinela(fila.get("motivo")),
                    "estado_anterior": _sin_centinela(fila.get("estado_anterior")),
                    "estado_nuevo": fila.get("estado_nuevo"),
                    "fecha": a_iso(fila.get("fecha_cambio")),
                }
                for fila in pagina.filas
            ]
        )


def _credencial(fila: dict[str, Any], nombres: dict[int, str]) -> str | None:
    idcredencial = fila.get("idcredencial")
    if idcredencial is None or int(idcredencial) == SIN_CREDENCIAL:
        return None
    return nombres.get(int(idcredencial))


def _sin_centinela(valor: Any) -> str | None:
    """`""` es el centinela de «sin motivo», no un motivo en blanco."""
    return None if valor in (None, SIN_MOTIVO) else valor
