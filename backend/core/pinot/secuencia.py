"""Identificadores nuevos que no dependen de leer lo que acabamos de escribir.

⚠️ El defecto que este módulo existe para cerrar
------------------------------------------------
Cuarenta y tantos repositorios calculaban su identificador siguiente así:

    SELECT MAX(idsession) AS max_id FROM Fact_Session   -->   max_id + 1

Y las tablas son **upsert por clave**. Pinot ingiere de forma asíncrona
**siempre**, así que entre escribir una fila y poder leerla pasa un tiempo. Todo
lo que se cree en esa ventana recibe **el mismo identificador**, y cada uno
sobrescribe al anterior.

No es teórico. El 2026-08-23 la ingesta se retrasó y **34 inicios de sesión
recibieron el id `985`**: el login respondía `200` —el token se emitía— y la
petición siguiente devolvía `401`, porque la sesión que el token nombraba ya la
había pisado la siguiente. Desde fuera parecía un fallo de autenticación.

Qué hace este módulo
--------------------
Mantiene, **en memoria del proceso**, la marca más alta entregada por tabla, y
devuelve siempre por encima de ella:

    siguiente = max(MAX_en_pinot, ultimo_entregado_aquí) + 1

Se sigue consultando Pinot para que un proceso recién arrancado continúe donde
lo dejó el anterior. Lo que añade es que **dentro del proceso la secuencia no
retrocede**, aunque Pinot vaya por detrás.

⚠️ Lo que este módulo NO resuelve, y hay que saberlo
-----------------------------------------------------
La marca vive en el proceso. Con **dos procesos escribiendo a la vez** —varios
workers de gunicorn, o dos réplicas del contenedor— cada uno llevaría su propia
cuenta y volverían a colisionar. Hoy el backend corre como un solo proceso
(`manage.py runserver`), así que la garantía es real; el día que se despliegue
con varios workers, deja de serlo.

La solución completa es un contador **durable y transaccional** —una secuencia en
un relacional, o identificadores que no necesiten leer nada, como el UUID que ya
usa `Fact_Factura.id_factura`—. Las dos son decisiones de arquitectura: la
primera introduce un almacén relacional que este proyecto evita a propósito, y la
segunda exige cambiar el tipo de la clave en decenas de esquemas de Pinot. Está
anotado en `decisiones-pendientes.md`.
"""

from __future__ import annotations

import threading
from typing import Any, Protocol


class _Consultable(Protocol):
    def query(self, sql: str, params: dict[str, Any] | None = ...) -> list[dict]: ...


#: Marca más alta entregada por `(tabla, columna)`. Protegida por `_CERROJO`
#: porque el servidor de desarrollo de Django atiende peticiones en hilos: dos
#: logins simultáneos entrarían aquí a la vez.
_ALTOS: dict[tuple[str, str], int] = {}
_CERROJO = threading.Lock()


def siguiente_id(pinot: _Consultable, tabla: str, columna: str) -> int:
    """Devuelve un identificador por encima de todo lo entregado antes.

    `tabla` y `columna` se interpolan en el SQL: **son literales del código**, no
    entrada de usuario. Se comprueba de todos modos, porque un identificador que
    llegara desde fuera aquí sería una inyección.
    """
    if not _es_identificador(tabla) or not _es_identificador(columna):
        raise ValueError(
            f"tabla o columna con forma inesperada: {tabla!r}, {columna!r}"
        )

    with _CERROJO:
        maximo = _maximo_en_pinot(pinot, tabla, columna)
        entregado = _ALTOS.get((tabla, columna), 0)
        # ⚠️ El `max` de los dos es el punto entero del módulo: cuando Pinot va
        # por detrás, `maximo` retrocede y sin esto volveríamos a repartir un id
        # ya usado.
        siguiente = max(maximo, entregado) + 1
        _ALTOS[(tabla, columna)] = siguiente
        return siguiente


def _maximo_en_pinot(pinot: _Consultable, tabla: str, columna: str) -> int:
    """El máximo ya visible. `0` si la tabla está vacía o no se puede leer.

    ⚠️ **Un fallo de lectura no interrumpe la escritura.** Si Pinot no responde,
    devolver `0` es seguro: la marca en memoria sigue mandando y la secuencia no
    retrocede. Propagar el error dejaría al sistema sin poder crear nada cada vez
    que la consulta analítica tiene un mal momento — y hoy los tiene.
    """
    try:
        filas = pinot.query(f"SELECT MAX({columna}) AS max_id FROM {tabla}")
    except Exception:
        return 0
    if not filas:
        return 0
    try:
        return int(filas[0].get("max_id") or 0)
    except (TypeError, ValueError):
        return 0


def _es_identificador(nombre: str) -> bool:
    return bool(nombre) and all(c.isalnum() or c == "_" for c in nombre)


def reiniciar_para_pruebas() -> None:
    """Olvida las marcas. **Solo para pruebas.**

    Sin esto, una prueba que siembra ids altos dejaría a la siguiente empezando
    por encima, y las que afirman «el primero es 1» fallarían según el orden.
    """
    with _CERROJO:
        _ALTOS.clear()
