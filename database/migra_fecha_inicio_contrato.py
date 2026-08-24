"""Rellena `Dim_Cliente.fecha_inicio_contrato` en las cuentas anteriores al arreglo.

Desde el 2026-08-23 la aprobación de una cuenta sella el inicio del contrato
(`aprobacion_proveedor_service`). Las cuentas aprobadas **antes** de ese cambio
se quedaron con el centinela, y con ellas tres informes de gestión de Cuentas:
antigüedad media, churn por cohorte y tasa de aprobación no tenían de dónde
calcular.

De dónde sale la fecha, y por qué
---------------------------------
No hay ninguna fecha de aprobación guardada: ni `fecha_creacion` —también
centinela en todas las cuentas reales— ni ningún historial de la decisión. Lo
más cercano que sí existe es **el inicio de la primera suscripción**, que es la
primera evidencia de que la cuenta operaba comercialmente.

⚠️ **Es un sustituto, no el dato.** Una cuenta pudo aprobarse días antes de
contratar, así que la antigüedad calculada será **por defecto**, nunca por
exceso. Se prefiere eso a inventar `today()` —que daría antigüedad cero a
cuentas de dos años— o a dejar el centinela, que es lo que rompía los informes.

⛔ **No toca las cuentas que ya tienen fecha.** Ni las aprobadas tras el arreglo
ni las sembradas: reescribir una fecha real con una estimada sería perder dato.

⛔ **No inventa fecha para quien no tiene suscripción.** Una cuenta rechazada o
sin contratar nunca empezó un contrato, y ponerle uno la haría aparecer en la
antigüedad media como si fuera cliente. Se quedan con el centinela y se informa
de cuántas son.

Idempotente: reejecutar no cambia nada, porque las filas ya rellenas se saltan.
"""
import argparse
import json
import os
import subprocess
import time
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _reversion import anadir_dry_run, respaldar

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)

#: Pinot no tiene NULL: una columna LONG sin valor llega con el mínimo de INT64.
CENTINELA = -9223372036854775808


def query(sql):
    req = urllib.request.Request(
        f"{BROKER}/query/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={"Content-Type": "application/json"},
    )
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("exceptions"):
        raise RuntimeError(f"Pinot: {d['exceptions']}")
    rt = d.get("resultTable")
    if not rt:
        return []
    return [dict(zip(rt["dataSchema"]["columnNames"], r)) for r in rt["rows"]]


def publish(topic, records):
    if not records:
        return
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    proc = subprocess.run(
        ["docker", "exec", "-i", "kafka", "kafka-console-producer",
         "--bootstrap-server", "localhost:9092", "--topic", topic],
        input=payload.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Error publicando en {topic}: {proc.stderr.decode()}")
    print(f"  -> {len(records)} cuenta(s) actualizada(s) en {topic}")


def _tiene_fecha(valor):
    return valor is not None and int(valor) > CENTINELA and int(valor) > 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    anadir_dry_run(parser)
    args = parser.parse_args()

    clientes = query("SELECT * FROM Dim_Cliente LIMIT 10000")

    # La fila se republica entera (la tabla es upsert por clave), asi que sin
    # copia previa un error en la fecha estimada enterraria el estado anterior
    # de **todas** las columnas, no solo de la que se pretendia tocar.
    respaldo = respaldar("Dim_Cliente", clientes, sufijo="fecha_inicio_contrato")
    print(f"Respaldo verificado -> {respaldo.name}")
    primeras = {
        int(f["idcliente"]): int(f["primera"])
        for f in query(
            "SELECT idcliente, MIN(fecha_inicio) AS primera FROM Fact_Suscripcion "
            "GROUP BY idcliente LIMIT 10000"
        )
        if f.get("primera") is not None and int(f["primera"]) > CENTINELA
    }

    a_escribir, ya_tenian, sin_suscripcion = [], 0, []
    for c in clientes:
        cid = int(c["idcliente"])
        if _tiene_fecha(c.get("fecha_inicio_contrato")):
            ya_tenian += 1
            continue
        primera = primeras.get(cid)
        if primera is None:
            sin_suscripcion.append(c.get("razon_social") or cid)
            continue
        # ⚠️ Se reescribe la fila entera porque la tabla es upsert por clave:
        # publicar solo el campo dejaria el resto en su valor por defecto.
        a_escribir.append({
            **c,
            "fecha_inicio_contrato": primera,
            "fecha_actualizacion": NOW_MS,
        })

    print(f"Cuentas totales           : {len(clientes)}")
    print(f"  ya tenian fecha         : {ya_tenian}")
    print(f"  se rellenan             : {len(a_escribir)}")
    print(f"  sin suscripcion (se deja): {len(sin_suscripcion)}")
    for nombre in sin_suscripcion:
        print(f"      - {nombre}")

    publish("Dim_Cliente_topic", a_escribir)
    print("\nListo. Falta recargar `dim_cliente` en el modelo analitico.")


if __name__ == "__main__":
    main()
