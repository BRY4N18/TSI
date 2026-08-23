"""La cadena critica de emergencias, y que hacer con ella cuando el almacen cae.

**El problema que resuelve** (PG-SEC-003, `research.md` §R5.1). Validar una sesion
son dos pasos con propiedades muy distintas:

    claims = verify_access_token(token)              # criptografia pura, SIN E/S
    if not session_repo.is_active(session_id):       # requiere el almacen

El primero —firma RS256, expiracion, formato de claims— **sigue funcionando con
el almacen caido**. Solo el segundo depende de infraestructura. Plantear la
eleccion como «denegar todo o admitir todo» daba por perdida la autenticacion
entera cuando lo unico que se pierde es **la comprobacion de revocacion**.

| Situacion | Fuera de la cadena | En la cadena |
|---|---|---|
| Sesion revocada (`is_active` -> `False`) | 401 | **401 tambien** |
| No se puede comprobar (`is_active` lanza) | 401 | Degradar y continuar |

⚠️ **La distincion decisiva:** «revocada» y «no puedo comprobar si esta revocada»
son cosas distintas, y antes de esto el codigo las trataba igual porque ambas
terminaban en excepcion. Una sesion revocada se deniega **siempre**, cadena
critica incluida: no hay ningun argumento de seguridad fisica para dejar entrar a
quien se le retiro el acceso a proposito.

**Lo que se sacrifica, dicho explicitamente:** durante una caida del almacen, un
token robado y revocado hace minutos seguiria sirviendo **en estas nueve rutas**
hasta que expire. Es una ventana acotada por la vigencia del token. El Principio
IX de la constitucion es absoluto: una ambulancia que no se despacha porque Redis
no responde es peor.

**El criterio para entrar en esta lista** no es «pertenece al modulo de
emergencias» —eso serian 46 rutas— sino **«su denegacion durante una caida
retrasa la llegada de ayuda a una persona»**. Los catalogos, los informes y los
listados historicos quedan fuera: se consultan antes o despues, no durante.

Confirmada por el responsable el 2026-08-23. Cualquier cambio en esta lista
requiere justificacion explicita de Safety (Principio IX) y Reliability (II),
segun `constitution.md` §Additional Constraints.
"""

from __future__ import annotations

import re

#: Las nueve rutas, por etapa de la cadena. Se guardan como expresiones porque
#: los patrones de Django llevan parametros y aqui llega la ruta ya resuelta.
#:
#: Anadir una entrada **amplia la ventana de riesgo**: solo debe hacerse con la
#: justificacion que exige la constitucion.
_PATRONES = (
    # Registro — sin registro no hay despacho posible.
    r"^/api/v1/accidentes/?$",
    r"^/api/v1/accidentes/[^/]+/confirmar-reporte/?$",
    # Asignacion — es el acto de enviar ayuda.
    r"^/api/v1/accidentes/[^/]+/despacho/asignar-manual/?$",
    r"^/api/v1/accidentes/[^/]+/despacho/unidades-candidatas/?$",
    # Confirmacion — la unidad no puede aceptar el aviso.
    r"^/api/v1/mi-despacho/[^/]+/confirmar/?$",
    r"^/api/v1/mi-despacho/[^/]+/rechazar/?$",
    # Seguimiento — se pierde de vista una unidad en ruta.
    r"^/api/v1/mi-seguimiento/posicion/?$",
    r"^/api/v1/mi-seguimiento/despachos/[^/]+/llegada/?$",
    r"^/api/v1/seguimiento/stream/?$",
)

_COMPILADOS = tuple(re.compile(p) for p in _PATRONES)

#: Numero de rutas confirmado. Una prueba lo verifica: ampliar la lista sin
#: revisar este numero es como se ensancha una excepcion de seguridad sin que
#: nadie lo note.
TOTAL_RUTAS = len(_PATRONES)


def es_cadena_critica(ruta: str) -> bool:
    """¿Denegar esta ruta durante una caida retrasaria la ayuda a una persona?"""
    if not ruta:
        return False
    return any(p.match(ruta) for p in _COMPILADOS)
