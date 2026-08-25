"""
Carga el dataset US_Accidents en el dominio de accidentes.

El CSV encaja casi campo por campo con `Fact_Accidente`; la severidad 1-4 del
dataset coincide exactamente con `Dim_Severidad` (Leve/Moderado/Grave/Fatal),
asi que no hace falta traducirla.

La jerarquia geografica NACE del propio CSV, en este orden — cada nivel necesita
el id del anterior:

    Country -> Dim_Pais -> State -> Dim_Estado -> County -> Dim_Condado
            -> City -> Dim_Ciudad -> Street -> Dim_Calle

**Por que se publica en dos pasadas.** Los hechos referencian `idcalle`, asi que
las dimensiones tienen que existir antes. La primera pasada solo recorre el CSV
construyendo los diccionarios de dimension; la segunda emite los hechos ya con
el id resuelto. Es a cambio de leer el fichero dos veces, que sale mas barato
que mantener 2 millones de filas en memoria.

**Sobre los nulos.** Pinot no almacena NULL en este proyecto: un nulo publicado
se vuelve un centinela (el literal 'null' en STRING, 0 en metrica). Por eso los
campos que el CSV no trae —heridos, fallecidos, vehiculos— se publican con un
valor explicito y no se omiten.

Uso:
    python database/carga_accidentes_csv.py --csv C:/US_Accidents.csv
    python database/carga_accidentes_csv.py --csv C:/US_Accidents.csv --limite 5000
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

csv.field_size_limit(10 ** 7)

LOTE = 20_000  # registros por invocacion del productor de Kafka


def _productor(topic: str):
    return subprocess.Popen(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092",
         "--topic", topic,
         "--batch-size", "65536",
         "--request-timeout-ms", "60000"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def publicar_stream(topic: str, registros, etiqueta: str) -> int:
    """Publica por streaming: un solo productor para todo el flujo."""
    p = _productor(topic)
    n = 0
    t0 = time.time()
    try:
        for r in registros:
            p.stdin.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))
            n += 1
            if n % LOTE == 0:
                p.stdin.flush()
                seg = time.time() - t0
                print(f"   {etiqueta}: {n:,} ({n/max(seg,1):,.0f}/s)", flush=True)
        p.stdin.flush()
    finally:
        p.stdin.close()
        p.wait()
    if p.returncode != 0:
        err = p.stderr.read().decode()[:300]
        raise SystemExit(f"fallo publicando en {topic}: {err}")
    print(f"   {etiqueta}: {n:,} publicados en {time.time()-t0:,.0f}s", flush=True)
    return n


def ms(texto: str) -> int:
    """'2020-01-26 12:58:00' -> epoch ms UTC. 0 si no parsea."""
    if not texto:
        return 0
    try:
        d = datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S")
        return int(d.replace(tzinfo=timezone.utc).timestamp() * 1000)
    except ValueError:
        return 0


def limpio(v: str, defecto: str = "Sin dato") -> str:
    v = (v or "").strip()
    return v if v else defecto


def num(v: str, defecto: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


def construir_dimensiones(ruta: str, limite: int | None):
    """Primera pasada: solo dimensiones."""
    paises, estados, condados, ciudades, calles = {}, {}, {}, {}, {}
    ahora = int(time.time() * 1000)
    n = 0
    with io.open(ruta, encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            n += 1
            if limite and n > limite:
                break
            pais = limpio(row["Country"], "US")
            estado = limpio(row["State"])
            condado = limpio(row["County"])
            ciudad = limpio(row["City"])
            calle = limpio(row["Street"])

            if pais not in paises:
                paises[pais] = len(paises) + 1
            kе = (pais, estado)
            if kе not in estados:
                estados[kе] = len(estados) + 1
            kc = (kе, condado)
            if kc not in condados:
                condados[kc] = len(condados) + 1
            kci = (kc, ciudad)
            if kci not in ciudades:
                ciudades[kci] = len(ciudades) + 1
            kca = (kci, calle)
            if kca not in calles:
                calles[kca] = len(calles) + 1
    return paises, estados, condados, ciudades, calles, ahora, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="C:/US_Accidents.csv")
    ap.add_argument("--limite", type=int, default=None,
                    help="cargar solo las primeras N filas (para probar)")
    args = ap.parse_args()

    print("1) Primera pasada: construyendo dimensiones desde el CSV")
    t0 = time.time()
    paises, estados, condados, ciudades, calles, ahora, leidas = construir_dimensiones(
        args.csv, args.limite)
    print(f"   leidas {leidas:,} filas en {time.time()-t0:,.0f}s")
    print(f"   Dim_Pais {len(paises):,} · Dim_Estado {len(estados):,} · "
          f"Dim_Condado {len(condados):,} · Dim_Ciudad {len(ciudades):,} · "
          f"Dim_Calle {len(calles):,}")

    print("\n2) Publicando dimensiones (de arriba abajo: cada nivel usa el id del anterior)")
    publicar_stream("Dim_Pais_topic", (
        {"idpais": i, "pais": p, "activo": True, "fecha_actualizacion": ahora}
        for p, i in paises.items()), "Dim_Pais")

    publicar_stream("Dim_Estado_topic", (
        {"idestado": i, "idpais": paises[k[0]], "estado": k[1],
         "activo": True, "fecha_actualizacion": ahora}
        for k, i in estados.items()), "Dim_Estado")

    publicar_stream("Dim_Condado_topic", (
        {"idcondado": i, "idestado": estados[k[0]], "condado": k[1],
         "activo": True, "fecha_actualizacion": ahora}
        for k, i in condados.items()), "Dim_Condado")

    publicar_stream("Dim_Ciudad_topic", (
        {"idciudad": i, "idcondado": condados[k[0]], "ciudad": k[1],
         "activo": True, "fecha_actualizacion": ahora}
        for k, i in ciudades.items()), "Dim_Ciudad")

    publicar_stream("Dim_Calle_topic", (
        {"idcalle": i, "idciudad": ciudades[k[0]], "calle": k[1],
         "activo": True, "fecha_actualizacion": ahora}
        for k, i in calles.items()), "Dim_Calle")

    print("\n3) Segunda pasada: publicando hechos")

    def hechos():
        n = 0
        with io.open(args.csv, encoding="utf-8", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                n += 1
                if args.limite and n > args.limite:
                    break
                pais = limpio(row["Country"], "US")
                kе = (pais, limpio(row["State"]))
                kc = (kе, limpio(row["County"]))
                kci = (kc, limpio(row["City"]))
                idcalle = calles[(kci, limpio(row["Street"]))]

                ini, fin = ms(row["Start_Time"]), ms(row["End_Time"])
                dur = int((fin - ini) / 60000) if fin > ini else 0

                yield {
                    "idaccidente": row["ID"],
                    "idseveridad": int(num(row["Severity"], 2)),
                    "idcalle": idcalle,
                    # El CSV no dice quien reporto ni como: se marca como origen
                    # externo con centinelas explicitos, porque Pinot convertiria
                    # un nulo en un centinela silencioso de todas formas.
                    "idusuario": 0,
                    "idtiporeportado": 0,
                    "idreferenciaestacion": 0,
                    "idaccidenteorigen": "",
                    "horainicio": row["Start_Time"][:19],
                    "horafin": row["End_Time"][:19],
                    "descripcion": limpio(row["Description"], "")[:900],
                    "codigopostal": limpio(row["Zipcode"], ""),
                    "activo": True,
                    "duracionminutos": dur,
                    "numvehiculos": 0,
                    "numvictimas": 0,
                    "numheridos": 0,
                    "numfallecidos": 0,
                    "latitudinicio": num(row["Start_Lat"]),
                    "longitudinicio": num(row["Start_Lng"]),
                    "distanciamillas": num(row["Distance(mi)"]),
                    "fechahoraaccidente": ini or ahora,
                    "fecha_actualizacion": ahora,
                }

    total = publicar_stream("Fact_Accidente_topic", hechos(), "Fact_Accidente")
    print(f"\nListo: {total:,} accidentes + "
          f"{len(paises)+len(estados)+len(condados)+len(ciudades)+len(calles):,} dimensiones.")
    print("Pinot tarda en ingerir: comprobar con SELECT count(*) FROM Fact_Accidente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
