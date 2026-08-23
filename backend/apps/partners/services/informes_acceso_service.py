"""Servicio de partners y credenciales — L1 y L2 de OT08.

El estado de incorporación se deriva **por lotes**
----------------------------------------------------
`ConsultaPartnerService.derivar_estado` es la fuente de verdad de los seis
estados, y aquí se reutiliza su **lógica** sin reutilizar su forma: aquel resuelve
**un** partner y para ello consulta la bitácora de ese partner, lo cual es
correcto cuando se resuelve uno y sería N+1 sobre una página.

Aquí las dos entradas que necesita —credenciales y eventos de activación— se
traen **en dos consultas por página**, y la derivación se aplica en memoria.

Y el filtro de estado va en dos pasos
--------------------------------------
Dos de los seis estados se derivan de columnas de `Dim_Partner` y **sí** se
pueden filtrar en la base: `Suspendido` (`activo = false`) y `Registrado`
(`activo = true` y plan vacío). Los otros cuatro dependen de las credenciales y
de la bitácora, así que se refinan aquí.

**Consecuencia declarada:** al filtrar por uno de esos cuatro estados, una página
puede devolver **menos filas que el `limit`**. `has_next` sigue siendo la
autoridad; el número de filas no lo es. Es la misma forma que el listado de demos
de Ventas y CRM.
"""

from __future__ import annotations

from typing import Any, Callable

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_PRODUCCION,
    CAMBIO_ACTIVACION_SANDBOX,
    CAMBIO_SOLICITUD_PRODUCCION,
    ENTORNO_PRODUCCION,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    ESTADO_REGISTRADO,
    ESTADO_SUSPENDIDO,
    SIN_PLAN,
)
from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_entero_ms, a_iso
from core.informes.paginacion import Orden, Pagina
from core.pinot.tiempo import ahora_ms
from core.repositories.partners.informes_acceso_repository import (
    CURSOR_CREDENCIALES,
    CURSOR_PARTNERS,
    ORDEN_CREDENCIALES,
    ORDEN_PARTNERS,
    InformesAccesoRepository,
)

DIA_MS = 86_400_000

#: Eventos que `derivar_estado` necesita para distinguir «Pruebas activo» de
#: «Plan asignado», y para detectar una promoción pendiente.
TIPOS_RELEVANTES = (
    CAMBIO_ACTIVACION_SANDBOX,
    CAMBIO_ACTIVACION_PRODUCCION,
    CAMBIO_SOLICITUD_PRODUCCION,
)

#: Los dos estados que **sí** se pueden filtrar en la base, y con qué.
FILTRO_PUSHABLE = {
    ESTADO_SUSPENDIDO: {"activo": False},
    ESTADO_REGISTRADO: {"activo": True, "con_plan": False},
}


class InformesAccesoService:
    def __init__(
        self,
        repo: InformesAccesoRepository | None = None,
        ahora: Callable[[], int] | None = None,
    ):
        self.repo = repo or InformesAccesoRepository()
        self.ahora = ahora or (lambda: ahora_ms())

    # ── L1 — Partners ────────────────────────────────────────────────────────

    def partners(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_PARTNERS,
        estado: str | None = None,
        plan: str | None = None,
        idpartner: int | None = None,
    ) -> Pagina:
        # Prefiltro: lo que se puede empujar a la base sin adivinar.
        pushable = FILTRO_PUSHABLE.get(estado, {})
        if estado is not None and estado not in FILTRO_PUSHABLE:
            # Los cuatro estados derivados comparten esta condición previa; el
            # refinamiento la estrecha después.
            pushable = {"activo": True, "con_plan": True}

        crudas = self.repo.partners(
            cursor=cursor,
            limit=limit,
            orden=orden,
            cuenta=acotamiento.titular,
            # ⚠️ **Acotar y filtrar son cosas distintas.** `cuenta` viene del
            # acotamiento —a qué tiene derecho quien pregunta— y `idpartner` de
            # lo que pidió. Mezclarlos haría que filtrar por un partner
            # pareciera reducir el alcance, o peor, que pedir uno ajeno lo
            # ampliara.
            idpartner=idpartner,
            plan=plan,
            **pushable,
        )
        pagina = CURSOR_PARTNERS.recortar(crudas, limit)

        idpartners = [f["idpartner"] for f in pagina.filas]
        credenciales = self.repo.credenciales_de(idpartners)
        eventos = self.repo.eventos_de(idpartners, TIPOS_RELEVANTES)
        cuentas = self.repo.razones_sociales(
            [f.get("idcliente") for f in pagina.filas]
        )

        filas = []
        for cruda in pagina.filas:
            derivado = _derivar_estado(
                cruda,
                credenciales.get(cruda["idpartner"], []),
                eventos.get(cruda["idpartner"], []),
            )
            # Refinamiento del filtro: los cuatro estados que la base no puede
            # distinguir se descartan aquí.
            if estado is not None and derivado != estado:
                continue
            filas.append(_fila_partner(cruda, derivado, cuentas))

        return pagina._replace(filas=filas)

    # ── L2 — Credenciales ────────────────────────────────────────────────────

    def credenciales(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CREDENCIALES,
        idpartner: int | None = None,
        entorno: str | None = None,
        activa: bool | None = None,
        caduca_en_dias: int | None = None,
    ) -> Pagina:
        ahora = self.ahora()

        crudas = self.repo.credenciales(
            cursor=cursor,
            limit=limit,
            orden=orden,
            cuenta=acotamiento.titular,
            idpartner=idpartner,
            entorno=entorno,
            activa=activa,
            caduca_antes_de=(
                ahora + caduca_en_dias * DIA_MS if caduca_en_dias is not None else None
            ),
        )
        pagina = CURSOR_CREDENCIALES.recortar(crudas, limit)

        partners = self.repo.nombres_de_partner(
            [f.get("idpartner") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "partner": partners.get(fila.get("idpartner")),
                    "nombre_credencial": fila.get("nombre_credencial"),
                    "entorno": fila.get("entorno"),
                    # **Si** está activa. No **por qué** no lo está: el registro
                    # de la credencial no lo contiene (research D2).
                    "activa": fila.get("activo"),
                    "fecha_creacion": a_iso(fila.get("fecha_creacion")),
                    "fecha_expiracion": a_iso(fila.get("fecha_expiracion")),
                    "dias_para_caducar": _dias_hasta(ahora, fila.get("fecha_expiracion")),
                }
                for fila in pagina.filas
            ]
        )


