"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from unittest.mock import patch

import bcrypt
import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import reiniciar_para_pruebas as reiniciar_secuencia


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
    # Catálogo canónico de severidades. Los planes guardan estos ids desde la
    # migración del 2026-08-11; antes había una escala paralela de nombres.
    "Dim_Severidad": [
        {
            "idseveridad": 1,
            "severidad": "Leve",
            "descripcion": "Daños materiales menores, sin heridos",
            "activo": True,
        },
        {
            "idseveridad": 2,
            "severidad": "Moderado",
            "descripcion": "Heridos leves o daños relevantes; requiere atención",
            "activo": True,
        },
        {
            "idseveridad": 3,
            "severidad": "Grave",
            "descripcion": "Heridos de consideración; prioridad alta de despacho",
            "activo": True,
        },
        {
            "idseveridad": 4,
            "severidad": "Fatal",
            "descripcion": "Víctimas mortales; máxima prioridad",
            "activo": True,
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
            "fechahorainiciosesion": 1783555200000,
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        },
        {
            "idsession": 3,
            "idusuario": 3,
            "token": "session-token-3",
            "refresh_token": "refresh-token-3",
            "navegador": "pytest",
            "fechahorainiciosesion": 1783555200000,
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
        },
        {
            "idsession": 4,
            "idusuario": 4,
            "token": "session-token-4",
            "refresh_token": "refresh-token-4",
            "navegador": "pytest",
            "fechahorainiciosesion": 1783555200000,
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
    # Declarada en `database/esquemas.json` y **sin ningún escritor**: el flujo
    # de transferencia de propiedad solo deja rastro en la bitácora de auditoría
    # (`AuditService.log_transferencia`). Se declara vacía porque la tabla
    # existe; que nadie la alimente está anotado en `decisiones-pendientes.md`.
    "Fact_HistorialTransferenciaPropiedad": [],
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
    "Fact_HistorialSeveridadAccidente": [],
    "Fact_CierreAccidente": [],
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
    "Dim_OrigenDespacho": [],
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
            "limites": '{"unidades_max": 5, "usuarios_max": 3, "api_calls_mes": 1000, "api_calls_minuto": 30}',
"precio_excedente_llamada": 0.06,
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": "[1]",
            "carga_lote_habilitada": False,
            "activo": True,
            "precio": 49.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idplan": 2,
            "nombre": "Profesional",
            "nivel": "Profesional",
            "limites": '{"unidades_max": 25, "usuarios_max": 10, "api_calls_mes": 10000, "api_calls_minuto": 120}',
"precio_excedente_llamada": 0.02,
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": "[1, 2]",
            "carga_lote_habilitada": True,
            "activo": True,
            "precio": 149.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idplan": 3,
            "nombre": "Empresarial",
            "nivel": "Empresarial",
            "limites": '{"unidades_max": 100, "usuarios_max": 50, "api_calls_mes": 100000, "api_calls_minuto": 600}',
"precio_excedente_llamada": 0.005,
            "periodicidad": "Anual",
            "severidades_desbloqueadas": "[1, 2, 3, 4]",
            "carga_lote_habilitada": True,
            "activo": True,
            "precio": 399.0,
            "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
        },
        {
            "idplan": 4,
            "nombre": "Legacy Off",
            "nivel": "Básico",
            "limites": '{"unidades_max": 1, "usuarios_max": 1, "api_calls_mes": 10, "api_calls_minuto": 5}',
"precio_excedente_llamada": 0.5,
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": "[1]",
            "carga_lote_habilitada": False,
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
            "periodicidad": "Mensual",
            "nivel": "Básico",
            "severidades_desbloqueadas": "[1]",
            "carga_lote_habilitada": True,
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
    # --- Partners y API (CU-O48 a CU-O55) ---
    "Dim_Partner": [],
    "Dim_CredencialAPI": [],
    "Fact_HistorialAccesoPartner": [],
    "Dim_VersionContratoAPI": [],
    # --- api-monitoring-and-billing (#08) ---
    "Fact_APIIntegracion": [],
    "Fact_LogLlamadaAPI": [],
    "Dim_EstadoIntegracion": [],
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

def _upsert_por_pk(rows: list, payload: dict, pk: str) -> None:
    """Upsert FULL por clave primaria, como hace Pinot con `upsertConfig`.

    Reemplaza la fila completa: publicar un payload parcial borra el resto de
    campos, igual que en Pinot real.
    """
    idx = next((i for i, r in enumerate(rows) if r.get(pk) == payload.get(pk)), None)
    if idx is not None:
        rows[idx] = payload
    else:
        rows.append(payload)


PINOT_STORE: dict[str, list[dict]] = {}


def _reset_pinot_store() -> None:
    import copy

    PINOT_STORE.clear()
    for table, rows in _INITIAL_PINOT_STORE.items():
        PINOT_STORE[table] = copy.deepcopy(rows)


_reset_pinot_store()


def _day_key_to_epoch_ms(day_key: str) -> int:
    """Convierte una clave de bucket 'YYYY-MM-DD' (o ISO semana 'YYYY-Www') de
    vuelta a epoch millis — DATETRUNC de Pinot real devuelve epoch millis, no
    un string, así que el doble del mock debe hacer lo mismo.

    (Antes esto remitía a `core/repositories/informes_tacticos/_periodo_utils.py`,
    borrado el 2026-08-19 con los informes tácticos agregados.)"""
    from datetime import datetime, timezone

    if "-W" in day_key:
        year, week = day_key.split("-W")
        dt = datetime.strptime(f"{year}-W{week}-1", "%G-W%V-%u").replace(tzinfo=timezone.utc)
    elif len(day_key) == 7:  # YYYY-MM
        dt = datetime.strptime(day_key, "%Y-%m").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.strptime(day_key, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _informe_keyset(filas: list[dict], sql_upper: str, params: dict, campos: list[str]) -> list[dict]:
    """Aplica cursor keyset, ORDER BY y LIMIT como lo haría Pinot.

    Se reproduce de verdad —y no con un recorte aproximado— porque la paginación
    de los listados tácticos ES lo que estas pruebas verifican (SC-005). Un doble
    que devolviera las primeras N filas sin honrar el cursor dejaría pasar
    exactamente el defecto que se está buscando: filas repetidas o saltadas entre
    páginas.
    """
    descendente = " DESC" in sql_upper

    if "%(CURSOR_0)S" in sql_upper:
        arranque = [params[f"cursor_{i}"] for i in range(len(campos))]

        def despues_del_cursor(fila: dict) -> bool:
            for i, campo in enumerate(campos):
                valor, tope = fila.get(campo), arranque[i]
                if valor != tope:
                    return valor < tope if descendente else valor > tope
            return False  # la fila del propio cursor no se repite

        filas = [f for f in filas if despues_del_cursor(f)]

    filas = sorted(filas, key=lambda f: tuple(f.get(c) for c in campos), reverse=descendente)
    return [dict(f) for f in filas[: params.get("limit", len(filas))]]


def _informes_ventas_crm(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tácticos de Ventas y CRM.

    Misma razón que en Cuentas y Clientes para ir antes que las ramas genéricas:
    `FROM DIM_PROSPECTO` captura por `IDUSUARIO =` y devolvería la fila entera,
    con `gmail` y `telefono` incluidos — es decir, escondería justo el defecto
    que research D4 prohíbe.
    """
    # ── L1 — Cartera de prospectos ───────────────────────────────────────────
    if "SELECT IDPROSPECTO, EMPRESA, NOMBRES, APELLIDOS, CARGO" in sql_upper:
        filas = list(PINOT_STORE["Dim_Prospecto"])
        if "IDUSUARIO = %(TITULAR)S" in sql_upper:
            filas = [f for f in filas if f.get("idusuario") == params.get("titular")]
        if "COMO_NOS_CONOCIO = %(CANAL)S" in sql_upper:
            filas = [f for f in filas if f.get("como_nos_conocio") == params.get("canal")]
        if "TIPO_ORGANIZACION = %(TIPO_ORGANIZACION)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("tipo_organizacion") == params.get("tipo_organizacion")
            ]
        if "ETAPA_ACTUAL = %(ETAPA)S" in sql_upper:
            filas = [f for f in filas if f.get("etapa_actual") == params.get("etapa")]
        if "ACTIVO = TRUE" in sql_upper:
            filas = [f for f in filas if f.get("activo") is True]
        if "MOTIVO_INACTIVIDAD = %(MOTIVO)S" in sql_upper:
            filas = [
                f for f in filas if f.get("motivo_inactividad") == params.get("motivo")
            ]
        filas = _informe_keyset(filas, sql_upper, params, ["idprospecto"])
        # Se recortan las columnas que la consulta enumera. Sin esto, `gmail` y
        # `telefono` llegarían a la respuesta en las pruebas y la fuga solo
        # aparecería contra Pinot real.
        return [
            {
                k: f.get(k)
                for k in (
                    "idprospecto", "empresa", "nombres", "apellidos", "cargo",
                    "tipo_organizacion", "como_nos_conocio", "etapa_actual",
                    "idusuario", "activo", "motivo_inactividad", "valor_estimado",
                    "fecha_registro",
                )
            }
            for f in filas
        ]

    # ── L3 — Demos activas (prefiltro por prefijo de fecha) ──────────────────
    if "SELECT IDPROSPECTO, EMPRESA, NOMBRES, APELLIDOS, IDUSUARIO, DEMO_EXPIRACION" in sql_upper:
        # ⚠️ La comparación es de TEXTO, igual que en Pinot: es exactamente lo
        # que hace que el prefijo `YYYY-MM-DD` sea la única parte segura — y
        # también lo que dejaba pasar el centinela `'null'`, porque cualquier
        # letra ordena después de cualquier dígito. El doble lo reproduce ahora,
        # incluido el `NOT IN` que lo excluye.
        centinelas = set(params.get("sin_demo") or [])
        filas = [
            f for f in PINOT_STORE["Dim_Prospecto"]
            if str(f.get("demo_expiracion") or "") not in centinelas
            and str(f.get("demo_expiracion") or "") >= params["prefijo_hoy"]
        ]
        if "IDUSUARIO = %(TITULAR)S" in sql_upper:
            filas = [f for f in filas if f.get("idusuario") == params.get("titular")]
        filas = _informe_keyset(filas, sql_upper, params, ["demo_expiracion", "idprospecto"])
        return [
            {
                k: f.get(k)
                for k in (
                    "idprospecto", "empresa", "nombres", "apellidos",
                    "idusuario", "demo_expiracion",
                )
            }
            for f in filas
        ]

    # ── L4 — Notificaciones enviadas (sin `estado_envio`) ────────────────────
    if "SELECT IDNOTIFICACION, ID_PROSPECTO, IDUSUARIOGERENTENOTIFICADO" in sql_upper:
        filas = list(PINOT_STORE["Fact_NotificacionVentas"])
        if "IDUSUARIOGERENTENOTIFICADO = %(TITULAR)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("idusuariogerentenotificado") == params.get("titular")
            ]
        if "FECHAHORANOTIFICACION >= %(DESDE_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoranotificacion") or 0) >= params["desde_ms"]
            ]
        if "FECHAHORANOTIFICACION <= %(HASTA_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoranotificacion") or 0) <= params["hasta_ms"]
            ]
        if "REGLADISPARADA = %(REGLA)S" in sql_upper:
            filas = [f for f in filas if f.get("regladisparada") == params.get("regla")]
        if "CANAL = %(CANAL)S" in sql_upper:
            filas = [f for f in filas if f.get("canal") == params.get("canal")]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahoranotificacion", "idnotificacion"]
        )
        # `estado_envio` se recorta aquí: sin esto llegaría a la respuesta en las
        # pruebas y solo se notaría contra Pinot real.
        return [
            {
                k: f.get(k)
                for k in (
                    "idnotificacion", "id_prospecto", "idusuariogerentenotificado",
                    "regladisparada", "canal", "fechahoranotificacion",
                )
            }
            for f in filas
        ]

    # ── L2 — Reasignaciones de cartera ───────────────────────────────────────
    if "SELECT IDASIGNACION, IDPROSPECTO, IDUSUARIOGERENTEANTERIOR" in sql_upper:
        filas = list(PINOT_STORE["Fact_Asignacion"])
        if "FECHAHORAASIGNACION >= %(DESDE_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoraasignacion") or 0) >= params["desde_ms"]
            ]
        if "FECHAHORAASIGNACION <= %(HASTA_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoraasignacion") or 0) <= params["hasta_ms"]
            ]
        if "IDPROSPECTO = %(IDPROSPECTO)S" in sql_upper:
            filas = [f for f in filas if f.get("idprospecto") == params.get("idprospecto")]
        if "TIPOASIGNACION = %(TIPO_ASIGNACION)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("tipoasignacion") == params.get("tipo_asignacion")
            ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahoraasignacion", "idasignacion"]
        )
        return [
            {
                k: f.get(k)
                for k in (
                    "idasignacion", "idprospecto", "idusuariogerenteanterior",
                    "idusuariogerenteactual", "tipoasignacion", "motivo",
                    "fechahoraasignacion",
                )
            }
            for f in filas
        ]

    if "SELECT IDASIGNACION, TIPOASIGNACION FROM FACT_ASIGNACION" in sql_upper:
        return [
            {"idasignacion": f.get("idasignacion"), "tipoasignacion": f.get("tipoasignacion")}
            for f in PINOT_STORE["Fact_Asignacion"]
        ]

    if "SELECT IDPROSPECTO, EMPRESA FROM DIM_PROSPECTO" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idprospecto": f["idprospecto"], "empresa": f.get("empresa")}
            for f in PINOT_STORE["Dim_Prospecto"]
            if f["idprospecto"] in permitidos
        ]

    if "SELECT ID_PROSPECTO, MOTIVO_PERDIDA, FECHA_TRANSICION FROM FACT_PIPELINE" in sql_upper:
        permitidos = set(params.get("ids") or [])
        filas = [
            f for f in PINOT_STORE["Fact_Pipeline"]
            if f.get("id_prospecto") in permitidos
            and f.get("etapa_nueva") == params.get("etapa")
        ]
        filas.sort(key=lambda f: f.get("fecha_transicion") or 0, reverse=True)
        return [
            {k: f.get(k) for k in ("id_prospecto", "motivo_perdida", "fecha_transicion")}
            for f in filas
        ]

    return None


def _informes_partners(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tácticos de Partners y API.

    Antes que las ramas genéricas: `FROM DIM_CREDENCIALAPI` devolvería la fila
    entera con `client_secret_hash` incluido — es decir, escondería la fuga que
    research D3 prohíbe.
    """
    # ── L1 — Partners ────────────────────────────────────────────────────────
    if "SELECT IDPARTNER, IDCLIENTE, NOMBREPARTNER, PLANAPI" in sql_upper:
        filas = list(PINOT_STORE["Dim_Partner"])
        if "IDCLIENTE = %(CUENTA)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("cuenta")]
        if "PLANAPI = %(PLAN)S" in sql_upper:
            filas = [f for f in filas if f.get("planapi") == params.get("plan")]
        if "ACTIVO = %(ACTIVO)S" in sql_upper:
            filas = [f for f in filas if bool(f.get("activo")) is params.get("activo")]
        if "PLANAPI <> %(SIN_PLAN)S" in sql_upper:
            filas = [f for f in filas if (f.get("planapi") or "") != params["sin_plan"]]
        elif "PLANAPI = %(SIN_PLAN)S" in sql_upper:
            filas = [f for f in filas if (f.get("planapi") or "") == params["sin_plan"]]
        filas = _informe_keyset(filas, sql_upper, params, ["idpartner"])
        from core.repositories.partners.informes_acceso_repository import (
            COLUMNAS_PARTNER,
        )

        return [{k: f.get(k) for k in COLUMNAS_PARTNER} for f in filas]

    # ── L2 — Credenciales (sin `client_secret_hash`) ─────────────────────────
    if "SELECT IDCREDENCIAL, IDPARTNER, IDCLIENTE, ENTORNO, ACTIVO" in sql_upper:
        filas = list(PINOT_STORE["Dim_CredencialAPI"])
        if "IDCLIENTE = %(CUENTA)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("cuenta")]
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            filas = [f for f in filas if f.get("idpartner") == params.get("idpartner")]
        if "ENTORNO = %(ENTORNO)S" in sql_upper:
            filas = [f for f in filas if f.get("entorno") == params.get("entorno")]
        if "ACTIVO = %(ACTIVA)S" in sql_upper:
            filas = [f for f in filas if bool(f.get("activo")) is params.get("activa")]
        if "FECHA_EXPIRACION <= %(CADUCA_ANTES_DE)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fecha_expiracion") or 0) <= params["caduca_antes_de"]
            ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fecha_expiracion", "idcredencial"]
        )
        # El secreto se recorta aquí. Sin esto llegaría a la respuesta en las
        # pruebas y la fuga solo aparecería contra Pinot real.
        from core.repositories.partners.informes_acceso_repository import (
            COLUMNAS_CREDENCIAL,
        )

        return [{k: f.get(k) for k in COLUMNAS_CREDENCIAL} for f in filas]

    if "SELECT IDPARTNER, ENTORNO, ACTIVO FROM DIM_CREDENCIALAPI" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idpartner", "entorno", "activo")}
            for f in PINOT_STORE["Dim_CredencialAPI"]
            if f.get("idpartner") in permitidos
        ]

    if "SELECT IDCREDENCIAL, NOMBRE_CREDENCIAL FROM DIM_CREDENCIALAPI" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idcredencial", "nombre_credencial")}
            for f in PINOT_STORE["Dim_CredencialAPI"]
            if f.get("idcredencial") in permitidos
        ]

    if "SELECT IDPARTNER, TIPO_CAMBIO, FECHA_CAMBIO FROM FACT_HISTORIALACCESOPARTNER" in sql_upper:
        permitidos = set(params.get("ids") or [])
        tipos = set(params.get("tipos") or [])
        return [
            {k: f.get(k) for k in ("idpartner", "tipo_cambio", "fecha_cambio")}
            for f in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if f.get("idpartner") in permitidos and f.get("tipo_cambio") in tipos
        ]

    if "SELECT IDPARTNER, NOMBREPARTNER FROM DIM_PARTNER" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idpartner": f["idpartner"], "nombrepartner": f.get("nombrepartner")}
            for f in PINOT_STORE["Dim_Partner"]
            if f["idpartner"] in permitidos
        ]

    if "SELECT IDPARTNER, IDCLIENTE FROM DIM_PARTNER" in sql_upper:
        return [
            {"idpartner": f["idpartner"], "idcliente": f.get("idcliente")}
            for f in PINOT_STORE["Dim_Partner"]
            if f.get("idcliente") == params.get("idcliente")
        ]

    # ── L3 — Cambios de acceso ───────────────────────────────────────────────
    if "SELECT IDHISTORIAL, IDPARTNER, IDCREDENCIAL, TIPO_CAMBIO" in sql_upper:
        filas = list(PINOT_STORE["Fact_HistorialAccesoPartner"])
        if "IDPARTNER IN %(IDPARTNERS)S" in sql_upper:
            permitidos = set(params.get("idpartners") or [])
            filas = [f for f in filas if f.get("idpartner") in permitidos]
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            filas = [f for f in filas if f.get("idpartner") == params.get("idpartner")]
        if "TIPO_CAMBIO = %(TIPO_CAMBIO)S" in sql_upper:
            filas = [f for f in filas if f.get("tipo_cambio") == params.get("tipo_cambio")]
        if "FECHA_CAMBIO >= %(DESDE_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fecha_cambio") or 0) >= params["desde_ms"]]
        if "FECHA_CAMBIO <= %(HASTA_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fecha_cambio") or 0) <= params["hasta_ms"]]
        filas = _informe_keyset(filas, sql_upper, params, ["fecha_cambio", "idhistorial"])
        from core.repositories.partners.informes_bitacora_repository import (
            COLUMNAS_BITACORA,
        )

        return [{k: f.get(k) for k in COLUMNAS_BITACORA} for f in filas]

    # ── L4 — Versiones del contrato ──────────────────────────────────────────
    if "SELECT IDVERSION, ID_SERVICIO, VERSION, ESTADO" in sql_upper:
        filas = list(PINOT_STORE["Dim_VersionContratoAPI"])
        if "ESTADO = %(ESTADO)S" in sql_upper:
            filas = [f for f in filas if f.get("estado") == params.get("estado")]
        if "ID_SERVICIO = %(ID_SERVICIO)S" in sql_upper:
            filas = [f for f in filas if f.get("id_servicio") == params.get("id_servicio")]
        filas = _informe_keyset(filas, sql_upper, params, ["fecha_publicacion", "idversion"])
        from core.repositories.partners.informes_contrato_repository import (
            COLUMNAS_VERSION,
        )

        return [{k: f.get(k) for k in COLUMNAS_VERSION} for f in filas]

    # ── L5 — Alcance de datos ────────────────────────────────────────────────
    if "SELECT ID_PREFERENCIA, ID_CLIENTE, FRECUENCIA_REPORTES" in sql_upper:
        filas = list(PINOT_STORE["Dim_Preferencias_Cliente"])
        if "ID_CLIENTE = %(ID_CLIENTE)S" in sql_upper:
            filas = [f for f in filas if f.get("id_cliente") == params.get("id_cliente")]
        if "FRECUENCIA_REPORTES = %(FRECUENCIA)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("frecuencia_reportes") == params.get("frecuencia")
            ]
        filas = _informe_keyset(filas, sql_upper, params, ["id_preferencia"])
        from core.repositories.partners.informes_contrato_repository import (
            COLUMNAS_ALCANCE,
        )

        return [{k: f.get(k) for k in COLUMNAS_ALCANCE} for f in filas]

    if "SELECT ID_SERVICIO, NOMBRE FROM DIM_SERVICIO" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"id_servicio": f["id_servicio"], "nombre": f.get("nombre")}
            for f in PINOT_STORE["Dim_Servicio"]
            if f["id_servicio"] in permitidos
        ]

    return None


