"""Siembra Dim_EstadoIntegracion (T006 de api-monitoring-and-billing).

Que es esta tabla
-----------------
NO es "el estado actual del partner". Es el catalogo de la **foto congelada**
que `Fact_APIIntegracion.idestadointegracion` guarda en cada llamada: en que
estado estaba el partner en el instante en que se atendio esa peticion
(RN-APM-006). Por eso refleja los estados derivados de
`partner-api-onboarding` § 9 y no condiciones de consumo.

Lo que NO va aqui, y por que
----------------------------
Se evaluo sembrar estados de consumo (cuota al 80%, cuota superada, rate
limited, suspendido por mora). No corresponden a esta tabla:

  - "Cuota al 80% / superada" se **deriva al consultar**, no se acumula al
    escribir (RN-APM-003). Congelarlo por llamada seria incorrecto y caro.
  - "Rate limited" es inalcanzable: un 429 **no genera fila** en
    `Fact_APIIntegracion` (§ 15 D2). Se registra en `Fact_LogLlamadaAPI`.
  - "Suspendido por mora" y "Dado de baja" pertenecen a
    `partner-access-management` (#09), no a este modulo.

Esa taxonomia si es util, pero como **presentacion derivada** en la consola de
consumo, no como catalogo en base.

Idempotente: no reescribe los estados que ya existan.

Uso:
    python database/seed_estado_integracion.py --dry-run
    python database/seed_estado_integracion.py
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"
TOPIC = "Dim_EstadoIntegracion_topic"

ESTADOS = [
    (
        1,
        "Pruebas activo",
        "La llamada se atendio con una credencial de Sandbox",
    ),
    (
        2,
        "Producción activa",
        "La llamada se atendio con una credencial de Producción",
    ),
    (
        3,
        "Suspendido",
        "El partner estaba suspendido. Ver nota de alcanzabilidad en el spec",
    ),
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
    print(f"   publicados {len(registros)} estados en {TOPIC}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ahora = int(time.time() * 1000)

    existentes = {
        int(f["idestadointegracion"])
        for f in query("SELECT idestadointegracion FROM Dim_EstadoIntegracion LIMIT 100")
    }
    print(f"Estados ya sembrados: {len(existentes)}")

    a_publicar = []
    for idestado, nombre, descripcion in ESTADOS:
        if idestado in existentes:
            print(f"   {nombre:<20} ya existe")
            continue
        a_publicar.append({
            "idestadointegracion": idestado,
            "nombre": nombre,
            "descripcion": descripcion,
            "activo": True,
            "fecha_actualizacion": ahora,
        })
        print(f"   {nombre:<20} -> se sembrara")

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
        if len(query("SELECT idestadointegracion FROM Dim_EstadoIntegracion LIMIT 100")) >= esperados:
            print("\nSiembra completa.")
            return 0
        time.sleep(3)
    print("\nATENCION: la ingesta no se completo en 60 s.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
