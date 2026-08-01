"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from unittest.mock import patch

import bcrypt
import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


# --- In-memory Pinot store for tests ---
_INITIAL_PINOT_STORE: dict[str, list[dict]] = {
    "Dim_Usuarios": [
        {
            "idusuario": 1,
            "nombres": "Admin",
            "apellidos": "Sistema",
            "gmail": "admin@tsi.com",
            "identificacion": "1234567890",
            "genero": "M",
            "telefono": "3001234567",
            "fechanacimiento": "1990-01-01",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idusuario": 2,
            "nombres": "Operador",
            "apellidos": "Test",
            "gmail": "operador@tsi.com",
            "identificacion": "0987654321",
            "genero": "F",
            "telefono": "3009876543",
            "fechanacimiento": "1992-05-15",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idusuario": 3,
            "nombres": "Carlos",
            "apellidos": "AdminLocal",
            "gmail": "cliente@tsi.com",
            "identificacion": "1111222233",
            "genero": "M",
            "telefono": "3001112233",
            "fechanacimiento": "1988-03-10",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idusuario": 4,
            "nombres": "Ana",
            "apellidos": "Miembro",
            "gmail": "miembro@tsi.com",
            "identificacion": "4444555566",
            "genero": "F",
            "telefono": "3004445566",
            "fechanacimiento": "1990-08-20",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idusuario": 6,
            "nombres": "Unidad",
            "apellidos": "Test",
            "gmail": "unidad@tsi.com",
            "identificacion": "7777888899",
            "genero": "M",
            "telefono": "3007778899",
            "fechanacimiento": "1991-02-02",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idusuario": 7,
            "nombres": "Técnico",
            "apellidos": "Campo",
            "gmail": "tecnico@tsi.com",
            "identificacion": "6666777788",
            "genero": "M",
            "telefono": "3006667788",
            "fechanacimiento": "1993-04-04",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Dim_Credencial": [
        {
            "idcredencial": 1,
            "idusuario": 1,
            "contrasena": "$2b$04$E0NV5Gj7YvN8qX9mKpL3UeJhZxWvF8nR2kT6yA1bC4dE7fG0hI3jK",
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idcredencial": 2,
            "idusuario": 2,
            "contrasena": "$2b$04$E0NV5Gj7YvN8qX9mKpL3UeJhZxWvF8nR2kT6yA1bC4dE7fG0hI3jK",
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idcredencial": 3,
            "idusuario": 3,
            "contrasena": "$2b$04$E0NV5Gj7YvN8qX9mKpL3UeJhZxWvF8nR2kT6yA1bC4dE7fG0hI3jK",
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idcredencial": 4,
            "idusuario": 4,
            "contrasena": "$2b$04$E0NV5Gj7YvN8qX9mKpL3UeJhZxWvF8nR2kT6yA1bC4dE7fG0hI3jK",
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idcredencial": 6,
            "idusuario": 6,
            "contrasena": "$2b$04$E0NV5Gj7YvN8qX9mKpL3UeJhZxWvF8nR2kT6yA1bC4dE7fG0hI3jK",
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idcredencial": 7,
            "idusuario": 7,
            "contrasena": "$2b$04$E0NV5Gj7YvN8qX9mKpL3UeJhZxWvF8nR2kT6yA1bC4dE7fG0hI3jK",
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Dim_Rol": [
        {
            "idrol": 1,
            "rol": "Administrador",
            "descripcion": "Gestor de identidades",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idrol": 2,
            "rol": "Operador",
            "descripcion": "Operador de emergencias",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idrol": 3,
            "rol": "Cliente",
            "descripcion": "Usuario de cuenta corporativa",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idrol": 4,
            "rol": "Unidad",
            "descripcion": "Unidad de emergencia",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idrol": 5,
            "rol": "Tecnico",
            "descripcion": "Técnico de campo",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idrol": 6,
            "rol": "Despacho",
            "descripcion": "Servicio de despacho",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Dim_Usuario_Rol": [
        {"idusuario": 1, "idrol": 1, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"},
        {"idusuario": 2, "idrol": 2, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"},
        {"idusuario": 3, "idrol": 3, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"},
        {"idusuario": 4, "idrol": 3, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"},
        {"idusuario": 6, "idrol": 4, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"},
        {"idusuario": 7, "idrol": 5, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"},
    ],
    "Fact_Session": [
        {
            "idsession": 1,
            "idusuario": 1,
            "token": "session-token-1",
            "refresh_token": "refresh-token-1",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        },
        {
            "idsession": 3,
            "idusuario": 3,
            "token": "session-token-3",
            "refresh_token": "refresh-token-3",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        },
        {
            "idsession": 4,
            "idusuario": 4,
            "token": "session-token-4",
            "refresh_token": "refresh-token-4",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        },
    ],
    "Dim_Cliente": [
        {
            "idcliente": 1,
            "nombre": "Empresa Demo",
            "razon_social": "Empresa Demo S.A.S.",
            "tipo": "Corporativo",
            "nit_identificacion": "900123456-1",
            "logo_url": None,
            "admin_local_id": 3,
            "estado": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Dim_Preferencias_Cliente": [
        {
            "id_preferencia": 1,
            "id_cliente": 1,
            "umbrales_alerta": "{}",
            "canales_notificacion": "email",
            "telefono_sms": None,
            "zonas_geograficas": "[1]",
            "destinatarios_reportes": "reportes@empresa.com",
            "frecuencia_reportes": "semanal",
            "formato_reportes": "PDF",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Dim_Usuario_Cliente": [
        {"idusuario": 3, "idcliente": 1, "activo": True},
        {"idusuario": 4, "idcliente": 1, "activo": True},
    ],
    "Fact_Onboarding": [],
    "Dim_UsuariosServidor": [],
    "Dim_RolesServidor": [],
    "Dim_UsuariosServidorRolesServidor": [],
    "Dim_RolesServidorRoles": [],
    "Fact_Accidente": [],
    "Fact_AccidenteTipoEstadoAccidente": [],
    "Fact_Despacho": [],
    "Fact_NotificacionDespacho": [],
    "Fact_BajaUnidad": [],
    "Fact_HistorialDespachoUnidad": [],
    "Dim_HistorialUbicacionUnidadEmergencia": [],
    "Dim_ParametrosSeguimiento": [],
    "Dim_ParametrosDespacho": [],
    "Dim_CondadoVecino": [
        {"idcondado": 1, "idcondadovecino": 2},
        {"idcondado": 2, "idcondadovecino": 1},
    ],
    "Dim_NotaAccidente": [],
    "Dim_EvidenciaFoto": [],
    "Dim_ElementoClimaticosAccidente": [],
    "Dim_ElementoFisicoAccidente": [],
    "Dim_Conductor": [],
    "Dim_Vehiculo": [],
    "Fact_Conductor_Accidente": [],
    "Dim_Implicado": [],
    "Dim_PeriodosDias": [
        {
            "idperiododia": 1,
            "amaneceranochecer": "Mañana",
            "activo": True,
        },
        {
            "idperiododia": 2,
            "amaneceranochecer": "Tarde",
            "activo": True,
        },
        {
            "idperiododia": 3,
            "amaneceranochecer": "Noche",
            "activo": True,
        },
    ],
    "Dim_EstadosClimas": [
        {"idestadoclima": 1, "condicionclima": "Despejado", "activo": True},
        {"idestadoclima": 2, "condicionclima": "Lluvia", "activo": True},
        {"idestadoclima": 3, "condicionclima": "Niebla", "activo": True},
    ],
    "Dim_Elementos_Fisicos": [
        {"idelementofisico": 1, "elementofisico": "Semáforo", "activo": True},
        {"idelementofisico": 2, "elementofisico": "Señal de Pare", "activo": True},
        {"idelementofisico": 3, "elementofisico": "Reductor", "activo": True},
    ],
    "Dim_Estado_Conductor": [
        {
            "idestadoconductor": idx,
            "estadosobriedad": estadosobriedad,
            "nivelatencion": nivelatencion,
            "condicionfisica": condicionfisica,
            "usoseguridad": usoseguridad,
            "activo": True,
        }
        for idx, (estadosobriedad, nivelatencion, condicionfisica, usoseguridad) in enumerate(
            (
                (s, a, f, u)
                for s in (True, False)
                for a in (True, False)
                for f in (True, False)
                for u in (True, False)
            ),
            start=1,
        )
    ],
    "Dim_TipoReportado": [
        {"idtiporeportado": 1, "tiporeportado": "Llamada telefónica", "activo": True},
        {"idtiporeportado": 2, "tiporeportado": "App móvil", "activo": True},
        {"idtiporeportado": 3, "tiporeportado": "Integración API", "activo": True},
        {"idtiporeportado": 4, "tiporeportado": "Cámara de tráfico", "activo": True},
    ],
    "Dim_ReferenciaEstacion": [
        {
            "idreferenciaestacion": 1,
            "codigoaeropuerto": "MEX",
            "zonahoraria": "America/Mexico_City",
            "activo": True,
        },
        {
            "idreferenciaestacion": 2,
            "codigoaeropuerto": "CUN",
            "zonahoraria": "America/Cancun",
            "activo": True,
        },
        {
            "idreferenciaestacion": 3,
            "codigoaeropuerto": "GDL",
            "zonahoraria": "America/Mexico_City",
            "activo": True,
        },
        {
            "idreferenciaestacion": 5,
            "codigoaeropuerto": "TIJ",
            "zonahoraria": "America/Tijuana",
            "activo": True,
        },
    ],
    "Fact_HistorialEstadoUnidad": [],
    "Dim_UnidadEmergencia": [
        {
            "idunidademergencia": 1,
            "idusuario": 6,
            "unidademergencia": "Ambulancia 01",
            "idtipounidad": 1,
            "idcondado": 1,
            "latitud": 19.43,
            "longitud": -99.13,
            "activo": True,
            "fecha_actualizacion": 1704067200000,
        },
        {
            "idunidademergencia": 2,
            "idusuario": 99,
            "unidademergencia": "Grúa 02",
            "idtipounidad": 2,
            "idcondado": 2,
            "latitud": 19.44,
            "longitud": -99.14,
            "activo": True,
            "fecha_actualizacion": 1704067200000,
        },
    ],
    "Dim_EstadoUnidadEmergencia": [
        {"idestadounidademergencia": 1, "estado": "Activa", "activo": True},
        {"idestadounidademergencia": 2, "estado": "Ocupada", "activo": True},
        {"idestadounidademergencia": 3, "estado": "Fuera de servicio", "activo": True},
        {"idestadounidademergencia": 4, "estado": "En Misión", "activo": True},
    ],
    "Dim_Calle": [
        {"idcalle": 1, "idciudad": 1, "nombre": "Av. Reforma", "calle": "Av. Reforma", "activo": True},
        {
            "idcalle": 99,
            "idciudad": 99,
            "nombre": "Fuera de cobertura",
            "calle": "Fuera de cobertura",
            "activo": True,
        },
    ],
    "Dim_Ciudad": [
        {
            "idciudad": 1,
            "idcondado": 1,
            "nombre": "Ciudad de México",
            "ciudad": "Ciudad de México",
            "activo": True,
        },
        {
            "idciudad": 99,
            "idcondado": 99,
            "nombre": "Sin cobertura",
            "ciudad": "Sin cobertura",
            "activo": True,
        },
    ],
    "Dim_Condado": [
        {"idcondado": 1, "idestadoregion": 1, "idestado": 1, "condado": "Cuauhtémoc", "activo": True},
        {"idcondado": 2, "idestadoregion": 1, "idestado": 1, "condado": "Benito Juárez", "activo": True},
        {"idcondado": 99, "idestadoregion": 99, "idestado": 99, "condado": "Sin cobertura", "activo": True},
    ],
    "Dim_EstadoRegion": [
        {"idestadoregion": 1, "nombre": "CDMX"},
        {"idestadoregion": 99, "nombre": "Sin producción"},
    ],
    "Dim_Pais": [
        {"idpais": 1, "pais": "México", "activo": True},
    ],
    "Dim_Estado": [
        {"idestado": 1, "idpais": 1, "estado": "Ciudad de México", "activo": True},
        {"idestado": 2, "idpais": 1, "estado": "Jalisco", "activo": True},
    ],
    "Dim_RegionOperativa": [
        {
            "idregionoperativa": 1,
            "idestado": 1,
            "estadoregion": "Producción",
            "activo": True,
            "nombreregion": "Centro",
        }
    ],
    "Dim_RegionOperativaEstadoRegion": [
        {"idregionoperativa": 1, "idestadoregion": 1},
    ],
    "Dim_ValidacionRegion": [],
    "Dim_Plan": [
        {
            "idplan": 1,
            "nombre": "Básico",
            "nivel": "Básico",
            "limites": '{"unidades_max": 5, "usuarios_max": 3, "api_calls_mes": 1000}',
            "activo": True,
            "precio": 49.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idplan": 2,
            "nombre": "Profesional",
            "nivel": "Profesional",
            "limites": '{"unidades_max": 25, "usuarios_max": 10, "api_calls_mes": 10000}',
            "activo": True,
            "precio": 149.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idplan": 3,
            "nombre": "Empresarial",
            "nivel": "Empresarial",
            "limites": '{"unidades_max": 100, "usuarios_max": 50, "api_calls_mes": 100000}',
            "activo": True,
            "precio": 399.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idplan": 4,
            "nombre": "Legacy Off",
            "nivel": "Básico",
            "limites": '{"unidades_max": 1, "usuarios_max": 1, "api_calls_mes": 10}',
            "activo": False,
            "precio": 9.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Fact_Suscripcion": [
        {
            "id_suscripcion": 1,
            "idcliente": 1,
            "idplan": 1,
            "estado": "Activa",
            "activo": True,
            "renovacionautomatica": True,
            "motivocancelacion": None,
            "fechacancelacion": None,
            "precio": 49.0,
            "fecha_inicio": 1704067200000,
            "fecha_fin": 1735689600000,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Dim_MetodoPago": [],
    "Fact_Factura": [],
    "Fact_Solicitud_Cambio_Plan": [],
    "Dim_Servicio": [
        {
            "id_servicio": 1,
            "nombre": "API Despacho",
            "tipo": "api",
            "descripcion": "Endpoints de despacho inteligente",
            "activo": True,
        },
        {
            "id_servicio": 2,
            "nombre": "API Registro de accidentes",
            "tipo": "api",
            "descripcion": "CU-O21 y consulta de casos",
            "activo": True,
        },
        {
            "id_servicio": 3,
            "nombre": "Portal Cliente",
            "tipo": "portal",
            "descripcion": "Acceso web corporativo",
            "activo": True,
        },
    ],
    "Dim_Estado_Soporte": [
        {"id_estado_soporte": 1, "nombre": "Abierto", "descripcion": "Ticket registrado", "activo": True},
        {"id_estado_soporte": 2, "nombre": "Pendiente_de_clasificacion", "descripcion": "Sin clasificar", "activo": True},
        {"id_estado_soporte": 3, "nombre": "En_progreso", "descripcion": "En atención", "activo": True},
        {"id_estado_soporte": 4, "nombre": "Escalado", "descripcion": "Escalado", "activo": True},
        {"id_estado_soporte": 5, "nombre": "Resuelto", "descripcion": "Resuelto", "activo": True},
        {"id_estado_soporte": 6, "nombre": "Cerrado", "descripcion": "Cerrado", "activo": True},
        {"id_estado_soporte": 7, "nombre": "Reabierto", "descripcion": "Reabierto", "activo": True},
    ],
    "Dim_SLAConfig": [
        {
            "idslaconfig": 1,
            "idplan": 1,
            "tipoincidencia": "tecnica",
            "prioridad": "alta",
            "activo": True,
            "tiemporespuestamax": 3600,
            "tiemporesolucionmax": 86400,
            "fechavigenciadesde": 1704067200000,
            "fechavigenciahasta": None,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idslaconfig": 2,
            "idplan": 1,
            "tipoincidencia": "emergencia_activa",
            "prioridad": "crítico",
            "activo": True,
            "tiemporespuestamax": 60,
            "tiemporesolucionmax": 3600,
            "fechavigenciadesde": 1704067200000,
            "fechavigenciahasta": None,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idslaconfig": 3,
            "idplan": 1,
            "tipoincidencia": "acceso",
            "prioridad": "media",
            "activo": True,
            "tiemporespuestamax": 7200,
            "tiemporesolucionmax": 172800,
            "fechavigenciadesde": 1704067200000,
            "fechavigenciahasta": None,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idslaconfig": 4,
            "idplan": 1,
            "tipoincidencia": "consulta_funcional",
            "prioridad": "baja",
            "activo": True,
            "tiemporespuestamax": 14400,
            "tiemporesolucionmax": 259200,
            "fechavigenciadesde": 1704067200000,
            "fechavigenciahasta": None,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
    ],
    "Fact_Reclamo": [],
    "Fact_Historial_Ticket": [],
    "Fact_ArchivosAdjuntosReclamos": [],
}

# Pre-compute bcrypt hash for "password123" at import (rounds=4 for test speed)
_TEST_PASSWORD_HASH = bcrypt.hashpw(b"password123", bcrypt.gensalt(rounds=4)).decode()
for _cred in _INITIAL_PINOT_STORE["Dim_Credencial"]:
    _cred["contrasena"] = _TEST_PASSWORD_HASH

# Commercial CRM seed data.
_INITIAL_PINOT_STORE["Dim_Usuarios"].extend([
    {"idusuario": 20, "nombres": "Gerente", "apellidos": "Ventas", "gmail": "gerente.ventas@tsi.com", "activo": True},
    {"idusuario": 21, "nombres": "Gerente", "apellidos": "Público", "gmail": "gerente.publico@tsi.com", "activo": True},
])
_INITIAL_PINOT_STORE["Dim_Credencial"].extend([
    {"idcredencial": 20, "idusuario": 20, "contrasena": _TEST_PASSWORD_HASH, "estadocredencial": "Activo"},
    {"idcredencial": 21, "idusuario": 21, "contrasena": _TEST_PASSWORD_HASH, "estadocredencial": "Activo"},
])
_INITIAL_PINOT_STORE["Dim_Rol"].extend([
    {"idrol": 7, "rol": "GerenteVentas", "activo": True},
    {"idrol": 8, "rol": "GerenteCuentasPublicas", "activo": True},
    {"idrol": 9, "rol": "Sistema", "activo": True},
    {
        "idrol": 10,
        "rol": "SupervisorSoporte",
        "descripcion": "Receptor de escalado automático SLA (RN-TIC-005)",
        "activo": True,
    },
])
_INITIAL_PINOT_STORE["Dim_Usuario_Rol"].extend([
    {"idusuario": 20, "idrol": 7},
    {"idusuario": 21, "idrol": 8},
    {"idusuario": 2, "idrol": 10},  # Operador también actúa como supervisor SLA en tests
])
_INITIAL_PINOT_STORE.update({
    "Dim_Prospecto": [],
    "Fact_Asignacion": [],
    "Fact_Pipeline": [],
    "Fact_Interaccion_Demo": [],
    "Fact_NotificacionVentas": [],
})

PINOT_STORE: dict[str, list[dict]] = {}


def _reset_pinot_store() -> None:
    import copy

    PINOT_STORE.clear()
    for table, rows in _INITIAL_PINOT_STORE.items():
        PINOT_STORE[table] = copy.deepcopy(rows)


_reset_pinot_store()


def _pinot_query_impl(sql: str, params: dict | None = None) -> list[dict]:
    """Route SQL queries to in-memory store."""
    params = params or {}
    sql_upper = sql.upper().replace("\n", " ").strip()

    # --- MAX id queries (must precede generic id lookups) ---
    if "MAX(IDPROSPECTO)" in sql_upper:
        rows = PINOT_STORE["Dim_Prospecto"]; return [{"max_id": max((r["idprospecto"] for r in rows), default=0)}]
    if "MAX(IDASIGNACION)" in sql_upper:
        rows = PINOT_STORE["Fact_Asignacion"]; return [{"max_id": max((r["idasignacion"] for r in rows), default=0)}]
    if "MAX(ID_TRANSICION)" in sql_upper:
        rows = PINOT_STORE["Fact_Pipeline"]; return [{"max_id": max((r["id_transicion"] for r in rows), default=0)}]
    if "MAX(IDINTERACCION)" in sql_upper:
        rows = PINOT_STORE["Fact_Interaccion_Demo"]
        return [{"max_id": max((r["idinteraccion"] for r in rows), default=0)}]
    if "MAX(IDNOTIFICACION)" in sql_upper:
        rows = PINOT_STORE["Fact_NotificacionVentas"]
        return [{"max_id": max((r["idnotificacion"] for r in rows), default=0)}]
    # --- Dim_Plan (public catalog read — RF-CPP-000 / billing) ---
    if "FROM DIM_PLAN" in sql_upper:
        if "MAX(IDPLAN)" in sql_upper:
            rows = PINOT_STORE["Dim_Plan"]
            return [{"max_id": max((r["idplan"] for r in rows), default=0)}]
        rows = list(PINOT_STORE["Dim_Plan"])
        if "IDPLAN =" in sql_upper:
            rows = [r for r in rows if r.get("idplan") == params.get("idplan")]
        if "IDPLAN >" in sql_upper:
            rows = [r for r in rows if int(r.get("idplan") or 0) > int(params.get("cursor", 0))]
        if "ACTIVO = TRUE" in sql_upper or "ACTIVO = %(ACTIVO)S" in sql_upper:
            want = params.get("activo", True)
            rows = [r for r in rows if r.get("activo") is want]
        elif "ACTIVO =" in sql_upper:
            want = params.get("activo", True)
            rows = [r for r in rows if bool(r.get("activo")) is bool(want)]
        if "NIVEL =" in sql_upper:
            rows = [r for r in rows if r.get("nivel") == params.get("nivel")]
        if "LIKE" in sql_upper:
            needle = str(params.get("q") or "").lower().strip("%")
            rows = [r for r in rows if needle in str(r.get("nombre") or "").lower()]
        rows.sort(key=lambda r: int(r.get("idplan") or 0))
        if "LIMIT" in sql_upper and "limit" in params:
            rows = rows[: int(params["limit"])]
        return rows
    # --- Billing tables ---
    if "MAX(IDMETODOPAGO)" in sql_upper:
        rows = PINOT_STORE["Dim_MetodoPago"]
        return [{"max_id": max((r["idmetodopago"] for r in rows), default=0)}]
    if "MAX(ID_SUSCRIPCION)" in sql_upper:
        rows = PINOT_STORE["Fact_Suscripcion"]
        return [{"max_id": max((r["id_suscripcion"] for r in rows), default=0)}]
    if "MAX(IDSOLICITUD)" in sql_upper:
        rows = PINOT_STORE["Fact_Solicitud_Cambio_Plan"]
        return [{"max_id": max((r["idsolicitud"] for r in rows), default=0)}]
    if "FROM DIM_METODOPAGO" in sql_upper:
        rows = list(PINOT_STORE["Dim_MetodoPago"])
        if "IDMETODOPAGO =" in sql_upper:
            rows = [r for r in rows if r.get("idmetodopago") == params.get("id")]
        return rows
    if "FROM FACT_FACTURA" in sql_upper:
        rows = list(PINOT_STORE["Fact_Factura"])
        if "ID_FACTURA =" in sql_upper:
            rows = [r for r in rows if r.get("id_factura") == params.get("id")]
        return rows
    if "FROM FACT_SOLICITUD_CAMBIO_PLAN" in sql_upper:
        rows = list(PINOT_STORE["Fact_Solicitud_Cambio_Plan"])
        if "IDSOLICITUD =" in sql_upper:
            rows = [r for r in rows if r.get("idsolicitud") == params.get("id")]
        return rows
    # --- Commercial CRM tables ---
    if "FROM DIM_PROSPECTO" in sql_upper:
        rows = list(PINOT_STORE["Dim_Prospecto"])
        if "GMAIL =" in sql_upper: rows = [r for r in rows if r.get("gmail") == params.get("gmail")]
        if "IDPROSPECTO =" in sql_upper: rows = [r for r in rows if r.get("idprospecto") == params.get("id")]
        if "IDUSUARIO =" in sql_upper: rows = [r for r in rows if r.get("idusuario") == params.get("owner_id", params.get("id"))]
        if "ACTIVO = TRUE" in sql_upper: rows = [r for r in rows if r.get("activo") is True]
        if "ETAPA_ACTUAL =" in sql_upper: rows = [r for r in rows if r.get("etapa_actual") == params.get("etapa")]
        if "IDPROSPECTO >" in sql_upper: rows = [r for r in rows if r.get("idprospecto", 0) > int(params.get("cursor", 0))]
        if "COUNT(*)" in sql_upper: return [{"count": len(rows)}]
        return rows[:params.get("limit", len(rows))]
    if "FROM FACT_ASIGNACION" in sql_upper:
        return [r for r in PINOT_STORE["Fact_Asignacion"] if r.get("idprospecto") == params.get("id")]
    if "FROM FACT_PIPELINE" in sql_upper:
        return [r for r in PINOT_STORE["Fact_Pipeline"] if r.get("id_prospecto") == params.get("id")]
    if "FROM FACT_INTERACCION_DEMO" in sql_upper:
        rows = list(PINOT_STORE["Fact_Interaccion_Demo"])
        if "IDPROSPECTO =" in sql_upper:
            rows = [r for r in rows if r.get("idprospecto") == params.get("id")]
        if "TIPO_EVENTO =" in sql_upper:
            rows = [r for r in rows if r.get("tipo_evento") == params.get("tipo")]
        if "TIMESTAMP_EVENTO >=" in sql_upper:
            rows = [r for r in rows if int(r.get("timestamp_evento") or 0) >= int(params.get("since", 0))]
        return rows
    if "FROM FACT_NOTIFICACIONVENTAS" in sql_upper:
        rows = list(PINOT_STORE["Fact_NotificacionVentas"])
        if "ID_PROSPECTO =" in sql_upper and "REGLADISPARADA" in sql_upper:
            rows = [
                r for r in rows
                if r.get("id_prospecto") == params.get("idp")
                and r.get("regladisparada") == params.get("regla")
                and int(params.get("start", 0)) <= int(r.get("fechahoranotificacion") or 0) < int(params.get("end", 0))
            ]
            if "COUNT(*)" in sql_upper:
                return [{"count": len(rows)}]
        if "IDUSUARIOGERENTENOTIFICADO =" in sql_upper:
            rows = [r for r in rows if r.get("idusuariogerentenotificado") == params.get("uid")]
        if "REGLADISPARADA =" in sql_upper and "ID_PROSPECTO =" not in sql_upper:
            rows = [r for r in rows if r.get("regladisparada") == params.get("regla")]
        if "ID_PROSPECTO =" in sql_upper and "REGLADISPARADA" not in sql_upper:
            rows = [r for r in rows if r.get("id_prospecto") == params.get("idp")]
        if "IDNOTIFICACION >" in sql_upper:
            rows = [r for r in rows if int(r.get("idnotificacion") or 0) > int(params.get("cursor", 0))]
        if "COUNT(*)" in sql_upper:
            return [{"count": len(rows)}]
        limit = int(params.get("limit", len(rows)))
        return rows[:limit]
    if "JOIN DIM_USUARIO_ROL" in sql_upper and "GERENTE" in str(params.get("role", "")).upper():
        wanted = next((r["idrol"] for r in PINOT_STORE["Dim_Rol"] if r.get("rol") == params["role"]), None)
        ids = {r["idusuario"] for r in PINOT_STORE["Dim_Usuario_Rol"] if r["idrol"] == wanted}
        return [{"idusuario": u["idusuario"]} for u in PINOT_STORE["Dim_Usuarios"] if u["idusuario"] in ids and u.get("activo")]
    if "MAX(IDUSUARIO)" in sql_upper:
        ids = [u["idusuario"] for u in PINOT_STORE["Dim_Usuarios"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDCREDENCIAL)" in sql_upper:
        ids = [c["idcredencial"] for c in PINOT_STORE["Dim_Credencial"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDROL)" in sql_upper and "ROLSERVIDOR" not in sql_upper:
        ids = [r["idrol"] for r in PINOT_STORE["Dim_Rol"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDSESSION)" in sql_upper:
        ids = [s["idsession"] for s in PINOT_STORE["Fact_Session"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDUSUARIOSSERVIDOR)" in sql_upper:
        ids = [u["idusuariosservidor"] for u in PINOT_STORE["Dim_UsuariosServidor"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDROLSERVIDOR)" in sql_upper:
        ids = [r["idrolservidor"] for r in PINOT_STORE["Dim_RolesServidor"]]
        return [{"max_id": max(ids) if ids else 0}]

    if "MAX(IDROLSERVIDOR)" in sql_upper:
        ids = [r["idrolservidor"] for r in PINOT_STORE["Dim_RolesServidor"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDCLIENTE)" in sql_upper:
        ids = [c["idcliente"] for c in PINOT_STORE["Dim_Cliente"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(ID_ONBOARDING)" in sql_upper:
        ids = [o["id_onboarding"] for o in PINOT_STORE["Fact_Onboarding"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(ID_PREFERENCIA)" in sql_upper:
        ids = [p["id_preferencia"] for p in PINOT_STORE["Dim_Preferencias_Cliente"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDACCIDENTETIPOESTADOACCIDENTE)" in sql_upper:
        ids = [
            r["idaccidentetipoestadoaccidente"]
            for r in PINOT_STORE["Fact_AccidenteTipoEstadoAccidente"]
        ]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDEVIDENCIAFOTO)" in sql_upper:
        ids = [r["idevidenciafoto"] for r in PINOT_STORE["Dim_EvidenciaFoto"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDNOTAACCIDENTES)" in sql_upper:
        ids = [r["idnotaaccidentes"] for r in PINOT_STORE["Dim_NotaAccidente"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDELEMENTOSFISICOSACCIDENTE)" in sql_upper:
        ids = [
            r["idelementosfisicosaccidente"]
            for r in PINOT_STORE["Dim_ElementoFisicoAccidente"]
        ]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDCONDUCTOR)" in sql_upper and "IDCONDUCTORACCIDENTE" not in sql_upper:
        ids = [r["idconductor"] for r in PINOT_STORE["Dim_Conductor"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDVEHICULO)" in sql_upper:
        ids = [r["idvehiculo"] for r in PINOT_STORE["Dim_Vehiculo"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDCONDUCTORACCIDENTE)" in sql_upper:
        ids = [r["idconductoraccidente"] for r in PINOT_STORE["Fact_Conductor_Accidente"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDIMPLICADO)" in sql_upper:
        ids = [r["idimplicado"] for r in PINOT_STORE["Dim_Implicado"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDHISTORIALESTADOSUNIDADESEMERGENCIAS)" in sql_upper:
        ids = [
            r["idhistorialestadosunidadesemergencias"]
            for r in PINOT_STORE["Fact_HistorialEstadoUnidad"]
        ]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDDESPACHO)" in sql_upper:
        ids = [r["iddespacho"] for r in PINOT_STORE["Fact_Despacho"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDNOTIFICACIONDESPACHO)" in sql_upper:
        ids = [r["idnotificaciondespacho"] for r in PINOT_STORE["Fact_NotificacionDespacho"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDHISTORIALDESPACHOUNIDAD)" in sql_upper:
        ids = [
            r["idhistorialdespachounidad"]
            for r in PINOT_STORE["Fact_HistorialDespachoUnidad"]
        ]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDUNIDADEMERGENCIA)" in sql_upper:
        ids = [r["idunidademergencia"] for r in PINOT_STORE["Dim_UnidadEmergencia"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDBAJAUNIDAD)" in sql_upper:
        ids = [r["idbajaunidad"] for r in PINOT_STORE["Fact_BajaUnidad"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDREGIONOPERATIVA)" in sql_upper:
        ids = [r["idregionoperativa"] for r in PINOT_STORE["Dim_RegionOperativa"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDVALIDACIONREGION)" in sql_upper:
        ids = [r["idvalidacionregion"] for r in PINOT_STORE["Dim_ValidacionRegion"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDREGIONOPERATIVAESTADOREGION)" in sql_upper:
        ids = [
            r.get("idregionoperativaestadoregion", 0)
            for r in PINOT_STORE["Dim_RegionOperativaEstadoRegion"]
        ]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDHISTORIALUBICACION)" in sql_upper:
        ids = [
            r["idhistorialubicacion"]
            for r in PINOT_STORE["Dim_HistorialUbicacionUnidadEmergencia"]
        ]
        return [{"max_id": max(ids) if ids else 0}]

    # --- incorporacion-regional: Dim_RegionOperativa / Dim_ValidacionRegion ---
    # (deben ir antes de los bloques de catálogo geográfico en cascada más abajo,
    # porque estos usan variantes "IN" que son superset-substring de los "=" existentes)
    if "FROM DIM_REGIONOPERATIVA " in sql_upper and "WHERE IDREGIONOPERATIVA >" in sql_upper:
        cursor = int(params.get("cursor", 0))
        return [
            r for r in PINOT_STORE["Dim_RegionOperativa"] if r["idregionoperativa"] > cursor
        ]
    if "FROM DIM_REGIONOPERATIVA " in sql_upper and "WHERE IDREGIONOPERATIVA =" in sql_upper:
        rid = params.get("idregionoperativa")
        return [r for r in PINOT_STORE["Dim_RegionOperativa"] if r["idregionoperativa"] == rid]

    if "FROM DIM_VALIDACIONREGION" in sql_upper and "WHERE IDREGIONOPERATIVA" in sql_upper:
        rid = params.get("idregionoperativa")
        return [
            r for r in PINOT_STORE["Dim_ValidacionRegion"] if r["idregionoperativa"] == rid
        ]

    if "FROM DIM_REGIONOPERATIVAESTADOREGION" in sql_upper and "WHERE IDREGIONOPERATIVA" in sql_upper:
        rid = params.get("idregionoperativa")
        return [
            {"idestadoregion": link["idestadoregion"]}
            for link in PINOT_STORE["Dim_RegionOperativaEstadoRegion"]
            if link["idregionoperativa"] == rid
        ]

    if "FROM DIM_CONDADO" in sql_upper and "WHERE IDESTADO IN" in sql_upper:
        idsestado = params.get("idsestado") or []
        return [
            {"idcondado": c["idcondado"]}
            for c in PINOT_STORE["Dim_Condado"]
            if c["idestado"] in idsestado
        ]

    if "FROM DIM_CIUDAD" in sql_upper and "WHERE IDCONDADO IN" in sql_upper:
        idscondado = params.get("idscondado") or []
        return [
            {"idciudad": c["idciudad"]}
            for c in PINOT_STORE["Dim_Ciudad"]
            if c["idcondado"] in idscondado
        ]

    if "FROM DIM_CALLE" in sql_upper and "WHERE IDCIUDAD IN" in sql_upper:
        idsciudad = params.get("idsciudad") or []
        return [
            {"idcalle": c["idcalle"]}
            for c in PINOT_STORE["Dim_Calle"]
            if c["idciudad"] in idsciudad
        ]

    if "FROM FACT_ACCIDENTE" in sql_upper and "WHERE IDCALLE IN" in sql_upper:
        idscalle = params.get("idscalle") or []
        return [
            a for a in PINOT_STORE["Fact_Accidente"]
            if a.get("idcalle") in idscalle and a.get("activo") is True
        ]

    # --- Dim_Cliente ---
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE NIT_IDENTIFICACION" in sql_upper:
        nit = params.get("nit")
        rows = [c for c in PINOT_STORE["Dim_Cliente"] if c["nit_identificacion"] == nit]
        if "RECHAZADO_ANULADO" in sql_upper or "<>" in sql_upper or "!=" in sql_upper:
            rows = [c for c in rows if c.get("estado") != "Rechazado_Anulado"]
        return rows
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE ADMIN_LOCAL_ID" in sql_upper:
        admin_id = params.get("admin_local_id")
        rows = [
            c for c in PINOT_STORE["Dim_Cliente"] if c.get("admin_local_id") == admin_id
        ]
        if "RECHAZADO_ANULADO" in sql_upper or "<>" in sql_upper or "!=" in sql_upper:
            rows = [c for c in rows if c.get("estado") != "Rechazado_Anulado"]
        return rows
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE IDCLIENTE" in sql_upper:
        cid = params.get("idcliente")
        return [c for c in PINOT_STORE["Dim_Cliente"] if c["idcliente"] == cid]
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE ESTADO" in sql_upper:
        estado = params.get("estado")
        return [c for c in PINOT_STORE["Dim_Cliente"] if c.get("estado") == estado]

    if "FROM DIM_CLIENTE" in sql_upper and "SELECT *" in sql_upper:
        return list(PINOT_STORE["Dim_Cliente"])

    # --- Fact_Onboarding ---
    if "FROM FACT_ONBOARDING" in sql_upper and "WHERE ID_CLIENTE" in sql_upper:
        cid = params.get("id_cliente")
        if "AND ETAPA" in sql_upper:
            etapa = params.get("etapa")
            return [
                o for o in PINOT_STORE["Fact_Onboarding"]
                if o["id_cliente"] == cid and o["etapa"] == etapa
            ]
        return [o for o in PINOT_STORE["Fact_Onboarding"] if o["id_cliente"] == cid]

    # --- Dim_Preferencias_Cliente ---
    if "FROM DIM_PREFERENCIAS_CLIENTE" in sql_upper and "WHERE ID_CLIENTE" in sql_upper:
        cid = params.get("id_cliente")
        return [p for p in PINOT_STORE["Dim_Preferencias_Cliente"] if p["id_cliente"] == cid]
    if "FROM DIM_PREFERENCIAS_CLIENTE" in sql_upper and "WHERE ID_PREFERENCIA" in sql_upper:
        pid = params.get("id_preferencia")
        return [p for p in PINOT_STORE["Dim_Preferencias_Cliente"] if p["id_preferencia"] == pid]

    # --- Dim_Usuario_Cliente ---
    if "FROM DIM_USUARIO_CLIENTE" in sql_upper and "WHERE IDCLIENTE" in sql_upper:
        cid = params.get("idcliente")
        return [
            m for m in PINOT_STORE["Dim_Usuario_Cliente"]
            if m["idcliente"] == cid and m.get("activo", True)
        ]
    if "FROM DIM_USUARIO_CLIENTE" in sql_upper and "SELECT IDCLIENTE" in sql_upper:
        uid = params.get("idusuario")
        return [
            {"idcliente": m["idcliente"]}
            for m in PINOT_STORE["Dim_Usuario_Cliente"]
            if m["idusuario"] == uid and m.get("activo", True)
        ]
    if "FROM DIM_USUARIO_CLIENTE" in sql_upper and "WHERE IDUSUARIO" in sql_upper:
        uid = params.get("idusuario")
        cid = params.get("idcliente")
        if cid is None:
            return [
                m for m in PINOT_STORE["Dim_Usuario_Cliente"]
                if m["idusuario"] == uid and m.get("activo", True)
            ]
        return [
            m for m in PINOT_STORE["Dim_Usuario_Cliente"]
            if m["idusuario"] == uid and m["idcliente"] == cid and m.get("activo", True)
        ]

    # --- Role/permission lookups (no JOIN, two sequential queries) ---
    if "FROM DIM_USUARIO_ROL" in sql_upper and "WHERE IDROL" in sql_upper:
        rid = params.get("idrol")
        return [
            {"idusuario": ur["idusuario"]}
            for ur in PINOT_STORE["Dim_Usuario_Rol"]
            if ur["idrol"] == rid
        ]

    if "FROM DIM_USUARIO_ROL" in sql_upper and "WHERE IDUSUARIO" in sql_upper:
        uid = params.get("idusuario")
        return [{"idrol": ur["idrol"]} for ur in PINOT_STORE["Dim_Usuario_Rol"] if ur["idusuario"] == uid]

    if "FROM DIM_ROL" in sql_upper and "IDROL IN" in sql_upper:
        role_ids = params.get("role_ids") or []
        return [{"rol": r["rol"]} for r in PINOT_STORE["Dim_Rol"] if r["idrol"] in role_ids and r["activo"]]

    if "FROM DIM_USUARIOSSERVIDORROLESSERVIDOR" in sql_upper and "WHERE IDUSUARIOSSERVIDOR" in sql_upper:
        sid = params.get("id")
        return [
            {"idrolservidor": a["idrolservidor"]}
            for a in PINOT_STORE["Dim_UsuariosServidorRolesServidor"]
            if a["idusuariosservidor"] == sid
        ]

    if "FROM DIM_ROLESSERVIDOR" in sql_upper and "IDROLSERVIDOR IN" in sql_upper:
        role_ids = params.get("role_ids") or []
        return [
            {"rolservidor": r["rolservidor"]}
            for r in PINOT_STORE["Dim_RolesServidor"]
            if r["idrolservidor"] in role_ids
        ]

    # --- Single-row lookups (WHERE ... LIMIT 1) ---
    if "FROM DIM_USUARIOS" in sql_upper and "WHERE GMAIL" in sql_upper:
        gmail = params.get("gmail")
        return [u for u in PINOT_STORE["Dim_Usuarios"] if u["gmail"] == gmail]

    if "FROM DIM_USUARIOS" in sql_upper and "WHERE IDUSUARIO" in sql_upper:
        uid = params.get("idusuario")
        return [u for u in PINOT_STORE["Dim_Usuarios"] if u["idusuario"] == uid]

    if "FROM DIM_CREDENCIAL" in sql_upper:
        uid = params.get("idusuario")
        return [c for c in PINOT_STORE["Dim_Credencial"] if c["idusuario"] == uid]

    if "FROM DIM_ROL" in sql_upper and "WHERE ROL" in sql_upper:
        rol = params.get("rol")
        return [r for r in PINOT_STORE["Dim_Rol"] if r["rol"] == rol]

    if "FROM DIM_ROL" in sql_upper and "WHERE IDROL" in sql_upper:
        rid = params.get("idrol")
        return [r for r in PINOT_STORE["Dim_Rol"] if r["idrol"] == rid]

    if "FROM FACT_SESSION" in sql_upper and "WHERE IDSESSION" in sql_upper:
        sid = params.get("idsession")
        return [s for s in PINOT_STORE["Fact_Session"] if s["idsession"] == sid]

    if "FROM FACT_SESSION" in sql_upper and "WHERE IDUSUARIO" in sql_upper:
        uid = params.get("idusuario")
        return [
            s for s in PINOT_STORE["Fact_Session"]
            if s["idusuario"] == uid and s["estadosession"] == "Inicio sesion"
        ]

    if "FROM DIM_USUARIOSSERVIDOR" in sql_upper and "WHERE IDUSUARIOSSERVIDOR" in sql_upper:
        sid = params.get("id")
        return [u for u in PINOT_STORE["Dim_UsuariosServidor"] if u["idusuariosservidor"] == sid]

    if "FROM DIM_ROLESSERVIDOR" in sql_upper and "WHERE IDROLSERVIDOR" in sql_upper:
        rid = params.get("id")
        return [r for r in PINOT_STORE["Dim_RolesServidor"] if r["idrolservidor"] == rid]

    # --- List queries ---
    if "FROM DIM_USUARIOS" in sql_upper and "IDUSUARIO >" in sql_upper:
        cursor = int(params.get("cursor", 0))
        limit = int(params.get("limit", 20))
        users = [u for u in PINOT_STORE["Dim_Usuarios"] if u["idusuario"] > cursor]
        return sorted(users, key=lambda u: u["idusuario"])[:limit]

    if "FROM DIM_USUARIOS" in sql_upper and "ORDER BY" in sql_upper:
        limit = int(params.get("limit", 20))
        return sorted(PINOT_STORE["Dim_Usuarios"], key=lambda u: u["idusuario"])[:limit]

    if "FROM DIM_ROL" in sql_upper and "ORDER BY" in sql_upper:
        return sorted(PINOT_STORE["Dim_Rol"], key=lambda r: r["idrol"])

    if "FROM DIM_USUARIOSSERVIDOR" in sql_upper and "ORDER BY" in sql_upper:
        return sorted(PINOT_STORE["Dim_UsuariosServidor"], key=lambda u: u["idusuariosservidor"])

    if "FROM DIM_ROLESSERVIDOR" in sql_upper and "ORDER BY" in sql_upper:
        return sorted(PINOT_STORE["Dim_RolesServidor"], key=lambda r: r["idrolservidor"])

    # --- Accidentes domain (TipoEstado before Accidente — substring collision) ---
    if "FROM FACT_ACCIDENTETIPOESTADOACCIDENTE" in sql_upper:
        aid = params.get("idaccidente")
        rows = [r for r in PINOT_STORE["Fact_AccidenteTipoEstadoAccidente"] if r["idaccidente"] == aid]
        if "ORDER BY FECHAHORAMODIFICADO DESC" in sql_upper:
            return sorted(rows, key=lambda r: r.get("fechahoramodificado", 0), reverse=True)[:1]
        return sorted(rows, key=lambda r: r.get("fechahoramodificado", 0))

    if "FROM FACT_ACCIDENTE" in sql_upper:
        if "WHERE IDACCIDENTE" in sql_upper:
            aid = params.get("idaccidente")
            return [a for a in PINOT_STORE["Fact_Accidente"] if a["idaccidente"] == aid]
        activo = params.get("activo", True)
        if "WHERE ACTIVO" in sql_upper:
            rows = [a for a in PINOT_STORE["Fact_Accidente"] if a.get("activo") == activo]
        elif "ACTIVO = TRUE" in sql_upper or "activo = true" in sql:
            rows = [a for a in PINOT_STORE["Fact_Accidente"] if a.get("activo") is True]
        else:
            rows = list(PINOT_STORE["Fact_Accidente"])
        # Los predicados de paginación/filtrado viven en el SQL real (ver
        # AccidenteRepository.list_activos); el doble debe aplicarlos igual o
        # los tests dejan de medir lo que hace Pinot.
        if "IDSEVERIDAD =" in sql_upper:
            rows = [r for r in rows if r.get("idseveridad") == params.get("idseveridad")]
        if "FECHAHORAACCIDENTE >=" in sql_upper:
            desde = params.get("fecha_desde", params.get("desde"))
            rows = [r for r in rows if (r.get("fechahoraaccidente") or 0) >= desde]
        if "FECHAHORAACCIDENTE <=" in sql_upper:
            hasta = params.get("fecha_hasta", params.get("hasta"))
            rows = [r for r in rows if (r.get("fechahoraaccidente") or 0) <= hasta]
        if "IDCALLE IN" in sql_upper:
            permitidas = set(params.get("idscalle") or [])
            rows = [r for r in rows if r.get("idcalle") in permitidas]
        if "IDACCIDENTE <" in sql_upper:
            rows = [r for r in rows if r["idaccidente"] < params.get("cursor")]
        if "ORDER BY IDACCIDENTE DESC" in sql_upper:
            rows = sorted(rows, key=lambda r: r["idaccidente"], reverse=True)
        if "LIMIT" in sql_upper and "limit" in params:
            rows = rows[: int(params["limit"])]
        return rows

    if "FROM DIM_CALLE" in sql_upper and "WHERE IDCALLE" in sql_upper:
        idcalle = params.get("idcalle")
        calles = [c for c in PINOT_STORE["Dim_Calle"] if c["idcalle"] == idcalle]
        if "SELECT IDCIUDAD" in sql_upper:
            return [{"idciudad": c["idciudad"]} for c in calles]
        return calles

    if "FROM DIM_CIUDAD" in sql_upper and "WHERE IDCIUDAD" in sql_upper:
        idciudad = params.get("idciudad")
        ciudades = [c for c in PINOT_STORE["Dim_Ciudad"] if c["idciudad"] == idciudad]
        if "SELECT IDCONDADO" in sql_upper:
            return [{"idcondado": c["idcondado"]} for c in ciudades]
        return ciudades

    if "FROM DIM_CONDADO " in sql_upper and "WHERE IDCONDADO" in sql_upper:
        idcondado = params.get("idcondado")
        condados = [c for c in PINOT_STORE["Dim_Condado"] if c["idcondado"] == idcondado]
        if "SELECT IDESTADO" in sql_upper:
            return [{"idestado": c["idestado"]} for c in condados]
        return condados

    # --- Catálogo geográfico en cascada (RF-REG-006 punto 3) ---
    if "FROM DIM_PAIS" in sql_upper:
        return [
            {"id": p["idpais"], "nombre": p["pais"]}
            for p in PINOT_STORE["Dim_Pais"]
            if p.get("activo", True)
        ]

    if "FROM DIM_ESTADO" in sql_upper and "WHERE IDPAIS" in sql_upper:
        idpais = params.get("idpais")
        return [
            {"id": e["idestado"], "nombre": e["estado"]}
            for e in PINOT_STORE["Dim_Estado"]
            if e["idpais"] == idpais and e.get("activo", True)
        ]

    if "FROM DIM_CONDADO" in sql_upper and "WHERE IDESTADO" in sql_upper:
        idestado = params.get("idestado")
        return [
            {"id": c["idcondado"], "nombre": c.get("condado", c.get("nombre"))}
            for c in PINOT_STORE["Dim_Condado"]
            if c["idestado"] == idestado and c.get("activo", True)
        ]

    if "FROM DIM_CIUDAD" in sql_upper and "WHERE IDCONDADO" in sql_upper:
        idcondado = params.get("idcondado")
        return [
            {"id": c["idciudad"], "nombre": c.get("ciudad", c.get("nombre"))}
            for c in PINOT_STORE["Dim_Ciudad"]
            if c["idcondado"] == idcondado and c.get("activo", True)
        ]

    if "FROM DIM_CALLE" in sql_upper and "WHERE IDCIUDAD" in sql_upper:
        idciudad = params.get("idciudad")
        return [
            {"id": c["idcalle"], "nombre": c.get("calle", c.get("nombre"))}
            for c in PINOT_STORE["Dim_Calle"]
            if c["idciudad"] == idciudad and c.get("activo", True)
        ]

    if "FROM DIM_REGIONOPERATIVAESTADOREGION" in sql_upper and "WHERE IDESTADOREGION" in sql_upper:
        idestadoregion = params.get("idestadoregion")
        return [
            {"idregionoperativa": link["idregionoperativa"]}
            for link in PINOT_STORE["Dim_RegionOperativaEstadoRegion"]
            if link["idestadoregion"] == idestadoregion
        ]

    if "FROM DIM_REGIONOPERATIVA" in sql_upper and "IDREGIONOPERATIVA IN" in sql_upper:
        region_ids = params.get("region_ids") or []
        return [
            {"idregionoperativa": region["idregionoperativa"]}
            for region in PINOT_STORE["Dim_RegionOperativa"]
            if region["idregionoperativa"] in region_ids
            and region.get("estadoregion") == "Producción"
            and region.get("activo")
        ]

    if "FROM FACT_DESPACHO" in sql_upper:
        if "WHERE IDDESPACHO" in sql_upper:
            did = params.get("iddespacho")
            return [d for d in PINOT_STORE["Fact_Despacho"] if d["iddespacho"] == did]
        if "WHERE IDUNIDADEMERGENCIA" in sql_upper and "ACTIVO = TRUE" in sql_upper:
            uid = params.get("idunidademergencia")
            return [
                d for d in PINOT_STORE["Fact_Despacho"]
                if d.get("idunidademergencia") == uid and d.get("activo")
            ]
        if "WHERE ACTIVO = TRUE" in sql_upper and "IDACCIDENTE" not in sql_upper:
            return [d for d in PINOT_STORE["Fact_Despacho"] if d.get("activo")]
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            rows = [d for d in PINOT_STORE["Fact_Despacho"] if d["idaccidente"] == aid]
            if "AND ACTIVO" in sql_upper:
                activo = params.get("activo", True)
                rows = [d for d in rows if d.get("activo") == activo]
            return rows
        return list(PINOT_STORE["Fact_Despacho"])

    if "FROM FACT_NOTIFICACIONDESPACHO" in sql_upper:
        if "WHERE IDNOTIFICACIONDESPACHO" in sql_upper:
            nid = params.get("idnotificaciondespacho")
            return [
                n for n in PINOT_STORE["Fact_NotificacionDespacho"]
                if n["idnotificaciondespacho"] == nid
            ]
        if "WHERE IDUNIDADDEMERGENCIA" in sql_upper:
            uid = params.get("idunidaddemergencia")
            return [
                n for n in PINOT_STORE["Fact_NotificacionDespacho"]
                if n.get("idunidaddemergencia") == uid
            ]
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            return [
                n for n in PINOT_STORE["Fact_NotificacionDespacho"]
                if n["idaccidente"] == aid
            ]
        return list(PINOT_STORE["Fact_NotificacionDespacho"])

    if "FROM FACT_HISTORIALDESPACHOUNIDAD" in sql_upper:
        did = params.get("iddespacho")
        return [
            r for r in PINOT_STORE["Fact_HistorialDespachoUnidad"]
            if r["iddespacho"] == did
        ]

    if "FROM DIM_HISTORIALUBICACIONUNIDADEMERGENCIA" in sql_upper:
        uid = params.get("idunidademergencia")
        rows = [
            r for r in PINOT_STORE["Dim_HistorialUbicacionUnidadEmergencia"]
            if r["idunidademergencia"] == uid
        ]
        if "ORDER BY FECHAHORA DESC" in sql_upper:
            rows.sort(key=lambda r: r.get("fechahora", 0), reverse=True)
            return rows[:1]
        # Ventana temporal, cursor keyset y tope de la traza GPS
        # (HistorialUbicacionRepository.list_by_unidad).
        if "FECHAHORA >=" in sql_upper:
            rows = [r for r in rows if (r.get("fechahora") or 0) >= params.get("desde")]
        if "FECHAHORA <=" in sql_upper:
            rows = [r for r in rows if (r.get("fechahora") or 0) <= params.get("hasta")]
        if "IDHISTORIALUBICACION >" in sql_upper:
            rows = [
                r for r in rows
                if int(r.get("idhistorialubicacion") or 0) > int(params.get("cursor", 0))
            ]
        if "ORDER BY IDHISTORIALUBICACION" in sql_upper:
            rows = sorted(rows, key=lambda r: int(r.get("idhistorialubicacion") or 0))
        if "LIMIT" in sql_upper and "limit" in params:
            rows = rows[: int(params["limit"])]
        return rows

    if "FROM DIM_PARAMETROSDESPACHO" in sql_upper:
        rows = list(PINOT_STORE["Dim_ParametrosDespacho"])
        if "ORDER BY FECHA_ACTUALIZACION DESC" in sql_upper:
            rows.sort(key=lambda r: r.get("fecha_actualizacion", 0), reverse=True)
            return rows[:1]
        return rows

    if "FROM DIM_PARAMETROSSEGUIMIENTO" in sql_upper:
        rows = list(PINOT_STORE["Dim_ParametrosSeguimiento"])
        if "ORDER BY FECHA_ACTUALIZACION DESC" in sql_upper:
            rows.sort(key=lambda r: r.get("fecha_actualizacion", 0), reverse=True)
            return rows[:1]
        return rows

    if "FROM DIM_CONDADOVECINO" in sql_upper:
        cid = params.get("idcondado")
        return [
            v for v in PINOT_STORE["Dim_CondadoVecino"]
            if v["idcondado"] == cid
        ]

    if "FROM DIM_EVIDENCIAFOTO" in sql_upper:
        if "WHERE IDEVIDENCIAFOTO" in sql_upper:
            eid = params.get("idevidenciafoto")
            return [e for e in PINOT_STORE["Dim_EvidenciaFoto"] if e["idevidenciafoto"] == eid]
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            rows = [e for e in PINOT_STORE["Dim_EvidenciaFoto"] if e["idaccidente"] == aid]
            # Filtro/orden/paginación de EvidenciaFotoRepository.list_by_accidente.
            if "SINCRONIZADO = TRUE" in sql_upper:
                rows = [r for r in rows if r.get("sincronizado") is True]
            if "IDEVIDENCIAFOTO <" in sql_upper:
                rows = [r for r in rows if r.get("idevidenciafoto", 0) < params.get("cursor")]
            if "ORDER BY FECHAHORA DESC" in sql_upper:
                rows = sorted(rows, key=lambda r: r.get("fechahora", 0), reverse=True)
            if "LIMIT" in sql_upper and "limit" in params:
                rows = rows[: int(params["limit"])]
            return rows
        return list(PINOT_STORE["Dim_EvidenciaFoto"])

    if "FROM DIM_ELEMENTOCLIMATICOSACCIDENTE" in sql_upper:
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            return [
                r for r in PINOT_STORE["Dim_ElementoClimaticosAccidente"]
                if r["idaccidente"] == aid
            ]
        return list(PINOT_STORE["Dim_ElementoClimaticosAccidente"])

    if "FROM DIM_ELEMENTOFISICOACCIDENTE" in sql_upper:
        if "WHERE IDELEMENTOSFISICOSACCIDENTE" in sql_upper:
            eid = params.get("id")
            return [
                r for r in PINOT_STORE["Dim_ElementoFisicoAccidente"]
                if r["idelementosfisicosaccidente"] == eid
            ]
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            return [
                r for r in PINOT_STORE["Dim_ElementoFisicoAccidente"]
                if r["idaccidente"] == aid
            ]
        return list(PINOT_STORE["Dim_ElementoFisicoAccidente"])

    if "FROM DIM_PERIODOSDIAS" in sql_upper:
        if "WHERE IDPERIODODIA" in sql_upper:
            pid = params.get("id")
            return [r for r in PINOT_STORE["Dim_PeriodosDias"] if r["idperiododia"] == pid]
        return list(PINOT_STORE["Dim_PeriodosDias"])

    if "FROM DIM_ESTADOSCLIMAS" in sql_upper:
        if "WHERE IDESTADOCLIMA" in sql_upper:
            cid = params.get("id")
            return [r for r in PINOT_STORE["Dim_EstadosClimas"] if r["idestadoclima"] == cid]
        return list(PINOT_STORE["Dim_EstadosClimas"])

    if "FROM DIM_ELEMENTOS_FISICOS" in sql_upper:
        if "WHERE IDELEMENTOFISICO" in sql_upper:
            eid = params.get("id")
            return [
                r for r in PINOT_STORE["Dim_Elementos_Fisicos"]
                if r["idelementofisico"] == eid
            ]
        return list(PINOT_STORE["Dim_Elementos_Fisicos"])

    if "FROM DIM_ESTADO_CONDUCTOR" in sql_upper:
        if "WHERE IDESTADOCONDUCTOR" in sql_upper:
            eid = params.get("id")
            return [
                r for r in PINOT_STORE["Dim_Estado_Conductor"]
                if r["idestadoconductor"] == eid
            ]
        return list(PINOT_STORE["Dim_Estado_Conductor"])

    if "FROM DIM_TIPOREPORTADO" in sql_upper:
        return [
            {"id": r["idtiporeportado"], "nombre": r["tiporeportado"]}
            for r in PINOT_STORE["Dim_TipoReportado"]
            if r.get("activo", True)
        ]

    if "FROM DIM_REFERENCIAESTACION" in sql_upper:
        return [
            {
                "id": r["idreferenciaestacion"],
                "nombre": r["codigoaeropuerto"],
                "zonahoraria": r.get("zonahoraria"),
            }
            for r in PINOT_STORE["Dim_ReferenciaEstacion"]
            if r.get("activo", True)
        ]

    if "FROM DIM_CONDUCTOR" in sql_upper:
        if "WHERE IDENTIFICACION" in sql_upper:
            ident = params.get("identificacion")
            return [
                r for r in PINOT_STORE["Dim_Conductor"]
                if r.get("identificacion") == ident
            ]
        if "WHERE IDCONDUCTOR" in sql_upper:
            cid = params.get("id")
            return [r for r in PINOT_STORE["Dim_Conductor"] if r["idconductor"] == cid]
        return list(PINOT_STORE["Dim_Conductor"])

    if "FROM DIM_VEHICULO" in sql_upper:
        if "WHERE IDVEHICULO" in sql_upper:
            vid = params.get("id")
            return [r for r in PINOT_STORE["Dim_Vehiculo"] if r["idvehiculo"] == vid]
        return list(PINOT_STORE["Dim_Vehiculo"])

    if "FROM FACT_CONDUCTOR_ACCIDENTE" in sql_upper:
        if "WHERE IDCONDUCTORACCIDENTE" in sql_upper:
            cid = params.get("id")
            return [
                r for r in PINOT_STORE["Fact_Conductor_Accidente"]
                if r["idconductoraccidente"] == cid
            ]
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            return [
                r for r in PINOT_STORE["Fact_Conductor_Accidente"]
                if r["idaccidente"] == aid
            ]
        return list(PINOT_STORE["Fact_Conductor_Accidente"])

    if "FROM DIM_IMPLICADO" in sql_upper:
        if "WHERE IDIMPLICADO" in sql_upper:
            iid = params.get("id")
            return [
                r for r in PINOT_STORE["Dim_Implicado"]
                if r["idimplicado"] == iid
            ]
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            return [
                r for r in PINOT_STORE["Dim_Implicado"]
                if r["idaccidente"] == aid
            ]
        return list(PINOT_STORE["Dim_Implicado"])

    if "FROM DIM_NOTAACCIDENTE" in sql_upper:
        aid = params.get("idaccidente")
        if "WHERE IDACCIDENTE" in sql_upper:
            return [n for n in PINOT_STORE["Dim_NotaAccidente"] if n["idaccidente"] == aid]
        return list(PINOT_STORE["Dim_NotaAccidente"])

    if "FROM FACT_HISTORIALESTADOUNIDAD" in sql_upper:
        uid = params.get("idunidademergencia")
        rows = [
            r for r in PINOT_STORE["Fact_HistorialEstadoUnidad"]
            if r["idunidademergencia"] == uid
        ]
        # Orden/cursor/tope ahora viven en el SQL real (ver
        # HistorialEstadoUnidadRepository.list_by_unidad); el doble debe aplicarlos
        # o `get_current_estado` devolvería una fila arbitraria en los tests.
        if "IDHISTORIALESTADOSUNIDADESEMERGENCIAS <" in sql_upper:
            rows = [
                r for r in rows
                if int(r.get("idhistorialestadosunidadesemergencias") or 0)
                < int(params.get("cursor", 0))
            ]
        if "ORDER BY FECHAHORA DESC" in sql_upper:
            rows = sorted(
                rows,
                key=lambda r: (
                    r.get("fechahora", 0),
                    r.get("idhistorialestadosunidadesemergencias", 0),
                ),
                reverse=True,
            )
        if "LIMIT" in sql_upper and "limit" in params:
            rows = rows[: int(params["limit"])]
        return rows

    if "FROM DIM_UNIDADEMERGENCIA" in sql_upper:
        if "WHERE PLACA" in sql_upper:
            placa = params.get("placa")
            return [
                u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u.get("placa") == placa and u.get("activo")
            ]
        if "WHERE IDCLIENTE" in sql_upper:
            cid = params.get("idcliente")
            return [
                u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u.get("idcliente") == cid
            ]
        if "IDCONDADO IN" in sql_upper:
            idscondado = params.get("idscondado") or []
            return [
                u
                for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u.get("idcondado") in idscondado and u.get("activo")
            ]
        if "WHERE IDUSUARIO" in sql_upper:
            user_id = params.get("idusuario")
            return [
                u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u.get("idusuario") == user_id and u.get("activo")
            ]
        if "WHERE IDUNIDADEMERGENCIA" in sql_upper:
            uid = params.get("idunidademergencia")
            if "SELECT LATITUD" in sql_upper:
                return [
                    u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                    if u["idunidademergencia"] == uid
                ]
            return [
                u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u["idunidademergencia"] == uid
            ]
        if "WHERE ACTIVO" in sql_upper or "activo = true" in sql.lower():
            rows = [u for u in PINOT_STORE["Dim_UnidadEmergencia"] if u.get("activo")]
            # Filtro/paginación de la flota (UnidadEmergenciaRepository.list_active).
            if "TIPOUNIDADEMERGENCIA =" in sql_upper:
                rows = [r for r in rows if r.get("tipounidademergencia") == params.get("tipo")]
            if "IDUNIDADEMERGENCIA >" in sql_upper:
                rows = [
                    r for r in rows
                    if int(r.get("idunidademergencia") or 0) > int(params.get("cursor", 0))
                ]
            if "ORDER BY IDUNIDADEMERGENCIA" in sql_upper:
                rows = sorted(rows, key=lambda r: int(r.get("idunidademergencia") or 0))
            if "LIMIT" in sql_upper and "limit" in params:
                rows = rows[: int(params["limit"])]
            return rows
        return list(PINOT_STORE["Dim_UnidadEmergencia"])

    if "FROM DIM_ESTADOUNIDADEMERGENCIA" in sql_upper:
        return list(PINOT_STORE["Dim_EstadoUnidadEmergencia"])

    if "FROM FACT_BAJAUNIDAD" in sql_upper:
        uid = params.get("idunidademergencia")
        if "WHERE IDUNIDADEMERGENCIA" in sql_upper:
            return [r for r in PINOT_STORE["Fact_BajaUnidad"] if r["idunidademergencia"] == uid]
        return list(PINOT_STORE["Fact_BajaUnidad"])

    # --- Soporte al cliente (gestion-tickets-soporte) ---
    if "MAX(ID_RECLAMO)" in sql_upper:
        ids = [r["id_reclamo"] for r in PINOT_STORE["Fact_Reclamo"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(ID_HISTORIAL)" in sql_upper:
        ids = [r["id_historial"] for r in PINOT_STORE["Fact_Historial_Ticket"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDSLACONFIG)" in sql_upper:
        ids = [r["idslaconfig"] for r in PINOT_STORE["Dim_SLAConfig"]]
        return [{"max_id": max(ids) if ids else 0}]
    if "MAX(IDARCHIVOADJUNTORECLAMO)" in sql_upper:
        ids = [r["idarchivoadjuntoreclamo"] for r in PINOT_STORE["Fact_ArchivosAdjuntosReclamos"]]
        return [{"max_id": max(ids) if ids else 0}]

    if "FROM FACT_RECLAMO" in sql_upper:
        if "WHERE ID_RECLAMO" in sql_upper:
            rid = params.get("id_reclamo")
            return [r for r in PINOT_STORE["Fact_Reclamo"] if r["id_reclamo"] == rid]
        return list(PINOT_STORE["Fact_Reclamo"])

    if "FROM FACT_HISTORIAL_TICKET" in sql_upper:
        rid = params.get("id_reclamo")
        return [r for r in PINOT_STORE["Fact_Historial_Ticket"] if r["id_reclamo"] == rid]

    if "FROM DIM_SLACONFIG" in sql_upper:
        if "WHERE IDSLACONFIG" in sql_upper:
            cid = params.get("idslaconfig")
            return [r for r in PINOT_STORE["Dim_SLAConfig"] if r["idslaconfig"] == cid]
        return list(PINOT_STORE["Dim_SLAConfig"])

    if "FROM FACT_ARCHIVOSADJUNTOSRECLAMOS" in sql_upper:
        rid = params.get("id_reclamo")
        return [r for r in PINOT_STORE["Fact_ArchivosAdjuntosReclamos"] if r["id_reclamo"] == rid]

    if "FROM DIM_ESTADO_SOPORTE" in sql_upper:
        nombre = params.get("nombre")
        if nombre:
            return [r for r in PINOT_STORE["Dim_Estado_Soporte"] if r["nombre"] == nombre]
        return list(PINOT_STORE["Dim_Estado_Soporte"])

    if "FROM DIM_SERVICIO" in sql_upper:
        return [
            {"id": r["id_servicio"], "nombre": r["nombre"]}
            for r in PINOT_STORE.get("Dim_Servicio", [])
            if r.get("activo", True)
        ]

    if "FROM FACT_SUSCRIPCION" in sql_upper:
        rows = list(PINOT_STORE["Fact_Suscripcion"])
        if "ID_SUSCRIPCION =" in sql_upper:
            rows = [r for r in rows if r.get("id_suscripcion") == params.get("id")]
        if "IDCLIENTE =" in sql_upper:
            rows = [r for r in rows if r.get("idcliente") == params.get("idcliente")]
        return rows

    return []


@pytest.fixture
def pinot_store():
    """Expose in-memory Pinot store for test seeding."""
    return PINOT_STORE


@pytest.fixture(autouse=True)
def reset_pinot_store():
    """Reset in-memory Pinot data between tests."""
    _reset_pinot_store()
    yield


@pytest.fixture(autouse=True)
def reset_throttle_history():
    """Clear DRF throttle counters between tests.

    SimpleRateThrottle persists its history in django.core.cache, which lives
    for the whole pytest process. Without this reset a test that exhausts a
    scope (p. ej. `prospecto_registro`: 10/min) makes every later test hitting
    the same endpoint fail with 429 depending on collection order.
    """
    from django.core.cache import cache

    cache.clear()
    yield


@pytest.fixture
def mock_pinot():
    """Patch PinotClient.query with in-memory store."""
    with patch.object(PinotClient, "query", side_effect=_pinot_query_impl):
        yield _pinot_query_impl


@pytest.fixture
def mock_kafka():
    """Patch KafkaWriter to capture published messages in memory."""
    published: list[dict] = []

    def _publish(self, topic, payload):
        published.append({"topic": topic, "payload": payload})
        # Mirror writes into Pinot store for read-after-write in tests
        if topic.endswith("Fact_Session_topic") or topic == "Fact_Session_topic":
            sessions = PINOT_STORE["Fact_Session"]
            existing_idx = next(
                (i for i, s in enumerate(sessions) if s["idsession"] == payload["idsession"]),
                None,
            )
            if existing_idx is not None:
                sessions[existing_idx] = payload
            else:
                sessions.append(payload)
        elif topic.endswith("Dim_Credencial_topic") or topic == "Dim_Credencial_topic":
            creds = PINOT_STORE["Dim_Credencial"]
            existing_idx = next(
                (i for i, c in enumerate(creds) if c["idusuario"] == payload["idusuario"]),
                None,
            )
            if existing_idx is not None:
                creds[existing_idx] = payload
            else:
                creds.append(payload)
        elif topic.endswith("Dim_Usuario_Rol_topic") or topic == "Dim_Usuario_Rol_topic":
            PINOT_STORE["Dim_Usuario_Rol"].append(payload)
        elif topic.endswith("Dim_UsuariosServidor_topic") or topic == "Dim_UsuariosServidor_topic":
            users = PINOT_STORE["Dim_UsuariosServidor"]
            existing_idx = next(
                (
                    i for i, u in enumerate(users)
                    if u["idusuariosservidor"] == payload["idusuariosservidor"]
                ),
                None,
            )
            if existing_idx is not None:
                users[existing_idx] = payload
            else:
                users.append(payload)
        elif topic.endswith("Dim_RolesServidor_topic") or topic == "Dim_RolesServidor_topic":
            roles = PINOT_STORE["Dim_RolesServidor"]
            existing_idx = next(
                (i for i, r in enumerate(roles) if r["idrolservidor"] == payload["idrolservidor"]),
                None,
            )
            if existing_idx is not None:
                roles[existing_idx] = payload
            else:
                roles.append(payload)
        elif topic.endswith("Dim_UsuariosServidorRolesServidor_topic"):
            PINOT_STORE["Dim_UsuariosServidorRolesServidor"].append(payload)
        elif topic.endswith("Dim_RolesServidorRoles_topic"):
            PINOT_STORE["Dim_RolesServidorRoles"].append(payload)
        elif topic.endswith("Dim_Usuarios_topic") or topic == "Dim_Usuarios_topic":
            users = PINOT_STORE["Dim_Usuarios"]
            existing_idx = next(
                (i for i, u in enumerate(users) if u["idusuario"] == payload["idusuario"]),
                None,
            )
            if existing_idx is not None:
                users[existing_idx] = payload
            else:
                users.append(payload)
        elif topic.endswith("Dim_Rol_topic") or topic == "Dim_Rol_topic":
            roles = PINOT_STORE["Dim_Rol"]
            existing_idx = next(
                (i for i, r in enumerate(roles) if r["idrol"] == payload["idrol"]),
                None,
            )
            if existing_idx is not None:
                roles[existing_idx] = payload
            else:
                roles.append(payload)
        elif topic.endswith("Dim_Cliente_topic") or topic == "Dim_Cliente_topic":
            clientes = PINOT_STORE["Dim_Cliente"]
            existing_idx = next(
                (i for i, c in enumerate(clientes) if c["idcliente"] == payload["idcliente"]),
                None,
            )
            if existing_idx is not None:
                clientes[existing_idx] = payload
            else:
                clientes.append(payload)
        elif topic.endswith("Dim_Prospecto_topic") or topic == "Dim_Prospecto_topic":
            rows = PINOT_STORE["Dim_Prospecto"]
            index = next((i for i, row in enumerate(rows) if row["idprospecto"] == payload["idprospecto"]), None)
            if index is None: rows.append(payload)
            else: rows[index] = payload
        elif topic.endswith("Fact_Asignacion_topic") or topic == "Fact_Asignacion_topic":
            rows = PINOT_STORE["Fact_Asignacion"]
            index = next((i for i, row in enumerate(rows) if row["idasignacion"] == payload["idasignacion"]), None)
            if index is None: rows.append(payload)
            else: rows[index] = payload
        elif topic.endswith("Fact_Pipeline_topic") or topic == "Fact_Pipeline_topic":
            rows = PINOT_STORE["Fact_Pipeline"]
            index = next((i for i, row in enumerate(rows) if row["id_transicion"] == payload["id_transicion"]), None)
            if index is None: rows.append(payload)
            else: rows[index] = payload
        elif topic.endswith("Fact_Interaccion_Demo_topic") or topic == "Fact_Interaccion_Demo_topic":
            rows = PINOT_STORE["Fact_Interaccion_Demo"]
            index = next(
                (i for i, row in enumerate(rows) if row["idinteraccion"] == payload["idinteraccion"]),
                None,
            )
            if index is None:
                rows.append(payload)
            else:
                rows[index] = payload
        elif topic.endswith("Fact_NotificacionVentas_topic") or topic == "Fact_NotificacionVentas_topic":
            rows = PINOT_STORE["Fact_NotificacionVentas"]
            index = next(
                (i for i, row in enumerate(rows) if row["idnotificacion"] == payload["idnotificacion"]),
                None,
            )
            if index is None:
                rows.append(payload)
            else:
                rows[index] = payload
        elif (
            topic.endswith("Dim_Preferencias_Cliente_topic")
            or topic == "Dim_Preferencias_Cliente_topic"
        ):
            prefs = PINOT_STORE["Dim_Preferencias_Cliente"]
            existing_idx = next(
                (
                    i for i, p in enumerate(prefs)
                    if p["id_preferencia"] == payload["id_preferencia"]
                ),
                None,
            )
            if existing_idx is not None:
                prefs[existing_idx] = payload
            else:
                prefs.append(payload)
        elif topic.endswith("Fact_Onboarding_topic") or topic == "Fact_Onboarding_topic":
            rows = PINOT_STORE["Fact_Onboarding"]
            existing_idx = next(
                (
                    i for i, o in enumerate(rows)
                    if o["id_onboarding"] == payload["id_onboarding"]
                ),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Fact_Accidente_topic") or topic == "Fact_Accidente_topic":
            rows = PINOT_STORE["Fact_Accidente"]
            existing_idx = next(
                (i for i, a in enumerate(rows) if a["idaccidente"] == payload["idaccidente"]),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Fact_AccidenteTipoEstadoAccidente_topic")
            or topic == "Fact_AccidenteTipoEstadoAccidente_topic"
        ):
            PINOT_STORE["Fact_AccidenteTipoEstadoAccidente"].append(payload)
        elif (
            topic.endswith("Dim_ElementoClimaticosAccidente_topic")
            or topic == "Dim_ElementoClimaticosAccidente_topic"
        ):
            rows = PINOT_STORE["Dim_ElementoClimaticosAccidente"]
            existing_idx = next(
                (
                    i for i, r in enumerate(rows)
                    if r["idelementoclimaticoaccidente"]
                    == payload["idelementoclimaticoaccidente"]
                ),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Dim_ElementoFisicoAccidente_topic")
            or topic == "Dim_ElementoFisicoAccidente_topic"
        ):
            rows = PINOT_STORE["Dim_ElementoFisicoAccidente"]
            existing_idx = next(
                (
                    i for i, r in enumerate(rows)
                    if r["idelementosfisicosaccidente"]
                    == payload["idelementosfisicosaccidente"]
                ),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Dim_Conductor_topic") or topic == "Dim_Conductor_topic":
            rows = PINOT_STORE["Dim_Conductor"]
            existing_idx = next(
                (i for i, r in enumerate(rows) if r["idconductor"] == payload["idconductor"]),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Dim_Vehiculo_topic") or topic == "Dim_Vehiculo_topic":
            rows = PINOT_STORE["Dim_Vehiculo"]
            existing_idx = next(
                (i for i, r in enumerate(rows) if r["idvehiculo"] == payload["idvehiculo"]),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Fact_Conductor_Accidente_topic")
            or topic == "Fact_Conductor_Accidente_topic"
        ):
            rows = PINOT_STORE["Fact_Conductor_Accidente"]
            existing_idx = next(
                (
                    i for i, r in enumerate(rows)
                    if r["idconductoraccidente"] == payload["idconductoraccidente"]
                ),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Dim_Implicado_topic") or topic == "Dim_Implicado_topic":
            rows = PINOT_STORE["Dim_Implicado"]
            existing_idx = next(
                (
                    i for i, r in enumerate(rows)
                    if r["idimplicado"] == payload["idimplicado"]
                ),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Dim_NotaAccidente_topic") or topic == "Dim_NotaAccidente_topic":
            PINOT_STORE["Dim_NotaAccidente"].append(payload)
        elif topic.endswith("Dim_EvidenciaFoto_topic") or topic == "Dim_EvidenciaFoto_topic":
            PINOT_STORE["Dim_EvidenciaFoto"].append(payload)
        elif (
            topic.endswith("Fact_HistorialEstadoUnidad_topic")
            or topic == "Fact_HistorialEstadoUnidad_topic"
        ):
            PINOT_STORE["Fact_HistorialEstadoUnidad"].append(payload)
        elif topic.endswith("Fact_Despacho_topic") or topic == "Fact_Despacho_topic":
            rows = PINOT_STORE["Fact_Despacho"]
            existing_idx = next(
                (i for i, d in enumerate(rows) if d["iddespacho"] == payload["iddespacho"]),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Fact_NotificacionDespacho_topic")
            or topic == "Fact_NotificacionDespacho_topic"
        ):
            rows = PINOT_STORE["Fact_NotificacionDespacho"]
            existing_idx = next(
                (
                    i for i, n in enumerate(rows)
                    if n["idnotificaciondespacho"] == payload["idnotificaciondespacho"]
                ),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Fact_HistorialDespachoUnidad_topic")
            or topic == "Fact_HistorialDespachoUnidad_topic"
        ):
            PINOT_STORE["Fact_HistorialDespachoUnidad"].append(payload)
        elif (
            topic.endswith("Dim_ParametrosDespacho_topic")
            or topic == "Dim_ParametrosDespacho_topic"
        ):
            rows = PINOT_STORE["Dim_ParametrosDespacho"]
            existing_idx = next(
                (i for i, p in enumerate(rows) if p.get("idparametrosdespacho") == payload.get("idparametrosdespacho")),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Dim_HistorialUbicacionUnidadEmergencia_topic")
            or topic == "Dim_HistorialUbicacionUnidadEmergencia_topic"
        ):
            PINOT_STORE["Dim_HistorialUbicacionUnidadEmergencia"].append(payload)
        elif topic.endswith("Dim_UnidadEmergencia_topic") or topic == "Dim_UnidadEmergencia_topic":
            units = PINOT_STORE["Dim_UnidadEmergencia"]
            existing_idx = next(
                (
                    i for i, u in enumerate(units)
                    if u["idunidademergencia"] == payload["idunidademergencia"]
                ),
                None,
            )
            if existing_idx is not None:
                units[existing_idx] = {**units[existing_idx], **payload}
            else:
                units.append(payload)
        elif (
            topic.endswith("Dim_ParametrosSeguimiento_topic")
            or topic == "Dim_ParametrosSeguimiento_topic"
        ):
            rows = PINOT_STORE["Dim_ParametrosSeguimiento"]
            existing_idx = next(
                (i for i, p in enumerate(rows) if p.get("idparametrosseguimiento") == payload.get("idparametrosseguimiento")),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Fact_Reclamo_topic") or topic == "Fact_Reclamo_topic":
            rows = PINOT_STORE["Fact_Reclamo"]
            existing_idx = next(
                (i for i, r in enumerate(rows) if r["id_reclamo"] == payload["id_reclamo"]),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Fact_Historial_Ticket_topic") or topic == "Fact_Historial_Ticket_topic":
            PINOT_STORE["Fact_Historial_Ticket"].append(payload)
        elif topic.endswith("Dim_SLAConfig_topic") or topic == "Dim_SLAConfig_topic":
            rows = PINOT_STORE["Dim_SLAConfig"]
            existing_idx = next(
                (i for i, r in enumerate(rows) if r["idslaconfig"] == payload["idslaconfig"]),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Fact_ArchivosAdjuntosReclamos_topic")
            or topic == "Fact_ArchivosAdjuntosReclamos_topic"
        ):
            PINOT_STORE["Fact_ArchivosAdjuntosReclamos"].append(payload)
        elif topic.endswith("Fact_BajaUnidad_topic") or topic == "Fact_BajaUnidad_topic":
            PINOT_STORE["Fact_BajaUnidad"].append(payload)
        elif topic.endswith("Dim_RegionOperativa_topic") or topic == "Dim_RegionOperativa_topic":
            regiones = PINOT_STORE["Dim_RegionOperativa"]
            existing_idx = next(
                (
                    i for i, r in enumerate(regiones)
                    if r["idregionoperativa"] == payload["idregionoperativa"]
                ),
                None,
            )
            if existing_idx is not None:
                regiones[existing_idx] = {**regiones[existing_idx], **payload}
            else:
                regiones.append(payload)
        elif topic.endswith("Dim_ValidacionRegion_topic") or topic == "Dim_ValidacionRegion_topic":
            PINOT_STORE["Dim_ValidacionRegion"].append(payload)
        elif (
            topic.endswith("Dim_RegionOperativaEstadoRegion_topic")
            or topic == "Dim_RegionOperativaEstadoRegion_topic"
        ):
            links = PINOT_STORE["Dim_RegionOperativaEstadoRegion"]
            existing_idx = next(
                (
                    i
                    for i, r in enumerate(links)
                    if r.get("idregionoperativaestadoregion")
                    == payload.get("idregionoperativaestadoregion")
                    or (
                        r.get("idregionoperativa") == payload.get("idregionoperativa")
                        and r.get("idestadoregion") == payload.get("idestadoregion")
                    )
                ),
                None,
            )
            if existing_idx is not None:
                links[existing_idx] = {**links[existing_idx], **payload}
            else:
                links.append(payload)
        elif topic.endswith("Dim_Plan_topic") or topic == "Dim_Plan_topic":
            rows = PINOT_STORE["Dim_Plan"]
            idx = next((i for i, r in enumerate(rows) if r["idplan"] == payload["idplan"]), None)
            if idx is not None:
                rows[idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Dim_MetodoPago_topic") or topic == "Dim_MetodoPago_topic":
            rows = PINOT_STORE["Dim_MetodoPago"]
            idx = next(
                (i for i, r in enumerate(rows) if r["idmetodopago"] == payload["idmetodopago"]),
                None,
            )
            if idx is not None:
                rows[idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Fact_Suscripcion_topic") or topic == "Fact_Suscripcion_topic":
            rows = PINOT_STORE["Fact_Suscripcion"]
            idx = next(
                (i for i, r in enumerate(rows) if r["id_suscripcion"] == payload["id_suscripcion"]),
                None,
            )
            if idx is not None:
                rows[idx] = payload
            else:
                rows.append(payload)
        elif topic.endswith("Fact_Factura_topic") or topic == "Fact_Factura_topic":
            rows = PINOT_STORE["Fact_Factura"]
            idx = next(
                (i for i, r in enumerate(rows) if r["id_factura"] == payload["id_factura"]),
                None,
            )
            if idx is not None:
                rows[idx] = payload
            else:
                rows.append(payload)
        elif (
            topic.endswith("Fact_Solicitud_Cambio_Plan_topic")
            or topic == "Fact_Solicitud_Cambio_Plan_topic"
        ):
            rows = PINOT_STORE["Fact_Solicitud_Cambio_Plan"]
            idx = next(
                (i for i, r in enumerate(rows) if r["idsolicitud"] == payload["idsolicitud"]),
                None,
            )
            if idx is not None:
                rows[idx] = payload
            else:
                rows.append(payload)

    with patch.object(KafkaWriter, "publish", _publish):
        yield published


@pytest.fixture
def api_client(mock_pinot, mock_kafka):
    """DRF APIClient with mocked Pinot/Kafka."""
    return APIClient()


@pytest.fixture
def auth_headers(mock_pinot, mock_kafka):
    """Real RS256 JWT for admin user with active session."""
    token = create_access_token(user_id=1, roles=["Administrador"], session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(auth_headers):
    """Alias for auth_headers (Administrador)."""
    return auth_headers

@pytest.fixture
def admin_crm_auth_headers(admin_auth_headers):
    return admin_auth_headers

@pytest.fixture
def gerente_ventas_auth_headers(mock_pinot, mock_kafka):
    PINOT_STORE["Fact_Session"].append({"idsession": 20, "idusuario": 20, "estadosession": "Inicio sesion"})
    token = create_access_token(user_id=20, roles=["GerenteVentas"], session_id=20)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

@pytest.fixture
def gerente_cuentas_publicas_auth_headers(mock_pinot, mock_kafka):
    PINOT_STORE["Fact_Session"].append({"idsession": 21, "idusuario": 21, "estadosession": "Inicio sesion"})
    token = create_access_token(user_id=21, roles=["GerenteCuentasPublicas"], session_id=21)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def demo_grant_factory(settings):
    from apps.ventas_crm.demo_tokens import issue_demo_grant

    def _factory(idprospecto: int) -> str:
        return issue_demo_grant(idprospecto)

    return _factory


@pytest.fixture
def demo_session_auth_headers(mock_pinot, mock_kafka, demo_grant_factory):
    """Bearer demo_session token for a seeded prospect with active demo_expiracion."""
    from datetime import datetime, timedelta, timezone

    from apps.ventas_crm.demo_tokens import format_iso_expiracion, issue_demo_session_token
    from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

    repo = ProspectoRepository()
    p = repo.create(
        {
            "nombres": "Demo",
            "apellidos": "User",
            "gmail": "demo.session@example.com",
            "empresa": "DemoCo",
            "tipo_organizacion": "Privado",
            "cargo": "Buyer",
            "telefono": "3001111111",
            "como_nos_conocio": "web",
            "demo_expiracion": None,
        }
    )
    iso = format_iso_expiracion(datetime.now(timezone.utc) + timedelta(minutes=30))
    repo.update_demo_expiracion(p["idprospecto"], iso)
    token = issue_demo_session_token(idprospecto=p["idprospecto"], demo_expiracion_iso=iso)
    return {
        "HTTP_AUTHORIZATION": f"Bearer {token}",
        "idprospecto": p["idprospecto"],
        "demo_grant": demo_grant_factory(p["idprospecto"]),
        "demo_expiracion": iso,
    }


@pytest.fixture
def operator_auth_headers(mock_pinot, mock_kafka):
    """Real RS256 JWT for operator user with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 2,
            "idusuario": 2,
            "token": "session-token-2",
            "refresh_token": "refresh-token-2",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=2, roles=["Operador"], session_id=2)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def operador_auth_headers(operator_auth_headers):
    """Alias for operator_auth_headers (spec naming)."""
    return operator_auth_headers


@pytest.fixture
def unidad_auth_headers(mock_pinot, mock_kafka):
    """Real RS256 JWT for unidad user with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 6,
            "idusuario": 6,
            "token": "session-token-6",
            "refresh_token": "refresh-token-6",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=6, roles=["Unidad"], session_id=6)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def tecnico_auth_headers(mock_pinot, mock_kafka):
    """Real RS256 JWT for técnico de campo (Tecnico role) with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 7,
            "idusuario": 7,
            "token": "session-token-7",
            "refresh_token": "refresh-token-7",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=7, roles=["Tecnico"], session_id=7)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def despacho_service_auth_headers(mock_pinot, mock_kafka):
    """JWT for Despacho service role with active session."""
    PINOT_STORE["Dim_Usuarios"].append(
        {
            "idusuario": 8,
            "nombres": "Servicio",
            "apellidos": "Despacho",
            "gmail": "despacho@tsi.com",
            "identificacion": "8888999900",
            "genero": "M",
            "telefono": "3008889900",
            "fechanacimiento": "1990-01-01",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 8,
            "idusuario": 8,
            "token": "session-token-8",
            "refresh_token": "refresh-token-8",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=8, roles=["Despacho"], session_id=8)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def cliente_auth_headers(mock_pinot, mock_kafka):
    """JWT for Cliente admin local (user 3) with active session."""
    token = create_access_token(user_id=3, roles=["Cliente"], session_id=3)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def cliente_member_auth_headers(mock_pinot, mock_kafka):
    """JWT for Cliente member (user 4, not admin local)."""
    token = create_access_token(user_id=4, roles=["Cliente"], session_id=4)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def mock_cuenta_pendiente_onboarding(mock_pinot, mock_kafka):
    """Cliente with estado_onboarding=Pendiente for onboarding tests."""
    PINOT_STORE["Dim_Cliente"].append(
        {
            "idcliente": 2,
            "nombre": "Nueva Empresa",
            "razon_social": "Nueva Empresa S.A.",
            "tipo": "Aseguradora",
            "nit_identificacion": "800111222-3",
            "logo_url": None,
            "plan_suscripcion": "basico",
            "estado_onboarding": "Pendiente",
            "estado": "Activo",
            "admin_local_id": 5,
            "fecha_inicio_contrato": 1704067200000,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    PINOT_STORE["Dim_Usuarios"].append(
        {
            "idusuario": 5,
            "nombres": "Onboarding",
            "apellidos": "Admin",
            "gmail": "onboarding@tsi.com",
            "identificacion": "5555666677",
            "genero": "M",
            "telefono": "3005556677",
            "fechanacimiento": "1990-01-01",
            "activo": True,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    PINOT_STORE["Dim_Credencial"].append(
        {
            "idcredencial": 5,
            "idusuario": 5,
            "contrasena": _TEST_PASSWORD_HASH,
            "estadocredencial": "Activo",
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    PINOT_STORE["Dim_Usuario_Rol"].append(
        {"idusuario": 5, "idrol": 3, "fecha_actualizacion": "2026-01-01T00:00:00+00:00"}
    )
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 5,
            "idusuario": 5,
            "token": "session-token-5",
            "refresh_token": "refresh-token-5",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    return 2


@pytest.fixture
def mock_onboarding_etapas(mock_pinot, mock_kafka, mock_cuenta_pendiente_onboarding):
    """Cliente 2 with cambio_password etapa completed."""
    PINOT_STORE["Fact_Onboarding"].append(
        {
            "id_onboarding": 1,
            "id_cliente": mock_cuenta_pendiente_onboarding,
            "etapa": "cambio_password",
            "completado": True,
            "fecha_completado": 1704067200000,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        }
    )
    PINOT_STORE["Dim_Cliente"] = [
        c if c["idcliente"] != mock_cuenta_pendiente_onboarding
        else {**c, "estado_onboarding": "En progreso"}
        for c in PINOT_STORE["Dim_Cliente"]
    ]
    return mock_cuenta_pendiente_onboarding


@pytest.fixture
def onboarding_cliente_auth_headers(mock_pinot, mock_kafka, mock_cuenta_pendiente_onboarding):
    """JWT for new admin local user (id 5) with active session."""
    token = create_access_token(user_id=5, roles=["Cliente"], session_id=5)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def accidente_activo(mock_pinot, mock_kafka):
    """Seed an active accidente with REPORTADO estado."""
    import time

    from apps.accidentes.domain_constants import ESTADO_REPORTADO
    from core.repositories.accidentes.accidente_repository import AccidenteRepository
    from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository

    ts = int(time.time() * 1000)
    idaccidente = "ACC-EVI-TEST-1"
    AccidenteRepository().create(
        {
            "idaccidente": idaccidente,
            "latitudinicio": 19.4326,
            "longitudinicio": -99.1332,
            "fechahoraaccidente": ts,
            "idseveridad": 2,
            "descripcion": "Caso evidencia test",
            "idcalle": 1,
            "idusuario": 2,
            "numvehiculos": 5,
            "activo": True,
        }
    )
    EstadoAccidenteRepository().append_estado(
        idaccidente=idaccidente, estado=ESTADO_REPORTADO, idusuario=2
    )
    return idaccidente


@pytest.fixture
def unidad_con_estado_activa(mock_pinot, mock_kafka):
    """Seed historial with Activa state for unit 1."""
    from core.repositories.despacho.historial_estado_unidad_repository import (
        HistorialEstadoUnidadRepository,
    )

    HistorialEstadoUnidadRepository().append_estado(
        idunidademergencia=1,
        estadonuevo="Activa",
        idusuario=6,
        estadoanterior="Fuera de servicio",
    )
    return 1


@pytest.fixture
def unidad_despacho_auth_headers(unidad_auth_headers):
    """Alias for unidad_auth_headers (spec naming)."""
    return unidad_auth_headers


@pytest.fixture
def operador_despacho_auth_headers(operator_auth_headers):
    """Alias for operator_auth_headers (despacho operador)."""
    return operator_auth_headers


@pytest.fixture
def operador_seguimiento_auth_headers(operator_auth_headers):
    """JWT operador para módulo seguimiento."""
    return operator_auth_headers


@pytest.fixture
def unidad_seguimiento_auth_headers(unidad_auth_headers):
    """JWT unidad para módulo seguimiento."""
    return unidad_auth_headers


@pytest.fixture
def cliente_expediente_auth_headers(cliente_auth_headers):
    """JWT cliente para expedientes cerrados."""
    return cliente_auth_headers


@pytest.fixture
def despacho_confirmado_unidad(mock_pinot, mock_kafka, despacho_pendiente_unidad):
    """Despacho confirmado (estado Confirmado) para pruebas de seguimiento."""
    from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService

    idnotif = despacho_pendiente_unidad["idnotificaciondespacho"]
    return ConfirmarDespachoService().confirmar(
        idnotificaciondespacho=idnotif,
        idunidademergencia=1,
        idusuario=6,
    )


@pytest.fixture
def director_tecnologico_auth_headers(mock_pinot, mock_kafka):
    """JWT for Director Tecnológico role with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 9,
            "idusuario": 9,
            "token": "session-token-9",
            "refresh_token": "refresh-token-9",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=9, roles=["DirectorTecnologico"], session_id=9)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def despacho_pendiente_unidad(mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa):
    """Seed pending despacho notification for unit 1."""
    from apps.despacho.services.asignacion_inteligente_service import AsignacionInteligenteService

    result = AsignacionInteligenteService().ejecutar(idaccidente=accidente_activo, idusuario=2)
    assert result is not None
    return result


# --- Soporte al cliente (gestion-tickets-soporte) ---


@pytest.fixture
def agente_soporte_auth_headers(mock_pinot, mock_kafka):
    """JWT for Soporte al cliente (agente) role with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 10,
            "idusuario": 10,
            "token": "session-token-10",
            "refresh_token": "refresh-token-10",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=10, roles=["Soporte"], session_id=10)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def desarrollador_apis_auth_headers(mock_pinot, mock_kafka):
    """JWT for Desarrollador de APIs role with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 11,
            "idusuario": 11,
            "token": "session-token-11",
            "refresh_token": "refresh-token-11",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(user_id=11, roles=["DesarrolladorAPIs"], session_id=11)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def cliente_soporte_auth_headers(cliente_auth_headers):
    """Alias for cliente_auth_headers (spec naming: soporte-cliente module)."""
    return cliente_auth_headers


@pytest.fixture
def director_tecnologico_soporte_auth_headers(director_tecnologico_auth_headers):
    """Alias for director_tecnologico_auth_headers (soporte-cliente escalado)."""
    return director_tecnologico_auth_headers


@pytest.fixture
def administrador_auth_headers(admin_auth_headers):
    """Alias for admin_auth_headers (spec naming: red_operativa module)."""
    return admin_auth_headers


@pytest.fixture
def operador_auth_headers_red_operativa(operador_auth_headers):
    """Alias for operador_auth_headers (spec naming: red_operativa module)."""
    return operador_auth_headers


@pytest.fixture
def proveedor_auth_headers(cliente_auth_headers):
    """JWT Proveedor/Cliente Activo (user 3 = admin_local de idcliente 1)."""
    return cliente_auth_headers


@pytest.fixture
def proveedor_billing_auth_headers(proveedor_auth_headers):
    """Alias billing — Proveedor autenticado (idcliente=1)."""
    return proveedor_auth_headers


@pytest.fixture
def admin_billing_auth_headers(admin_auth_headers):
    """Alias billing — Administrador."""
    return admin_auth_headers


@pytest.fixture
def director_estrategia_billing_auth_headers(mock_pinot, mock_kafka):
    """RF-SUSF-001 — DirectorEstrategia JWT with active session."""
    PINOT_STORE["Fact_Session"].append(
        {
            "idsession": 12,
            "idusuario": 12,
            "token": "session-token-12",
            "refresh_token": "refresh-token-12",
            "navegador": "pytest",
            "fechahorainiciosesion": "2026-07-09T00:00:00+00:00",
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        }
    )
    token = create_access_token(
        user_id=12, roles=["DirectorEstrategia"], session_id=12
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def mock_unidad_emergencia(mock_pinot, mock_kafka):
    """Seed an active Dim_UnidadEmergencia row for red_operativa tests."""
    unidad = {
        "idunidademergencia": 500,
        "idcliente": 1,
        "idcondado": 1,
        "tipopropiedad": "Externa",
        "placa": "RED-OP-500",
        "capacidad": "4",
        "contactoproveedor": "5555555555",
        "unidademergencia": "Grúa Red Operativa Test",
        "tipounidademergencia": "Grúa",
        "activo": True,
        "latitud": 19.4326,
        "longitud": -99.1332,
        "fecha_actualizacion": "2026-07-21T00:00:00+00:00",
    }
    PINOT_STORE["Dim_UnidadEmergencia"].append(unidad)
    return unidad


@pytest.fixture
def mock_despacho_activo(mock_pinot, mock_kafka, mock_unidad_emergencia):
    """Seed an active Fact_Despacho row for the seeded unidad (no fechahoraretiro)."""
    despacho = {
        "iddespacho": 900,
        "idaccidente": "ACC-RED-OP-TEST-1",
        "idunidademergencia": mock_unidad_emergencia["idunidademergencia"],
        "activo": True,
        "fechahoraretiro": None,
    }
    PINOT_STORE["Fact_Despacho"].append(despacho)
    return despacho
