"""Verificacion end-to-end del modulo #07 contra Pinot REAL.

Por que existe
--------------
Los 105 tests del modulo corren contra el doble en memoria de `conftest.py`,
que no reproduce ni los centinelas de Pinot ni el retraso de ingesta
(`decisiones-pendientes.md` #18). Este script ejerce los SERVICIOS REALES
contra la base real, que es donde aparecieron los tres defectos de esta sesion.

Cubre el ciclo completo de CU-O48 y CU-O49:
  registro -> asignacion de plan -> emision -> solicitud -> aprobacion

Deja filas de prueba. Limpiar con:
    python database/limpia_datos_prueba.py
    python database/seed_versiones_contrato.py   # la limpieza purga el catalogo

ATENCION: esa limpieza NO borra el cliente 920001 ni su suscripcion, porque
Dim_Cliente y Fact_Suscripcion contienen datos reales y no se purgan enteras.
Ese par sobrevive a proposito y es reutilizable en la siguiente ejecucion.

Uso (desde la raiz del repo):
    python database/verifica_onboarding_e2e.py
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# `backend/.env` apunta a los hostnames de la red de Docker (`pinot-broker`,
# `kafka:29092`), que no resuelven desde el host. Los puertos publicados
# 8099 y 9092 son los mismos servicios, asi que el script los fuerza: se
# ejerce el codigo de produccion, solo cambia como llega al contenedor.
os.environ["PINOT_BROKER_URL"] = "http://localhost:8099"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"

import django  # noqa: E402

django.setup()

from apps.partners.domain_constants import (  # noqa: E402
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    NUNCA_EXPIRA,
    SIN_CUPO,
    SIN_PLAN,
)
from apps.partners.services.asignar_plan_acceso_service import (  # noqa: E402
    AsignarPlanAccesoService,
)
from apps.partners.services.consulta_partner_service import (  # noqa: E402
    ConsultaPartnerService,
)
from apps.partners.services.emitir_credencial_service import (  # noqa: E402
    EmitirCredencialError,
    EmitirCredencialService,
)
from apps.partners.services.promocion_produccion_service import (  # noqa: E402
    PromocionProduccionError,
    PromocionProduccionService,
)
from apps.partners.services.registro_partner_service import (  # noqa: E402
    RegistroPartnerError,
    RegistroPartnerService,
)
from apps.partners.services.secreto_service import SecretoService  # noqa: E402

BROKER = "http://localhost:8099"
ID_CLIENTE = 920_001
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
    import subprocess

    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=json.dumps(registro, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())


def esperar(sql, segundos=40):
    """Pinot tarda 5-15 s en ingerir: esta espera es la realidad del sistema."""
    limite = time.time() + segundos
    while time.time() < limite:
        filas = query(sql)
        if filas:
            return filas
        time.sleep(2)
    return []


print("0) Preparando cliente con suscripcion vigente")
ahora = int(time.time() * 1000)
plan = query("SELECT idplan, nombre, limites FROM Dim_Plan WHERE idplan = 2 LIMIT 1")
if not plan:
    print("   ERROR: falta el plan 2 (Profesional). Ejecuta los seeds.")
    sys.exit(1)
limites = json.loads(plan[0]["limites"])
print(f"   plan: {plan[0]['nombre']} -> {limites['api_calls_mes']}/mes, "
      f"{limites['api_calls_minuto']}/min")

publish("Dim_Cliente_topic", {
    "idcliente": ID_CLIENTE, "nombre": "E2E Onboarding", "razon_social": "E2E",
    "tipo": "aseguradora", "nit_identificacion": "E2E-001", "plan_suscripcion": "Profesional",
    "logo_url": "", "estado_onboarding": "Completado", "admin_local_id": 1,
    "estado": "Activo", "activo": True, "fecha_actualizacion": ahora,
})
publish("Fact_Suscripcion_topic", {
    "id_suscripcion": ID_CLIENTE, "idcliente": ID_CLIENTE, "idplan": 2,
    "estado": "Activa", "activo": True, "renovacionautomatica": True,
    "motivocancelacion": "", "periodicidad": "Mensual", "nivel": "Profesional",
    "severidades_desbloqueadas": '["Baja","Media"]', "carga_lote_habilitada": True,
    "precio": 149.0, "fecha_inicio": ahora, "fecha_fin": ahora + 30 * 86400000,
    "fechacancelacion": 0, "fecha_actualizacion": ahora,
})
if not esperar(f"SELECT idcliente FROM Dim_Cliente WHERE idcliente = {ID_CLIENTE}"):
    print("   ERROR: el cliente no llego a Pinot")
    sys.exit(1)
esperar(f"SELECT id_suscripcion FROM Fact_Suscripcion WHERE idcliente = {ID_CLIENTE}")
print("   cliente y suscripcion ingeridos")

print("\n1) RF-PON-001 — registro del partner")
partner = RegistroPartnerService().registrar(
    idcliente=ID_CLIENTE,
    nombrepartner="E2E Aseguradora",
    contacto_tecnico_nombre="QA",
    contacto_tecnico_gmail="qa@e2e.com",
    ejecutado_por="Administrador",
)
IDPARTNER = int(partner["idpartner"])
comprobar("el partner nace SIN plan (centinela '')", partner["planapi"] == SIN_PLAN,
          f"es {partner['planapi']!r}")
comprobar("el partner nace SIN cupo (centinela -1)",
          partner["limitellamadasmes"] == SIN_CUPO)
esperar(f"SELECT idpartner FROM Dim_Partner WHERE idpartner = {IDPARTNER}")

print("\n2) RN-PON-002 — un segundo partner sobre el mismo cliente se rechaza")
try:
    RegistroPartnerService().registrar(
        idcliente=ID_CLIENTE, nombrepartner="Duplicado",
        contacto_tecnico_nombre="X", contacto_tecnico_gmail="x@e2e.com",
        ejecutado_por="Administrador",
    )
    comprobar("el duplicado se rechaza", False, "NO lanzo error")
except RegistroPartnerError as exc:
    comprobar("el duplicado se rechaza contra Pinot real",
              exc.code == "partner_duplicado",
              f"idpartner_existente={exc.extra.get('idpartner_existente')}")

print("\n3) RF-PON-004 — sin plan NO se pueden emitir credenciales")
try:
    EmitirCredencialService().emitir(
        idpartner=IDPARTNER, nombre_credencial="prematura", ejecutado_por="Partner"
    )
    comprobar("la guarda de plan bloquea la emision", False, "NO lanzo error")
except EmitirCredencialError as exc:
    # Este es EL caso que el centinela 'null' de Pinot dejaba pasar.
    comprobar("la guarda `planapi <> ''` bloquea contra Pinot real",
              exc.code == "sin_plan")

print("\n4) RF-PON-003 — el cupo se deriva del plan contratado")
conplan = AsignarPlanAccesoService().asignar(
    idpartner=IDPARTNER, ejecutado_por="Administrador"
)
comprobar("cupo mensual derivado del plan",
          conplan["limitellamadasmes"] == limites["api_calls_mes"],
          f"{conplan['limitellamadasmes']}")
comprobar("cupo por minuto derivado del plan",
          conplan["limitellamadasminuto"] == limites["api_calls_minuto"],
          f"{conplan['limitellamadasminuto']}")
esperar(
    f"SELECT idpartner FROM Dim_Partner WHERE idpartner = {IDPARTNER} AND planapi <> ''"
)

print("\n5) RF-PON-004/005 — emision de credenciales nombradas")
cred_a = EmitirCredencialService().emitir(
    idpartner=IDPARTNER, nombre_credencial="plataforma-siniestros", ejecutado_por="Partner"
)
comprobar("se entrega el secreto en claro (unica vez)", bool(cred_a.get("client_secret")))
comprobar("la vigencia de pruebas es finita",
          cred_a["fecha_expiracion"] != NUNCA_EXPIRA)

cred_b = EmitirCredencialService().emitir(
    idpartner=IDPARTNER, nombre_credencial="deteccion-fraude", ejecutado_por="Partner"
)
comprobar("conviven varias credenciales nombradas en el mismo entorno",
          cred_a["idcredencial"] != cred_b["idcredencial"])

esperar(
    f"SELECT idcredencial FROM Dim_CredencialAPI WHERE idpartner = {IDPARTNER} "
    f"AND nombre_credencial = 'deteccion-fraude'"
)

print("\n6) RNF-PON-002 — el secreto NO se persiste en claro")
filas = query(
    f"SELECT idcredencial, client_secret_hash FROM Dim_CredencialAPI "
    f"WHERE idpartner = {IDPARTNER} LIMIT 10"
)
hashes = [f["client_secret_hash"] for f in filas]
comprobar("Pinot guarda hash bcrypt, no el secreto",
          all(h.startswith("$2b$") for h in hashes) and cred_a["client_secret"] not in hashes)
comprobar("el hash almacenado verifica contra el secreto entregado",
          any(SecretoService().verificar(cred_a["client_secret"], h) for h in hashes))

print("\n7) RN-PON-014 — nombre duplicado entre activas se rechaza")
try:
    EmitirCredencialService().emitir(
        idpartner=IDPARTNER, nombre_credencial="plataforma-siniestros",
        ejecutado_por="Partner",
    )
    comprobar("el nombre duplicado se rechaza", False, "NO lanzo error")
except EmitirCredencialError as exc:
    comprobar("el nombre duplicado se rechaza contra Pinot real",
              exc.code == "nombre_duplicado")

print("\n8) RN-PON-004 — solicitud y aprobacion de produccion")
PromocionProduccionService().solicitar(
    idpartner=IDPARTNER, nombre_credencial="produccion-siniestros"
)
esperar(
    f"SELECT idhistorial FROM Fact_HistorialAccesoPartner WHERE idpartner = {IDPARTNER} "
    f"AND tipo_cambio = 'solicitud_promocion_produccion'"
)
resolucion = PromocionProduccionService().resolver(idpartner=IDPARTNER, decision="aprobar")
comprobar("la aprobacion emite credencial de produccion",
          resolucion["estado"] == ESTADO_PRODUCCION_ACTIVA)
comprobar("produccion lleva el centinela 'no expira nunca'",
          resolucion["credencial"]["fecha_expiracion"] == NUNCA_EXPIRA)

esperar(
    f"SELECT idcredencial FROM Dim_CredencialAPI WHERE idpartner = {IDPARTNER} "
    f"AND entorno = 'Producción'"
)

print("\n9) RN-PON-008 — pruebas y produccion COEXISTEN")
sandbox_activas = query(
    f"SELECT idcredencial FROM Dim_CredencialAPI WHERE idpartner = {IDPARTNER} "
    f"AND entorno = 'Sandbox' AND activo = true LIMIT 10"
)
produccion = query(
    f"SELECT idcredencial FROM Dim_CredencialAPI WHERE idpartner = {IDPARTNER} "
    f"AND entorno = 'Producción' AND activo = true LIMIT 10"
)
comprobar("las credenciales de pruebas siguen activas tras aprobar produccion",
          len(sandbox_activas) == 2, f"{len(sandbox_activas)} activas")
comprobar("existe la credencial de produccion", len(produccion) == 1)

print("\n10) RF-PON-012 — el estado derivado es correcto contra Pinot real")
detalle = ConsultaPartnerService().detalle(IDPARTNER)
comprobar("estado derivado = Produccion activa",
          detalle["estado"] == ESTADO_PRODUCCION_ACTIVA, detalle["estado"])
comprobar("el detalle NUNCA expone el hash ni el secreto",
          "client_secret_hash" not in json.dumps(detalle["credenciales"])
          and cred_a["client_secret"] not in json.dumps(detalle))

print("\n11) RF-PON-010 — la bitacora registro todo el ciclo")
eventos = query(
    f"SELECT tipo_cambio FROM Fact_HistorialAccesoPartner WHERE idpartner = {IDPARTNER} "
    f"LIMIT 100"
)
tipos = {e["tipo_cambio"] for e in eventos}
esperados = {
    "registro", "asignacion_plan", "activacion_sandbox",
    "solicitud_promocion_produccion", "activacion_produccion",
}
comprobar("los 5 eventos del ciclo estan en la bitacora",
          esperados <= tipos, f"faltan: {esperados - tipos or 'ninguno'}")

print("\n" + "=" * 68)
fallos = [d for d, ok in resultados if not ok]
print(f"  {len(resultados) - len(fallos)}/{len(resultados)} comprobaciones correctas")
for d in fallos:
    print(f"    FALLA: {d}")
print("=" * 68)
print(f"\n(partner de prueba idpartner={IDPARTNER}, cliente {ID_CLIENTE})")
print("Limpia con: python database/limpia_datos_prueba.py")
sys.exit(1 if fallos else 0)
