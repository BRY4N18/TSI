"""Verifica que el esquema Pinot de Partners y API quedo correcto.

No comprueba solo la configuracion: reproduce las reglas de negocio que estaban
rotas por los centinelas de Pinot y confirma que ahora se cumplen.

Deja filas de prueba (ids 99xxxx). Para limpiarlas:
    python database/despliega_partners.py --forzar

Uso:
    python database/verifica_partners.py
"""
import json
import subprocess
import sys
import time
import urllib.request

CONTROLLER = "http://localhost:9000"
BROKER = "http://localhost:8099"
NUNCA_EXPIRA = 253402300799000

resultados = []


def comprobar(descripcion, condicion, detalle=""):
    resultados.append((descripcion, bool(condicion), detalle))
    marca = "OK   " if condicion else "FALLA"
    print(f"  [{marca}] {descripcion}" + (f"  ({detalle})" if detalle else ""))


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
        raise RuntimeError(f"Error publicando: {proc.stderr.decode()}")


def esperar(sql, segundos=30):
    limite = time.time() + segundos
    while time.time() < limite:
        filas = query(sql)
        if filas:
            return filas[0]
        time.sleep(1.5)
    return None


print("1) Configuracion de tablas")
for tabla, esperado in (("Dim_Partner", "fecha_actualizacion"),
                        ("Dim_CredencialAPI", "fecha_actualizacion"),
                        ("Dim_VersionContratoAPI", "fecha_actualizacion")):
    d = json.load(urllib.request.urlopen(f"{CONTROLLER}/tables/{tabla}", timeout=20))
    cfg = d.get("REALTIME") or d.get("OFFLINE")
    tc = cfg["segmentsConfig"]["timeColumnName"]
    cc = cfg["upsertConfig"]["comparisonColumns"][0]
    comprobar(f"{tabla}: timeColumnName = {esperado}", tc == esperado, f"es {tc}")
    comprobar(f"{tabla}: comparisonColumn = {esperado}", cc == esperado, f"es {cc}")

print("\n2) Columnas nuevas de Dim_CredencialAPI")
esq = json.load(urllib.request.urlopen(f"{CONTROLLER}/schemas/Dim_CredencialAPI", timeout=20))
nombres = {c["name"] for g in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
           for c in esq.get(g, [])}
comprobar("existe nombre_credencial", "nombre_credencial" in nombres)
comprobar("existe fecha_expiracion", "fecha_expiracion" in nombres)

print("\n3) Dim_VersionContratoAPI conserva la FK a Dim_Servicio")
esq = json.load(urllib.request.urlopen(f"{CONTROLLER}/schemas/Dim_VersionContratoAPI", timeout=20))
nombres = {c["name"] for g in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
           for c in esq.get(g, [])}
comprobar("existe id_servicio (FK, normalizacion 1:N)", "id_servicio" in nombres)

print("\n4) RF-PON-004: un partner SIN plan no debe poder emitir credenciales")
ahora = int(time.time() * 1000)
publish("Dim_Partner_topic", {
    "idpartner": 990001, "idcliente": 990, "nombrepartner": "Sin plan",
    "contacto_tecnico_nombre": "QA", "contacto_tecnico_gmail": "qa@test.com",
    "planapi": None, "limitellamadasmes": None, "limitellamadasminuto": None,
    "sandbox_activado": None, "sandbox_expiracion": None,
    "fecha_suspension": None, "motivo_suspension": None,
    "activo": True, "fecha_actualizacion": ahora,
})
fila = esperar("SELECT * FROM Dim_Partner WHERE idpartner = 990001")
if not fila:
    print("     ERROR: la fila no llego a Pinot")
    sys.exit(1)
comprobar("planapi centinela = '' (antes era el string 'null')",
          fila["planapi"] == "", f"es {fila['planapi']!r}")
comprobar("limitellamadasmes centinela = -1 (antes era 0)",
          fila["limitellamadasmes"] == -1, f"es {fila['limitellamadasmes']}")
comprobar("sandbox_expiracion centinela = 0 (antes era Long.MIN_VALUE)",
          fila["sandbox_expiracion"] == 0, f"es {fila['sandbox_expiracion']}")

sin_plan = query("SELECT idpartner FROM Dim_Partner "
                 "WHERE idpartner = 990001 AND planapi <> ''")
comprobar("la guarda \"planapi <> ''\" EXCLUYE al partner sin plan",
          len(sin_plan) == 0, f"devolvio {len(sin_plan)} filas")

print("\n5) RF-PON-008: una credencial de PRODUCCION no debe figurar como vencida")
publish("Dim_CredencialAPI_topic", {
    "idcredencial": 990002, "idpartner": 990001, "idcliente": 990,
    "client_secret_hash": "hash", "nombre_credencial": "sistema-siniestros",
    "entorno": "Produccion", "activo": True,
    "fecha_creacion": ahora, "fecha_expiracion": None,
    "fecha_actualizacion": ahora,
})
fila = esperar("SELECT * FROM Dim_CredencialAPI WHERE idcredencial = 990002")
comprobar("fecha_expiracion centinela = ano 9999 (antes Long.MIN_VALUE)",
          fila["fecha_expiracion"] == NUNCA_EXPIRA, f"es {fila['fecha_expiracion']}")

vencidas = query(f"SELECT idcredencial FROM Dim_CredencialAPI "
                 f"WHERE idcredencial = 990002 AND fecha_expiracion < {ahora}")
comprobar("el job de expiracion NO la marca como vencida",
          len(vencidas) == 0, f"devolvio {len(vencidas)} filas")

print("\n6) El upsert sigue aplicando actualizaciones (revocacion CU-O55)")
publish("Dim_CredencialAPI_topic", {
    "idcredencial": 990002, "idpartner": 990001, "idcliente": 990,
    "client_secret_hash": "hash", "nombre_credencial": "sistema-siniestros",
    "entorno": "Produccion", "activo": False,
    "fecha_creacion": ahora, "fecha_expiracion": None,
    "fecha_actualizacion": ahora + 5000,
})
limite = time.time() + 30
revocada = False
while time.time() < limite:
    f = query("SELECT activo FROM Dim_CredencialAPI WHERE idcredencial = 990002")
    if f and f[0]["activo"] in (False, 0):
        revocada = True
        break
    time.sleep(1.5)
comprobar("la revocacion se aplica (activo -> false)", revocada)

print("\n" + "=" * 66)
fallos = [d for d, ok, _ in resultados if not ok]
print(f"  {len(resultados) - len(fallos)}/{len(resultados)} comprobaciones correctas")
if fallos:
    print("  FALLAN:")
    for d in fallos:
        print(f"    - {d}")
print("=" * 66)
print("\nLimpia las filas de prueba con: python database/despliega_partners.py --forzar")
sys.exit(1 if fallos else 0)
