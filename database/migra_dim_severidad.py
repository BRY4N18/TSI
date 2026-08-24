"""Corrige Dim_Severidad: `severidad` pasa de metrica INT a dimension STRING.

El defecto
----------
`severidad` guarda el NOMBRE de la severidad ("Leve", "Grave"...), pero estaba
declarada como **metrica INT**. Pinot descarta en silencio toda fila cuyo valor
no sea numerico: por eso la tabla llevaba 0 filas y la siembra "funcionaba" sin
escribir nada. Ni error, ni aviso.

Detectado el 2026-08-09 al sembrar el catalogo para RF-APM-002 de #08.

Por que ahora
-------------
La tabla esta **vacia**: no hay datos que migrar ni que perder. Cambiar el tipo
de una columna exige borrar y recrear la tabla, asi que este es el momento mas
barato que va a haber.

Ojo con dos efectos ya conocidos de recrear tablas en Pinot:
  - Al recrearla, **re-consume el topic Kafka desde el principio**
    (`auto.offset.reset: smallest`). Como parte de la siembra fallida publico
    mensajes invalidos, se purga el topic antes.
  - Durante unos segundos tras el DELETE la *external view* sigue viva y
    recrear devuelve 409. Se reintenta con espera.

Como se revierte
----------------
No hay datos que respaldar: la tabla esta **vacia**, que es justamente el motivo
de hacerlo ahora. La reversion es volver a poner `severidad` como metrica INT en
`esquemas.json` y recrear la tabla — lo mismo que hace este script, en sentido
contrario y con el mismo coste, que es cero.

Revertirlo devolveria el defecto: Pinot volveria a descartar en silencio toda
fila con un nombre de severidad. Se documenta para que la vuelta atras sea una
decision y no un reflejo ante el primer susto.

Uso:
    python database/migra_dim_severidad.py --dry-run
    python database/migra_dim_severidad.py
"""

import argparse
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONTROLADOR = "http://localhost:9000"
BROKER = "http://localhost:8099"
TABLA = "Dim_Severidad"
TOPIC = "Dim_Severidad_topic"


def pedir(metodo, url, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(
        url, data=datos, method=metodo, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def contar():
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": f"SELECT COUNT(*) AS n FROM {TABLA}"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
        rt = d.get("resultTable")
        return rt["rows"][0][0] if rt else 0
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    esquemas = json.loads((RAIZ / "esquemas.json").read_text(encoding="utf-8"))
    tablas = json.loads((RAIZ / "tablas.json").read_text(encoding="utf-8"))

    esquema = next(e for e in esquemas if e["schemaName"] == TABLA)
    tabla = next(t for t in tablas if t["tableName"] == TABLA)

    metricas = esquema.get("metricFieldSpecs", [])
    if not any(m["name"] == "severidad" for m in metricas):
        print("El esquema ya esta corregido. Sin cambios.")
        return 0

    filas = contar()
    print(f"Filas actuales en {TABLA}: {filas}")
    if filas:
        print("ATENCION: la tabla NO esta vacia. Aborta: habria perdida de datos.")
        return 1

    # `severidad` deja de ser metrica y pasa a dimension STRING.
    esquema["metricFieldSpecs"] = [m for m in metricas if m["name"] != "severidad"]
    if not esquema["metricFieldSpecs"]:
        esquema.pop("metricFieldSpecs")
    esquema.setdefault("dimensionFieldSpecs", []).append(
        {"name": "severidad", "dataType": "STRING", "defaultNullValue": ""}
    )

    print("\nCambio a aplicar:")
    print("  severidad: metrica INT  ->  dimension STRING (defaultNullValue '')")

    if args.dry_run:
        print("\n--dry-run: no se aplico nada.")
        return 0

    # 1. Purgar el topic: la siembra fallida dejo mensajes con el tipo viejo y
    #    al recrear la tabla se re-consumirian desde el principio.
    print("\n1) Purgando el topic")
    cfg = {"partitions": [{"topic": TOPIC, "partition": 0, "offset": -1}], "version": 1}
    ruta = "/tmp/purga_severidad.json"
    subprocess.run(
        ["docker", "exec", "kafka", "sh", "-c",
         f"echo '{json.dumps(cfg)}' > {ruta}"], check=True, capture_output=True,
    )
    subprocess.run(
        ["docker", "exec", "kafka", "kafka-delete-records",
         "--bootstrap-server", "localhost:9092", "--offset-json-file", ruta],
        capture_output=True,
    )
    print("   topic purgado")

    print("2) Borrando la tabla")
    print("   ", pedir("DELETE", f"{CONTROLADOR}/tables/{TABLA}")[0])

    # Cambiar el TIPO de una columna es incompatible hacia atras: un PUT
    # devuelve 400 «Only allow adding new columns». Con la tabla vacia, borrar y
    # recrear el esquema es seguro y es la unica via.
    print("3) Borrando y recreando el esquema (PUT no admite cambios de tipo)")
    print("    delete:", pedir("DELETE", f"{CONTROLADOR}/schemas/{TABLA}")[0])
    codigo, cuerpo = pedir("POST", f"{CONTROLADOR}/schemas", esquema)
    print("    create:", codigo, cuerpo[:120])
    if codigo not in (200, 201):
        print("    NO se pudo crear el esquema; se aborta antes de recrear la tabla")
        return 1

    print("4) Recreando la tabla")
    for intento in range(1, 11):
        codigo, cuerpo = pedir("POST", f"{CONTROLADOR}/tables", tabla)
        if codigo in (200, 201):
            print("    recreada")
            break
        # 409: la external view sigue viva unos segundos tras el DELETE.
        print(f"    intento {intento}: {codigo}, reintentando...")
        time.sleep(4)
    else:
        print("    NO se pudo recrear la tabla")
        return 1

    # 5. Persistir el esquema corregido en el repositorio.
    (RAIZ / "esquemas.json").write_text(
        json.dumps(esquemas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("5) esquemas.json actualizado")

    print("\nListo. Ahora: python database/seed_severidad.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
