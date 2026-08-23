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

El contador es **durable y compartido entre procesos**
-------------------------------------------------------
La marca en memoria sola no bastaría: con varios workers de gunicorn cada uno
llevaría su cuenta y volverían a colisionar. Por eso el reparto se hace sobre un
SQLite propio (`secuencias.sqlite3`) con un `UPDATE ... RETURNING` atómico: dos
procesos que pidan a la vez reciben números distintos porque SQLite serializa la
escritura.

⚠️ **No es la base de datos del dominio.** El proyecto guarda su dominio en
Pinot a propósito y aquí no se cambia nada de eso: este fichero contiene una
tabla de contadores, es infraestructura, y puede borrarse sin perder ningún dato
de negocio — al arrancar se resiembra desde el `MAX()` de Pinot.

⛔ **Si SQLite falla, no se interrumpe la escritura**: se cae al reparto en
memoria, que sigue siendo correcto dentro del proceso. Un contador indisponible
no puede dejar al sistema sin poder crear nada.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Protocol

from django.conf import settings


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
        piso = max(maximo, entregado)
        siguiente = _reservar_durable(tabla, columna, piso)
        if siguiente is None:
            siguiente = piso + 1
        _ALTOS[(tabla, columna)] = siguiente
        return siguiente


def _ruta_contador() -> Path:
    return Path(getattr(settings, "BASE_DIR", ".")) / "secuencias.sqlite3"


def _reservar_durable(tabla: str, columna: str, piso: int) -> int | None:
    """Reserva el siguiente número en el contador compartido, o `None` si falla.

    El `MAX(...)` deja el contador por encima de lo que Pinot ya tiene visible:
    si otro proceso reservó mientras tanto, gana el contador; si la tabla creció
    por fuera —una carga masiva, un seed—, gana Pinot.

    ⚠️ `RETURNING` hace que reservar y leer sean **la misma operación**. Leer y
    luego escribir dejaría exactamente la ventana que este módulo existe para
    cerrar, solo que entre procesos en vez de contra Pinot.
    """
    clave = f"{tabla}.{columna}"
    try:
        with sqlite3.connect(_ruta_contador(), timeout=5.0, isolation_level=None) as cx:
            cx.execute("PRAGMA journal_mode=WAL")
            cx.execute(
                "CREATE TABLE IF NOT EXISTS secuencias ("
                "clave TEXT PRIMARY KEY, valor INTEGER NOT NULL)"
            )
            fila = cx.execute(
                "INSERT INTO secuencias(clave, valor) VALUES(?, ?) "
                "ON CONFLICT(clave) DO UPDATE SET valor = MAX(valor, ?) + 1 "
                "RETURNING valor",
                (clave, piso + 1, piso),
            ).fetchone()
        return int(fila[0]) if fila else None
    except Exception:
        return None


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
        try:
            with sqlite3.connect(_ruta_contador(), timeout=5.0, isolation_level=None) as cx:
                cx.execute("DROP TABLE IF EXISTS secuencias")
        except Exception:
            pass
