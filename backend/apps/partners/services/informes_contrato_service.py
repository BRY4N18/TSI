"""Servicio de versiones del contrato y alcance de datos — L4 y L5.

⚠️ **Sin alcance configurado no es acceso ilimitado** (FR-023).

`zonas_geograficas` ausente significa **que no se ha configurado**, no «todas las
zonas». Devolver una lista vacía invitaría a leerla como «sin restricción», y en
un módulo cuya función es decir qué datos puede consumir un partner, eso daría
por contratado un alcance que nadie acordó.

`None` es la respuesta honesta: no se sabe qué alcance tiene, porque no se ha
definido.
"""

from __future__ import annotations

from typing import Any

from apps.partners.domain_constants import SIN_FECHA_RETIRO, SIN_URL
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.partners.informes_contrato_repository import (
    CURSOR_ALCANCE,
    CURSOR_VERSIONES,
    ORDEN_ALCANCE,
    ORDEN_VERSIONES,
    InformesContratoRepository,
)


class InformesContratoService:
    def __init__(self, repo: InformesContratoRepository | None = None):
        self.repo = repo or InformesContratoRepository()

    # ── L4 — Versiones del contrato ──────────────────────────────────────────

    def versiones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_VERSIONES,
        estado: str | None = None,
        id_servicio: int | None = None,
    ) -> Pagina:
        crudas = self.repo.versiones(
            cursor=cursor, limit=limit, orden=orden, estado=estado, id_servicio=id_servicio
        )
        pagina = CURSOR_VERSIONES.recortar(crudas, limit)

        servicios = self.repo.nombres_de_servicio(
            [f.get("id_servicio") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "servicio": servicios.get(fila.get("id_servicio")),
                    "version": fila.get("version"),
                    "estado": fila.get("estado"),
                    "spec_url": _sin_centinela(fila.get("spec_url"), SIN_URL),
                    "fecha_publicacion": a_iso(fila.get("fecha_publicacion")),
                    # `0` es el centinela de «no retirada», no la época.
                    "fecha_retiro": _fecha_retiro(fila.get("fecha_retiro")),
                }
                for fila in pagina.filas
            ]
        )

    # ── L5 — Alcance de datos por cliente ────────────────────────────────────

    def alcance(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ALCANCE,
        id_cliente: int | None = None,
        frecuencia: str | None = None,
    ) -> Pagina:
        crudas = self.repo.alcance(
            cursor=cursor,
            limit=limit,
            orden=orden,
            id_cliente=id_cliente,
            frecuencia=frecuencia,
        )
        pagina = CURSOR_ALCANCE.recortar(crudas, limit)

        cuentas = self.repo.razones_sociales(
            [f.get("id_cliente") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "cuenta": cuentas.get(fila.get("id_cliente")),
                    "frecuencia_reportes": _vacio_a_none(fila.get("frecuencia_reportes")),
                    "formato_reportes": _vacio_a_none(fila.get("formato_reportes")),
                    "canales_notificacion": _vacio_a_none(fila.get("canales_notificacion")),
                    # ⚠️ `None` cuando no hay alcance configurado. **Nunca una
                    # lista vacía**, que se leería como «todas las zonas».
                    "zonas_geograficas": _vacio_a_none(fila.get("zonas_geograficas")),
                    "destinatarios_reportes": _vacio_a_none(
                        fila.get("destinatarios_reportes")
                    ),
                }
                for fila in pagina.filas
            ]
        )


def _fecha_retiro(valor: Any) -> str | None:
    """`0` significa «no retirada», no 1970."""
    if valor is None or int(valor or SIN_FECHA_RETIRO) == SIN_FECHA_RETIRO:
        return None
    return a_iso(valor)


def _sin_centinela(valor: Any, centinela: Any) -> Any:
    return None if valor in (None, centinela) else valor


def _vacio_a_none(valor: Any) -> Any:
    """Un texto vacío es «sin configurar», no un valor configurado a nada.

    La distinción importa especialmente en `zonas_geograficas`: leer «vacío»
    como «todas» daría por contratado un alcance que nadie acordó.
    """
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None
