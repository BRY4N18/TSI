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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import bcrypt  # noqa: E402
from django.conf import settings  # noqa: E402

from core.pinot.client import PinotClient  # noqa: E402
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

from _demo_seed_common import DEMO_PASSWORD, ESTADO_CREDENCIAL_ACTIVO  # noqa: E402
GMAIL = "elena.nunez.estrategia@demo.tsi.com"
ROLE_NAME = "DirectorEstrategia"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def _siguiente_id(pinot: PinotClient, columna: str, tabla: str) -> int:
    """Primer id libre de la tabla.

    Antes estos ids venian hardcodeados (USER_ID/ROLE_ID/CRED_ID = 12,
    USER_ROLE_ID = 31) y chocaban con los que ya reservaba
    seed_demo_usuarios_roles.py para el Gerente de Ventas. Como las tablas de
    Pinot son upsert por clave primaria, correr este seed despues del otro
    sobrescribia a ese usuario en silencio en vez de agregar uno nuevo.
    """
    rows = pinot.query(f"SELECT MAX({columna}) AS max_id FROM {tabla}")
    max_id = rows[0].get("max_id") if rows else 0
    return int(max_id or 0) + 1


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
    role_id = int(existing_role[0]["idrol"]) if existing_role else _siguiente_id(pinot, "idrol", "Dim_Rol")
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
    user_id = int(existing_user[0]["idusuario"]) if existing_user else _siguiente_id(pinot, "idusuario", "Dim_Usuarios")
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

    existing_cred = pinot.query(
        "SELECT idcredencial FROM Dim_Credencial WHERE idusuario = %(idusuario)s LIMIT 1",
        {"idusuario": user_id},
    )
    cred_id = (
        int(existing_cred[0]["idcredencial"])
        if existing_cred
        else _siguiente_id(pinot, "idcredencial", "Dim_Credencial")
    )
    user_role_id = _siguiente_id(pinot, "idusuariorol", "Dim_Usuario_Rol")

    writer.publish(
        topics["credential"],
        {
            "idcredencial": cred_id,
            "idusuario": user_id,
            "contrasena": pwd_hash,
            "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
            "fecha_actualizacion": now + 2,
        },
    )
    print(f"published Dim_Credencial idcredencial={cred_id}")

    writer.publish(
        topics["user_role"],
        {
            "idusuariorol": user_role_id,
            "idusuario": user_id,
            "idrol": role_id,
            "activo": True,
            "fecha_actualizacion": now + 3,
        },
    )
    print(f"published Dim_Usuario_Rol idusuariorol={user_role_id}")

    print()
    print(f"Demo login: {GMAIL} / {DEMO_PASSWORD}")
    print("OK — wait ~5–15s for Pinot realtime before login.")


if __name__ == "__main__":
    main()