def _informes_red_operativa(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tácticos de Red Operativa.

    Antes que las ramas genéricas por la misma razón de siempre: `FROM
    DIM_UNIDADEMERGENCIA` devolvería la fila entera, con `latitud`, `longitud` y
    `contactoproveedor` incluidos — es decir, escondería la fuga que research D6
    prohíbe.
    """
    # ── L1 — Composición de la flota ─────────────────────────────────────────
    if "SELECT IDUNIDADEMERGENCIA, IDCLIENTE, PLACA, UNIDADEMERGENCIA" in sql_upper:
        filas = list(PINOT_STORE["Dim_UnidadEmergencia"])
        if "IDCLIENTE = %(PROVEEDOR)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("proveedor")]
        if "IDCONDADO = %(IDCONDADO)S" in sql_upper:
            filas = [f for f in filas if f.get("idcondado") == params.get("idcondado")]
        if "TIPOUNIDADEMERGENCIA = %(TIPO_UNIDAD)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("tipounidademergencia") == params.get("tipo_unidad")
            ]
        if "ACTIVO = %(DADO_DE_ALTA)S" in sql_upper:
            filas = [
                f for f in filas if bool(f.get("activo")) is params.get("dado_de_alta")
            ]
        filas = _informe_keyset(filas, sql_upper, params, ["idunidademergencia"])
        # Se recortan las columnas enumeradas. Sin esto, `latitud`, `longitud` y
        # `contactoproveedor` llegarían a la respuesta en las pruebas y la fuga
        # solo aparecería contra Pinot real.
        return [
            {
                k: f.get(k)
                for k in (
                    "idunidademergencia", "idcliente", "placa", "unidademergencia",
                    "tipounidademergencia", "capacidad", "idcondado",
                    "zonacobertura", "tipopropiedad", "activo",
                )
            }
            for f in filas
        ]

    if "SELECT IDUNIDADEMERGENCIA, TIPOUNIDADEMERGENCIA FROM DIM_UNIDADEMERGENCIA" in sql_upper:
        return [
            {
                "idunidademergencia": f.get("idunidademergencia"),
                "tipounidademergencia": f.get("tipounidademergencia"),
            }
            for f in PINOT_STORE["Dim_UnidadEmergencia"]
        ]

    if "SELECT IDUNIDADEMERGENCIA, IDCLIENTE FROM DIM_UNIDADEMERGENCIA" in sql_upper:
        return [
            {"idunidademergencia": f["idunidademergencia"], "idcliente": f.get("idcliente")}
            for f in PINOT_STORE["Dim_UnidadEmergencia"]
            if f.get("idcliente") == params.get("idcliente")
        ]

    if "SELECT IDUNIDADEMERGENCIA, PLACA, IDCLIENTE FROM DIM_UNIDADEMERGENCIA" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idunidademergencia", "placa", "idcliente")}
            for f in PINOT_STORE["Dim_UnidadEmergencia"]
            if f["idunidademergencia"] in permitidos
        ]

    if "SELECT IDCONDADO, CONDADO, IDESTADO FROM DIM_CONDADO WHERE IDCONDADO IN" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idcondado", "condado", "idestado")}
            for f in PINOT_STORE["Dim_Condado"]
            if f["idcondado"] in permitidos
        ]

    if "SELECT IDESTADO, ESTADO FROM DIM_ESTADO" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idestado": f["idestado"], "estado": f.get("estado")}
            for f in PINOT_STORE["Dim_Estado"]
            if f["idestado"] in permitidos
        ]

    # ── L2 — Bajas de unidad ─────────────────────────────────────────────────
    if "SELECT IDBAJAUNIDAD, IDUNIDADEMERGENCIA, IDUSUARIO, IDACCIDENTE" in sql_upper:
        filas = list(PINOT_STORE["Fact_BajaUnidad"])
        if "IDUNIDADEMERGENCIA IN %(IDUNIDADES)S" in sql_upper:
            permitidos = set(params.get("idunidades") or [])
            filas = [f for f in filas if f.get("idunidademergencia") in permitidos]
        if "TIPOBAJA = %(TIPO_BAJA)S" in sql_upper:
            filas = [f for f in filas if f.get("tipobaja") == params.get("tipo_baja")]
        if "FECHAHORA >= %(DESDE_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fechahora") or 0) >= params["desde_ms"]]
        if "FECHAHORA <= %(HASTA_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fechahora") or 0) <= params["hasta_ms"]]
        filas = _informe_keyset(filas, sql_upper, params, ["fechahora", "idbajaunidad"])
        return [
            {
                k: f.get(k)
                for k in (
                    "idbajaunidad", "idunidademergencia", "idusuario", "idaccidente",
                    "motivo", "tipobaja", "fechahora",
                )
            }
            for f in filas
        ]

    # ── L3 — Regiones operativas ─────────────────────────────────────────────
    if "SELECT IDREGIONOPERATIVA, IDESTADO, NOMBREREGION, ESTADOREGION" in sql_upper:
        filas = list(PINOT_STORE["Dim_RegionOperativa"])
        if "ESTADOREGION = %(ESTADO_REGION)S" in sql_upper:
            filas = [
                f for f in filas if f.get("estadoregion") == params.get("estado_region")
            ]
        if "FECHA_ACTUALIZACION <= %(SIN_CAMBIO_DESDE)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fecha_actualizacion") or 0) <= params["sin_cambio_desde"]
            ]
        filas = _informe_keyset(filas, sql_upper, params, ["idregionoperativa"])
        return [
            {
                k: f.get(k)
                for k in (
                    "idregionoperativa", "idestado", "nombreregion", "estadoregion",
                    "activo", "fecha_actualizacion",
                )
            }
            for f in filas
        ]

    if "SELECT IDREGIONOPERATIVA, NOMBREREGION FROM DIM_REGIONOPERATIVA" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idregionoperativa": f["idregionoperativa"], "nombreregion": f.get("nombreregion")}
            for f in PINOT_STORE["Dim_RegionOperativa"]
            if f["idregionoperativa"] in permitidos
        ]

    # ── L4 — Intentos de validación ──────────────────────────────────────────
    if "SELECT IDVALIDACIONREGION, IDREGIONOPERATIVA, IDUSUARIO, RESULTADO" in sql_upper:
        filas = list(PINOT_STORE["Dim_ValidacionRegion"])
        if "IDREGIONOPERATIVA = %(IDREGION)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("idregionoperativa") == params.get("idregion")
            ]
        if "RESULTADO = %(RESULTADO)S" in sql_upper:
            filas = [f for f in filas if f.get("resultado") == params.get("resultado")]
        if "FECHAHORA >= %(DESDE_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fechahora") or 0) >= params["desde_ms"]]
        if "FECHAHORA <= %(HASTA_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fechahora") or 0) <= params["hasta_ms"]]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahora", "idvalidacionregion"]
        )
        return [
            {
                k: f.get(k)
                for k in (
                    "idvalidacionregion", "idregionoperativa", "idusuario",
                    "resultado", "motivo", "fechahora",
                )
            }
            for f in filas
        ]

    if "SELECT IDVALIDACIONREGION, RESULTADO FROM DIM_VALIDACIONREGION" in sql_upper:
        return [
            {"idvalidacionregion": f.get("idvalidacionregion"), "resultado": f.get("resultado")}
            for f in PINOT_STORE["Dim_ValidacionRegion"]
        ]

    return None


def _informes_suscripciones(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tácticos de Suscripciones y Facturación.

    Va antes que las ramas genéricas por la misma razón que los otros dos
    módulos: `FROM DIM_METODOPAGO` devolvería la fila entera, con `tokenpasarela`
    incluido — es decir, escondería la fuga que research D4 prohíbe.
    """
    # ── L1 — Suscripciones ───────────────────────────────────────────────────
    if "SELECT ID_SUSCRIPCION, IDCLIENTE, IDPLAN, IDPLAN_PROGRAMADO" in sql_upper:
        filas = list(PINOT_STORE["Fact_Suscripcion"])
        if "IDCLIENTE = %(CUENTA)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("cuenta")]
        if "ESTADO = %(ESTADO)S" in sql_upper:
            filas = [f for f in filas if f.get("estado") == params.get("estado")]
        if "IDPLAN = %(IDPLAN)S" in sql_upper:
            filas = [f for f in filas if f.get("idplan") == params.get("idplan")]
        if "IDPLAN_PROGRAMADO > %(SIN_CAMBIO)S" in sql_upper:
            filas = [
                f for f in filas
                if int(f.get("idplan_programado") or 0) > params["sin_cambio"]
            ]
        if "IDPLAN_PROGRAMADO <= %(SIN_CAMBIO)S" in sql_upper:
            filas = [
                f for f in filas
                if int(f.get("idplan_programado") or 0) <= params["sin_cambio"]
            ]
        if "FECHA_FIN <= %(VENCE_ANTES_DE)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fecha_fin") or 0) <= params["vence_antes_de"]
            ]
        if "FECHACANCELACION >= %(CANCELADA_DESDE)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechacancelacion") or 0) >= params["cancelada_desde"]
            ]
        if "FECHACANCELACION <= %(CANCELADA_HASTA)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("fechacancelacion") is not None
                and f["fechacancelacion"] <= params["cancelada_hasta"]
            ]
        filas = _informe_keyset(filas, sql_upper, params, ["id_suscripcion"])
        return [
            {
                k: f.get(k)
                for k in (
                    "id_suscripcion", "idcliente", "idplan", "idplan_programado",
                    "estado", "nivel", "precio", "periodicidad",
                    "renovacionautomatica", "motivocancelacion", "fecha_inicio",
                    "fecha_fin", "fechacancelacion",
                )
            }
            for f in filas
        ]

    # ── L2 — Facturas ────────────────────────────────────────────────────────
    if "SELECT ID_FACTURA, ID_CLIENTE, NUMERO_FACTURA" in sql_upper:
        filas = list(PINOT_STORE["Fact_Factura"])
        if "ID_CLIENTE = %(CUENTA)S" in sql_upper:
            filas = [f for f in filas if f.get("id_cliente") == params.get("cuenta")]
        if "ESTADO_PAGO = %(ESTADO_PAGO)S" in sql_upper:
            filas = [f for f in filas if f.get("estado_pago") == params.get("estado_pago")]
        if "FECHA_EMISION >= %(DESDE_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fecha_emision") or 0) >= params["desde_ms"]]
        if "FECHA_EMISION <= %(HASTA_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fecha_emision") or 0) <= params["hasta_ms"]]
        if "FECHA_VENCIMIENTO < %(VENCIDAS_ANTES_DE)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fecha_vencimiento") or 0) < params["vencidas_antes_de"]
            ]
        if "ESTADO_PAGO IN %(ESTADOS_MORA)S" in sql_upper:
            permitidos = set(params.get("estados_mora") or [])
            filas = [f for f in filas if f.get("estado_pago") in permitidos]
        filas = _informe_keyset(filas, sql_upper, params, ["fecha_emision", "id_factura"])
        return [
            {
                k: f.get(k)
                for k in (
                    "id_factura", "id_cliente", "numero_factura", "periodo", "tipo",
                    "es_nota_credito", "estado_pago", "reintentos", "monto_base",
                    "impuestos", "monto_total", "fecha_emision", "fecha_vencimiento",
                )
            }
            for f in filas
        ]

    # ── L4 — Métodos de pago vigentes (sin `tokenpasarela`) ──────────────────
    if "SELECT IDMETODOPAGO, IDCLIENTE, TIPO, ULTIMOSDIGITOS" in sql_upper:
        filas = [f for f in PINOT_STORE["Dim_MetodoPago"] if f.get("activo")]
        if "IDCLIENTE = %(CUENTA)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("cuenta")]
        if "FECHAEXPIRACION <= %(CADUCA_ANTES_DE)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechaexpiracion") or 0) <= params["caduca_antes_de"]
            ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechaexpiracion", "idmetodopago"]
        )
        # `tokenpasarela` se recorta aquí. Sin esto llegaría a la respuesta en
        # las pruebas y la fuga solo aparecería contra Pinot real — que es
        # exactamente lo que la prueba de research D4 existe para impedir.
        return [
            {
                k: f.get(k)
                for k in ("idmetodopago", "idcliente", "tipo", "ultimosdigitos",
                          "fechaexpiracion")
            }
            for f in filas
        ]

    # ── L3 — Solicitudes de cambio de plan ───────────────────────────────────
    if "SELECT IDSOLICITUD, IDCLIENTE, IDPLANACTUAL, IDPLANSOLICITADO" in sql_upper:
        filas = list(PINOT_STORE["Fact_Solicitud_Cambio_Plan"])
        if "IDCLIENTE = %(CUENTA)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("cuenta")]
        if "ESTADO = %(ESTADO)S" in sql_upper:
            filas = [f for f in filas if f.get("estado") == params.get("estado")]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fecha_solicitud", "idsolicitud"]
        )
        return [
            {
                k: f.get(k)
                for k in (
                    "idsolicitud", "idcliente", "idplanactual", "idplansolicitado",
                    "estado", "motivo", "idadminaprobador", "motivo_rechazo",
                    "fecha_solicitud", "fecha_resolucion",
                )
            }
            for f in filas
        ]

    if "SELECT IDPLAN, NOMBRE FROM DIM_PLAN" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idplan": f["idplan"], "nombre": f.get("nombre")}
            for f in PINOT_STORE["Dim_Plan"]
            if f["idplan"] in permitidos
        ]

    return None


