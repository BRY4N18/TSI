"""Seed demo users: Operador + reset Admin password (Pinot-compatible Kafka payloads).

Pinot REALTIME schemas expect LONG millis for fecha_* (not ISO strings) and
Dim_Usuario_Rol needs idusuariorol + activo (same shape as initial seed).

Run inside Django container:
  python /app/scripts/seed_demo_usuarios_roles.py

Demo logins (password: password123):
  Operador  sofia.castro.operador@demo.tsi.com
  Admin     carlos.mendoza.admin@demo.tsi.com
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import bcrypt  # noqa: E402
from django.conf import settings  # noqa: E402

from core.pinot.client import PinotClient  # noqa: E402
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

DEMO_PASSWORD = "password123"
OPERADOR_GMAIL = "sofia.castro.operador@demo.tsi.com"
ADMIN_GMAIL = "carlos.mendoza.admin@demo.tsi.com"

OPERADOR_USER_ID = 10
OPERADOR_ROLE_ID = 11
OPERADOR_CRED_ID = 10
OPERADOR_USER_ROLE_ID = 30  # seed used 1–20; keep clear of collisions
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
            "estadocredencial": "ACTIVA",
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
                "estadocredencial": "ACTIVA",
                "fecha_actualizacion": now + 4,
            },
        )
        print(f"published Dim_Credencial Admin idusuario={admin_id} password=password123")

    print()
    print("Demo logins (password for both: password123)")
    print(f"  Operador → {OPERADOR_GMAIL}   → /accidentes/lista")
    print(f"  Admin    → {ADMIN_GMAIL} → /suscripciones/catalogo-planes")
    print("OK — wait ~5–15s for Pinot realtime before login.")


if __name__ == "__main__":
    main()
