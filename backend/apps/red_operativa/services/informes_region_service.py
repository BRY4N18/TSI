"""Servicio de regiones e intentos de validación — L3 y L4 de OT11/OT13.

`dias_sin_cambio` se calcula con **reloj inyectable**, como en los módulos
anteriores: es el número que decide si una región lleva demasiado tiempo
detenida en validación, y con el reloj real no sería verificable.

Los cinco estados se devuelven **tal cual**, sin agrupar (research D4).
"""

from __future__ import annotations

from typing import Any, Callable

from core.informes.formato import a_entero_ms, a_iso
from core.informes.paginacion import Orden, Pagina
from core.pinot.tiempo import ahora_ms
from core.repositories.red_operativa.informes_region_repository import (
    CURSOR_REGIONES,
    CURSOR_VALIDACIONES,
    ORDEN_REGIONES,
    ORDEN_VALIDACIONES,
    InformesRegionRepository,
)

DIA_MS = 86_400_000


class InformesRegionService:
    def __init__(
        self,
        repo: InformesRegionRepository | None = None,
        ahora: Callable[[], int] | None = None,
    ):
        self.repo = repo or InformesRegionRepository()
        self.ahora = ahora or (lambda: ahora_ms())

    # ── L3 — Regiones operativas ─────────────────────────────────────────────

    def regiones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_REGIONES,
        estado_region: str | None = None,
        detenida_mas_de_dias: int | None = None,
    ) -> Pagina:
        ahora = self.ahora()

        crudas = self.repo.regiones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            estado_region=estado_region,
            sin_cambio_desde=(
                ahora - detenida_mas_de_dias * DIA_MS
                if detenida_mas_de_dias is not None
                else None
            ),
        )
        pagina = CURSOR_REGIONES.recortar(crudas, limit)

        estados = self.repo.nombres_de_estado(
            [f.get("idestado") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "nombre_region": fila.get("nombreregion"),
                    # El estado se devuelve tal cual, sin agrupar: `En_Alerta`
                    # opera con cobertura degradada y `Despublicada` ya no opera.
                    "estado_region": fila.get("estadoregion"),
                    "estado_geografico": estados.get(fila.get("idestado")),
                    "dias_sin_cambio": _dias(ahora, fila.get("fecha_actualizacion")),
                    "fecha_actualizacion": a_iso(fila.get("fecha_actualizacion")),
                }
                for fila in pagina.filas
            ]
        )

    # ── L4 — Intentos de validación ──────────────────────────────────────────

    def validaciones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_VALIDACIONES,
        idregion: int | None = None,
        resultado: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        crudas = self.repo.validaciones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idregion=idregion,
            resultado=resultado,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_VALIDACIONES.recortar(crudas, limit)

        regiones = self.repo.nombres_de_region(
            [f.get("idregionoperativa") for f in pagina.filas]
        )
        ejecutores = self.repo.nombres_de_usuario(
            [f.get("idusuario") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "region": regiones.get(fila.get("idregionoperativa")),
                    "resultado": fila.get("resultado"),
                    # El motivo es lo que hace útil el historial: sin él, dos
                    # rechazos son dos fechas sin nada que corregir.
                    "motivo": fila.get("motivo"),
                    "ejecutada_por": ejecutores.get(fila.get("idusuario")),
                    "fecha": a_iso(fila.get("fechahora")),
                }
                for fila in pagina.filas
            ]
        )

    def resultados_disponibles(self) -> list[str]:
        return self.repo.resultados_disponibles()


def _dias(ahora: int, desde: Any) -> int | None:
    """Días desde el último cambio de estado, o `None` si no hay fecha.

    `None` y no `0`: un `0` diría «cambió hoy», que es lo contrario de no saber
    cuándo cambió — y en un listado que sirve para detectar regiones detenidas
    la mandaría al final de la cola.
    """
    inicio = a_entero_ms(desde)
    if inicio is None:
        return None
    return max(0, (ahora - inicio) // DIA_MS)
