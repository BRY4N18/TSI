"""PG-SEC-010 — la demo interactiva no es una puerta trasera.

TSI emite **dos familias de credenciales que no se parecen en nada**:

| | JWT de usuario | Token de demo |
|---|---|---|
| Algoritmo | RS256 (par de claves) | HS256 (secreto compartido) |
| Claims | `sub`, `roles`, `session_id` | `typ`, `idprospecto`, `jti` |
| Quién lo obtiene | Un usuario dado de alta | **Cualquier visitante** que deje sus datos |

La última fila es la que importa. Un token de demo lo consigue quien rellena un
formulario en la web, sin que nadie apruebe nada. Si los endpoints de negocio lo
aceptaran, el alta de prospectos sería un registro abierto al sistema entero.

Que ambos sean «un JWT» es precisamente lo peligroso: se parecen lo bastante como
para que alguien los trate igual al añadir un endpoint.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.ventas_crm.demo_tokens import issue_demo_session_token

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

#: Endpoints de negocio de distintos módulos. Se eligen variados a propósito: el
#: aislamiento tiene que valer en todos, no solo donde alguien se acordó.
ENDPOINTS_DE_NEGOCIO = [
    "/api/v1/usuarios",
    "/api/v1/accidentes",
    "/api/v1/partners",
    "/api/v1/soporte/tickets",
    "/api/v1/informes/emergencias/casos",
]


@pytest.fixture
def token_demo() -> str:
    """Token de demo **válido**: bien firmado y sin expirar.

    Que sea válido es el punto. Uno caducado lo rechazaría cualquier cosa; lo que
    se comprueba es que un token legítimo **de su clase** no sirva fuera de ella.
    """
    return issue_demo_session_token(
        idprospecto=1, demo_expiracion_iso="2099-01-01T00:00:00+00:00"
    )


@pytest.mark.parametrize("ruta", ENDPOINTS_DE_NEGOCIO)
def test_un_token_de_demo_no_abre_ningun_endpoint_de_negocio(token_demo, ruta):
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token_demo}")

    respuesta = api.get(ruta)

    assert respuesta.status_code == 401, (
        f"{ruta} devolvió {respuesta.status_code} con un token de demo. Ese token "
        "lo obtiene cualquier visitante que rellene el formulario de prospecto "
        "(PG-SEC-010)."
    )


def test_el_token_de_demo_no_lleva_rol_ni_sesion(token_demo):
    """Aislamiento por construcción, no solo por rechazo.

    Aunque un endpoint lo aceptara por error, el token no contiene nada con lo
    que autorizar: sin `roles` no hay permiso que conceder y sin `session_id` no
    hay sesión que validar. Es la segunda barrera, y la que sobrevive a un
    descuido en la primera.
    """
    import jwt

    claims = jwt.decode(token_demo, options={"verify_signature": False})

    assert claims["typ"] == "demo_session"
    assert "roles" not in claims
    assert "session_id" not in claims
    assert "sub" not in claims


def test_las_dos_familias_usan_algoritmos_distintos(token_demo):
    """RS256 frente a HS256.

    No es un detalle de implementación: significa que el secreto de la demo **no
    puede** firmar un token de usuario válido. Aunque se filtrara, no serviría
    para entrar al sistema principal.
    """
    import jwt

    from core.jwt_utils import create_access_token

    assert jwt.get_unverified_header(token_demo)["alg"] == "HS256"

    token_usuario = create_access_token(user_id=3, roles=["Administrador"], session_id=1)
    assert jwt.get_unverified_header(token_usuario)["alg"] == "RS256"


def test_un_token_de_demo_falsificado_con_claims_de_usuario_no_entra():
    """El intento evidente: añadirle `roles` y `session_id` a un token de demo.

    Falla por el algoritmo antes que por los claims — pero se comprueba el efecto,
    no el motivo, porque el efecto es lo que protege.
    """
    import time

    import jwt
    from django.conf import settings

    falsificado = jwt.encode(
        {
            "typ": "demo_session",
            "idprospecto": 1,
            "sub": "3",
            "roles": ["Administrador"],
            "session_id": 1,
            "exp": int(time.time()) + 3600,
        },
        settings.DEMO_SESSION_SECRET,
        algorithm="HS256",
    )

    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {falsificado}")

    assert api.get("/api/v1/usuarios").status_code == 401


def test_los_secretos_de_demo_y_de_usuario_son_distintos():
    """Compartirlos uniría las dos familias en una sola superficie.

    Bastaría con que se filtrara el secreto de la demo —el de menor valor, el que
    circula por el flujo público— para poder firmar credenciales del sistema.
    """
    from django.conf import settings

    assert settings.DEMO_SESSION_SECRET != settings.DEMO_GRANT_SECRET
    assert str(settings.DEMO_SESSION_SECRET) not in str(settings.JWT_PRIVATE_KEY)
