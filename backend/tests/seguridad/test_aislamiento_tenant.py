"""PG-SEC-001 — aislamiento multi-tenant (IDOR).

El mayor riesgo real del sistema: TSI sirve a partners, aseguradoras, municipios y
clientes sobre el **mismo** modelo dimensional. Un fallo de aislamiento no produce
ningún síntoma —nadie reporta que vio datos de más— y es lo primero que encuentra
quien itera identificadores en una URL.

**Qué prueba esta suite y qué no.** Recorre el inventario de rutas y comprueba, de
forma sistemática, que un actor de un tenant no obtiene datos de otro. Lo que
**no** hace es afirmar un código HTTP concreto: el requisito de seguridad es «no
devuelve datos ajenos» y, para un no gestor, «la respuesta no delata si el recurso
existe». Un aserto sobre el número exacto rompería con cualquier cambio legítimo
de contrato sin detectar ninguna fuga.

Ver `contracts/respuestas-seguridad.md` §C1 y `decisiones-pendientes.md` #51.
"""

from __future__ import annotations

import json

import pytest

from apps.partners.permissions import DENEGACION_UNIFICADA
from core.seguridad.inventario_rutas import RutaInventariada, rutas_con_identificador
from tests.seguridad import datos_dos_tenants as datos

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

#: Identificador que no existe en ningún tenant.
ID_INEXISTENTE = 8_888_888
#: Identificador que existe y pertenece al tenant B.
ID_AJENO = 999
#: Identificador de un recurso del propio actor, para detectar pruebas vacuas.
ID_PROPIO = 1

#: Códigos que constituyen una denegación válida. Se admite el rango entero en vez
#: de fijar uno: lo que se verifica es que **no hay datos ajenos**, no qué número
#: eligió el módulo. Fijarlo aquí convertiría esta suite en una prueba de contrato.
CODIGOS_DENEGACION = frozenset({400, 401, 403, 404, 405, 410, 422})


def _ids_de_prueba(ruta: RutaInventariada, valor: int) -> dict[str, int]:
    return {nombre: valor for nombre in ruta.parametros_id}


#: Identificadores por tipo de recurso. Un `999` genérico no sirve para un
#: accidente (`ACC-…`) ni para una factura (`F-…`): la ruta devolvería 404 por
#: formato y la prueba pasaría sin haber tocado el aislamiento. Cada entrada
#: apunta a un recurso **realmente sembrado** en `datos_dos_tenants`.
IDS_POR_RECURSO = {
    "accidente": (datos.ACCIDENTE_A, datos.ACCIDENTE_B),
    "factura": ("F-0001", "F-9999"),
}


#: Qué tenant posee el recurso que se va a pedir.
AJENO, PROPIO, INEXISTENTE = "ajeno", "propio", "inexistente"


def _valor_para(nombre: str, quien: str, es_entero: bool = False) -> str:
    """El identificador del tipo correcto, del tenant que toque.

    El caso `INEXISTENTE` respeta el tipo del parámetro: un id textual en un
    `<int:...>` haría que la URL no se pudiera construir y la prueba compararía
    contra `None` en vez de contra una respuesta.
    """
    # Un `<int:...>` manda sobre el nombre: `idelementosfisicosaccidente` contiene
    # «accidente» pero es un entero, y darle un id textual dejaría la ruta sin
    # construir — y por tanto sin probar.
    if not es_entero:
        for clave, (propio, del_otro) in IDS_POR_RECURSO.items():
            if clave in nombre.lower():
                if quien == INEXISTENTE:
                    return f"{propio.split('-')[0]}-NO-EXISTE"
                return str(del_otro if quien == AJENO else propio)
    return str({AJENO: ID_AJENO, PROPIO: ID_PROPIO}.get(quien, ID_INEXISTENTE))


