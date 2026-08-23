"""Un segundo estado geografico, para que la region de un condado deje de ser ambigua.

Por que hace falta un estado entero
-----------------------------------
`dim_geografia` deja la region del condado **ausente a proposito** cuando el
estado tiene mas de una region: hoy todas comparten `idestado = 1`, y elegir una
daria «una cifra que nadie cuestiona porque no parece rota». La decision esta
documentada en el cargador y es correcta.

La consecuencia es que **ningun accidente puede atribuirse a una region**, y
varios informes de Red Operativa se quedan sin poder nombrarla.

Este seed crea un estado con **una sola region**, de modo que la atribucion
condado -> region sea inequivoca.

⛔ Esto NO desbloquea `casos-activos-al-despublicar`
----------------------------------------------------
Se escribio creyendo que la geografia era lo que faltaba. **No lo era.** El
informe filtra `WHERE despublicada_en IS NOT NULL`, y esa fecha solo existe si la
version de la region lleva `inicio_es_real = 1` — la marca que distingue «se sabe
cuando ocurrio el cambio» de «es desde que empezamos a mirar».

`versionado.decidir_version` exige que **quien llama aporte el instante**, y solo
puede salir de una tabla de historial del origen. `dim_region.construir` no lo
aporta, y no puede: nada historiza cuando se despublico una region.
`Dim_ValidacionRegion` guarda `Aprobada`/`Rechazada` —el resultado de validar, no
una despublicacion— y `Dim_RegionOperativaEstadoRegion` es una tabla de enlace
que se sobrescribe, no un historial. Las 8 filas de `dim_region` llevan
`inicio_es_real = 0`, y siempre lo llevaran.

**Lo que este seed si arregla** es la atribucion condado -> region, que estaba
ausente para todos los condados y que usan otros informes: `cobertura-flota-por-
region` pasa a nombrar una region real en vez de solo «Sin region asignada», y
`condados-cobertura-critica` ve el condado nuevo.

Dos fases, porque la despublicacion es un CAMBIO observado
-----------------------------------------------------------
`dim_region` versiona por `estado_ciclo_vida`, y **la primera version de toda
region lleva `inicio_es_real = 0`**: se conoce el estado, no desde cuando lo es.
El informe exige `inicio_es_real = 1`, es decir, una transicion que el cargador
haya visto **entre dos ejecuciones**.

Por eso la region nace en `Produccion`, se carga, se despublica y se vuelve a
cargar. Sembrarla despublicada de golpe dejaria `despublicada_en` nulo y el
informe seguiria vacio — con la geografia ya arreglada, que es el peor sitio
donde quedarse a medias.

    python database/seed_segundo_estado_geografico.py            # fase 1
    # (recargar dimensiones)
    python database/seed_segundo_estado_geografico.py --despublicar   # fase 2
    # (recargar dimensiones y hecho_accidente)

Idempotente: reescribe por clave primaria (upsert), no acumula.
"""
import json
import subprocess
import sys
import time
import urllib.request

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)
DIA_MS = 86_400_000

# ── Ids reservados ───────────────────────────────────────────────────────────
ID_PAIS = 1
ID_ESTADO = 9201
ID_CONDADO = 9201
ID_CIUDAD = 9201
ID_CALLES = (9201, 9202)
ID_REGION = 9201

#: Literales canonicos de `informes_region_repository`.
ESTADO_PRODUCCION = "Producción"
ESTADO_DESPUBLICADA = "Despublicada"

#: `Dim_Severidad`. Se usan las dos que el informe cuenta aparte.
SEVERIDAD_GRAVE = 3
SEVERIDAD_FATAL = 4
SEVERIDAD_LEVE = 1


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
    print(f"  -> {len(records)} registro(s) en {topic}")


def _region(estado_region):
    return [{
        "idregionoperativa": ID_REGION,
        "idestado": ID_ESTADO,
        "nombreregion": "Costa Oriente",
        "estadoregion": estado_region,
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    }]


