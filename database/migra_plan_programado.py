"""Anade `idplan_programado` a `Fact_Suscripcion` (decision #27, RN-SUSF-006).

Por que hace falta
------------------
El SRS 3.3.1 dice dos cosas a la vez: que "una mejora de plan se autoaprueba y
aplica de inmediato", y que "todo cambio de plan aplica a partir del siguiente
ciclo de facturacion". Hasta ahora el sistema aplicaba TODO de inmediato, asi
que una reduccion aprobada a mitad de ciclo le retiraba al cliente, en el acto,
un nivel de servicio que ya habia pagado hasta el fin del periodo. Ademas la
factura del ciclo se emite con el precio que la suscripcion tenga al cerrar, de
modo que el cliente pagaba el ciclo entero al precio bajo aunque hubiera
disfrutado medio ciclo del plan alto — justo el prorrateo que la regla prohibe.

Decision (2026-08-12, opcion 1): la MEJORA sigue aplicando de inmediato; la
REDUCCION aprobada queda PROGRAMADA y la aplica el job de renovacion al recorrer
el ciclo. Es la unica lectura que no contradice ninguna de las dos frases del
SRS en el caso que perjudica al cliente.

Esta columna es donde se anota esa reduccion pendiente de aplicar.

Centinela 0 = "sin cambio programado"
-------------------------------------
Aqui 0 SI es un centinela seguro, a diferencia de `precio_excedente_llamada`:
`idplan` es una clave primaria que arranca en 1, asi que 0 no puede confundirse
con ningun plan real. Se declara explicitamente como `defaultNullValue` para no
depender del defecto de Pinot para INT, que es `Integer.MIN_VALUE`; el codigo
que lo lee trata cualquier valor <= 0 como "sin cambio programado", de modo que
las filas ya existentes se comportan bien con cualquiera de los dos valores.

Cambio aditivo
--------------
No hay que reingerir nada: las filas existentes toman el valor por defecto. Aun
asi se exporta un respaldo de la tabla antes de tocar el esquema, y se recargan
los segmentos para que la columna quede disponible en las consultas.

Uso:
    python database/migra_plan_programado.py --dry-run
    python database/migra_plan_programado.py
"""
import argparse
import datetime
import json
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONTROLLER = "http://localhost:9000"
BROKER = "http://localhost:8099"
RESPALDOS = RAIZ / "_respaldos"

TABLA = "Fact_Suscripcion"
SIN_CAMBIO = 0  # centinela: "sin cambio de plan programado"

COLUMNA = {
    "name": "idplan_programado",
    "dataType": "INT",
    "defaultNullValue": SIN_CAMBIO,
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"1. Leyendo esquema de {TABLA}")
    esquema = json.loads(urllib.request.urlopen(f"{CONTROLLER}/schemas/{TABLA}").read())
    existentes = {c["name"] for c in esquema.get("dimensionFieldSpecs", [])}
    if COLUMNA["name"] in existentes:
        print(f"   `{COLUMNA['name']}` ya existe — nada que hacer.")
        return

    filas = query(f"SELECT * FROM {TABLA} LIMIT 10000")
    print(f"   {len(filas)} filas en la tabla")

    if args.dry_run:
        print(f"\n[dry-run] Se anadiria la columna: {COLUMNA}")
        return

    RESPALDOS.mkdir(exist_ok=True)
    sello = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = RESPALDOS / f"{TABLA}-{sello}.json"
    destino.write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"2. Respaldo escrito en {destino}")

    esquema.setdefault("dimensionFieldSpecs", []).append(COLUMNA)
    codigo, cuerpo = pedir("PUT", f"{CONTROLLER}/schemas/{TABLA}", esquema)
    print(f"3. PUT /schemas/{TABLA} -> {codigo} {cuerpo[:200]}")
    if codigo >= 300:
        raise SystemExit("No se pudo actualizar el esquema")

    codigo, cuerpo = pedir("POST", f"{CONTROLLER}/segments/{TABLA}/reload")
    print(f"4. Reload de segmentos -> {codigo} {cuerpo[:200]}")

    print("\nListo. La columna arranca en 0 = sin cambio programado.")


if __name__ == "__main__":
    main()
