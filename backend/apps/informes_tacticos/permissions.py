"""DRF permissions for informes_tacticos module.

FR-007 de la spec pedía roles "Operador y Supervisor" — el rol "Supervisor" no
existe en el sistema (ver `.specify/docs/actors.md`). Se usan los roles reales:
Operador (uso operativo diario) y Administrador (función de supervisión dentro
del alcance operativo actual), igual que `apps.accidentes.permissions`.
"""

from rest_framework.permissions import BasePermission

from core.auth.roles_tacticos import (
    AUTORIDAD_EMERGENCIAS,
    AUTORIDAD_SOPORTE,
    AUTORIDAD_VENTAS_CRM,
    AUTORIDAD_RED_OPERATIVA_CRECIMIENTO,
    AUTORIDAD_RED_OPERATIVA_VALIDACION,
    AUTORIDAD_SUSCRIPCIONES_CATALOGO,
    AUTORIDAD_SUSCRIPCIONES_FINANZAS,
    AUTORIDAD_CUENTAS,
    AUTORIDAD_CUENTAS_ACCESOS_TECNICOS,
    AUTORIDAD_PARTNERS_API,
)

#: ⚠️ **El `Administrador` no ve informes de gestión.**
#:
#: Decisión del 2026-08-19: su papel es **operar el sistema**, no leer la gestión
#: de los departamentos. Hasta entonces entraba a los 84 informes compuestos
#: —cada director abre entre 3 y 17— y eso anulaba los dos repartos de autoridad
#: que este módulo se esfuerza en mantener: en Red Operativa veía crecimiento y
#: validación, y en Suscripciones finanzas y catálogo.
#:
#: Sigue entrando a los **listados simples**, que son trabajo operativo.

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
    * El **responsable operativo** —el `Administrador`— entra también, y ve lo
      mismo que el director.

    ⚠️ **El `Administrador` NO entra acotado, y este endpoint no acota a nadie.**

    Esto afirmaba que entraba limitado por titularidad. Medido el 2026-08-19: el
    director y el `Administrador` reciben **exactamente las mismas filas**, y
    `meta.acotado_a` viaja vacío para los dos, porque aquí no hay eje de
    titularidad — un accidente, una región o una suscripción no tienen «dueño»
    al que reducir la vista.

    Se corrige el texto y no el código a propósito: describir un control que no
    existe es peor que no describir ninguno, porque quien lo lee deja de
    buscarlo. Si el `Administrador` debe ver menos, la vía es **no dejarle
    abrir** el informe, no un acotamiento que aquí no significa nada.

    Queda como decisión abierta: hoy el `Administrador` puede abrir los 84
    informes compuestos y cada director entre 3 y 17.

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
        return bool(roles & AUTORIDAD_EMERGENCIAS)


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

    El **Administrador** entra a las dos materias: su papel no está repartido.

    ⚠️ **El `Administrador` NO entra acotado, y este endpoint no acota a nadie.**

    Esto afirmaba que entraba limitado por titularidad. Medido el 2026-08-19: el
    director y el `Administrador` reciben **exactamente las mismas filas**, y
    `meta.acotado_a` viaja vacío para los dos, porque aquí no hay eje de
    titularidad — un accidente, una región o una suscripción no tienen «dueño»
    al que reducir la vista.

    Se corrige el texto y no el código a propósito: describir un control que no
    existe es peor que no describir ninguno, porque quien lo lee deja de
    buscarlo. Si el `Administrador` debe ver menos, la vía es **no dejarle
    abrir** el informe, no un acotamiento que aquí no significa nada.

    Queda como decisión abierta: hoy el `Administrador` puede abrir los 84
    informes compuestos y cada director entre 3 y 17.

    ⚠️ Ojo a lo que eso implica **aquí en concreto**: este permiso existe para
    que ningún director vea la materia del otro, y el `Administrador` las ve las
    dos. El reparto se sostiene entre directores y no frente a él.

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
        return bool(roles & AUTORIDAD_POR_MATERIA[materia])


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
            roles & {ROLE_GERENTE_VENTAS}
        )


#: Materia → roles que la gobiernan. Ver `SuscripcionesCompuestosPermission`.
AUTORIDAD_SUSCRIPCIONES_POR_MATERIA = {
    "finanzas": AUTORIDAD_SUSCRIPCIONES_FINANZAS,
    "catalogo": AUTORIDAD_SUSCRIPCIONES_CATALOGO,
}


class SuscripcionesCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Suscripciones (FR-038, FR-039).

    ⚠️ **La autoridad está repartida, y esto es lo que la reparte.**

    El **Director Financiero** gobierna facturación, cobro y mora. El **Director
    de Estrategia** gobierna el catálogo y los precios. Cada uno entra **a su
    materia y no a la del otro**: admitir a las dos autoridades del departamento
    y quedarse tranquilo daría a cada uno acceso a la materia ajena, sin síntoma.

    El **Administrador** entra a las dos materias.

    ⚠️ **El `Administrador` NO entra acotado, y este endpoint no acota a nadie.**

    Esto afirmaba que entraba limitado por titularidad. Medido el 2026-08-19: el
    director y el `Administrador` reciben **exactamente las mismas filas**, y
    `meta.acotado_a` viaja vacío para los dos, porque aquí no hay eje de
    titularidad — un accidente, una región o una suscripción no tienen «dueño»
    al que reducir la vista.

    Se corrige el texto y no el código a propósito: describir un control que no
    existe es peor que no describir ninguno, porque quien lo lee deja de
    buscarlo. Si el `Administrador` debe ver menos, la vía es **no dejarle
    abrir** el informe, no un acotamiento que aquí no significa nada.

    Queda como decisión abierta: hoy el `Administrador` puede abrir los 84
    informes compuestos y cada director entre 3 y 17.

    ⚠️ Igual que en Red Operativa: el reparto finanzas/catálogo se sostiene entre
    directores y no frente al `Administrador`, que ve las dos.

    Un informe **sin materia declarada no lo ve nadie**.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False

        from apps.informes_tacticos.services.suscripciones_compuestos_service import (
            SuscripcionesCompuestosService,
        )

        materia = SuscripcionesCompuestosService().materia_de(view.kwargs.get("informe", ""))
        if materia is None:
            return False

        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_SUSCRIPCIONES_POR_MATERIA[materia])


#: Rol operativo del agente de soporte. Entra **acotado a sus tickets**.
ROLE_AGENTE_SOPORTE = "Soporte"


class SoporteCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Soporte al Cliente (FR-030 a FR-033).

    * El **Gerente de Éxito del Cliente** es la autoridad: ve el departamento
      entero, sin acotamiento por titularidad.
    * El **agente** ve **sus propios tickets**. El acotamiento lo aplica la
      vista, no esta clase.
    * Un **cliente** no entra.

    ⚠️ **La exención no alcanza al dato sensible.** Que el gerente vea el
    departamento entero no le da asunto, descripción, mensajes ni notas
    internas: esas columnas no están en el modelo.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_SOPORTE) or bool(
            roles & {ROLE_AGENTE_SOPORTE}
        )


class CuentasCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Cuentas y Clientes (FR-030).

    ⚠️ **La autoridad está repartida por materia**, como en Red Operativa y en
    Suscripciones:

    * el **Director de Cuentas** responde del **ciclo de vida** de las cuentas y
      de su **incorporación**;
    * el **Director Tecnológico** gobierna **solo** la capa de **accesos
      técnicos** (§5.1). Un informe de churn o de onboarding no lo ve.

    Cada uno entra a su materia y no a la del otro: quien fija los criterios
    técnicos de acceso no es quien responde de por qué se van los clientes.

    ⚠️ **El `Administrador` ya no entra**, y el cargo nuevo es lo que lo hizo
    posible. Hasta el 2026-08-19 era la única forma de abrir siete de estos nueve
    informes, porque el departamento **no tenía autoridad propia**: se leían por
    ser administrador del sistema, no por responder de ellos. Retirarlo antes de
    crear el cargo los habría dejado inalcanzables.

    Un informe **sin materia declarada no lo ve nadie**, igual que en los otros
    departamentos repartidos: una materia por defecto dejaría accesible un
    informe nuevo a quien no le corresponde, y en silencio.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False

        from apps.informes_tacticos.services.cuentas_compuestos_service import (
            MATERIA_ACCESO,
            CuentasCompuestosService,
        )

        materia = CuentasCompuestosService().materia_de(view.kwargs.get("informe", ""))
        if materia is None:
            return False

        roles = set(getattr(user, "roles", []))
        if materia == MATERIA_ACCESO:
            return bool(roles & AUTORIDAD_CUENTAS_ACCESOS_TECNICOS)
        return bool(roles & AUTORIDAD_CUENTAS)


class PartnersCompuestosPermission(BasePermission):
    """Acceso a los informes compuestos de Partners y API (FR-034).

    El **Director Tecnológico** y el **Administrador** entran. Un rol de
    **partner** no: son cifras comparadas de todos los partners.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_PARTNERS_API)

