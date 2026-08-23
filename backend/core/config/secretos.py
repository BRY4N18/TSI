"""Registro central de secretos y guardas de configuración de despliegue.

Implementa `PG-CFG-001` y `PG-CFG-002` de `specs/Global/PlanPruebas/spec.md`.

El problema que resuelve: cada secreto de `config/settings.py` tiene un valor por
defecto cómodo para desarrollo. Si un despliegue olvida exportar la variable, el
sistema arranca igual — con la clave de firma publicada en el repositorio o con la
contraseña de ClickHouse que aparece en el `docker-compose`. No falla nada; queda
abierto en silencio, que es la peor forma de fallar.

La guarda ya existía para los secretos de la demo interactiva
(`apps/ventas_crm/demo_tokens.py`). Aquí se generaliza: un único registro que
enumera *todos* los valores por defecto inseguros, revisado en el arranque.

Nota sobre `DJANGO_DEBUG`: se lee de `os.environ` y no de `settings.DEBUG` porque
pytest-django fuerza `settings.DEBUG = False` durante la suite, lo que activaría la
guarda en cada test aunque el entorno sea de desarrollo. Es el mismo criterio que
usa `demo_tokens.py`.
"""

from __future__ import annotations

import os

from django.core.exceptions import ImproperlyConfigured

# Valor por defecto de cada secreto que solo es aceptable en desarrollo local.
# Añadir aquí toda variable sensible nueva: `test_configuracion_segura.py`
# verifica que el registro cubra las que declara `settings.py`.
DEFAULTS_INSEGUROS: dict[str, str] = {
    "DJANGO_SECRET_KEY": "django-insecure-dev-only-change-in-production",
    "CLICKHOUSE_PASSWORD": "tactico",
    "DEMO_GRANT_SECRET": "dev-demo-grant-secret-min-32-chars!!",
    "DEMO_SESSION_SECRET": "dev-demo-session-secret-min-32-chars!",
}

# Nombre de la variable de settings que corresponde a cada variable de entorno,
# cuando no coinciden.
_ALIAS_SETTINGS: dict[str, str] = {
    "DJANGO_SECRET_KEY": "SECRET_KEY",
}


def es_entorno_local() -> bool:
    """True cuando el proceso corre en desarrollo local.

    Se apoya en `DJANGO_DEBUG` para no introducir una variable nueva que los
    despliegues actuales no exportan todavía.
    """
    return os.environ.get("DJANGO_DEBUG", "true").lower() == "true"


def nombre_en_settings(variable: str) -> str:
    return _ALIAS_SETTINGS.get(variable, variable)


def verifica_secretos(valores: dict[str, object]) -> None:
    """Aborta el arranque si algún secreto conserva su valor de desarrollo.

    `valores` mapea nombre de variable de entorno → valor efectivo ya resuelto por
    `settings.py`. Se recorre el registro completo y se acumulan todos los fallos
    en un solo mensaje: quien despliega necesita la lista entera, no el primero de
    la lista una vez por intento.
    """
    if es_entorno_local():
        return

    inseguros = [
        variable
        for variable, default in DEFAULTS_INSEGUROS.items()
        if variable in valores and str(valores[variable]) == default
    ]
    if not inseguros:
        return

    detalle = ", ".join(sorted(inseguros))
    raise ImproperlyConfigured(
        f"Secretos con el valor por defecto de desarrollo y DJANGO_DEBUG=false: {detalle}. "
        "Configúralos explícitamente en el entorno antes de arrancar "
        "(PG-CFG-002 del plan global de pruebas)."
    )


def verifica_debug(debug: bool) -> None:
    """`DEBUG` activo fuera de local expone el traceback completo al navegador."""
    entorno = os.environ.get("TSI_ENV", "local").lower()
    if debug and entorno not in ("local", "e2e", "test"):
        raise ImproperlyConfigured(
            f"DJANGO_DEBUG=true con TSI_ENV={entorno}. DEBUG revela settings, rutas y "
            "fragmentos de entorno en cada excepción; solo se admite en local "
            "(PG-CFG-001 del plan global de pruebas)."
        )


def verifica_hosts(allowed_hosts: list[str]) -> None:
    """Fuera de local, `ALLOWED_HOSTS` no puede quedar abierto ni apuntar a localhost."""
    if es_entorno_local():
        return

    abiertos = [h for h in allowed_hosts if h.strip() in ("*", "localhost", "127.0.0.1")]
    if abiertos:
        raise ImproperlyConfigured(
            f"ALLOWED_HOSTS contiene {abiertos} con DJANGO_DEBUG=false. Declara los "
            "dominios reales del despliegue (PG-CFG-003 del plan global de pruebas)."
        )
