"""Datos sembrados para los informes tácticos de Partners y API.

**`dos_partners` es el fixture del que depende que este módulo esté probado.**
Con un solo partner con credenciales, filtrar y no filtrar devuelven lo mismo.

Los demás casos protegen defectos concretos:

* una credencial **revocada por el partner** y otra **desactivada en cascada**
  sobre el mismo partner — en `Dim_CredencialAPI` son **indistinguibles**, y esa
  indistinguibilidad es justo lo que L2 no debe disimular;
* credenciales de **pruebas y producción a la vez**, porque activar producción no
  elimina el acceso de pruebas;
* un partner **suspendido**, que conserva el acceso a sus propios listados;
* una **versión de contrato retirada**, que sigue apareciendo;
* un cliente **sin alcance configurado**, que no es acceso ilimitado.

`client_secret_hash` se siembra con un valor reconocible: si aparece en una
respuesta, la prueba de research D3 debe fallar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_PRODUCCION,
    CAMBIO_ACTIVACION_SANDBOX,
    CAMBIO_DESACTIVACION_POR_CASCADA,
    CAMBIO_REACTIVACION,
    CAMBIO_REVOCACION_CREDENCIAL,
    CAMBIO_SUSPENSION_MANUAL,
    EJECUTADO_POR_ADMINISTRADOR,
    EJECUTADO_POR_PARTNER,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    SIN_CREDENCIAL,
    SIN_FECHA_RETIRO,
    SIN_MOTIVO,
    VERSION_RETIRADA,
    VERSION_VIGENTE,
)
from conftest import PINOT_STORE
from core.jwt_utils import create_access_token

#: 2026-08-11T12:00:00Z
AHORA = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
AHORA_MS = int(AHORA.timestamp() * 1000)
DIA_MS = 86_400_000

CUENTA_A = 4401
CUENTA_B = 4402
CUENTA_SIN_ALCANCE = 4403
ADMIN_A = 4501
ADMIN_B = 4502

PARTNER_A = 4601   # producción activa, con credenciales de ambos entornos
PARTNER_B = 4602   # de la otra cuenta
PARTNER_SUSP = 4603  # suspendido, de la cuenta A

SERVICIO = 4701

#: Valor que jamás puede aparecer en una respuesta.
SECRETO = "hash_NO-DEBE-SALIR-NUNCA"


@pytest.fixture
def reloj_fijo():
    return lambda: AHORA_MS


@pytest.fixture
def cuentas_partners(mock_pinot):
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {"idusuario": ADMIN_A, "nombres": "Marta", "apellidos": "Silva",
             "gmail": "marta.silva@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
            {"idusuario": ADMIN_B, "nombres": "Ivan", "apellidos": "Ortega",
             "gmail": "ivan.ortega@tsi.com", "activo": True, "fecha_actualizacion": AHORA_MS},
        ]
    )
    PINOT_STORE["Dim_Cliente"].extend(
        [
            {"idcliente": CUENTA_A, "razon_social": "Integradora Silva S.A.",
             "tipo": "Corporativo", "estado": "Activo", "admin_local_id": ADMIN_A,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
            {"idcliente": CUENTA_B, "razon_social": "Integradora Andina Ltda.",
             "tipo": "Corporativo", "estado": "Activo", "admin_local_id": ADMIN_B,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
            {"idcliente": CUENTA_SIN_ALCANCE, "razon_social": "Sin Alcance S.A.",
             "tipo": "Corporativo", "estado": "Activo", "admin_local_id": 0,
             "fecha_creacion": AHORA_MS, "fecha_actualizacion": AHORA_MS},
        ]
    )
    # El vínculo usuario→cuenta se guarda aquí; `admin_local_id` es solo el
    # respaldo. Sembrar ambos evita que la resolución dependa del respaldo.
    PINOT_STORE["Dim_Usuario_Cliente"].extend(
        [
            {"idusuario": ADMIN_A, "idcliente": CUENTA_A, "activo": True},
            {"idusuario": ADMIN_B, "idcliente": CUENTA_B, "activo": True},
        ]
    )
    PINOT_STORE["Dim_Servicio"].append(
        {"id_servicio": SERVICIO, "nombre": "API de Accidentes", "tipo": "REST",
         "descripcion": "", "activo": True, "fecha_actualizacion": AHORA_MS}
    )


def _partner(pid, *, nombre, idcliente, activo=True, plan="Profesional",
             suspension=None, motivo=None):
    return {
        "idpartner": pid,
        "idcliente": idcliente,
        "nombrepartner": nombre,
        "planapi": plan,
        "contacto_tecnico_nombre": "Contacto Tecnico",
        "contacto_tecnico_gmail": "tecnico@ejemplo.com",
        "fecha_suspension": suspension or "",
        "motivo_suspension": motivo or "",
        "activo": activo,
        "limitellamadasmes": 10000,
        "limitellamadasminuto": 60,
        "sandbox_activado": AHORA_MS - 90 * DIA_MS,
        "sandbox_expiracion": AHORA_MS + 90 * DIA_MS,
        "fecha_actualizacion": AHORA_MS,
    }


def _credencial(cid, *, idpartner, idcliente, entorno, activo=True, nombre="cred",
                expira_en_dias=30):
    return {
        "idcredencial": cid,
        "idpartner": idpartner,
        "idcliente": idcliente,
        # No es un hash inofensivo: con él un partner se autentica.
        "client_secret_hash": SECRETO,
        "entorno": entorno,
        "activo": activo,
        "nombre_credencial": nombre,
        "fecha_creacion": AHORA_MS - 60 * DIA_MS,
        "fecha_actualizacion": AHORA_MS,
        "fecha_expiracion": AHORA_MS + expira_en_dias * DIA_MS,
    }


@pytest.fixture
def dos_partners(mock_pinot, cuentas_partners):
    """Dos cuentas con partners y credenciales a la vez.

    El partner A tiene **credenciales de pruebas y de producción**: activar
    producción no elimina el acceso de pruebas, y el listado debe mostrar ambas.
    """
    PINOT_STORE["Dim_Partner"].extend(
        [
            _partner(PARTNER_A, nombre="Silva Integraciones", idcliente=CUENTA_A),
            _partner(PARTNER_B, nombre="Andina Conecta", idcliente=CUENTA_B),
            _partner(PARTNER_SUSP, nombre="Silva Legacy", idcliente=CUENTA_A,
                     activo=False, suspension="2026-07-01", motivo="impago"),
        ]
    )
    PINOT_STORE["Dim_CredencialAPI"].extend(
        [
            _credencial(4801, idpartner=PARTNER_A, idcliente=CUENTA_A,
                        entorno=ENTORNO_PRODUCCION, nombre="prod-principal",
                        expira_en_dias=10),
            # Coexiste con la de producción.
            _credencial(4802, idpartner=PARTNER_A, idcliente=CUENTA_A,
                        entorno=ENTORNO_SANDBOX, nombre="sandbox-pruebas",
                        expira_en_dias=200),
            # ⚠️ Revocada por el partner: inactiva.
            _credencial(4803, idpartner=PARTNER_A, idcliente=CUENTA_A,
                        entorno=ENTORNO_SANDBOX, activo=False,
                        nombre="revocada", expira_en_dias=300),
            # ⚠️ Desactivada en cascada: inactiva **por otra razón**, y en la
            # tabla es indistinguible de la anterior.
            _credencial(4804, idpartner=PARTNER_SUSP, idcliente=CUENTA_A,
                        entorno=ENTORNO_PRODUCCION, activo=False,
                        nombre="cascada", expira_en_dias=300),
            _credencial(4805, idpartner=PARTNER_B, idcliente=CUENTA_B,
                        entorno=ENTORNO_PRODUCCION, nombre="andina-prod",
                        expira_en_dias=50),
        ]
    )
    PINOT_STORE["Fact_HistorialAccesoPartner"].extend(
        [
            {"idhistorial": 4901, "idpartner": PARTNER_A,
             "idcredencial": SIN_CREDENCIAL, "tipo_cambio": CAMBIO_ACTIVACION_SANDBOX,
             "ejecutado_por": EJECUTADO_POR_ADMINISTRADOR, "motivo": SIN_MOTIVO,
             "estado_anterior": SIN_MOTIVO, "estado_nuevo": "Pruebas activo",
             "fecha_cambio": AHORA_MS - 90 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 90 * DIA_MS},
            {"idhistorial": 4902, "idpartner": PARTNER_A,
             "idcredencial": SIN_CREDENCIAL, "tipo_cambio": CAMBIO_ACTIVACION_PRODUCCION,
             "ejecutado_por": EJECUTADO_POR_ADMINISTRADOR, "motivo": SIN_MOTIVO,
             "estado_anterior": "Pruebas activo", "estado_nuevo": "Producción activa",
             "fecha_cambio": AHORA_MS - 60 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 60 * DIA_MS},
            # ⚠️ Decisión de seguridad del partner.
            {"idhistorial": 4903, "idpartner": PARTNER_A, "idcredencial": 4803,
             "tipo_cambio": CAMBIO_REVOCACION_CREDENCIAL,
             "ejecutado_por": EJECUTADO_POR_PARTNER,
             "motivo": "secreto comprometido", "estado_anterior": "Activo",
             "estado_nuevo": "Activo", "fecha_cambio": AHORA_MS - 20 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 20 * DIA_MS},
            # ⚠️ Consecuencia administrativa de una suspensión. Distinto tipo.
            {"idhistorial": 4904, "idpartner": PARTNER_SUSP, "idcredencial": 4804,
             "tipo_cambio": CAMBIO_DESACTIVACION_POR_CASCADA,
             "ejecutado_por": EJECUTADO_POR_ADMINISTRADOR,
             "motivo": "suspension por impago", "estado_anterior": "Activo",
             "estado_nuevo": "Suspendido", "fecha_cambio": AHORA_MS - 10 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 10 * DIA_MS},
            {"idhistorial": 4905, "idpartner": PARTNER_SUSP,
             "idcredencial": SIN_CREDENCIAL, "tipo_cambio": CAMBIO_SUSPENSION_MANUAL,
             "ejecutado_por": EJECUTADO_POR_ADMINISTRADOR, "motivo": "impago",
             "estado_anterior": "Activo", "estado_nuevo": "Suspendido",
             "fecha_cambio": AHORA_MS - 10 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 10 * DIA_MS},
            # Reactivación **sin motivo**: correcto, no dato faltante.
            {"idhistorial": 4906, "idpartner": PARTNER_B,
             "idcredencial": SIN_CREDENCIAL, "tipo_cambio": CAMBIO_REACTIVACION,
             "ejecutado_por": EJECUTADO_POR_ADMINISTRADOR, "motivo": SIN_MOTIVO,
             "estado_anterior": "Suspendido", "estado_nuevo": "Activo",
             "fecha_cambio": AHORA_MS - 5 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 5 * DIA_MS},
        ]
    )


@pytest.fixture
def contrato_sembrado(mock_pinot, cuentas_partners):
    """Una versión vigente y otra **retirada**, que sigue apareciendo (FR-004)."""
    PINOT_STORE["Dim_VersionContratoAPI"].extend(
        [
            {"idversion": 4851, "id_servicio": SERVICIO, "version": "v2",
             "estado": VERSION_VIGENTE, "spec_url": "https://api.tsi/v2",
             "activo": True, "fecha_publicacion": AHORA_MS - 30 * DIA_MS,
             "fecha_retiro": SIN_FECHA_RETIRO,
             "fecha_actualizacion": AHORA_MS - 30 * DIA_MS},
            {"idversion": 4852, "id_servicio": SERVICIO, "version": "v1",
             "estado": VERSION_RETIRADA, "spec_url": "https://api.tsi/v1",
             "activo": False, "fecha_publicacion": AHORA_MS - 400 * DIA_MS,
             "fecha_retiro": AHORA_MS - 40 * DIA_MS,
             "fecha_actualizacion": AHORA_MS - 40 * DIA_MS},
        ]
    )


@pytest.fixture
def alcance_sembrado(mock_pinot, cuentas_partners):
    """Un cliente con alcance configurado y otro **sin configurar** (FR-023)."""
    PINOT_STORE["Dim_Preferencias_Cliente"].extend(
        [
            {"id_preferencia": 4871, "id_cliente": CUENTA_A,
             "umbrales_alerta": "", "frecuencia_reportes": "mensual",
             "formato_reportes": "PDF", "canales_notificacion": "correo",
             "telefono_sms": "NO-DEBE-SALIR-0999", "zonas_geograficas": "Norte,Centro",
             "destinatarios_reportes": "ops@silva.com", "activo": True,
             "fecha_actualizacion": AHORA_MS},
            # ⚠️ Sin zonas configuradas: **no** es acceso ilimitado.
            {"id_preferencia": 4872, "id_cliente": CUENTA_SIN_ALCANCE,
             "umbrales_alerta": "", "frecuencia_reportes": "",
             "formato_reportes": "", "canales_notificacion": "",
             "telefono_sms": "", "zonas_geograficas": "",
             "destinatarios_reportes": "", "activo": True,
             "fecha_actualizacion": AHORA_MS},
        ]
    )


@pytest.fixture
def todo_sembrado(dos_partners, contrato_sembrado, alcance_sembrado):
    return True


def _headers(user_id: int, roles: list[str]) -> dict:
    token = create_access_token(user_id=user_id, roles=roles, session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def partner_a_informes_headers(mock_pinot, mock_kafka):
    return _headers(ADMIN_A, ["PartnerIntegracion"])


@pytest.fixture
def partner_b_informes_headers(mock_pinot, mock_kafka):
    return _headers(ADMIN_B, ["PartnerIntegracion"])


@pytest.fixture
def gestor_headers(mock_pinot, mock_kafka):
    return _headers(4599, ["DesarrolladorAPIs"])


@pytest.fixture
def director_tecnologico_informes_headers(mock_pinot, mock_kafka):
    return _headers(4598, ["DirectorTecnologico"])
