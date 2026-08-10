"""Redespliega en Pinot las tablas del departamento Partners y API.

Pinot NO permite cambiar en caliente `timeColumnName` (vive en segmentsConfig,
inmutable) ni `upsertConfig`. La unica via es borrar y recrear la tabla, por eso
este script existe en vez de un simple PUT.

Se ejecuta despues de `migra_partners_esquema.py`.

SEGURIDAD: se niega a borrar una tabla que tenga filas, salvo --forzar.
Al momento de escribirse, las cuatro tablas estaban vacias (0 filas).

Uso:
    python database/despliega_partners.py --dry-run
    python database/despliega_partners.py
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONTROLLER = "http://localhost:9000"
BROKER = "http://localhost:8099"

TABLAS_OBJETIVO = [
    "Dim_Partner",
    "Dim_CredencialAPI",
    "Fact_HistorialAccesoPartner",
    "Dim_VersionContratoAPI",
]


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


def contar_filas(tabla):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": f"SELECT COUNT(*) FROM {tabla}"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception:
        return None
    if d.get("exceptions"):
        return None
    rt = d.get("resultTable")
    return rt["rows"][0][0] if rt else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--forzar", action="store_true",
                        help="permite recrear tablas que tienen filas (SE PIERDEN)")
    args = parser.parse_args()

    esquemas = {e["schemaName"]: e for e in
                json.loads((RAIZ / "esquemas.json").read_text(encoding="utf-8"))}
    tablas = {t["tableName"]: t for t in
              json.loads((RAIZ / "tablas.json").read_text(encoding="utf-8"))}

    existentes = set(json.load(urllib.request.urlopen(f"{CONTROLLER}/tables", timeout=20))["tables"])

    print("Estado actual:")
    bloqueadas = []
    for nombre in TABLAS_OBJETIVO:
        if nombre in existentes:
            filas = contar_filas(nombre)
            print(f"  {nombre:32} existe, filas = {filas}")
            if filas:
                bloqueadas.append((nombre, filas))
        else:
            print(f"  {nombre:32} no existe (se creara)")

    if bloqueadas and not args.forzar:
        print("\nABORTADO: estas tablas tienen filas y se perderian:")
        for n, f in bloqueadas:
            print(f"  - {n}: {f} filas")
        print("Revisa los datos. Si aun asi quieres recrearlas: --forzar")
        return 1

    if args.dry_run:
        print("\n--dry-run: no se toco nada.")
        return 0

    for nombre in TABLAS_OBJETIVO:
        print(f"\n--- {nombre}")
        if nombre in existentes:
            code, cuerpo = pedir("DELETE", f"{CONTROLLER}/tables/{nombre}")
            print(f"  borrar tabla   -> {code}")
            if code >= 400:
                print(f"     {cuerpo[:300]}")
                return 1
            code, _ = pedir("DELETE", f"{CONTROLLER}/schemas/{nombre}")
            print(f"  borrar esquema -> {code}")

        code, cuerpo = pedir("POST", f"{CONTROLLER}/schemas", esquemas[nombre])
        print(f"  crear esquema  -> {code}")
        if code >= 400:
            print(f"     {cuerpo[:300]}")
            return 1

        # Tras un DELETE, Pinot tarda en retirar la "external view" del
        # servidor. Hasta que no desaparece, recrear la tabla devuelve 409.
        # No hay endpoint para consultarlo, asi que se reintenta con espera.
        for intento in range(1, 13):
            code, cuerpo = pedir("POST", f"{CONTROLLER}/tables", tablas[nombre])
            if code < 400:
                print(f"  crear tabla    -> {code}")
                break
            if code == 409 and "External view" in cuerpo:
                print(f"  crear tabla    -> 409 external view aun viva, "
                      f"reintento {intento}/12 en 5s")
                time.sleep(5)
                continue
            print(f"  crear tabla    -> {code}")
            print(f"     {cuerpo[:300]}")
            return 1
        else:
            print(f"  crear tabla    -> ABORTADO: la external view de {nombre} "
                  f"no se limpio tras 60s")
            return 1

    print("\nRedespliegue completo.")
    print("Verifica con: python database/verifica_partners.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
