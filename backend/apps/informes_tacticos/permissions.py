"""DRF permissions for informes_tacticos module.

FR-007 de la spec pedía roles "Operador y Supervisor" — el rol "Supervisor" no
existe en el sistema (ver `.specify/docs/actors.md`). Se usan los roles reales:
Operador (uso operativo diario) y Administrador (función de supervisión dentro
del alcance operativo actual), igual que `apps.accidentes.permissions`.
"""

from rest_framework.permissions import BasePermission

from core.auth.roles_tacticos import (
    AUTORIDAD_EMERGENCIAS,
    AUTORIDAD_VENTAS_CRM,
    AUTORIDAD_RED_OPERATIVA_CRECIMIENTO,
    AUTORIDAD_RED_OPERATIVA_VALIDACION,
)

ROLE_OPERADOR = "Operador"
ROLE_ADMIN = "Administrador"

INFORMES_TACTICOS_ROLES = frozenset({ROLE_OPERADOR, ROLE_ADMIN})


class InformesTacticosLecturaPermission(BasePermission):
    """Read access to informes tácticos simples: Operador or Administrador."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & INFORMES_TACTICOS_ROLES)


class EmergenciasCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Emergencias (FR-021, FR-023).

    Dos cargos entran, por razones distintas:

    * El **Director de Operaciones** es la autoridad del departamento. Entra sin
      acotamiento por titularidad: ve el departamento entero, que es de lo que
      responde.
    * El **responsable operativo** —el `Administrador`— entra **con** su
      acotamiento, el mismo que ya se le aplica en los listados simples.

    Quien no es ninguno de los dos no entra. El `Operador` sí ve los listados
    simples y **no** ve estos: un listado es su trabajo del día, y un informe
    compuesto es una lectura de gestión sobre el trabajo de todos.

    ⚠️ **La exención de acotamiento no alcanza al dato sensible.** Que el
    Director de Operaciones vea el departamento entero no le da coordenadas,
    identidad de personas ni texto libre interno: esas exclusiones son
    constitucionales, valen para todos los cargos, y no se resuelven aquí sino
    enumerando columnas en las consultas del catálogo. Esta clase decide **quién
    entra**, nunca **qué se le muestra de más**.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_EMERGENCIAS) or ROLE_ADMIN in roles


#: Materia → roles que la gobiernan. Ver `RedOperativaCompuestosPermission`.
AUTORIDAD_POR_MATERIA = {
    "crecimiento": AUTORIDAD_RED_OPERATIVA_CRECIMIENTO,
    "validacion": AUTORIDAD_RED_OPERATIVA_VALIDACION,
}


class RedOperativaCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Red Operativa (FR-025, FR-026).

    ⚠️ **La autoridad está repartida, y esto es lo que la reparte.**

    Este departamento no tiene una jefatura única. El **Director de Expansión**
    gobierna el crecimiento y la flota; el **Director Tecnológico**, los
    criterios de validación de región. Cada uno entra **a su materia y no a la
    del otro**, que es la parte fácil de olvidar: lo natural al escribir un
    permiso es admitir a las dos autoridades del departamento y quedarse
    tranquilo, y eso daría a cada director acceso a la materia del otro sin que
    nada fallara ni nadie se quejara.

    El **Administrador** entra a las dos, con su acotamiento: es el responsable
    operativo, y su papel no está repartido.

    Un informe **sin materia declarada no lo ve nadie**. Es deliberado: la
    alternativa —una materia por defecto— dejaría accesible un informe nuevo a
    quien no le corresponde, y en silencio.

    ⚠️ **La exención no alcanza al dato sensible** (FR-026). Que un director vea
    su materia entera no le da coordenadas, contacto de proveedor ni la identidad
    de quien validó una región: esas exclusiones son constitucionales, valen para
    todos los cargos, y se resuelven enumerando columnas en las consultas. Esta
    clase decide **quién entra**, nunca **qué se le muestra de más**.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False

        from apps.informes_tacticos.services.red_operativa_compuestos_service import (
            RedOperativaCompuestosService,
        )

        materia = RedOperativaCompuestosService().materia_de(view.kwargs.get("informe", ""))
        if materia is None:
            return False

        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_POR_MATERIA[materia]) or ROLE_ADMIN in roles


#: Rol operativo del ejecutivo comercial. Entra **acotado a sus prospectos**.
ROLE_GERENTE_VENTAS = "GerenteVentas"


class VentasCrmCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Ventas y CRM (FR-033, FR-034).

    Dos cargos entran, y **no ven lo mismo**:

    * El **Director de Marketing** es la autoridad del departamento: ve el
      departamento entero, sin acotamiento por titularidad.
    * El **ejecutivo comercial** ve **sus propios prospectos**, no los de los
      demas. El acotamiento no lo decide esta clase —eso lo hace la vista, que
      pasa su identificador al servicio— pero si decide que entra.

    El `Administrador` entra tambien, acotado igual que el ejecutivo: es el
    responsable operativo, y su papel no le da la vista de departamento.

    ⚠️ **La exencion del director no alcanza al dato personal.** Este es el
    departamento con mas dato personal del sistema —prospectos con nombre,
    correo, telefono y cargo— y **nada de eso esta en el modelo**. Que el
    director vea el departamento entero no le da el telefono de nadie: esa
    exclusion es constitucional y se resuelve en el esquema, no aqui.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_VENTAS_CRM) or bool(
            roles & {ROLE_ADMIN, ROLE_GERENTE_VENTAS}
        )
