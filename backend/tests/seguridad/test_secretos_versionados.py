"""PG-CFG-005 — ningún secreto versionado.

**La regla figuraba como cubierta y nunca se había ejecutado.** `gitleaks`
estaba en el workflow de CI desde el principio, así que la casilla estaba
marcada; al correrlo por primera vez sobre el historial completo el 2026-08-23
salieron 9 hallazgos. Los 9 resultaron ser falsos positivos —claves de
diccionario, fixtures de prueba y la credencial de ClickHouse en localhost— pero
eso no se sabía hasta mirarlos.

Lo que estas pruebas vigilan no es el escaneo en sí (eso lo hace CI, y la de
`integration` lo repite aquí) sino **la forma de la excepción**: que la allowlist
siga nombrando ficheros concretos y no se convierta en un patrón amplio que apaga
la comprobación sin que nadie lo note.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from django.conf import settings

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

RAIZ = Path(settings.BASE_DIR).parent
CONFIG = RAIZ / ".gitleaks.toml"
WORKFLOW = RAIZ / ".github" / "workflows" / "ci.yml"


def _texto() -> str:
    return CONFIG.read_text(encoding="utf-8")


def test_la_configuracion_de_gitleaks_existe():
    """Sin ella, CI usa la config por defecto y el paso queda en rojo siempre."""
    assert CONFIG.exists(), (
        ".gitleaks.toml no existe: los 9 falsos positivos ya revisados volverían "
        "a dejar el escaneo en rojo permanente."
    )


def test_ci_le_pasa_la_configuracion_al_escaneo():
    """La acción no la toma sola: hay que nombrarla en `GITLEAKS_CONFIG`.

    Es el fallo silencioso de este arreglo: el fichero existe, la excepción está
    razonada, y CI la ignora porque nadie se lo dijo.
    """
    flujo = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    pasos = [
        p
        for trabajo in flujo["jobs"].values()
        for p in trabajo.get("steps", [])
        if "gitleaks" in str(p.get("uses", ""))
    ]
    assert pasos, "El workflow ya no ejecuta gitleaks (PG-CFG-005)."

    for paso in pasos:
        assert "GITLEAKS_CONFIG" in (paso.get("env") or {}), (
            "El paso de gitleaks no recibe GITLEAKS_CONFIG: usará la config por "
            "defecto y fallará por los falsos positivos ya revisados."
        )


def test_la_lista_de_excepciones_nombra_ficheros_y_no_carpetas():
    """Una excepción por carpeta apaga la comprobación para todo lo que entre después.

    Es la degradación natural de cualquier allowlist: alguien amplía el patrón
    para que deje de molestar y, meses después, un secreto real cae dentro. Cada
    entrada debe terminar en un fichero concreto.
    """
    sospechosas = []
    for linea in _texto().splitlines():
        limpia = linea.strip()
        if not limpia.startswith("'''") or "=" in limpia:
            continue
        ruta = limpia.strip("',").strip("'''").strip(",").strip("'")
        if not ruta or ruta.startswith("("):
            continue
        # Una ruta a fichero termina en una extensión escapada: `\.py`, `\.md`…
        if "\\." not in ruta.rsplit("/", 1)[-1]:
            sospechosas.append(ruta)

    assert not sospechosas, (
        "Excepciones que no apuntan a un fichero concreto:\n  "
        + "\n  ".join(sospechosas)
        + "\n\n  Un patrón de carpeta deja pasar todo lo que se añada dentro."
    )


def test_cada_excepcion_esta_justificada():
    """Una ruta sin motivo escrito no se puede revisar dentro de seis meses.

    Se comprueba que haya un comentario en las líneas inmediatamente anteriores:
    quien añada la siguiente excepción tiene que explicar por qué no es un
    secreto, que es justo el análisis que faltaba cuando la regla estaba
    «cubierta» sin haberse ejecutado nunca.
    """
    lineas = _texto().splitlines()
    sin_motivo = []
    for i, linea in enumerate(lineas):
        limpia = linea.strip()
        if not (limpia.startswith("'''") and limpia.endswith(("''',", "'''"))):
            continue
        anteriores = [l.strip() for l in lineas[max(0, i - 6) : i]]
        if not any(l.startswith("#") for l in anteriores):
            sin_motivo.append(limpia)

    assert not sin_motivo, (
        "Excepciones sin comentario que explique por qué no son un secreto:\n  "
        + "\n  ".join(sin_motivo)
    )


def test_la_clave_privada_jwt_no_esta_versionada():
    """Con ella cualquiera firma tokens de sesión válidos.

    Se comprueba contra el índice de git y no contra el disco: el fichero
    **existe** en local —hace falta para arrancar— y lo que importa es que no
    esté seguido.
    """
    resultado = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "backend/config/keys/jwt_private.pem"],
        cwd=RAIZ,
        capture_output=True,
    )
    assert resultado.returncode != 0, (
        "jwt_private.pem está versionado: quien tenga el repositorio puede "
        "firmar tokens de sesión válidos."
    )


@pytest.mark.integration
def test_gitleaks_no_encuentra_secretos_en_el_historial():
    """El escaneo de verdad, sobre los 30 commits.

    Vive bajo `integration` porque necesita Docker. La suite unitaria comprueba
    la *forma* de la excepción; esta comprueba el *hecho*.
    """
    if not shutil.which("docker"):
        pytest.skip("Docker no disponible")

    # Sin el prefijo `//` que exige MSYS: subprocess no pasa por el shell, así
    # que no hay conversión de rutas que esquivar.
    ruta = str(RAIZ).replace("\\", "/")
    resultado = subprocess.run(
        [
            "docker", "run", "--rm", "-v", f"{ruta}:/repo",
            "zricethezav/gitleaks:latest", "detect", "--source=/repo",
            "--config=/repo/.gitleaks.toml", "--no-banner", "--redact",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert resultado.returncode == 0, (
        "gitleaks encontró secretos en el historial:\n" + resultado.stdout[-3000:]
    )