def geografia():
    """El estado, su condado, su ciudad y dos calles.

    ⚠️ **Una sola region en este estado**, que es el punto entero: con dos, el
    cargador volveria a dejar la region del condado ausente y no habriamos
    arreglado nada.
    """
    estado = [{
        "idestado": ID_ESTADO,
        "estado": "Veracruz",
        "idpais": ID_PAIS,
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    }]
    condado = [{
        "idcondado": ID_CONDADO,
        "condado": "Boca del Rio",
        "idestado": ID_ESTADO,
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    }]
    ciudad = [{
        "idciudad": ID_CIUDAD,
        "ciudad": "Boca del Rio Centro",
        "idcondado": ID_CONDADO,
        "activo": True,
        "fecha_actualizacion": NOW_MS,
    }]
    calles = [
        {
            "idcalle": idcalle,
            "calle": nombre,
            "idciudad": ID_CIUDAD,
            "activo": True,
            "fecha_actualizacion": NOW_MS,
        }
        for idcalle, nombre in zip(ID_CALLES, ("Av. Ruiz Cortines", "Blvd. Costero"))
    ]
    return estado, condado, ciudad, calles


#: Accidentes de la region. `hora_cierre` sale del historial de estados, y estos
#: no tienen ninguno: quedan **abiertos**, que es lo que el informe cuenta.
#:
#: Se mezclan severidades a proposito: el informe separa `casos_graves` de
#: `casos_activos`, y con todos graves esa distincion no se veria.
ACCIDENTES = [
    (ID_CALLES[0], SEVERIDAD_FATAL, "Volcadura en el distribuidor", 3),
    (ID_CALLES[0], SEVERIDAD_GRAVE, "Alcance multiple en hora pico", 5),
    (ID_CALLES[1], SEVERIDAD_GRAVE, "Choque contra parapeto", 9),
    (ID_CALLES[1], SEVERIDAD_LEVE, "Roce lateral sin heridos", 12),
]


def accidentes():
    filas = []
    for n, (idcalle, idseveridad, descripcion, dias) in enumerate(ACCIDENTES):
        momento = NOW_MS - dias * DIA_MS
        filas.append({
            "idaccidente": f"ACC-BORDE-{ID_REGION}-{n + 1}",
            "idcalle": idcalle,
            "idseveridad": idseveridad,
            "idusuario": 10,
            "idtiporeportado": 1,
            "idreferenciaestacion": -2147483648,
            "idaccidenteorigen": "null",
            # ⚠️ Sin hora de fin y sin historial de cierre: el caso sigue
            # **abierto**, que es justo lo que el informe cuenta dentro de una
            # region que alguien esta a punto de despublicar.
            "horainicio": "null",
            "horafin": "null",
            "descripcion": descripcion,
            "codigopostal": "94290",
            "activo": True,
            "duracionminutos": 0,
            "numvehiculos": 2,
            "numvictimas": 1 if idseveridad >= SEVERIDAD_GRAVE else 0,
            "numheridos": 1 if idseveridad >= SEVERIDAD_GRAVE else 0,
            "numfallecidos": 1 if idseveridad == SEVERIDAD_FATAL else 0,
            "latitudinicio": 19.1058 + n * 0.001,
            "longitudinicio": -96.1064 + n * 0.001,
            "distanciamillas": 0.0,
            "fechahoraaccidente": momento,
            "fecha_actualizacion": NOW_MS,
        })
    return filas


def fase_uno():
    estado, condado, ciudad, calles = geografia()
    print("Geografia")
    publish("Dim_Estado_topic", estado)
    publish("Dim_Condado_topic", condado)
    publish("Dim_Ciudad_topic", ciudad)
    publish("Dim_Calle_topic", calles)

    print("Region, en Produccion")
    publish("Dim_RegionOperativa_topic", _region(ESTADO_PRODUCCION))

    print("Accidentes abiertos")
    publish("Fact_Accidente_topic", accidentes())

    print(
        "\nFase 1 lista. Ahora **recarga las dimensiones** y vuelve con"
        " `--despublicar`:\n"
        "  la primera version de la region debe existir antes de que el cambio"
        " a Despublicada\n  pueda observarse como transicion real."
    )


def fase_dos():
    vigente = query(
        f"SELECT estadoregion FROM Dim_RegionOperativa "
        f"WHERE idregionoperativa = {ID_REGION} LIMIT 1"
    )
    if not vigente:
        raise SystemExit(
            "La region no existe todavia: ejecuta primero la fase 1 y recarga"
            " las dimensiones."
        )
    print(f"Region actualmente en '{vigente[0].get('estadoregion')}' -> Despublicada")
    publish("Dim_RegionOperativa_topic", _region(ESTADO_DESPUBLICADA))
    print(
        "\nFase 2 lista. Recarga dimensiones y `hecho_accidente`:\n"
        "  la segunda version llevara `inicio_es_real = 1`, que es lo que el"
        " informe exige."
    )


if __name__ == "__main__":
    if "--despublicar" in sys.argv:
        fase_dos()
    else:
        fase_uno()