def _informes_cuentas_clientes(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tácticos de Cuentas y Clientes.

    Va **antes** que las ramas genéricas de `Dim_Usuarios`, `Dim_Cliente` y
    compañía: aquellas despachan por `WHERE ...` y capturarían estas consultas
    devolviendo otra cosa. El despacho aquí es por la **lista de columnas
    enumerada**, que es única por listado — y que existe porque research D7
    prohíbe `SELECT *` sobre las tablas con material sensible.

    Devuelve `None` si la consulta no es de este módulo, para que el enrutador
    siga probando el resto de ramas.
    """
    # ── L1 — Solicitudes de alta pendientes ──────────────────────────────────
    if "SELECT IDCLIENTE, RAZON_SOCIAL, TIPO, FECHA_CREACION FROM DIM_CLIENTE" in sql_upper:
        filas = [
            f for f in PINOT_STORE["Dim_Cliente"]
            if f.get("estado") == params.get("estado")
        ]
        if "TIPO = %(TIPO)S" in sql_upper:
            filas = [f for f in filas if f.get("tipo") == params.get("tipo")]
        if "FECHA_CREACION <= %(CREADAS_ANTES_DE)S" in sql_upper:
            corte = params["creadas_antes_de"]
            filas = [f for f in filas if (f.get("fecha_creacion") or 0) <= corte]
        filas = _informe_keyset(filas, sql_upper, params, ["fecha_creacion", "idcliente"])
        return [
            {k: f.get(k) for k in ("idcliente", "razon_social", "tipo", "fecha_creacion")}
            for f in filas
        ]

    # ── L2 — Incorporación incompleta ────────────────────────────────────────
    if "SELECT ID_ONBOARDING, ID_CLIENTE, ETAPA, FECHA_ACTUALIZACION FROM FACT_ONBOARDING" in sql_upper:
        filas = [f for f in PINOT_STORE["Fact_Onboarding"] if not f.get("completado")]
        if "ETAPA = %(ETAPA)S" in sql_upper:
            filas = [f for f in filas if f.get("etapa") == params.get("etapa")]
        if "FECHA_ACTUALIZACION <= %(DETENIDAS_ANTES_DE)S" in sql_upper:
            corte = params["detenidas_antes_de"]
            filas = [f for f in filas if (f.get("fecha_actualizacion") or 0) <= corte]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fecha_actualizacion", "id_onboarding"]
        )
        return [
            {k: f.get(k) for k in ("id_onboarding", "id_cliente", "etapa", "fecha_actualizacion")}
            for f in filas
        ]

    if "SELECT ID_ONBOARDING, ETAPA FROM FACT_ONBOARDING" in sql_upper:
        return [
            {"id_onboarding": f.get("id_onboarding"), "etapa": f.get("etapa")}
            for f in PINOT_STORE["Fact_Onboarding"]
        ]

    if "SELECT IDCLIENTE, RAZON_SOCIAL FROM DIM_CLIENTE" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idcliente": f["idcliente"], "razon_social": f.get("razon_social")}
            for f in PINOT_STORE["Dim_Cliente"]
            if f["idcliente"] in permitidos
        ]

    # ── L3 — Cuentas por estado ──────────────────────────────────────────────
    if "SELECT IDCLIENTE, RAZON_SOCIAL, TIPO, ESTADO, ESTADO_ONBOARDING" in sql_upper:
        filas = list(PINOT_STORE["Dim_Cliente"])
        if "ESTADO = %(ESTADO)S" in sql_upper:
            filas = [f for f in filas if f.get("estado") == params.get("estado")]
        if "TIPO = %(TIPO)S" in sql_upper:
            filas = [f for f in filas if f.get("tipo") == params.get("tipo")]
        filas = _informe_keyset(filas, sql_upper, params, ["idcliente"])
        return [
            {
                k: f.get(k)
                for k in (
                    "idcliente",
                    "razon_social",
                    "tipo",
                    "estado",
                    "estado_onboarding",
                    "fecha_inicio_contrato",
                    "admin_local_id",
                )
            }
            for f in filas
        ]

    # ── L4 — Transferencias de propiedad ─────────────────────────────────────
    if "FROM FACT_HISTORIALTRANSFERENCIAPROPIEDAD" in sql_upper and "IDUSUARIOANTERIOR" in sql_upper:
        filas = list(PINOT_STORE["Fact_HistorialTransferenciaPropiedad"])
        if "FECHAHORA >= %(DESDE_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fechahora") or 0) >= params["desde_ms"]]
        if "FECHAHORA <= %(HASTA_MS)S" in sql_upper:
            filas = [f for f in filas if (f.get("fechahora") or 0) <= params["hasta_ms"]]
        if "IDCLIENTE = %(IDCLIENTE)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("idcliente")]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahora", "idhistorialtransferencia"]
        )
        return [
            {
                k: f.get(k)
                for k in (
                    "idhistorialtransferencia",
                    "idcliente",
                    "idusuarioanterior",
                    "idusuarionuevo",
                    "fechahora",
                )
            }
            for f in filas
        ]

    if "SELECT IDUSUARIO, NOMBRES, APELLIDOS FROM DIM_USUARIOS" in sql_upper:
        ids = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idusuario", "nombres", "apellidos")}
            for f in PINOT_STORE["Dim_Usuarios"]
            if f["idusuario"] in ids
        ]

    # ── L5 — Usuarios y sus roles ────────────────────────────────────────────
    if "SELECT IDUSUARIO, NOMBRES, APELLIDOS, GMAIL, ACTIVO FROM DIM_USUARIOS" in sql_upper:
        filas = list(PINOT_STORE["Dim_Usuarios"])
        if "ACTIVO = %(ACTIVO)S" in sql_upper:
            filas = [f for f in filas if bool(f.get("activo")) is params.get("activo")]
        if "IDUSUARIO IN %(IDUSUARIOS)S" in sql_upper:
            permitidos = set(params.get("idusuarios") or [])
            filas = [f for f in filas if f["idusuario"] in permitidos]
        return _informe_keyset(filas, sql_upper, params, ["idusuario"])

    if "SELECT IDUSUARIO, NOMBRES, APELLIDOS, GMAIL FROM DIM_USUARIOS" in sql_upper:
        ids = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idusuario", "nombres", "apellidos", "gmail")}
            for f in PINOT_STORE["Dim_Usuarios"]
            if f["idusuario"] in ids
        ]

    if "SELECT IDUSUARIO, IDROL FROM DIM_USUARIO_ROL" in sql_upper:
        filas = [f for f in PINOT_STORE["Dim_Usuario_Rol"] if f.get("activo", True)]
        if "IDUSUARIO IN %(IDUSUARIOS)S" in sql_upper:
            permitidos = set(params.get("idusuarios") or [])
            filas = [f for f in filas if f["idusuario"] in permitidos]
        if "IDROL IN %(IDROLES)S" in sql_upper:
            permitidos = set(params.get("idroles") or [])
            filas = [f for f in filas if f["idrol"] in permitidos]
        return [{"idusuario": f["idusuario"], "idrol": f["idrol"]} for f in filas]

    if "SELECT IDROL FROM DIM_ROL WHERE ROL = %(ROL)S" in sql_upper:
        return [
            {"idrol": r["idrol"]}
            for r in PINOT_STORE["Dim_Rol"]
            if r.get("rol") == params.get("rol") and r.get("activo")
        ]

    if "SELECT IDROL, ROL FROM DIM_ROL" in sql_upper:
        filas = list(PINOT_STORE["Dim_Rol"])
        if "IDROL IN %(IDROLES)S" in sql_upper:
            permitidos = set(params.get("idroles") or [])
            filas = [f for f in filas if f["idrol"] in permitidos]
        if "ACTIVO = TRUE" in sql_upper:
            filas = [f for f in filas if f.get("activo")]
        return [{"idrol": f["idrol"], "rol": f.get("rol")} for f in filas]

    # ── L6 — Sesiones abiertas (sin `token`) ─────────────────────────────────
    if "SELECT IDSESSION, IDUSUARIO, NAVEGADOR, FECHAHORAINICIOSESION FROM FACT_SESSION" in sql_upper:
        filas = [
            f for f in PINOT_STORE["Fact_Session"]
            if f.get("estadosession") == params.get("estado")
        ]
        if "IDUSUARIO = %(IDUSUARIO)S" in sql_upper:
            filas = [f for f in filas if f["idusuario"] == params.get("idusuario")]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahorainiciosesion", "idsession"]
        )
        # El doble guarda la fila entera; la consulta real solo trae 4 columnas.
        # Recortarlas aquí es lo que hace que la prueba de research D7 signifique
        # algo: sin esto, `token` llegaría a la respuesta en las pruebas y el
        # fallo solo aparecería contra Pinot real.
        return [
            {k: f.get(k) for k in ("idsession", "idusuario", "navegador", "fechahorainiciosesion")}
            for f in filas
        ]

    # ── L7 — Credenciales temporales (sin `contrasena`) ──────────────────────
    if "SELECT IDCREDENCIAL, IDUSUARIO, FECHA_ACTUALIZACION FROM DIM_CREDENCIAL" in sql_upper:
        filas = [
            f for f in PINOT_STORE["Dim_Credencial"]
            if f.get("estadocredencial") == params.get("estado")
        ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fecha_actualizacion", "idcredencial"]
        )
        return [
            {k: f.get(k) for k in ("idcredencial", "idusuario", "fecha_actualizacion")}
            for f in filas
        ]

    # ── L8 — Accesos técnicos (sin `contrasena` de servidor) ─────────────────
    if "SELECT IDUSUARIOSERVIDOR, IDUSUARIO, USUARIO FROM DIM_USUARIOSSERVIDOR" in sql_upper:
        filas = [f for f in PINOT_STORE["Dim_UsuariosServidor"] if f.get("activo")]
        filas = _informe_keyset(filas, sql_upper, params, ["idusuarioservidor"])
        return [
            {k: f.get(k) for k in ("idusuarioservidor", "idusuario", "usuario")}
            for f in filas
        ]

    if "SELECT IDUSUARIOSERVIDOR, IDROLSERVIDOR FROM DIM_USUARIOSSERVIDORROLESSERVIDOR" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idusuarioservidor": f["idusuarioservidor"], "idrolservidor": f["idrolservidor"]}
            for f in PINOT_STORE["Dim_UsuariosServidorRolesServidor"]
            if f["idusuarioservidor"] in permitidos and f.get("activo", True)
        ]

    if "SELECT IDROLSERVIDOR, ROLSERVIDOR FROM DIM_ROLESSERVIDOR" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idrolservidor": f["idrolservidor"], "rolservidor": f.get("rolservidor")}
            for f in PINOT_STORE["Dim_RolesServidor"]
            if f["idrolservidor"] in permitidos
        ]

    if "SELECT IDROLSERVIDOR, IDROL FROM DIM_ROLESSERVIDORROLES" in sql_upper:
        permitidos = set(params.get("ids") or [])
        return [
            {"idrolservidor": f["idrolservidor"], "idrol": f["idrol"]}
            for f in PINOT_STORE["Dim_RolesServidorRoles"]
            if f["idrolservidor"] in permitidos and f.get("activo", True)
        ]

    return None


def _informes_soporte(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tácticos de Soporte al Cliente.

    Antes que las ramas genéricas: `FROM FACT_HISTORIAL_TICKET` devolvería la
    fila entera, con `mensaje` y `es_nota_interna` incluidos — es decir,
    escondería en las pruebas la fuga de notas internas que research D4 prohíbe.
    """
    # ── L1 — Tickets (sin `descripcion`) ─────────────────────────────────────
    if "SELECT ID_RECLAMO, IDCLIENTE, ASUNTO, ESTADO, PRIORIDAD" in sql_upper:
        filas = list(PINOT_STORE["Fact_Reclamo"])
        if "IDCLIENTE = %(IDCLIENTE)S" in sql_upper:
            filas = [f for f in filas if f.get("idcliente") == params.get("idcliente")]
        if "ESTADO = %(ESTADO)S" in sql_upper:
            filas = [f for f in filas if f.get("estado") == params.get("estado")]
        if "SLA_STATUS = %(SLA_STATUS)S" in sql_upper:
            filas = [f for f in filas if f.get("sla_status") == params.get("sla_status")]
        if "PRIORIDAD = %(PRIORIDAD)S" in sql_upper:
            filas = [f for f in filas if f.get("prioridad") == params.get("prioridad")]
        if "TIPO_INCIDENCIA = %(TIPO_INCIDENCIA)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("tipo_incidencia") == params.get("tipo_incidencia")
            ]
        if "ID_AGENTE_ASIGNADO = %(AGENTE)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("id_agente_asignado") == params.get("agente")
            ]
        if "IDFACTURA NOT IN %(SIN_FACTURA)S" in sql_upper:
            centinelas = set(params.get("sin_factura") or [])
            filas = [f for f in filas if str(f.get("idfactura") or "") not in centinelas]
        elif "IDFACTURA IN %(SIN_FACTURA)S" in sql_upper:
            centinelas = set(params.get("sin_factura") or [])
            filas = [f for f in filas if str(f.get("idfactura") or "") in centinelas]
        filas = _informe_keyset(filas, sql_upper, params, ["fechahora", "id_reclamo"])
        from core.repositories.soporte.informes_tickets_repository import (
            COLUMNAS_TICKET,
        )

        return [{k: f.get(k) for k in COLUMNAS_TICKET} for f in filas]

    # ── L2 — Escalados (sin `mensaje` ni `es_nota_interna`) ──────────────────
    if "SELECT ID_HISTORIAL, ID_RECLAMO, TIPO_ACCION, IDUSUARIO" in sql_upper:
        filas = list(PINOT_STORE["Fact_Historial_Ticket"])
        if "TIPO_ACCION = %(TIPO_ACCION)S" in sql_upper:
            filas = [
                f for f in filas if f.get("tipo_accion") == params.get("tipo_accion")
            ]
        elif "TIPO_ACCION IN %(TIPOS)S" in sql_upper:
            admitidos = set(params.get("tipos") or [])
            filas = [f for f in filas if f.get("tipo_accion") in admitidos]
        if "ID_RECLAMO IN %(ID_RECLAMOS)S" in sql_upper:
            admitidos = set(params.get("id_reclamos") or [])
            filas = [f for f in filas if f.get("id_reclamo") in admitidos]
        if "FECHA_ACCION >= %(DESDE_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fecha_accion") or 0) >= params["desde_ms"]
            ]
        if "FECHA_ACCION <= %(HASTA_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fecha_accion") or 0) <= params["hasta_ms"]
            ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fecha_accion", "id_historial"]
        )
        # El texto se recorta aquí. Sin esto llegaría a la respuesta en las
        # pruebas y la fuga solo aparecería contra Pinot real.
        from core.repositories.soporte.informes_escalados_repository import (
            COLUMNAS_ESCALADO,
        )

        return [{k: f.get(k) for k in COLUMNAS_ESCALADO} for f in filas]

    if "SELECT ID_RECLAMO, IDCLIENTE FROM FACT_RECLAMO" in sql_upper:
        if "IDCLIENTE = %(IDCLIENTE)S" in sql_upper:
            return [
                {"id_reclamo": f["id_reclamo"], "idcliente": f.get("idcliente")}
                for f in PINOT_STORE["Fact_Reclamo"]
                if f.get("idcliente") == params.get("idcliente")
            ]
        permitidos = set(params.get("ids") or [])
        return [
            {"id_reclamo": f["id_reclamo"], "idcliente": f.get("idcliente")}
            for f in PINOT_STORE["Fact_Reclamo"]
            if f.get("id_reclamo") in permitidos
        ]

    return None


