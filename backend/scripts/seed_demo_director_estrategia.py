"""Seed demo Director de Estrategia (RF-SUSF-001) — Pinot-compatible Kafka payloads.

Run inside Django container:
  python /app/scripts/seed_demo_director_estrategia.py

Demo login: elena.nunez.estrategia@demo.tsi.com / password123
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
GMAIL = "elena.nunez.estrategia@demo.tsi.com"
ROLE_NAME = "DirectorEstrategia"
USER_ID = 12
ROLE_ID = 12
CRED_ID = 12
USER_ROLE_ID = 31


def _now_ms() -> int:
    return int(time.time() * 1000)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def main() -> None:
    pinot = PinotClient()
    writer = KafkaWriter()
    topics = settings.KAFKA_TOPICS
    now = _now_ms()
    pwd_hash = _hash(DEMO_PASSWORD)

    existing_role = pinot.query(
        "SELECT idrol FROM Dim_Rol WHERE rol = %(rol)s LIMIT 1",
        {"rol": ROLE_NAME},
    )
    role_id = int(existing_role[0]["idrol"]) if existing_role else ROLE_ID
    writer.publish(
        topics["role"],
        {
            "idrol": role_id,
            "rol": ROLE_NAME,
            "descripcion": "Director de Estrategia — catálogo Dim_Plan (RF-SUSF-001)",
            "activo": True,
            "fecha_actualizacion": now,
        },
    )
    print(f"published Dim_Rol {ROLE_NAME} idrol={role_id}")

    existing_user = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": GMAIL},
    )
    user_id = int(existing_user[0]["idusuario"]) if existing_user else USER_ID
    writer.publish(
        topics["user"],
        {
            "idusuario": user_id,
            "nombres": "Elena",
            "apellidos": "Nunez",
            "gmail": GMAIL,
            "identificacion": "DE-DEMO-001",
            "genero": "F",
            "telefono": "0991234512",
            "activo": True,
            "fechanacimiento": 631152000000,
            "fecha_actualizacion": now + 1,
        },
    )
    print(f"published Dim_Usuarios Director idusuario={user_id}")

    writer.publish(
        topics["credential"],
        {
            "idcredencial": CRED_ID,
            "idusuario": user_id,
            "contrasena": pwd_hash,
            "estadocredencial": "ACTIVA",
            "fecha_actualizacion": now + 2,
        },
    )
    print(f"published Dim_Credencial idcredencial={CRED_ID}")

    writer.publish(
        topics["user_role"],
        {
            "idusuariorol": USER_ROLE_ID,
            "idusuario": user_id,
            "idrol": role_id,
            "activo": True,
            "fecha_actualizacion": now + 3,
        },
    )
    print(f"published Dim_Usuario_Rol idusuariorol={USER_ROLE_ID}")

    print()
    print(f"Demo login: {GMAIL} / {DEMO_PASSWORD}")
    print("OK — wait ~5–15s for Pinot realtime before login.")


if __name__ == "__main__":
    main()
