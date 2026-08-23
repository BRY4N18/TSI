"""PG-SEC-006 — un ejecutable renombrado a `.jpg` no entra.

El sistema acepta hasta 50 MB por petición multipart (evidencia fotográfica de
accidentes, adjuntos de tickets). Antes de esta suite, el tipo se tomaba de
`archivo.content_type` — una cabecera **que envía el cliente**. Validar con ella
equivale a preguntarle al fichero si es peligroso.

Lo único que no miente son los primeros bytes.
"""

from __future__ import annotations

import pytest

from core.seguridad.validacion_archivos import (
    TAMANO_MAXIMO,
    ArchivoDemasiadoGrandeError,
    ArchivoInvalidoError,
    detectar_extension,
    sanear_nombre,
    validar_imagen,
)

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

#: Cabeceras reales de cada formato. Un JPEG mínimo válido empieza por FF D8 FF.
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
GIF = b"GIF89a" + b"\x00" * 64

#: Lo que un atacante subiría. `MZ` es la cabecera de un ejecutable de Windows;
#: `\x7fELF` la de uno de Linux.
EJECUTABLE_WINDOWS = b"MZ\x90\x00\x03" + b"\x00" * 64
EJECUTABLE_LINUX = b"\x7fELF\x02\x01\x01" + b"\x00" * 64
SVG_CON_SCRIPT = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
HTML = b"<!DOCTYPE html><html><body>hola</body></html>"


# --- Lo legítimo pasa ---------------------------------------------------------


@pytest.mark.parametrize("contenido,esperada", [(JPEG, ".jfif"), (PNG, ".png"), (GIF, ".gif")])
def test_una_imagen_real_se_acepta(contenido, esperada):
    """Control negativo: sin esto, una validación que rechace TODO pasaría.

    Es la trampa que ya apareció cuatro veces en esta jornada — una suite verde
    que no distingue «funciona» de «nada funciona».
    """
    assert validar_imagen(contenido) == esperada


# --- Lo peligroso no ----------------------------------------------------------


@pytest.mark.parametrize(
    "contenido,descripcion",
    [
        (EJECUTABLE_WINDOWS, "ejecutable de Windows"),
        (EJECUTABLE_LINUX, "ejecutable de Linux"),
        (SVG_CON_SCRIPT, "SVG con script"),
        (HTML, "HTML"),
        (b"", "fichero vacío"),
        (b"no soy nada", "bytes sin formato reconocible"),
    ],
)
def test_lo_que_no_es_imagen_se_rechaza(contenido, descripcion):
    with pytest.raises(ArchivoInvalidoError):
        validar_imagen(contenido)


def test_un_ejecutable_renombrado_a_jpg_no_engana():
    """El caso que da nombre a la historia.

    El nombre y el `Content-Type` dicen «imagen»; los bytes dicen «ejecutable».
    Solo los bytes cuentan.
    """
    with pytest.raises(ArchivoInvalidoError):
        validar_imagen(EJECUTABLE_WINDOWS, nombre="foto-vacaciones.jpg")


def test_un_archivo_demasiado_grande_se_rechaza_por_tamano():
    """413, no 400: el fichero puede ser válido y aun así no caber.

    Distinguirlos importa para el cliente legítimo, que con un 400 buscaría el
    error en el formato.
    """
    with pytest.raises(ArchivoDemasiadoGrandeError):
        validar_imagen(JPEG + b"\x00" * TAMANO_MAXIMO)


def test_el_tamano_se_comprueba_antes_que_el_formato():
    """Un fichero enorme no debe recorrerse entero para descubrir que no cabe."""
    enorme_invalido = EJECUTABLE_WINDOWS + b"\x00" * TAMANO_MAXIMO

    with pytest.raises(ArchivoDemasiadoGrandeError):
        validar_imagen(enorme_invalido)


# --- El nombre no escapa del directorio ---------------------------------------


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("../../etc/passwd", "passwd"),
        ("..\\..\\windows\\system32\\cmd.exe", "cmd.exe"),
        ("/absoluta/foto.jpg", "foto.jpg"),
        ("foto.jpg", "foto.jpg"),
        ("", "sin-nombre"),
        ("   ", "sin-nombre"),
    ],
)
def test_el_nombre_se_sanea(entrada, esperado):
    """La travesía de rutas no depende de que el almacén sea local.

    Un nombre con separadores también confunde a quien después construya una
    clave de blob concatenando cadenas.
    """
    assert sanear_nombre(entrada) == esperado


# --- El mensaje no delata -----------------------------------------------------


def test_el_error_no_revela_que_tipo_se_detecto():
    """Contrato C5.

    «Se esperaba una imagen» basta para el usuario legítimo. «Se detectó un
    ejecutable PE» le confirma al atacante que la detección funciona y por dónde
    va — le ahorra el trabajo de averiguarlo probando.
    """
    with pytest.raises(ArchivoInvalidoError) as exc:
        validar_imagen(EJECUTABLE_WINDOWS)

    mensaje = str(exc.value).lower()
    for delator in ("ejecutable", "elf", "exe", "svg", "html", "script", "pe32"):
        assert delator not in mensaje, f"El mensaje revela «{delator}»: {mensaje}"


# --- La detección funciona, no solo rechaza -----------------------------------


def test_la_deteccion_distingue_formatos_de_verdad():
    """Si `detectar_extension` devolviera siempre `None`, todo lo anterior
    pasaría igual **rechazándolo todo**. Esta prueba lo impide.
    """
    assert detectar_extension(JPEG) == ".jfif"  # JPEG con cabecera JFIF
    assert detectar_extension(PNG) == ".png"
    assert detectar_extension(EJECUTABLE_WINDOWS) not in (".jpg", ".png", None)
