"""Seed Dim_TipoReportado y Dim_ReferenciaEstacion vía Kafka → Pinot (CU-O21).

Run inside Django container:
  python /app/scripts/seed_catalogos_registro.py

From host (Kafka en localhost:9092, Django settings):
  cd backend
  $env:DJANGO_SETTINGS_MODULE='config.settings'
  $env:PYTHONPATH=(Get-Location).Path
  python scripts/seed_catalogos_registro.py
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


def main() -> None:
    now = int(time.time() * 1000)
    writer = KafkaWriter()

    tipos = [
        {"idtiporeportado": 1, "tiporeportado": "Llamada telefónica"},
        {"idtiporeportado": 2, "tiporeportado": "App móvil"},
        {"idtiporeportado": 3, "tiporeportado": "Integración API"},
        {"idtiporeportado": 4, "tiporeportado": "Cámara de tráfico"},
    ]
    for i, row in enumerate(tipos):
        payload = {**row, "activo": True, "fecha_actualizacion": now + i}
        writer.publish("Dim_TipoReportado_topic", payload)
        print(f"published Dim_TipoReportado id={row['idtiporeportado']}")

    estaciones = [
        {
            "idreferenciaestacion": 1,
            "codigoaeropuerto": "MEX",
            "zonahoraria": "America/Mexico_City",
        },
        {
            "idreferenciaestacion": 2,
            "codigoaeropuerto": "CUN",
            "zonahoraria": "America/Cancun",
        },
        {
            "idreferenciaestacion": 3,
            "codigoaeropuerto": "GDL",
            "zonahoraria": "America/Mexico_City",
        },
        {
            "idreferenciaestacion": 5,
            "codigoaeropuerto": "TIJ",
            "zonahoraria": "America/Tijuana",
        },
    ]
    for i, row in enumerate(estaciones):
        payload = {**row, "activo": True, "fecha_actualizacion": now + 100 + i}
        writer.publish("Dim_ReferenciaEstacion_topic", payload)
        print(f"published Dim_ReferenciaEstacion id={row['idreferenciaestacion']}")

    print("OK — catálogos registro publicados (TipoReportado + ReferenciaEstacion)")
    print(
        "Verificar en UI: GET /api/v1/accidentes/tipos-reportado y "
        "/api/v1/accidentes/referencias-estacion (tras ingest Pinot)."
    )


if __name__ == "__main__":
    main()
