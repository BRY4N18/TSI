"""Tercer eje de acotamiento: la **cobertura geográfica contratada**.

Los tres ejes anteriores acotan por **titularidad** —quién es el dueño de la
fila—: el ejecutivo de un prospecto, la cuenta de una suscripción, el partner de
una credencial. Este no. Un cliente no ve «sus» accidentes: ve los de las
**zonas que tiene contratadas**, y esos accidentes no son suyos en ningún
sentido.

Por eso es un módulo aparte y no un parámetro más de `resolver_organizacion`.
Cambian las tres cosas a la vez:

* **lo que se resuelve** — un conjunto de ubicaciones, no un identificador;
* **cómo filtra el repositorio** — `IN (…)`, no `= x`;
* **lo que significa no tener nada** — cero resultados, no acceso total.

⚠️ Sin zonas contratadas es CERO, nunca TODO
---------------------------------------------
De las dos lecturas posibles de «este cliente no tiene zonas», una da acceso a
todo el mapa de siniestralidad a quien no contrató nada. Se elige la otra, y se
elige **explícitamente**, porque el fallo por omisión —un `if zonas:` que se
salta el filtro cuando el conjunto está vacío— cae justo en la lectura peligrosa.

⚠️ El conjunto se resuelve UNA VEZ, antes de consultar
--------------------------------------------------------
El acotamiento traduce condados contratados a un conjunto de calles encadenando
catálogos, y ese conjunto viaja al `WHERE`. Es el patrón que el sistema ya
documenta como estándar para resolver un nivel geográfico.

**No se comprueba la zona fila a fila.** El módulo operativo lo hace así hoy —a
diez líneas del sitio donde hace lo correcto—, y no es un filtro: el número de
filas recorridas crece justamente cuando las zonas del cliente son escasas, que
es cuando menos resultados va a haber.
"""

from __future__ import annotations

from typing import Callable, Iterable, NamedTuple

from core.informes.acotamiento import ACOTADO_TODOS, AccesoDenegado

#: Valor propio de `meta.acotado_a` para este eje.
#:
#: No se reutiliza `propios` porque diría algo falso: los accidentes de una zona
#: contratada **no son del cliente**. Un consumidor que leyera `propios` podría
#: entender que el listado abarca todo lo que le pertenece, cuando abarca lo que
#: ocurrió donde contrató cobertura.
ACOTADO_ZONAS = "zonas_contratadas"


class Cobertura(NamedTuple):
    """Resultado de resolver qué ubicaciones puede consultar el solicitante.

    `ubicaciones` es el conjunto por el que el repositorio filtrará, o `None`
    para no filtrar (rol interno). **Un conjunto vacío no es `None`**: significa
    «ninguna ubicación», y el repositorio debe devolver cero filas.

    `solo_cerrados` lo impone el eje, no el consumidor: la emergencia en curso
    es información operativa. Viaja aquí y no en la vista para que ningún
    listado nuevo pueda olvidarlo.
    """

    ubicaciones: frozenset[int] | None
    alcance: str
    solo_cerrados: bool = False

    @property
    def acotado(self) -> bool:
        return self.ubicaciones is not None

    @property
    def sin_cobertura(self) -> bool:
        """Acotado a un conjunto vacío: cero resultados, no acceso total."""
        return self.ubicaciones is not None and not self.ubicaciones


def resolver_cobertura(
    *,
    roles: Iterable[str] | None,
    user_id: int,
    roles_internos: Iterable[str],
    roles_cliente: Iterable[str],
    resolver_ubicaciones: Callable[[int], frozenset[int]],
) -> Cobertura:
    """Decide qué ubicaciones puede consultar el solicitante, o niega el acceso.

    `roles_internos` ven todo, en cualquier situación. `roles_cliente` quedan
    limitados a sus zonas contratadas **y a los casos ya cerrados**. Quien no
    esté en ninguno de los dos conjuntos no accede.

    El orden importa, igual que en los otros ejes: **primero se descarta a quien
    no tiene ningún rol reconocido**. Si se resolvieran las zonas antes, un rol
    desconocido caería en la rama de cliente y recibiría un listado vacío en vez
    de una negativa — y leería «no hay accidentes» donde debía leer «no puedes
    consultar esto».
    """
    del_solicitante = set(roles or [])
    internos = set(roles_internos)
    clientes = set(roles_cliente)

    solapan = internos & clientes
    if solapan:
        # Un rol en ambos conjuntos haría el resultado dependiente del orden de
        # evaluación. Se detecta al configurar, no en producción.
        raise ValueError(
            f"Los roles {sorted(solapan)} estan declarados como internos y "
            f"clientes a la vez."
        )

    es_interno = bool(del_solicitante & internos)
    es_cliente = bool(del_solicitante & clientes)

    if not es_interno and not es_cliente:
        raise AccesoDenegado("El rol del solicitante no accede a este listado.")

    if es_interno:
        # Tener también un rol de cliente no reduce el alcance: es la misma
        # regla del rol mixto de Soporte.
        return Cobertura(ubicaciones=None, alcance=ACOTADO_TODOS, solo_cerrados=False)

    # ⚠️ `frozenset()` vacío, **no** `None`. La diferencia es todo el control de
    # acceso de este eje: `None` significa «no filtres».
    ubicaciones = frozenset(resolver_ubicaciones(int(user_id)))
    return Cobertura(
        ubicaciones=ubicaciones, alcance=ACOTADO_ZONAS, solo_cerrados=True
    )
