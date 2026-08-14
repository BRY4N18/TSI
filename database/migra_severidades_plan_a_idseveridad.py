"""Migra `severidades_desbloqueadas` de nombres propios a ids de `Dim_Severidad`.

Contexto
--------
El catalogo de planes guardaba una escala paralela — "Baja"/"Media"/"Alta" — que
no correspondia a ninguna fila de `Dim_Severidad` (Leve/Moderado/Grave/Fatal).
Convivian por un diccionario puente en `apps/partners/services/consumo_datos_service.py`.
Decision de negocio del 2026-08-11: se migra a los ids reales y el puente se borra.

Mapeo aplicado (acumulativo, igual que el puente que sustituye):

    Baja  -> [1]              Leve
    Media -> [1, 2]           + Moderado
    Alta  -> [1, 2, 3, 4]     + Grave y Fatal

"Alta" conserva a Fatal por decision explicita: ningun cliente pierde cobertura
respecto de lo que tenia contratado antes de la migracion.

Tablas afectadas
----------------
- `Dim_Plan.severidades_desbloqueadas`
- `Fact_Suscripcion.severidades_desbloqueadas` (copia congelada de lo contratado)

Ambas son upsert por clave primaria: se relee la fila completa y se republica
entera, porque publicar un registro parcial borraria el resto de columnas.

Uso (dentro del contenedor Django):
    python /app/scripts/../../database/migra_severidades_plan_a_idseveridad.py
o, mas comodo, copiando el fichero al contenedor:
    docker cp database/migra_severidades_plan_a_idseveridad.py accidentes-django:/tmp/
    docker exec accidentes-django python /tmp/migra_severidades_plan_a_idseveridad.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.environ.get("PYTHONPATH", "/app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from core.pinot.client import PinotClient  # noqa: E402
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter  # noqa: E402

MAPEO_LEGADO: dict[str, list[int]] = {
    "baja": [1],
    "media": [1, 2],
    "alta": [1, 2, 3, 4],
}

TABLAS = (
    ("Dim_Plan", "idplan", "Dim_Plan_topic"),
    ("Fact_Suscripcion", "id_suscripcion", "Fact_Suscripcion_topic"),
)


def traducir(crudo) -> list[int] | None:
    """Devuelve la lista de ids, o None si la fila no necesita migrarse."""
    if crudo in (None, "", "null"):
        return None
    try:
        valores = json.loads(crudo)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(valores, list) or not valores:
        return None
    # Ya migrada: todos los elementos son numeros.
    if all(isinstance(v, int) and not isinstance(v, bool) for v in valores):
        return None

    ids: set[int] = set()
    for v in valores:
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            ids.add(v)
        elif isinstance(v, str):
            ids.update(MAPEO_LEGADO.get(v.strip().lower(), ()))
    return sorted(ids) or None


def main() -> None:
    pinot = PinotClient()
    writer = KafkaWriter()
    total = 0

    for tabla, pk, topic in TABLAS:
        filas = pinot.query(f"SELECT * FROM {tabla} LIMIT 1000") or []
        for fila in filas:
            nuevos = traducir(fila.get("severidades_desbloqueadas"))
            if nuevos is None:
                continue
            payload = {
                **fila,
                "severidades_desbloqueadas": json.dumps(nuevos, ensure_ascii=False),
            }
            writer.publish(topic, payload)
            total += 1
            print(f"{tabla} {pk}={fila.get(pk)} -> {nuevos}")

    print(f"filas republicadas: {total}")


if __name__ == "__main__":
    main()
