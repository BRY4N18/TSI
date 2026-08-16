"""T021 — la cartera no devuelve datos de contacto (research D4).

El propósito táctico es **supervisar la cartera**, no contactar: para contactar
existe la pantalla operativa, que ya tiene esos datos y su control de acceso.
Exponerlos aquí convertiría un volcado de informe en una lista de contactos
exportable.

Y es asimétrico: exponer de menos se corrige añadiendo una columna; retirar un
dato después de que circule, no.

Dos mitades, como en el módulo piloto
-------------------------------------
Contra la respuesta **y** contra el código. El doble en memoria recorta a mano
las columnas que la consulta enumera, así que si alguien cambiara la consulta a
`SELECT *` la primera mitad podría seguir pasando mientras contra Pinot real el
correo y el teléfono viajarían en la respuesta.
"""

from __future__ import annotations

import inspect
import json
import re

import pytest

from core.repositories.ventas_crm import informes_cartera_repository

RUTA = "/api/v1/informes/ventas-crm/prospectos"

PROHIBIDAS = ("gmail", "telefono", "correo", "email")


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
class TestLaRespuestaNoLlevaContacto:
    def test_ninguna_clave_de_contacto(self, api_client, admin_auth_headers, dos_carteras):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        assert not (_claves(cuerpo) & set(PROHIBIDAS))

    def test_ningun_valor_de_contacto(self, api_client, admin_auth_headers, dos_carteras):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "NO-DEBE-SALIR" not in json.dumps(cuerpo)

    def test_tampoco_bajo_acotamiento(self, api_client, gerente_a_headers, dos_carteras):
        # El gerente ve su propia cartera; eso no le da acceso al contacto.
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        assert cuerpo["data"]
        assert "NO-DEBE-SALIR" not in json.dumps(cuerpo)

    def test_si_llega_lo_necesario_para_identificar_la_oportunidad(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        # Exponer menos no puede significar exponer nada: el listado debe seguir
        # sirviendo para reconocer de qué oportunidad se habla.
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()
        fila = cuerpo["data"][0]

        assert fila["empresa"]
        assert fila["nombre_contacto"]
        assert "cargo" in fila

    def test_no_expone_identificadores_internos(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert "idprospecto" not in fila
            assert "idusuario" not in fila


class TestElCodigoNoPuedeFiltrarlos:
    """La mitad que el doble en memoria no puede cubrir."""

    @property
    def _consultas(self) -> list[str]:
        fuente = inspect.getsource(informes_cartera_repository)
        return re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

    def test_hay_consultas_que_inspeccionar(self):
        assert len(self._consultas) >= 3

    def test_ninguna_usa_select_estrella(self):
        for consulta in self._consultas:
            assert not re.search(r"SELECT\s+\*", consulta, re.IGNORECASE), consulta

    @pytest.mark.parametrize("columna", ["gmail", "telefono"])
    def test_ninguna_consulta_selecciona_una_columna_de_contacto(self, columna):
        for consulta in self._consultas:
            assert columna not in consulta.lower(), (
                f"la consulta selecciona '{columna}': {consulta}"
            )

    def test_la_consulta_de_cartera_enumera_sus_columnas(self):
        # El SQL está partido en literales concatenados, así que se busca el que
        # abre el `SELECT` y no el que lleva el `FROM`.
        cartera = next(c for c in self._consultas if "idprospecto" in c)

        # Enumerar es lo que hace que añadir una columna sensible al esquema no
        # la publique sola.
        assert cartera.startswith("SELECT idprospecto, empresa")
        assert "*" not in cartera
