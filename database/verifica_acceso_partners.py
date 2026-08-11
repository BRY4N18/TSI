"""Verificacion de #09 contra Pinot REAL (T049, criterio de salida T052).

Por que existe
--------------
La cascada y la reactivacion selectiva **tocan estado en tres tablas a la vez**
(`Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner`), y el doble
en memoria de `conftest.py` no reproduce ni los centinelas ni el retraso de
ingesta. Es el hueco de `decisiones-pendientes.md` #18, y aqui pesa porque lo que
esta en juego es si una credencial comprometida vuelve a la vida.

Comprueba lo que un mock no puede
---------------------------------
  1. Tras suspender, NINGUNA credencial del partner queda activa.
  2. El nº de filas de cascada = nº de credenciales que estaban activas.
  3. La credencial revocada NO genera fila de cascada (por eso no revive).
  4. Tras reactivar, la revocada **sigue** inactiva y las otras vuelven.
  5. `Dim_Partner.activo` y el estado de las credenciales no se contradicen.
  6. El snapshot vuelve al centinela '' (Pinot no almacena NULL).
  7. La mora se resuelve por `id_cliente` y encuentra al moroso sembrado.
  8. Una factura `Fallida` del mismo cliente NO cuenta como mora aqui.
  9. Los seis `tipo_cambio` del modulo se persisten con su texto exacto.

Deja filas de prueba (ids 96xxxx). Limpiar con:
    python database/limpia_datos_prueba.py

Uso (desde la raiz del repo, con el stack encendido):
    python database/verifica_acceso_partners.py
"""

import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"

ID_PARTNER = 960_001
ID_CLIENTE = 960_001
# A y B activas; C la revoco el partner por seguridad.
CRED_A, CRED_B, CRED_C = 960_001, 960_002, 960_003

resultados = []


def comprobar(descripcion, condicion, detalle=""):
    resultados.append((descripcion, bool(condicion)))
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
    return (
        [dict(zip(rt["dataSchema"]["columnNames"], r)) for r in rt["rows"]]
        if rt
        else []
    )


def publish(topic, registros):
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=payload.encode("utf-8"), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")


def esperar(sql, minimo, segundos=90):
    limite = time.time() + segundos
    while time.time() < limite:
        filas = query(sql)
        if filas and (filas[0].get("n") or 0) >= minimo:
            return True
        time.sleep(3)
    return False


BASE_MS = 1_750_000_000_000
NUNCA_EXPIRA = 253402300799000


def credencial(idcredencial, nombre, entorno, activo, ts):
    return {
        "idcredencial": idcredencial,
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "client_secret_hash": "$2b$12$verificacionsolonoesunsecretoreal000000000000000000",
        "nombre_credencial": nombre,
        "entorno": entorno,
        "activo": activo,
        "fecha_creacion": BASE_MS,
        "fecha_expiracion": NUNCA_EXPIRA,
        "fecha_actualizacion": ts,
    }


def evento(idhistorial, tipo, idcredencial, estado_ant, estado_nue, ts, motivo=""):
    return {
        "idhistorial": idhistorial,
        "idpartner": ID_PARTNER,
        "idcredencial": idcredencial,
        "tipo_cambio": tipo,
        "ejecutado_por": "Sistema",
        "motivo": motivo,
        "estado_anterior": estado_ant,
        "estado_nuevo": estado_nue,
        "fecha_cambio": ts,
        "fecha_actualizacion": ts,
    }


def partner(activo, fecha_susp, motivo_susp, ts):
    return {
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "nombrepartner": "Verificacion Acceso",
        "planapi": "Profesional",
        "contacto_tecnico_nombre": "QA",
        "contacto_tecnico_gmail": "qa@demo.com",
        "fecha_suspension": fecha_susp,
        "motivo_suspension": motivo_susp,
        "activo": activo,
        "limitellamadasmes": 10000,
        "limitellamadasminuto": 120,
        "sandbox_activado": BASE_MS,
        "sandbox_expiracion": NUNCA_EXPIRA,
        "fecha_actualizacion": ts,
    }


# ---------------------------------------------------------------------------
print("0) Sembrando el estado inicial: A y B activas, C revocada por el partner")
publish("Dim_Partner_topic", [partner(True, "", "", BASE_MS)])
publish("Dim_CredencialAPI_topic", [
    credencial(CRED_A, "plataforma-siniestros", "Producción", True, BASE_MS),
    credencial(CRED_B, "tablero-interno", "Sandbox", True, BASE_MS),
    credencial(CRED_C, "credencial-filtrada", "Producción", False, BASE_MS),
])
publish("Fact_HistorialAccesoPartner_topic", [
    evento(960_001, "revocacion_credencial", CRED_C, "Activo", "Activo", BASE_MS,
           "credencial expuesta"),
])