def _derivar_estado(
    partner: dict[str, Any],
    credenciales: list[dict[str, Any]],
    eventos: list[dict[str, Any]],
) -> str:
    """Los seis estados, en el mismo orden de precedencia que el flujo operativo.

    Se replica la lógica de `ConsultaPartnerService.derivar_estado` porque su
    forma —una consulta a la bitácora por partner— no sirve sobre una página.
    **La precedencia es la misma**, y una prueba lo comprueba comparando ambas
    sobre los mismos datos.
    """
    if not partner.get("activo", False):
        return ESTADO_SUSPENDIDO

    # Guarda contra el CENTINELA, no contra nulidad: un partner sin plan lleva
    # cadena vacía, y `is not None` sería siempre cierto.
    if str(partner.get("planapi", SIN_PLAN) or SIN_PLAN) == SIN_PLAN:
        return ESTADO_REGISTRADO

    ultimo = max(
        eventos, key=lambda e: e.get("fecha_cambio") or 0, default=None
    )
    if ultimo and ultimo.get("tipo_cambio") == CAMBIO_SOLICITUD_PRODUCCION:
        return ESTADO_PENDIENTE_APROBACION

    if any(
        c.get("entorno") == ENTORNO_PRODUCCION and c.get("activo") for c in credenciales
    ):
        return ESTADO_PRODUCCION_ACTIVA

    # «Pruebas activo» no exige credencial viva: una vencida deja al partner
    # aquí, listo para regenerar sin repetir el alta.
    hubo_sandbox = any(
        e.get("tipo_cambio") in (CAMBIO_ACTIVACION_SANDBOX, CAMBIO_ACTIVACION_PRODUCCION)
        for e in eventos
    )
    if credenciales or hubo_sandbox:
        return ESTADO_PRUEBAS_ACTIVO

    return ESTADO_PLAN_ASIGNADO


def _fila_partner(
    cruda: dict[str, Any], estado: str, cuentas: dict[int, str]
) -> dict[str, Any]:
    fila = {
        "cuenta": cuentas.get(cruda.get("idcliente")),
        "nombre_partner": cruda.get("nombrepartner"),
        "estado_acceso": estado,
        "plan_api": cruda.get("planapi") or None,
        "limite_llamadas_mes": _sin_centinela(cruda.get("limitellamadasmes")),
        "limite_llamadas_minuto": _sin_centinela(cruda.get("limitellamadasminuto")),
        "contacto_tecnico": cruda.get("contacto_tecnico_nombre"),
    }
    if estado == ESTADO_SUSPENDIDO:
        # Solo una suspensión tiene fecha y motivo. Devolverlos en un partner
        # activo —aunque fuera vacíos— sugeriría que la pregunta le aplica.
        fila["fecha_suspension"] = cruda.get("fecha_suspension") or None
        fila["motivo_suspension"] = cruda.get("motivo_suspension") or None
    return fila


def _sin_centinela(valor: Any) -> int | None:
    """`-1` significa «sin cupo», no «cupo de menos uno».

    `0` sí sería un cupo válido —cero llamadas—, así que no se puede usar
    ausencia genérica: hay que comparar con el centinela declarado.
    """
    if valor is None:
        return None
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return None if numero < 0 else numero


def _dias_hasta(ahora: int, expiracion: Any) -> int | None:
    fin = a_entero_ms(expiracion)
    if fin is None:
        return None
    return max(0, (fin - ahora) // DIA_MS)