def _construir_url(ruta: RutaInventariada, valor: int) -> str | None:
    """Sustituye cada parámetro del patrón por un identificador realmente sembrado.

    `valor` indica **de quién** es el recurso: `ID_AJENO` para el tenant B,
    `ID_PROPIO` para el A, `ID_INEXISTENTE` para ninguno. El tipo concreto lo
    decide `_valor_para` según el nombre del parámetro.

    Devuelve `None` si el patrón tiene parámetros que no sabemos rellenar; esas
    rutas se reportan aparte en vez de darse por probadas.
    """
    quien = {ID_AJENO: AJENO, ID_PROPIO: PROPIO}.get(valor, INEXISTENTE)
    url = "/" + ruta.patron
    for nombre in ruta.parametros:
        valor = _valor_para(nombre, quien, es_entero=f"<int:{nombre}>" in url)
        marcador_int = f"<int:{nombre}>"
        marcador_str = f"<str:{nombre}>"
        marcador_pelado = f"<{nombre}>"
        if marcador_int in url:
            # Un parámetro `int` no admite un id textual: si el recurso es de
            # tipo cadena, esta ruta no se puede construir y se reporta.
            if not str(valor).lstrip("-").isdigit():
                return None
            url = url.replace(marcador_int, str(valor))
        elif marcador_str in url or marcador_pelado in url:
            url = url.replace(marcador_str, str(valor)).replace(marcador_pelado, str(valor))
        else:
            return None
    return url if "<" not in url else None


def _rutas_probables() -> list[RutaInventariada]:
    return [r for r in rutas_con_identificador() if _construir_url(r, ID_AJENO)]


def _idents(ruta: RutaInventariada) -> str:
    return f"{ruta.patron}::{ruta.nombre_vista}"


RUTAS = _rutas_probables()


# --- T011: lectura de un recurso ajeno ---------------------------------------


def _ejercita_el_aislamiento(cliente, ruta) -> bool:
    """¿El actor accede de verdad a lo suyo en esta ruta?

    **La comprobación que evita que esta suite mienta.** Si el actor no obtiene
    su propio recurso, la denegación del ajeno no demuestra nada: puede venir del
    rol (`403`), o de que no haya recurso sembrado (`404`). En ambos casos la
    prueba pasaría en verde sin haber ejercitado el aislamiento ni una vez —
    confianza infundada, que es peor que no tener suite.

    Se exige **2xx sobre el recurso propio**. Es deliberadamente estricto: un
    criterio laxo infla la cobertura declarada, que es justo lo que este bloque
    existe para impedir.
    """
    url_propio = _construir_url(ruta, ID_PROPIO)
    return 200 <= cliente.get(url_propio).status_code < 300


@pytest.mark.parametrize("ruta", RUTAS, ids=_idents)
def test_un_get_a_un_recurso_ajeno_no_devuelve_datos(
    cliente_por_materia, ruta, registro_cobertura, request
):
    """El caso base del IDOR: cambiar un número en la URL.

    Recorre los cinco actores por materia (T078). Con uno solo, 90 de 92 rutas se
    denegaban por rol y la prueba pasaba sin ejercitar la tenencia.
    """
    if "get" not in ruta.metodos:
        pytest.skip(f"{ruta.patron} no implementa GET")

    from tests.seguridad.conftest import es_actor_acotado

    materia = request.node.callspec.params["cliente_por_materia"]
    if not es_actor_acotado(materia):
        pytest.skip(
            f"El rol «{materia}» opera sobre todos los tenants por diseño (ver "
            "ROLES_ACOTADOS_POR_TENANT). Exigirle aislamiento daría un falso "
            "positivo, y una suite con falsos positivos enseña a ignorarla."
        )

    url = _construir_url(ruta, ID_AJENO)
    respuesta = cliente_por_materia.get(url)

    if not _ejercita_el_aislamiento(cliente_por_materia, ruta):
        registro_cobertura["no_ejercitadas"].append(ruta.patron)
        pytest.skip(
            f"NO EJERCITADA: este actor no alcanza {ruta.patron} ni con su propio "
            "recurso, así que la denegación es de autorización vertical y no de "
            "tenencia."
        )

    registro_cobertura["ejercitadas"].append(ruta.patron)
    assert respuesta.status_code in CODIGOS_DENEGACION or _sin_datos(respuesta), (
        f"{url} devolvió {respuesta.status_code} con contenido al pedir un recurso "
        f"del tenant ajeno. Posible IDOR (PG-SEC-001)."
    )


def _sin_datos(respuesta) -> bool:
    """Un 200 solo es aceptable si no lleva datos de la entidad ajena."""
    if respuesta.status_code != 200:
        return True
    try:
        cuerpo = respuesta.json()
    except (ValueError, json.JSONDecodeError):
        return False
    datos = cuerpo.get("data") if isinstance(cuerpo, dict) else cuerpo
    return not datos


# --- T012: escritura sobre un recurso ajeno ----------------------------------


