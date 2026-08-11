"""Siembra el escenario de demo del frontend de #08 (monitoreo y facturacion).

Por que existe
--------------
Los escenarios B, H e I del quickstart no se pueden mirar en pantalla sin datos
que los produzcan, y son justo los que dependen de que el **copy** comunique
bien: un test comprueba que un token no esta, no que la frase se entienda.

Que crea
--------
  - **Partner 1 (Integradora Andina)** — cliente 920001, el del usuario demo
    `partner.demo@demo.tsi.com`. Cupo 10 000 y **15 000 llamadas**: 150 % de
    consumo, que es el escenario B (el excedente NO debe parecer un fallo).
    Sus logs incluyen 200, 403, 429 y 500 para el autodiagnostico.
  - **Partner 2 (Andes Logistica)** — cliente 1, **suspendido**: escenario I,
    donde el partner suspendido sigue viendo su consumo.
  - **Una factura de excedente con los tres reintentos agotados** y **un partner
    no tarificable**: los dos tipos del escenario H.

El partner 3 usa el plan 5 («Magnifico»), que tiene tarifa. Para forzar el caso
«no tarificable» se le pone el **centinela -1.0** en su propio plan de demo.

Deja datos de demo (ids 1, 2 y 970001). Limpiar con:
    python database/limpia_datos_prueba.py

Uso (desde la raiz del repo, con el stack encendido):
    python database/seed_monitoreo_demo.py
"""

import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

BROKER = "http://localhost:8099"

# Partner del usuario demo: es el que se ve al entrar al portal.
ID_PARTNER_DEMO = 1
ID_CLIENTE_DEMO = 920001
# Partner suspendido, para el escenario I.
ID_PARTNER_SUSPENDIDO = 2
ID_CLIENTE_SUSPENDIDO = 1
# Partner sin tarifa, para el escenario H.
ID_PARTNER_SIN_TARIFA = 970001
ID_CLIENTE_SIN_TARIFA = 970001
ID_PLAN_SIN_TARIFA = 970001

CUPO = 10_000
LLAMADAS = 15_000  # 150 % del cupo
NUNCA_EXPIRA = 253402300799000


def query(sql):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"},
    )
    d = json.load(urllib.request.urlopen(req, timeout=30))
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


def esperar(sql, minimo, segundos=90):
    limite = time.time() + segundos
    while time.time() < limite:
        filas = query(sql)
        if filas and (filas[0].get("n") or 0) >= minimo:
            return True
        time.sleep(3)
    return False


AHORA = int(datetime.now(timezone.utc).timestamp() * 1000)
HORA = 3_600_000
MES = 30 * 24 * HORA


def partner(idpartner, idcliente, nombre, activo, cupo=CUPO, suspension=("", "")):
    return {
        "idpartner": idpartner,
        "idcliente": idcliente,
        "nombrepartner": nombre,
        "planapi": "Profesional",
        "contacto_tecnico_nombre": "Diego Ramos",
        "contacto_tecnico_gmail": "partner.demo@demo.tsi.com",
        "fecha_suspension": suspension[0],
        "motivo_suspension": suspension[1],
        "activo": activo,
        "limitellamadasmes": cupo,
        "limitellamadasminuto": 120,
        "sandbox_activado": AHORA - MES,
        "sandbox_expiracion": NUNCA_EXPIRA,
        "fecha_actualizacion": AHORA,
    }


def credencial(idcredencial, idpartner, idcliente, nombre, entorno, activo=True):
    return {
        "idcredencial": idcredencial,
        "idpartner": idpartner,
        "idcliente": idcliente,
        # Hash de demo: nadie se autentica con esta credencial en la verificacion.
        "client_secret_hash": "$2b$12$demonstracionsolonoesunsecretoreal0000000000000000",
        "nombre_credencial": nombre,
        "entorno": entorno,
        "activo": activo,
        "fecha_creacion": AHORA - MES,
        "fecha_expiracion": NUNCA_EXPIRA,
        "fecha_actualizacion": AHORA,
    }


print("1) Partners")
publish("Dim_Partner_topic", [
    partner(ID_PARTNER_DEMO, ID_CLIENTE_DEMO, "Integradora Andina", True),
    partner(
        ID_PARTNER_SUSPENDIDO, ID_CLIENTE_SUSPENDIDO, "Andes Logística", False,
        suspension=("2026-08-01T09:00:00+00:00", "Mora de 18 días en excedente de API"),
    ),
    partner(ID_PARTNER_SIN_TARIFA, ID_CLIENTE_SIN_TARIFA, "Sierra Datos", True),
])
publish("Dim_CredencialAPI_topic", [
    credencial(11, ID_PARTNER_DEMO, ID_CLIENTE_DEMO, "plataforma-siniestros", "Producción"),
    credencial(12, ID_PARTNER_DEMO, ID_CLIENTE_DEMO, "tablero-interno", "Sandbox"),
    credencial(21, ID_PARTNER_SUSPENDIDO, ID_CLIENTE_SUSPENDIDO, "flota-andes", "Producción", False),
])

