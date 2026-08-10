"""Seed Dim_Plan via Kafka for local portal visualization (RF-CPP-000).

Run inside the Django container:
  python /app/scripts/seed_planes_publicos.py
or:
  DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=/app python scripts/seed_planes_publicos.py
"""

from __future__ import annotations

import json
import os
import sys
import time

# Allow `python /tmp/...` and host-path runs without manage.py.
sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402


def main() -> None:
    now = int(time.time() * 1000)
    planes = [
        {
            "idplan": 1,
            "nombre": "Básico",
            "nivel": "Básico",
            "limites": json.dumps(
                {"unidades_max": 5, "usuarios_max": 3, "api_calls_mes": 1000, "api_calls_minuto": 30},
                ensure_ascii=False,
            ),
            "periodicidad": "Mensual",
            # Valor inicial de siembra — el Director de Estrategia puede reconfigurarlo
            # libremente; ya no está atado a `nivel` (SRS §3.3.1, RN-SUSF-002).
            "severidades_desbloqueadas": json.dumps(["Baja"], ensure_ascii=False),
            "carga_lote_habilitada": False,
            "activo": True,
            "precio": 49.0,
            # Tarifa unitaria del excedente (RF-O54.1). Por encima del precio
            # incluido; el Director de Estrategia la reconfigura (CU-O26).
            "precio_excedente_llamada": 0.06,
            "fecha_actualizacion": now,
        },
        {
            "idplan": 2,
            "nombre": "Profesional",
            "nivel": "Profesional",
            "limites": json.dumps(
                {"unidades_max": 25, "usuarios_max": 10, "api_calls_mes": 10000, "api_calls_minuto": 120},
                ensure_ascii=False,
            ),
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": json.dumps(["Baja", "Media"], ensure_ascii=False),
            "carga_lote_habilitada": True,
            "activo": True,
            "precio": 149.0,
            # Tarifa unitaria del excedente (RF-O54.1). Por encima del precio
            # incluido; el Director de Estrategia la reconfigura (CU-O26).
            "precio_excedente_llamada": 0.02,
            "fecha_actualizacion": now + 1,
        },
        {
            "idplan": 3,
            "nombre": "Empresarial",
            "nivel": "Empresarial",
            "limites": json.dumps(
                {"unidades_max": 100, "usuarios_max": 50, "api_calls_mes": 100000, "api_calls_minuto": 600},
                ensure_ascii=False,
            ),
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": json.dumps(["Baja", "Media", "Alta"], ensure_ascii=False),
            "carga_lote_habilitada": True,
            "activo": True,
            "precio": 399.0,
            # Tarifa unitaria del excedente (RF-O54.1). Por encima del precio
            # incluido; el Director de Estrategia la reconfigura (CU-O26).
            "precio_excedente_llamada": 0.005,
            "fecha_actualizacion": now + 2,
        },
    ]
    writer = KafkaWriter()
    for plan in planes:
        writer.publish("Dim_Plan_topic", plan)
        print(f"published idplan={plan['idplan']} nombre={plan['nombre']}")


if __name__ == "__main__":
    main()
