"""Seed Dim_Servicio + rol SupervisorSoporte (ops CU-O91 / CU-O96).

Run inside Django container:
  python /app/scripts/seed_catalogos_soporte.py

From host (Kafka localhost:9092):
  cd backend
  $env:DJANGO_SETTINGS_MODULE='config.settings'
  $env:PYTHONPATH=(Get-Location).Path
  $env:KAFKA_BOOTSTRAP_SERVERS='localhost:9092'
  python scripts/seed_catalogos_soporte.py

Opcional — también publica Dim_Usuario_Rol para el supervisor:
  $env:SOPORTE_SUPERVISOR_USER_ID='15'
  python scripts/seed_catalogos_soporte.py

El escalado SLA resuelve por rol SupervisorSoporte; el env solo fuerza
preferencia si hay varios usuarios con ese rol.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

SUPERVISOR_ROLE_ID = 10


def main() -> None:
    now = int(time.time() * 1000)
    writer = KafkaWriter()

    servicios = [
        {
            "id_servicio": 1,
            "nombre": "API Despacho",
            "tipo": "api",
            "descripcion": "Endpoints de despacho inteligente",
        },
        {
            "id_servicio": 2,
            "nombre": "API Registro de accidentes",
            "tipo": "api",
            "descripcion": "CU-O21 y consulta de casos",
        },
        {
            "id_servicio": 3,
            "nombre": "Portal Cliente",
            "tipo": "portal",
            "descripcion": "Acceso web corporativo",
        },
    ]
    for i, row in enumerate(servicios):
        writer.publish(
            "Dim_Servicio_topic",
            {**row, "activo": True, "fecha_actualizacion": now + i},
        )
        print(f"published Dim_Servicio id={row['id_servicio']}")

    writer.publish(
        "Dim_Rol_topic",
        {
            "idrol": SUPERVISOR_ROLE_ID,
            "rol": "SupervisorSoporte",
            "descripcion": "Receptor de escalado automático SLA (RN-TIC-005)",
            "activo": True,
            "fecha_actualizacion": now + 100,
        },
    )
    print(f"published Dim_Rol SupervisorSoporte idrol={SUPERVISOR_ROLE_ID}")

    raw_uid = os.environ.get("SOPORTE_SUPERVISOR_USER_ID", "").strip()
    if raw_uid:
        idusuario = int(raw_uid)
        writer.publish(
            "Dim_Usuario_Rol_topic",
            {
                "idusuario": idusuario,
                "idrol": SUPERVISOR_ROLE_ID,
                "fecha_actualizacion": now + 200,
            },
        )
        print(
            f"published Dim_Usuario_Rol idusuario={idusuario} "
            f"idrol={SUPERVISOR_ROLE_ID} (SupervisorSoporte)"
        )
    else:
        print(
            "OK — asigne el rol SupervisorSoporte a un usuario en Dim_Usuario_Rol "
            "(o re-ejecute con SOPORTE_SUPERVISOR_USER_ID=<id> para publicarlo)."
        )


if __name__ == "__main__":
    main()