print("2) Plan sin tarifa (centinela -1.0) y su suscripción")
publish("Dim_Plan_topic", [{
    "idplan": ID_PLAN_SIN_TARIFA,
    "nombre": "Demo sin tarifa",
    "nivel": "Profesional",
    "precio_mensual": 100.0,
    # EL CENTINELA: no hay con qué calcular el excedente (RF-APM-011).
    "precio_excedente_llamada": -1.0,
    "limites": '{"api_calls_mes": 10000, "api_calls_minuto": 120}',
    "severidades_desbloqueadas": "null",
    "activo": True,
    "fecha_actualizacion": AHORA,
}])
publish("Fact_Suscripcion_topic", [{
    "id_suscripcion": ID_CLIENTE_SIN_TARIFA,
    "idcliente": ID_CLIENTE_SIN_TARIFA,
    "id_cliente": ID_CLIENTE_SIN_TARIFA,
    "idplan": ID_PLAN_SIN_TARIFA,
    "estado": "Activa",
    "activo": True,
    "fecha_inicio": AHORA - MES,
    "fecha_actualizacion": AHORA,
}])

print(f"3) Consumo del partner demo: {LLAMADAS} llamadas contra un cupo de {CUPO} (150 %)")
# Se agrega en pocas filas con `llamadas` alto: la UI suma, no cuenta filas.
consumo = []
for i in range(30):
    consumo.append({
        "idapiintegracion": 500_000 + i,
        "idpartner": ID_PARTNER_DEMO,
        "idcliente": ID_CLIENTE_DEMO,
        "idservicio": 1 if i % 2 == 0 else 2,
        "idestadointegracion": 2,
        "entorno": "Producción",
        "llamadas": LLAMADAS // 30,
        "errores": 4,
        "latencia": 88.0 + i,
        "activo": True,
        "fechahora": AHORA - i * HORA,
        "fecha_actualizacion": AHORA - i * HORA,
    })
# El partner sin tarifa tambien consume de mas: si no, no seria una excepcion.
for i in range(10):
    consumo.append({
        "idapiintegracion": 600_000 + i,
        "idpartner": ID_PARTNER_SIN_TARIFA,
        "idcliente": ID_CLIENTE_SIN_TARIFA,
        "idservicio": 1,
        "idestadointegracion": 2,
        "entorno": "Producción",
        "llamadas": 1_500,
        "errores": 0,
        "latencia": 92.0,
        "activo": True,
        "fechahora": AHORA - i * HORA,
        "fecha_actualizacion": AHORA - i * HORA,
    })
publish("Fact_APIIntegracion_topic", consumo)

print("4) Logs con los cuatro casos: 200, 403, 429 y 500")
CODIGOS = [200] * 12 + [403, 403, 429, 429, 429, 500]
ENDPOINTS = ["/api/v1/datos/accidentes"] * 16 + ["/api/v1/datos/accidentes?idseveridad=4"] * 2
logs = []
for i, codigo in enumerate(CODIGOS):
    logs.append({
        "idlogllamadaapi": 700_000 + i,
        "idpartner": ID_PARTNER_DEMO,
        "idcredencialapi": 11,
        "endpoint": ENDPOINTS[i % len(ENDPOINTS)],
        "metodohttp": "GET",
        "codigohttp": codigo,
        # 192.168.1.1 como entero: la UI debe formatearlo con puntos.
        "iporigen": 3232235777,
        "latenciams": 80.0 + i * 3,
        "fechallamada": AHORA - i * (HORA // 2),
        "fecha_actualizacion": AHORA - i * (HORA // 2),
    })
publish("Fact_LogLlamadaAPI_topic", logs)

print("5) Factura de excedente con los tres reintentos agotados")
publish("Fact_Factura_topic", [{
    "id_factura": "FAC-DEMO-EXCEDENTE-AGOTADA",
    "id_cliente": ID_CLIENTE_SUSPENDIDO,
    "id_suscripcion": ID_CLIENTE_SUSPENDIDO,
    "idmetodopago": 1,
    "numero_factura": "FAC-202607-00000099",
    "periodo": datetime.now(timezone.utc).strftime("%Y-%m"),
    "estado_pago": "Pendiente",
    "desglose_cargos": "[]",
    # Es el prefijo que deja `programar_reintento` al agotar los tres.
    "resultado_ultimo_reintento": "agotados: el emisor no respondió (timeout)",
    "id_factura_original": "",
    "es_nota_credito": False,
    "motivo_anulacion": "",
    "activo": True,
    "tipo": "excedente_api",
    "reintentos": 4,
    "monto_base": 63.5,
    "impuestos": 0.0,
    "monto_total": 63.5,
    "fecha_emision": AHORA - 5 * 24 * HORA,
    "fecha_vencimiento": AHORA - 2 * 24 * HORA,
    "fecha_actualizacion": AHORA,
}])

print("\n6) Esperando la ingesta de Pinot…")
ok = all([
    esperar(f"SELECT COUNT(*) AS n FROM Dim_Partner WHERE idpartner = {ID_PARTNER_DEMO}", 1),
    esperar(f"SELECT COUNT(*) AS n FROM Fact_APIIntegracion WHERE idpartner = {ID_PARTNER_DEMO}", 30),
    esperar(f"SELECT COUNT(*) AS n FROM Fact_LogLlamadaAPI WHERE idpartner = {ID_PARTNER_DEMO}", 18),
    esperar("SELECT COUNT(*) AS n FROM Fact_Factura WHERE tipo = 'excedente_api'", 1),
])
if not ok:
    print("   ERROR: la ingesta no se completó")
    sys.exit(1)

total = query(
    f"SELECT SUM(llamadas) AS n FROM Fact_APIIntegracion "
    f"WHERE idpartner = {ID_PARTNER_DEMO} AND entorno = 'Producción'"
)
print(f"\nListo. Consumo del partner demo: {int(total[0]['n'])} de {CUPO} llamadas.")
print("  Portal del partner:  partner.demo@demo.tsi.com")
print("  Consola/excepciones: un usuario con rol Administrador")
print("\nLimpia con: python database/limpia_datos_prueba.py")
