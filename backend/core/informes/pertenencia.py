"""Los dos criterios de pertenencia a una cuenta, nombrados y explícitos.

⚠️ «Pertenecer a una organización» significa **dos cosas distintas** en este
sistema, según qué departamento haga la pregunta (research D1 de Red Operativa):

| Criterio | Quién resuelve | Pantalla operativa que lo usa |
|---|---|---|
| **Administrador local** | **Una sola persona** por cuenta | Alta de unidades (Red Operativa), facturación (Suscripciones) |
| **Vínculo a la cuenta** | **Cualquier miembro** | Expediente de cliente (Seguimiento), tickets (Soporte) |

Por qué no se unifican
----------------------
La regla del contrato común es que **un informe nunca sea más amplio que la
pantalla operativa del mismo dato**. Como las pantallas usan criterios distintos,
unificar a uno solo rompería la regla en un departamento u otro:

* unificar al **amplio** daría, por informe, acceso a la flota completa a un
  empleado que la pantalla de alta de unidades rechaza — la puerta trasera exacta
  que la regla prohíbe;
* unificar al **estricto** dejaría sin sus propios tickets a los usuarios de
  Soporte que hoy sí los ven.

Por eso el criterio es un **parámetro explícito** y cada listado declara cuál
usa. No es una opción de configuración: es una afirmación sobre a qué pantalla
está espejando ese listado.

Sobre la corrección
-------------------
El eje «organización» se diseñó en Suscripciones como si la pertenencia fuese un
concepto único. No lo es. **El comportamiento por defecto no cambia** —sigue
siendo el estricto, que es el que Suscripciones ya tenía—: esto añade una
opción, no altera la existente.
"""

from __future__ import annotations

from typing import Callable

#: Nombres de los criterios, para que un listado declare el suyo de forma legible
#: y para que la elección aparezca en las trazas y en las pruebas.
ADMIN_LOCAL = "admin_local"
VINCULO_A_CUENTA = "vinculo"

CRITERIOS = (ADMIN_LOCAL, VINCULO_A_CUENTA)


def por_admin_local(user_id: int) -> int | None:
    """La cuenta de la que el usuario es **administrador local**, o `None`.

    Es el criterio **estricto**: solo una persona por cuenta lo cumple.

    Reutiliza `find_by_admin_local`, que ya excluye las cuentas soft-anuladas
    (`Rechazado_Anulado`) — una cuenta anulada no es una cuenta a la que
    pertenecer. **No exige que la cuenta esté `Activo`**: eso lo exige el flujo
    operativo porque controla escrituras, y aquí se leen los propios registros
    (ver `resolver_organizacion`).
    """
    from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository

    cliente = ClienteRepository().find_by_admin_local(user_id)
    return int(cliente["idcliente"]) if cliente else None


def por_vinculo_a_cuenta(user_id: int) -> int | None:
    """La cuenta a la que el usuario está **vinculado**, o `None`.

    Es el criterio **amplio**: cualquier miembro de la organización lo cumple.
    Lo usan las pantallas de Seguimiento y Soporte, y por tanto lo usarán sus
    listados tácticos.

    Se apoya en `list_cuentas_del_usuario`, que mira `Dim_Usuario_Cliente`
    **y además** el `admin_local_id` — el administrador local también pertenece
    a su cuenta, así que el criterio amplio contiene al estricto.

    ⚠️ **`get_cliente_ids_for_user` no sirve aquí pese a su nombre**: solo mira
    el `admin_local_id`, así que es el criterio estricto disfrazado. Es una
    trampa que el propio `cuenta_usuario_repository` documenta.

    Si un usuario estuviera vinculado a más de una cuenta se toma la primera de
    forma determinista. Es una situación que el modelo operativo no contempla
    —un usuario pertenece a una organización— y forzarla aquí a un error dejaría
    el listado inservible por un dato que nadie puede corregir desde la pantalla.
    """
    from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
        CuentaUsuarioRepository,
    )

    cuentas = CuentaUsuarioRepository().list_cuentas_del_usuario(user_id)
    if not cuentas:
        return None
    return min(int(c["idcliente"]) for c in cuentas)


#: El resolutor de cada criterio. `ADMIN_LOCAL` es el **defecto** de
#: `resolver_organizacion`, que es lo que Suscripciones ya hacía.
RESOLUTOR_POR_CRITERIO: dict[str, Callable[[int], int | None]] = {
    ADMIN_LOCAL: por_admin_local,
    VINCULO_A_CUENTA: por_vinculo_a_cuenta,
}


def resolutor(criterio: str) -> Callable[[int], int | None]:
    """Devuelve el resolutor del criterio, o falla nombrando los válidos.

    Falla al configurar y no en tiempo de petición: un criterio mal escrito
    resolvería a `None` para todo el mundo y el listado devolveria `403` a
    usuarios legítimos, que es un fallo mucho más difícil de diagnosticar.
    """
    if criterio not in RESOLUTOR_POR_CRITERIO:
        raise ValueError(
            f"Criterio de pertenencia desconocido: '{criterio}'. "
            f"Use uno de: {', '.join(CRITERIOS)}."
        )
    return RESOLUTOR_POR_CRITERIO[criterio]
