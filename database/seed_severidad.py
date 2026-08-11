"""Siembra Dim_Severidad — catalogo canonico de severidad de accidentes.

Por que hacia falta
-------------------
La tabla existia en Pinot con **0 filas** y **nadie la leia**. Hasta hoy, la
severidad vivia repartida en tres sitios desconectados (verificado 2026-08-09):

  1. `Fact_Accidente.idseveridad` — un entero suelto, validado solo por
     `enum: [1,2,3,4]` en el contrato OpenAPI de Emergencias.
  2. `frontend/src/app/modules/accidentes/severidad.constants.ts` — las
     etiquetas, **hardcodeadas en el cliente**.
  3. `apps/suscripciones/services/catalogo_plan_service.SEVERIDADES` — un
     `frozenset({"Baja","Media","Alta"})`, **otro vocabulario distinto**.

Ningun sitio era la fuente de verdad, asi que un consumidor nuevo (el partner
de #08) no tenia de donde leerlas. Este seed convierte la tabla en el catalogo
canonico que su nombre siempre prometio.

Los valores son los de accidentes, que son los que de verdad viajan en los
datos: 1 Leve, 2 Moderado, 3 Grave, 4 Fatal.

Idempotente: solo siembra las severidades que aun no existan.

Uso:
    python database/seed_severidad.py --dry-run
    python database/seed_severidad.py
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"
TOPIC = "Dim_Severidad_topic"

# Orden de gravedad ascendente: el id ES el nivel.
SEVERIDADES = [
    (1, "Leve", "Daños materiales menores, sin heridos"),
    (2, "Moderado", "Heridos leves o daños relevantes; requiere atención"),
    (3, "Grave", "Heridos de consideración; prioridad alta de despacho"),
    (4, "Fatal", "Víctimas mortales; máxima prioridad"),
]


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
    return [dict(zip(rt["dataSchema"]["columnNames"], r)) for r in rt["rows"]] if rt else []


def publish(registros):
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", TOPIC],
        input=payload.encode("utf-8"), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando: {proc.stderr.decode()}")
    print(f"   publicadas {len(registros)} severidades en {TOPIC}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ahora = int(time.time() * 1000)

    existentes = {
        int(f["idseveridad"])
        for f in query("SELECT idseveridad FROM Dim_Severidad LIMIT 100")
    }
    print(f"Severidades ya sembradas: {len(existentes)}")

    a_publicar = []
    for idseveridad, nombre, descripcion in SEVERIDADES:
        if idseveridad in existentes:
            print(f"   {idseveridad} {nombre:<10} ya existe")
            continue
        a_publicar.append({
            "idseveridad": idseveridad,
            "severidad": nombre,
            "descripcion": descripcion,
            "activo": True,
            "fecha_actualizacion": ahora,
        })
        print(f"   {idseveridad} {nombre:<10} -> se sembrara")

    if not a_publicar:
        print("\nSin cambios: el catalogo ya esta completo.")
        return 0
    if args.dry_run:
        print(f"\n--dry-run: no se publico nada ({len(a_publicar)} pendientes)")
        return 0

    publish(a_publicar)

    limite = time.time() + 60
    esperados = len(existentes) + len(a_publicar)
    while time.time() < limite:
        if len(query("SELECT idseveridad FROM Dim_Severidad LIMIT 100")) >= esperados:
            print("\nSiembra completa.")
            return 0
        time.sleep(3)
    print("\nATENCION: la ingesta no se completo en 60 s.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
