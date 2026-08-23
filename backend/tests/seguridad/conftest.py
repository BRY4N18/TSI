"""Fixtures compartidas por las suites adversariales de seguridad.

Dos cosas viven aquí porque ninguna prueba del paquete debe poder olvidarlas:

1. El mock de Pinot, con `autouse=True`. Sin él, `JWTSessionAuthentication` sale a
   buscar un Pinot real que la suite no levanta, agota el timeout de red y la
   excepción acaba traducida en `AuthenticationFailed` — un `401` que **aparenta
   ser un fallo de permisos** y manda a diagnosticar al sitio equivocado. Costó 42
   pruebas en falso rojo el 2026-08-23 (`changelog.md` C3); la pista real era el
   tiempo de ejecución, no el aserto.

2. Los dos tenants y las **dos** vías de autenticación. Cubrir solo el JWT dejaría
   fuera toda la API de partners — precisamente la que consumen terceros — y la
   suite reportaría cobertura completa igualmente (`research.md` §R2).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from apps.partners.domain_constants import (
    ROL_ADMINISTRADOR,
    ROL_CLIENTE,
    ROL_DIRECTOR_TECNOLOGICO,
    ROL_PARTNER_INTEGRACION,
)
from core.auth.roles_tacticos import (
    ROL_DIRECTOR_FINANCIERO,
    ROL_DIRECTOR_OPERACIONES,
)
from core.jwt_utils import create_access_token
from tests.seguridad import datos_dos_tenants

#: Tenant A: el actor de las pruebas. Corresponde al `idcliente` 1 que ya siembra
#: `conftest.py` raíz, para no duplicar el fixture de datos.
TENANT_A = 1
#: Tenant B: el dueño de los recursos que A no debe alcanzar.
TENANT_B = 999

#: Usuario de cada tenant, según el almacén en memoria del conftest raíz.
USUARIO_A = 3
USUARIO_B = 99


@pytest.fixture(autouse=True)
def _pinot_en_memoria(request):
    """Obligatoria en todo el paquete **salvo en las pruebas de integración**.

    ⚠️ La exclusión no es un detalle. `autouse=True` alcanza a todo el paquete,
    incluidas las suites marcadas `integration` — que existen precisamente para
    hablar con motores reales. Con el mock puesto, `test_reconciliacion_integracion`
    comparaba el almacén en memoria contra ClickHouse y reportaba discrepancias
    inventadas: «100 en origen» eran las filas sembradas por esta misma fixture,
    no las de Pinot.

    Una prueba de integración silenciosamente mockeada es el peor de los dos
    mundos: no prueba la integración y además miente sobre lo que encontró.

    Siembra además los dos tenants: `Dim_Partner`, `Fact_Reclamo`, `Fact_Factura`
    y `Dim_Prospecto` están **vacíos** en el store raíz, así que sin esto el `404`
    es cierto y la prueba no demuestra nada sobre aislamiento (T078).
    """
    if request.node.get_closest_marker("integration"):
        # No se piden `mock_pinot`/`mock_kafka` como parametros: pedirlos los
        # activaria igualmente, porque una fixture parchea al construirse. Se
        # resuelven de forma perezosa solo cuando hacen falta.
        yield None
        return

    from conftest import PINOT_STORE

    mock = request.getfixturevalue("mock_pinot")
    request.getfixturevalue("mock_kafka")
    datos_dos_tenants.sembrar(PINOT_STORE)
    yield mock


#: Un actor por materia. Probar IDOR exige **el rol correcto y el tenant
#: equivocado**: con un único `PartnerIntegracion`, 90 de 92 rutas se deniegan por
#: autorización vertical y la suite no llega a ejercitar la tenencia (HALLAZGOS.md).
#: Los nombres salen de las clases de permiso del propio sistema, no de una
#: suposición: `IsCRMUser` exige `GerenteVentas` (no `Gerente`),
#: `IsUnidadDespachoOwn` exige `Unidad`, y Red Operativa la resuelve
#: `IsAdministradorOrDirectorTecnologico`. Elegir el rol «que suena bien» deja al
#: actor fuera por autorización vertical y la ruta sin examinar.
#: Roles **acotados por tenant**: solo estos deben quedarse fuera de lo ajeno.
#:
#: La distinción es imprescindible y no es un detalle: varios roles operan sobre
#: todos los tenants **por diseño**, y exigirles aislamiento produciría falsos
#: positivos que enseñan a ignorar la suite. Verificado en el código, no supuesto:
#:
#: - `es_solo_reportador()` (Soporte) acota **únicamente** a Cliente y Partner;
#:   quien tiene cualquier rol de atención ve los tickets de todos, que es su
#:   trabajo.
#: - `IsAdministradorOrDirectorTecnologico` hace al Director Tecnológico autoridad
#:   sobre **todas** las regiones operativas.
#: - `Unidad` atiende los accidentes que se le despachan, sean de quien sean.
ROLES_ACOTADOS_POR_TENANT = frozenset({ROL_CLIENTE, ROL_PARTNER_INTEGRACION})

ACTORES_POR_MATERIA = {
    "partner": [ROL_PARTNER_INTEGRACION],
    "cliente": [ROL_CLIENTE],
    "operaciones": [ROL_DIRECTOR_OPERACIONES],
    "ventas": ["GerenteVentas"],
    "finanzas": [ROL_DIRECTOR_FINANCIERO],
    "tecnologico": [ROL_DIRECTOR_TECNOLOGICO],
    "unidad": ["Unidad"],
}


def _cliente_jwt(roles: list[str], idusuario: int) -> APIClient:
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=idusuario, roles=roles, session_id=1)}"
        )
    )
    return api


@pytest.fixture
def cliente_tenant_a() -> APIClient:
    """Partner de integración del tenant A. El actor que intenta salirse."""
    return _cliente_jwt([ROL_PARTNER_INTEGRACION], USUARIO_A)


@pytest.fixture
def cliente_tenant_b() -> APIClient:
    """Partner de integración del tenant B. Existe para poder crear sus recursos."""
    return _cliente_jwt([ROL_PARTNER_INTEGRACION], USUARIO_B)


@pytest.fixture
def cliente_gestor() -> APIClient:
    """Administrador: opera sobre cualquier tenant, por diseño.

    Su presencia en la suite no es decorativa — sirve para comprobar que el
    endurecimiento **no** le degrada el diagnóstico, que es el error en el que se
    cae al corregir un IDOR de forma indiscriminada.
    """
    return _cliente_jwt([ROL_ADMINISTRADOR], USUARIO_A)


def es_actor_acotado(materia: str) -> bool:
    """¿Este actor debe quedarse fuera de los datos de otro tenant?"""
    return bool(ROLES_ACOTADOS_POR_TENANT.intersection(ACTORES_POR_MATERIA[materia]))


@pytest.fixture(params=sorted(ACTORES_POR_MATERIA), ids=lambda m: f"actor-{m}")
def materia_actual(request) -> str:
    return request.param


@pytest.fixture(params=sorted(ACTORES_POR_MATERIA), ids=lambda m: f"actor-{m}")
def cliente_por_materia(request) -> APIClient:
    """Recorre los cinco actores, siempre desde el tenant A.

    Parametrizada a propósito: una ruta que ningún actor alcanza queda señalada
    como no ejercitada en vez de contarse como cubierta por el primero que la
    deniegue.
    """
    return _cliente_jwt(ACTORES_POR_MATERIA[request.param], USUARIO_A)


@pytest.fixture
def cliente_anonimo() -> APIClient:
    """Sin credencial. Debe recibir 401, nunca 403 (contrato C3)."""
    return APIClient()


@pytest.fixture
def peticion_factory():
    """Construye una petición sintética para interrogar clases de permiso.

    US2 cruza 15 roles × 234 rutas = 3.510 celdas. Hacerlo por HTTP volvería el
    ciclo rápido inviable y llevaría a que se deje de esperar el CI, que es como
    muere un pipeline. Se interroga la clase de permiso directamente
    (`research.md` §R6).
    """

    def _crear(roles: list[str], idusuario: int = USUARIO_A, **kwargs):
        usuario = SimpleNamespace(
            is_authenticated=True, roles=roles, idusuario=idusuario, **kwargs
        )
        return SimpleNamespace(user=usuario, query_params={}, data={})

    return _crear


#: Acumula qué rutas ejercitaron de verdad el aislamiento y cuáles no. Es de
#: sesión a propósito: la conclusión solo existe al final del recorrido.
_COBERTURA: dict[str, list[str]] = {"ejercitadas": [], "no_ejercitadas": []}


@pytest.fixture(scope="session")
def registro_cobertura() -> dict[str, list[str]]:
    return _COBERTURA


def pytest_sessionfinish(session, exitstatus):
    """Informe de cobertura real del aislamiento.

    Sin esto la suite reporta «82 passed» y nadie sabe que la mayoría fueron
    denegaciones por rol, no por tenencia. Un número verde que no distingue
    ambas cosas es exactamente la confianza infundada que este bloque existe
    para evitar.
    """
    ejercitadas = _COBERTURA["ejercitadas"]
    no_ejercitadas = _COBERTURA["no_ejercitadas"]
    if not (ejercitadas or no_ejercitadas):
        return

    total = len(ejercitadas) + len(no_ejercitadas)
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:  # pragma: no cover
        return
    reporter.write_sep("=", "PG-SEC-001 — cobertura REAL del aislamiento")
    reporter.write_line(f"Rutas que ejercitaron la tenencia : {len(ejercitadas)}/{total}")
    reporter.write_line(f"Rutas NO ejercitadas (denegadas por rol): {len(no_ejercitadas)}/{total}")
    if ejercitadas:
        reporter.write_line("Ejercitadas de verdad (el actor accede a lo suyo y no a lo ajeno):")
        for patron in sorted(set(ejercitadas)):
            reporter.write_line(f"  + {patron}")
    if no_ejercitadas:
        reporter.write_line(
            "Estas necesitan un actor con el rol adecuado y otro tenant; "
            "hoy NO están cubiertas contra IDOR:"
        )
        for patron in no_ejercitadas:
            reporter.write_line(f"  - {patron}")
