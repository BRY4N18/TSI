"""Seed / reset demo Proveedor de flota for local UX review (alta-unidades).

Creates or refreshes:
  - Dim_Rol `Proveedor` (JWT lands on /red-operativa/alta-unidades/catalogo)
  - Link Dim_Usuario_Rol for ana.torres (admin_local of Dim_Cliente Activo #1)
  - Password reset to password123

Demo login:
  ana.torres.cliente@demo.tsi.com / password123

Run inside Django container:
  docker exec -e PYTHONPATH=/app -e DJANGO_SETTINGS_MODULE=config.settings \\
    accidentes-django python /app/scripts/seed_demo_proveedor_flota.py
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
GMAIL = "ana.torres.cliente@demo.tsi.com"
CRED_ID = 1
PROVEEDOR_ROLE_ID = 13
PROVEEDOR_USER_ROLE_ID = 40


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

    user = pinot.query(
        "SELECT idusuario FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": GMAIL},
    )
    if not user:
        print(f"ERROR: usuario no encontrado: {GMAIL}")
        sys.exit(1)
    user_id = int(user[0]["idusuario"])

    cliente = pinot.query(
        "SELECT idcliente, estado, admin_local_id, nombre FROM Dim_Cliente WHERE admin_local_id = %(uid)s LIMIT 1",
        {"uid": user_id},
    )
    if not cliente:
        print(f"ERROR: Dim_Cliente con admin_local_id={user_id} no encontrado")
        sys.exit(1)
    if cliente[0].get("estado") != "Activo":
        print(f"WARN: cliente estado={cliente[0].get('estado')} (se espera Activo)")

    existing_role = pinot.query(
        "SELECT idrol FROM Dim_Rol WHERE rol = %(rol)s LIMIT 1",
        {"rol": "Proveedor"},
    )
    role_id = int(existing_role[0]["idrol"]) if existing_role else PROVEEDOR_ROLE_ID
    writer.publish(
        topics["role"],
        {
            "idrol": role_id,
            "rol": "Proveedor",
            "descripcion": "Proveedor de flota de unidades de emergencia",
            "activo": True,
            "fecha_actualizacion": now,
        },
    )
    print(f"published Dim_Rol Proveedor idrol={role_id}")

    writer.publish(
        topics["user_role"],
        {
            "idusuariorol": PROVEEDOR_USER_ROLE_ID,
            "idusuario": user_id,
            "idrol": role_id,
            "activo": True,
            "fecha_actualizacion": now + 1,
        },
    )
    print(f"published Dim_Usuario_Rol Proveedor idusuariorol={PROVEEDOR_USER_ROLE_ID}")

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
    print(f"published Dim_Credencial password reset for idusuario={user_id}")

    print()
    print("Demo Proveedor flota (password: password123)")
    print(f"  {GMAIL}")
    print(
        f"  cliente=#{cliente[0]['idcliente']} {cliente[0].get('nombre')} "
        f"estado={cliente[0].get('estado')}"
    )
    print("  → http://localhost:4200/red-operativa/alta-unidades/catalogo")
    print("OK — wait ~5–15s for Pinot realtime before login.")


if __name__ == "__main__":
    main()
