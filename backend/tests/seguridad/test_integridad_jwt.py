"""PG-SEC-003 — integridad del JWT: los tokens manipulados no entran.

Hasta ahora se probaba que un token **válido** funciona (fixture `auth_headers`),
que es la mitad fácil y la que no tiene riesgo. Lo que faltaba es la otra mitad:
que los inválidos **no** funcionen.

Las seis variantes de aquí no son un catálogo académico. Cada una corresponde a
un ataque concreto sobre un token capturado:

| Variante | Lo que intenta el atacante |
|---|---|
| Firma alterada | Cambiar el contenido y esperar que nadie verifique |
| `alg: none` | Que la biblioteca acepte un token sin firmar |
| Algoritmo distinto | Confusión HS256/RS256: firmar con la clave *pública* |
| Expirado | Reutilizar un token viejo indefinidamente |
| Claims manipulados | Elevar su rol o cambiar de tenant |
| Sesión revocada | Seguir dentro tras un cierre de sesión |

La tercera merece atención: la confusión de algoritmo es la vulnerabilidad
clásica de las bibliotecas JWT. Si el verificador admite HS256 cuando el emisor
usa RS256, la **clave pública** —que es pública— pasa a servir como secreto de
firma y cualquiera emite tokens válidos.

Contrato: `contracts/respuestas-seguridad.md` §C3.
"""

from __future__ import annotations

import time

import jwt
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

#: Endpoint protegido y barato, sin dependencias de datos: lo único que se mide
#: aquí es si la credencial pasa o no.
RUTA_PROTEGIDA = "/api/v1/usuarios"

USUARIO = 3
SESION = 1


def _cliente(token: str) -> APIClient:
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api


def _payload(**extra):
    ahora = int(time.time())
    base = {
        "sub": str(USUARIO),
        "roles": ["Administrador"],
        "session_id": SESION,
        "iat": ahora,
        "exp": ahora + 3600,
        "iss": settings.JWT_ISSUER,
    }
    base.update(extra)
    return base


# --- Las seis variantes adversariales -----------------------------------------


def test_un_token_valido_si_entra():
    """Control negativo. Sin esto, las demás pruebas podrían pasar por accidente.

    Si el endpoint denegara a todo el mundo —por un fallo de configuración o de
    fixture—, las seis pruebas de abajo pasarían sin haber comprobado nada. Es la
    misma trampa que la suite de aislamiento tuvo que corregir.
    """
    token = create_access_token(user_id=USUARIO, roles=["Administrador"], session_id=SESION)
    assert _cliente(token).get(RUTA_PROTEGIDA).status_code != 401


def test_firma_alterada_no_entra():
    token = create_access_token(user_id=USUARIO, roles=["Administrador"], session_id=SESION)
    cabecera, cuerpo, firma = token.split(".")
    # Voltear un carácter de la firma basta: no hace falta forjarla.
    alterada = ("A" if firma[0] != "A" else "B") + firma[1:]

    assert _cliente(f"{cabecera}.{cuerpo}.{alterada}").get(RUTA_PROTEGIDA).status_code == 401


def test_alg_none_no_entra():
    """El ataque más antiguo contra JWT: declarar que el token no lleva firma."""
    sin_firmar = jwt.encode(_payload(), key="", algorithm="none")

    assert _cliente(sin_firmar).get(RUTA_PROTEGIDA).status_code == 401


def test_algoritmo_distinto_al_declarado_no_entra():
    """Confusión HS256/RS256, la vulnerabilidad clásica de las bibliotecas JWT.

    Se firma con HS256 usando la **clave pública** como secreto. Si el verificador
    admitiera HS256, ese secreto —que es público por definición— permitiría a
    cualquiera emitir tokens válidos.
    """
    import base64
    import hashlib
    import hmac
    import json

    publica = settings.JWT_PUBLIC_KEY
    if not isinstance(publica, (str, bytes)):
        from cryptography.hazmat.primitives import serialization

        publica = publica.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    if isinstance(publica, str):
        publica = publica.encode()

    # El token se ensambla a mano, no con `jwt.encode`: PyJWT se niega a firmar
    # con una clave asimétrica como secreto HMAC. Esa negativa protege a quien
    # **emite**, y aquí lo que hay que probar es el **verificador** — que es la
    # mitad que un atacante sí puede alcanzar.
    def _b64(datos: bytes) -> str:
        return base64.urlsafe_b64encode(datos).decode().rstrip("=")

    cabecera = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    cuerpo = _b64(json.dumps(_payload()).encode())
    firma = _b64(
        hmac.new(publica, f"{cabecera}.{cuerpo}".encode(), hashlib.sha256).digest()
    )

    assert _cliente(f"{cabecera}.{cuerpo}.{firma}").get(RUTA_PROTEGIDA).status_code == 401


