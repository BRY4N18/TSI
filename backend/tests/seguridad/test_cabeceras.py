"""PG-SEC-008 — cabeceras y cookies de seguridad, en Django y en nginx.

Dos servidores responden al navegador y **ninguno de los dos basta solo**:
Django sirve `/api/`, nginx sirve la aplicación Angular y los estáticos. Una
cabecera puesta solo en uno deja media superficie descubierta, y es el error
natural porque al probar la API se ve todo correcto.

El caso que más se olvida son las respuestas de **error**: nginx omite
`add_header` en los 4xx/5xx salvo que se marque `always`, y son precisamente las
que un atacante provoca a propósito.

Contrato: `contracts/respuestas-seguridad.md` §C6.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.partners.domain_constants import ROL_ADMINISTRADOR
from core.jwt_utils import create_access_token

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

NGINX_CONF = Path(settings.BASE_DIR).parent / "frontend" / "nginx.conf"

#: Cabeceras que no dependen de HTTPS y por tanto deben estar **siempre**.
SIEMPRE = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}


def _cliente() -> APIClient:
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=3, roles=[ROL_ADMINISTRADOR], session_id=1)}"
        )
    )
    return api


# --- Lado Django --------------------------------------------------------------


@pytest.mark.parametrize("cabecera,valor", sorted(SIEMPRE.items()))
def test_django_envia_las_cabeceras_que_no_dependen_de_https(cabecera, valor):
    respuesta = _cliente().get("/api/v1/usuarios")
    assert respuesta.headers.get(cabecera) == valor, (
        f"Falta {cabecera}: {dict(respuesta.headers)}"
    )


@pytest.mark.parametrize("cabecera,valor", sorted(SIEMPRE.items()))
def test_django_las_envia_tambien_en_las_respuestas_de_error(cabecera, valor):
    """El caso que se escapa.

    Un `404` o un `401` son respuestas como cualquier otra y las mismas
    protecciones aplican. Son además las que un atacante ve más a menudo.
    """
    respuesta = _cliente().get("/api/v1/usuarios/999999")
    assert respuesta.status_code >= 400
    assert respuesta.headers.get(cabecera) == valor


def test_django_declara_las_protecciones_que_exigen_https():
    """Se comprueba sobre el texto de `settings.py`, no importando con otro entorno.

    El módulo ya está cargado en el proceso de pytest y reimportarlo no reevalúa
    el condicional; la alternativa —un subproceso por aserción— cuesta segundos y
    demuestra lo mismo.
    """
    fuente = (Path(settings.BASE_DIR) / "config" / "settings.py").read_text(encoding="utf-8")
    bloque = fuente.split("if not _ES_LOCAL:", 1)
    assert len(bloque) == 2, "Falta el bloque de seguridad condicional."

    for ajuste in (
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SESSION_COOKIE_HTTPONLY",
        "SECURE_HSTS_SECONDS",
    ):
        assert ajuste in bloque[1], f"{ajuste} no se activa fuera de local."


# --- Lado nginx ---------------------------------------------------------------


@pytest.mark.parametrize("cabecera", sorted(SIEMPRE))
def test_nginx_declara_las_mismas_cabeceras(cabecera):
    """nginx no puede contradecir ni omitir lo que Django declara."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    assert re.search(rf"add_header\s+{re.escape(cabecera)}\b", conf, re.I), (
        f"{NGINX_CONF.name} no declara {cabecera}."
    )


@pytest.mark.parametrize("cabecera", sorted(SIEMPRE) + ["Content-Security-Policy"])
def test_nginx_usa_always_para_no_perderlas_en_los_errores(cabecera):
    """Sin `always`, nginx omite la cabecera en 4xx y 5xx.

    Es un fallo silencioso perfecto: el navegador recibe la cabecera en el camino
    feliz, una revisión manual la ve, y desaparece exactamente en las respuestas
    que importan.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    linea = next(
        (l for l in conf.splitlines() if re.search(rf"add_header\s+{re.escape(cabecera)}\b", l, re.I)),
        None,
    )
    assert linea, f"{cabecera} no está declarada en nginx.conf"
    assert linea.rstrip().rstrip(";").endswith("always"), (
        f"{cabecera} sin `always`: se perderá en las respuestas de error.\n  {linea.strip()}"
    )


def test_la_csp_no_admite_scripts_en_linea():
    """`unsafe-inline` en `script-src` anula buena parte de la CSP.

    Se admite en `style-src` porque Angular inyecta estilos por componente; en
    scripts no hay concesión que valga, que es donde la directiva protege de
    verdad.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    csp = next(l for l in conf.splitlines() if "Content-Security-Policy" in l)

    script_src = re.search(r"script-src([^;]*)", csp)
    assert script_src, "La CSP no declara script-src"
    assert "unsafe-inline" not in script_src.group(1), (
        f"script-src admite unsafe-inline: {script_src.group(0)}"
    )
    assert "unsafe-eval" not in script_src.group(1), script_src.group(0)


def test_la_csp_impide_que_la_aplicacion_se_incruste():
    """`frame-ancestors 'none'` es la versión moderna de X-Frame-Options.

    Se declaran las dos porque los navegadores antiguos ignoran la primera y los
    modernos dan preferencia a la CSP.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    csp = next(l for l in conf.splitlines() if "Content-Security-Policy" in l)
    assert "frame-ancestors 'none'" in csp, csp
