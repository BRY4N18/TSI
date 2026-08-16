"""T045 — recorrer un listado por páginas devuelve cada fila **exactamente una
vez** (SC-005).

Es la prueba que justifica haber elegido keyset sobre `OFFSET`, y la única que
puede detectar el defecto que `OFFSET` produce: filas repetidas o saltadas entre
páginas. Ese defecto no lanza ningún error — devuelve datos plausibles — así que
sin esta comprobación pasaría inadvertido hasta que alguien cuadrara totales.

El método es comparar dos lecturas del mismo listado:

* **de una sola página**, con `limit` alto — la verdad de referencia;
* **por páginas de una fila**, siguiendo el cursor hasta agotarlo.

Deben coincidir en contenido **y en orden**.
"""

from __future__ import annotations

import json

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

#: Los ocho, con el fixture que les da filas suficientes para paginar.
LISTADOS = [
    "usuarios-por-rol",
    "sesiones-activas",
    "credenciales-temporales",
    "accesos-tecnicos",
    "solicitudes-alta-pendientes",
    "onboarding-incompleto",
    "cuentas-por-estado",
    "transferencias-propiedad",
]


@pytest.fixture
def todo_sembrado(
    sesiones_sembradas,
    credenciales_temporales_sembradas,
    accesos_tecnicos_sembrados,
    onboarding_sembrado,
    transferencias_sembradas,
    usuario_multirol,
):
    """Todos los listados con filas, para que ninguna prueba recorra un vacío."""
    return True


def _recorrer(api_client, headers, informe, limit=1, tope=200):
    """Recorre el listado por páginas y devuelve las filas concatenadas."""
    filas = []
    cursor = None
    paginas = 0
    while paginas < tope:
        url = f"{BASE}/{informe}?limit={limit}"
        if cursor:
            # El cursor es opaco: se reenvía tal cual, sin interpretarlo.
            from urllib.parse import quote

            url += f"&cursor={quote(cursor)}"
        cuerpo = api_client.get(url, **headers).json()
        filas.extend(cuerpo["data"])
        paginas += 1
        cursor = cuerpo["meta"]["pagination"]["cursor"]
        if cursor is None:
            return filas, paginas
    raise AssertionError(f"'{informe}' no termino de paginar en {tope} paginas")


@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
class TestIntegridadDelRecorrido:
    def test_el_recorrido_coincide_con_la_lectura_de_una_pagina(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        de_una_vez = api_client.get(
            f"{BASE}/{informe}?limit=500", **admin_auth_headers
        ).json()["data"]

        por_paginas, _ = _recorrer(api_client, admin_auth_headers, informe, limit=1)

        assert por_paginas == de_una_vez, (
            "el recorrido por paginas no reproduce la lectura completa: "
            "hay filas repetidas, saltadas o en distinto orden"
        )

    def test_ninguna_fila_se_repite(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        filas, _ = _recorrer(api_client, admin_auth_headers, informe, limit=1)

        serializadas = [json.dumps(f, sort_keys=True) for f in filas]
        assert len(serializadas) == len(set(serializadas))

    def test_el_recorrido_termina(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        """El cursor llega a `null`: no hay bucle infinito."""
        filas, paginas = _recorrer(api_client, admin_auth_headers, informe, limit=1)

        # Con `limit=1`, la última página es la que devuelve `cursor: null`.
        assert paginas == max(len(filas), 1)

    def test_paginas_de_dos_dan_el_mismo_resultado_que_de_una(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        # El tamaño de página no puede alterar el contenido; si lo altera, el
        # desempate del cursor está mal y el fallo depende de dónde caiga el corte.
        de_una, _ = _recorrer(api_client, admin_auth_headers, informe, limit=1)
        de_dos, _ = _recorrer(api_client, admin_auth_headers, informe, limit=2)

        assert de_una == de_dos


@pytest.mark.api
class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400_no_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        # Devolver el principio ante un cursor corrupto haría que el consumidor
        # recorriera en bucle las mismas filas creyendo que avanza.
        respuesta = api_client.get(
            f"{BASE}/cuentas-por-estado?cursor=basura", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(
            f"{BASE}/transferencias-propiedad?cursor=123", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        # Vacío es "sin cursor", que sí significa el principio.
        respuesta = api_client.get(
            f"{BASE}/cuentas-por-estado?cursor=", **admin_auth_headers
        )

        assert respuesta.status_code == 200
