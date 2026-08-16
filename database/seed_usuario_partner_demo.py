"""Siembra un usuario demo con rol PartnerIntegracion (idrol 15).

Por que existe
--------------
El rol 15 se creo el 2026-08-08, pero `Dim_Usuario_Rol` **no se lo asigna a
nadie**: el portal del partner era inalcanzable en la demo, no por un defecto
de la UI sino por ausencia de datos. Se detecto al ejecutar el quickstart del
frontend (T088) contra la app real.

Que crea
--------
  - `Dim_Usuarios`      usuario 9001, partner.demo@demo.tsi.com
  - `Dim_Credencial`    su contrasena (la misma `password123` de la demo)
  - `Dim_Usuario_Rol`   el vinculo con el rol 15
  - `Dim_Cliente`       republica el cliente 920001 con `admin_local_id = 9001`

El vinculo usuario->cliente se hace por `admin_local_id` y no por
`Dim_Usuario_Cliente`, y `ClienteLookupService.resolve_idcliente()` ya contempla
ese camino.

El motivo NO es que esa tabla carezca de topic de Kafka: lo tiene declarado
(`Dim_Usuario_Cliente_topic`, ver `database/tablas.json`). El motivo real es que
**ningun codigo de produccion publica en el** — las unicas escrituras estan en
las pruebas—, asi que sembrar por ahi dejaria el vinculo invisible para todo lo
demas. La conclusion practica se mantiene; la justificacion anterior era falsa.

Consecuencia, anotada en `decisiones-pendientes.md` #23: hoy la pertenencia a una
cuenta se resuelve de hecho por administrador local en TODOS los departamentos,
asi que de una organizacion con cinco usuarios solo uno consulta los listados
acotados a su cuenta.

Idempotente: si el usuario ya existe, no vuelve a publicarlo.

Uso:
    python database/seed_usuario_partner_demo.py --dry-run
    python database/seed_usuario_partner_demo.py
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import bcrypt

# La contrasena NO se hardcodea aqui: se toma de la fuente compartida y se
# hashea al vuelo, como el resto de los seeds demo. Convivir con un literal
# propio fue justo el defecto que corrigio
# `tests/regression/test_credenciales_demo_consistentes.py`.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend" / "scripts"))
from _demo_seed_common import DEMO_PASSWORD, ESTADO_CREDENCIAL_ACTIVO  # noqa: E402

BROKER = "http://localhost:8099"

ID_USUARIO = 9001
GMAIL = "partner.demo@demo.tsi.com"
ID_ROL_PARTNER = 15
ID_CLIENTE = 920001


def hashear(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

SIN_FECHA = -9223372036854775808
SIN_PROSPECTO = -2147483648


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


def publish(topic, registro):
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=json.dumps(registro, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"   publicado en {topic}")


def esperar(sql, segundos=45):
    limite = time.time() + segundos
    while time.time() < limite:
        if query(sql):
            return True
        time.sleep(2)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ahora = int(time.time() * 1000)

    if query(f"SELECT idusuario FROM Dim_Usuarios WHERE idusuario = {ID_USUARIO} LIMIT 1"):
        print(f"El usuario {ID_USUARIO} ya existe. Sin cambios.")
        return 0

    cliente = query(f"SELECT * FROM Dim_Cliente WHERE idcliente = {ID_CLIENTE} LIMIT 1")
    if not cliente:
        print(f"ERROR: no existe el cliente {ID_CLIENTE}.")
        return 1

    suscripcion = query(
        f"SELECT estado FROM Fact_Suscripcion WHERE idcliente = {ID_CLIENTE} LIMIT 5"
    )
    if not any(s.get("estado") in ("Activa", "Activo") for s in suscripcion):
        print(f"ERROR: el cliente {ID_CLIENTE} no tiene suscripcion vigente.")
        return 1

    print(f"Cliente {ID_CLIENTE} ({cliente[0]['nombre']}) con suscripcion vigente.")
    print(f"Se creara el usuario {ID_USUARIO} <{GMAIL}> con rol {ID_ROL_PARTNER}.")

    if args.dry_run:
        print("\n--dry-run: no se publico nada.")
        return 0

    publish("Dim_Usuarios_topic", {
        "idusuario": ID_USUARIO, "gmail": GMAIL, "nombres": "Diego", "apellidos": "Ramos",
        "identificacion": "0102030415", "telefono": "0991234515", "genero": "M",
        "fechanacimiento": SIN_FECHA, "activo": True, "fecha_actualizacion": ahora,
    })
    publish("Dim_Credencial_topic", {
        "idcredencial": ID_USUARIO, "idusuario": ID_USUARIO,
        "contrasena": hashear(DEMO_PASSWORD),
        "estadocredencial": ESTADO_CREDENCIAL_ACTIVO,
        "fecha_solicitud_cambio": SIN_FECHA, "fecha_actualizacion": ahora,
    })
    publish("Dim_Usuario_Rol_topic", {
        "idusuariorol": ID_USUARIO, "idusuario": ID_USUARIO, "idrol": ID_ROL_PARTNER,
        "activo": True, "fecha_actualizacion": ahora,
    })

    # Upsert FULL: se republica la fila COMPLETA del cliente cambiando solo
    # `admin_local_id`; publicar campos sueltos borraria el resto.
    fila_cliente = {**cliente[0], "admin_local_id": ID_USUARIO, "fecha_actualizacion": ahora}
    fila_cliente.setdefault("idprospecto", SIN_PROSPECTO)
    publish("Dim_Cliente_topic", fila_cliente)

    print("\nEsperando ingesta...")
    ok = esperar(f"SELECT idusuario FROM Dim_Usuarios WHERE idusuario = {ID_USUARIO}")
    ok &= esperar(
        f"SELECT idusuario FROM Dim_Usuario_Rol WHERE idusuario = {ID_USUARIO} "
        f"AND idrol = {ID_ROL_PARTNER}"
    )
    ok &= esperar(
        f"SELECT idcliente FROM Dim_Cliente WHERE idcliente = {ID_CLIENTE} "
        f"AND admin_local_id = {ID_USUARIO}"
    )

    if not ok:
        print("ATENCION: la ingesta no se completo. Reintenta la verificacion en unos segundos.")
        return 1

    print(f"\nListo. Entra con {GMAIL} / {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
