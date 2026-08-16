"""Servicio de los dos listados de OT04 — incorporacion de clientes nuevos.

Aporta lo unico que el repositorio no puede: **el ahora**.

Por que el reloj se inyecta
---------------------------
`dias_transcurridos` y el filtro `dias_minimo` dependen de la hora actual, que
no es un dato de la tabla. Empotrar esa dependencia en SQL —con la fecha del
broker de Pinot— haria el calculo imposible de probar de forma determinista y lo
ataria al reloj del servidor de datos (research D5).

El precedente esta en el propio repositorio: `run_dunning` inyecta `now` para
poder verificar los reintentos a D+3 y D+5, y es exactamente la razon por la que
la mora se pudo probar de punta a punta.

El reparto entre Python y Pinot no es arbitrario
------------------------------------------------
* **`dias_minimo` se traduce a fecha de corte** y viaja al `WHERE`. El filtrado
  ocurre en Pinot. Aplicarlo en Python despues de paginar devolveria paginas
  incompletas: el `LIMIT` ya habria recortado antes de descartar nada.
* **`dias_transcurridos` se calcula aqui.** Es presentacion, no filtrado, y no
  afecta a que filas salen.
"""

from __future__ import annotations

from typing import Any, Callable

from core.informes.formato import a_entero_ms, a_iso
from core.informes.paginacion import Orden, Pagina
from core.pinot.tiempo import ahora_ms
from core.repositories.cuentas_clientes.informes_incorporacion_repository import (
    CURSOR_ONBOARDING,
    CURSOR_SOLICITUDES,
    ORDEN_ONBOARDING,
    ORDEN_SOLICITUDES,
    InformesIncorporacionRepository,
)

DIA_MS = 86_400_000


class InformesIncorporacionService:
    def __init__(
        self,
        repo: InformesIncorporacionRepository | None = None,
        ahora: Callable[[], int] = ahora_ms,
    ):
        self.repo = repo or InformesIncorporacionRepository()
        #: Se inyecta como **funcion**, no como valor, para que cada peticion
        #: lea el instante en el momento de atenderse. Un valor fijado en el
        #: constructor envejeceria con el proceso: un servidor levantado hace
        #: tres dias calcularia la antiguedad contra el arranque.
        self.ahora = ahora

    # ── L1 — Solicitudes de alta pendientes ──────────────────────────────────

    def solicitudes_pendientes(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SOLICITUDES,
        tipo: str | None = None,
        dias_minimo: int | None = None,
    ) -> Pagina:
        ahora = self.ahora()
        crudas = self.repo.solicitudes_pendientes(
            cursor=cursor,
            limit=limit,
            orden=orden,
            tipo=tipo,
            creadas_antes_de=self._fecha_de_corte(ahora, dias_minimo),
        )
        pagina = CURSOR_SOLICITUDES.recortar(crudas, limit)

        return pagina._replace(
            filas=[
                {
                    "razon_social": fila.get("razon_social"),
                    "tipo": fila.get("tipo"),
                    "fecha_solicitud": a_iso(fila.get("fecha_creacion")),
                    "dias_transcurridos": self._dias(ahora, fila.get("fecha_creacion")),
                }
                for fila in pagina.filas
            ]
        )

    # ── L2 — Incorporacion incompleta ────────────────────────────────────────

    def onboarding_incompleto(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ONBOARDING,
        etapa: str | None = None,
        dias_minimo: int | None = None,
    ) -> Pagina:
        ahora = self.ahora()
        crudas = self.repo.etapas_pendientes(
            cursor=cursor,
            limit=limit,
            orden=orden,
            etapa=etapa,
            detenidas_antes_de=self._fecha_de_corte(ahora, dias_minimo),
        )
        pagina = CURSOR_ONBOARDING.recortar(crudas, limit)

        razones = self.repo.razones_sociales([f["id_cliente"] for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "razon_social": razones.get(fila["id_cliente"]),
                    "etapa": fila.get("etapa"),
                    "fecha_ultima_actualizacion": a_iso(fila.get("fecha_actualizacion")),
                    "dias_detenido": self._dias(ahora, fila.get("fecha_actualizacion")),
                }
                for fila in pagina.filas
            ]
        )

    def etapas_disponibles(self) -> list[str]:
        return self.repo.etapas_disponibles()

    # ── Calculo de antiguedad ────────────────────────────────────────────────

    @staticmethod
    def _fecha_de_corte(ahora: int, dias_minimo: int | None) -> int | None:
        """`dias_minimo` → instante limite que viaja al `WHERE`.

        "Al menos 7 dias de antiguedad" es "creada en o antes de hace 7 dias".
        """
        if dias_minimo is None:
            return None
        return ahora - dias_minimo * DIA_MS

    @staticmethod
    def _dias(ahora: int, desde: Any) -> int | None:
        """Dias completos transcurridos, o `None` si no hay fecha de partida.

        Ausente devuelve `None` y **no `0`** (FR-021): un `0` diria "llego hoy",
        que es lo contrario de lo que significa no saber cuando llego — y en una
        bandeja ordenada por antiguedad lo mandaria al final de la cola.

        La ausencia la decide `marca_ausente`, el mismo criterio que usa `a_iso`
        para la fecha que se muestra. Compartirlo evita que una fila salga con la
        fecha en `null` y a la vez con una antiguedad calculada.
        """
        inicio = a_entero_ms(desde)
        if inicio is None:
            return None
        return max(0, (ahora - inicio) // DIA_MS)
