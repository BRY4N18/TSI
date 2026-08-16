"""T043 — primera página de los cuatro listados por debajo del umbral (SC-004).

Sobre el doble en memoria, así que **no mide Pinot**: mide que la capa de
informes no introduzca coste propio. El objetivo de 2 s de SC-004 se verifica
contra el stack real siguiendo el `quickstart.md`.

Lo que sí detecta, y es lo que se busca
---------------------------------------
El coste que crece con las filas por resolver catálogos **una consulta por fila**
en vez de una por página. Funciona, da el resultado correcto, y se degrada en
proporción al tamaño de página sin que ninguna prueba funcional lo note.
"""

from __future__ import annotations

import time

import pytest

BASE = "/api/v1/informes/ventas-crm"

LISTADOS = ["prospectos", "reasignaciones", "demos-activas", "notificaciones-enviadas"]

UMBRAL_MS = 300


@pytest.fixture
def todo_sembrado(
    dos_carteras, asignaciones_sembradas, notificaciones_sembradas,
    demos_formato_mixto, reloj_congelado,
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

    @pytest.fixture
    def cartera_grande(self, mock_pinot, gerentes_sembrados):
        """Cuarenta prospectos perdidos, para que el coste tenga dónde dispararse.

        Todos del mismo tipo a propósito: así la única variable entre las dos
        medidas es **el número de filas de la página**, que es justo lo que no
        debe influir.
        """
        from conftest import PINOT_STORE
        from apps.ventas_crm.tests.conftest import AHORA_MS, GERENTE_A, _prospecto

        for i in range(40):
            pid = 8600 + i
            PINOT_STORE["Dim_Prospecto"].append(
                _prospecto(pid, empresa=f"Perdida {i}", idusuario=GERENTE_A,
                           activo=False, motivo="perdido", etapa="Perdido")
            )
            PINOT_STORE["Fact_Pipeline"].append(
                {
                    "id_transicion": pid,
                    "id_prospecto": pid,
                    "etapa_anterior": "Contactado",
                    "etapa_nueva": "Perdido",
                    "motivo_perdida": "competencia",
                    "gerente_id": GERENTE_A,
                    "fecha_transicion": AHORA_MS,
                    "fecha_actualizacion": AHORA_MS,
                }
            )

    def test_el_numero_de_consultas_no_depende_del_numero_de_filas(
        self, api_client, admin_auth_headers, cartera_grande
    ):
        """La propiedad que importa: constante, no proporcional.

        Se comparan dos páginas que traen **el mismo tipo de filas** en
        cantidades muy distintas. Si los catálogos se resolvieran fila a fila,
        la de 40 costaría decenas de consultas más que la de 4.
        """
        pocas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/prospectos?limit=4"
        )
        muchas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/prospectos?limit=40"
        )

        assert muchas == pocas, (
            f"40 filas cuestan {muchas} consultas y 4 cuestan {pocas}: "
            "el catalogo se esta resolviendo fila a fila"
        )

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_ninguna_pagina_grande_dispara_el_coste(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        """Cota superior floja, para los cuatro listados.

        No se compara contra una página de una fila: los listados que resuelven
        un catálogo **condicional** —el motivo de pérdida solo se consulta si la
        página trae algún perdido— hacen una consulta menos cuando la página no
        contiene ese caso. Es una optimización correcta, y compararlas
        directamente la penalizaría.
        """
        consultas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/{informe}?limit=50"
        )

        assert consultas <= 7, f"'{informe}' hace {consultas} consultas por peticion"

