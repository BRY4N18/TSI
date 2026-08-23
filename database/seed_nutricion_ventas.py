"""Interacciones de demo y avisos al ejecutivo — las 4 pantallas secas de Ventas.

`Fact_Interaccion_Demo` y `Fact_NotificacionVentas` estaban **a cero en Pinot**:
nadie habia escrito nunca en ellas. Sin dato de origen, `hecho_interaccion_demo` y
`hecho_notificacion_ventas` salian vacios del modelo analitico y cuatro pantallas
de gestion no tenian nada que pintar:

| Pantalla | Necesita |
|---|---|
| `intensidad-demo` | Prospectos con **distinto** numero de eventos y de secciones |
| `secciones-visitadas` | Varias secciones, con una claramente mas visitada |
| `reglas-disparo` | Dos reglas con **tasas de acierto distintas** |
| `latencia-reaccion` | Avisos atendidos **y avisos ignorados**, para que haya mediana |

El vocabulario no se inventa
----------------------------
`tipo_evento` sale de `ingesta_interaccion_demo_service.TIPOS`, las reglas y sus
canales de `reglas_demo_catalog`, y `precios` es la seccion que dispara ambas.
Sembrar valores que el sistema no produce convierte el fixture en una afirmacion
sobre datos que nadie escribe — es el error del `"09:30"` de `hora_fin`.

⚠️ **Ninguna interaccion va sin seccion.** La consulta de secciones tiene un
`ifNull(nullIf(seccion, ''), 'sin seccion registrada')` defensivo, pero la
ingesta **exige** seccion y `demo_sesion_service` escribe `'demo'` hasta en el
inicio de sesion: una fila sin seccion no puede existir. Dejar esa rama sin
ejercitar es honesto; fabricarla seria inventar un caso imposible.

⚠️ El aviso ignorado importa mas que el atendido
-------------------------------------------------
`hecho_notificacion_ventas` deriva la reaccion como **el primer avance de etapa
posterior al aviso**, y si no hay ninguno deja `segundos_a_reaccion` **ausente**
con `hubo_avance = 0`. Contarlo como latencia cero haria que los peores casos
—los avisos que nadie atendio— *mejoraran* el indicador. Por eso aqui se siembran
las dos caras: sin ignorados, la regla que evita ese error no se ejerce.

Idempotente: reescribe por clave primaria (upsert), no acumula.
"""
import json
import subprocess
import time
import urllib.request

BROKER = "http://localhost:8099"
NOW_MS = int(time.time() * 1000)
SEGUNDO_MS = 1000
DIA_MS = 86_400_000

# ── Ids reservados ───────────────────────────────────────────────────────────
INTERACCION_BASE = 9500
NOTIFICACION_BASE = 9500

# ── Vocabulario canonico, importado de donde lo define el codigo ─────────────
#: `apps/ventas_crm/services/ingesta_interaccion_demo_service.TIPOS`
INICIO, CLICK, TIEMPO, FIN = "inicio_sesion", "click", "tiempo_seccion", "fin_sesion"
#: `apps/ventas_crm/services/reglas_demo_catalog`
REGLA_TIEMPO_PRECIOS = "tiempo_seccion_precios_5min"
REGLA_VISITO_PRICING = "visito_pricing_3x"
CANAL_POR_REGLA = {REGLA_TIEMPO_PRECIOS: "email", REGLA_VISITO_PRICING: "push"}

#: Sesiones de demo, en orden de intensidad decreciente. `intensidad-demo`
#: ordena por numero de eventos, asi que con todos iguales el listado no diria
#: nada: la pregunta que responde es **quien esta mirando mas**.
#:
#: `precios` se repite a proposito — es la seccion que dispara las dos reglas, y
#: la que `secciones-visitadas` debe destacar.
SESIONES = [
    (9001, [(INICIO, "demo"), (CLICK, "precios"), (TIEMPO, "precios"),
            (CLICK, "cobertura"), (TIEMPO, "cobertura"), (CLICK, "precios"),
            (CLICK, "integraciones"), (FIN, "demo")]),
    (9003, [(INICIO, "demo"), (CLICK, "precios"), (TIEMPO, "precios"),
            (CLICK, "cobertura"), (FIN, "demo")]),
    (9005, [(INICIO, "demo"), (CLICK, "precios"), (CLICK, "integraciones"),
            (FIN, "demo")]),
    (9002, [(INICIO, "demo"), (CLICK, "cobertura"), (FIN, "demo")]),
    # Entro y no volvio: un solo evento. Sin este, «intensidad» no tendria suelo.
    (9012, [(INICIO, "demo")]),
]

