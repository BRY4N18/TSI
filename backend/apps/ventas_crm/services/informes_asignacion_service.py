"""Servicio de las reasignaciones de cartera — L2 de OT02 / CU-O19.

La regla que este módulo existe para sostener: **la primera asignación de un
prospecto no tiene responsable anterior, y eso se presenta como ausencia**.

No es un caso raro: toda la cartera pasó por ahí. Devolver `0` o cadena vacía
crearía un ejecutivo fantasma —«el prospecto pasó de nadie a Lucía» leído como
«pasó del usuario 0 a Lucía»— y en un listado de movimientos de cartera eso es
inventar un movimiento que no ocurrió (research D7).
"""

from __future__ import annotations

from typing import Any

from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.ventas_crm.informes_asignacion_repository import (
    CURSOR_ASIGNACIONES,
    ORDEN_ASIGNACIONES,
    InformesAsignacionRepository,
)


class InformesAsignacionService:
    def __init__(self, repo: InformesAsignacionRepository | None = None):
        self.repo = repo or InformesAsignacionRepository()

    def reasignaciones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ASIGNACIONES,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        idprospecto: int | None = None,
        tipo_asignacion: str | None = None,
    ) -> Pagina:
        crudas = self.repo.reasignaciones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
            idprospecto=idprospecto,
            tipo_asignacion=tipo_asignacion,
        )
        pagina = CURSOR_ASIGNACIONES.recortar(crudas, limit)

        # Se resuelven los dos extremos en una sola consulta de catálogo: son la
        # misma tabla, y separarlas costaría el doble sin ganar nada.
        usuarios = self.repo.nombres_de_usuario(
            [f.get("idusuariogerenteanterior") for f in pagina.filas]
            + [f.get("idusuariogerenteactual") for f in pagina.filas]
        )
        empresas = self.repo.empresas_de_prospecto(
            [f.get("idprospecto") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "empresa": empresas.get(fila.get("idprospecto")),
                    # `None` en la primera asignación: el prospecto no venía de
                    # nadie. Un `0` sería un ejecutivo fantasma.
                    "ejecutivo_anterior": usuarios.get(
                        fila.get("idusuariogerenteanterior")
                    ),
                    "ejecutivo_nuevo": usuarios.get(fila.get("idusuariogerenteactual")),
                    "tipo_asignacion": fila.get("tipoasignacion"),
                    "motivo": fila.get("motivo"),
                    "fecha": a_iso(fila.get("fechahoraasignacion")),
                }
                for fila in pagina.filas
            ]
        )

    def tipos_disponibles(self) -> list[str]:
        return self.repo.tipos_disponibles()
