"""Validacion de subidas por el contenido real, no por lo que el cliente declara.

Por que hace falta (PG-SEC-006). El endpoint de evidencia fotografica tomaba el
tipo de `archivo.content_type`, que es una cabecera **que envia el cliente**.
Validar con ella es preguntarle al fichero si es peligroso: un ejecutable
renombrado a `.jpg` y anunciado como `image/jpeg` pasaba sin mas.

Lo unico que no miente son los primeros bytes del fichero, que son los que este
modulo mira.

⚠️ **Alcance declarado.** Los bytes magicos identifican el **formato**; no
garantizan que el contenido sea inocuo. Un JPEG valido puede llevar carga en sus
metadatos. Aqui se cierra la confusion de tipo, que es lo que `PG-SEC-006`
declara; el analisis de contenido no esta en este plan.
"""

from __future__ import annotations

import puremagic

#: Formatos admitidos como evidencia. Lista blanca, no lista negra: enumerar lo
#: prohibido deja fuera todo lo que aun no se conoce.
#: `.jfif` esta en la lista porque `puremagic` devuelve esa extension para un
#: JPEG con cabecera JFIF, que es la forma mas comun. Omitirla rechazaria fotos
#: perfectamente validas — un falso positivo que el usuario legitimo sufre y el
#: atacante no.
EXTENSIONES_IMAGEN = frozenset({".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif"})

#: 10 MB, el mismo techo que ya aplica el almacenamiento de blobs.
TAMANO_MAXIMO = 10 * 1024 * 1024


class ArchivoInvalidoError(ValueError):
    """El fichero no es de un tipo admitido, o su nombre no es seguro."""


class ArchivoDemasiadoGrandeError(ValueError):
    """Excede el techo. Se traduce a 413, no a 400."""


def detectar_extension(contenido: bytes) -> str | None:
    """Extension segun los bytes iniciales, o `None` si no se reconoce."""
    if not contenido:
        return None
    try:
        coincidencias = puremagic.magic_string(contenido)
    except puremagic.PureError:
        return None
    return coincidencias[0].extension.lower() if coincidencias else None


def sanear_nombre(nombre: str) -> str:
    """Deja solo el nombre base, sin ruta.

    `../../etc/passwd` y `C:\\\\ruta\\\\fichero.jpg` se reducen al ultimo tramo. La
    travesia de rutas no depende de que el almacenamiento sea local: un nombre
    con separadores tambien confunde a quien despues construya una clave de blob
    concatenando.
    """
    limpio = nombre.replace(chr(92), "/").split("/")[-1]
    limpio = limpio.replace(chr(0), "").strip()
    return limpio or "sin-nombre"


def validar_imagen(contenido: bytes, *, nombre: str = "") -> str:
    """Comprueba que el contenido sea una imagen admitida y devuelve su extension.

    Lanza `ArchivoDemasiadoGrandeError` o `ArchivoInvalidoError`.

    ⚠️ El mensaje de error **no dice que tipo se detecto**. «Se esperaba una
    imagen» basta para el usuario legitimo; «se detecto un ejecutable PE» le
    confirma al atacante que la deteccion funciona y por donde va
    (`contracts/respuestas-seguridad.md` §C5).
    """
    if len(contenido) > TAMANO_MAXIMO:
        raise ArchivoDemasiadoGrandeError("El archivo excede el tamano permitido")

    extension = detectar_extension(contenido)
    if extension not in EXTENSIONES_IMAGEN:
        raise ArchivoInvalidoError("El archivo no es una imagen admitida")

    return extension
