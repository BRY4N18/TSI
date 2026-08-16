"""Datos sembrados para los listados tácticos de Cuentas y Clientes.

Viven aquí y **no** en el `_INITIAL_PINOT_STORE` global a propósito. Las cuatro
tablas de accesos técnicos se siembran vacías en el store compartido, y las
pruebas de `test_server_access_contract.py` cuentan filas que ellas mismas dan
de alta: sembrarlas globalmente cambiaría esos recuentos y rompería una suite
ajena a este trabajo. Como fixture, el dato existe solo donde se pide.

Cada fixture cubre un caso que, sin él, dejaría una prueba **pasando sin probar
nada**: un listado vacío satisface toda comprobación de forma —envelope,
paginación, ausencia de campos sensibles— porque no hay ninguna fila donde algo
pueda fallar.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE
from core.repositories.cuentas_clientes.cliente_repository import (
    ESTADO_CLIENTE_ACTIVO,
    ESTADO_CLIENTE_BAJA,
    ESTADO_CLIENTE_PENDIENTE,
)
from core.repositories.cuentas_clientes.credential_repository import (
    ESTADO_CREDENCIAL_ACTIVO,
    ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
)
from core.repositories.cuentas_clientes.session_repository import (
    ESTADO_SESION_ACTIVA,
    ESTADO_SESION_CERRADA,
)

#: Instante fijo para que las aserciones de fecha no dependan del reloj.
#: 2026-08-01T00:00:00Z
BASE_MS = 1_785_542_400_000
DIA_MS = 86_400_000


@pytest.fixture
def accesos_tecnicos_sembrados(mock_pinot):
    """Cuentas de servidor con su cadena completa hasta el rol de negocio.

    Incluye a propósito los tres casos que el listado debe distinguir:

    * una cuenta **con** rol técnico y su mapeo a rol de negocio,
    * una cuenta con rol técnico **sin** mapeo — acceso que nadie sabe a qué
      habilita, y que por eso debe seguir apareciendo con `roles_negocio: []`,
    * una cuenta **inactiva**, que no debe aparecer.
    """
    PINOT_STORE["Dim_UsuariosServidor"].extend(
        [
            {
                "idusuarioservidor": 1,
                "idusuario": 1,
                "usuario": "admin_infra",
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idusuarioservidor": 2,
                "idusuario": 2,
                "usuario": "deploy_bot",
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idusuarioservidor": 3,
                "idusuario": 3,
                "usuario": "cuenta_retirada",
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "activo": False,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )
    PINOT_STORE["Dim_RolesServidor"].extend(
        [
            {
                "idrolservidor": 1,
                "rolservidor": "sysadmin",
                "descripcion": "Administración de servidores",
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idrolservidor": 2,
                "rolservidor": "despliegue",
                "descripcion": "Publicación de versiones",
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )
    PINOT_STORE["Dim_UsuariosServidorRolesServidor"].extend(
        [
            {
                "idusuarioservidorrolservidor": 1,
                "idusuarioservidor": 1,
                "idrolservidor": 1,
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idusuarioservidorrolservidor": 2,
                "idusuarioservidor": 2,
                "idrolservidor": 2,
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )
    # Solo `sysadmin` mapea a un rol de negocio. `despliegue` queda sin mapear
    # a propósito: es el caso que el listado existe para hacer visible.
    PINOT_STORE["Dim_RolesServidorRoles"].append(
        {"idrolservidor": 1, "idrol": 1, "activo": True, "fecha_actualizacion": BASE_MS}
    )


@pytest.fixture
def sesiones_sembradas(mock_pinot):
    """Sesiones abiertas de dos usuarios, más una cerrada que no debe salir."""
    PINOT_STORE["Fact_Session"].extend(
        [
            {
                "idsession": 5001,
                "idusuario": 1,
                "token": "NO-DEBE-SALIR-NUNCA",
                "refresh_token": "NO-DEBE-SALIR-NUNCA",
                "navegador": "Firefox",
                "fechahorainiciosesion": BASE_MS,
                "fechahoracierresesion": None,
                "estadosession": ESTADO_SESION_ACTIVA,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idsession": 5002,
                "idusuario": 2,
                "token": "NO-DEBE-SALIR-NUNCA",
                "refresh_token": "NO-DEBE-SALIR-NUNCA",
                "navegador": "Chrome",
                "fechahorainiciosesion": BASE_MS + DIA_MS,
                "fechahoracierresesion": None,
                "estadosession": ESTADO_SESION_ACTIVA,
                "fecha_actualizacion": BASE_MS + DIA_MS,
            },
            {
                "idsession": 5003,
                "idusuario": 3,
                "token": "NO-DEBE-SALIR-NUNCA",
                "refresh_token": "NO-DEBE-SALIR-NUNCA",
                "navegador": "Safari",
                "fechahorainiciosesion": BASE_MS + 2 * DIA_MS,
                "fechahoracierresesion": BASE_MS + 3 * DIA_MS,
                "estadosession": ESTADO_SESION_CERRADA,
                "fecha_actualizacion": BASE_MS + 3 * DIA_MS,
            },
        ]
    )


@pytest.fixture
def credenciales_temporales_sembradas(mock_pinot):
    """Tres credenciales pendientes de cambio, más una activa que no debe salir."""
    PINOT_STORE["Dim_Credencial"].extend(
        [
            {
                "idcredencial": 5101,
                "idusuario": 1,
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "estadocredencial": ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idcredencial": 5102,
                "idusuario": 2,
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "estadocredencial": ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
                "fecha_actualizacion": BASE_MS + DIA_MS,
            },
            {
                "idcredencial": 5103,
                "idusuario": 3,
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "estadocredencial": ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
                "fecha_actualizacion": BASE_MS + 2 * DIA_MS,
            },
            {
                "idcredencial": 5104,
                "idusuario": 4,
                "contrasena": "NO-DEBE-SALIR-NUNCA",
                "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )


@pytest.fixture
def solicitudes_pendientes_sembradas(mock_pinot):
    """Solicitudes de alta con antigüedades escalonadas, más una ya aprobada.

    Las fechas se escalonan a propósito: sin varias antigüedades distintas, el
    filtro `dias_minimo` no puede demostrarse —cualquier corte devolvería todo o
    nada, y las dos cosas parecerían funcionar—.
    """
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {
                "idcliente": 7001,
                "razon_social": "Aseguradora Norte S.A.",
                "tipo": "Corporativo",
                "estado": ESTADO_CLIENTE_PENDIENTE,
                "fecha_creacion": BASE_MS,  # la más antigua
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idcliente": 7002,
                "razon_social": "Municipio del Valle",
                "tipo": "Corporativo",
                "estado": ESTADO_CLIENTE_PENDIENTE,
                "fecha_creacion": BASE_MS + 5 * DIA_MS,
                "fecha_actualizacion": BASE_MS + 5 * DIA_MS,
            },
            {
                "idcliente": 7003,
                "razon_social": "Grúas del Sur Ltda.",
                "tipo": "Proveedor",
                "estado": ESTADO_CLIENTE_PENDIENTE,
                "fecha_creacion": BASE_MS + 9 * DIA_MS,  # la más reciente
                "fecha_actualizacion": BASE_MS + 9 * DIA_MS,
            },
            {
                "idcliente": 7004,
                "razon_social": "Ya Aprobada S.A.",
                "tipo": "Corporativo",
                "estado": ESTADO_CLIENTE_ACTIVO,
                "fecha_creacion": BASE_MS,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )


@pytest.fixture
def onboarding_sembrado(mock_pinot, solicitudes_pendientes_sembradas):
    """Etapas de incorporación: dos pendientes del mismo cliente y una completada."""
    PINOT_STORE["Fact_Onboarding"].extend(
        [
            {
                "id_onboarding": 7101,
                "id_cliente": 7001,
                "etapa": "verificacion_documental",
                "completado": False,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "id_onboarding": 7102,
                "id_cliente": 7001,
                "etapa": "configuracion_inicial",
                "completado": False,
                "fecha_actualizacion": BASE_MS + 4 * DIA_MS,
            },
            {
                "id_onboarding": 7103,
                "id_cliente": 7002,
                "etapa": "verificacion_documental",
                "completado": True,
                "fecha_completado": BASE_MS + DIA_MS,
                "fecha_actualizacion": BASE_MS + DIA_MS,
            },
        ]
    )


@pytest.fixture
def cuentas_sembradas(mock_pinot):
    """Cuentas en todos los estados, incluida una **dada de baja**.

    La de baja es el caso central del escenario 2 de la User Story 3: la baja es
    lógica y la fila conserva su razón social. Sin ella sembrada, la prueba de
    que «sigue apareciendo» pasaría contra un listado que la excluye.

    Y `admin_local_id: 88888` en una de ellas es el otro caso que importa: un
    propietario que **no resuelve** a ningún usuario vivo. La fila no puede
    omitirse por eso.
    """
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {
                "idcliente": 8001,
                "razon_social": "Cuenta Viva S.A.",
                "tipo": "Corporativo",
                "estado": ESTADO_CLIENTE_ACTIVO,
                "estado_onboarding": "Completado",
                "fecha_inicio_contrato": BASE_MS,
                "admin_local_id": 1,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idcliente": 8002,
                "razon_social": "Cuenta Cerrada S.A.",
                "tipo": "Corporativo",
                "estado": ESTADO_CLIENTE_BAJA,
                "estado_onboarding": "Completado",
                "fecha_inicio_contrato": BASE_MS,
                "admin_local_id": 2,
                "fecha_actualizacion": BASE_MS + DIA_MS,
            },
            {
                "idcliente": 8003,
                "razon_social": "Cuenta Huerfana S.A.",
                "tipo": "Proveedor",
                "estado": ESTADO_CLIENTE_ACTIVO,
                "estado_onboarding": None,
                "fecha_inicio_contrato": None,
                "admin_local_id": 88888,  # no existe en Dim_Usuarios
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )


@pytest.fixture
def transferencias_sembradas(mock_pinot, cuentas_sembradas):
    """Tres transferencias escalonadas en el tiempo, para probar el rango.

    La primera no tiene propietario anterior: es la asignación inicial de la
    cuenta, un caso legítimo que debe salir con `propietario_anterior: null` en
    vez de omitirse.
    """
    PINOT_STORE["Fact_HistorialTransferenciaPropiedad"].extend(
        [
            {
                "idhistorialtransferencia": 8101,
                "idcliente": 8001,
                "idusuarioanterior": None,
                "idusuarionuevo": 1,
                "fechahora": BASE_MS,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idhistorialtransferencia": 8102,
                "idcliente": 8001,
                "idusuarioanterior": 1,
                "idusuarionuevo": 2,
                "fechahora": BASE_MS + 5 * DIA_MS,
                "fecha_actualizacion": BASE_MS + 5 * DIA_MS,
            },
            {
                "idhistorialtransferencia": 8103,
                "idcliente": 8002,
                "idusuarioanterior": 2,
                "idusuarionuevo": 3,
                "fechahora": BASE_MS + 20 * DIA_MS,
                "fecha_actualizacion": BASE_MS + 20 * DIA_MS,
            },
        ]
    )


@pytest.fixture
def reloj_fijo():
    """Instante conocido para que la antigüedad no dependa del reloj real.

    Es 2026-08-11T00:00:00Z: **10 días** después de `BASE_MS`. Con ese ancla,
    cada antigüedad de las fixtures es un número exacto y comprobable, en vez de
    algo que cambia cada día que pasa y acaba haciendo fallar la suite sola.
    """
    return lambda: BASE_MS + 10 * DIA_MS


@pytest.fixture
def usuario_multirol(mock_pinot):
    """Un usuario con dos roles y otro sin ninguno (User Story 1, escenario 2).

    Son los dos extremos que research D4 obliga a distinguir: el primero **no**
    puede producir dos filas, y el segundo **no** puede desaparecer.
    """
    PINOT_STORE["Dim_Rol"].extend(
        [
            {"idrol": 90, "rol": "Auditor", "activo": True, "fecha_actualizacion": BASE_MS},
            {"idrol": 91, "rol": "Revisor", "activo": True, "fecha_actualizacion": BASE_MS},
        ]
    )
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {
                "idusuario": 900,
                "nombres": "Dos",
                "apellidos": "Roles",
                "gmail": "dosroles@tsi.com",
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idusuario": 901,
                "nombres": "Cero",
                "apellidos": "Roles",
                "gmail": "ceroroles@tsi.com",
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )
    PINOT_STORE["Dim_Usuario_Rol"].extend(
        [
            {
                "idusuariorol": 900,
                "idusuario": 900,
                "idrol": 90,
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
            {
                "idusuariorol": 901,
                "idusuario": 900,
                "idrol": 91,
                "activo": True,
                "fecha_actualizacion": BASE_MS,
            },
        ]
    )
    # 901 no recibe ninguna asignación: es el caso de FR-023.
