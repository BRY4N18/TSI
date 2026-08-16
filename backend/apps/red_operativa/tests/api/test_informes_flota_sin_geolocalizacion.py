"""T019 — la flota no devuelve posición ni contacto (research D6).

`latitud` y `longitud` son la **última posición conocida** de la unidad, que la
constitución trata como dato sensible sujeto a control de acceso y auditoría.
`contactoproveedor` es dato personal, por el mismo criterio aplicado en Ventas y
CRM.

Ninguno aporta a un listado de composición: para seguir una unidad en tránsito
existe el módulo de seguimiento, con su propio control. Exponerlos ampliaría la
superficie sin ganancia.

Dos mitades, como en los tres módulos anteriores: contra la respuesta **y**
contra el código. El doble recorta las columnas que la consulta enumera, así que
un `SELECT *` podría pasar la primera mitad y filtrar la posición contra Pinot
real.
"""

from __future__ import annotations

import inspect
import json
import re

import pytest

from apps.red_operativa.tests.conftest import CONTACTO_PROHIBIDO, POSICION_PROHIBIDA
from core.repositories.red_operativa import informes_flota_repository

RUTA = "/api/v1/informes/red-operativa/flota"

PROHIBIDAS = ("latitud", "longitud", "contactoproveedor", "contacto", "posicion")


def _claves(objeto, encontradas=None):
    encontradas = encontradas if encontradas is not None else set()
    if isinstance(objeto, dict):
        for clave, valor in objeto.items():
            encontradas.add(clave)
            _claves(valor, encontradas)
    elif isinstance(objeto, list):
        for elemento in objeto:
            _claves(elemento, encontradas)
    return encontradas


@pytest.mark.api
class TestLaRespuestaNoLlevaPosicionNiContacto:
    def test_ninguna_clave_prohibida(self, api_client, admin_auth_headers, dos_flotas):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        assert not (_claves(cuerpo) & set(PROHIBIDAS))

    def test_ningun_valor_de_posicion(self, api_client, admin_auth_headers, dos_flotas):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert str(POSICION_PROHIBIDA) not in json.dumps(cuerpo)

    def test_ningun_valor_de_contacto(self, api_client, admin_auth_headers, dos_flotas):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert CONTACTO_PROHIBIDO not in json.dumps(cuerpo)

    def test_tampoco_para_el_propio_proveedor(
        self, api_client, proveedor_a_headers, dos_flotas
    ):
        # Que la unidad sea suya no convierte su posición en dato de listado:
        # para seguirla en tránsito existe el módulo de seguimiento.
        respuesta = api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers)

        assert respuesta.json()["data"]
        assert str(POSICION_PROHIBIDA) not in respuesta.content.decode()

    def test_si_llega_lo_necesario_para_identificar_la_unidad(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()
        fila = cuerpo["data"][0]

        assert fila["placa"]
        assert fila["tipo_unidad"]
        assert "condado" in fila

    def test_no_expone_identificadores_internos(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert "idunidademergencia" not in fila
            assert "idcliente" not in fila
            assert "idcondado" not in fila


class TestElCodigoNoPuedeFiltrarlos:
    @property
    def _consultas(self) -> list[str]:
        fuente = inspect.getsource(informes_flota_repository)
        return re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

    def test_hay_consultas_que_inspeccionar(self):
        assert len(self._consultas) >= 3

    def test_ninguna_usa_select_estrella(self):
        for consulta in self._consultas:
            assert not re.search(r"SELECT\s+\*", consulta, re.IGNORECASE), consulta

    @pytest.mark.parametrize("columna", ["latitud", "longitud", "contactoproveedor"])
    def test_ninguna_selecciona_una_columna_prohibida(self, columna):
        for consulta in self._consultas:
            assert columna not in consulta.lower(), consulta

    def test_la_consulta_de_flota_enumera_sus_columnas(self):
        flota = next(c for c in self._consultas if "idunidademergencia, idcliente" in c)

        assert flota.startswith("SELECT idunidademergencia, idcliente, placa")
        assert "*" not in flota
