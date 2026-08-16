"""Datos sembrados para los informes tácticos de Suscripciones y Facturación.

**`dos_cuentas` es el fixture del que depende que este módulo esté probado.**
Con una sola cuenta poblada, filtrar por cuenta y no filtrar devuelven lo mismo,
así que toda prueba de acotamiento pasa aunque el acotamiento no exista. Es el
mismo riesgo que en Ventas y CRM, y por la misma razón.

Los otros tres casos sembrados protegen defectos concretos:

* una suscripción **con** cambio programado y otra **sin** él — el «sin» es un
  `0` explícito, no una ausencia, y confundirlos devuelve *todas* como si todas
  tuvieran una reducción pendiente (research D2);
* una factura **`Fallida` vencida** y otra **`En disputa`** — la segunda está
  fuera del cobro a propósito y presentarla como mora induce a perseguir un
  cargo que el sistema detuvo (research D3);
* un método de pago **reemplazado**, para que el vigente tenga de qué
  distinguirse (FR-007).

Y `tokenpasarela` se siembra con un valor reconocible: **no es un hash**, el
servicio de cobro lo pasa a la pasarela para ejecutar el cargo. Si aparece en
una respuesta, la prueba de T028 debe fallar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import PINOT_STORE
from core.jwt_utils import create_access_token

#: Instante fijo: 2026-08-11T12:00:00Z.
AHORA = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
AHORA_MS = int(AHORA.timestamp() * 1000)
DIA_MS = 86_400_000

CUENTA_A = 7701
CUENTA_B = 7702
ADMIN_A = 7801  # admin local de la cuenta A
ADMIN_B = 7802  # admin local de la cuenta B
SIN_CUENTA = 7803

PLAN_BASICO = 7901
PLAN_PRO = 7902

#: Valor que jamás puede aparecer en una respuesta. Con él se puede cobrar.
TOKEN_PASARELA = "tok_NO-DEBE-SALIR-NUNCA"


@pytest.fixture
def reloj_fijo():
    return lambda: AHORA_MS


@pytest.fixture
def cuentas_y_planes(mock_pinot):
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {"idusuario": ADMIN_A, "nombres": "Ana", "apellidos": "Torres",
             "gmail": "ana.torres@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idusuario": ADMIN_B, "nombres": "Teresa", "apellidos": "Beltran",
             "gmail": "teresa.beltran@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idusuario": SIN_CUENTA, "nombres": "Sin", "apellidos": "Cuenta",
             "gmail": "sin.cuenta@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {"idcliente": CUENTA_A, "razon_social": "Aseguradora Torres S.A.",
             "tipo": "Corporativo", "estado": "Activo", "admin_local_id": ADMIN_A,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
            # La cuenta B está **suspendida** a propósito: FR-011 dice que
            # conserva el acceso a sus propios registros.
            {"idcliente": CUENTA_B, "razon_social": "Transportes Beltran Ltda.",
             "tipo": "Corporativo", "estado": "Dado de baja", "admin_local_id": ADMIN_B,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Plan"].extend(
        [
            {"idplan": PLAN_BASICO, "nombre": "Basico", "nivel": "1", "activo": True,
             "precio": 100.0, "periodicidad": "mensual", "fecha_actualizacion": AHORA_MS},
            {"idplan": PLAN_PRO, "nombre": "Pro", "nivel": "2", "activo": True,
             "precio": 300.0, "periodicidad": "mensual", "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def dos_cuentas(mock_pinot, cuentas_y_planes):
    """Dos cuentas con facturación simultánea — el fixture que hace reales las pruebas.

    Tamaños distintos a propósito (A tiene 2 suscripciones, B tiene 1), para que
    un conteo pueda distinguir «acotado» de «sin acotar».
    """
    PINOT_STORE["Fact_Suscripcion"].extend(
        [
            # Con reducción de plan programada: `idplan_programado > 0`.
            {"id_suscripcion": 7001, "idcliente": CUENTA_A, "idplan": PLAN_PRO,
             "idplan_programado": PLAN_BASICO, "estado": "Activa", "activo": True,
             "renovacionautomatica": True, "motivocancelacion": None,
             "periodicidad": "mensual", "nivel": "2", "precio": 300.0,
             "fecha_inicio": AHORA_MS - 60 * DIA_MS, "fecha_fin": AHORA_MS + 5 * DIA_MS,
             "fechacancelacion": None, "fecha_actualizacion": AHORA_MS},
            # SIN cambio programado: el código escribe un `0` explícito, no un
            # vacío. Es el caso que una guarda de nulidad no distinguiría.
            {"id_suscripcion": 7002, "idcliente": CUENTA_A, "idplan": PLAN_BASICO,
             "idplan_programado": 0, "estado": "Cancelada", "activo": False,
             "renovacionautomatica": False, "motivocancelacion": "precio",
             "periodicidad": "mensual", "nivel": "1", "precio": 100.0,
             "fecha_inicio": AHORA_MS - 200 * DIA_MS, "fecha_fin": AHORA_MS - 10 * DIA_MS,
             "fechacancelacion": AHORA_MS - 10 * DIA_MS, "fecha_actualizacion": AHORA_MS},
            {"id_suscripcion": 7003, "idcliente": CUENTA_B, "idplan": PLAN_BASICO,
             "idplan_programado": 0, "estado": "Suspendida", "activo": True,
             "renovacionautomatica": True, "motivocancelacion": None,
             "periodicidad": "mensual", "nivel": "1", "precio": 100.0,
             "fecha_inicio": AHORA_MS - 90 * DIA_MS, "fecha_fin": AHORA_MS + 60 * DIA_MS,
             "fechacancelacion": None, "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def facturas_sembradas(mock_pinot, dos_cuentas):
    """Las cuatro situaciones de `estado_pago`, más una de la otra cuenta."""
    PINOT_STORE["Fact_Factura"].extend(
        [
            # Vencida e impaga: **sí** es mora.
            {"id_factura": "FAC-202606-00000001", "id_cliente": CUENTA_A,
             "id_suscripcion": 7001, "idmetodopago": 7601,
             "numero_factura": "0001", "periodo": "2026-06", "estado_pago": "Fallida",
             "tipo": "cargo", "es_nota_credito": False, "id_factura_original": None,
             "motivo_anulacion": None, "activo": True, "reintentos": 3,
             "monto_base": 100.0, "impuestos": 12.0, "monto_total": 112.0,
             "fecha_emision": AHORA_MS - 40 * DIA_MS,
             "fecha_vencimiento": AHORA_MS - 25 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
            # En disputa y vencida: **no** es mora. El sistema dejó de cobrarla.
            {"id_factura": "FAC-202607-00000002", "id_cliente": CUENTA_A,
             "id_suscripcion": 7001, "idmetodopago": 7601,
             "numero_factura": "0002", "periodo": "2026-07", "estado_pago": "En disputa",
             "tipo": "cargo", "es_nota_credito": False, "id_factura_original": None,
             "motivo_anulacion": None, "activo": True, "reintentos": 1,
             "monto_base": 100.0, "impuestos": 12.0, "monto_total": 112.0,
             "fecha_emision": AHORA_MS - 20 * DIA_MS,
             "fecha_vencimiento": AHORA_MS - 5 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
            {"id_factura": "FAC-202608-00000003", "id_cliente": CUENTA_A,
             "id_suscripcion": 7001, "idmetodopago": 7601,
             "numero_factura": "0003", "periodo": "2026-08", "estado_pago": "Pagada",
             "tipo": "cargo", "es_nota_credito": False, "id_factura_original": None,
             "motivo_anulacion": None, "activo": True, "reintentos": 0,
             "monto_base": 100.0, "impuestos": 12.0, "monto_total": 112.0,
             "fecha_emision": AHORA_MS - 5 * DIA_MS,
             "fecha_vencimiento": AHORA_MS + 10 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
            {"id_factura": "FAC-202608-00000004", "id_cliente": CUENTA_B,
             "id_suscripcion": 7003, "idmetodopago": 7603,
             "numero_factura": "0004", "periodo": "2026-08", "estado_pago": "Pendiente",
             "tipo": "cargo", "es_nota_credito": False, "id_factura_original": None,
             "motivo_anulacion": None, "activo": True, "reintentos": 0,
             "monto_base": 100.0, "impuestos": 12.0, "monto_total": 112.0,
             "fecha_emision": AHORA_MS - 2 * DIA_MS,
             "fecha_vencimiento": AHORA_MS + 13 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def metodos_pago_sembrados(mock_pinot, dos_cuentas):
    """Un método vigente, uno **reemplazado** y uno próximo a caducar."""
    PINOT_STORE["Dim_MetodoPago"].extend(
        [
            {"idmetodopago": 7601, "idcliente": CUENTA_A, "tipo": "tarjeta",
             "tokenpasarela": TOKEN_PASARELA, "ultimosdigitos": "4242",
             "activo": True, "fechaexpiracion": AHORA_MS + 10 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
            # Reemplazado: sigue existiendo pero ya no es el medio de cobro.
            {"idmetodopago": 7602, "idcliente": CUENTA_A, "tipo": "tarjeta",
             "tokenpasarela": TOKEN_PASARELA, "ultimosdigitos": "1111",
             "activo": False, "fechaexpiracion": AHORA_MS + 300 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
            {"idmetodopago": 7603, "idcliente": CUENTA_B, "tipo": "tarjeta",
             "tokenpasarela": TOKEN_PASARELA, "ultimosdigitos": "9999",
             "activo": True, "fechaexpiracion": AHORA_MS + 200 * DIA_MS,
             "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def solicitudes_sembradas(mock_pinot, dos_cuentas):
    """Una pendiente (sin resolutor) y una rechazada (con motivo)."""
    PINOT_STORE["Fact_Solicitud_Cambio_Plan"].extend(
        [
            {"idsolicitud": 7501, "idcliente": CUENTA_A, "idplanactual": PLAN_PRO,
             "idplansolicitado": PLAN_BASICO, "estado": "Pendiente", "motivo": "coste",
             "idadminaprobador": None, "motivo_rechazo": None,
             "fecha_solicitud": AHORA_MS - 8 * DIA_MS, "fecha_resolucion": None,
             "fecha_actualizacion": AHORA_MS - 8 * DIA_MS},
            {"idsolicitud": 7502, "idcliente": CUENTA_A, "idplanactual": PLAN_BASICO,
             "idplansolicitado": PLAN_PRO, "estado": "Rechazada", "motivo": "crecimiento",
             "idadminaprobador": ADMIN_A, "motivo_rechazo": "mora pendiente",
             "fecha_solicitud": AHORA_MS - 3 * DIA_MS,
             "fecha_resolucion": AHORA_MS - DIA_MS,
             "fecha_actualizacion": AHORA_MS - DIA_MS},
            {"idsolicitud": 7503, "idcliente": CUENTA_B, "idplanactual": PLAN_BASICO,
             "idplansolicitado": PLAN_PRO, "estado": "Pendiente", "motivo": "flota",
             "idadminaprobador": None, "motivo_rechazo": None,
             "fecha_solicitud": AHORA_MS - DIA_MS, "fecha_resolucion": None,
             "fecha_actualizacion": AHORA_MS - DIA_MS},
        ]
    )


@pytest.fixture
def todo_sembrado(
    dos_cuentas, facturas_sembradas, metodos_pago_sembrados, solicitudes_sembradas
):
    return True


def _headers(user_id: int, roles: list[str]) -> dict:
    token = create_access_token(user_id=user_id, roles=roles, session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def cliente_a_headers(mock_pinot, mock_kafka):
    return _headers(ADMIN_A, ["Cliente"])


@pytest.fixture
def cliente_b_headers(mock_pinot, mock_kafka):
    """Su cuenta está dada de baja: **conserva** el acceso a lo suyo (FR-011)."""
    return _headers(ADMIN_B, ["Cliente"])


@pytest.fixture
def sin_cuenta_headers(mock_pinot, mock_kafka):
    return _headers(SIN_CUENTA, ["Cliente"])


@pytest.fixture
def director_estrategia_headers(mock_pinot, mock_kafka):
    return _headers(7810, ["DirectorEstrategia"])


@pytest.fixture
def director_financiero_headers(mock_pinot, mock_kafka):
    return _headers(7811, ["DirectorFinanciero"])
