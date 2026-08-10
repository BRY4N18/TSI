"""Habilita el autoservicio del partner y el limite de llamadas por minuto.

Dos cambios que faltaban para poder implementar Partners y API:

1. Rol `PartnerIntegracion` (idrol 15).
   El SRS L121 define "Partner de integracion" como actor: el area tecnica de un
   cliente integrador, que obtiene credenciales y ve su consumo. Ninguno de los
   14 roles existentes lo cubria, asi que un partner no tenia forma de entrar al
   sistema y todo el autoservicio de CU-O49 era inalcanzable.

   No se reutiliza `Cliente` (idrol 1): aunque todo partner pertenece a un
   cliente, son personas distintas de la misma organizacion con permisos
   distintos. Tampoco `DesarrolladorAPIs` (idrol 5), que es el equipo de TSI que
   registra partners, no quien consume.

   De paso corrige la descripcion del idrol 5, que decia "Consumo de
   integraciones via API" — eso describia al partner, no al desarrollador
   (SRS L124: "Equipo tecnico de integraciones").

2. `api_calls_minuto` en `Dim_Plan.limites`.
   El SRS §3.4.1 exige que el plan de acceso defina el limite de llamadas
   "mensual y por minuto"; solo existia el mensual. Sin el, RF-PON-003 no puede
   derivar el cupo del partner y devolveria 422 siempre.

   No es un prorrateo del mensual: protege contra rafagas. Los valores que
   siembra este script son SOLO valores iniciales — el Director de Estrategia
   los reconfigura libremente al editar el plan (CU-O26 / RF-O26.1), igual que
   ya ocurre con `severidades_desbloqueadas` y `carga_lote_habilitada`.

Uso:
    python database/migra_rol_partner_y_limite_minuto.py --dry-run
    python database/migra_rol_partner_y_limite_minuto.py
"""
import argparse
import datetime
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BROKER = "http://localhost:8099"
RESPALDOS = RAIZ / "_respaldos"

ROL_PARTNER = {
    "idrol": 15,
    "rol": "PartnerIntegracion",
    "descripcion": "Area tecnica de un cliente integrador: credenciales y consumo propio (CU-O49)",
    "activo": True,
}
DESCRIPCION_DEV_APIS = "Equipo tecnico de integraciones: registra partners, asigna planes y vigila consumo"

# Valores iniciales por nivel. Protegen contra rafagas; no son un prorrateo del
# cupo mensual. Reconfigurables por el Director de Estrategia (CU-O26).
POR_MINUTO_POR_NIVEL = {"Básico": 30, "Profesional": 120, "Empresarial": 600}
POR_MINUTO_DEFECTO = 30


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
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"   publicados {len(registros)} registros en {topic}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ahora = int(time.time() * 1000)

    # --- 1. Roles ------------------------------------------------------------
    print("1) Rol PartnerIntegracion")
    roles = query("SELECT idrol, rol, descripcion FROM Dim_Rol LIMIT 1000")
    por_id = {r["idrol"]: r for r in roles}
    print(f"   roles actuales: {len(roles)}")

    roles_a_publicar = []
    if 15 in por_id:
        print(f"   idrol 15 ya existe: {por_id[15]['rol']!r}")
    else:
        roles_a_publicar.append({**ROL_PARTNER, "fecha_actualizacion": ahora})
        print("   idrol 15 -> se creara PartnerIntegracion")

    dev = por_id.get(5)
    if dev and dev.get("descripcion") != DESCRIPCION_DEV_APIS:
        roles_a_publicar.append({
            "idrol": 5, "rol": dev["rol"], "descripcion": DESCRIPCION_DEV_APIS,
            "activo": True, "fecha_actualizacion": ahora,
        })
        print(f"   idrol 5 -> corregir descripcion")
        print(f"      antes: {dev.get('descripcion')!r}")
        print(f"      ahora: {DESCRIPCION_DEV_APIS!r}")

    # --- 2. Limites de planes ------------------------------------------------
    print("\n2) api_calls_minuto en Dim_Plan.limites")
    planes = query("SELECT * FROM Dim_Plan LIMIT 1000")
    print(f"   planes actuales: {len(planes)}")

    RESPALDOS.mkdir(exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RESPALDOS / f"Dim_Plan_{marca}.json"
    destino.write_text(json.dumps(planes, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(json.loads(destino.read_text(encoding="utf-8"))) != len(planes):
        print("   ABORTADO: el respaldo no se pudo releer intacto.")
        return 1
    print(f"   respaldo verificado -> {destino.name}")

    planes_a_publicar = []
    for plan in planes:
        try:
            limites = json.loads(plan.get("limites") or "{}")
        except json.JSONDecodeError:
            print(f"   AVISO: limites ilegible en {plan['nombre']!r}, se omite")
            continue
        if "api_calls_minuto" in limites:
            print(f"   {plan['nombre']:<24} ya lo tiene ({limites['api_calls_minuto']})")
            continue
        valor = POR_MINUTO_POR_NIVEL.get(plan.get("nivel"), POR_MINUTO_DEFECTO)
        limites["api_calls_minuto"] = valor
        nuevo = dict(plan)
        nuevo["limites"] = json.dumps(limites, ensure_ascii=False)
        nuevo["fecha_actualizacion"] = ahora
        planes_a_publicar.append(nuevo)
        print(f"   {plan['nombre']:<24} nivel={plan.get('nivel'):<14} -> api_calls_minuto={valor}")

    if not roles_a_publicar and not planes_a_publicar:
        print("\nSin cambios: todo esta al dia.")
        return 0

    if args.dry_run:
        print(f"\n--dry-run: no se publico nada. "
              f"({len(roles_a_publicar)} roles, {len(planes_a_publicar)} planes pendientes)")
        return 0

    print("\n3) Publicando")
    publish("Dim_Rol_topic", roles_a_publicar)
    publish("Dim_Plan_topic", planes_a_publicar)

    # --- 3. Verificar --------------------------------------------------------
    print("\n4) Verificando ingesta")
    limite = time.time() + 60
    ok_rol = ok_planes = False
    while time.time() < limite:
        if not ok_rol:
            ok_rol = bool(query("SELECT idrol FROM Dim_Rol WHERE idrol = 15"))
        if not ok_planes:
            faltan = [
                p["nombre"] for p in query("SELECT nombre, limites FROM Dim_Plan LIMIT 1000")
                if "api_calls_minuto" not in (p.get("limites") or "")
            ]
            ok_planes = not faltan
        if ok_rol and ok_planes:
            break
        time.sleep(3)

    print(f"   rol PartnerIntegracion visible: {ok_rol}")
    print(f"   todos los planes con api_calls_minuto: {ok_planes}")
    if not (ok_rol and ok_planes):
        print(f"   ATENCION: ingesta incompleta. Respaldo en {destino}")
        return 1

    print("\nMigracion completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