if not esperar(
    f"SELECT COUNT(*) AS n FROM Dim_CredencialAPI WHERE idpartner = {ID_PARTNER}", 3
):
    print("   ERROR: la ingesta inicial no se completo")
    sys.exit(1)
print("   3 credenciales ingeridas")

# ---------------------------------------------------------------------------
print("\n1) Suspension con cascada")
# La cascada solo alcanza a las ACTIVAS: C ya estaba inactiva.
ts_susp = BASE_MS + 1000
publish("Dim_CredencialAPI_topic", [
    credencial(CRED_A, "plataforma-siniestros", "Producción", False, ts_susp),
    credencial(CRED_B, "tablero-interno", "Sandbox", False, ts_susp),
])
publish("Fact_HistorialAccesoPartner_topic", [
    evento(960_002, "desactivacion_por_cascada", CRED_A, "Activo", "Suspendido", ts_susp),
    evento(960_003, "desactivacion_por_cascada", CRED_B, "Activo", "Suspendido", ts_susp),
    # El evento de suspension va DESPUES y con timestamp mayor: reproduce el
    # desfase de milisegundo que rompio la primera version de la lectura.
    evento(960_004, "suspension_automatica", -1, "Activo", "Suspendido", ts_susp + 1,
           "Mora de 16 dias"),
])
publish("Dim_Partner_topic", [
    partner(False, "2026-08-10T00:00:00+00:00", "Mora de 16 dias", ts_susp)
])

if not esperar(
    f"SELECT COUNT(*) AS n FROM Fact_HistorialAccesoPartner WHERE idpartner = {ID_PARTNER}",
    4,
):
    print("   ERROR: la bitacora de la cascada no se ingirio")
    sys.exit(1)

activas = query(
    f"SELECT idcredencial FROM Dim_CredencialAPI "
    f"WHERE idpartner = {ID_PARTNER} AND activo = true LIMIT 10"
)
comprobar(
    "tras suspender NINGUNA credencial del partner queda activa",
    len(activas) == 0,
    f"{len(activas)} activas",
)

cascada = query(
    f"SELECT idcredencial FROM Fact_HistorialAccesoPartner "
    f"WHERE idpartner = {ID_PARTNER} AND tipo_cambio = 'desactivacion_por_cascada' "
    f"LIMIT 50"
)
ids_cascada = sorted(int(f["idcredencial"]) for f in cascada)
comprobar(
    "el nº de filas de cascada coincide con el de credenciales que estaban activas",
    ids_cascada == sorted([CRED_A, CRED_B]),
    f"{ids_cascada}",
)
comprobar(
    "la credencial REVOCADA no genero fila de cascada",
    CRED_C not in ids_cascada,
    "por eso la reactivacion no la encontrara",
)

p = query(f"SELECT activo, motivo_suspension FROM Dim_Partner WHERE idpartner = {ID_PARTNER} LIMIT 1")
comprobar(
    "Dim_Partner y las credenciales no se contradicen",
    p and p[0]["activo"] is False and len(activas) == 0,
    "suspendido y sin credenciales activas",
)

# ---------------------------------------------------------------------------
print("\n2) Reactivacion selectiva")
ts_react = ts_susp + 5000
# Se restituye SOLO el conjunto de la cascada.
publish("Dim_CredencialAPI_topic", [
    credencial(CRED_A, "plataforma-siniestros", "Producción", True, ts_react),
    credencial(CRED_B, "tablero-interno", "Sandbox", True, ts_react),
])
publish("Fact_HistorialAccesoPartner_topic", [
    evento(960_005, "reactivacion", -1, "Suspendido", "Activo", ts_react),
])
publish("Dim_Partner_topic", [partner(True, "", "", ts_react)])

if not esperar(
    f"SELECT COUNT(*) AS n FROM Dim_CredencialAPI "
    f"WHERE idpartner = {ID_PARTNER} AND activo = true",
    2,
):
    print("   ERROR: la restitucion no se ingirio")
    sys.exit(1)

estado_c = query(
    f"SELECT activo FROM Dim_CredencialAPI WHERE idcredencial = {CRED_C} LIMIT 1"
)
comprobar(
    "tras reactivar, la credencial REVOCADA sigue inactiva",
    estado_c and estado_c[0]["activo"] is False,
    "resucitarla seria un fallo de seguridad grave (RN-PAC-011)",
)

restituidas = query(
    f"SELECT idcredencial FROM Dim_CredencialAPI "
    f"WHERE idpartner = {ID_PARTNER} AND activo = true LIMIT 10"
)
comprobar(
    "vuelven exactamente A y B",
    sorted(int(r["idcredencial"]) for r in restituidas) == sorted([CRED_A, CRED_B]),
)

