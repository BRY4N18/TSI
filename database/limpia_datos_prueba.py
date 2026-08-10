"""Elimina las filas de prueba que dejan los verificadores.

Borrar filas en Pinot con upsert no es posible sin recrear la tabla, y recrearla
NO basta: Pinot re-consume el topic Kafka desde el principio
(`auto.offset.reset: smallest`) y las filas reaparecen. Hay que purgar el topic
primero y recrear despues. Este script hace las dos cosas en orden.

Solo opera sobre tablas que deben quedar VACIAS. Nunca toca Fact_Reclamo ni
Fact_Historial_Ticket, que tienen datos reales.

Uso:
    python database/limpia_datos_prueba.py
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONTROLLER = "http://localhost:9000"
BROKER = "http://localhost:8099"

# Tablas que deben terminar en 0 filas. Fact_Reclamo y Fact_Historial_Ticket
# quedan deliberadamente fuera: contienen datos reales.
A_LIMPIAR = [
    "Dim_Partner",
    "Dim_CredencialAPI",
    "Fact_HistorialAccesoPartner",
    "Dim_VersionContratoAPI",
    "Fact_Factura",
]
INTOCABLES = {"Fact_Reclamo", "Fact_Historial_Ticket"}

# Dim_VersionContratoAPI se purga junto al resto, pero NO es dato de prueba:
# es catalogo. Tras esta limpieza hay que resembrarlo o CU-O50 devuelve 404:
#     python database/seed_versiones_contrato.py


def pedir(metodo, url, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(
        url, data=datos, method=metodo,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def contar(tabla):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": f"SELECT COUNT(*) FROM {tabla}"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
        rt = d.get("resultTable")
        return rt["rows"][0][0] if rt else 0
    except Exception:
        return 0


def main():
    assert not (set(A_LIMPIAR) & INTOCABLES), "una tabla con datos reales entro en la lista"

    esquemas = {e["schemaName"]: e for e in
                json.loads((RAIZ / "esquemas.json").read_text(encoding="utf-8"))}
    tablas = {t["tableName"]: t for t in
              json.loads((RAIZ / "tablas.json").read_text(encoding="utf-8"))}

    print("1) Purgando topics Kafka")
    particiones = [{"topic": f"{t}_topic", "partition": 0, "offset": -1} for t in A_LIMPIAR]
    plan = json.dumps({"partitions": particiones, "version": 1})
    subprocess.run(["docker", "exec", "-i", "kafka", "sh", "-c",
                    "cat > /tmp/limpieza.json"], input=plan.encode(), capture_output=True)
    proc = subprocess.run(
        ["docker", "exec", "kafka", "kafka-delete-records",
         "--bootstrap-server", "localhost:9092",
         "--offset-json-file", "/tmp/limpieza.json"],
        capture_output=True,
    )
    for linea in proc.stdout.decode().splitlines():
        if "partition:" in linea:
            print(f"   {linea.strip()}")

    print("\n2) Recreando tablas")
    for nombre in A_LIMPIAR:
        existentes = set(json.load(urllib.request.urlopen(f"{CONTROLLER}/tables", timeout=20))["tables"])
        if nombre in existentes:
            code, _ = pedir("DELETE", f"{CONTROLLER}/tables/{nombre}")
            if code >= 400:
                print(f"   {nombre}: error al borrar ({code})")
                return 1
            pedir("DELETE", f"{CONTROLLER}/schemas/{nombre}")
        pedir("POST", f"{CONTROLLER}/schemas", esquemas[nombre])
        for _ in range(12):
            code, cuerpo = pedir("POST", f"{CONTROLLER}/tables", tablas[nombre])
            if code < 400:
                break
            if code == 409 and "External view" in cuerpo:
                time.sleep(5)
                continue
            print(f"   {nombre}: error al crear ({code}) {cuerpo[:200]}")
            return 1
        else:
            print(f"   {nombre}: external view no se limpio")
            return 1
        print(f"   {nombre}: recreada")

    time.sleep(6)
    print("\n3) Recuento final")
    fallos = []
    for nombre in A_LIMPIAR:
        n = contar(nombre)
        print(f"   {nombre:32} {n}")
        if n:
            fallos.append(nombre)
    print("\n   datos reales (no tocados):")
    for nombre in sorted(INTOCABLES):
        print(f"   {nombre:32} {contar(nombre)}")

    if fallos:
        print(f"\nATENCION: siguen con filas: {fallos}")
        return 1
    print("\nLimpieza completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
