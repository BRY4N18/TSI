"""Siembra Dim_VersionContratoAPI: una version vigente por servicio (CU-O50).

El versionado es POR SERVICIO. `Dim_Servicio` contiene varios (API Despacho,
API Registro de accidentes, Portal Cliente) y cada uno lleva su propio ciclo:
sin la FK `id_servicio`, los tres colapsarian en una sola linea temporal.

Idempotente: solo siembra los servicios que aun no tienen version.

Uso:
    python database/seed_versiones_contrato.py --dry-run
    python database/seed_versiones_contrato.py
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"
TOPIC = "Dim_VersionContratoAPI_topic"

VERSION_INICIAL = "v1"
SIN_URL = ""
SIN_FECHA_RETIRO = 0  # centinela: sin fecha de retiro planificada (RN-PON-012)


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


def publish(registros):
    if not registros:
        return
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", TOPIC],
        input=payload.encode("utf-8"), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando: {proc.stderr.decode()}")
    print(f"   publicados {len(registros)} registros en {TOPIC}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ahora = int(time.time() * 1000)

    # Solo los servicios de tipo 'api': la tabla versiona CONTRATOS DE API, que
    # es lo que un partner integra. El Portal Cliente es una interfaz web sin
    # contrato publicado, y darle una "v1 vigente" inventaria un compromiso de
    # compatibilidad que nadie asumio (RN-PON-012).
    servicios = query(
        "SELECT id_servicio, nombre, tipo FROM Dim_Servicio "
        "WHERE tipo = 'api' AND activo = true LIMIT 100"
    )
    if not servicios:
        print("No hay servicios en Dim_Servicio. Ejecuta antes "
              "backend/scripts/seed_catalogos_soporte.py")
        return 1

    existentes = query(
        "SELECT idversion, id_servicio, version FROM Dim_VersionContratoAPI LIMIT 1000"
    )
    ya_versionados = {v["id_servicio"] for v in existentes}
    siguiente_id = max((v["idversion"] for v in existentes), default=0) + 1

    print(f"Servicios: {len(servicios)} | ya versionados: {len(ya_versionados)}")
    a_publicar = []
    for servicio in servicios:
        sid = servicio["id_servicio"]
        if sid in ya_versionados:
            print(f"   {servicio['nombre'][:28]:<30} ya tiene version")
            continue
        a_publicar.append(
            {
                "idversion": siguiente_id,
                "id_servicio": sid,
                "version": VERSION_INICIAL,
                "estado": "vigente",
                "spec_url": SIN_URL,
                "fecha_publicacion": ahora,
                "fecha_retiro": SIN_FECHA_RETIRO,
                "activo": True,
                "fecha_actualizacion": ahora,
            }
        )
        print(f"   {servicio['nombre'][:28]:<30} -> {VERSION_INICIAL} vigente")
        siguiente_id += 1

    if not a_publicar:
        print("\nSin cambios: todos los servicios tienen version.")
        return 0
    if args.dry_run:
        print(f"\n--dry-run: no se publico nada ({len(a_publicar)} pendientes)")
        return 0

    publish(a_publicar)

    limite = time.time() + 60
    while time.time() < limite:
        if len(query("SELECT idversion FROM Dim_VersionContratoAPI LIMIT 1000")) >= len(
            existentes
        ) + len(a_publicar):
            print("\nSiembra completa.")
            return 0
        time.sleep(3)
    print("\nATENCION: la ingesta no se completo en 60 s.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
