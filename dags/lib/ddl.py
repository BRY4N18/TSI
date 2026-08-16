"""DDL idempotente del modelo analítico táctico (contracts/esquema-analitico.md).

Cada flujo llama a `ensure_*` al inicio de su corrida: `CREATE TABLE IF NOT
EXISTS` es seguro de repetir.

Dos bloques conviven a propósito
--------------------------------
1. **El modelo** — 5 dimensiones y 2 hechos de la primera fase.
2. **Las tres tablas por informe** del diseño anterior, al final del fichero.

Las segundas **no se borran todavía**. Se retiran en la fase 6 del módulo, y solo
cuando las consultas equivalentes sobre el modelo devuelvan las mismas cifras que
ellas (research D7). Retirarlas antes dejaría al sistema sin esos tres informes y
sin forma de comparar.

Dos convenciones que no son decorativas
---------------------------------------
**La ausencia se escribe `Nullable`, nunca 0 ni una fecha centinela.** Un hito no
alcanzado guardado como fecha cero convertiría todos los casos abiertos en
cerrados en 1970, y ningún promedio de duración volvería a ser creíble.

**Los hechos van particionados por mes.** No es una optimización: es lo que
permite recargar un período descartando su partición en vez de borrar filas por
condición, que en este almacén es una mutación (research D3).
"""

from __future__ import annotations

from lib.clickhouse_http_client import execute_clickhouse

# ───────────────────────────── Dimensiones ──────────────────────────────


def ensure_dim_tiempo() -> None:
    """Una fila por día. **Se genera, no se extrae** de ningún origen."""
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_tiempo (
            fecha            Date,
            anio             UInt16,
            trimestre        UInt8,
            mes              UInt8,
            nombre_mes       String,
            semana_iso       UInt8,
            dia_del_mes      UInt8,
            dia_semana       UInt8,
            nombre_dia       String,
            es_fin_de_semana UInt8,
            version          DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY fecha
        """
    )


def ensure_dim_geografia() -> None:
    """Una fila por calle **con sus ascendientes aplanados**.

    Agrupar por condado es así una columna y no tres saltos. Sin coordenadas:
    la ubicación se expresa por nombre (exclusión del §5 del contrato).
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_geografia (
            idcalle      Int32,
            calle        String,
            idciudad     Int32,
            ciudad       String,
            idcondado    Int32,
            condado      String,
            idestado     Int32,
            estado       String,
            idpais       Int32,
            pais         String,
            version      DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idcalle
        """
    )


def ensure_dim_severidad() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_severidad (
            idseveridad  Int32,
            severidad    String,
            descripcion  Nullable(String),
            orden        UInt8,
            version      DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idseveridad
        """
    )


def ensure_dim_origen_despacho() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_origen_despacho (
            idorigendespacho Int32,
            origen           String,
            version          DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY idorigendespacho
        """
    )


def ensure_dim_unidad() -> None:
    """Una fila por **versión** de unidad, no por unidad.

    Es la dimensión que resuelve la atribución histórica: dos despachos de la
    misma unidad en épocas distintas apuntan a `sk_unidad` distintos, y por eso
    cada uno conserva su proveedor correcto.

    `inicio_es_real = 0` marca que la fecha de inicio **no es un cambio
    observado** sino el momento en que el modelo empezó a mirar. Para la unidad
    lo será siempre: nada en el origen historiza el cambio de proveedor.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS dim_unidad (
            sk_unidad          UInt64,
            idunidademergencia Int32,
            placa              String,
            nombre_unidad      Nullable(String),
            tipo_unidad        Nullable(String),
            capacidad          Nullable(Int32),
            idcliente          Int32,
            proveedor          String,
            idcondado          Nullable(Int32),
            condado            Nullable(String),
            zona_cobertura     Nullable(String),
            valido_desde       DateTime,
            valido_hasta       Nullable(DateTime),
            es_vigente         UInt8,
            inicio_es_real     UInt8,
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY (idunidademergencia, valido_desde)
        """
    )


# ─────────────────────────────── Hechos ─────────────────────────────────


def ensure_hecho_accidente() -> None:
    """Instantánea acumulada. **Grano: un caso registrado.**

    Los tiempos del proceso son restas de esta misma fila, sin uniones y sin
    ordenar. Un hito no alcanzado va `NULL`.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_accidente (
            idaccidente             String,
            fecha                   Date,
            fechahora_accidente     DateTime,
            franja_horaria          String,

            idcalle                 Nullable(Int32),
            condado                 Nullable(String),
            ciudad                  Nullable(String),
            idseveridad             Nullable(Int32),
            severidad               Nullable(String),
            tipo_reportado          Nullable(String),

            hora_confirmacion       Nullable(DateTime),
            hora_primera_asignacion Nullable(DateTime),
            hora_primera_llegada    Nullable(DateTime),
            hora_cierre             Nullable(DateTime),

            num_vehiculos           Nullable(Int32),
            num_heridos             Nullable(Int32),
            num_victimas            Nullable(Int32),
            num_fallecidos          Nullable(Int32),
            duracion_minutos        Nullable(Int32),
            total_intentos_despacho Nullable(Int32),
            num_evidencias          Nullable(Int32),

            fue_descartado          UInt8,
            es_duplicado            UInt8,
            duplicado_de            Nullable(String),

            cargado_en              DateTime,
            version                 DateTime
        ) ENGINE = ReplacingMergeTree(version)
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idaccidente)
        """
    )


def ensure_hecho_despacho() -> None:
    """Instantánea acumulada. **Grano: un intento de asignación a una unidad.**

    `proveedor` es el de la versión vigente **al despachar**. Copiar el actual
    reintroduciría el defecto que este modelo existe para corregir.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_despacho (
            iddespacho         Int32,
            idaccidente        String,
            fecha              Date,
            fechahora_despacho DateTime,

            sk_unidad          UInt64,
            idunidademergencia Int32,
            unidad             String,
            proveedor          String,
            idorigendespacho   Int32,
            origen_despacho    String,
            idseveridad        Nullable(Int32),
            severidad          Nullable(String),
            condado            Nullable(String),

            hora_confirmacion  Nullable(DateTime),
            hora_rechazo       Nullable(DateTime),
            hora_llegada       Nullable(DateTime),
            hora_retiro        Nullable(DateTime),

            segundos_respuesta Nullable(Int32),
            segundos_transito  Nullable(Int32),
            segundos_atencion  Nullable(Int32),

            numero_intento     UInt8,
            resultado          String,
            motivo_rechazo     Nullable(String),
            retiro_forzado     UInt8,

            cargado_en         DateTime,
            version            DateTime
        ) ENGINE = ReplacingMergeTree(version)
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idaccidente, iddespacho)
        """
    )


def ensure_hecho_ping_unidad() -> None:
    """Hecho de **transacción**. Grano: una posición reportada por una unidad.

    Es el hecho más voluminoso del modelo —59 045 filas hoy y creciendo con cada
    seguimiento— y el que sostiene el informe de pérdida de señal: los huecos se
    detectan comparando instantes consecutivos de la misma unidad.

    ⚠️ **Sin latitud ni longitud.** El origen las trae y **no se copian**: la
    pérdida de señal se calcula con los instantes, no con las posiciones. Es el
    caso que mejor ilustra la exclusión del §5 — la utilidad analítica no
    requiere el dato sensible, así que el dato sensible no entra.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_ping_unidad (
            idping             Int32,
            fecha              Date,
            fechahora          DateTime,

            sk_unidad          UInt64,
            idunidademergencia Int32,
            proveedor          String,
            idaccidente        Nullable(String),

            segundos_desde_anterior Nullable(Int32),

            cargado_en         DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idunidademergencia, fechahora)
        """
    )


def ensure_hecho_estado_unidad() -> None:
    """Hecho de **transacción**. Grano: un cambio de estado registrado.

    Es el tercer hecho del modelo, y el primero que no es una instantánea
    acumulada. Por eso usa `MergeTree` y no el motor con deduplicación: una fila
    de transacción **no se actualiza nunca** —el suceso ya ocurrió— y las
    consultas sobre esta tabla no necesitan forzar versión final. La idempotencia
    la da el descarte de partición, no el motor.

    `idusuario` **no se copia**, aunque el origen lo trae: analizar la
    disponibilidad de la flota no requiere saber quién movió cada estado.
    """
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS hecho_estado_unidad (
            idhistorial                  Int32,
            fecha                        Date,
            fechahora                    DateTime,

            sk_unidad                    UInt64,
            idunidademergencia           Int32,
            unidad                       String,
            proveedor                    String,

            idestadounidademergencia     Nullable(Int32),
            estado_nuevo                 Nullable(String),
            estado_anterior              Nullable(String),

            es_cambio_efectivo           UInt8,
            segundos_en_estado_anterior  Nullable(Int32),

            cargado_en                   DateTime
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(fecha)
        ORDER BY (fecha, idunidademergencia, idhistorial)
        """
    )


