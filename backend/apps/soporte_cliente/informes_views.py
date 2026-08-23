"""Vistas de los dos listados tácticos de Soporte al Cliente.

Vive junto a `views.py` y no dentro de un paquete `views/` porque ese módulo ya
existe como fichero: convertirlo en paquete rompería los imports del módulo
operativo por un detalle de organización que no aporta nada.

⚠️ El acotamiento se decide por lo que NO se tiene
---------------------------------------------------
`resolver_organizacion` recibe los roles de atención como amplios y los de
reporte como acotados. Un usuario con **ambos** cae en la rama amplia, que es
justo FR-012: tener un rol de atención saca del acotamiento.

Decidirlo por «ser Cliente» —la comparación que el módulo operativo ya tuvo que
corregir— dejaría al **Partner de integración viendo tickets ajenos**, porque
también reporta y no es Cliente. Una prueba comprueba que este acotamiento y el
`es_solo_reportador` del módulo operativo coinciden en toda combinación de roles.

Criterio de pertenencia: **amplio** (`VINCULO_A_CUENTA`), el mismo que usa la
pantalla operativa de tickets. Un informe nunca es más amplio que su pantalla, y
tampoco más estrecho.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.soporte_cliente import domain_constants as dc
from apps.soporte_cliente.permissions import (
    ROLES_ATENCION,
    ROLES_REPORTADORES,
    InformesEscaladosPermission,
    InformesTicketsPermission,
)
from apps.soporte_cliente.services.informes_escalados_service import (
    InformesEscaladosService,
)
from apps.soporte_cliente.services.informes_tickets_service import (
    InformesTicketsService,
)
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import (
    ACOTADO_TODOS,
    AccesoDenegado,
    resolver_organizacion,
)
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.pertenencia import VINCULO_A_CUENTA
from core.informes.vistas import ERRORES_DE_VALIDACION, ListadoBaseView
from core.repositories.soporte.informes_escalados_repository import (
    CURSOR_ESCALADOS,
    ORDEN_ESCALADOS,
    TIPO_PUBLICO,
)
from core.repositories.soporte.informes_tickets_repository import (
    CURSOR_TICKETS,
    ORDEN_TICKETS,
)

#: Los estados del ticket, **importados** del dominio.
ESTADOS_TICKET = (
    dc.ESTADO_ABIERTO,
    dc.ESTADO_PENDIENTE_DE_CLASIFICACION,
    dc.ESTADO_EN_PROGRESO,
    dc.ESTADO_ESCALADO,
    dc.ESTADO_RESUELTO,
    dc.ESTADO_CERRADO,
    dc.ESTADO_REABIERTO,
)

#: ⚠️ **Cinco, no cuatro.** `data-model.md` enumera cuatro situaciones de
#: compromiso; el dominio tiene una quinta, `cumplido`, que
#: `resolver_ticket_service` escribe al resolver dentro de plazo.
#:
#: Implementar las cuatro de la spec dejaría el filtro rechazando con `400` un
#: valor legítimo y haría imposible listar los tickets resueltos a tiempo. Se
#: importan del dominio, que es donde se escriben.
SITUACIONES_COMPROMISO = (
    dc.SLA_EN_CURSO,
    dc.SLA_EN_RIESGO,
    dc.SLA_INCUMPLIDO,
    dc.SLA_SIN_COMPROMISO,
    dc.SLA_CUMPLIDO,
)


class TicketsView(ListadoBaseView):
    """L1 — la cola, acotada a quien no atiende."""

    permission_classes = [IsAuthenticated401, InformesTicketsPermission]
    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_TICKETS)
            cursor = CURSOR_TICKETS.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado", ESTADOS_TICKET
            )
            situacion = self.parse_enumeracion(
                request.query_params, "situacion_compromiso", SITUACIONES_COMPROMISO
            )
            prioridad = request.query_params.get("prioridad") or None
            tipo_incidencia = request.query_params.get("tipo_incidencia") or None
            agente = self.parse_entero(request.query_params, "agente", minimo=1)
            con_factura = self.parse_booleano(request.query_params, "con_factura")
            cuenta = self.parse_entero(request.query_params, "cuenta", minimo=1)

            acotamiento = resolver_organizacion(
                roles=getattr(request.user, "roles", []) or [],
                user_id=request.user.idusuario,
                roles_amplios=ROLES_ATENCION,
                roles_acotados=ROLES_REPORTADORES,
                criterio=VINCULO_A_CUENTA,
                cuenta_pedida=cuenta,
            )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesTicketsService().tickets(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            estado=estado,
            situacion_compromiso=situacion,
            prioridad=prioridad,
            tipo_incidencia=tipo_incidencia,
            agente=agente,
            con_factura=con_factura,
        )
        return listado_response(
            pagina,
            {
                "estado": estado,
                "situacion_compromiso": situacion,
                "prioridad": prioridad,
                "tipo_incidencia": tipo_incidencia,
                "agente": agente,
                "con_factura": con_factura,
                "cuenta": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
        )


class EscaladosView(ListadoBaseView):
    """L2 — escalados del período. **Solo roles de atención** (FR-008).

    Sin acotamiento por cuenta: quien entra aquí ya atiende tickets de todas.
    """

    permission_classes = [IsAuthenticated401, InformesEscaladosPermission]
    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_ESCALADOS)
            cursor = CURSOR_ESCALADOS.decodificar(request.query_params.get("cursor"))
            tipo = self.parse_enumeracion(
                request.query_params, "tipo_escalado", sorted(TIPO_PUBLICO)
            )
            cuenta = self.parse_entero(request.query_params, "cuenta", minimo=1)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesEscaladosService().escalados(
            cursor=cursor,
            limit=limit,
            orden=orden,
            tipo_escalado=tipo,
            cuenta=cuenta,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "tipo_escalado": tipo, "cuenta": cuenta},
            acotado_a=ACOTADO_TODOS,
        )


class CatalogosSoporteView(ListadoBaseView):
    """Opciones de «Cuenta» y «Agente» de los dos listados de Soporte.

    ⚠️ **«Agente» no es el directorio entero.** Ofrecer las treinta y una
    personas del sistema —incluidas las unidades registradas como usuario— no
    ayuda a elegir y sugiere que cualquiera de ellas podría atender un ticket.
    Solo entran quienes llevan un rol de atención.

    ⚠️ **La lista de cuentas se acota igual que las filas.** Un cliente que entra
    a su propia cola no puede ver el catálogo completo de cuentas: eso diría
    quién más usa la plataforma, y lo diría con su listado devolviendo lo de
    siempre. Se resuelve con el mismo `resolver_organizacion` que el listado.
    """

    permission_classes = [IsAuthenticated401, InformesTicketsPermission]
    admite_rango = False

    def get(self, request: Request):
        from core.api.response_envelope import success_response
        from core.informes.catalogos import CatalogosFiltrosRepository

        try:
            acotamiento = resolver_organizacion(
                roles=getattr(request.user, "roles", []) or [],
                user_id=request.user.idusuario,
                roles_amplios=ROLES_ATENCION,
                roles_acotados=ROLES_REPORTADORES,
                criterio=VINCULO_A_CUENTA,
                cuenta_pedida=None,
            )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        repo = CatalogosFiltrosRepository()
        # `titular is None` es el rol de atención: ve todas las cuentas. Un
        # reportador queda acotado a la suya, y **solo a la suya**.
        cuentas = (
            None if acotamiento.titular is None else frozenset({int(acotamiento.titular)})
        )
        return success_response(
            {
                "cuenta": repo.clientes(cuentas),
                "agente": repo.usuarios_con_rol(sorted(ROLES_ATENCION)),
            },
            meta={"acotado_a": acotamiento.alcance},
        )
