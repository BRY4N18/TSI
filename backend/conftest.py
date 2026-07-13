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
            "estadoregion": "Producción",
            "activo": True,
            "nombreregion": "Centro",
        }
    ],
    "Dim_RegionOperativaEstadoRegion": [
        {"idregionoperativa": 1, "idestadoregion": 1},
    ],
}

# Pre-compute bcrypt hash for "password123" at import (rounds=4 for test speed)
_TEST_PASSWORD_HASH = bcrypt.hashpw(b"password123", bcrypt.gensalt(rounds=4)).decode()
for _cred in _INITIAL_PINOT_STORE["Dim_Credencial"]:
    _cred["contrasena"] = _TEST_PASSWORD_HASH

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
    if "MAX(IDHISTORIALUBICACION)" in sql_upper:
        ids = [
            r["idhistorialubicacion"]
            for r in PINOT_STORE["Dim_HistorialUbicacionUnidadEmergencia"]
        ]
        return [{"max_id": max(ids) if ids else 0}]

    # --- Dim_Cliente ---
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE NIT_IDENTIFICACION" in sql_upper:
        nit = params.get("nit")
        return [c for c in PINOT_STORE["Dim_Cliente"] if c["nit_identificacion"] == nit]
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE ADMIN_LOCAL_ID" in sql_upper:
        admin_id = params.get("admin_local_id")
        return [c for c in PINOT_STORE["Dim_Cliente"] if c.get("admin_local_id") == admin_id]
    if "FROM DIM_CLIENTE" in sql_upper and "WHERE IDCLIENTE" in sql_upper:
        cid = params.get("idcliente")
        return [c for c in PINOT_STORE["Dim_Cliente"] if c["idcliente"] == cid]

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
            return [a for a in PINOT_STORE["Fact_Accidente"] if a.get("activo") == activo]
        if "ACTIVO = TRUE" in sql_upper or "activo = true" in sql:
            return [a for a in PINOT_STORE["Fact_Accidente"] if a.get("activo") is True]
        return list(PINOT_STORE["Fact_Accidente"])

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
            return [e for e in PINOT_STORE["Dim_EvidenciaFoto"] if e["idaccidente"] == aid]
        return list(PINOT_STORE["Dim_EvidenciaFoto"])

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
        return rows

    if "FROM DIM_UNIDADEMERGENCIA" in sql_upper:
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
            return [u for u in PINOT_STORE["Dim_UnidadEmergencia"] if u.get("activo")]
        return list(PINOT_STORE["Dim_UnidadEmergencia"])

    if "FROM DIM_ESTADOUNIDADEMERGENCIA" in sql_upper:
        return list(PINOT_STORE["Dim_EstadoUnidadEmergencia"])

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
            pass
        elif (
            topic.endswith("Dim_ElementoFisicoAccidente_topic")
            or topic == "Dim_ElementoFisicoAccidente_topic"
        ):
            pass
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
