"""Acotamiento por titularidad: a quién ve cada quien en un listado táctico.

Vive en `core/informes/` y no en la app de un departamento porque **seis
departamentos vienen detrás** y todos acotan por algo: Ventas por ejecutivo,
Soporte por cliente reportador, Partners por partner, Red Operativa por
proveedor de flota. Si cada uno lo resolviera por su cuenta, el patrón divergiría
y la puerta trasera aparecería en el que se despistara — que es exactamente lo
que casi ocurre en F18 con el rol de partner.

El comportamiento no se inventa aquí
------------------------------------
Se copia del que ya está en producción y verificado
(`apps/ventas_crm/services/consulta_notificacion_ventas_service.py:25-37`).
Copiarlo mantiene coherente lo que el usuario ve en pantalla y lo que obtiene por
informe, que es lo que exige la regla del contrato común: **un informe nunca es
más amplio que la pantalla operativa del mismo dato**.

| Rol del solicitante | No indica titular | Indica otro titular |
|---|---|---|
| Rol amplio (Administrador, autoridad) | Ve **todos** | Filtra por ese titular |
| Rol acotado (Gerente, Cliente, Partner…) | Forzado **a lo suyo** | **Negativa** |
| Cualquier otro | Negativa | Negativa |

Por qué pedir lo ajeno es negativa y no sustitución
---------------------------------------------------
Devolverle su propia cartera a quien pidió la ajena **oculta al solicitante que
pidió algo indebido**, y produce un informe que parece responder a una pregunta
que nadie hizo. Un `403` es información; una sustitución silenciosa es una
respuesta plausible y equivocada.

Qué decide este módulo y qué no
-------------------------------
Devuelve **a quién** acotar. **No** decide por qué columna: eso cambia por
listado —`idusuario` en prospectos, `idusuariogerentenotificado` en
notificaciones— y lo sabe el repositorio. Esa separación es la que permite
reutilizarlo cuando el eje sea cliente, partner o proveedor.
"""

from __future__ import annotations

from typing import Callable, Iterable, NamedTuple


class AccesoDenegado(PermissionError):
    """El solicitante no puede ver lo que pide.

    Es `403`, no `404` ni una lista vacía: la diferencia le dice al consumidor
    que el problema es de permisos y no de datos.
    """


#: Valores de `meta.acotado_a`, que declaran el alcance real de la respuesta.
ACOTADO_PROPIOS = "propios"
ACOTADO_TODOS = "todos"


class Acotamiento(NamedTuple):
    """Resultado de resolver quién ve qué.

    `titular` es el valor por el que el repositorio filtrará, o `None` para no
    filtrar. `alcance` es lo que viaja en `meta.acotado_a`.
    """

    titular: int | None
    alcance: str

    @property
    def acotado(self) -> bool:
        return self.titular is not None


def resolver(
    *,
    roles: Iterable[str] | None,
    user_id: int,
    roles_amplios: Iterable[str],
    roles_acotados: Iterable[str],
    titular_pedido: int | None = None,
) -> Acotamiento:
    """Decide el acotamiento de una petición, o niega el acceso.

    `roles_amplios` ven todo el departamento y **pueden** filtrar por un titular
    concreto. `roles_acotados` quedan forzados a lo suyo. Quien no esté en
    ninguno de los dos conjuntos no accede.

    El orden de las comprobaciones importa: **primero se descarta a quien no
    tiene ningún rol reconocido**. Si se resolviera el titular antes, un rol
    desconocido con `titular_pedido` ausente caería en la rama de "ver todo".
    """
    del_solicitante = set(roles or [])
    amplios = set(roles_amplios)
    acotados = set(roles_acotados)

    solapan = amplios & acotados
    if solapan:
        # Un rol en ambos conjuntos haría el resultado dependiente del orden de
        # evaluación — es decir, del azar. Se detecta al configurar, no en
        # producción con datos de por medio.
        raise ValueError(
            f"Los roles {sorted(solapan)} estan declarados como amplios y acotados a la vez."
        )

    es_amplio = bool(del_solicitante & amplios)
    es_acotado = bool(del_solicitante & acotados)

    if not es_amplio and not es_acotado:
        raise AccesoDenegado("El rol del solicitante no accede a este listado.")

    if es_amplio:
        # Puede filtrar por quien quiera, o no filtrar. Que declare un titular
        # no reduce su alcance declarado: sigue teniendo acceso a todos y ha
        # elegido mirar a uno.
        if titular_pedido is not None:
            return Acotamiento(titular=int(titular_pedido), alcance=ACOTADO_TODOS)
        return Acotamiento(titular=None, alcance=ACOTADO_TODOS)

    if titular_pedido is not None and int(titular_pedido) != int(user_id):
        raise AccesoDenegado("No puede consultar la cartera de otro titular.")

    return Acotamiento(titular=int(user_id), alcance=ACOTADO_PROPIOS)


