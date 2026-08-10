"""Verifica el vinculo factura-disputa contra Pinot real.

Los tests del backend usan el doble en memoria de `conftest.py`, que no
reproduce los centinelas de Pinot ni los tipos del esquema. Este script
comprueba contra la base real lo que aquellos no pueden ver.

Deja filas de prueba (ids 99xxxx) en Fact_Factura. Fact_Reclamo NO se toca.

Uso:
    python database/verifica_factura_reclamo.py
"""
import json
import subprocess
import sys
import time
import urllib.request

CONTROLLER = "http://localhost:9000"
BROKER = "http://localhost:8099"

resultados = []


def comprobar(descripcion, condicion, detalle=""):
    resultados.append((descripcion, bool(condicion)))
    print(f"  [{'OK   ' if condicion else 'FALLA'}] {descripcion}" + (f"  ({detalle})" if detalle else ""))


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


def publish(topic, registro):
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=json.dumps(registro).encode(), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())


def tipo_de(tabla, columna):
    esq = json.load(urllib.request.urlopen(f"{CONTROLLER}/schemas/{tabla}", timeout=20))
    for grupo in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs"):
        for c in esq.get(grupo, []):
            if c["name"] == columna:
                return c
    return None


print("1) Tipos del esquema desplegado")
c = tipo_de("Fact_Reclamo", "idfactura")
comprobar("Fact_Reclamo.idfactura es STRING", c and c["dataType"] == "STRING",
          f"es {c['dataType'] if c else 'ausente'}")
comprobar("Fact_Reclamo.idfactura tiene defaultNullValue ''",
          c and c.get("defaultNullValue") == "", f"es {c.get('defaultNullValue')!r}")
f = tipo_de("Fact_Factura", "id_factura")
comprobar("Fact_Factura.id_factura es STRING", f and f["dataType"] == "STRING")
comprobar("los dos lados del vinculo coinciden en tipo",
          c and f and c["dataType"] == f["dataType"], f"{c['dataType']} vs {f['dataType']}")

t = tipo_de("Fact_Factura", "tipo")
comprobar("Fact_Factura.tipo existe y es STRING", t and t["dataType"] == "STRING")
comprobar("Fact_Factura.tipo tiene default 'suscripcion'",
          t and t.get("defaultNullValue") == "suscripcion", f"es {t.get('defaultNullValue')!r}")

print("\n2) Los 8 tickets sobrevivieron a la migracion")
filas = query("SELECT id_reclamo, idfactura FROM Fact_Reclamo LIMIT 1000")
comprobar("Fact_Reclamo conserva 8 filas", len(filas) == 8, f"hay {len(filas)}")
comprobar("ningun idfactura quedo con el centinela INT viejo",
          all(str(r["idfactura"]) != "-2147483648" for r in filas))
comprobar("los tickets sin factura tienen idfactura = ''",
          all(r["idfactura"] == "" for r in filas))

print("\n3) Un UUID real cabe donde antes no (era la razon del cambio)")
uuid_real = "8c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f"
ahora = int(time.time() * 1000)
publish("Fact_Factura_topic", {
    "id_factura": uuid_real, "id_cliente": 990, "id_suscripcion": 1,
    "idmetodopago": 1, "numero_factura": "TEST-0001", "periodo": "2026-08",
    "estado_pago": "Pendiente", "desglose_cargos": "{}",
    "resultado_ultimo_reintento": "", "id_factura_original": "",
    "es_nota_credito": False, "motivo_anulacion": "", "activo": True,
    "reintentos": 0, "monto_base": 100.0, "impuestos": 0.0, "monto_total": 100.0,
    "tipo": "excedente_api",
    "fecha_emision": ahora, "fecha_vencimiento": ahora + 86400000,
    "fecha_actualizacion": ahora,
})
limite = time.time() + 40
fila = None
while time.time() < limite:
    r = query(f"SELECT * FROM Fact_Factura WHERE id_factura = '{uuid_real}'")
    if r:
        fila = r[0]
        break
    time.sleep(2)
comprobar("una factura con id UUID se persiste entera", fila is not None)
if fila:
    comprobar("el UUID se conserva sin truncar", fila["id_factura"] == uuid_real)
    comprobar("tipo = 'excedente_api' se guarda", fila["tipo"] == "excedente_api",
              f"es {fila['tipo']!r}")

print("\n4) RF-O54.3: la consulta de no-duplicacion de excedente ya es posible")
dup = query(f"SELECT id_factura FROM Fact_Factura "
            f"WHERE tipo = 'excedente_api' AND periodo = '2026-08' AND id_cliente = 990")
comprobar("se puede filtrar por tipo + periodo + cliente", len(dup) == 1,
          f"devolvio {len(dup)} filas")

print("\n5) Una factura sin 'tipo' cae en 'suscripcion' (no en excedente)")
otro = "9d2e3f4a-5b6c-7d8e-9f0a-1b2c3d4e5f60"
publish("Fact_Factura_topic", {
    "id_factura": otro, "id_cliente": 991, "id_suscripcion": 1,
    "idmetodopago": 1, "numero_factura": "TEST-0002", "periodo": "2026-08",
    "estado_pago": "Pendiente", "desglose_cargos": "{}",
    "resultado_ultimo_reintento": "", "id_factura_original": "",
    "es_nota_credito": False, "motivo_anulacion": "", "activo": True,
    "reintentos": 0, "monto_base": 50.0, "impuestos": 0.0, "monto_total": 50.0,
    # sin "tipo": debe tomar el default
    "fecha_emision": ahora, "fecha_vencimiento": ahora + 86400000,
    "fecha_actualizacion": ahora,
})
limite = time.time() + 40
fila2 = None
while time.time() < limite:
    r = query(f"SELECT tipo FROM Fact_Factura WHERE id_factura = '{otro}'")
    if r:
        fila2 = r[0]
        break
    time.sleep(2)
comprobar("una factura sin 'tipo' se clasifica como 'suscripcion'",
          fila2 and fila2["tipo"] == "suscripcion",
          f"es {fila2['tipo']!r}" if fila2 else "no llego")
comprobar("y NO contamina la consulta de excedentes",
          len(query("SELECT id_factura FROM Fact_Factura "
                    "WHERE tipo = 'excedente_api' AND id_cliente = 991")) == 0)

print("\n" + "=" * 66)
fallos = [d for d, ok in resultados if not ok]
print(f"  {len(resultados) - len(fallos)}/{len(resultados)} comprobaciones correctas")
for d in fallos:
    print(f"    FALLA: {d}")
print("=" * 66)
print("\nQuedan 2 facturas de prueba en Fact_Factura (id_cliente 990 y 991).")
sys.exit(1 if fallos else 0)