def _informes_emergencias(sql_upper: str, params: dict) -> list[dict] | None:
    """Consultas de los listados tacticos de Emergencias.

    Antes que las ramas genericas: `FROM FACT_ACCIDENTE` devolveria la fila
    entera, con `latitudinicio` y `longitudinicio` incluidos - es decir,
    esconderia en las pruebas la fuga de coordenadas que research D4 prohibe.
    """
    # -- L1 - Casos (sin coordenadas) -----------------------------------------
    if "SELECT IDACCIDENTE, IDSEVERIDAD, IDCALLE, IDTIPOREPORTADO" in sql_upper:
        filas = list(PINOT_STORE["Fact_Accidente"])
        if "IDCALLE IN %(IDCALLES)S" in sql_upper:
            admitidas = set(params.get("idcalles") or [])
            filas = [f for f in filas if f.get("idcalle") in admitidas]
        if "IDSEVERIDAD = %(IDSEVERIDAD)S" in sql_upper:
            filas = [
                f for f in filas if f.get("idseveridad") == params.get("idseveridad")
            ]
        if "IDTIPOREPORTADO = %(IDTIPOREPORTADO)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("idtiporeportado") == params.get("idtiporeportado")
            ]
        if "ACTIVO = TRUE" in sql_upper:
            filas = [f for f in filas if bool(f.get("activo"))]
        if "ACTIVO = FALSE" in sql_upper:
            filas = [f for f in filas if not bool(f.get("activo"))]
        centinelas = set(params.get("sin_valor") or [])
        if "HORAFIN NOT IN %(SIN_VALOR)S" in sql_upper:
            filas = [f for f in filas if str(f.get("horafin") or "") not in centinelas]
        elif "HORAFIN IN %(SIN_VALOR)S" in sql_upper:
            filas = [f for f in filas if str(f.get("horafin") or "") in centinelas]
        if "IDACCIDENTEORIGEN NOT IN %(SIN_VALOR)S" in sql_upper:
            filas = [
                f for f in filas
                if str(f.get("idaccidenteorigen") or "") not in centinelas
            ]
        elif "IDACCIDENTEORIGEN IN %(SIN_VALOR)S" in sql_upper:
            filas = [
                f for f in filas
                if str(f.get("idaccidenteorigen") or "") in centinelas
            ]
        if "FECHAHORAACCIDENTE >= %(DESDE_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoraaccidente") or 0) >= params["desde_ms"]
            ]
        if "FECHAHORAACCIDENTE <= %(HASTA_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoraaccidente") or 0) <= params["hasta_ms"]
            ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahoraaccidente", "idaccidente"]
        )
        # Las coordenadas se recortan aqui. Sin esto llegarian a la respuesta en
        # las pruebas y la fuga solo apareceria contra Pinot real.
        from core.repositories.accidentes.informes_casos_repository import (
            COLUMNAS_CASO,
        )

        return [{k: f.get(k) for k in COLUMNAS_CASO} for f in filas]

    # -- L2 - Despachos -------------------------------------------------------
    if "SELECT IDDESPACHO, IDACCIDENTE, IDUNIDADEMERGENCIA" in sql_upper:
        filas = list(PINOT_STORE["Fact_Despacho"])
        if "IDORIGENDESPACHO = %(IDORIGENDESPACHO)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("idorigendespacho") == params.get("idorigendespacho")
            ]
        if "IDUNIDADEMERGENCIA = %(IDUNIDADEMERGENCIA)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("idunidademergencia") == params.get("idunidademergencia")
            ]
        if "IDACCIDENTE = %(IDACCIDENTE)S" in sql_upper:
            filas = [
                f for f in filas if f.get("idaccidente") == params.get("idaccidente")
            ]
        sin_hora = params.get("sin_hora", 0)
        if "FECHAHORALLEGADA = %(SIN_HORA)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoradespacho") or 0) > sin_hora
                and (f.get("fechahorallegada") or 0) == sin_hora
                and (f.get("fechahoraretiro") or 0) == sin_hora
            ]
        elif "FECHAHORALLEGADA > %(SIN_HORA)S OR FECHAHORARETIRO > %(SIN_HORA)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahorallegada") or 0) > sin_hora
                or (f.get("fechahoraretiro") or 0) > sin_hora
            ]
        if "FECHAHORADESPACHO >= %(DESDE_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoradespacho") or 0) >= params["desde_ms"]
            ]
        if "FECHAHORADESPACHO <= %(HASTA_MS)S" in sql_upper:
            filas = [
                f for f in filas
                if (f.get("fechahoradespacho") or 0) <= params["hasta_ms"]
            ]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahoradespacho", "iddespacho"]
        )
        from core.repositories.seguimiento.informes_despachos_repository import (
            COLUMNAS_DESPACHO,
        )

        return [{k: f.get(k) for k in COLUMNAS_DESPACHO} for f in filas]

    # -- L3 / L4 - Evidencia --------------------------------------------------
    if "SELECT IDEVIDENCIAFOTO, IDACCIDENTE, IDUSUARIO" in sql_upper:
        filas = _filtrar_evidencia(PINOT_STORE["Dim_EvidenciaFoto"], sql_upper, params)
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahora", "idevidenciafoto"]
        )
        from core.repositories.accidentes.informes_evidencia_repository import (
            COLUMNAS_FOTO,
        )

        return [{k: f.get(k) for k in COLUMNAS_FOTO} for f in filas]

    if "SELECT IDNOTAACCIDENTES, IDACCIDENTE, IDUSUARIO" in sql_upper:
        filas = _filtrar_evidencia(PINOT_STORE["Dim_NotaAccidente"], sql_upper, params)
        if "TIPO = %(TIPO)S" in sql_upper:
            filas = [f for f in filas if f.get("tipo") == params.get("tipo")]
        filas = _informe_keyset(
            filas, sql_upper, params, ["fechahora", "idnotaaccidentes"]
        )
        from core.repositories.accidentes.informes_evidencia_repository import (
            COLUMNAS_NOTA,
        )

        return [{k: f.get(k) for k in COLUMNAS_NOTA} for f in filas]

    # -- L5 - Cierres ---------------------------------------------------------
    if "SELECT IDACCIDENTE, RESULTADO_ATENCION, OBSERVACIONES_FINALES" in sql_upper:
        filas = list(PINOT_STORE["Fact_CierreAccidente"])
        if "RESULTADO_ATENCION = %(RESULTADO)S" in sql_upper:
            filas = [
                f for f in filas
                if f.get("resultado_atencion") == params.get("resultado")
            ]
        centinelas = set(params.get("sin_texto") or [])
        if "OBSERVACIONES_FINALES NOT IN %(SIN_TEXTO)S" in sql_upper:
            filas = [
                f for f in filas
                if str(f.get("observaciones_finales") or "") not in centinelas
            ]
        elif "OBSERVACIONES_FINALES IN %(SIN_TEXTO)S" in sql_upper:
            filas = [
                f for f in filas
                if str(f.get("observaciones_finales") or "") in centinelas
            ]
        if "CALIFICACION > 0" in sql_upper:
            filas = [f for f in filas if (f.get("calificacion") or 0) > 0]
        elif "CALIFICACION <= 0" in sql_upper:
            filas = [f for f in filas if (f.get("calificacion") or 0) <= 0]
        filas = _informe_keyset(filas, sql_upper, params, ["idaccidente"])
        from core.repositories.accidentes.informes_cierres_repository import (
            COLUMNAS_CIERRE,
        )

        return [{k: f.get(k) for k in COLUMNAS_CIERRE} for f in filas]

    # -- Catalogos geograficos por lote ---------------------------------------
    #
    # ⚠️ Cada rama exige TAMBIEN su clausula WHERE. Los informes agregados
    # consultan `Dim_Calle` y `Dim_Ciudad` con **la misma lista de columnas** y
    # distinto filtro: dispatchar solo por las columnas capturaba sus consultas
    # y les devolvia filas filtradas por la columna equivocada — es decir, un
    # fallo silencioso en 19 informes que ya estaban construidos.
    if "SELECT IDCIUDAD, IDCONDADO FROM DIM_CIUDAD WHERE IDCONDADO IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {"idciudad": f["idciudad"], "idcondado": f.get("idcondado")}
            for f in PINOT_STORE["Dim_Ciudad"]
            if f.get("idcondado") in admitidos and f.get("activo", True)
        ]

    if "SELECT IDCALLE, IDCIUDAD FROM DIM_CALLE WHERE IDCIUDAD IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {"idcalle": f["idcalle"], "idciudad": f.get("idciudad")}
            for f in PINOT_STORE["Dim_Calle"]
            if f.get("idciudad") in admitidos and f.get("activo", True)
        ]

    if "SELECT IDCALLE, CALLE, IDCIUDAD FROM DIM_CALLE WHERE IDCALLE IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idcalle", "calle", "idciudad")}
            for f in PINOT_STORE["Dim_Calle"]
            if f.get("idcalle") in admitidos
        ]

    if "SELECT IDCIUDAD, CIUDAD, IDCONDADO FROM DIM_CIUDAD WHERE IDCIUDAD IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idciudad", "ciudad", "idcondado")}
            for f in PINOT_STORE["Dim_Ciudad"]
            if f.get("idciudad") in admitidos
        ]

    if "SELECT IDCONDADO, CONDADO, IDESTADO FROM DIM_CONDADO" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idcondado", "condado", "idestado")}
            for f in PINOT_STORE["Dim_Condado"]
            if f.get("idcondado") in admitidos
        ]

    if "SELECT IDSEVERIDAD, SEVERIDAD FROM DIM_SEVERIDAD WHERE IDSEVERIDAD IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {"idseveridad": f["idseveridad"], "severidad": f.get("severidad")}
            for f in PINOT_STORE["Dim_Severidad"]
            if f.get("idseveridad") in admitidos
        ]

    if "SELECT IDTIPOREPORTADO, TIPOREPORTADO FROM DIM_TIPOREPORTADO WHERE IDTIPOREPORTADO IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idtiporeportado", "tiporeportado")}
            for f in PINOT_STORE["Dim_TipoReportado"]
            if f.get("idtiporeportado") in admitidos
        ]

    if "SELECT IDUNIDADEMERGENCIA, UNIDADEMERGENCIA FROM DIM_UNIDADEMERGENCIA WHERE IDUNIDADEMERGENCIA IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idunidademergencia", "unidademergencia")}
            for f in PINOT_STORE["Dim_UnidadEmergencia"]
            if f.get("idunidademergencia") in admitidos
        ]

    if "SELECT IDORIGENDESPACHO, ORIGENDESPACHO FROM DIM_ORIGENDESPACHO WHERE IDORIGENDESPACHO IN" in sql_upper:
        admitidos = set(params.get("ids") or [])
        return [
            {k: f.get(k) for k in ("idorigendespacho", "origendespacho")}
            for f in PINOT_STORE["Dim_OrigenDespacho"]
            if f.get("idorigendespacho") in admitidos
        ]

    if "SELECT ID_CLIENTE, ZONAS_GEOGRAFICAS FROM DIM_PREFERENCIAS_CLIENTE" in sql_upper:
        return [
            {"id_cliente": f["id_cliente"],
             "zonas_geograficas": f.get("zonas_geograficas")}
            for f in PINOT_STORE["Dim_Preferencias_Cliente"]
            if f.get("id_cliente") == params.get("id_cliente")
        ]

    return None


