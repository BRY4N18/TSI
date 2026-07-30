"""Seed rol Unidad + Dim_EstadoRegion mínimos (ops Red Operativa O56 / O55).

Run inside Django container:
  python /app/scripts/seed_catalogos_red_operativa.py

From host (Kafka localhost:9092):
  cd backend
  $env:DJANGO_SETTINGS_MODULE='config.settings'
  $env:PYTHONPATH=(Get-Location).Path
  $env:KAFKA_BOOTSTRAP_SERVERS='localhost:9092'
  python scripts/seed_catalogos_red_operativa.py

Publica:
  - Dim_Rol `Unidad` (idrol=4) — requerido por importación lote CU-O56
  - Dim_EstadoRegion (CDMX=1, Jalisco=2) — requerido por alta región CU-O55
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings  # noqa: E402

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

UNIDAD_ROLE_ID = 4


def main() -> None:
    now = int(time.time() * 1000)
    writer = KafkaWriter()
    topics = settings.KAFKA_TOPICS

    writer.publish(
        topics["role"],
        {
            "idrol": UNIDAD_ROLE_ID,
            "rol": "Unidad",
            "descripcion": "Unidad de emergencia (login CU-O30 / lote O56)",
            "activo": True,
            "fecha_actualizacion": now,
        },
    )
    print(f"published Dim_Rol Unidad idrol={UNIDAD_ROLE_ID}")

    estados = [
        {"idestadoregion": 1, "nombre": "CDMX", "activo": True},
        {"idestadoregion": 2, "nombre": "Jalisco", "activo": True},
    ]
    estado_topic = topics["estado_region"]
    for i, row in enumerate(estados):
        writer.publish(
            estado_topic,
            {**row, "fecha_actualizacion": now + i},
        )
        print(f"published Dim_EstadoRegion id={row['idestadoregion']}")

    print("OK — rol Unidad y catálogo Dim_EstadoRegion listos para O56/O55.")


if __name__ == "__main__":
    main()
