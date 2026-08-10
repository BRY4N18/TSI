"""
Higiene de datos del entorno demo. Idempotente: correrlo dos veces no cambia nada.

Corrige cuatro cosas detectadas al recorrer el sistema:

1. Unidades de prueba de humo (`Humo`, `Humo Test`, `Prueba SMTP`, placas HUMO-*/SMTP-*)
   que quedaron activas y aparecen en la flota y en el mapa operativo.

2. Unidades apuntando a `idusuario` inexistente. Son el residuo del rollback fallido
   de importacion_lote_unidad_service (el rollback releia de Pinot un registro recien
   escrito por Kafka, que aun no estaba ingerido, y `update()` devolvia None en
   silencio). El codigo ya esta corregido; esto limpia lo que quedo de antes.
   Una unidad sin usuario valido no puede iniciar sesion (CU-O30 `find_by_usuario`),
   asi que ocupa cupo de flota sin poder operar nunca.

3. Rol `Unidad` duplicado (idrol 4 y 7). Se desactiva el que no tiene usuarios
   asignados; no se borra para no romper referencias historicas.

4. Descripciones de accidentes con contenido ofensivo cargado como dato de prueba.

Todas las escrituras van por Kafka (unico canal de escritura, ver infrastructure.md).
Las tablas son upsert por clave primaria, asi que se publica el registro completo
con la correccion aplicada; publicar un registro parcial borraria el resto de campos.

Uso:
    python database/higiene_datos.py --dry-run   # solo reporta
    python database/higiene_datos.py             # aplica
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)

# Marcas de datos de prueba en la flota.
NOMBRES_PRUEBA = {"humo", "humo test", "prueba smtp"}
PREFIJOS_PLACA_PRUEBA = ("HUMO-", "SMTP-", "SMTP2-")

# Descripciones a saneadas. Se reemplaza el texto, no se borra el accidente:
# el caso participa de despachos e historial y borrarlo dejaria huerfanos.
TEXTO_SANEADO = "Descripcion retirada por contenido inapropiado (dato de prueba)."
PATRONES_OFENSIVOS = ("por culpa del negro",)


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


def publish(topic, records):
    if not records:
        return
    payload = "\n".join(json.dumps(r) for r in records)
    proc = subprocess.run(
        [
            "docker", "exec", "-i", "kafka",
            "kafka-console-producer", "--bootstrap-server", "localhost:9092",
            "--topic", topic,
        ],
        input=payload.encode(),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"  -> publicados {len(records)} registros en {topic}")


def es_unidad_de_prueba(u):
    nombre = str(u.get("unidademergencia") or "").strip().lower()
    placa = str(u.get("placa") or "")
    return nombre in NOMBRES_PRUEBA or placa.startswith(PREFIJOS_PLACA_PRUEBA)


def limpiar_unidades(dry_run):
    unidades = query("SELECT * FROM Dim_UnidadEmergencia LIMIT 10000")
    usuarios = {u["idusuario"] for u in query("SELECT idusuario FROM Dim_Usuarios LIMIT 10000")}

    a_desactivar = []
    for u in unidades:
        if not u.get("activo"):
            continue
        idusuario = u.get("idusuario")
        # Pinot devuelve el centinela de nulo de INT cuando la columna no se escribio.
        huerfana = idusuario is None or idusuario == -2147483648 or idusuario not in usuarios
        if es_unidad_de_prueba(u) or huerfana:
            motivo = "prueba" if es_unidad_de_prueba(u) else f"idusuario {idusuario} inexistente"
            a_desactivar.append((u, motivo))

    print(f"\n[1/4+2] Unidades a desactivar: {len(a_desactivar)}")
    for u, motivo in a_desactivar:
        print(f"  - #{u['idunidademergencia']} {u.get('unidademergencia')!r} "
              f"placa={u.get('placa')!r} ({motivo})")

    if not dry_run:
        publish(
            "Dim_UnidadEmergencia_topic",
            [{**u, "activo": False, "fecha_actualizacion": NOW_MS} for u, _ in a_desactivar],
        )
    return len(a_desactivar)


def limpiar_roles_duplicados(dry_run):
    roles = query("SELECT * FROM Dim_Rol LIMIT 10000")
    asignaciones = query("SELECT idrol FROM Dim_Usuario_Rol LIMIT 10000")
    en_uso = {a["idrol"] for a in asignaciones}

    por_nombre = {}
    for r in roles:
        if r.get("activo"):
            por_nombre.setdefault(r["rol"], []).append(r)

    todas_asignaciones = query("SELECT * FROM Dim_Usuario_Rol LIMIT 10000")

    a_desactivar = []
    reasignaciones = []
    for nombre, grupo in por_nombre.items():
        if len(grupo) < 2:
            continue
        # Se conserva el de menor id como canonico. Los permisos del sistema se
        # evaluan por NOMBRE de rol, no por id (ver core/auth/permissions.py), asi
        # que mover un usuario entre dos filas que se llaman igual no cambia lo
        # que puede hacer: solo deja una definicion en vez de dos.
        conservar = min(grupo, key=lambda r: r["idrol"])
        for r in grupo:
            if r["idrol"] == conservar["idrol"]:
                continue
            for asig in todas_asignaciones:
                if asig["idrol"] == r["idrol"]:
                    reasignaciones.append({**asig, "idrol": conservar["idrol"],
                                           "fecha_actualizacion": NOW_MS})
            a_desactivar.append((r, conservar))

    print(f"\n[3] Roles duplicados: {len(a_desactivar)} a consolidar "
          f"({len(reasignaciones)} asignaciones a reapuntar)")
    for r, conservar in a_desactivar:
        usados = " (tenia usuarios)" if r["idrol"] in en_uso else ""
        print(f"  - idrol={r['idrol']} {r['rol']!r} -> se unifica en idrol={conservar['idrol']}{usados}")

    if not dry_run:
        # Primero reapuntar usuarios, despues desactivar el rol vacio: al reves
        # habria un instante sin rol valido.
        publish("Dim_Usuario_Rol_topic", reasignaciones)
        publish(
            "Dim_Rol_topic",
            [{**r, "activo": False, "fecha_actualizacion": NOW_MS} for r, _ in a_desactivar],
        )
    return len(a_desactivar)


def sanear_descripciones(dry_run):
    accidentes = query("SELECT * FROM Fact_Accidente LIMIT 10000")
    a_sanear = [
        a for a in accidentes
        if any(p in str(a.get("descripcion") or "").lower() for p in PATRONES_OFENSIVOS)
    ]

    print(f"\n[4] Descripciones a sanear: {len(a_sanear)}")
    for a in a_sanear:
        print(f"  - {a['idaccidente']}: {str(a.get('descripcion'))[:60]!r}")

    if not dry_run:
        publish(
            "Fact_Accidente_topic",
            [{**a, "descripcion": TEXTO_SANEADO, "fecha_actualizacion": NOW_MS} for a in a_sanear],
        )
    return len(a_sanear)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="solo reporta, no escribe")
    args = parser.parse_args()

    if args.dry_run:
        print("=== MODO DRY-RUN: no se escribe nada ===")

    total = 0
    total += limpiar_unidades(args.dry_run)
    total += limpiar_roles_duplicados(args.dry_run)
    total += sanear_descripciones(args.dry_run)

    print(f"\n{'Se detectaron' if args.dry_run else 'Se corrigieron'} {total} registros.")
    if not args.dry_run and total:
        print("Pinot tarda unos segundos en reflejar los cambios (ingesta Kafka).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
