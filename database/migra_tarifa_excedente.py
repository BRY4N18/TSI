"""Anade la tarifa de excedente al catalogo de planes (CU-O54 / RF-O54.1).

Por que hace falta
------------------
RF-O54.1 exige "calcular el importe del consumo segun la tarifa vigente del
plan", pero `Dim_Plan` no tenia donde guardarla: su columna `precio` es el
importe de la SUSCRIPCION mensual, no el precio unitario del excedente. Sin
este dato, CU-O54 no puede calcular ningun importe y la linea de ingresos por
consumo de datos sigue sin ser exigible.

Decision (2026-08-08, opcion A): columna `precio_excedente_llamada` (DOUBLE)
en `Dim_Plan`, configurable por el Director de Estrategia junto al resto del
plan (CU-O26 / RF-O26.1), igual que se resolvio `api_calls_minuto`. Se
descarto derivarla del precio del plan porque el excedente saldria al mismo
precio unitario que el consumo ya pagado, sin margen comercial.

Centinela -1.0 = "sin tarifa configurada"
-----------------------------------------
NO se usa 0.0 como defecto. Un cero significaria "excedente gratis" y CU-O54
emitiria facturas de importe 0 sin que nadie lo note: ingreso real no cobrado
en silencio, justo lo que RN-APM-014 prohibe. Con -1.0 el corte mensual puede
distinguir "gratis" de "sin configurar" y alertar en vez de facturar mal.
Mismo criterio que `Dim_Partner.limitellamadasmes = -1`.

Valores iniciales
-----------------
Se siembra un precio unitario por encima del incluido (el consumo dentro del
cupo ya esta pagado por la suscripcion; el excedente no tiene descuento por
volumen), redondeado a cifras comerciales. Son valores INICIALES: el Director
de Estrategia los reconfigura desde el formulario de plan.

Riesgo
------
`Dim_Plan` tiene 5 filas reales, pero `Dim_Plan_topic` conserva sus mensajes
(offset inicio 0), asi que recrear la tabla los re-ingiere. Aun asi se exporta
y se relee el respaldo antes de tocar nada.

Uso:
    python database/migra_tarifa_excedente.py --dry-run
    python database/migra_tarifa_excedente.py
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

SIN_TARIFA = -1.0  # centinela: "sin tarifa configurada" (nunca 0.0)

# La tarifa inicial se deriva del precio unitario REAL de cada plan
# (precio / api_calls_mes), no de su nivel. Derivarla del nivel daba resultados
# absurdos en planes cuyo cupo no encaja con su nivel: "Magnifico" es nivel
# Empresarial con solo 100 llamadas/mes, asi que por nivel le tocaba $0.005
# cuando su consumo incluido cuesta $1.20 por llamada — el excedente saldria
# 240 veces mas barato que el cupo, y al partner le convendria pasarse.
RECARGO = 1.25          # el excedente no tiene el descuento por volumen del cupo
TARIFA_DEFECTO = 0.06   # solo si el plan no permite calcular el unitario


def tarifa_inicial(plan):
    """Precio unitario del excedente, siempre por encima del incluido."""
    try:
        incluido = plan["precio"] / json.loads(plan["limites"])["api_calls_mes"]
    except (KeyError, TypeError, ZeroDivisionError, json.JSONDecodeError):
        return TARIFA_DEFECTO, None
    bruta = incluido * RECARGO
    # Redondeo a una cifra comercial legible, conservando la magnitud.
    if bruta >= 1:
        tarifa = round(bruta, 2)
    elif bruta >= 0.01:
        tarifa = round(bruta, 2)
    else:
        tarifa = round(bruta, 4)
    # Nunca por debajo del incluido, pase lo que pase con el redondeo.
    if tarifa <= incluido:
        tarifa = round(incluido * RECARGO, 5)
    return tarifa, incluido

COLUMNA = {
    "name": "precio_excedente_llamada",
    "dataType": "DOUBLE",
    "defaultNullValue": SIN_TARIFA,
}


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
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=payload.encode("utf-8"), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando: {proc.stderr.decode()}")
    print(f"   publicados {len(registros)} registros en {topic}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ahora = int(time.time() * 1000)

    # --- 1. Respaldo -------------------------------------------------------
    print("1) Respaldo de Dim_Plan")
    planes = query("SELECT * FROM Dim_Plan LIMIT 1000")
    RESPALDOS.mkdir(exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RESPALDOS / f"Dim_Plan_tarifa_{marca}.json"
    destino.write_text(json.dumps(planes, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(json.loads(destino.read_text(encoding="utf-8"))) != len(planes):
        print("   ABORTADO: el respaldo no se pudo releer intacto.")
        return 1
    print(f"   {len(planes)} planes respaldados -> {destino.name}")

    # --- 2. Esquema --------------------------------------------------------
    print("\n2) Columna precio_excedente_llamada en el esquema")
    ruta_esq = RAIZ / "esquemas.json"
    esquemas = json.loads(ruta_esq.read_text(encoding="utf-8"))
    plan_esq = next(e for e in esquemas if e["schemaName"] == "Dim_Plan")
    existentes = {
        c["name"]
        for g in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
        for c in plan_esq.get(g, [])
    }
    hay_cambio_esquema = COLUMNA["name"] not in existentes
    if hay_cambio_esquema:
        plan_esq.setdefault("metricFieldSpecs", []).append(COLUMNA)
        print(f"   + {COLUMNA['name']} (DOUBLE, defaultNullValue={SIN_TARIFA})")
    else:
        print("   ya existe")

    # --- 3. Valores --------------------------------------------------------
    print("\n3) Tarifa inicial por plan")
    a_publicar = []
    for plan in planes:
        actual = plan.get("precio_excedente_llamada")
        if actual is not None and actual != SIN_TARIFA:
            print(f"   {plan['nombre'][:22]:<24} ya tiene tarifa ({actual})")
            continue
        tarifa, incluido = tarifa_inicial(plan)
        nuevo = dict(plan)
        nuevo["precio_excedente_llamada"] = tarifa
        nuevo["fecha_actualizacion"] = ahora
        a_publicar.append(nuevo)
        if incluido is None:
            detalle = "(sin unitario calculable, se usa el defecto)"
        else:
            detalle = f"(incluido ${incluido:.5f}, x{tarifa / incluido:.2f})"
        print(f"   {plan['nombre'][:22]:<24} -> ${tarifa}/llamada {detalle}")

    if not hay_cambio_esquema and not a_publicar:
        print("\nSin cambios: todo esta al dia.")
        return 0

    if args.dry_run:
        print("\n--dry-run: no se escribio ni se desplego nada.")
        return 0

    ruta_esq.write_text(json.dumps(esquemas, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n   escrito {ruta_esq.name}")

    # --- 4. Recrear la tabla ------------------------------------------------
    # Pinot no admite anadir una columna en caliente de forma fiable sobre una
    # tabla REALTIME con upsert. Se recrea: el topic conserva los mensajes
    # (offset inicio 0), asi que los planes se re-ingieren solos.
    print("\n4) Recreando Dim_Plan")
    tablas = {t["tableName"]: t for t in
              json.loads((RAIZ / "tablas.json").read_text(encoding="utf-8"))}
    code, cuerpo = pedir("DELETE", f"{CONTROLLER}/tables/Dim_Plan")
    print(f"   borrar tabla   -> {code}")
    if code >= 400:
        print(f"      {cuerpo[:300]}\n   Respaldo intacto en {destino}")
        return 1
    pedir("DELETE", f"{CONTROLLER}/schemas/Dim_Plan")
    code, cuerpo = pedir("POST", f"{CONTROLLER}/schemas", plan_esq)
    print(f"   crear esquema  -> {code}")
    if code >= 400:
        print(f"      {cuerpo[:300]}")
        return 1
    for intento in range(1, 13):
        code, cuerpo = pedir("POST", f"{CONTROLLER}/tables", tablas["Dim_Plan"])
        if code < 400:
            print(f"   crear tabla    -> {code}")
            break
        if code == 409 and "External view" in cuerpo:
            print(f"   crear tabla    -> 409 external view viva, reintento {intento}/12 en 5s")
            time.sleep(5)
            continue
        print(f"   crear tabla    -> {code} {cuerpo[:200]}")
        return 1
    else:
        print("   ABORTADO: external view no se limpio")
        return 1

    # --- 5. Publicar la tarifa ---------------------------------------------
    print("\n5) Publicando la tarifa")
    publish("Dim_Plan_topic", a_publicar)

    # --- 6. Verificar -------------------------------------------------------
    print("\n6) Verificando")
    limite = time.time() + 90
    filas = []
    while time.time() < limite:
        try:
            filas = query("SELECT idplan, nombre, precio_excedente_llamada FROM Dim_Plan LIMIT 1000")
        except Exception:
            filas = []
        if len(filas) >= len(planes) and all(
            f.get("precio_excedente_llamada", SIN_TARIFA) != SIN_TARIFA for f in filas
        ):
            break
        time.sleep(3)

    print(f"   planes en Pinot: {len(filas)} / {len(planes)} esperados")
    sin = [f["nombre"] for f in filas if f.get("precio_excedente_llamada", SIN_TARIFA) == SIN_TARIFA]
    if len(filas) < len(planes) or sin:
        print(f"   ATENCION: incompleto. Sin tarifa: {sin}. Respaldo en {destino}")
        return 1
    for f in sorted(filas, key=lambda x: x["idplan"]):
        print(f"   {f['nombre'][:22]:<24} ${f['precio_excedente_llamada']}/llamada")

    print("\nMigracion completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
