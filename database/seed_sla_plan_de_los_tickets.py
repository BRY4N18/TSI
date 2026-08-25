"""
Siembra Dim_SLAConfig para el plan que realmente tienen los tickets demo.

**Por qué existe este script.** `seed_soporte.py` fija `ID_PLAN = 1` y publica
todas sus configuraciones de SLA contra ese plan, pero la suscripción del
cliente demo acaba en el plan 2 (la siembra de planes/suscripciones corre
después y lo reasigna). Resultado: los 14 tickets salen con `idplan = 2` y
ninguna configuración cruza, así que **todos** quedan con
`motivo_sin_compromiso = 'sin_config'` y el informe de cumplimiento de SLA
devuelve `pct_cumplimiento = null` para siempre. No es que falten datos: es que
los dos seeds no se hablan.

Este script publica las mismas cinco reglas contra el plan de los tickets, con
ids que no colisionan con las de `seed_soporte.py`.

Uso:
    python database/seed_sla_plan_de_los_tickets.py [--idplan 2]

Requiere el contenedor `kafka` en ejecución (único canal de escritura → Pinot).
El informe táctico lee de ClickHouse, así que además hace falta que corra el DAG
de Airflow para que estas filas lleguen al almacén.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time

NOW_MS = int(time.time() * 1000)
DAY = 86_400_000

# Mismas combinaciones tipo/prioridad que `seed_soporte.py`, para que los
# tickets ya sembrados encuentren compromiso. Ids desde 101 para no pisar las
# de aquel script (1-5).
REGLAS = [
    ("tecnica", "alta", 1800, 7200),
    ("acceso", "media", 7200, 172800),
    ("consulta_funcional", "baja", 14400, 259200),
    ("emergencia_activa", "crítico", 60, 3600),
    ("Facturación", "baja", 14400, 259200),
]


def publish(topic: str, records: list[dict]) -> None:
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=payload.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit("fallo publicando en %s: %s" % (topic, proc.stderr.decode()))
    print("Publicados %d registros en %s" % (len(records), topic))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idplan", type=int, default=2,
                    help="plan de los tickets demo (por defecto 2)")
    args = ap.parse_args()

    configs = [
        {
            "idslaconfig": 101 + i,
            "idplan": args.idplan,
            "tipoincidencia": tipo,
            "prioridad": prioridad,
            "activo": True,
            "tiemporespuestamax": resp,
            "tiemporesolucionmax": reso,
            "fechavigenciadesde": NOW_MS - 60 * DAY,
            "fechavigenciahasta": None,
            "fecha_actualizacion": NOW_MS,
        }
        for i, (tipo, prioridad, resp, reso) in enumerate(REGLAS)
    ]
    publish("Dim_SLAConfig_topic", configs)
    print("\nListo. Estas reglas cubren el plan %d." % args.idplan)
    print("El informe tactico lee de ClickHouse: hasta que corra el DAG de")
    print("Airflow, el cumplimiento seguira mostrandose como 'sin dato'.")


if __name__ == "__main__":
    main()
