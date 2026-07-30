"""Seed catálogos CU-O46 vía Kafka → Pinot.

Run inside Django container:
  python /app/scripts/seed_catalogos_enriquecimiento.py
or from host (with Django settings):
  DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=backend python backend/scripts/seed_catalogos_enriquecimiento.py
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

    periodos = [
        {
            "idperiododia": 1,
            "amaneceranochecer": "Mañana",
            "crepusculocivil": None,
            "crepusculonautico": None,
            "crepusculoastronomico": None,
            "activo": True,
            "fecha_actualizacion": now,
        },
        {
            "idperiododia": 2,
            "amaneceranochecer": "Tarde",
            "crepusculocivil": None,
            "crepusculonautico": None,
            "crepusculoastronomico": None,
            "activo": True,
            "fecha_actualizacion": now + 1,
        },
        {
            "idperiododia": 3,
            "amaneceranochecer": "Noche",
            "crepusculocivil": None,
            "crepusculonautico": None,
            "crepusculoastronomico": None,
            "activo": True,
            "fecha_actualizacion": now + 2,
        },
    ]
    for row in periodos:
        writer.publish("Dim_PeriodosDias_topic", row)
        print(f"published Dim_PeriodosDias idperiododia={row['idperiododia']}")

    climas = [
        {
            "idestadoclima": 1,
            "condicionclima": "Despejado",
            "temperaturaf": None,
            "sensaciontermicaf": None,
            "humedadporcentaje": None,
            "presionpulgadas": None,
            "visibilidadmillas": None,
            "velocidadvientomph": None,
            "direccionviento": None,
            "precipitacionpulgadas": None,
            "activo": True,
            "fecha_actualizacion": now,
        },
        {
            "idestadoclima": 2,
            "condicionclima": "Lluvia",
            "temperaturaf": None,
            "sensaciontermicaf": None,
            "humedadporcentaje": None,
            "presionpulgadas": None,
            "visibilidadmillas": None,
            "velocidadvientomph": None,
            "direccionviento": None,
            "precipitacionpulgadas": None,
            "activo": True,
            "fecha_actualizacion": now + 1,
        },
        {
            "idestadoclima": 3,
            "condicionclima": "Niebla",
            "temperaturaf": None,
            "sensaciontermicaf": None,
            "humedadporcentaje": None,
            "presionpulgadas": None,
            "visibilidadmillas": None,
            "velocidadvientomph": None,
            "direccionviento": None,
            "precipitacionpulgadas": None,
            "activo": True,
            "fecha_actualizacion": now + 2,
        },
    ]
    for row in climas:
        writer.publish("Dim_EstadosClimas_topic", row)
        print(f"published Dim_EstadosClimas idestadoclima={row['idestadoclima']}")

    fisicos = [
        {
            "idelementofisico": 1,
            "elementofisico": "Semáforo",
            "activo": True,
            "fecha_actualizacion": now,
        },
        {
            "idelementofisico": 2,
            "elementofisico": "Señal de Pare",
            "activo": True,
            "fecha_actualizacion": now + 1,
        },
        {
            "idelementofisico": 3,
            "elementofisico": "Reductor",
            "activo": True,
            "fecha_actualizacion": now + 2,
        },
        {
            "idelementofisico": 4,
            "elementofisico": "Paso peatonal",
            "activo": True,
            "fecha_actualizacion": now + 3,
        },
    ]
    for row in fisicos:
        writer.publish("Dim_Elementos_Fisicos_topic", row)
        print(f"published Dim_Elementos_Fisicos idelementofisico={row['idelementofisico']}")

    estados = []
    next_id = 1
    for estadosobriedad in (True, False):
        for nivelatencion in (True, False):
            for condicionfisica in (True, False):
                for usoseguridad in (True, False):
                    estados.append(
                        {
                            "idestadoconductor": next_id,
                            "estadosobriedad": estadosobriedad,
                            "nivelatencion": nivelatencion,
                            "condicionfisica": condicionfisica,
                            "usoseguridad": usoseguridad,
                            "activo": True,
                            "fecha_actualizacion": now + next_id,
                        }
                    )
                    next_id += 1
    for row in estados:
        writer.publish("Dim_Estado_Conductor_topic", row)
        print(f"published Dim_Estado_Conductor idestadoconductor={row['idestadoconductor']}")

    print("OK — catálogos enriquecimiento publicados")
    print(
        "Nota infra: topic Dim_Implicado_topic ya registrado en "
        "settings.KAFKA_TOPICS['implicado'] (RF-EVI-010). "
        "Asegurar tabla Pinot Dim_Implicado en el entorno."
    )


if __name__ == "__main__":
    main()
