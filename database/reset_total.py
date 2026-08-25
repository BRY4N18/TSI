"""
Limpieza total: deja las 79 tablas de Pinot vacias y devuelve la identidad.

**Por que no basta con borrar filas.** Pinot con upsert no permite borrar filas:
hay que recrear la tabla. Y recrearla TAMPOCO basta — al recrearse re-consume el
topic Kafka desde el principio (`auto.offset.reset: smallest`) y todo reaparece.
El orden correcto es: purgar el topic, borrar tabla y esquema, recrear. Este
script hace las tres cosas para las 79 tablas.

**La identidad sobrevive al borrado.** Se vuelca `Dim_Usuarios`, `Dim_Rol` y
`Dim_Usuario_Rol` a disco ANTES de purgar, y se republican despues con los
mismos ids: el borrado es total pero las credenciales de acceso siguen siendo
las mismas. `Fact_Session` NO se restaura — una sesion vieja apuntando a datos
que ya no existen solo genera 401 confusos; se vuelve a iniciar sesion.

Uso:
    python database/reset_total.py --dry-run     # que haria, sin tocar nada
    python database/reset_total.py               # ejecuta
"""
from __future__ import annotations

import argparse
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

# Tablas cuyo contenido se restaura tras el borrado, para no perder el acceso.
# `Dim_Credencial` es imprescindible y se olvido en la primera version: el hash
# de la contrasena vive ahi, no en `Dim_Usuarios`. Sin ella los usuarios existen
# pero el login devuelve 401.
IDENTIDAD = ["Dim_Usuarios", "Dim_Rol", "Dim_Usuario_Rol", "Dim_Credencial"]

VOLCADO = RAIZ / "_respaldos" / "identidad_reset.json"


def pedir(metodo: str, url: str, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    if datos:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def consulta(sql: str):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def contar(tabla: str) -> int:
    try:
        d = consulta(f"SELECT count(*) FROM {tabla}")
        return int(d["resultTable"]["rows"][0][0])
    except Exception:  # noqa: BLE001
        return -1


def volcar_identidad() -> dict:
    """Lee las tablas de identidad enteras antes de purgarlas."""
    fuera = {}
    for tabla in IDENTIDAD:
        d = consulta(f"SELECT * FROM {tabla} LIMIT 100000")
        rt = d.get("resultTable")
        if not rt:
            fuera[tabla] = []
            continue
        cols = rt["dataSchema"]["columnNames"]
        fuera[tabla] = [dict(zip(cols, fila)) for fila in rt["rows"]]
        print(f"   {tabla:24} {len(fuera[tabla])} filas volcadas")
    VOLCADO.parent.mkdir(parents=True, exist_ok=True)
    VOLCADO.write_text(json.dumps(fuera, ensure_ascii=False), encoding="utf-8")
    return fuera


def publicar(topic: str, registros: list[dict]) -> None:
    if not registros:
        return
    carga = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=carga.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"fallo publicando en {topic}: {proc.stderr.decode()[:300]}")


def purgar_topics(tablas: list[str]) -> None:
    particiones = [{"topic": f"{t}_topic", "partition": 0, "offset": -1} for t in tablas]
    plan = json.dumps({"partitions": particiones, "version": 1})
    subprocess.run(
        ["docker", "exec", "-i", "kafka", "sh", "-c", "cat > /tmp/reset_total.json"],
        input=plan.encode(), capture_output=True,
    )
    proc = subprocess.run(
        ["docker", "exec", "kafka", "kafka-delete-records",
         "--bootstrap-server", "localhost:9092",
         "--offset-json-file", "/tmp/reset_total.json"],
        capture_output=True,
    )
    ok = sum(1 for l in proc.stdout.decode().splitlines() if "partition:" in l)
    print(f"   {ok} particiones purgadas")
    if proc.returncode != 0:
        print(f"   aviso: {proc.stderr.decode()[:200]}")


def recrear(nombre: str, esquema: dict, tabla: dict) -> bool:
    existentes = set(json.load(urllib.request.urlopen(f"{CONTROLLER}/tables", timeout=30))["tables"])
    if nombre in existentes:
        code, _ = pedir("DELETE", f"{CONTROLLER}/tables/{nombre}")
        if code >= 400:
            print(f"   {nombre}: no se pudo borrar ({code})")
            return False
        pedir("DELETE", f"{CONTROLLER}/schemas/{nombre}")
    pedir("POST", f"{CONTROLLER}/schemas", esquema)
    # La external view sigue viva unos segundos tras el DELETE y recrear da 409.
    for _ in range(15):
        code, cuerpo = pedir("POST", f"{CONTROLLER}/tables", tabla)
        if code < 400:
            return True
        if code == 409 and "External view" in cuerpo:
            time.sleep(4)
            continue
        print(f"   {nombre}: no se pudo crear ({code}) {cuerpo[:160]}")
        return False
    print(f"   {nombre}: la external view no se limpio")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    esquemas = {e["schemaName"]: e for e in
                json.loads((RAIZ / "esquemas.json").read_text(encoding="utf-8"))}
    tablas = {t["tableName"]: t for t in
              json.loads((RAIZ / "tablas.json").read_text(encoding="utf-8"))}
    nombres = sorted(set(esquemas) & set(tablas))

    faltan = sorted((set(esquemas) | set(tablas)) - set(nombres))
    if faltan:
        print(f"AVISO: sin par esquema/tabla, se ignoran: {faltan}")

    print(f"Tablas a vaciar: {len(nombres)}")
    if args.dry_run:
        total = sum(max(contar(n), 0) for n in nombres)
        print(f"Filas que se perderian: {total:,}")
        print(f"Identidad que se restauraria: {', '.join(IDENTIDAD)}")
        return 0

    print("\n1) Volcando identidad")
    identidad = volcar_identidad()
    print(f"   respaldo en {VOLCADO}")

    print("\n2) Purgando topics Kafka")
    purgar_topics(nombres)

    print("\n3) Recreando tablas")
    fallos = []
    for i, nombre in enumerate(nombres, 1):
        if recrear(nombre, esquemas[nombre], tablas[nombre]):
            print(f"   [{i:2}/{len(nombres)}] {nombre}")
        else:
            fallos.append(nombre)
    if fallos:
        print(f"\nFallaron: {fallos}")
        return 1

    print("\n4) Restaurando identidad")
    time.sleep(8)
    for tabla, filas in identidad.items():
        publicar(f"{tabla}_topic", filas)
        print(f"   {tabla:24} {len(filas)} filas republicadas")

    print("\n5) Esperando ingesta (~20s)")
    time.sleep(20)
    vacias = con_datos = 0
    for nombre in nombres:
        n = contar(nombre)
        if nombre in IDENTIDAD:
            con_datos += 1
            print(f"   {nombre:32} {n}  (identidad)")
        elif n > 0:
            print(f"   {nombre:32} {n}  <-- deberia estar vacia")
        else:
            vacias += 1
    print(f"\nVacias: {vacias}/{len(nombres) - len(IDENTIDAD)}   Identidad restaurada: {con_datos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