#: Avisos: `(idprospecto, regla, latencia_segundos_o_None)`.
#: `None` = **ignorado**, el caso que da sentido al indicador.
#:
#: Las latencias son 600, 3600 y 10800 para que la mediana caiga en 3600 y no
#: coincida con ningun extremo — una mediana igual al minimo no distingue una
#: mediana bien calculada de un `min()`.
AVISOS = [
    (9001, REGLA_TIEMPO_PRECIOS, 3600),
    (9003, REGLA_TIEMPO_PRECIOS, 600),
    (9005, REGLA_TIEMPO_PRECIOS, None),
    (9002, REGLA_VISITO_PRICING, 10800),
    (9006, REGLA_VISITO_PRICING, None),
]


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


def _transiciones_por_prospecto():
    filas = query(
        "SELECT id_prospecto, etapa_anterior, etapa_nueva, fecha_transicion "
        "FROM Fact_Pipeline LIMIT 100000"
    )
    por = {}
    for f in filas:
        por.setdefault(f["id_prospecto"], []).append(f)
    for lista in por.values():
        lista.sort(key=lambda f: f["fecha_transicion"])
    return por


def interacciones():
    """Una sesion por prospecto, con los eventos separados 90 s.

    Las sesiones se colocan en dias distintos y **recientes** para que caigan
    dentro de cualquier periodo que la pantalla ofrezca por defecto.
    """
    filas = []
    ident = INTERACCION_BASE
    for dias_atras, (idprospecto, eventos) in enumerate(SESIONES, start=3):
        inicio = NOW_MS - dias_atras * DIA_MS
        for n, (tipo, seccion) in enumerate(eventos):
            ident += 1
            filas.append({
                "idinteraccion": ident,
                "idprospecto": idprospecto,
                "tipo_evento": tipo,
                "seccion": seccion,
                # Libre y sin garantia de contenido; el cargador no lo copia.
                "metadata": "{}",
                "timestamp_evento": inicio + n * 90 * SEGUNDO_MS,
                "fecha_actualizacion": NOW_MS,
            })
    return filas


def notificaciones():
    """Avisos anclados a las transiciones **reales** de cada prospecto.

    Un aviso «con reaccion» se coloca `latencia` segundos **antes del primer
    avance** del prospecto: asi el avance que el cargador encuentra es
    exactamente ese, y la latencia sembrada es la que debe salir. Anclarlo a una
    fecha inventada dejaria la latencia a merced de que hubiera o no un avance
    cerca, que es justo lo que la prueba quiere fijar.

    Un aviso «ignorado» se coloca **un dia despues de la ultima transicion**: por
    construccion no puede haber ningun avance posterior.
    """
    por_prospecto = _transiciones_por_prospecto()
    filas = []
    ident = NOTIFICACION_BASE

    for idprospecto, regla, latencia in AVISOS:
        transiciones = por_prospecto.get(idprospecto, [])
        if not transiciones:
            print(f"  ! prospecto {idprospecto} sin transiciones: aviso omitido")
            continue

        if latencia is None:
            momento = transiciones[-1]["fecha_transicion"] + DIA_MS
            nota = "ignorado"
        else:
            momento = transiciones[0]["fecha_transicion"] - latencia * SEGUNDO_MS
            nota = f"reaccion en {latencia} s"

        ident += 1
        filas.append({
            "idnotificacion": ident,
            "id_prospecto": idprospecto,
            # No hay interaccion concreta detras de estos avisos sembrados.
            "idinteraccion": 0,
            # El cargador **no copia** este campo —es identidad de persona— pero
            # el esquema lo tiene y la aplicacion lo escribe.
            "idusuariogerentenotificado": 12,
            "regladisparada": regla,
            "canal": CANAL_POR_REGLA[regla],
            # ⚠️ Vacio a proposito: ningun codigo escribe `estado_envio`, y el
            # cargador no lo copia por eso mismo. Inventarlo aqui daria pie a un
            # informe de «envios fallidos» que no podria funcionar.
            "estado_envio": "",
            "fechahoranotificacion": momento,
            "fecha_actualizacion": NOW_MS,
        })
        print(f"     prospecto {idprospecto}: {regla} — {nota}")
    return filas


def main():
    print("Interacciones de demo")
    publish("Fact_Interaccion_Demo_topic", interacciones())

    print("Avisos al ejecutivo")
    publish("Fact_NotificacionVentas_topic", notificaciones())

    print("\nListo. Falta que Airflow cargue los dos hechos al modelo analitico.")


if __name__ == "__main__":
    main()
