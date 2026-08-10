"""Alinea el vinculo factura-disputa entre Suscripciones y Soporte.

Dos cambios, decididos el 2026-08-08 al especificar Partners y API:

1. `Fact_Factura` += `tipo` (STRING: 'suscripcion' | 'excedente_api').
   RF-O54.3 exige verificar que no exista ya una factura de excedente para el
   mismo partner y periodo antes de emitir. Sin un discriminador esa consulta
   es imposible, y un reintento sobre un proceso que si llego a emitir
   generaria un DOBLE COBRO. El defaultNullValue es 'suscripcion' porque el
   codigo de facturacion actual no escribe la columna y todas sus facturas son
   de suscripcion: asi sigue siendo correcto sin tocarlo.

2. `Fact_Reclamo.idfactura` INT -> STRING.
   `Fact_Factura.id_factura` es un UUID (`str(uuid.uuid4())` en
   `factura_repository.py`), asi que el vinculo implementado en la auditoria de
   Soporte (decisiones-pendientes #14) nunca podria enlazar: los tipos no
   coinciden. Un UUID no cabe en un INT.

RIESGO Y COMO SE MITIGA
-----------------------
Pinot no permite cambiar el tipo de una columna: hay que recrear la tabla. Y
`Fact_Reclamo_topic` esta PURGADO (offset inicio == offset final), de modo que
sus filas viven SOLO en Pinot: recrear la tabla sin mas las perderia. Por eso
este script exporta las filas antes de tocar nada, y las vuelve a publicar
despues. Si la exportacion falla, aborta sin modificar nada.

`Fact_Factura` estaba vacia, asi que su recreacion no arrastra datos.

Los `idfactura` existentes valen -2147483648 (centinela INT de Pinot, es decir
"sin factura vinculada") y se convierten a "" (centinela STRING equivalente).

Uso:
    python database/migra_factura_reclamo.py --dry-run
    python database/migra_factura_reclamo.py
"""
import argparse
import datetime
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
RESPALDOS = RAIZ / "_respaldos"

CENTINELA_INT = -2147483648   # Integer.MIN_VALUE: "sin factura" en el esquema viejo
CENTINELA_STR = ""            # equivalente en el esquema nuevo


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


