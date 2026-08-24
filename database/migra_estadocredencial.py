"""
Unifica `Dim_Credencial.estadocredencial` al valor canónico "Activo".

Dos convenciones convivían: los seeds escribían "ACTIVA" mientras el código compara
contra "Activo" (ver `core/repositories/cuentas_clientes/credential_repository.py`).
El login no lo notaba porque solo bloquea "Inactivo", pero
`onboarding_service` exige `== "Activo"`, así que consideraba inválida la credencial
de todos los usuarios sembrados y bloqueaba su onboarding.

Los seeds ya quedaron corregidos; este script migra las filas que se escribieron antes.
Idempotente: correrlo dos veces no cambia nada.

Uso:
    python database/migra_estadocredencial.py --dry-run
    python database/migra_estadocredencial.py
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _reversion import respaldar
import time
import urllib.request

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)

CANONICO = "Activo"
# Variantes vistas en datos ya escritos que significan lo mismo.
EQUIVALENTES = {"activa", "activo"}


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

    filas = query("SELECT * FROM Dim_Credencial LIMIT 10000")

    # La fila se republica entera: sin copia previa, un error aqui enterraria
    # el estado anterior de toda la credencial, no solo del campo de estado.
    respaldo = respaldar("Dim_Credencial", filas, sufijo="estadocredencial")
    print(f"Respaldo verificado -> {respaldo.name}")

    a_migrar = [
        r for r in filas
        if str(r.get("estadocredencial") or "").strip().lower() in EQUIVALENTES
        and r.get("estadocredencial") != CANONICO
    ]

    print(f"Credenciales totales: {len(filas)}")
    print(f"A migrar a {CANONICO!r}: {len(a_migrar)}")
    for r in a_migrar:
        print(f"  - idcredencial={r['idcredencial']} idusuario={r['idusuario']} "
              f"{r['estadocredencial']!r} -> {CANONICO!r}")

    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return 0

    publish(
        "Dim_Credencial_topic",
        [{**r, "estadocredencial": CANONICO, "fecha_actualizacion": NOW_MS} for r in a_migrar],
    )
    if a_migrar:
        print("\nPinot tarda unos segundos en reflejar los cambios (ingesta Kafka).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
