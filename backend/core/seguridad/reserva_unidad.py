"""Reserva de unidad de emergencia — cierra la ventana entre comprobar y escribir.

**El problema.** `AsignacionManualService.asignar()` comprueba la disponibilidad
leyendo de Pinot y luego escribe vía Kafka. Entre ambas cosas no hay transacción
—son dos sistemas distintos— y la escritura **no es visible de inmediato**: viaja
por Kafka y Pinot la ingiere de forma asíncrona. La comprobación de la segunda
petición no ve el despacho que la primera acaba de crear aunque haya pasado un
segundo entero.

No es una carrera de milisegundos: la ventana mide lo que tarda la ingesta.
Reproducido en `tests/seguridad/test_concurrencia_despacho.py` — dos operadores,
dos despachos activos para la misma ambulancia, **cero errores**. Una de las dos
no llega y nadie se entera.

**La primitiva.** `cache.add()` es una operación de comprobar-e-insertar atómica:
inserta solo si la clave no existe, y devuelve si lo consiguió. Es la misma
llamada tanto en `LocMemCache` como en Redis o Memcached, así que el código no
cambia si mañana se configura un backend compartido.

⚠️ **Límite actual, y conviene tenerlo escrito.** Sin `CACHES` en `settings.py`,
Django usa `LocMemCache`, que es **por proceso**. Con varios workers de gunicorn
la reserva protege dentro de cada worker pero no entre ellos: dos peticiones
atendidas por workers distintos podrían volver a colisionar. Cerrar eso del todo
exige un backend compartido —Redis— que hoy no está desplegado. Lo que sí hace
esta reserva es reducir la ventana de «lo que tarda Kafka+Pinot» (segundos) a
«lo que tarda un reparto entre workers» (una petición), y dejar el resto visible
en vez de silencioso.

El TTL existe para que un fallo a mitad de la asignación no deje la unidad
bloqueada para siempre: la reserva caduca sola.
"""

from __future__ import annotations

from contextlib import contextmanager

from django.core.cache import cache

#: Cuánto vive la reserva si nadie la suelta. Debe cubrir con holgura el trayecto
#: Kafka→Pinot; pasado ese punto, Pinot ya responde con el despacho y la
#: comprobación normal vuelve a ser suficiente.
TTL_SEGUNDOS = 30

PREFIJO = "tsi:reserva:unidad:"


class UnidadReservadaError(RuntimeError):
    """Otra petición está asignando esta misma unidad en este instante."""


def clave(idunidademergencia: int) -> str:
    return f"{PREFIJO}{int(idunidademergencia)}"


@contextmanager
def reservar(idunidademergencia: int):
    """Toma la unidad en exclusiva mientras dura el bloque.

    Se libera siempre —también si la asignación falla— porque una unidad que
    quedó sin asignar debe volver a estar disponible de inmediato: es una
    ambulancia parada.
    """
    if not cache.add(clave(idunidademergencia), "1", TTL_SEGUNDOS):
        raise UnidadReservadaError("Unidad no disponible")
    try:
        yield
    finally:
        cache.delete(clave(idunidademergencia))