# ──────────────────────────── Orquestación ──────────────────────────────

#: Las dimensiones, en el orden en que se crean. **Siempre antes que los hechos.**
DIMENSIONES = (
    ensure_dim_tiempo,
    ensure_dim_geografia,
    ensure_dim_severidad,
    ensure_dim_origen_despacho,
    ensure_dim_unidad,
)

HECHOS = (
    ensure_hecho_accidente,
    ensure_hecho_despacho,
    ensure_hecho_estado_unidad,
    ensure_hecho_ping_unidad,
)


def ensure_modelo_analitico() -> None:
    """Crea el modelo entero. Idempotente: repetirlo no altera nada."""
    for crear in DIMENSIONES + HECHOS:
        crear()


# ──────────────── Diseño anterior — se retira en la fase 6 ───────────────
#
# ⚠️ No borrar todavía. Estas tres tablas siguen sirviendo sus informes hasta que
# T047 verifique que el modelo devuelve las mismas cifras. Sus valores actuales
# están anotados en quickstart.md §3.8 como referencia de esa comparación.


def ensure_perdida_senal_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS perdida_senal_gps (
            periodo Date,
            idunidademergencia Int32,
            idaccidente String,
            inicio_hueco DateTime,
            fin_hueco DateTime,
            duracion_seg Int32,
            umbral_usado_seg Int32,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY (periodo, idunidademergencia, inicio_hueco)
        """
    )


def ensure_indice_calidad_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS indice_calidad_historico (
            periodo Date,
            pct_completitud Float64,
            pct_descarte Float64,
            pct_fusion Float64,
            pct_cobertura_evidencia Float64,
            indice_consolidado Float64,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY periodo
        """
    )


def ensure_rendimiento_proveedor_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS rendimiento_por_proveedor (
            periodo Date,
            idcliente Int32,
            pct_rechazo Float64,
            tiempo_llegada_promedio_seg Float64,
            pct_abortos Float64,
            total_despachos Int32,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY (periodo, idcliente)
        """
    )
