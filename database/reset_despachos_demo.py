"""
Libera los despachos activos del entorno demo y devuelve las unidades a "Activa".

Cada corrida del flujo end-to-end (o de una demo en vivo) deja despachos activos
en `Fact_Despacho` y unidades en `Ocupada`/`En Misión`. Con una flota de 2-3
unidades eso agota rápido las candidatas disponibles: `unidades-candidatas`
devuelve 0 y todo accidente nuevo va a escalamiento de zona en vez de poder
demostrar la asignación normal.

Este script no reemplaza un cierre de caso real (no toca `Fact_Accidente` ni
`Fact_AccidenteTipoEstadoAccidente`): solo resetea el estado operativo de la
flota para poder seguir demostrando el despacho. Para cerrar el caso de verdad,
usar el flujo normal (CU-O28 cierre / CU-O42 cancelación).

Idempotente: si no hay nada que liberar, no escribe nada.

Uso:
    python database/reset_despachos_demo.py --dry-run
    python database/reset_despachos_demo.py
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)

ESTADO_ACTIVA = "Activa"


def query(sql):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"},
    )
    d = json.load(urllib.request.urlopen(req, timeout=30))
    if d.get("exceptions"):
        raise RuntimeError(f"Pinot: {d['exceptions']}")
    rt = d.get("resultTable")
    if not rt:
        return []
    return [dict(zip(rt["dataSchema"]["columnNames"], r)) for r in rt["rows"]]


def publish(topic, records):
    if not records:
        return
    payload = "\n".join(json.dumps(r) for r in records)
    proc = subprocess.run(
        [
            "docker", "exec", "-i", "kafka",
            "kafka-console-producer", "--bootstrap-server", "localhost:9092",
            "--topic", topic,
        ],
        input=payload.encode(),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"  -> publicados {len(records)} registros en {topic}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    despachos_activos = [d for d in query("SELECT * FROM Fact_Despacho LIMIT 10000") if d.get("activo")]
    unidades_ids = sorted({int(d["idunidademergencia"]) for d in despachos_activos})

    print(f"Despachos activos: {len(despachos_activos)}")
    for d in despachos_activos:
        print(f"  - iddespacho={d['iddespacho']} idaccidente={d['idaccidente']} "
              f"idunidademergencia={d['idunidademergencia']}")

    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return 0

    if not despachos_activos:
        print("Nada que liberar.")
        return 0

    publish(
        "Fact_Despacho_topic",
        [{**d, "activo": False, "fecha_actualizacion": NOW_MS} for d in despachos_activos],
    )

    maximo = query(
        "SELECT MAX(idhistorialestadosunidadesemergencias) AS max_id FROM Fact_HistorialEstadoUnidad"
    )
    siguiente = int((maximo[0].get("max_id") or 0)) + 1
    historial = query("SELECT * FROM Fact_HistorialEstadoUnidad LIMIT 10000")
    estados_actuales = {}
    for r in sorted(historial, key=lambda r: r.get("fechahora", 0)):
        estados_actuales[int(r["idunidademergencia"])] = r.get("estadonuevo")

    eventos = []
    for offset, uid in enumerate(unidades_ids):
        eventos.append({
            "idhistorialestadosunidadesemergencias": siguiente + offset,
            "idunidademergencia": uid,
            "idestadounidademergencia": 1,
            "estadoanterior": estados_actuales.get(uid, ESTADO_ACTIVA),
            "estadonuevo": ESTADO_ACTIVA,
            "idusuario": None,
            "fechahora": NOW_MS,
            "fecha_actualizacion": NOW_MS,
            "activo": True,
        })
    publish("Fact_HistorialEstadoUnidad_topic", eventos)

    print(f"\nLiberados {len(despachos_activos)} despachos, "
          f"{len(unidades_ids)} unidades vueltas a {ESTADO_ACTIVA!r}.")
    print("Pinot tarda unos segundos en reflejar los cambios (ingesta Kafka).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
