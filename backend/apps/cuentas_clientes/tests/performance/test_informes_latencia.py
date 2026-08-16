"""T048 — la primera página de los ocho listados, por debajo del umbral (SC-002).

Sobre el doble en memoria, así que **no mide Pinot**: mide que la capa de
informes no introduzca coste propio. El umbral es el del resto de las pruebas de
rendimiento de esta app (300 ms con mocks); el objetivo de 2 s de SC-002 se
verifica contra el stack real siguiendo el `quickstart.md`.

Lo que sí puede detectar aquí, y es lo que se busca
---------------------------------------------------
El coste que crece con las filas por resolver catálogos **una consulta por
fila** en vez de una por página. Es el error clásico de este patrón: funciona,
da el resultado correcto, y se degrada en proporción al tamaño de la página sin
que ninguna prueba funcional lo note. Por eso la última clase compara el número
de consultas de una página de 1 fila con el de una de 50.
"""

from __future__ import annotations

import time

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

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

UMBRAL_MS = 300


@pytest.fixture
def todo_sembrado(
    sesiones_sembradas,
    credenciales_temporales_sembradas,
    accesos_tecnicos_sembrados,
    onboarding_sembrado,
    transferencias_sembradas,
    usuario_multirol,
):
    return True


@pytest.mark.slow
@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
def test_primera_pagina_bajo_el_umbral(
    api_client, admin_auth_headers, informe, todo_sembrado
):
    muestras: list[float] = []

    for _ in range(20):
        inicio = time.perf_counter()
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)
        muestras.append((time.perf_counter() - inicio) * 1000)
        assert respuesta.status_code == 200

    muestras.sort()
    p95 = muestras[int(len(muestras) * 0.95) - 1]

    assert p95 <= UMBRAL_MS, f"'{informe}' tarda {p95:.1f} ms en la primera pagina"


@pytest.mark.slow
@pytest.mark.api
class TestElCosteNoCreceConLasFilas:
    """Los catálogos se resuelven por página, no fila a fila."""

    @staticmethod
    def _consultas(api_client, headers, url) -> int:
        from unittest.mock import patch

        from conftest import _pinot_query_impl

        contador = {"n": 0}

        def contando(self, sql, params=None):
            contador["n"] += 1
            return _pinot_query_impl(sql, params)

        with patch("core.pinot.client.PinotClient.query", contando):
            api_client.get(url, **headers)
        return contador["n"]

    @pytest.mark.parametrize(
        "informe", ["usuarios-por-rol", "accesos-tecnicos", "transferencias-propiedad"]
    )
    def test_una_pagina_grande_no_cuesta_mas_consultas_que_una_pequena(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        una = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/{informe}?limit=1"
        )
        muchas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/{informe}?limit=50"
        )

        assert muchas == una, (
            f"'{informe}' hace {muchas} consultas con 50 filas y {una} con 1: "
            "el catalogo se esta resolviendo fila a fila"
        )

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_ningun_listado_pasa_de_un_punado_de_consultas(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        """El techo es constante y bajo, sea cual sea el tamaño de la página.

        El contador incluye las consultas de **autenticación** (validación del
        token y de la sesión), que ocurren antes de llegar a la vista, así que el
        número no es solo el del listado.

        El más caro es `accesos-tecnicos`, con 7: dos de autenticación, una del
        listado y cuatro para la cadena `UsuariosServidorRolesServidor` →
        `RolesServidor` → `RolesServidorRoles` → `Rol`, más el nombre de usuario.
        Es el precio de que Pinot no admita JOIN, y **no crece con las filas** —
        eso lo garantiza la prueba anterior, que es la que importa.
        """
        consultas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/{informe}?limit=50"
        )

        assert consultas <= 7, f"'{informe}' hace {consultas} consultas por peticion"