def test_token_expirado_no_entra():
    ahora = int(time.time())
    expirado = jwt.encode(
        _payload(iat=ahora - 7200, exp=ahora - 3600),
        settings.JWT_PRIVATE_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert _cliente(expirado).get(RUTA_PROTEGIDA).status_code == 401


def test_claims_manipulados_no_entran():
    """Elevar el rol reescribiendo el cuerpo del token.

    Es el caso que un desarrollador da por imposible «porque está firmado» — y lo
    está, pero solo si alguien lo verifica. Esta prueba es la que comprueba que
    alguien lo verifica.
    """
    import base64
    import json

    token = create_access_token(user_id=USUARIO, roles=["Cliente"], session_id=SESION)
    cabecera, cuerpo, firma = token.split(".")

    datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    datos["roles"] = ["Administrador"]
    nuevo = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode().rstrip("=")

    assert _cliente(f"{cabecera}.{nuevo}.{firma}").get(RUTA_PROTEGIDA).status_code == 401


def test_emisor_distinto_no_entra():
    """Un token de otro sistema, aunque esté bien firmado por él."""
    ajeno = jwt.encode(
        _payload(iss="otro-emisor"),
        settings.JWT_PRIVATE_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert _cliente(ajeno).get(RUTA_PROTEGIDA).status_code == 401


# --- Forma de la respuesta (contrato C3) --------------------------------------


def test_todas_las_variantes_responden_igual():
    """Distinguirlas le dice al atacante qué modificar.

    «Firma inválida» frente a «expirado» convierte el endpoint en un oráculo de
    depuración gratuito: prueba, lee el motivo, corrige, repite.
    """
    ahora = int(time.time())
    token_ok = create_access_token(user_id=USUARIO, roles=["Cliente"], session_id=SESION)
    cabecera, cuerpo, firma = token_ok.split(".")

    variantes = {
        "firma_alterada": f"{cabecera}.{cuerpo}.{'A' if firma[0] != 'A' else 'B'}{firma[1:]}",
        "alg_none": jwt.encode(_payload(), key="", algorithm="none"),
        "expirado": jwt.encode(
            _payload(iat=ahora - 7200, exp=ahora - 3600),
            settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM,
        ),
        "emisor_ajeno": jwt.encode(
            _payload(iss="otro"), settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM,
        ),
    }

    respuestas = {n: _cliente(t).get(RUTA_PROTEGIDA) for n, t in variantes.items()}

    codigos = {n: r.status_code for n, r in respuestas.items()}
    assert set(codigos.values()) == {401}, codigos

    cuerpos = {n: r.content for n, r in respuestas.items()}
    distintos = set(cuerpos.values())
    assert len(distintos) == 1, (
        f"Las variantes devuelven cuerpos distintos y delatan el motivo del rechazo: "
        f"{ {n: c[:80] for n, c in cuerpos.items()} }"
    )


def test_sin_credencial_es_401_y_no_403():
    """`401` = «no sé quién eres» · `403` = «sé quién eres y no puedes».

    Confundirlos fue el fallo de `changelog.md` C3 y desorienta al cliente
    legítimo sin aportar nada.
    """
    assert APIClient().get(RUTA_PROTEGIDA).status_code == 401


def test_una_cabecera_malformada_no_rompe_el_servidor():
    """Ningún `Authorization` extraño debe producir un 500."""
    for valor in ("Bearer", "Bearer ", "Basic abc", "Bearer a.b", "Bearer ...", "x" * 5000):
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=valor)
        respuesta = api.get(RUTA_PROTEGIDA)
        assert respuesta.status_code < 500, (valor, respuesta.status_code)


# --- Revocación de sesión y disponibilidad del almacén ------------------------


def test_una_sesion_revocada_no_entra_aunque_el_token_siga_vigente():
    """La sexta variante: el token es criptográficamente impecable.

    Firma válida, sin expirar, claims intactos. Lo único que cambió es que la
    sesión se cerró — y ese hecho **no vive en el token**, así que solo se
    detecta consultando el almacén. Es la razón de que exista `is_active`, y el
    motivo de que su caída plantee un dilema (ver `research.md` §R5.1).
    """
    from conftest import PINOT_STORE

    token = create_access_token(user_id=USUARIO, roles=["Administrador"], session_id=SESION)
    assert _cliente(token).get(RUTA_PROTEGIDA).status_code != 401, (
        "Control previo: la sesión debía estar activa antes de revocarla."
    )

    for fila in PINOT_STORE["Fact_Session"]:
        if fila.get("idsession") == SESION:
            fila["estadosession"] = "Cierre sesion"

    assert _cliente(token).get(RUTA_PROTEGIDA).status_code == 401


def _con_almacen_caido():
    """Simula que el almacen de sesion no responde.

    Se parchea `is_active` para que **lance**, no para que devuelva `False`: la
    diferencia es todo el sentido de PG-SEC-003. Devolver `False` significa
    «revocada» y debe denegar siempre; lanzar significa «no lo se».
    """
    from unittest.mock import patch

    from core.repositories.cuentas_clientes.session_repository import SessionRepository

    return patch.object(
        SessionRepository, "is_active", side_effect=ConnectionError("almacen caido")
    )


def test_con_el_almacen_caido_se_deniega_fuera_de_la_cadena_critica():
    """El resto del sistema sigue cerrado (fail-closed).

    Partners, suscripciones, informes o gestion de usuarios no tienen ningun
    argumento de seguridad fisica: si no se puede comprobar la revocacion, no se
    entra.
    """
    token = create_access_token(user_id=USUARIO, roles=["Administrador"], session_id=SESION)

    with _con_almacen_caido():
        respuesta = _cliente(token).get(RUTA_PROTEGIDA)

    assert respuesta.status_code == 401, (
        "Con el almacen caido, un endpoint fuera de la cadena critica debe "
        "denegar. Un 200 aqui significa que se admite cualquier sesion, revocada "
        "incluida, en TODO el sistema."
    )


def test_con_el_almacen_caido_la_cadena_critica_sigue_operativa():
    """El Principio IX es absoluto: la ayuda no se detiene por una caida de Redis.

    Se comprueba que la peticion **no muere en la autenticacion**. El codigo
    concreto depende de la vista —puede faltar un dato, o el rol puede no ser el
    adecuado—, pero un `401` significaria que la degradacion no funciona.
    """
    from core.seguridad.cadena_critica import es_cadena_critica

    ruta = "/api/v1/mi-seguimiento/posicion"
    assert es_cadena_critica(ruta), "La ruta de prueba debe estar en la lista."

    token = create_access_token(user_id=USUARIO, roles=["Unidad"], session_id=SESION)

    with _con_almacen_caido():
        respuesta = _cliente(token).post(ruta, {}, format="json")

    assert respuesta.status_code != 401, (
        f"{ruta} devolvio 401 con el almacen caido. La degradacion de PG-SEC-003 "
        "no se esta aplicando: una unidad en ruta no podria reportar su posicion "
        "durante una caida de Redis."
    )


def test_una_sesion_revocada_se_deniega_TAMBIEN_en_la_cadena_critica():
    """La mitad que no se degrada, y la que mas facil seria perder al implementar.

    Degradar ante una caida es una concesion al Principio IX. Dejar entrar a
    quien se le retiro el acceso **a proposito** no lo es: ahi no hay dilema de
    seguridad fisica que resolver, solo un acceso revocado.
    """
    from conftest import PINOT_STORE

    from core.seguridad.cadena_critica import es_cadena_critica

    ruta = "/api/v1/mi-seguimiento/posicion"
    assert es_cadena_critica(ruta)

    for fila in PINOT_STORE["Fact_Session"]:
        if fila.get("idsession") == SESION:
            fila["estadosession"] = "Cierre sesion"

    token = create_access_token(user_id=USUARIO, roles=["Unidad"], session_id=SESION)
    respuesta = _cliente(token).post(ruta, {}, format="json")

    assert respuesta.status_code == 401, (
        "Una sesion REVOCADA entro por la cadena critica. La degradacion solo "
        "cubre «no se puede comprobar», nunca «se comprobo y esta cerrada»."
    )


def test_la_lista_de_la_cadena_critica_no_crece_sin_que_nadie_lo_note():
    """Cada ruta anadida **amplia la ventana de riesgo**.

    Sin este aserto, la excepcion de seguridad se ensancharia poco a poco sin
    revision: cada anadido parece razonable por separado.
    """
    from core.seguridad.cadena_critica import TOTAL_RUTAS

    assert TOTAL_RUTAS == 9, (
        f"La cadena critica tiene {TOTAL_RUTAS} rutas y las confirmadas son 9. "
        "Ampliarla exige justificacion explicita de Safety (Principio IX) y "
        "Reliability (II), segun constitution.md."
    )


@pytest.mark.parametrize("ruta", [
    "/api/v1/usuarios",
    "/api/v1/partners",
    "/api/v1/informes/emergencias/casos",
    "/api/v1/accidentes/ACC-1/evidencias",
    "/api/v1/soporte/tickets",
])
def test_lo_que_no_es_cadena_critica_no_se_cuela_en_la_lista(ruta):
    """Los catalogos, informes y listados NO degradan.

    El criterio es «su denegacion retrasa la llegada de ayuda», no «pertenece al
    modulo de emergencias». Con el criterio ancho serian 46 rutas.
    """
    from core.seguridad.cadena_critica import es_cadena_critica

    assert not es_cadena_critica(ruta)
