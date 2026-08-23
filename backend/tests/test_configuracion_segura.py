"""Guardas de configuración de despliegue — PG-CFG-001/002/003.

Cubre el hueco que dejaba `settings.py`: cada secreto tenía un valor por defecto
cómodo para desarrollo y ninguna comprobación impedía que llegara a producción.
Un despliegue que olvidara exportar `DJANGO_SECRET_KEY` arrancaba firmando
sesiones con una clave publicada en el repositorio, sin un solo aviso.

Las pruebas parametrizadas sobre `DEFAULTS_INSEGUROS` son deliberadas: añadir un
secreto al registro lo incorpora automáticamente a la suite, y `test_registro_cubre_settings`
falla si alguien añade un default inseguro a `settings.py` sin registrarlo.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

from core.config import secretos

pytestmark = pytest.mark.unit

SETTINGS_PY = Path(__file__).resolve().parent.parent / "config" / "settings.py"


def _entorno_produccion(**extra: str) -> mock._patch_dict:
    return mock.patch.dict(
        os.environ, {"DJANGO_DEBUG": "false", "TSI_ENV": "production", **extra}
    )


# --- PG-CFG-002: ningún secreto conserva su valor de desarrollo ---


@pytest.mark.parametrize("variable", sorted(secretos.DEFAULTS_INSEGUROS))
def test_secreto_con_default_de_desarrollo_aborta_en_produccion(variable: str) -> None:
    valores = {variable: secretos.DEFAULTS_INSEGUROS[variable]}

    with _entorno_produccion():
        with pytest.raises(ImproperlyConfigured) as exc:
            secretos.verifica_secretos(valores)

    assert variable in str(exc.value)


@pytest.mark.parametrize("variable", sorted(secretos.DEFAULTS_INSEGUROS))
def test_secreto_configurado_explicitamente_pasa(variable: str) -> None:
    with _entorno_produccion():
        secretos.verifica_secretos({variable: "valor-real-del-despliegue-32-chars"})


def test_el_mensaje_enumera_todos_los_secretos_inseguros_de_una_vez() -> None:
    """Quien despliega necesita la lista entera, no descubrirlos de uno en uno."""
    with _entorno_produccion():
        with pytest.raises(ImproperlyConfigured) as exc:
            secretos.verifica_secretos(dict(secretos.DEFAULTS_INSEGUROS))

    mensaje = str(exc.value)
    for variable in secretos.DEFAULTS_INSEGUROS:
        assert variable in mensaje


def test_en_local_los_defaults_siguen_siendo_validos() -> None:
    """El desarrollo no puede volverse hostil: sin .env el sistema arranca igual."""
    with mock.patch.dict(os.environ, {"DJANGO_DEBUG": "true"}):
        secretos.verifica_secretos(dict(secretos.DEFAULTS_INSEGUROS))


def test_registro_cubre_todos_los_defaults_sensibles_de_settings() -> None:
    """Un secreto nuevo en settings.py sin registrar hace fallar esta prueba.

    Sin esto el registro envejece: se añade una credencial con default, nadie la
    da de alta, y la guarda pasa a dar una falsa sensación de cobertura completa.
    """
    fuente = SETTINGS_PY.read_text(encoding="utf-8")
    patron = re.compile(
        r'os\.environ\.get\(\s*"([A-Z_]*(?:SECRET|PASSWORD|KEY|TOKEN))"\s*,\s*"([^"]+)"',
        re.MULTILINE,
    )
    con_default = {
        variable: default
        for variable, default in patron.findall(fuente)
        if default.strip()  # un default vacío no es una credencial utilizable
    }

    sin_registrar = set(con_default) - set(secretos.DEFAULTS_INSEGUROS)
    assert not sin_registrar, (
        f"Secretos con valor por defecto no registrados en DEFAULTS_INSEGUROS: "
        f"{sorted(sin_registrar)}. Añádelos a core/config/secretos.py (PG-CFG-002)."
    )


# --- PG-CFG-001: DEBUG jamás activo fuera de local ---


def test_debug_activo_en_produccion_aborta() -> None:
    with mock.patch.dict(os.environ, {"TSI_ENV": "production"}):
        with pytest.raises(ImproperlyConfigured, match="DJANGO_DEBUG"):
            secretos.verifica_debug(True)


@pytest.mark.parametrize("entorno", ["local", "e2e", "test"])
def test_debug_activo_es_valido_en_entornos_de_desarrollo(entorno: str) -> None:
    with mock.patch.dict(os.environ, {"TSI_ENV": entorno}):
        secretos.verifica_debug(True)


def test_debug_apagado_es_valido_en_cualquier_entorno() -> None:
    with mock.patch.dict(os.environ, {"TSI_ENV": "production"}):
        secretos.verifica_debug(False)


# --- PG-CFG-003: ALLOWED_HOSTS cerrado por defecto ---


@pytest.mark.parametrize("host", ["*", "localhost", "127.0.0.1"])
def test_allowed_hosts_abierto_aborta_en_produccion(host: str) -> None:
    with _entorno_produccion():
        with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
            secretos.verifica_hosts([host])


def test_allowed_hosts_con_dominios_reales_pasa() -> None:
    with _entorno_produccion():
        secretos.verifica_hosts(["api.traficoseguro.com", "www.traficoseguro.com"])


# --- PG-SEC-008: cabeceras y cookies de seguridad ---


def test_cabeceras_de_seguridad_activas_en_todo_entorno() -> None:
    """Estas tres no dependen de HTTPS, así que no hay excusa para desactivarlas."""
    from django.conf import settings

    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.X_FRAME_OPTIONS == "DENY"
    assert settings.SECURE_REFERRER_POLICY == "same-origin"


def test_settings_declara_las_protecciones_que_exigen_https() -> None:
    """El bloque condicional de producción existe y activa lo que debe.

    Se comprueba sobre el texto de `settings.py` en vez de importarlo con
    DJANGO_DEBUG=false: el módulo ya está cargado en el proceso de pytest y
    reimportarlo con otro entorno no reevalúa el condicional. La alternativa
    (un subproceso por aserción) cuesta segundos y prueba lo mismo.
    """
    fuente = SETTINGS_PY.read_text(encoding="utf-8")
    bloque = fuente.split("if not _ES_LOCAL:", 1)
    assert len(bloque) == 2, "Falta el bloque de seguridad condicional (PG-SEC-008)."

    produccion = bloque[1]
    for ajuste in (
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SESSION_COOKIE_HTTPONLY",
        "SECURE_HSTS_SECONDS",
    ):
        assert ajuste in produccion, f"{ajuste} no se activa fuera de local (PG-SEC-008)."
