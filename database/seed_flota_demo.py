"""
Flota demo minima y consistente, para reponer lo que retiro `higiene_datos.py`.

La higiene desactivo 10 unidades (restos de pruebas de humo y unidades apuntando a
un usuario que nunca existio), dejando la flota con una sola unidad. Este seed deja
una unidad por cada usuario con rol Unidad, correctamente ligada, para que el
despacho sea demostrable: sin `idusuario` valido la unidad no puede iniciar sesion
(CU-O30 `find_by_usuario`) y `mi-despacho` responde 403.

Tambien retira la fila centinela de Dim_Usuario_Cliente que quedo de una escritura
previa sin la columna de clave primaria (ver seed_soporte.py, ya corregido).

Idempotente: reescribe por clave primaria (upsert), no acumula.
"""
import json
import subprocess
import time
import urllib.request

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)

# Definicion de la flota, en orden. Cada entrada se liga al siguiente usuario que
# tenga rol Unidad: si se hardcodea el idusuario, un cambio en el catalogo de roles
# deja la unidad apuntando a alguien que ya no es unidad de campo y esa unidad no
# puede iniciar sesion (CU-O30 `find_by_usuario` -> 403 en mi-despacho).
#
# La tercera unidad vive en el condado vecino (2, Benito Juarez) a proposito: sin
# flota del otro lado, escalar a condados vecinos (CU-O34) siempre resolvia "sin
# unidades disponibles" aunque la consulta de adyacencia funcionara.
FLOTA = [
    {
        "idunidademergencia": 1,
        "unidademergencia": "Ambulancia 01",
        "placa": "TSI-001",
        "tipounidademergencia": "Ambulancia",
        "capacidad": "4",
        "latitud": 19.4326,
        "longitud": -99.1332,
        "idcondado": 1,
    },
    {
        "idunidademergencia": 2,
        "unidademergencia": "Grua 02",
        "placa": "TSI-002",
        "tipounidademergencia": "Grua",
        "capacidad": "2",
        "latitud": 19.4390,
        "longitud": -99.1400,
        "idcondado": 1,
    },
    {
        "idunidademergencia": 3,
        "unidademergencia": "Ambulancia 03",
        "placa": "TSI-003",
        "tipounidademergencia": "Ambulancia",
        "capacidad": "4",
        "latitud": 19.3910,
        "longitud": -99.1580,
        "idcondado": 2,
    },
]

ROL_UNIDAD = "Unidad"
ID_CLIENTE = 1


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


def main():
    # Usuarios que realmente tienen rol Unidad, resueltos por nombre de rol.
    roles_unidad = {
        r["idrol"]
        for r in query("SELECT idrol, rol, activo FROM Dim_Rol LIMIT 10000")
        if r["rol"] == ROL_UNIDAD and r.get("activo")
    }
    activos = {u["idusuario"] for u in query("SELECT idusuario, activo FROM Dim_Usuarios LIMIT 10000") if u.get("activo")}
    unidades_usuarios = sorted(
        {
            r["idusuario"]
            for r in query("SELECT idusuario, idrol FROM Dim_Usuario_Rol LIMIT 10000")
            if r["idrol"] in roles_unidad and r["idusuario"] in activos
        }
    )
    print(f"Usuarios con rol {ROL_UNIDAD}: {unidades_usuarios}")
    if len(unidades_usuarios) < len(FLOTA):
        print(f"  ! solo se sembraran {len(unidades_usuarios)} de {len(FLOTA)} unidades: "
              f"faltan usuarios con rol {ROL_UNIDAD}")

    unidades = []
    for datos, idusuario in zip(FLOTA, unidades_usuarios):
        unidades.append({
            **datos,
            "idusuario": idusuario,
            "idcliente": ID_CLIENTE,
            "tipopropiedad": "Propia",
            "contactoproveedor": "",
            "zonacobertura": None,
            "activo": True,
            "fecha_creacion": NOW_MS,
            "fecha_actualizacion": NOW_MS,
        })
    print(f"Flota demo: {len(unidades)} unidades")
    publish("Dim_UnidadEmergencia_topic", unidades)

    # Estado inicial "Activa" para que entren al algoritmo de despacho.
    # La forma del registro debe coincidir con la que escribe la aplicacion
    # (HistorialEstadoUnidadRepository.append_estado): el estado vigente se lee
    # de `estadonuevo`, no de `idestadounidademergencia`. Los ids arrancan
    # despues del maximo existente porque la tabla es upsert por clave primaria
    # y reusar un id pisaria historial real.
    maximo = query(
        "SELECT MAX(idhistorialestadosunidadesemergencias) AS max_id FROM Fact_HistorialEstadoUnidad"
    )
    siguiente = int((maximo[0].get("max_id") or 0)) + 1
    estados = []
    for offset, u in enumerate(unidades):
        estados.append({
            "idhistorialestadosunidadesemergencias": siguiente + offset,
            "idunidademergencia": u["idunidademergencia"],
            "idestadounidademergencia": 1,
            "estadoanterior": "Fuera de servicio",
            "estadonuevo": "Activa",
            "idusuario": u["idusuario"],
            "fechahora": NOW_MS,
            "fecha_actualizacion": NOW_MS,
            "activo": True,
        })
    publish("Fact_HistorialEstadoUnidad_topic", estados)

    # Retirar la fila centinela: se escribio sin `idusuariocliente`, asi que Pinot
    # la guardo bajo el minimo de INT como clave y convive con el vinculo real.
    huerfanas = [
        {**r, "activo": False, "fecha_actualizacion": NOW_MS}
        for r in query("SELECT * FROM Dim_Usuario_Cliente LIMIT 1000")
        if r.get("idusuariocliente") in (None, -2147483648)
    ]
    print(f"Vinculos usuario-cliente con clave centinela: {len(huerfanas)}")
    publish("Dim_Usuario_Cliente_topic", huerfanas)


if __name__ == "__main__":
    main()
