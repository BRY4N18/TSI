"""Cuadre entre la capa analitica y la operacional (PG-ANA-001).

**El fallo que esto detecta no es un error: es un informe que miente.** ClickHouse
es una capa **derivada** — se alimenta de Pinot vía Airflow y nunca es fuente de
verdad. Si un DAG carga de menos, la consulta responde igual de rápido, el
informe se pinta igual de bien, y los números son sencillamente otros. Nadie
recibe un error; alguien firma un documento.

Es el peor modo de fallo del sistema porque no tiene sintoma. Un `500` se ve; un
informe con el 80 % de los casos se entrega.

**Por que un modulo declarativo y no una prueba por tabla.** Hay 20 tablas de
hechos y cada una tendria su prueba a mano, que envejeceria por separado. Aqui la
correspondencia se declara una vez y las pruebas la recorren: una tabla nueva sin
entrada queda **señalada**, en vez de quedarse sin cuadrar en silencio.

⚠️ **Esto solo se puede comprobar contra motores reales.** Un doble de Pinot
devuelve lo que se le programo, asi que cuadraria consigo mismo siempre. Las
pruebas que lo usan estan marcadas `integration`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Correspondencia:
    """Como se cuadra una tabla analitica contra su origen operacional."""

    #: Tabla de ClickHouse (modelo analitico, minusculas).
    analitica: str
    #: Tabla de Pinot que la alimenta (modelo dimensional, `Fact_*`/`Dim_*`).
    operacional: str
    #: Clave de grano, **con nombre propio en cada lado**. No es redundancia:
    #: `hecho_sesion.idsesion` corresponde a `Fact_Session.idsession`, y
    #: `hecho_llamada_api.idlog` a `Fact_LogLlamadaAPI.idlogllamadaapi`. Un solo
    #: campo produciria discrepancias falsas por un nombre, no por un dato — y
    #: una suite con falsos positivos se desactiva en cuanto estorba.
    #:
    #: El conteo va sobre valores **distintos**: `COUNT(*)` daria falsos
    #: negativos en tablas que agregan y falsos positivos si el origen tiene
    #: duplicados por upsert.
    clave_analitica: str
    clave_operacional: str
    #: Columna de fecha en cada lado. No coinciden: Pinot guarda epoch ms y
    #: ClickHouse un `Date` ya truncado.
    fecha_operacional: str
    fecha_analitica: str = "fecha"
    #: Medidas numericas cuya suma debe coincidir, como pares
    #: `(nombre_operacional, nombre_analitico)`. Los dos lados usan convenciones
    #: distintas —`numvehiculos` en Pinot, `num_vehiculos` en ClickHouse— y es
    #: justo lo que hace que «comparar los numeros» sea mas dificil de lo que
    #: parece: media docena de columnas se llaman casi igual pero no igual.
    #:
    #: Un conteo que cuadra con sumas que no cuadran significa que estan todas
    #: las filas con los valores cambiados. Ese caso un informe no lo delata de
    #: ninguna forma: el numero de casos es correcto y los heridos no.
    medidas: tuple[tuple[str, str], ...] = field(default=())
    #: Tolerancia de filas. Cero salvo justificacion escrita: si una tabla
    #: necesita margen, el motivo va aqui y no en el aserto.
    tolerancia: int = 0
    #: Por que esta tabla admite tolerancia, si la admite.
    nota: str = ""
    #: Condicion extra sobre el lado analitico. Necesaria cuando una tabla de
    #: hechos **mezcla varios origenes**: `hecho_evidencia` guarda fotos y notas
    #: juntas, asi que contarla entera contra `Dim_EvidenciaFoto` da mas filas de
    #: las que hay — y parece un duplicado cuando es otra cosa.
    filtro_analitico: str = ""


#: Columna de marca de carga. La escriben todos los `hecho_*` del modelo.
COLUMNA_CARGA = "cargado_en"


def sql_frescura_analitica(c: "Correspondencia") -> str:
    """Instante de la ultima carga real, **no** la fecha del dato mas reciente.

    La distincion no es sutil y costo un diagnostico equivocado. `fecha` es la
    fecha de **negocio** —emision de la factura, inicio de la suscripcion— y
    puede estar en el futuro: `hecho_suscripcion` tiene contratos que empiezan
    dentro de tres meses, asi que medir frescura con ella daba «-100 dias de
    antiguedad» y la tabla pasaba el control sin haberse cargado nunca.

    `cargado_en` responde a la pregunta que importa: *cuando corrio el DAG*.

    Separa **dos fallos que se ven igual** y se arreglan distinto:

    - *Desfase de carga*: el DAG no ha corrido y faltan los dias recientes. El
      ETL esta bien; lo que falla es que nadie lo ejecuto.
    - *Discrepancia real*: el periodo esta cargado y aun asi los numeros no
      coinciden. Ahi si hay un defecto.

    Sin esta distincion, un «faltan 193» manda a depurar una transformacion
    correcta durante horas.
    """
    return f"SELECT max({COLUMNA_CARGA}) AS ultima FROM {c.analitica}"


#: Las 20 tablas de hechos del modelo analitico, con su origen operacional.
#:
#: Los nombres de clave y de fecha **no se adivinaron**: salen de cruzar
#: `dags/lib/ddl.py` con `database/esquemas.json`. Adivinarlos habria producido
#: discrepancias por un nombre mal escrito en vez de por un dato mal cargado, y
#: nadie distingue una cosa de la otra leyendo un fallo.
#:
#: Anadir una entrada es barato; **no anadirla es lo que cuesta**, porque la
#: tabla queda fuera del cuadre sin que nada lo diga.
CORRESPONDENCIAS: tuple[Correspondencia, ...] = (
    Correspondencia(
        analitica="hecho_accidente",
        operacional="Fact_Accidente",
        clave_analitica="idaccidente",
        clave_operacional="idaccidente",
        fecha_operacional="fechahoraaccidente",
        medidas=(
            ("numvehiculos", "num_vehiculos"),
            ("numvictimas", "num_victimas"),
            ("numheridos", "num_heridos"),
            ("numfallecidos", "num_fallecidos"),
        ),
    ),
    Correspondencia(
        analitica="hecho_despacho",
        operacional="Fact_Despacho",
        clave_analitica="iddespacho",
        clave_operacional="iddespacho",
        fecha_operacional="fechahoradespacho",
    ),
    Correspondencia(
        analitica="hecho_ticket",
        operacional="Fact_Reclamo",
        clave_analitica="id_reclamo",
        clave_operacional="id_reclamo",
        fecha_operacional="fechahora",
    ),
    Correspondencia(
        analitica="hecho_accion_ticket",
        operacional="Fact_Historial_Ticket",
        clave_analitica="id_historial",
        clave_operacional="id_historial",
        fecha_operacional="fecha_accion",
    ),
    Correspondencia(
        analitica="hecho_sesion",
        operacional="Fact_Session",
        clave_analitica="idsesion",
        clave_operacional="idsession",
        fecha_operacional="fechahorainiciosesion",
    ),
    Correspondencia(
        analitica="hecho_onboarding",
        operacional="Fact_Onboarding",
        clave_analitica="idonboarding",
        clave_operacional="id_onboarding",
        fecha_operacional="fecha_completado",
    ),
    Correspondencia(
        analitica="hecho_llamada_api",
        operacional="Fact_LogLlamadaAPI",
        clave_analitica="idlog",
        clave_operacional="idlogllamadaapi",
        fecha_operacional="fechallamada",
    ),
    Correspondencia(
        analitica="hecho_cambio_acceso",
        operacional="Fact_HistorialAccesoPartner",
        clave_analitica="idhistorial",
        clave_operacional="idhistorial",
        fecha_operacional="fecha_cambio",
    ),
    Correspondencia(
        analitica="hecho_suscripcion",
        operacional="Fact_Suscripcion",
        clave_analitica="id_suscripcion",
        clave_operacional="id_suscripcion",
        fecha_operacional="fecha_inicio",
    ),
    Correspondencia(
        analitica="hecho_factura",
        operacional="Fact_Factura",
        clave_analitica="id_factura",
        clave_operacional="id_factura",
        fecha_operacional="fecha_emision",
        medidas=(("monto_total", "monto_total"),),
    ),
    Correspondencia(
        analitica="hecho_solicitud_cambio_plan",
        operacional="Fact_Solicitud_Cambio_Plan",
        clave_analitica="idsolicitud",
        clave_operacional="idsolicitud",
        fecha_operacional="fecha_solicitud",
    ),
    Correspondencia(
        analitica="hecho_transicion_embudo",
        operacional="Fact_Pipeline",
        clave_analitica="idtransicion",
        clave_operacional="id_transicion",
        fecha_operacional="fecha_transicion",
    ),
    Correspondencia(
        analitica="hecho_asignacion_prospecto",
        operacional="Fact_Asignacion",
        clave_analitica="idasignacion",
        clave_operacional="idasignacion",
        fecha_operacional="fechahoraasignacion",
    ),
    Correspondencia(
        analitica="hecho_notificacion_ventas",
        operacional="Fact_NotificacionVentas",
        clave_analitica="idnotificacion",
        clave_operacional="idnotificacion",
        fecha_operacional="fechahoranotificacion",
    ),
    Correspondencia(
        analitica="hecho_baja_unidad",
        operacional="Fact_BajaUnidad",
        clave_analitica="idbaja",
        clave_operacional="idbajaunidad",
        fecha_operacional="fechahora",
    ),
    Correspondencia(
        analitica="hecho_validacion_region",
        operacional="Dim_ValidacionRegion",
        clave_analitica="idvalidacion",
        clave_operacional="idvalidacionregion",
        fecha_operacional="fechahora",
    ),
    # `hecho_evidencia` guarda **fotos y notas en la misma tabla**, asi que se
    # cuadra en dos mitades. Contarla entera contra `Dim_EvidenciaFoto` daba
    # «sobran 49», que parece un duplicado y es simplemente otra cosa dentro.
    Correspondencia(
        analitica="hecho_evidencia",
        operacional="Dim_EvidenciaFoto",
        clave_analitica="idevidencia",
        clave_operacional="idevidenciafoto",
        fecha_operacional="fechahora",
        filtro_analitico="tipo = 'foto'",
    ),
    Correspondencia(
        analitica="hecho_evidencia",
        operacional="Dim_NotaAccidente",
        clave_analitica="idevidencia",
        clave_operacional="idnotaaccidentes",
        fecha_operacional="fechahora",
        filtro_analitico="tipo != 'foto'",
    ),
    Correspondencia(
        analitica="hecho_estado_unidad",
        operacional="Fact_HistorialEstadoUnidad",
        clave_analitica="idhistorial",
        clave_operacional="idhistorialestadosunidadesemergencias",
        fecha_operacional="fechahora",
    ),
    Correspondencia(
        analitica="hecho_ping_unidad",
        operacional="Dim_HistorialUbicacionUnidadEmergencia",
        clave_analitica="idping",
        clave_operacional="idhistorialunidademergencia",
        fecha_operacional="fechahora",
    ),
    Correspondencia(
        analitica="hecho_interaccion_demo",
        operacional="Fact_Interaccion_Demo",
        clave_analitica="idinteraccion",
        clave_operacional="idinteraccion",
        fecha_operacional="fecha_actualizacion",
    ),
)

#: Tope de extraccion de los DAGs (`dags/lib/hechos/*.py::LIMITE`). Importa aqui
#: porque **es el modo de fallo mas probable de todos**: cuando el origen supera
#: el limite, la extraccion trunca sin avisar y el cuadre pasa a fallar por una
#: razon que no es un error de codigo. Ver `PG-OPE-006`.
LIMITE_EXTRACCION = 500_000


def sql_conteo_operacional(c: Correspondencia, desde_ms: int, hasta_ms: int) -> str:
    """Conteo de claves distintas en Pinot para la ventana dada."""
    return (
        f"SELECT COUNT(DISTINCT {c.clave_operacional}) AS total FROM {c.operacional} "
        f"WHERE {c.fecha_operacional} >= {desde_ms} "
        f"AND {c.fecha_operacional} <= {hasta_ms} "
        f"LIMIT 1"
    )


def sql_conteo_analitico(c: Correspondencia, desde: str, hasta: str) -> str:
    """Conteo de claves distintas en ClickHouse para la misma ventana."""
    extra = f" AND {c.filtro_analitico}" if c.filtro_analitico else ""
    return (
        f"SELECT COUNT(DISTINCT {c.clave_analitica}) AS total FROM {c.analitica} "
        f"WHERE {c.fecha_analitica} >= toDate('{desde}') "
        f"AND {c.fecha_analitica} <= toDate('{hasta}'){extra}"
    )


def sql_medidas_operacional(c: Correspondencia, desde_ms: int, hasta_ms: int) -> str:
    # El alias usa el nombre **analitico** en los dos lados para que las dos
    # respuestas lleguen con las mismas claves y se puedan comparar directamente.
    campos = ", ".join(f"SUM({op}) AS {an}" for op, an in c.medidas)
    return (
        f"SELECT {campos} FROM {c.operacional} "
        f"WHERE {c.fecha_operacional} >= {desde_ms} "
        f"AND {c.fecha_operacional} <= {hasta_ms} "
        f"LIMIT 1"
    )


def sql_medidas_analitico(c: Correspondencia, desde: str, hasta: str) -> str:
    # ⚠️ Los alias repiten el nombre de la columna a proposito para que ambos
    # lados devuelvan las mismas claves. En ClickHouse eso es seguro dentro de un
    # SUM(); lo que rompe es aliasar una columna con su propio nombre **sin**
    # agregar, que produce ILLEGAL_AGGREGATION (PG-ANA-005).
    campos = ", ".join(f"SUM({an}) AS {an}" for _op, an in c.medidas)
    return (
        f"SELECT {campos} FROM {c.analitica} "
        f"WHERE {c.fecha_analitica} >= toDate('{desde}') "
        f"AND {c.fecha_analitica} <= toDate('{hasta}')"
    )


def discrepancia(operacional: int, analitico: int, c: Correspondencia) -> str | None:
    """Mensaje de fallo, o `None` si cuadra dentro de la tolerancia."""
    diferencia = abs(operacional - analitico)
    if diferencia <= c.tolerancia:
        return None

    sentido = "faltan" if analitico < operacional else "sobran"
    aviso = ""
    if operacional >= LIMITE_EXTRACCION:
        aviso = (
            f" ⚠️ El origen alcanza el tope de extraccion ({LIMITE_EXTRACCION}): "
            "la carga pudo truncarse sin avisar, que es un fallo del ETL y no del cuadre."
        )
    return (
        f"{c.analitica} no cuadra con {c.operacional}: {operacional} en origen, "
        f"{analitico} en analitica — {sentido} {diferencia}.{aviso}"
    )
