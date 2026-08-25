"""
Reubica la flota y las regiones operativas a EE.UU.

Los accidentes vienen del dataset US_Accidents, pero la flota demo nace en CDMX.
Con esa mezcla el despacho automatico no encuentra nunca una unidad cercana y el
mapa dibuja dos nubes de puntos separadas por 3.000 km.

Cada unidad se lleva a un **foco real de siniestralidad** — se eligen las calles
con mas accidentes del dataset y se usa su coordenada media, asi que las
unidades caen donde de verdad hay trabajo y no en un punto arbitrario.

**Por que se lee la fila entera antes de republicar.** Las tablas de Pinot son
upsert por clave primaria: publicar un registro parcial no actualiza campos,
**borra los que faltan**. Asi que se lee la fila completa, se cambian solo las
columnas de ubicacion y se republica entera.

Uso:
    python database/reubica_flota_ee_uu.py --dry-run
    python database/reubica_flota_ee_uu.py
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"


def consulta(sql: str) -> list[dict]:
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    rt = d.get("resultTable")
    if not rt:
        raise SystemExit(f"consulta sin resultado: {json.dumps(d)[:300]}")
    cols = rt["dataSchema"]["columnNames"]
    return [dict(zip(cols, fila)) for fila in rt["rows"]]


def publicar(topic: str, registros: list[dict]) -> None:
    if not registros:
        return
    carga = "\n".join(json.dumps(r, ensure_ascii=False) for r in registros)
    p = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=carga.encode("utf-8"), capture_output=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"fallo publicando en {topic}: {p.stderr.decode()[:300]}")


def focos(n: int) -> list[dict]:
    """Las n calles con mas accidentes, con su coordenada media y su condado."""
    calles = consulta(
        "SELECT idcalle, count(*) AS n, avg(latitudinicio) AS lat, "
        "avg(longitudinicio) AS lng FROM Fact_Accidente "
        f"GROUP BY idcalle ORDER BY n DESC LIMIT {n * 4}"
    )
    fuera, condados_vistos = [], set()
    for c in calles:
        det = consulta(f"SELECT idcalle, calle, idciudad FROM Dim_Calle WHERE idcalle = {int(c['idcalle'])}")
        if not det:
            continue
        ciu = consulta(f"SELECT idciudad, ciudad, idcondado FROM Dim_Ciudad WHERE idciudad = {int(det[0]['idciudad'])}")
        if not ciu:
            continue
        idcondado = int(ciu[0]["idcondado"])
        # una unidad por condado: repartir la flota, no amontonarla
        if idcondado in condados_vistos:
            continue
        condados_vistos.add(idcondado)
        con = consulta(f"SELECT idcondado, condado, idestado FROM Dim_Condado WHERE idcondado = {idcondado}")
        fuera.append({
            "idcondado": idcondado,
            "condado": con[0]["condado"] if con else "?",
            "idestado": int(con[0]["idestado"]) if con else 0,
            "ciudad": ciu[0]["ciudad"],
            "calle": det[0]["calle"],
            "lat": float(c["lat"]),
            "lng": float(c["lng"]),
            "accidentes": int(c["n"]),
        })
        if len(fuera) >= n:
            break
    return fuera


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    unidades = consulta("SELECT * FROM Dim_UnidadEmergencia LIMIT 500")
    print(f"Unidades: {len(unidades)}")
    destinos = focos(max(len(unidades), 1))
    print(f"Focos de siniestralidad elegidos: {len(destinos)}")
    for d in destinos:
        print(f"   {d['ciudad']:22} {d['condado']:20} {d['accidentes']:>6} accidentes  "
              f"({d['lat']:.4f}, {d['lng']:.4f})")

    if not destinos:
        print("sin focos: ¿esta cargado Fact_Accidente?")
        return 1

    ahora = int(time.time() * 1000)
    nuevas = []
    for i, u in enumerate(unidades):
        d = destinos[i % len(destinos)]
        fila = dict(u)  # fila COMPLETA: un registro parcial borraria columnas
        fila["idcondado"] = d["idcondado"]
        fila["latitud"] = d["lat"]
        fila["longitud"] = d["lng"]
        fila["zonacobertura"] = f"{d['ciudad']}, {d['condado']}"
        fila["fecha_actualizacion"] = ahora
        nuevas.append(fila)
        print(f"   unidad {u.get('idunidademergencia')} -> {d['ciudad']}")

    regiones = consulta("SELECT * FROM Dim_RegionOperativa LIMIT 200")
    nuevas_reg = []
    for i, r in enumerate(regiones):
        d = destinos[i % len(destinos)]
        fila = dict(r)
        fila["idestado"] = d["idestado"]
        fila["nombreregion"] = f"Region {d['condado']}"
        fila["fecha_actualizacion"] = ahora
        nuevas_reg.append(fila)
    print(f"Regiones operativas a reubicar: {len(nuevas_reg)}")

    if args.dry_run:
        print("\n(dry-run: no se publica nada)")
        return 0

    publicar("Dim_UnidadEmergencia_topic", nuevas)
    publicar("Dim_RegionOperativa_topic", nuevas_reg)
    print(f"\nPublicadas {len(nuevas)} unidades y {len(nuevas_reg)} regiones. "
          "Pinot tarda ~10s en reflejarlo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
