"""Verificacion de #08 contra Pinot REAL (T062, criterio de salida T066).

Por que existe
--------------
Este modulo **vive de agregaciones** —SUM, AVG, GROUP BY— y el doble en memoria
de `conftest.py` las reproduce **a mano**. Que 396 tests pasen ahi no garantiza
que Pinot resuelva las mismas consultas igual: es exactamente el hueco de
`decisiones-pendientes.md` #18, y aqui pesa mas que en #07 porque de estas
cifras sale lo que se le factura a un cliente.

Comprueba lo que un mock no puede
---------------------------------
  1. `SUM(llamadas)` da el total exacto contra filas reales.
  2. El filtro de entorno **excluye** de verdad el consumo de sandbox.
  3. `GROUP BY idservicio` agrupa bien.
  4. El `LIMIT` implicito de Pinot no trunca la agregacion.
  5. `Dim_EstadoIntegracion` tiene solo los 2 estados alcanzables.
  6. `Dim_Severidad` tiene el catalogo canonico con `severidad` como STRING.

Deja filas de prueba (ids 95xxxx). Limpiar con:
    python database/limpia_datos_prueba.py

Uso (desde la raiz del repo, con el stack encendido):
    python database/verifica_monitoreo_api.py
"""

import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"

ID_PARTNER = 950_001
ID_CLIENTE = 950_001
LLAMADAS_PRODUCCION = 37
LLAMADAS_SANDBOX = 11

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
    return [dict(zip(rt["dataSchema"]["columnNames"], r)) for r in rt["rows"]] if rt else []


def publish(topic, registros):
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=payload.encode("utf-8"), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")


def esperar(sql, minimo, segundos=60):
    limite = time.time() + segundos
    while time.time() < limite:
        filas = query(sql)
        if filas and (filas[0].get("n") or 0) >= minimo:
            return True
        time.sleep(3)
    return False


BASE_MS = 1_750_000_000_000  # ventana fija: la verificacion no depende del reloj


def fila_consumo(i, entorno, idservicio, codigo=200):
    return {
        "idapiintegracion": 950_000 + i,
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "idservicio": idservicio,
        "idestadointegracion": 2 if entorno == "Producción" else 1,
        "entorno": entorno,
        "llamadas": 1,
        "errores": 1 if codigo >= 400 else 0,
        "latencia": 100.0,
        "activo": True,
        "fechahora": BASE_MS + i,
        "fecha_actualizacion": BASE_MS + i,
    }


print("0) Sembrando consumo de prueba")
filas = []
i = 0
for _ in range(LLAMADAS_PRODUCCION):
    filas.append(fila_consumo(i, "Producción", 1 if i % 2 == 0 else 2))
    i += 1
for _ in range(LLAMADAS_SANDBOX):
    filas.append(fila_consumo(i, "Sandbox", 1))
    i += 1
publish("Fact_APIIntegracion_topic", filas)

if not esperar(
    f"SELECT COUNT(*) AS n FROM Fact_APIIntegracion WHERE idpartner = {ID_PARTNER}",
    LLAMADAS_PRODUCCION + LLAMADAS_SANDBOX,
):
    print("   ERROR: la ingesta no se completo")
    sys.exit(1)
print(f"   {len(filas)} filas ingeridas")

VENTANA = f"fechahora >= {BASE_MS} AND fechahora < {BASE_MS + 100_000}"

print("\n1) Exactitud de SUM(llamadas)")
r = query(
    f"SELECT SUM(llamadas) AS total FROM Fact_APIIntegracion "
    f"WHERE idpartner = {ID_PARTNER} AND entorno = 'Producción' AND {VENTANA} LIMIT 1"
)
total = int(r[0]["total"] or 0)
comprobar(
    "SUM(llamadas) cuenta exactamente las de produccion",
    total == LLAMADAS_PRODUCCION,
    f"esperado {LLAMADAS_PRODUCCION}, obtenido {total}",
)

print("\n2) El filtro de entorno EXCLUYE de verdad el sandbox")
comprobar(
    "el consumo de pruebas no entra en el total de produccion",
    total != LLAMADAS_PRODUCCION + LLAMADAS_SANDBOX,
    f"sin el filtro darian {LLAMADAS_PRODUCCION + LLAMADAS_SANDBOX}",
)
r = query(
    f"SELECT SUM(llamadas) AS total FROM Fact_APIIntegracion "
    f"WHERE idpartner = {ID_PARTNER} AND entorno = 'Sandbox' AND {VENTANA} LIMIT 1"
)
comprobar(
    "sandbox se consulta aparte y da su propio total",
    int(r[0]["total"] or 0) == LLAMADAS_SANDBOX,
)

print("\n3) GROUP BY idservicio")
grupos = query(
    f"SELECT idservicio, SUM(llamadas) AS llamadas FROM Fact_APIIntegracion "
    f"WHERE idpartner = {ID_PARTNER} AND entorno = 'Producción' AND {VENTANA} "
    f"GROUP BY idservicio ORDER BY llamadas DESC LIMIT 50"
)
comprobar("agrupa en los 2 servicios sembrados", len(grupos) == 2, f"{len(grupos)} grupos")
comprobar(
    "la suma de los grupos coincide con el total",
    sum(int(g["llamadas"]) for g in grupos) == LLAMADAS_PRODUCCION,
)

print("\n4) El LIMIT implicito no trunca la agregacion")
# Pinot aplica LIMIT 10 silencioso a las consultas sin limite. Una agregacion
# sobre 37 filas debe dar 37, no 10: si diera 10, el excedente facturado
# saldria mal y nadie lo notaria.
comprobar(
    "la agregacion no se queda en las 10 primeras filas",
    total > 10,
    f"{total} > 10",
)

print("\n5) Catalogo Dim_EstadoIntegracion")
estados = query(
    "SELECT idestadointegracion, nombre, activo FROM Dim_EstadoIntegracion "
    "ORDER BY idestadointegracion LIMIT 10"
)
activos = [e for e in estados if e.get("activo")]
comprobar("solo 2 estados activos (el 3 es inalcanzable)", len(activos) == 2,
          f"{[e['nombre'] for e in activos]}")

print("\n6) Catalogo Dim_Severidad")
severidades = query(
    "SELECT idseveridad, severidad FROM Dim_Severidad ORDER BY idseveridad LIMIT 10"
)
comprobar("las 4 severidades canonicas estan sembradas", len(severidades) == 4)
comprobar(
    "`severidad` guarda el NOMBRE como texto, no un numero",
    bool(severidades) and isinstance(severidades[0].get("severidad"), str),
    f"{severidades[0].get('severidad') if severidades else 'sin filas'}",
)

print("\n" + "=" * 68)
fallos = [d for d, ok in resultados if not ok]
print(f"  {len(resultados) - len(fallos)}/{len(resultados)} comprobaciones correctas")
for d in fallos:
    print(f"    FALLA: {d}")
print("=" * 68)
print(f"\n(consumo de prueba del partner {ID_PARTNER})")
print("Limpia con: python database/limpia_datos_prueba.py")
sys.exit(1 if fallos else 0)
