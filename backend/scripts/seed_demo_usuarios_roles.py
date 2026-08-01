"""Seed demo users: Operador + GerenteVentas + reset Admin password (Pinot-compatible Kafka payloads).

Pinot REALTIME schemas expect LONG millis for fecha_* (not ISO strings) and
Dim_Usuario_Rol needs idusuariorol + activo (same shape as initial seed).

Run inside Django container:
  python /app/scripts/seed_demo_usuarios_roles.py

Demo logins (password: password123):
  Operador       sofia.castro.operador@demo.tsi.com
  GerenteVentas  lucia.ramos.ventas@demo.tsi.com
  Admin          carlos.mendoza.admin@demo.tsi.com
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import bcrypt  # noqa: E402
from django.conf import settings  # noqa: E402

from core.pinot.client import PinotClient  # noqa: E402
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

from _demo_seed_common import (  # noqa: E402
    DEMO_PASSWORD,
    ESTADO_CREDENCIAL_ACTIVO,
    ROL_ID_POR_NOMBRE,
)
OPERADOR_GMAIL = "sofia.castro.operador@demo.tsi.com"
GERENTE_VENTAS_GMAIL = "lucia.ramos.ventas@demo.tsi.com"
ADMIN_GMAIL = "carlos.mendoza.admin@demo.tsi.com"

OPERADOR_USER_ID = 10
# Los idrol salen del catalogo canonico compartido: antes esta constante valia
# 11 y creaba un segundo rol "Operador" junto al idrol 4 de database/seed_usuarios.py.
OPERADOR_ROLE_ID = ROL_ID_POR_NOMBRE["Operador"]
OPERADOR_CRED_ID = 10
OPERADOR_USER_ROLE_ID = 30  # seed used 1–20; keep clear of collisions
GERENTE_VENTAS_USER_ID = 12
GERENTE_VENTAS_ROLE_ID = ROL_ID_POR_NOMBRE["GerenteVentas"]
GERENTE_VENTAS_CRED_ID = 12
GERENTE_VENTAS_USER_ROLE_ID = 31
ADMIN_USER_ID = 2
ADMIN_CRED_ID = 2


def _now_ms() -> int:
    return int(time.time() * 1000)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def main() -> None:
    pinot = PinotClient()
    writer = KafkaWriter()
    topics = settings.KAFKA_TOPICS
    now = _now_ms()
    pwd_hash = _hash(DEMO_PASSWORD)

    # --- Role Operador ---
    existing_role = pinot.query(
        "SELECT idrol FROM Dim_Rol WHERE rol = %(rol)s LIMIT 1",
        {"rol": "Operador"},
    )
    role_id = int(existing_role[0]["idrol"]) if existing_role else OPERADOR_ROLE_ID
    writer.publish(
        topics["role"],
        {
            "idrol": role_id,
            "rol": "Operador",
            "descripcion": "Operador de emergencias (accidentes / despacho / seguimiento)",
            "activo": True,
            "fecha_actualizacion": now,
        },
    )
    print(f"published Dim_Rol Operador idrol={role_id}")

    # --- User Operador ---
    existing_user = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": OPERADOR_GMAIL},
    )
    user_id = int(existing_user[0]["idusuario"]) if existing_user else OPERADOR_USER_ID
    writer.publish(
        topics["user"],
        {
            "idusuario": user_id,
            "nombres": "Sofia",
            "apellidos": "Castro",
            "gmail": OPERADOR_GMAIL,
            "identificacion": "OP-DEMO-001",
            "genero": "F",
            "telefono": "0991234510",
            "activo": True,
            "fechanacimiento": 645580800000,  # 1990-06-15 approx ms
            "fecha_actualizacion": now + 1,
        },
    )
    print(f"published Dim_Usuarios Operador idusuario={user_id}")

    # --- Credential Operador ---
    writer.publish(
        topics["credential"],
        {
            "idcredencial": OPERADOR_CRED_ID,
            "idusuario": user_id,
            "contrasena": pwd_hash,
            "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
            "fecha_actualizacion": now + 2,
        },
    )
    print(f"published Dim_Credencial Operador idcredencial={OPERADOR_CRED_ID}")

    # --- Usuario_Rol Operador ---
    writer.publish(
        topics["user_role"],
        {
            "idusuariorol": OPERADOR_USER_ROLE_ID,
            "idusuario": user_id,
            "idrol": role_id,
            "activo": True,
            "fecha_actualizacion": now + 3,
        },
    )
    print(f"published Dim_Usuario_Rol Operador idusuariorol={OPERADOR_USER_ROLE_ID}")

    # --- Role GerenteVentas ---
    existing_gv_role = pinot.query(
        "SELECT idrol FROM Dim_Rol WHERE rol = %(rol)s LIMIT 1",
        {"rol": "GerenteVentas"},
    )
    gv_role_id = int(existing_gv_role[0]["idrol"]) if existing_gv_role else GERENTE_VENTAS_ROLE_ID
    writer.publish(
        topics["role"],
        {
            "idrol": gv_role_id,
            "rol": "GerenteVentas",
            "descripcion": "Gerente de ventas — pipeline comercial y prospectos",
            "activo": True,
            "fecha_actualizacion": now + 5,
        },
    )
    print(f"published Dim_Rol GerenteVentas idrol={gv_role_id}")

    existing_gv_user = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": GERENTE_VENTAS_GMAIL},
    )
    gv_user_id = (
        int(existing_gv_user[0]["idusuario"]) if existing_gv_user else GERENTE_VENTAS_USER_ID
    )
    writer.publish(
        topics["user"],
        {
            "idusuario": gv_user_id,
            "nombres": "Lucia",
            "apellidos": "Ramos",
            "gmail": GERENTE_VENTAS_GMAIL,
            "identificacion": "GV-DEMO-001",
            "genero": "F",
            "telefono": "0991234512",
            "activo": True,
            "fechanacimiento": 662688000000,
            "fecha_actualizacion": now + 6,
        },
    )
    print(f"published Dim_Usuarios GerenteVentas idusuario={gv_user_id}")

    writer.publish(
        topics["credential"],
        {
            "idcredencial": GERENTE_VENTAS_CRED_ID,
            "idusuario": gv_user_id,
            "contrasena": pwd_hash,
            "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
            "fecha_actualizacion": now + 7,
        },
    )
    print(f"published Dim_Credencial GerenteVentas idcredencial={GERENTE_VENTAS_CRED_ID}")

    writer.publish(
        topics["user_role"],
        {
            "idusuariorol": GERENTE_VENTAS_USER_ROLE_ID,
            "idusuario": gv_user_id,
            "idrol": gv_role_id,
            "activo": True,
            "fecha_actualizacion": now + 8,
        },
    )
    print(f"published Dim_Usuario_Rol GerenteVentas idusuariorol={GERENTE_VENTAS_USER_ROLE_ID}")

    # --- Reset Admin password (planes / catálogo / aprobaciones) ---
    admin = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": ADMIN_GMAIL},
    )
    if not admin:
        print(f"WARN admin not found: {ADMIN_GMAIL}")
    else:
        admin_id = int(admin[0]["idusuario"])
        writer.publish(
            topics["credential"],
            {
                "idcredencial": ADMIN_CRED_ID,
                "idusuario": admin_id,
                "contrasena": pwd_hash,
                "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
                "fecha_actualizacion": now + 4,
            },
        )
        print(f"published Dim_Credencial Admin idusuario={admin_id} password=password123")

    print()
    print("Demo logins (password for all: password123)")
    print(f"  Operador       → {OPERADOR_GMAIL}   → /accidentes/lista")
    print(f"  GerenteVentas  → {GERENTE_VENTAS_GMAIL} → /ventas-crm/prospectos")
    print(f"  Admin          → {ADMIN_GMAIL} → /suscripciones/catalogo-planes")
    print("OK — wait ~5–15s for Pinot realtime before login.")


if __name__ == "__main__":
    main()
