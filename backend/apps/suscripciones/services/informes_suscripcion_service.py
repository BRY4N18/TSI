"""Servicio de suscripciones — L1 de OT05/OT07.

La regla de presentación que este módulo sostiene: **el cambio programado se
devuelve como ausencia cuando no lo hay, nunca como un plan con identificador
cero**.

El `0` no es un plan. No existe en el catálogo, así que resolverlo devolvería
`null` de todas formas — pero la clave seguiría presente, sugiriendo que hay un
cambio cuyo nombre no se pudo averiguar. Son dos cosas distintas: «no hay
cambio» y «hay un cambio que no sé nombrar».
"""

from __future__ import annotations

from typing import Any, Callable

from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.pinot.tiempo import ahora_ms
from core.repositories.suscripciones.informes_suscripcion_repository import (
    CURSOR_SUSCRIPCIONES,
    ORDEN_SUSCRIPCIONES,
    SIN_CAMBIO_PROGRAMADO,
    InformesSuscripcionRepository,
)

DIA_MS = 86_400_000

ESTADO_CANCELADA = "Cancelada"


class InformesSuscripcionService:
    def __init__(
        self,
        repo: InformesSuscripcionRepository | None = None,
        ahora: Callable[[], int] | None = None,
    ):
        self.repo = repo or InformesSuscripcionRepository()
        #: Se resuelve aquí y no como valor por defecto del parámetro: aquél se
        #: evalúa al definir la clase y quedaría atado a la función original,
        #: impidiendo fijarlo en una prueba de API.
        self.ahora = ahora or (lambda: ahora_ms())

    def suscripciones(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SUSCRIPCIONES,
        estado: str | None = None,
        idplan: int | None = None,
        con_cambio_programado: bool | None = None,
        vence_en_dias: int | None = None,
        cancelada_desde_ms: int | None = None,
        cancelada_hasta_ms: int | None = None,
    ) -> Pagina:
        ahora = self.ahora()

        crudas = self.repo.suscripciones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            cuenta=acotamiento.titular,
            estado=estado,
            idplan=idplan,
            con_cambio_programado=con_cambio_programado,
            vence_antes_de=(
                ahora + vence_en_dias * DIA_MS if vence_en_dias is not None else None
            ),
            cancelada_desde=cancelada_desde_ms,
            cancelada_hasta=cancelada_hasta_ms,
        )
        pagina = CURSOR_SUSCRIPCIONES.recortar(crudas, limit)

        planes = self.repo.nombres_de_plan(
            [f.get("idplan") for f in pagina.filas]
            + [f.get("idplan_programado") for f in pagina.filas]
        )
        cuentas = self.repo.razones_sociales([f.get("idcliente") for f in pagina.filas])

        return pagina._replace(
            filas=[_fila(f, planes, cuentas) for f in pagina.filas]
        )


def _fila(
    cruda: dict[str, Any], planes: dict[int, str], cuentas: dict[int, str]
) -> dict[str, Any]:
    estado = cruda.get("estado")
    fila = {
        "cuenta": cuentas.get(cruda.get("idcliente")),
        "plan": planes.get(cruda.get("idplan")),
        "nivel": cruda.get("nivel"),
        "estado": estado,
        "precio": cruda.get("precio"),
        "periodicidad": cruda.get("periodicidad"),
        "renovacion_automatica": cruda.get("renovacionautomatica"),
        "fecha_inicio": a_iso(cruda.get("fecha_inicio")),
        "fecha_fin": a_iso(cruda.get("fecha_fin")),
        # ⚠️ **Dos campos planos, no un objeto anidado.** Ambos `None` cuando no
        # hay cambio: el `0` no es un plan, es la marca de que no hay ninguno
        # (research D2). Ver `_cambio_programado`.
        **_cambio_programado(cruda, planes),
    }
    if estado == ESTADO_CANCELADA:
        # El motivo y la fecha solo tienen sentido en una cancelada. Devolverlos
        # en una activa —aunque fuera `null`— sugeriría que la pregunta aplica.
        fila["motivo_cancelacion"] = cruda.get("motivocancelacion")
        fila["fecha_cancelacion"] = a_iso(cruda.get("fechacancelacion"))
    return fila


def _cambio_programado(
    cruda: dict[str, Any], planes: dict[int, str]
) -> dict[str, Any]:
    """El cambio pendiente, **aplanado en dos campos**.

    Devuelve siempre las dos claves; ambas `None` cuando no hay ningún cambio
    programado.

    `cambio_programado_se_aplica_el` es el fin del ciclo vigente: una reducción
    aprobada no se aplica al aprobarse sino **al cerrar el período ya pagado**.
    Sin esa fecha, el listado diría que hay un cambio pendiente sin decir cuándo,
    que es la mitad de la información que la pregunta necesita.

    ⚠️ **Antes esto era un objeto anidado** `{plan, se_aplica_el}`, y la tabla lo
    pintaba **`[object Object]`**: el catálogo de columnas del frontend declara
    campos escalares y no sabe recorrer un objeto. Se aplanó aquí, del lado que
    conoce el dato, en vez de enseñar a la capa compartida a recorrer objetos
    arbitrarios — eso habría metido lógica de presentación en 32 listados para
    resolver un caso.
    """
    try:
        idplan = int(cruda.get("idplan_programado") or SIN_CAMBIO_PROGRAMADO)
    except (TypeError, ValueError):
        idplan = SIN_CAMBIO_PROGRAMADO
    if idplan <= SIN_CAMBIO_PROGRAMADO:
        return {
            "cambio_programado_plan": None,
            "cambio_programado_se_aplica_el": None,
        }
    return {
        "cambio_programado_plan": planes.get(idplan),
        "cambio_programado_se_aplica_el": a_iso(cruda.get("fecha_fin")),
    }
