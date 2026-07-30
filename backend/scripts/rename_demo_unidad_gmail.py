"""Rename misnamed Unidad demo user gmail (ops one-shot).

diego.ramirez.operador@demo.tsi.com has JWT role Unidad — rename local-part.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from django.conf import settings

OLD = "diego.ramirez.operador@demo.tsi.com"
NEW = "diego.ramirez.unidad@demo.tsi.com"


def main() -> None:
    pinot = PinotClient()
    rows = pinot.query(
        "SELECT * FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
        {"gmail": OLD},
    )
    if not rows:
        # Already renamed?
        rows = pinot.query(
            "SELECT * FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
            {"gmail": NEW},
        )
        if rows:
            print(f"OK already renamed: {NEW} idusuario={rows[0].get('idusuario')}")
            return
        print(f"WARN user not found: {OLD}")
        return

    user = dict(rows[0])
    user["gmail"] = NEW
    user["fecha_actualizacion"] = int(time.time() * 1000)
    KafkaWriter().publish(settings.KAFKA_TOPICS["user"], user)
    print(f"published rename {OLD} → {NEW} idusuario={user.get('idusuario')}")


if __name__ == "__main__":
    main()