def _filtrar_evidencia(tabla, sql_upper: str, params: dict) -> list[dict]:
    filas = list(tabla)
    if "SINCRONIZADO = %(SINCRONIZADO)S" in sql_upper:
        filas = [
            f for f in filas
            if bool(f.get("sincronizado")) is params.get("sincronizado")
        ]
    if "IDACCIDENTE = %(IDACCIDENTE)S" in sql_upper:
        filas = [f for f in filas if f.get("idaccidente") == params.get("idaccidente")]
    if "IDUSUARIO = %(IDUSUARIO)S" in sql_upper:
        filas = [f for f in filas if f.get("idusuario") == params.get("idusuario")]
    if "FECHAHORA >= %(DESDE_MS)S" in sql_upper:
        filas = [f for f in filas if (f.get("fechahora") or 0) >= params["desde_ms"]]
    if "FECHAHORA <= %(HASTA_MS)S" in sql_upper:
        filas = [f for f in filas if (f.get("fechahora") or 0) <= params["hasta_ms"]]
    return filas


def _pinot_query_impl(sql: str, params: dict | None = None) -> list[dict]:
    """Route SQL queries to in-memory store."""
    params = params or {}
    sql_upper = sql.upper().replace("\n", " ").strip()

    # --- Listados tácticos: deben preceder a las ramas genéricas por tabla ---
    for _resolver_informe in (
        _informes_cuentas_clientes,
        _informes_ventas_crm,
        _informes_suscripciones,
        _informes_red_operativa,
        _informes_partners,
        _informes_soporte,
        _informes_emergencias,
    ):
        informe = _resolver_informe(sql_upper, params)
        if informe is not None:
            return informe

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
    # --- Partners y API (CU-O48 a CU-O55) ---
    if "MAX(IDPARTNER)" in sql_upper:
        rows = PINOT_STORE["Dim_Partner"]
        return [{"max_id": max((r["idpartner"] for r in rows), default=0)}]
    if "MAX(IDCREDENCIAL)" in sql_upper:
        rows = PINOT_STORE["Dim_CredencialAPI"]
        return [{"max_id": max((r["idcredencial"] for r in rows), default=0)}]
    if "MAX(IDHISTORIAL)" in sql_upper:
        rows = PINOT_STORE["Fact_HistorialAccesoPartner"]
        return [{"max_id": max((r["idhistorial"] for r in rows), default=0)}]
    if "MAX(IDVERSION)" in sql_upper:
        rows = PINOT_STORE["Dim_VersionContratoAPI"]
        return [{"max_id": max((r["idversion"] for r in rows), default=0)}]

    # --- Monitoreo y facturacion de API (#08) ---
    #
    # OJO: este modulo vive de agregaciones y el doble las reproduce a mano.
    # Es exactamente el hueco que documenta `decisiones-pendientes.md` #18:
    # que estas consultas pasen aqui NO garantiza que Pinot las resuelva igual.
    # La verificacion contra Pinot real (T066) sigue siendo criterio de salida.
    if "MAX(IDAPIINTEGRACION)" in sql_upper:
        rows = PINOT_STORE["Fact_APIIntegracion"]
        return [{"max_id": max((r["idapiintegracion"] for r in rows), default=0)}]
    if "MAX(IDLOGLLAMADAAPI)" in sql_upper:
        rows = PINOT_STORE["Fact_LogLlamadaAPI"]
        return [{"max_id": max((r["idlogllamadaapi"] for r in rows), default=0)}]

    if "FROM DIM_ESTADOINTEGRACION" in sql_upper:
        rows = list(PINOT_STORE["Dim_EstadoIntegracion"])
        if "IDESTADOINTEGRACION = %(ID)S" in sql_upper:
            rows = [r for r in rows if r["idestadointegracion"] == params.get("id")]
        return rows[: params.get("limit", len(rows))]

    if "FROM FACT_APIINTEGRACION" in sql_upper:
        rows = list(PINOT_STORE["Fact_APIIntegracion"])
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            rows = [r for r in rows if r["idpartner"] == params.get("idpartner")]
        if "ENTORNO = %(ENTORNO)S" in sql_upper:
            rows = [r for r in rows if r.get("entorno") == params.get("entorno")]
        if "FECHAHORA >= %(DESDE)S" in sql_upper:
            rows = [r for r in rows if r.get("fechahora", 0) >= params.get("desde", 0)]
        if "FECHAHORA < %(HASTA)S" in sql_upper:
            rows = [r for r in rows if r.get("fechahora", 0) < params.get("hasta", 0)]

        if "GROUP BY IDSERVICIO" in sql_upper:
            por_servicio: dict = {}
            for r in rows:
                acc = por_servicio.setdefault(
                    r["idservicio"], {"idservicio": r["idservicio"], "llamadas": 0, "errores": 0}
                )
                acc["llamadas"] += r.get("llamadas", 0)
                acc["errores"] += r.get("errores", 0)
            agrupado = sorted(
                por_servicio.values(), key=lambda a: a["llamadas"], reverse=True
            )
            return agrupado[: params.get("limit", len(agrupado))]

        if "SUM(LLAMADAS)" in sql_upper:
            latencias = [r.get("latencia", 0.0) for r in rows]
            return [{
                "llamadas": sum(r.get("llamadas", 0) for r in rows),
                "errores": sum(r.get("errores", 0) for r in rows),
                "latencia_media": (sum(latencias) / len(latencias)) if latencias else 0.0,
            }]
        return rows[: params.get("limit", len(rows))]

    if "FROM FACT_LOGLLAMADAAPI" in sql_upper:
        rows = list(PINOT_STORE["Fact_LogLlamadaAPI"])
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            rows = [r for r in rows if r["idpartner"] == params.get("idpartner")]
        if "CODIGOHTTP >= 400" in sql_upper:
            rows = [r for r in rows if r.get("codigohttp", 0) >= 400]
        # --- Filtros y paginacion de la consola (#08 FE) ---
        # Todos se resuelven aqui, contra la "base": la UI no filtra en memoria.
        if "CODIGOHTTP = %(CODIGOHTTP)S" in sql_upper:
            rows = [r for r in rows if r.get("codigohttp") == params.get("codigohttp")]
        if "FECHALLAMADA >= %(DESDE)S" in sql_upper:
            rows = [r for r in rows if r.get("fechallamada", 0) >= params.get("desde", 0)]
        if "FECHALLAMADA < %(HASTA)S" in sql_upper:
            rows = [r for r in rows if r.get("fechallamada", 0) < params.get("hasta", 0)]
        if "IDCREDENCIALAPI = %(IDCREDENCIALAPI)S" in sql_upper:
            rows = [
                r for r in rows
                if r.get("idcredencialapi") == params.get("idcredencialapi")
            ]
        if "ENDPOINT = %(ENDPOINT)S" in sql_upper:
            rows = [r for r in rows if r.get("endpoint") == params.get("endpoint")]
        if "IDLOGLLAMADAAPI < %(CURSOR)S" in sql_upper:
            # Cursor COMPUESTO: replica el ORDER BY (fecha DESC, id DESC).
            cf = params.get("cursor_fecha", 0)
            cid = params.get("cursor", 0)
            rows = [
                r for r in rows
                if r.get("fechallamada", 0) < cf
                or (r.get("fechallamada", 0) == cf and r.get("idlogllamadaapi", 0) < cid)
            ]

        if "GROUP BY CODIGOHTTP" in sql_upper:
            por_codigo: dict = {}
            for r in rows:
                por_codigo[r["codigohttp"]] = por_codigo.get(r["codigohttp"], 0) + 1
            agrupado = sorted(
                ({"codigohttp": c, "total": t} for c, t in por_codigo.items()),
                key=lambda a: a["total"],
                reverse=True,
            )
            return agrupado[: params.get("limit", len(agrupado))]

        rows.sort(
            key=lambda r: (r.get("fechallamada", 0), r.get("idlogllamadaapi", 0)),
            reverse="DESC" in sql_upper,
        )
        return rows[: params.get("limit", len(rows))]

    if "FROM DIM_PARTNER" in sql_upper:
        rows = list(PINOT_STORE["Dim_Partner"])
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            rows = [r for r in rows if r["idpartner"] == params.get("idpartner")]
        if "IDCLIENTE = %(IDCLIENTE)S" in sql_upper:
            rows = [r for r in rows if r["idcliente"] == params.get("idcliente")]
        if "IDPARTNER < %(CURSOR)S" in sql_upper:
            rows = [r for r in rows if r["idpartner"] < params.get("cursor")]
        rows.sort(key=lambda r: r["idpartner"], reverse="DESC" in sql_upper)
        return rows[: params.get("limit", len(rows))]

    if "FROM DIM_CREDENCIALAPI" in sql_upper:
        rows = list(PINOT_STORE["Dim_CredencialAPI"])
        if "IDCREDENCIAL = %(ID)S" in sql_upper:
            rows = [r for r in rows if r["idcredencial"] == params.get("id")]
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            rows = [r for r in rows if r["idpartner"] == params.get("idpartner")]
        if "ENTORNO = %(ENTORNO)S" in sql_upper:
            rows = [r for r in rows if r.get("entorno") == params.get("entorno")]
        if "ACTIVO = TRUE" in sql_upper:
            rows = [r for r in rows if r.get("activo")]
        if "FECHA_EXPIRACION < %(AHORA)S" in sql_upper:
            rows = [r for r in rows if r.get("fecha_expiracion", 0) < params.get("ahora", 0)]
        rows.sort(key=lambda r: r["idcredencial"], reverse="DESC" in sql_upper)
        return rows[: params.get("limit", len(rows))]

    if "FROM FACT_HISTORIALACCESOPARTNER" in sql_upper:
        rows = list(PINOT_STORE["Fact_HistorialAccesoPartner"])
        if "IDPARTNER = %(IDPARTNER)S" in sql_upper:
            rows = [r for r in rows if r["idpartner"] == params.get("idpartner")]
        rows.sort(
            key=lambda r: (r.get("fecha_cambio", 0), r.get("idhistorial", 0)),
            reverse="DESC" in sql_upper,
        )
        return rows[: params.get("limit", len(rows))]

    if "FROM DIM_VERSIONCONTRATOAPI" in sql_upper:
        rows = list(PINOT_STORE["Dim_VersionContratoAPI"])
        if "ID_SERVICIO = %(ID_SERVICIO)S" in sql_upper:
            rows = [r for r in rows if r["id_servicio"] == params.get("id_servicio")]
        if "ACTIVO = TRUE" in sql_upper:
            rows = [r for r in rows if r.get("activo")]
        rows.sort(key=lambda r: r.get("fecha_publicacion", 0), reverse="DESC" in sql_upper)
        return rows[: params.get("limit", len(rows))]

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
        if "ID_CLIENTE =" in sql_upper:
            rows = [r for r in rows if r.get("id_cliente") == params.get("idcliente")]
        if "ID_SUSCRIPCION =" in sql_upper:
            rows = [r for r in rows if r.get("id_suscripcion") == params.get("id_suscripcion")]
        if "PERIODO =" in sql_upper:
            rows = [r for r in rows if r.get("periodo") == params.get("periodo")]
        # --- Facturacion de excedente de API (#08) ---
        # `tipo` es lo que distingue la factura de excedente de la de
        # suscripcion del mismo periodo: sin este filtro, la comprobacion de no
        # duplicacion daria un falso positivo y no se cobraria el excedente.
        if "TIPO = %(TIPO)S" in sql_upper:
            rows = [r for r in rows if r.get("tipo") == params.get("tipo")]
        if "PROXIMO_REINTENTO > 0" in sql_upper:
            rows = [r for r in rows if (r.get("proximo_reintento") or 0) > 0]
        if "PROXIMO_REINTENTO <= %(AHORA)S" in sql_upper:
            rows = [
                r for r in rows
                if (r.get("proximo_reintento") or 0) <= params.get("ahora", 0)
            ]
        # --- Mora de excedente de API (#09, § 15 D3) ---
        # `estado_pago` es lo que separa la mora de este modulo de la de
        # Suscripciones: aqui SOLO cuenta 'Pendiente'. Si este filtro se
        # ignorase, una factura 'Fallida' suspenderia al partner y tendriamos
        # dos modulos suspendiendo por la misma factura.
        if "ESTADO_PAGO = %(ESTADO)S" in sql_upper:
            rows = [r for r in rows if r.get("estado_pago") == params.get("estado")]
        if "FECHA_VENCIMIENTO < %(AHORA)S" in sql_upper:
            rows = [
                r for r in rows
                if int(r.get("fecha_vencimiento") or 0) < params.get("ahora", 0)
            ]
        if "ORDER BY FECHA_VENCIMIENTO ASC" in sql_upper:
            rows = sorted(rows, key=lambda r: r.get("fecha_vencimiento") or 0)
        if "ORDER BY FECHA_EMISION DESC" in sql_upper:
            rows = sorted(rows, key=lambda r: r.get("fecha_emision") or 0, reverse=True)
        if "LIMIT" in sql_upper and params.get("limit") is not None:
            rows = rows[: int(params["limit"])]
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
    # Nota: aquí vivía una rama que resolvía un `JOIN Dim_Usuario_Rol` de la
    # asignación automática de prospectos. Pinot no admite JOIN entre tablas y
    # ese doble hacía pasar la suite mientras el endpoint fallaba con 500 contra
    # Pinot real. El servicio ahora consulta en dos pasos y esas consultas se
    # resuelven en las ramas genéricas de Dim_Rol / Dim_Usuario_Rol / Dim_Usuarios.
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
    if "MAX(IDHISTORIALSEVERIDADACCIDENTE)" in sql_upper:
        ids = [
            r["idhistorialseveridadaccidente"]
            for r in PINOT_STORE["Fact_HistorialSeveridadAccidente"]
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
    if "MAX(IDHISTORIALUNIDADEMERGENCIA)" in sql_upper:
        ids = [
            r["idhistorialunidademergencia"]
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

    # --- informes_tacticos: agregaciones GROUP BY adicionales de Despacho ---
    # Deben interceptar ANTES de los bloques genéricos de Fact_Despacho/
    # Fact_HistorialDespachoUnidad/Fact_AccidenteTipoEstadoAccidente/Dim_Calle/
    # Dim_Ciudad más abajo, que no filtran por fecha ni entienden estos shapes.
    if "IDORIGENDESPACHO, IDUNIDADEMERGENCIA" in sql_upper and "FROM FACT_DESPACHO" in sql_upper:
        desde = params.get("desde")
        hasta = params.get("hasta")
        return [
            {"idorigendespacho": d["idorigendespacho"], "idunidademergencia": d.get("idunidademergencia")}
            for d in PINOT_STORE["Fact_Despacho"]
            if desde <= (d.get("fechahoradespacho") or 0) <= hasta
        ]

    if "FECHAHORALLEGADA IS NOT NULL" in sql_upper:
        desde = params.get("desde")
        hasta = params.get("hasta")
        return [
            {
                "idaccidente": d["idaccidente"],
                "idunidademergencia": d.get("idunidademergencia"),
                "fechahoradespacho": d.get("fechahoradespacho"),
                "fechahorallegada": d.get("fechahorallegada"),
            }
            for d in PINOT_STORE["Fact_Despacho"]
            if desde <= (d.get("fechahoradespacho") or 0) <= hasta and d.get("fechahorallegada") is not None
        ]

    if "GROUP BY IDUNIDADEMERGENCIA" in sql_upper and "FROM FACT_DESPACHO" in sql_upper:
        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            d for d in PINOT_STORE["Fact_Despacho"]
            if desde <= (d.get("fechahoradespacho") or 0) <= hasta
        ]
        buckets: dict[int, int] = {}
        for d in rows:
            buckets[d.get("idunidademergencia")] = buckets.get(d.get("idunidademergencia"), 0) + 1
        return [
            {"idunidademergencia": k, "total_despachos": v} for k, v in sorted(buckets.items())
        ]

    if "WHERE IDDESPACHO IN" in sql_upper and "FROM FACT_DESPACHO" in sql_upper:
        ids = params.get("ids") or []
        return [
            {"iddespacho": d["iddespacho"], "idunidademergencia": d.get("idunidademergencia")}
            for d in PINOT_STORE["Fact_Despacho"]
            if d["iddespacho"] in ids
        ]

    if "WHERE IDACCIDENTE IN" in sql_upper and "FROM FACT_DESPACHO" in sql_upper:
        ids = params.get("ids") or []
        return [
            {"idaccidente": d["idaccidente"], "idunidademergencia": d.get("idunidademergencia")}
            for d in PINOT_STORE["Fact_Despacho"]
            if d.get("idaccidente") in ids
        ]

    if "AS PERIODO, ESTADONUEVO" in sql_upper:
        from datetime import datetime, timezone

        desde = params.get("desde")
        hasta = params.get("hasta")
        estados_validos = {"RETIRADO", "CERRADO"}
        if "DATETRUNC('WEEK'" in sql_upper:
            unit = "week"
        elif "DATETRUNC('MONTH'" in sql_upper:
            unit = "month"
        else:
            unit = "day"
        rows = []
        for h in PINOT_STORE["Fact_HistorialDespachoUnidad"]:
            if not (desde <= (h.get("fechahora") or 0) <= hasta):
                continue
            if (h.get("estadonuevo") or "").upper() not in estados_validos:
                continue
            dt = datetime.fromtimestamp(h["fechahora"] / 1000, tz=timezone.utc)
            if unit == "day":
                key = dt.strftime("%Y-%m-%d")
            elif unit == "week":
                key = dt.strftime("%G-W%V")
            else:
                key = dt.strftime("%Y-%m")
            rows.append(
                {
                    "periodo": _day_key_to_epoch_ms(key),
                    "estadonuevo": h.get("estadonuevo"),
                    "idusuario": h.get("idusuario"),
                }
            )
        return rows

    if "SELECT IDDESPACHO, ESTADONUEVO" in sql_upper:
        desde = params.get("desde")
        hasta = params.get("hasta")
        return [
            {"iddespacho": h["iddespacho"], "estadonuevo": h.get("estadonuevo")}
            for h in PINOT_STORE["Fact_HistorialDespachoUnidad"]
            if desde <= (h.get("fechahora") or 0) <= hasta
        ]

    if (
        "FROM FACT_ACCIDENTETIPOESTADOACCIDENTE" in sql_upper
        and "IDTIPOESTADOINCIDENTE IN" in sql_upper
        and "GROUP BY" not in sql_upper
    ):
        desde = params.get("desde")
        hasta = params.get("hasta")
        estados_validos = {
            v
            for k, v in params.items()
            if k in ("reportado", "asignado", "cerrado") and v is not None
        }
        return [
            {
                "idaccidente": r["idaccidente"],
                "idtipoestadoincidente": r["idtipoestadoincidente"],
                "fechahoramodificado": r.get("fechahoramodificado"),
            }
            for r in PINOT_STORE["Fact_AccidenteTipoEstadoAccidente"]
            if desde <= (r.get("fechahoramodificado") or 0) <= hasta
            and r.get("idtipoestadoincidente") in estados_validos
        ]

    if "WHERE IDACCIDENTE IN" in sql_upper and "FROM FACT_ACCIDENTE" in sql_upper:
        ids = params.get("ids") or []
        return [
            {"idaccidente": a["idaccidente"], "idseveridad": a.get("idseveridad")}
            for a in PINOT_STORE["Fact_Accidente"]
            if a["idaccidente"] in ids
        ]

    if "SELECT IDCALLE, CALLE" in sql_upper and "FROM DIM_CALLE" in sql_upper:
        ids = params.get("ids") or []
        return [
            {"idcalle": c["idcalle"], "calle": c.get("calle")}
            for c in PINOT_STORE["Dim_Calle"]
            if c["idcalle"] in ids
        ]

    if "WHERE IDCALLE IN" in sql_upper and "FROM DIM_CALLE" in sql_upper:
        ids = params.get("ids") or []
        return [
            {"idcalle": c["idcalle"], "idciudad": c.get("idciudad")}
            for c in PINOT_STORE["Dim_Calle"]
            if c["idcalle"] in ids
        ]

    if "WHERE IDCIUDAD IN" in sql_upper and "FROM DIM_CIUDAD" in sql_upper:
        ids = params.get("ids") or []
        return [
            {"idciudad": c["idciudad"], "idcondado": c.get("idcondado")}
            for c in PINOT_STORE["Dim_Ciudad"]
            if c["idciudad"] in ids
        ]

    # --- Dim_Cliente ---
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE IDCLIENTE IN" in sql_upper:
        ids = params.get("ids") or []
        return [c for c in PINOT_STORE["Dim_Cliente"] if c.get("idcliente") in ids]
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
    if "FROM DIM_USUARIO_ROL" in sql_upper and "MAX(IDUSUARIOROL)" in sql_upper:
        # `Dim_Usuario_Rol` es upsert por `idusuariorol`: sin esta clave las
        # asignaciones se pisaban entre sí (ver RoleRepository.assign_role_to_user).
        ids = [
            int(ur.get("idusuariorol") or 0)
            for ur in PINOT_STORE["Dim_Usuario_Rol"]
        ]
        return [{"max_id": max(ids) if ids else 0}]

    if (
        "FROM DIM_USUARIO_ROL" in sql_upper
        and "WHERE IDUSUARIO" in sql_upper
        and "IDROL =" in sql_upper
    ):
        uid = params.get("idusuario")
        rid = params.get("idrol")
        return [
            dict(ur)
            for ur in PINOT_STORE["Dim_Usuario_Rol"]
            if ur.get("idusuario") == uid and ur.get("idrol") == rid
        ]

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

    if "FROM DIM_SEVERIDAD" in sql_upper:
        filas = [s for s in PINOT_STORE["Dim_Severidad"] if s.get("activo")]
        return sorted(filas, key=lambda s: s["idseveridad"])

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

    if "FROM DIM_USUARIOS" in sql_upper and "IDUSUARIO IN" in sql_upper:
        ids = set(params.get("ids") or [])
        rows = [u for u in PINOT_STORE["Dim_Usuarios"] if u["idusuario"] in ids]
        if "ACTIVO = TRUE" in sql_upper:
            rows = [u for u in rows if u.get("activo")]
        return [{"idusuario": u["idusuario"]} for u in rows]

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

    # --- informes_tacticos: agregaciones GROUP BY adicionales de Registro ---
    # Deben interceptar ANTES de los bloques genéricos de Accidentes de abajo.
    if (
        "FROM FACT_ACCIDENTETIPOESTADOACCIDENTE" in sql_upper
        and "GROUP BY PERIODO, IDTIPOESTADOINCIDENTE" in sql_upper
    ):
        from datetime import datetime, timezone

        desde = params.get("desde")
        hasta = params.get("hasta")
        estados_validos = {params.get("descartado"), params.get("fusionado")}
        rows = [
            r
            for r in PINOT_STORE["Fact_AccidenteTipoEstadoAccidente"]
            if desde <= (r.get("fechahoramodificado") or 0) <= hasta
            and r.get("idtipoestadoincidente") in estados_validos
        ]
        if "DATETRUNC('WEEK'" in sql_upper:
            unit = "week"
        elif "DATETRUNC('MONTH'" in sql_upper:
            unit = "month"
        else:
            unit = "day"
        buckets: dict[tuple[str, int], int] = {}
        for r in rows:
            dt = datetime.fromtimestamp(r["fechahoramodificado"] / 1000, tz=timezone.utc)
            if unit == "day":
                key = dt.strftime("%Y-%m-%d")
            elif unit == "week":
                key = dt.strftime("%G-W%V")
            else:
                key = dt.strftime("%Y-%m")
            bucket_key = (key, r["idtipoestadoincidente"])
            buckets[bucket_key] = buckets.get(bucket_key, 0) + 1
        return [
            {"periodo": _day_key_to_epoch_ms(k[0]), "idtipoestadoincidente": k[1], "total": v}
            for k, v in sorted(buckets.items())
        ]

    if "FROM FACT_ACCIDENTE" in sql_upper and "TOTAL_COMPLETOS" in sql_upper:
        from datetime import datetime, timezone

        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            r
            for r in PINOT_STORE["Fact_Accidente"]
            if desde <= (r.get("fechahoraaccidente") or 0) <= hasta
        ]
        if "DATETRUNC('WEEK'" in sql_upper:
            unit = "week"
        elif "DATETRUNC('MONTH'" in sql_upper:
            unit = "month"
        else:
            unit = "day"
        totales: dict[str, int] = {}
        completos: dict[str, int] = {}
        for r in rows:
            dt = datetime.fromtimestamp(r["fechahoraaccidente"] / 1000, tz=timezone.utc)
            if unit == "day":
                key = dt.strftime("%Y-%m-%d")
            elif unit == "week":
                key = dt.strftime("%G-W%V")
            else:
                key = dt.strftime("%Y-%m")
            totales[key] = totales.get(key, 0) + 1
            if r.get("idseveridad") is not None and r.get("idcalle") is not None:
                completos[key] = completos.get(key, 0) + 1
        return [
            {"periodo": _day_key_to_epoch_ms(k), "total_casos": v, "total_completos": completos.get(k, 0)}
            for k, v in sorted(totales.items())
        ]

    if "FROM FACT_ACCIDENTE" in sql_upper and "GROUP BY IDSEVERIDAD" in sql_upper:
        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            r
            for r in PINOT_STORE["Fact_Accidente"]
            if desde <= (r.get("fechahoraaccidente") or 0) <= hasta
        ]
        buckets: dict[int, int] = {}
        for r in rows:
            buckets[r.get("idseveridad")] = buckets.get(r.get("idseveridad"), 0) + 1
        return [
            {"idseveridad": k, "total_casos": v} for k, v in sorted(buckets.items())
        ]

    if "FROM FACT_ACCIDENTE" in sql_upper and "SUM(NUMVICTIMAS)" in sql_upper:
        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            r
            for r in PINOT_STORE["Fact_Accidente"]
            if desde <= (r.get("fechahoraaccidente") or 0) <= hasta
        ]
        buckets: dict[int, dict[str, int]] = {}
        for r in rows:
            b = buckets.setdefault(
                r.get("idcalle"), {"total_victimas": 0, "total_heridos": 0, "total_fallecidos": 0}
            )
            b["total_victimas"] += r.get("numvictimas") or 0
            b["total_heridos"] += r.get("numheridos") or 0
            b["total_fallecidos"] += r.get("numfallecidos") or 0
        return [{"idcalle": k, **v} for k, v in sorted(buckets.items())]

    if (
        "FROM FACT_ACCIDENTE" in sql_upper
        and "GROUP BY IDCALLE" in sql_upper
        and "ORDER BY TOTAL_CASOS DESC" in sql_upper
    ):
        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            r
            for r in PINOT_STORE["Fact_Accidente"]
            if desde <= (r.get("fechahoraaccidente") or 0) <= hasta
        ]
        buckets: dict[int, int] = {}
        for r in rows:
            buckets[r.get("idcalle")] = buckets.get(r.get("idcalle"), 0) + 1
        ranked = sorted(buckets.items(), key=lambda kv: (-kv[1], kv[0]))
        result = [{"idcalle": k, "total_casos": v} for k, v in ranked]
        tokens = sql_upper.rstrip(";").rstrip().split()
        if tokens and tokens[-2] == "LIMIT":
            result = result[: int(tokens[-1])]
        return result

    if (
        "FROM FACT_ACCIDENTE" in sql_upper
        and "GROUP BY IDCALLE" in sql_upper
        and "ORDER BY IDCALLE" in sql_upper
    ):
        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            r
            for r in PINOT_STORE["Fact_Accidente"]
            if desde <= (r.get("fechahoraaccidente") or 0) <= hasta
        ]
        buckets: dict[int, int] = {}
        for r in rows:
            buckets[r.get("idcalle")] = buckets.get(r.get("idcalle"), 0) + 1
        return [{"idcalle": k, "total_casos": v} for k, v in sorted(buckets.items())]

    # --- Accidentes domain (TipoEstado before Accidente — substring collision) ---
    if "FROM FACT_ACCIDENTETIPOESTADOACCIDENTE" in sql_upper:
        aid = params.get("idaccidente")
        rows = [r for r in PINOT_STORE["Fact_AccidenteTipoEstadoAccidente"] if r["idaccidente"] == aid]
        if "ORDER BY FECHAHORAMODIFICADO DESC" in sql_upper:
            return sorted(rows, key=lambda r: r.get("fechahoramodificado", 0), reverse=True)[:1]
        return sorted(rows, key=lambda r: r.get("fechahoramodificado", 0))

    # --- informes_tacticos: agregaciones GROUP BY sobre Fact_Accidente ---
    # Deben interceptar ANTES del bloque genérico "FROM FACT_ACCIDENTE" de abajo,
    # que devuelve filas crudas (sin agregar) y no entiende GROUP BY/DATETRUNC.
    if "FROM FACT_ACCIDENTE" in sql_upper and "GROUP BY PERIODO" in sql_upper:
        from datetime import datetime, timezone

        desde = params.get("desde")
        hasta = params.get("hasta")
        rows = [
            r
            for r in PINOT_STORE["Fact_Accidente"]
            if desde <= (r.get("fechahoraaccidente") or 0) <= hasta
        ]
        if "DATETRUNC('WEEK'" in sql_upper:
            unit = "week"
        elif "DATETRUNC('MONTH'" in sql_upper:
            unit = "month"
        else:
            unit = "day"
        buckets: dict[str, int] = {}
        for r in rows:
            dt = datetime.fromtimestamp(r["fechahoraaccidente"] / 1000, tz=timezone.utc)
            if unit == "day":
                key = dt.strftime("%Y-%m-%d")
            elif unit == "week":
                key = dt.strftime("%G-W%V")
            else:
                key = dt.strftime("%Y-%m")
            buckets[key] = buckets.get(key, 0) + 1
        return [
            {"periodo": _day_key_to_epoch_ms(k), "total_casos": v} for k, v in sorted(buckets.items())
        ]

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
        if "IDACCIDENTE LIKE" in sql_upper:
            patron = (params.get("busqueda") or "").strip("%")
            rows = [r for r in rows if patron in r["idaccidente"].upper()]
        if "CURSOR_FECHA" in sql_upper:
            cf = params.get("cursor_fecha")
            ci = params.get("cursor_id")
            rows = [
                r for r in rows
                if (r.get("fechahoraaccidente") or 0) < cf
                or ((r.get("fechahoraaccidente") or 0) == cf and r["idaccidente"] < ci)
            ]
        elif "IDACCIDENTE <" in sql_upper:
            rows = [r for r in rows if r["idaccidente"] < params.get("cursor")]
        if "ORDER BY FECHAHORAACCIDENTE DESC, IDACCIDENTE DESC" in sql_upper:
            rows = sorted(rows, key=lambda r: (r.get("fechahoraaccidente") or 0, r["idaccidente"]), reverse=True)
        elif "ORDER BY IDACCIDENTE DESC" in sql_upper:
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

    if "FROM DIM_CONDADO" in sql_upper and "WHERE IDCONDADO IN" in sql_upper:
        ids = params.get("ids") or []
        return [c for c in PINOT_STORE["Dim_Condado"] if c.get("idcondado") in ids]

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

    if "FROM FACT_HISTORIALSEVERIDADACCIDENTE" in sql_upper:
        aid = params.get("idaccidente")
        return [
            r for r in PINOT_STORE["Fact_HistorialSeveridadAccidente"]
            if r["idaccidente"] == aid
        ]

    if "FROM FACT_CIERREACCIDENTE" in sql_upper:
        aid = params.get("idaccidente")
        rows = [r for r in PINOT_STORE["Fact_CierreAccidente"] if r["idaccidente"] == aid]
        return rows[:1] if "LIMIT 1" in sql_upper else rows

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
        if "IDHISTORIALUNIDADEMERGENCIA >" in sql_upper:
            rows = [
                r for r in rows
                if int(r.get("idhistorialunidademergencia") or 0) > int(params.get("cursor", 0))
            ]
        if "ORDER BY IDHISTORIALUNIDADEMERGENCIA" in sql_upper:
            rows = sorted(rows, key=lambda r: int(r.get("idhistorialunidademergencia") or 0))
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
        filas = [n for n in PINOT_STORE["Dim_NotaAccidente"] if n["idaccidente"] == aid] \
            if "WHERE IDACCIDENTE" in sql_upper else list(PINOT_STORE["Dim_NotaAccidente"])
        # Última alerta cuyo texto contiene un marcador (guarda anti-repetición
        # del aviso de señal GPS perdida): el doble tiene que soportar el LIKE
        # y el ORDER BY, o la prueba no vería la diferencia.
        if "TIPO = 'ALERTA'" in sql_upper and "LIKE" not in sql_upper:
            filas = [n for n in filas if n.get("tipo") == "alerta"]
            filas.sort(key=lambda n: n.get("fechahora", 0), reverse=True)
            return filas
        if "TIPO = 'ALERTA'" in sql_upper and "LIKE" in sql_upper:
            patron = str(params.get("patron", "%")).strip("%")
            filas = [
                n
                for n in filas
                if n.get("tipo") == "alerta" and patron in str(n.get("nota", ""))
            ]
            filas.sort(key=lambda n: n.get("fechahora", 0), reverse=True)
            return filas[:1]
        return filas

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
            # El filtro por `activo` se aplica SOLO si la consulta lo pide. Antes se
            # aplicaba siempre, así que `find_by_placa` —que busca la placa en
            # cualquier estado para impedir duplicarla contra una unidad de baja—
            # recibía del doble solo las activas y la prueba no veía nada.
            solo_activas = "ACTIVO = TRUE" in sql_upper
            return [
                u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u.get("placa") == placa and (u.get("activo") or not solo_activas)
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
        if "WHERE IDUNIDADEMERGENCIA IN" in sql_upper:
            ids = params.get("ids") or []
            return [
                u for u in PINOT_STORE["Dim_UnidadEmergencia"]
                if u.get("idunidademergencia") in ids
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

    if "FROM DIM_ORIGENDESPACHO" in sql_upper:
        return list(PINOT_STORE["Dim_OrigenDespacho"])

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
        if "ACTIVO = TRUE" in sql_upper:
            rows = [r for r in rows if r.get("activo") is True]
        if "ORDER BY FECHA_INICIO DESC" in sql_upper:
            rows = sorted(rows, key=lambda r: r.get("fecha_inicio") or 0, reverse=True)
        if "LIMIT 1" in sql_upper:
            rows = rows[:1]
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
def reset_secuencia_ids():
    """Olvida la marca alta de identificadores entre pruebas.

    ⚠️ `core.pinot.secuencia` guarda **en el módulo** el id más alto entregado
    por tabla: es lo que impide repartir el mismo id dos veces mientras Pinot
    ingiere. Esa memoria sobrevive a `_reset_pinot_store`, así que sin esta
    limpieza una prueba que crea tres sesiones deja a la siguiente empezando en
    4, y las que afirman «la primera es la 1» fallan **según el orden de
    colección** — que es exactamente el tipo de fallo que no se reproduce
    aislado.
    """
    reiniciar_secuencia()
    yield
    reiniciar_secuencia()


@pytest.fixture(autouse=True)
def reset_throttle_history():
    """Clear DRF throttle counters between tests.

    SimpleRateThrottle persists its history in django.core.cache, which lives
    for the whole pytest process. Without this reset a test that exhausts a
    scope (p. ej. `prospecto_registro`: 10/min) makes every later test hitting
    the same endpoint fail with 429 depending on collection order.

    OJO: esta limpieza tambien aisla la **lista de denegacion de credenciales**
    de #09 (`services/denylist_credenciales.py`), que vive en el mismo cache. Si
    algun dia se acota este reset a las claves de throttle, hay que anadir
    `partners:denylist:*` explicitamente: sin eso, una credencial revocada en un
    test rechazaria peticiones en los siguientes.
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
        # Copia, no referencia: el productor real serializa a JSON dentro de
        # publish(), así que lo que viaja por Kafka es el estado del dict en
        # ese instante. Guardar la referencia dejaba ver a las pruebas campos
        # que el emisor añade *después* de publicar y que ningún consumidor
        # recibe jamás (B27: `append_estado` añade "estado" al volver).
        published.append({"topic": topic, "payload": dict(payload)})
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
            topic.endswith("Fact_HistorialSeveridadAccidente_topic")
            or topic == "Fact_HistorialSeveridadAccidente_topic"
        ):
            PINOT_STORE["Fact_HistorialSeveridadAccidente"].append(payload)
        elif (
            topic.endswith("Fact_CierreAccidente_topic")
            or topic == "Fact_CierreAccidente_topic"
        ):
            rows = PINOT_STORE["Fact_CierreAccidente"]
            existing_idx = next(
                (i for i, p in enumerate(rows) if p.get("idaccidente") == payload.get("idaccidente")),
                None,
            )
            if existing_idx is not None:
                rows[existing_idx] = payload
            else:
                rows.append(payload)
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
        # --- Partners y API (CU-O48 a CU-O55) ---
        elif topic.endswith("Dim_Partner_topic"):
            _upsert_por_pk(PINOT_STORE["Dim_Partner"], payload, "idpartner")
        elif topic.endswith("Dim_CredencialAPI_topic"):
            _upsert_por_pk(PINOT_STORE["Dim_CredencialAPI"], payload, "idcredencial")
        elif topic.endswith("Dim_VersionContratoAPI_topic"):
            _upsert_por_pk(PINOT_STORE["Dim_VersionContratoAPI"], payload, "idversion")
        elif topic.endswith("Fact_HistorialAccesoPartner_topic"):
            # Bitacora inmutable: solo INSERT, nunca upsert (RN-PON-010).
            PINOT_STORE["Fact_HistorialAccesoPartner"].append(payload)
        # --- Monitoreo y facturacion de API (#08) ---
        elif topic.endswith("Fact_APIIntegracion_topic"):
            # Append-only (RNF-APM-005): cada llamada es una fila nueva.
            PINOT_STORE["Fact_APIIntegracion"].append(payload)
        elif topic.endswith("Fact_LogLlamadaAPI_topic"):
            # Append-only: incluye tambien las peticiones rechazadas.
            PINOT_STORE["Fact_LogLlamadaAPI"].append(payload)
        elif topic.endswith("Dim_EstadoIntegracion_topic"):
            _upsert_por_pk(
                PINOT_STORE["Dim_EstadoIntegracion"], payload, "idestadointegracion"
            )
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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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


# --- Partners y API (CU-O48 a CU-O55) ---

def _sembrar_credencial_api(*, entorno, idcredencial, idpartner=880):
    """Siembra partner + credencial y devuelve las cabeceras de maquina.

    La API de datos de partners (#08) NO se autentica con JWT: usa
    `X-Client-Id` + `X-Client-Secret` contra `Dim_CredencialAPI`. El secreto se
    hashea aqui igual que en produccion para que la verificacion bcrypt sea la
    real y no un atajo del test.
    """
    from apps.partners.services.secreto_service import SecretoService

    secreto = f"secreto-de-prueba-{entorno.lower()}-{idcredencial}"

    if not any(p["idpartner"] == idpartner for p in PINOT_STORE["Dim_Partner"]):
        PINOT_STORE["Dim_Partner"].append({
            "idpartner": idpartner,
            "idcliente": idpartner,
            "nombrepartner": "Partner de pruebas",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "Profesional",
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 1,
            "sandbox_expiracion": 253402300799000,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        })

    PINOT_STORE["Dim_CredencialAPI"].append({
        "idcredencial": idcredencial,
        "idpartner": idpartner,
        "idcliente": idpartner,
        "client_secret_hash": SecretoService().hash(secreto),
        "nombre_credencial": f"cred-{entorno.lower()}",
        "entorno": entorno,
        "activo": True,
        "fecha_creacion": 1,
        "fecha_expiracion": 253402300799000,
        "fecha_actualizacion": 1,
    })

    return {
        "HTTP_X_CLIENT_ID": f"tsi-p{idpartner}-c{idcredencial}",
        "HTTP_X_CLIENT_SECRET": secreto,
    }


@pytest.fixture
def credencial_sandbox_headers(mock_pinot, mock_kafka):
    """Credencial de API en entorno de pruebas."""
    return _sembrar_credencial_api(entorno="Sandbox", idcredencial=8801)


@pytest.fixture
def credencial_produccion_headers(mock_pinot, mock_kafka):
    """Credencial de API en produccion."""
    return _sembrar_credencial_api(entorno="Producción", idcredencial=8802)


@pytest.fixture
def devapis_auth_headers(mock_pinot, mock_kafka):
    """JWT del Desarrollador de APIs: registra partners y asigna planes."""
    PINOT_STORE["Fact_Session"].append(
        {"idsession": 50, "idusuario": 50, "estadosession": "Inicio sesion"}
    )
    token = create_access_token(user_id=50, roles=["DesarrolladorAPIs"], session_id=50)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def partner_auth_headers(mock_pinot, mock_kafka):
    """JWT del Partner de integracion (idrol 15) — autoservicio sobre lo suyo.

    El usuario 51 se vincula al cliente 1 via Dim_Usuario_Cliente para que
    `verificar_propiedad` lo resuelva (el JWT no lleva idcliente).
    """
    PINOT_STORE["Fact_Session"].append(
        {"idsession": 51, "idusuario": 51, "estadosession": "Inicio sesion"}
    )
    PINOT_STORE.setdefault("Dim_Usuario_Cliente", []).append(
        {"idusuario": 51, "idcliente": 1}
    )
    token = create_access_token(user_id=51, roles=["PartnerIntegracion"], session_id=51)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def partner_ajeno_auth_headers(mock_pinot, mock_kafka):
    """Partner vinculado a OTRO cliente — para probar el control de propiedad."""
    PINOT_STORE["Fact_Session"].append(
        {"idsession": 52, "idusuario": 52, "estadosession": "Inicio sesion"}
    )
    PINOT_STORE.setdefault("Dim_Usuario_Cliente", []).append(
        {"idusuario": 52, "idcliente": 999}
    )
    token = create_access_token(user_id=52, roles=["PartnerIntegracion"], session_id=52)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def partner_con_credenciales(mock_pinot, mock_kafka):
    """Partner 1 con tres credenciales en los tres estados posibles (#09).

    Es el escenario que da sentido a la reactivacion selectiva: A y B activas, y
    C que el partner **revoco por seguridad**. Al suspender, las tres quedan
    inactivas; al reactivar deben volver solo A y B.

    C se siembra ya inactiva Y con su fila de bitacora de revocacion, igual que
    la habria dejado el servicio real: sin esa fila, un test podria pasar por el
    motivo equivocado.
    """
    from apps.partners.services.secreto_service import SecretoService

    idpartner = 1
    PINOT_STORE["Dim_Partner"].append({
        "idpartner": idpartner,
        "idcliente": 1,
        "nombrepartner": "Integradora Andina",
        "contacto_tecnico_nombre": "Ana",
        "contacto_tecnico_gmail": "ana@integradora.com",
        "planapi": "Profesional",
        "limitellamadasmes": 10000,
        "limitellamadasminuto": 120,
        "sandbox_activado": 1,
        "sandbox_expiracion": 253402300799000,
        "fecha_suspension": "",
        "motivo_suspension": "",
        "activo": True,
        "fecha_actualizacion": 1,
    })

    hash_secreto = SecretoService().hash("secreto-de-prueba")
    for idcredencial, nombre, entorno, activo in (
        (101, "plataforma-siniestros", "Producción", True),
        (102, "tablero-interno", "Sandbox", True),
        (103, "credencial-filtrada", "Producción", False),
    ):
        PINOT_STORE["Dim_CredencialAPI"].append({
            "idcredencial": idcredencial,
            "idpartner": idpartner,
            "idcliente": 1,
            "client_secret_hash": hash_secreto,
            "nombre_credencial": nombre,
            "entorno": entorno,
            "activo": activo,
            "fecha_creacion": 1,
            "fecha_expiracion": 253402300799000,
            "fecha_actualizacion": 1,
        })

    # La 103 la revoco el partner: queda constancia, como en produccion.
    PINOT_STORE["Fact_HistorialAccesoPartner"].append({
        "idhistorial": 1,
        "idpartner": idpartner,
        "idcredencial": 103,
        "tipo_cambio": "revocacion_credencial",
        "ejecutado_por": "Partner",
        "motivo": "credencial expuesta en repositorio público",
        "estado_anterior": "Activo",
        "estado_nuevo": "Activo",
        "fecha_cambio": 1,
        "fecha_actualizacion": 1,
    })
    return {"idpartner": idpartner, "activas": [101, 102], "revocada": 103}


@pytest.fixture
def partner_suspendido(partner_con_credenciales):
    """El mismo partner, ya suspendido y con su cascada escrita.

    Reproduce el estado que deja `SuspenderPartnerService`: las tres
    credenciales inactivas, pero **solo dos filas de cascada** — la revocada no
    genero ninguna porque ya estaba inactiva cuando llego la suspension. Esa
    ausencia es justo lo que impide resucitarla al reactivar.
    """
    idpartner = partner_con_credenciales["idpartner"]
    for partner in PINOT_STORE["Dim_Partner"]:
        if partner["idpartner"] == idpartner:
            partner.update({
                "activo": False,
                "fecha_suspension": "2026-08-10T00:00:00+00:00",
                "motivo_suspension": "Mora de 16 días en facturas de excedente de API",
            })
    for credencial in PINOT_STORE["Dim_CredencialAPI"]:
        if credencial["idpartner"] == idpartner:
            credencial["activo"] = False

    for idhistorial, idcredencial in ((2, 101), (3, 102)):
        PINOT_STORE["Fact_HistorialAccesoPartner"].append({
            "idhistorial": idhistorial,
            "idpartner": idpartner,
            "idcredencial": idcredencial,
            "tipo_cambio": "desactivacion_por_cascada",
            "ejecutado_por": "Sistema",
            "motivo": "Mora de 16 días",
            "estado_anterior": "Activo",
            "estado_nuevo": "Suspendido",
            "fecha_cambio": 100,
            "fecha_actualizacion": 100,
        })
    PINOT_STORE["Fact_HistorialAccesoPartner"].append({
        "idhistorial": 4,
        "idpartner": idpartner,
        "idcredencial": -1,
        "tipo_cambio": "suspension_automatica",
        "ejecutado_por": "Sistema",
        "motivo": "Mora de 16 días",
        "estado_anterior": "Activo",
        "estado_nuevo": "Suspendido",
        "fecha_cambio": 100,
        "fecha_actualizacion": 100,
    })
    return partner_con_credenciales


@pytest.fixture
def factura_excedente_vencida():
    """Fabrica de facturas de excedente para las pruebas de mora (#09).

    `dias_vencida` positivo = ya vencida. El `estado_pago` es lo que decide si
    genera mora aqui: solo `Pendiente` cuenta (§ 15 D3).
    """
    import time

    def _crear(*, idcliente=1, dias_vencida=20, estado_pago="Pendiente",
               tipo="excedente_api", id_factura=None):
        ahora = int(time.time() * 1000)
        fila = {
            "id_factura": id_factura or f"FAC-EXC-{idcliente}-{dias_vencida}-{estado_pago}",
            "id_cliente": idcliente,
            "id_suscripcion": idcliente,
            "tipo": tipo,
            "estado_pago": estado_pago,
            "monto_total": 42.0,
            "periodo": "2026-07",
            "fecha_emision": ahora - dias_vencida * 86_400_000,
            "fecha_vencimiento": ahora - dias_vencida * 86_400_000,
            "activo": True,
            "fecha_actualizacion": ahora,
        }
        PINOT_STORE["Fact_Factura"].append(fila)
        return fila

    return _crear


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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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
            "fechahorainiciosesion": 1783555200000,
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
