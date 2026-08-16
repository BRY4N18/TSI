"""Base común de los cuatro listados tácticos de Red Operativa.

Declara el **criterio de pertenencia** de este departamento de forma explícita
(research D1). No se deja al defecto transversal a propósito: un cambio en ese
defecto alteraría en silencio quién ve la flota de una empresa proveedora.
"""

from __future__ import annotations

from rest_framework.request import Request

from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import Acotamiento, resolver_organizacion
from core.informes.pertenencia import ADMIN_LOCAL
from core.informes.vistas import ListadoBaseView

#: **Administrador local**, el criterio estricto — el mismo que exige
#: `IsProveedorFlota` en la pantalla operativa de alta de unidades.
#:
#: Usar el amplio daría, por informe, la flota completa de una organización a un
#: empleado al que esa pantalla rechaza. Es la puerta trasera exacta que la regla
#: del contrato común prohíbe, y lo fija `test_acotamiento_no_amplia.py`.
CRITERIO_PERTENENCIA = ADMIN_LOCAL


class ListadoRedOperativaBaseView(ListadoBaseView):
    """Base de los cuatro: permiso por materia y acotamiento cuando aplica."""

    permission_classes = [IsAuthenticated401]

    roles_amplios: frozenset[str] = frozenset()
    roles_acotados: frozenset[str] = frozenset()

    def acotar(self, request: Request) -> Acotamiento:
        cuenta = self.parse_entero(request.query_params, "proveedor", minimo=1)
        return resolver_organizacion(
            roles=getattr(request.user, "roles", []) or [],
            user_id=request.user.idusuario,
            roles_amplios=self.roles_amplios,
            roles_acotados=self.roles_acotados,
            criterio=CRITERIO_PERTENENCIA,
            cuenta_pedida=cuenta,
        )