# ── Segundo eje: la organizacion ─────────────────────────────────────────────
#
# `resolver` asume que **el titular es el solicitante**: en Ventas y CRM, la
# cartera de un gerente se acota por su propio identificador de usuario.
#
# Aqui hay un salto de indireccion en medio: el usuario pregunta y el resultado
# se acota a la **cuenta cliente a la que pertenece**. Es una segunda funcion, no
# una reescritura de la primera.
#
# Y no es un caso aislado: Red Operativa acota por proveedor de flota, Partners
# por partner y Soporte por cliente reportador — los tres son este mismo eje. Si
# no se resuelve aqui, la quinta y la sexta copia aparecen solas.


class OrganizacionNoResuelta(AccesoDenegado):
    """El solicitante no pertenece a ninguna cuenta consultable.

    Hereda de `AccesoDenegado` a proposito: para la vista es el mismo `403`. La
    subclase existe para que el mensaje pueda distinguir "no tienes cuenta" de
    "esa cuenta no es la tuya", que son dos situaciones muy distintas para quien
    las lee.
    """


def resolver_organizacion(
    *,
    roles: Iterable[str] | None,
    user_id: int,
    roles_amplios: Iterable[str],
    roles_acotados: Iterable[str],
    resolver_cuenta: Callable[[int], int | None] | None = None,
    criterio: str | None = None,
    cuenta_pedida: int | None = None,
) -> Acotamiento:
    """Acota por la cuenta cliente del solicitante, resuelta por pertenencia.

    **El criterio de pertenencia es explicito y cada listado declara el suyo**
    (research D1 de Red Operativa). «Pertenecer a una cuenta» significa dos cosas
    distintas en este sistema —ser su administrador local, o estar vinculado a
    ella— y las pantallas operativas de cada departamento usan una u otra.
    Unificarlas romperia la regla del contrato comun en un departamento u otro.

    Se declara de una de dos formas, y **solo una**:

    * `criterio=` con un nombre de `core.informes.pertenencia` — la via normal;
    * `resolver_cuenta=` con una funcion propia — para pruebas y para ejes que
      no sean la cuenta cliente.

    Si no se declara ninguna se usa **`ADMIN_LOCAL`**, que es lo que Suscripciones
    ya hacia antes de que este parametro existiera: la ampliacion **no cambia el
    comportamiento por defecto**, solo anade una opcion.

    **No exige que la cuenta este activa**, y esa es la diferencia deliberada
    con `ProveedorAccessService.resolve_cliente_activo`. Aquel controla
    **escrituras** —dar de alta unidades— y ahi tiene sentido exigir una cuenta
    vigente. Este controla la **lectura de los propios registros**, y una cuenta
    suspendida o pendiente es justamente donde su responsable necesita mirar para
    saber que regularizar. Negarle el acceso lo dejaria a ciegas sobre su propia
    deuda.
    """
    if resolver_cuenta is not None and criterio is not None:
        # Declarar los dos dejaria en duda cual gana, y la respuesta seria
        # distinta segun el orden en que alguien leyera el codigo.
        raise ValueError(
            "Declare 'criterio' o 'resolver_cuenta', no ambos: son dos formas de "
            "decir lo mismo y juntas hacen ambiguo cual se aplica."
        )

    del_solicitante = set(roles or [])
    amplios = set(roles_amplios)
    acotados = set(roles_acotados)

    solapan = amplios & acotados
    if solapan:
        raise ValueError(
            f"Los roles {sorted(solapan)} estan declarados como amplios y acotados a la vez."
        )

    es_amplio = bool(del_solicitante & amplios)
    es_acotado = bool(del_solicitante & acotados)

    if not es_amplio and not es_acotado:
        raise AccesoDenegado("El rol del solicitante no accede a este listado.")

    if es_amplio:
        if cuenta_pedida is not None:
            return Acotamiento(titular=int(cuenta_pedida), alcance=ACOTADO_TODOS)
        return Acotamiento(titular=None, alcance=ACOTADO_TODOS)

    if resolver_cuenta is None:
        from core.informes.pertenencia import ADMIN_LOCAL, resolutor

        resolver_cuenta = resolutor(criterio or ADMIN_LOCAL)

    # Rol acotado: se resuelve su cuenta **antes** de comparar con la pedida.
    # Al reves, quien no pertenece a ninguna cuenta podria pedir la ajena y
    # recibir un mensaje distinto segun acertara o no el numero.
    propia = resolver_cuenta(int(user_id))
    if propia is None:
        raise OrganizacionNoResuelta(
            "El solicitante no pertenece a ninguna cuenta cliente."
        )

    if cuenta_pedida is not None and int(cuenta_pedida) != int(propia):
        raise AccesoDenegado("No puede consultar los registros de otra cuenta.")

    return Acotamiento(titular=int(propia), alcance=ACOTADO_PROPIOS)
