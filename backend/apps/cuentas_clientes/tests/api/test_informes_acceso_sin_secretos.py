"""T023 — ninguna respuesta lleva material sensible (research D7).

Esta prueba tiene **dos mitades deliberadas**, y ninguna sustituye a la otra:

1. **Contra la respuesta.** Que `contrasena`, `token` ni su valor aparezcan en el
   cuerpo devuelto.
2. **Contra el código fuente.** Que los repositorios no usen `SELECT *` sobre las
   tablas con material sensible.

La segunda existe porque **el doble en memoria no basta**. El fake de
`conftest.py` recorta a mano las columnas que la consulta enumera, así que si
alguien cambiara la consulta a `SELECT *`, la primera mitad podría seguir
pasando mientras contra Pinot real la contraseña viajaría en la respuesta. Una
prueba que solo mira el resultado del doble da confianza falsa justo en la
garantía donde menos se puede permitir.
"""

from __future__ import annotations

import inspect
import json
import re

import pytest

from core.repositories.cuentas_clientes import informes_acceso_repository

BASE = "/api/v1/informes/cuentas-clientes"

#: Claves que no pueden aparecer en ninguna respuesta, en ningún nivel.
PROHIBIDAS = ("contrasena", "token", "refresh_token", "client_secret_hash", "password")

#: Identificadores internos: tampoco son dato de presentación
#: (`design-system.md` §8). Se comprueban como clave exacta, no como subcadena:
#: `usuario_servidor` contiene "usuario" y es un campo legítimo del contrato.
IDENTIFICADORES = (
    "idusuario",
    "idcredencial",
    "idsession",
    "idrol",
    "idusuarioservidor",
    "idrolservidor",
)


def _claves(objeto, encontradas=None):
    """Todas las claves del cuerpo, recorriendo listas y diccionarios anidados."""
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
class TestLaRespuestaNoLlevaSecretos:
    def test_sesiones_activas_no_devuelve_el_token(
        self, api_client, admin_auth_headers, sesiones_sembradas
    ):
        respuesta = api_client.get(f"{BASE}/sesiones-activas", **admin_auth_headers)
        cuerpo = respuesta.json()

        assert len(cuerpo["data"]) > 0, "sin filas esta prueba no probaria nada"
        assert not (_claves(cuerpo) & set(PROHIBIDAS))
        assert "NO-DEBE-SALIR-NUNCA" not in json.dumps(cuerpo)

    def test_credenciales_temporales_no_devuelve_la_contrasena(
        self, api_client, admin_auth_headers, credenciales_temporales_sembradas
    ):
        cuerpo = api_client.get(
            f"{BASE}/credenciales-temporales", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) > 0, "sin filas esta prueba no probaria nada"
        assert not (_claves(cuerpo) & set(PROHIBIDAS))
        assert "NO-DEBE-SALIR-NUNCA" not in json.dumps(cuerpo)

    def test_accesos_tecnicos_no_devuelve_la_contrasena_de_servidor(
        self, api_client, admin_auth_headers, accesos_tecnicos_sembrados
    ):
        cuerpo = api_client.get(f"{BASE}/accesos-tecnicos", **admin_auth_headers).json()

        assert len(cuerpo["data"]) > 0, "sin filas esta prueba no probaria nada"
        assert not (_claves(cuerpo) & set(PROHIBIDAS))
        assert "NO-DEBE-SALIR-NUNCA" not in json.dumps(cuerpo)

    def test_ningun_listado_expone_identificadores_internos(
        self,
        api_client,
        admin_auth_headers,
        sesiones_sembradas,
        credenciales_temporales_sembradas,
        accesos_tecnicos_sembrados,
    ):
        for informe in (
            "usuarios-por-rol",
            "sesiones-activas",
            "credenciales-temporales",
            "accesos-tecnicos",
        ):
            cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()
            filtradas = _claves(cuerpo) & set(IDENTIFICADORES)

            assert not filtradas, f"'{informe}' expone identificadores: {filtradas}"


class TestElCodigoNoPuedeFiltrarlos:
    """La mitad que el doble en memoria no puede cubrir.

    Sin esto, cambiar una consulta a `SELECT *` seguiría pasando las pruebas de
    arriba —porque el fake recorta las columnas él mismo— y la contraseña solo
    viajaría contra Pinot real, que es donde importa.
    """

    @property
    def _consultas(self) -> list[str]:
        """El texto de las consultas del repositorio, sin comentarios ni docstring.

        Se inspecciona solo esto y no el fichero entero porque el módulo
        **documenta a propósito** qué está prohibido —`SELECT *` y los nombres
        de las columnas sensibles—, y esa documentación no puede ser lo que haga
        fallar la prueba que la respalda.
        """
        fuente = inspect.getsource(informes_acceso_repository)
        return re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

    def test_hay_consultas_que_inspeccionar(self):
        # Si el patrón dejara de encontrar consultas, todas las comprobaciones
        # de abajo pasarían recorriendo una lista vacía.
        assert len(self._consultas) >= 4

    @pytest.mark.parametrize(
        "tabla", ["Dim_Credencial", "Fact_Session", "Dim_UsuariosServidor"]
    )
    def test_no_hay_select_estrella_sobre_las_tablas_sensibles(self, tabla):
        patron = re.compile(rf"SELECT\s+\*\s+FROM\s+{tabla}", re.IGNORECASE)

        for consulta in self._consultas:
            assert not patron.search(consulta), (
                f"`SELECT *` sobre {tabla} deja viajar su columna sensible hasta la vista"
            )

    def test_ninguna_consulta_usa_select_estrella(self):
        for consulta in self._consultas:
            assert not re.search(r"SELECT\s+\*", consulta, re.IGNORECASE), consulta

    @pytest.mark.parametrize("columna", ["contrasena", "token", "refresh_token"])
    def test_ninguna_consulta_nombra_una_columna_sensible(self, columna):
        for consulta in self._consultas:
            assert columna not in consulta.lower(), (
                f"la consulta selecciona '{columna}': {consulta}"
            )
