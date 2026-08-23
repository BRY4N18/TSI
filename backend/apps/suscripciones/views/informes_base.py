"""Base común de los cuatro listados tácticos de Suscripciones y Facturación.

Resuelve el acotamiento por **organización**: quién pregunta → a qué cuenta
pertenece. La resolución de pertenencia se inyecta en el resolutor transversal
en vez de vivir dentro de él, porque `core/informes/` no debe conocer el
repositorio de cuentas — mañana el eje será partner o proveedor.

⚠️ Sobre la pertenencia
-----------------------
Se resuelve por `admin_local_id`, igual que el flujo operativo. **No se exige
que la cuenta esté `Activo`**, a diferencia de
`ProveedorAccessService.resolve_cliente_activo`: aquél controla escrituras y
éste lecturas de los propios registros, y una cuenta suspendida es justamente
donde su responsable necesita mirar para saber qué regularizar (FR-011).
"""

from __future__ import annotations

from rest_framework.request import Request

from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import Acotamiento, resolver_organizacion
from core.informes.vistas import ListadoBaseView
from core.informes.pertenencia import ADMIN_LOCAL
from apps.suscripciones.permissions import (
    AMPLIOS_CATALOGO,
    AMPLIOS_FINANZAS,
    ROLES_INFORMES_ACOTADOS,
    InformesCatalogoPermission,
    InformesFinanzasPermission,
)


#: Criterio de pertenencia de este departamento (research D1 de Red Operativa).
#:
#: **Administrador local**, el estricto — el mismo que usa la pantalla operativa
#: de facturación. Declararlo aquí y no dejarlo al defecto es lo que hace que un
#: cambio en el defecto transversal no altere este departamento en silencio.
CRITERIO_PERTENENCIA = ADMIN_LOCAL


class ListadoSuscripcionesBaseView(ListadoBaseView):
    """Base de los cuatro: acotamiento por organización y permiso por materia."""

    permission_classes = [IsAuthenticated401]

    #: Roles que ven todas las cuentas. Lo declara cada vista, porque la
    #: autoridad de este departamento está **repartida por materia**.
    roles_amplios: frozenset[str] = frozenset()
    roles_acotados: frozenset[str] = frozenset()

    def acotar(self, request: Request) -> Acotamiento:
        cuenta = self.parse_entero(request.query_params, "cuenta", minimo=1)
        return resolver_organizacion(
            roles=getattr(request.user, "roles", []) or [],
            user_id=request.user.idusuario,
            roles_amplios=self.roles_amplios,
            roles_acotados=self.roles_acotados,
            criterio=CRITERIO_PERTENENCIA,
            cuenta_pedida=cuenta,
        )


class CatalogosSuscripcionesView(ListadoSuscripcionesBaseView):
    """Opciones del desplegable «Cuenta», compartido por los cuatro listados.

    Hereda `acotar()` de la base, así que respeta la pertenencia: quien solo ve
    su cuenta recibe **una** opción, no el catálogo entero. Publicarlo completo
    diría qué otras empresas están suscritas.

    ⚠️ **No se instancia directamente.** La autoridad de este departamento está
    repartida por materia —finanzas y catálogo tienen directores distintos—, así
    que los roles no pueden declararse aquí: heredar sin declararlos deja
    `roles_amplios` vacío y **todo el mundo recibe un 400**, que es exactamente
    lo que pasó al escribirlo. Cada materia tiene su subclase, abajo.
    """

    def get(self, request: Request):
        from core.api.response_envelope import success_response
        from core.informes.catalogos import CatalogosFiltrosRepository

        try:
            acotamiento = self.acotar(request)
        except Exception as exc:  # noqa: BLE001 — mismo manejo que los listados
            return self.manejar_peticion_invalida(exc)

        cuentas = (
            None if acotamiento.titular is None else frozenset({int(acotamiento.titular)})
        )
        return success_response(
            {"cuenta": CatalogosFiltrosRepository().clientes(cuentas)},
            meta={"acotado_a": acotamiento.alcance},
        )


class CatalogosCatalogoView(CatalogosSuscripcionesView):
    """Catálogos de la materia **catálogo y precios** (Director de Estrategia)."""

    permission_classes = [IsAuthenticated401, InformesCatalogoPermission]
    roles_amplios = AMPLIOS_CATALOGO
    roles_acotados = ROLES_INFORMES_ACOTADOS


class CatalogosFinanzasView(CatalogosSuscripcionesView):
    """Catálogos de la materia **facturación y cobro** (Director Financiero)."""

    permission_classes = [IsAuthenticated401, InformesFinanzasPermission]
    roles_amplios = AMPLIOS_FINANZAS
    roles_acotados = ROLES_INFORMES_ACOTADOS
