"""T028 ⛔ — el identificador de cobro no sale jamás (SC-003, research D4).

**Esta no es una prueba más.** `Dim_MetodoPago.tokenpasarela` no es un hash ni
una referencia opaca inofensiva: `cobro_service.py:68` lo pasa a la pasarela
para ejecutar el cargo. **Quien lo tenga, puede cobrar.** No hay nada que romper
—bastaría con leer la respuesta— y el impacto no es informativo sino económico.

Por qué se inspecciona la respuesta **completa** y no los campos del contrato
-----------------------------------------------------------------------------
Un `SELECT *` filtra el campo **aunque el contrato no lo declare**. El contrato
describe lo que se pretende devolver; la respuesta es lo que se devuelve. Una
prueba que comparase contra la lista de campos declarados daría por bueno
exactamente el caso que hay que impedir.

Por eso se serializa el cuerpo entero a texto y se busca el valor, además de
comprobar contra el código fuente que la consulta enumera sus columnas.
"""

from __future__ import annotations

import inspect
import json
import re

import pytest

from apps.suscripciones.tests.conftest import TOKEN_PASARELA
from core.repositories.suscripciones import informes_facturacion_repository

BASE = "/api/v1/informes/suscripciones-facturacion"

LISTADOS = ["suscripciones", "facturas", "metodos-pago", "solicitudes-cambio-plan"]

#: Nombres que no pueden aparecer como clave en ninguna respuesta.
PROHIBIDAS = ("tokenpasarela", "token_pasarela", "token", "gateway_token")


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
class TestElValorNoApareceEnNingunaRespuesta:
    """Sobre el cuerpo **serializado completo**, no sobre los campos declarados."""

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_el_identificador_de_cobro_no_esta_en_el_cuerpo(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=500", **admin_auth_headers)
        cuerpo = respuesta.content.decode()

        assert respuesta.status_code == 200
        assert TOKEN_PASARELA not in cuerpo, (
            f"'{informe}' filtro el identificador de cobro: con el se puede cobrar"
        )

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_ninguna_clave_sospechosa(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}?limit=500", **admin_auth_headers).json()

        filtradas = _claves(cuerpo) & set(PROHIBIDAS)
        assert not filtradas, f"'{informe}' expone {filtradas}"

    def test_el_listado_de_metodos_devuelve_filas(
        self, api_client, admin_auth_headers, todo_sembrado
    ):
        """Sin filas, las dos pruebas de arriba no probarían nada."""
        cuerpo = api_client.get(f"{BASE}/metodos-pago", **admin_auth_headers).json()

        assert len(cuerpo["data"]) >= 2

    def test_tampoco_bajo_acotamiento(
        self, api_client, cliente_a_headers, todo_sembrado
    ):
        # Que el método sea suyo no le da derecho a su identificador de cobro:
        # con él, cualquiera que lea la respuesta puede cargar contra su tarjeta.
        respuesta = api_client.get(f"{BASE}/metodos-pago", **cliente_a_headers)

        assert respuesta.json()["data"], "sin filas esta prueba no probaria nada"
        assert TOKEN_PASARELA not in respuesta.content.decode()

    def test_si_llega_lo_necesario_para_identificar_el_metodo(
        self, api_client, admin_auth_headers, todo_sembrado
    ):
        """Exponer menos no puede significar exponer nada.

        Tipo y últimos dígitos identifican la tarjeta ante una persona y son
        inútiles para cobrar.
        """
        cuerpo = api_client.get(f"{BASE}/metodos-pago", **admin_auth_headers).json()
        fila = cuerpo["data"][0]

        assert fila["tipo"]
        assert fila["ultimos_digitos"]
        assert fila["fecha_expiracion"]


class TestElCodigoNoPuedeFiltrarlo:
    """La mitad que el doble en memoria no puede cubrir.

    El fake recorta las columnas que la consulta enumera, así que si alguien la
    cambiara a `SELECT *` las pruebas de arriba podrían seguir pasando mientras
    contra Pinot real el identificador viajaría en la respuesta.
    """

    @property
    def _consultas(self) -> list[str]:
        fuente = inspect.getsource(informes_facturacion_repository)
        return re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

    def test_hay_consultas_que_inspeccionar(self):
        assert len(self._consultas) >= 3

    def test_ninguna_usa_select_estrella(self):
        for consulta in self._consultas:
            assert not re.search(r"SELECT\s+\*", consulta, re.IGNORECASE), consulta

    def test_ninguna_selecciona_el_identificador_de_cobro(self):
        for consulta in self._consultas:
            assert "tokenpasarela" not in consulta.lower(), consulta

    def test_la_consulta_de_metodos_enumera_sus_columnas(self):
        metodos = next(c for c in self._consultas if "idmetodopago" in c)

        assert metodos.startswith("SELECT idmetodopago, idcliente, tipo, ultimosdigitos")
        assert "*" not in metodos

    def test_tampoco_lo_selecciona_ningun_otro_repositorio_de_informes(self):
        """La fuga podría entrar por otro listado del departamento."""
        from core.repositories.suscripciones import (
            informes_cambio_plan_repository,
            informes_suscripcion_repository,
        )

        for modulo in (
            informes_suscripcion_repository,
            informes_cambio_plan_repository,
        ):
            fuente = inspect.getsource(modulo)
            for consulta in re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE):
                assert "tokenpasarela" not in consulta.lower(), consulta
                assert not re.search(r"SELECT\s+\*", consulta, re.IGNORECASE), consulta