def publish(topic, registros):
    if not registros:
        return
    payload = "\n".join(json.dumps(r) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=payload.encode(), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")


def recrear(nombre, esquema, tabla):
    """Borra y recrea. Reintenta el POST mientras la external view siga viva."""
    existentes = set(json.load(urllib.request.urlopen(f"{CONTROLLER}/tables", timeout=20))["tables"])
    if nombre in existentes:
        code, cuerpo = pedir("DELETE", f"{CONTROLLER}/tables/{nombre}")
        print(f"    borrar tabla   -> {code}")
        if code >= 400:
            raise RuntimeError(cuerpo[:300])
        pedir("DELETE", f"{CONTROLLER}/schemas/{nombre}")

    code, cuerpo = pedir("POST", f"{CONTROLLER}/schemas", esquema)
    print(f"    crear esquema  -> {code}")
    if code >= 400:
        raise RuntimeError(cuerpo[:300])

    for intento in range(1, 13):
        code, cuerpo = pedir("POST", f"{CONTROLLER}/tables", tabla)
        if code < 400:
            print(f"    crear tabla    -> {code}")
            return
        if code == 409 and "External view" in cuerpo:
            print(f"    crear tabla    -> 409 external view viva, reintento {intento}/12 en 5s")
            time.sleep(5)
            continue
        raise RuntimeError(cuerpo[:300])
    raise RuntimeError(f"external view de {nombre} no se limpio tras 60s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # --- 1. Exportar Fact_Reclamo ANTES de tocar nada ------------------------
    print("1) Respaldo de Fact_Reclamo (su topic Kafka esta purgado: es la unica copia)")
    filas = query("SELECT * FROM Fact_Reclamo LIMIT 100000")
    print(f"   {len(filas)} filas leidas de Pinot")

    RESPALDOS.mkdir(exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RESPALDOS / f"Fact_Reclamo_{marca}.json"
    destino.write_text(json.dumps(filas, indent=2, ensure_ascii=False), encoding="utf-8")
    releido = json.loads(destino.read_text(encoding="utf-8"))
    if len(releido) != len(filas):
        print("   ABORTADO: el respaldo no se pudo releer intacto.")
        return 1
    print(f"   respaldo verificado -> {destino.relative_to(RAIZ.parent)}")

    con_factura = [f for f in filas if f.get("idfactura") not in (CENTINELA_INT, None)]
    print(f"   filas con factura vinculada real: {len(con_factura)}")

    # --- 2. Convertir --------------------------------------------------------
    convertidas = []
    for f in filas:
        nueva = dict(f)
        viejo = f.get("idfactura")
        nueva["idfactura"] = CENTINELA_STR if viejo in (CENTINELA_INT, None) else str(viejo)
        convertidas.append(nueva)

    # --- 3. Esquemas ---------------------------------------------------------
    ruta_esq = RAIZ / "esquemas.json"
    ruta_tab = RAIZ / "tablas.json"
    esquemas = json.loads(ruta_esq.read_text(encoding="utf-8"))
    tablas = {t["tableName"]: t for t in json.loads(ruta_tab.read_text(encoding="utf-8"))}
    por_nombre = {e["schemaName"]: e for e in esquemas}
    cambios = []

    # 3a. Fact_Factura += tipo
    factura = por_nombre["Fact_Factura"]
    nombres = {c["name"] for g in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
               for c in factura.get(g, [])}
    if "tipo" not in nombres:
        factura["dimensionFieldSpecs"].append({
            "name": "tipo", "dataType": "STRING", "defaultNullValue": "suscripcion",
        })
        cambios.append("Fact_Factura: + tipo (STRING, default 'suscripcion')")

    # 3b. Fact_Reclamo.idfactura INT -> STRING
    reclamo = por_nombre["Fact_Reclamo"]
    for campo in reclamo["dimensionFieldSpecs"]:
        if campo["name"] == "idfactura" and campo["dataType"] != "STRING":
            campo["dataType"] = "STRING"
            campo["defaultNullValue"] = CENTINELA_STR
            cambios.append("Fact_Reclamo.idfactura: INT -> STRING (default '')")

    if not cambios:
        print("\nSin cambios: el esquema ya esta al dia.")
        return 0

    print("\n2) Cambios de esquema:")
    for c in cambios:
        print(f"   - {c}")

    if args.dry_run:
        print("\n--dry-run: no se escribio ni se desplego nada.")
        print(f"(el respaldo si se creo: {destino.name})")
        return 0

    ruta_esq.write_text(json.dumps(esquemas, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"   escrito {ruta_esq.name}")

    # --- 4. Redesplegar ------------------------------------------------------
    print("\n3) Redespliegue en Pinot")
    for nombre in ("Fact_Factura", "Fact_Reclamo"):
        print(f"  --- {nombre}")
        recrear(nombre, por_nombre[nombre], tablas[nombre])

    # --- 5. Republicar -------------------------------------------------------
    print(f"\n4) Republicando {len(convertidas)} filas en Fact_Reclamo_topic")
    publish("Fact_Reclamo_topic", convertidas)

    limite = time.time() + 90
    vistas = 0
    while time.time() < limite:
        try:
            vistas = query("SELECT COUNT(*) FROM Fact_Reclamo")[0] if False else \
                len(query("SELECT id_reclamo FROM Fact_Reclamo LIMIT 100000"))
        except Exception:
            vistas = 0
        if vistas >= len(convertidas):
            break
        time.sleep(3)

    print(f"   filas en Pinot: {vistas} / {len(convertidas)} esperadas")
    if vistas < len(convertidas):
        print(f"   ATENCION: faltan filas. Respaldo intacto en {destino}")
        return 1

    print("\nMigracion completa.")
    print("Verifica con: python database/verifica_factura_reclamo.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