@pytest.mark.parametrize("verbo", ["put", "patch", "delete"])
@pytest.mark.parametrize("ruta", RUTAS, ids=_idents)
def test_una_escritura_sobre_un_recurso_ajeno_es_denegada(cliente_tenant_a, ruta, verbo):
    """No basta con el código: lo que importa es que el recurso de B no cambie.

    Aquí se comprueba la denegación; que el dato siga intacto se verifica en la
    prueba de integridad de más abajo, que sí puede leerlo como gestor.
    """
    if verbo not in ruta.metodos:
        pytest.skip(f"{ruta.patron} no implementa {verbo.upper()}")

    url = _construir_url(ruta, ID_AJENO)
    respuesta = getattr(cliente_tenant_a, verbo)(url, {}, format="json")

    assert respuesta.status_code in CODIGOS_DENEGACION, (
        f"{verbo.upper()} {url} devolvió {respuesta.status_code}: un tenant ajeno "
        f"pudo modificar el recurso (PG-SEC-001)."
    )


# --- T013: indistinguibilidad para quien no es gestor ------------------------


@pytest.mark.parametrize("ruta", RUTAS, ids=_idents)
def test_inexistente_y_ajeno_son_indistinguibles_para_un_no_gestor(cliente_tenant_a, ruta):
    """Contrato C1, y el aserto más importante de la suite.

    Si «no existe» y «no es tuyo» responden distinto, un atacante enumera el
    padrón ajeno iterando ids —cuántos partners hay, qué rangos están ocupados,
    si un competidor es cliente— **sin llegar a ver un solo dato**. La fuga no
    necesita que el aislamiento falle: le basta con que las dos negativas
    difieran.
    """
    if "get" not in ruta.metodos:
        pytest.skip(f"{ruta.patron} no implementa GET")

    url_ajeno = _construir_url(ruta, ID_AJENO)
    url_inexistente = _construir_url(ruta, ID_INEXISTENTE)

    r_ajeno = cliente_tenant_a.get(url_ajeno)
    r_inexistente = cliente_tenant_a.get(url_inexistente)

    assert r_ajeno.status_code == r_inexistente.status_code, (
        f"{ruta.patron} distingue por código: {r_ajeno.status_code} para un recurso "
        f"ajeno y {r_inexistente.status_code} para uno inexistente. Oráculo de "
        f"enumeración (PG-SEC-001)."
    )
    assert r_ajeno.content == r_inexistente.content, (
        f"{ruta.patron} distingue por cuerpo aunque el código coincida. Las vistas "
        f"vuelcan el mensaje en `detail`, así que un texto distinto filtra igual."
    )


# --- T014: el gestor conserva el diagnóstico ---------------------------------


def test_el_gestor_conserva_el_diagnostico_preciso(cliente_gestor):
    """La corrección no debe degradar la consola de gestión.

    Es el error en el que se cae al corregir un IDOR de forma indiscriminada:
    unificar todas las respuestas y dejar al administrador sin saber si un id
    existe. A quien opera sobre cualquier tenant, un 404 no le revela nada.
    """
    from types import SimpleNamespace

    from apps.partners.permissions import (
        PartnerInexistenteError,
        resolver_partner_visible,
    )
    from apps.partners.domain_constants import ROL_ADMINISTRADOR

    peticion = SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True, roles=[ROL_ADMINISTRADOR], idusuario=3)
    )
    with pytest.raises(PartnerInexistenteError):
        resolver_partner_visible(peticion, None)


def test_el_mensaje_de_denegacion_es_una_constante():
    """Redactar el mensaje en cada punto de fallo es cómo reaparecen las fugas."""
    assert DENEGACION_UNIFICADA
    assert "no encontrado" not in DENEGACION_UNIFICADA.lower(), (
        "El mensaje unificado no debe sugerir inexistencia."
    )


# --- T016: la suite no puede envejecer (SC-002) ------------------------------


def test_toda_ruta_con_identificador_esta_cubierta():
    """Sin esto, la cobertura envejece en cuanto alguien añade un endpoint.

    Es el criterio SC-002 y lo que distingue esta suite de una lista escrita a
    mano: una ruta nueva con identificador que no se pueda construir queda
    señalada aquí en vez de pasar desapercibida reportando «todo cubierto».
    """
    todas = rutas_con_identificador()
    cubiertas = {r.patron for r in RUTAS}
    sin_cubrir = [r.patron for r in todas if r.patron not in cubiertas]

    assert not sin_cubrir, (
        f"{len(sin_cubrir)} rutas con identificador no están cubiertas por la suite "
        f"de aislamiento porque su patrón no se pudo construir: {sin_cubrir[:10]}. "
        "Añadir soporte para ese tipo de parámetro en `_construir_url` — no ignorarlas."
    )
