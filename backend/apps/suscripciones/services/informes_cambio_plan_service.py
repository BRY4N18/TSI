"""Servicio de solicitudes de cambio de plan — L3 de OT07 / CU-O34.

La regla que sostiene: **mientras la solicitud siga pendiente, el resolutor y el
motivo de rechazo se presentan como ausentes**.

No es cosmético. Una solicitud pendiente todavía no la ha resuelto nadie, así
que devolver `resuelta_por: null` junto a `estado: "Pendiente"` es redundante en
el mejor caso y contradictorio en el peor — invita a leer «alguien la resolvió y
no sé quién». Omitir la clave dice exactamente lo que pasa: aún no hay resolución.
"""

from __future__ import annotations

from typing import Any, Callable

from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_entero_ms, a_iso
from core.informes.paginacion import Orden, Pagina
from core.pinot.tiempo import ahora_ms
from core.repositories.suscripciones.informes_cambio_plan_repository import (
    CURSOR_SOLICITUDES,
    ORDEN_SOLICITUDES,
    InformesCambioPlanRepository,
)
from core.repositories.suscripciones.informes_suscripcion_repository import (
    InformesSuscripcionRepository,
)

DIA_MS = 86_400_000
ESTADO_PENDIENTE = "Pendiente"


class InformesCambioPlanService:
    def __init__(
        self,
        repo: InformesCambioPlanRepository | None = None,
        planes: InformesSuscripcionRepository | None = None,
        ahora: Callable[[], int] | None = None,
    ):
        self.repo = repo or InformesCambioPlanRepository()
        #: El catálogo de planes se reutiliza del repositorio de suscripciones
        #: en vez de duplicar la consulta: es la misma tabla y la misma pregunta.
        self.planes = planes or InformesSuscripcionRepository()
        self.ahora = ahora or (lambda: ahora_ms())

    def solicitudes(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SOLICITUDES,
        estado: str | None = None,
    ) -> Pagina:
        ahora = self.ahora()

        crudas = self.repo.solicitudes(
            cursor=cursor,
            limit=limit,
            orden=orden,
            cuenta=acotamiento.titular,
            estado=estado,
        )
        pagina = CURSOR_SOLICITUDES.recortar(crudas, limit)

        nombres_plan = self.planes.nombres_de_plan(
            [f.get("idplanactual") for f in pagina.filas]
            + [f.get("idplansolicitado") for f in pagina.filas]
        )
        cuentas = self.planes.razones_sociales(
            [f.get("idcliente") for f in pagina.filas]
        )
        resolutores = self.repo.nombres_de_usuario(
            [f.get("idadminaprobador") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                _fila(f, nombres_plan, cuentas, resolutores, ahora)
                for f in pagina.filas
            ]
        )


def _fila(
    cruda: dict[str, Any],
    planes: dict[int, str],
    cuentas: dict[int, str],
    resolutores: dict[int, str],
    ahora: int,
) -> dict[str, Any]:
    estado = cruda.get("estado")
    fila = {
        "cuenta": cuentas.get(cruda.get("idcliente")),
        "plan_actual": planes.get(cruda.get("idplanactual")),
        "plan_solicitado": planes.get(cruda.get("idplansolicitado")),
        "estado": estado,
        "motivo": cruda.get("motivo"),
        "fecha_solicitud": a_iso(cruda.get("fecha_solicitud")),
        "dias_espera": _dias_espera(cruda, ahora),
    }
    if estado != ESTADO_PENDIENTE:
        # Solo una solicitud ya resuelta tiene resolutor y fecha de resolución.
        fila["resuelta_por"] = resolutores.get(cruda.get("idadminaprobador"))
        fila["fecha_resolucion"] = a_iso(cruda.get("fecha_resolucion"))
        fila["motivo_rechazo"] = cruda.get("motivo_rechazo")
    return fila


def _dias_espera(cruda: dict[str, Any], ahora: int) -> int | None:
    """Días que la solicitud lleva —o llevó— esperando.

    En una resuelta se mide hasta su resolución, no hasta hoy: si se midiera
    hasta hoy, una solicitud resuelta en un día seguiría acumulando «espera»
    para siempre y la bandeja mentiría sobre el tiempo de respuesta.
    """
    inicio = a_entero_ms(cruda.get("fecha_solicitud"))
    if inicio is None:
        return None
    fin = a_entero_ms(cruda.get("fecha_resolucion")) or ahora
    return max(0, (fin - inicio) // DIA_MS)
