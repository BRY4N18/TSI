"""Filtros y paginacion de `GET /logs-api` (BE-DELTA-06).

Antes, este endpoint devolvia `next_cursor` en su `meta` pero **no aceptaba
ningun cursor**: anunciaba una paginacion que no existia. Y los filtros de
codigo y fecha no existian en absoluto, asi que la UI los habria tenido que
resolver en memoria sobre la ultima pagina — dando una falsa sensacion de
exhaustividad y descuadrando el recuento de cada pagina.

Ahora **todo se resuelve en la base**: cada cambio de filtro es una consulta.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/logs-api"
ID_PARTNER = 660
BASE_MS = 1_750_000_000_000
DIA = 86_400_000


@pytest.fixture
def historial(mock_pinot, mock_kafka):
    """Partner 660 con 30 llamadas, con el id **al revés** que la fecha.

    Los ids ascienden mientras las fechas descienden, que es el caso que rompía
    el cursor simple: `idlogllamadaapi < cursor` saltaba a un punto que no
    corresponde al orden de la consulta. Los datos así existen (siembras,
    backfills, reingestas), y por eso el cursor es compuesto.

    El `Dim_Partner` hace falta: la vista comprueba propiedad, y un partner
    inexistente devuelve 404 aunque quien pregunte sea un gestor.

    """
    PINOT_STORE["Dim_Partner"].append({
        "idpartner": ID_PARTNER,
        "idcliente": ID_PARTNER,
        "nombrepartner": "Consola Demo",
        "planapi": "Profesional",
        "contacto_tecnico_nombre": "QA",
        "contacto_tecnico_gmail": "qa@demo.com",
        "limitellamadasmes": 10000,
        "limitellamadasminuto": 120,
        "sandbox_activado": 1,
        "sandbox_expiracion": 253402300799000,
        "fecha_suspension": "",
        "motivo_suspension": "",
        "activo": True,
        "fecha_actualizacion": 1,
    })
    for i in range(30):
        PINOT_STORE["Fact_LogLlamadaAPI"].append({
            # id ascendente…
            "idlogllamadaapi": 1000 + i,
            "idpartner": ID_PARTNER,
            "idcredencial": 1,
            "endpoint": "/api/v1/datos/accidentes",
            "metodohttp": "GET",
            # 10 de cada: 200, 429 y 500
            "codigohttp": [200, 429, 500][i % 3],
            "latencia": 90.0,
            "iporigen": 3232235777,
            # …y fecha DESCENDENTE: el id no ordena como la fecha.
            "fechallamada": BASE_MS - i * DIA,
            "fecha_actualizacion": BASE_MS - i * DIA,
        })
    return ID_PARTNER


def _pedir(api_client, cabeceras, **params) -> dict:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return api_client.get(f"{URL}?idpartner={ID_PARTNER}&{query}", **cabeceras).json()


class TestPaginacionReal:
    def test_devuelve_el_cursor_de_la_siguiente_pagina(
        self, api_client, historial, devapis_auth_headers
    ):
        # Act
        cuerpo = _pedir(api_client, devapis_auth_headers, limit=10)

        # Assert
        assert len(cuerpo["data"]) == 10
        assert cuerpo["meta"]["pagination"]["next_cursor"] is not None

    @staticmethod
    def _siguiente(cuerpo):
        p = cuerpo["meta"]["pagination"]
        return {"cursor": p["next_cursor"], "cursor_fecha": p["next_cursor_fecha"]}

    def test_el_cursor_devuelto_SE_PUEDE_USAR(
        self, api_client, historial, devapis_auth_headers
    ):
        """🎯 Antes el `meta` anunciaba un cursor que el endpoint no aceptaba.

        Esa es la diferencia entre paginar y decir que se pagina.
        """
        # Arrange
        primera = _pedir(api_client, devapis_auth_headers, limit=10)

        # Act
        segunda = _pedir(
            api_client, devapis_auth_headers, limit=10, **self._siguiente(primera)
        )

        # Assert — la segunda página no repite ninguna fila de la primera
        ids_primera = {f["idlogllamadaapi"] for f in primera["data"]}
        ids_segunda = {f["idlogllamadaapi"] for f in segunda["data"]}
        assert len(segunda["data"]) == 10
        assert ids_primera & ids_segunda == set()

    def test_las_paginas_recorren_todo_el_historial_sin_huecos(
        self, api_client, historial, devapis_auth_headers
    ):
        # Arrange
        vistos: list[int] = []
        siguiente: dict = {}

        # Act — se recorre hasta agotar
        for _ in range(5):
            cuerpo = _pedir(api_client, devapis_auth_headers, limit=10, **siguiente)
            vistos.extend(f["idlogllamadaapi"] for f in cuerpo["data"])
            if cuerpo["meta"]["pagination"]["next_cursor"] is None:
                break
            siguiente = self._siguiente(cuerpo)

        # Assert — las 30, sin repetir ninguna y sin saltarse ninguna
        assert len(vistos) == len(set(vistos)), "la paginación repitió filas"
        assert sorted(vistos) == list(range(1000, 1030))

    def test_la_ultima_pagina_no_ofrece_cursor(
        self, api_client, historial, devapis_auth_headers
    ):
        # Act
        cuerpo = _pedir(api_client, devapis_auth_headers, limit=100)

        # Assert
        assert len(cuerpo["data"]) == 30
        assert cuerpo["meta"]["pagination"]["next_cursor"] is None


class TestFiltrosEnLaBase:
    def test_filtra_por_codigo_concreto(self, api_client, historial, devapis_auth_headers):
        # Act
        cuerpo = _pedir(api_client, devapis_auth_headers, codigohttp=429, limit=100)

        # Assert
        assert len(cuerpo["data"]) == 10
        assert {f["codigohttp"] for f in cuerpo["data"]} == {429}

    def test_el_filtro_por_codigo_alcanza_TODO_el_historial(
        self, api_client, historial, devapis_auth_headers
    ):
        """🎯 Con filtrado en memoria sobre una ventana de 10, este test daría 3.

        Es justo la falsa sensación de exhaustividad que se quería evitar: el
        usuario concluiría que hay 3 llamadas con 500 cuando hay 10.
        """
        # Act — página pequeña, pero el filtro va a la base
        cuerpo = _pedir(api_client, devapis_auth_headers, codigohttp=500, limit=100)

        # Assert
        assert len(cuerpo["data"]) == 10

    def test_filtra_por_rango_temporal(self, api_client, historial, devapis_auth_headers):
        # Act — los 5 días más recientes
        cuerpo = _pedir(
            api_client, devapis_auth_headers,
            desde=BASE_MS - 4 * DIA, hasta=BASE_MS + DIA, limit=100,
        )

        # Assert
        assert len(cuerpo["data"]) == 5

    def test_un_codigo_concreto_manda_sobre_solo_errores(
        self, api_client, historial, devapis_auth_headers
    ):
        """Pedir 200 con el conmutador puesto no puede devolver vacío en
        silencio: sería contradictorio y el usuario no sabría por qué."""
        # Act
        cuerpo = _pedir(
            api_client, devapis_auth_headers, solo_errores="true", codigohttp=200, limit=100
        )

        # Assert
        assert len(cuerpo["data"]) == 10
        assert {f["codigohttp"] for f in cuerpo["data"]} == {200}

    def test_los_filtros_se_combinan_con_la_paginacion(
        self, api_client, historial, devapis_auth_headers
    ):
        # Arrange — 10 llamadas con 429, de 4 en 4
        primera = _pedir(api_client, devapis_auth_headers, codigohttp=429, limit=4)

        # Act
        p = primera["meta"]["pagination"]
        segunda = _pedir(
            api_client, devapis_auth_headers, codigohttp=429, limit=4,
            cursor=p["next_cursor"], cursor_fecha=p["next_cursor_fecha"],
        )

        # Assert — el filtro se mantiene en la segunda página
        assert {f["codigohttp"] for f in segunda["data"]} == {429}
        assert len(segunda["data"]) == 4


class TestValidacion:
    def test_un_cursor_no_numerico_returns_400(
        self, api_client, historial, devapis_auth_headers
    ):
        assert api_client.get(
            f"{URL}?idpartner={ID_PARTNER}&cursor=abc", **devapis_auth_headers
        ).status_code == 400

    def test_sigue_exigiendo_idpartner(self, api_client, historial, devapis_auth_headers):
        assert api_client.get(URL, **devapis_auth_headers).status_code == 400

    def test_un_partner_inexistente_returns_404_no_403(
        self, api_client, historial, devapis_auth_headers
    ):
        """Que el partner no exista no es un problema de permisos.

        `verificar_propiedad` trata `None` como propiedad ajena y devolvería
        403, que despistaría a un gestor que sí tiene acceso a todos.
        """
        assert api_client.get(
            f"{URL}?idpartner=999999", **devapis_auth_headers
        ).status_code == 404


class TestQuienPuedeConsultarla:
    """BE-DELTA-07 — el partner puede ver SUS registros."""

    def test_el_partner_ve_los_suyos(self, api_client, mock_pinot, mock_kafka, partner_auth_headers):
        """🎯 RN-APM-009 existe para que el partner se autodiagnostique.

        Hasta 2026-08-10 el endpoint era exclusivo del Desarrollador de APIs, y
        eso contradecía la regla: el partner no podía ver sus propios errores.
        Se detectó verificando el panel de consumo contra la app real.
        """
        # Arrange — el partner del token (usuario 51) es del cliente 1
        PINOT_STORE["Dim_Partner"].append({
            "idpartner": 1, "idcliente": 1, "nombrepartner": "Suyo",
            "planapi": "Profesional", "contacto_tecnico_nombre": "A",
            "contacto_tecnico_gmail": "a@demo.com", "limitellamadasmes": 100,
            "limitellamadasminuto": 10, "sandbox_activado": 1,
            "sandbox_expiracion": 253402300799000, "fecha_suspension": "",
            "motivo_suspension": "", "activo": True, "fecha_actualizacion": 1,
        })
        PINOT_STORE["Fact_LogLlamadaAPI"].append({
            "idlogllamadaapi": 1, "idpartner": 1, "idcredencialapi": 1,
            "endpoint": "/api/v1/datos/accidentes", "metodohttp": "GET",
            "codigohttp": 403, "latenciams": 90.0, "iporigen": 3232235777,
            "fechallamada": BASE_MS, "fecha_actualizacion": BASE_MS,
        })

        # Act
        respuesta = api_client.get(f"{URL}?idpartner=1", **partner_auth_headers)

        # Assert
        assert respuesta.status_code == 200
        assert len(respuesta.json()["data"]) == 1

    def test_un_partner_NO_ve_los_de_otro(
        self, api_client, historial, partner_auth_headers
    ):
        """El permiso se relajó, el control de propiedad no."""
        assert api_client.get(
            f"{URL}?idpartner={ID_PARTNER}", **partner_auth_headers
        ).status_code == 403
