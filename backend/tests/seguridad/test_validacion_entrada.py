"""PG-API-004 — ningún cuerpo malformado debe reventar un endpoint.

**Por qué el `500` es el objetivo y no el `400`.** Un `400` es una respuesta:
pasa por el manejador central, lleva el envelope, y no cuenta nada de más. Un
`500` es **el único camino que no pasa por ahí** —`drf_exception_handler`
devuelve `None` para las excepciones ajenas a DRF— y por tanto la única respuesta
del sistema sobre la que no hay ninguna garantía de qué muestra.

Ya apareció una vez: `POST /usuarios` con el cuerpo incompleto lanzaba
`KeyError` → 500 (`changelog.md` C7). El patrón —`request.data` en crudo hacia un
servicio que indexa por clave— puede repetirse, y esta suite lo busca en los
**105 endpoints de escritura** en vez de esperar a que alguien lo encuentre.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.partners.domain_constants import ROL_ADMINISTRADOR
from core.jwt_utils import create_access_token
from core.seguridad.inventario_rutas import inventariar

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

USUARIO = 3
SESION = 1

#: Cuerpos que un cliente descuidado —o un atacante— envía. Ninguno debe
#: producir un `500`; todos deben rechazarse con 4xx.
CUERPOS = {
    "vacio": {},
    "campo_desconocido": {"campo_que_no_existe": "x"},
    "tipos_cambiados": {"idusuario": "no-soy-un-numero", "activo": "quizas"},
    "cadena_larga": {"nombres": "x" * 10_000},
    "nulos": {"nombres": None, "gmail": None},
    "unicode": {"nombres": "🚑💥", "gmail": "ñ@ü.com"},
    "fecha_imposible": {"fechanacimiento": "2026-02-30"},
    "fecha_futura": {"fechanacimiento": "2099-01-01"},
    "numero_negativo": {"numvehiculos": -5, "numheridos": -1},
    "anidado_inesperado": {"nombres": {"a": [1, 2, 3]}},
}


def _cliente() -> APIClient:
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=USUARIO, roles=[ROL_ADMINISTRADOR], session_id=SESION)}"
        )
    )
    return api


def _endpoints_de_escritura():
    """Sin parámetros de ruta: construir ids válidos para 105 endpoints daría
    404 la mayoría de las veces y el recorrido no probaría la validación."""
    return [
        r
        for r in inventariar()
        if "post" in r.metodos and not r.parametros
    ]


RUTAS = _endpoints_de_escritura()


@pytest.mark.parametrize("nombre,cuerpo", sorted(CUERPOS.items()))
def test_ningun_cuerpo_malformado_produce_un_500(nombre, cuerpo):
    """El aserto de la regla, sobre todos los endpoints a la vez.

    Se agrupa por cuerpo y no por endpoint para que el fallo diga «esta forma de
    entrada rompe estos endpoints», que es la información accionable: el arreglo
    suele ser el mismo para todos.
    """
    cliente = _cliente()
    rotos = []

    for ruta in RUTAS:
        respuesta = cliente.post(f"/{ruta.patron}", cuerpo, format="json")
        if respuesta.status_code >= 500:
            rotos.append(f"{ruta.patron} -> {respuesta.status_code}")

    assert not rotos, (
        f"Cuerpo «{nombre}» produce 5xx en {len(rotos)} endpoints:\n  "
        + "\n  ".join(rotos[:12])
        + "\n\n  El 500 es el único camino que no pasa por el manejador central, "
        "y por tanto el único sin garantía de qué muestra."
    )


def test_un_cuerpo_que_no_es_json_no_revienta():
    """Texto plano donde se espera JSON.

    El parser falla antes de llegar a la vista, así que el manejo depende de DRF
    y no del código propio — conviene comprobarlo en vez de suponerlo.
    """
    cliente = _cliente()
    rotos = []

    for ruta in RUTAS:
        respuesta = cliente.post(
            f"/{ruta.patron}", data="esto no es json", content_type="application/json"
        )
        if respuesta.status_code >= 500:
            rotos.append(f"{ruta.patron} -> {respuesta.status_code}")

    assert not rotos, "JSON malformado produce 5xx:\n  " + "\n  ".join(rotos[:12])


def test_un_array_donde_se_espera_un_objeto_no_revienta():
    """`[]` en vez de `{}`.

    Un servicio que hace `data.get(...)` sobre una lista lanza `AttributeError`,
    que no es de DRF y por tanto termina en 500.
    """
    cliente = _cliente()
    rotos = []

    for ruta in RUTAS:
        respuesta = cliente.post(f"/{ruta.patron}", [1, 2, 3], format="json")
        if respuesta.status_code >= 500:
            rotos.append(f"{ruta.patron} -> {respuesta.status_code}")

    assert not rotos, (
        "Un array donde se espera un objeto produce 5xx:\n  " + "\n  ".join(rotos[:12])
    )


def test_hay_endpoints_de_escritura_que_recorrer():
    """Control negativo: sin esto, la suite pasaría recorriendo una lista vacía."""
    assert len(RUTAS) >= 30, (
        f"Solo {len(RUTAS)} endpoints de escritura sin parámetros. El sistema "
        "tiene 105 de escritura en total: probablemente falló el filtrado."
    )
