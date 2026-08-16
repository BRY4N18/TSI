"""Servicio de la evidencia levantada en campo — L3 y L4.

⚠️ Las dos horas son distintas, y la diferencia es información
---------------------------------------------------------------
`hora_captura` es la del sitio y se devuelve **tal cual**. `hora_registro` es
cuándo llegó al sistema, y sale de **columnas distintas** en cada tabla: la
fotografía tiene una propia, la nota usa la marca genérica de modificación.

En un registro hecho en línea las dos coinciden; en uno capturado sin conexión
difieren, y ahí es donde un error de columna se vería. Por eso las pruebas
comprueban **el contraste entre los dos casos**: verificar solo el registro en
línea no distinguiría una implementación correcta de una que sella la hora de
subida en ambos campos.
"""

from __future__ import annotations

from typing import Any

from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.accidentes.informes_evidencia_repository import (
    CURSOR_FOTOS,
    CURSOR_NOTAS,
    ORDEN_EVIDENCIA,
    InformesEvidenciaRepository,
)


class InformesEvidenciaService:
    def __init__(self, repo: InformesEvidenciaRepository | None = None):
        self.repo = repo or InformesEvidenciaRepository()

    def fotos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_EVIDENCIA,
        sincronizado: bool | None = None,
        idaccidente: str | None = None,
        idusuario: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        crudas = self.repo.fotos(
            cursor=cursor,
            limit=limit,
            orden=orden,
            sincronizado=sincronizado,
            idaccidente=idaccidente,
            idusuario=idusuario,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_FOTOS.recortar(crudas, limit)
        autores = self.repo.autores([f.get("idusuario") for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "numero_caso": fila.get("idaccidente"),
                    "autor": autores.get(_positivo(fila.get("idusuario"))),
                    "url": fila.get("urlevidenciafoto"),
                    "sincronizado": bool(fila.get("sincronizado")),
                    # ⚠️ La del sitio. Nunca se sustituye por la de subida.
                    "hora_captura": a_iso(fila.get("fechahora")),
                    # Columna **propia** de esta tabla.
                    "hora_registro": _hora(fila.get("fecha_sincronizacion")),
                }
                for fila in pagina.filas
            ]
        )

    def notas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_EVIDENCIA,
        sincronizado: bool | None = None,
        tipo: str | None = None,
        idaccidente: str | None = None,
        idusuario: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        crudas = self.repo.notas(
            cursor=cursor,
            limit=limit,
            orden=orden,
            sincronizado=sincronizado,
            tipo=tipo,
            idaccidente=idaccidente,
            idusuario=idusuario,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_NOTAS.recortar(crudas, limit)
        autores = self.repo.autores([f.get("idusuario") for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "numero_caso": fila.get("idaccidente"),
                    "autor": autores.get(_positivo(fila.get("idusuario"))),
                    "nota": fila.get("nota"),
                    "tipo": _vacio_a_none(fila.get("tipo")),
                    "sincronizado": bool(fila.get("sincronizado")),
                    "hora_captura": a_iso(fila.get("fechahora")),
                    # ⚠️ Marca **genérica** de modificación: esta tabla no tiene
                    # columna de sincronización propia (deuda anotada).
                    "hora_registro": _hora(fila.get("fecha_actualizacion")),
                }
                for fila in pagina.filas
            ]
        )


def _positivo(valor: Any) -> int | None:
    if valor is None:
        return None
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return None
    return entero if entero > 0 else None


def _hora(valor: Any) -> str | None:
    try:
        marca = int(valor or 0)
    except (TypeError, ValueError):
        return None
    return None if marca <= 0 else a_iso(marca)


def _vacio_a_none(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in ("", "null") else texto