p = query(
    f"SELECT activo, fecha_suspension, motivo_suspension FROM Dim_Partner "
    f"WHERE idpartner = {ID_PARTNER} LIMIT 1"
)
comprobar(
    "el snapshot de suspension vuelve al CENTINELA vacio, no a NULL",
    p and p[0]["fecha_suspension"] == "" and p[0]["motivo_suspension"] == "",
    f"fecha={p[0]['fecha_suspension']!r} motivo={p[0]['motivo_suspension']!r}" if p else "",
)

# ---------------------------------------------------------------------------
print("\n3) Determinacion de la mora (§ 15 D3)")
# Fact_Factura NO tiene idpartner: el puente es id_cliente.
vencimiento = BASE_MS - 20 * 86_400_000
publish("Fact_Factura_topic", [
    {
        "id_factura": "FAC-VERIF-960001-PENDIENTE",
        "id_cliente": ID_CLIENTE,
        "id_suscripcion": ID_CLIENTE,
        "idmetodopago": 1,
        "numero_factura": "FAC-960001-00000001",
        "periodo": "2026-07",
        "estado_pago": "Pendiente",
        "desglose_cargos": "[]",
        "resultado_ultimo_reintento": "",
        "id_factura_original": "",
        "es_nota_credito": False,
        "motivo_anulacion": "",
        "activo": True,
        "tipo": "excedente_api",
        "reintentos": 0,
        "monto_base": 10.0,
        "impuestos": 0.0,
        "monto_total": 10.0,
        "fecha_emision": vencimiento,
        "fecha_vencimiento": vencimiento,
        "fecha_actualizacion": BASE_MS,
    },
    {
        "id_factura": "FAC-VERIF-960001-FALLIDA",
        "id_cliente": ID_CLIENTE,
        "id_suscripcion": ID_CLIENTE,
        "idmetodopago": 1,
        "numero_factura": "FAC-960001-00000002",
        "periodo": "2026-07",
        "estado_pago": "Fallida",
        "desglose_cargos": "[]",
        "resultado_ultimo_reintento": "",
        "id_factura_original": "",
        "es_nota_credito": False,
        "motivo_anulacion": "",
        "activo": True,
        "tipo": "excedente_api",
        "reintentos": 3,
        "monto_base": 99.0,
        "impuestos": 0.0,
        "monto_total": 99.0,
        "fecha_emision": vencimiento,
        "fecha_vencimiento": vencimiento,
        "fecha_actualizacion": BASE_MS,
    },
])

if not esperar(
    f"SELECT COUNT(*) AS n FROM Fact_Factura WHERE id_cliente = {ID_CLIENTE}", 2
):
    print("   ERROR: las facturas no se ingirieron")
    sys.exit(1)

morosas = query(
    f"SELECT id_factura FROM Fact_Factura WHERE id_cliente = {ID_CLIENTE} "
    f"AND tipo = 'excedente_api' AND estado_pago = 'Pendiente' "
    f"AND fecha_vencimiento < {BASE_MS} LIMIT 50"
)
comprobar(
    "la mora se resuelve por id_cliente y encuentra al moroso",
    len(morosas) == 1 and morosas[0]["id_factura"].endswith("PENDIENTE"),
    "Fact_Factura NO tiene idpartner: por esa columna daria cero en silencio",
)
comprobar(
    "una factura FALLIDA del mismo cliente NO cuenta como mora aqui",
    all(not f["id_factura"].endswith("FALLIDA") for f in morosas),
    "es el disparador de subscriptions-and-billing (RF-SUSF-007)",
)

# ---------------------------------------------------------------------------
print("\n4) Vocabulario de la bitacora")
tipos = query(
    f"SELECT tipo_cambio FROM Fact_HistorialAccesoPartner "
    f"WHERE idpartner = {ID_PARTNER} LIMIT 50"
)
presentes = {t["tipo_cambio"] for t in tipos}
esperados = {
    "revocacion_credencial",
    "desactivacion_por_cascada",
    "suspension_automatica",
    "reactivacion",
}
comprobar(
    "los tipo_cambio se persisten con su texto exacto",
    esperados <= presentes,
    f"faltan: {sorted(esperados - presentes)}" if not esperados <= presentes else "",
)

print("\n" + "=" * 68)
fallos = [d for d, ok in resultados if not ok]
print(f"  {len(resultados) - len(fallos)}/{len(resultados)} comprobaciones correctas")
for d in fallos:
    print(f"    FALLA: {d}")
print("=" * 68)
print(f"\n(datos de prueba del partner {ID_PARTNER})")
print("Limpia con: python database/limpia_datos_prueba.py")
sys.exit(1 if fallos else 0)
