# Data Model — Informes Compuestos de Ventas y CRM

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo consume el [modelo analítico](../../../modelo-analitico/) y le añade **dos dimensiones y
cuatro hechos**. Es el primero cuyo dominio no reutiliza ninguna tabla existente.

---

## 1. Los 13 informes

### OT02 — El embudo *(5 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 1 | Embudo de conversión | etapa origen × etapa destino × período | `hecho_transicion_embudo` |
| 2 | Tiempo medio de permanencia por etapa | etapa × período | `hecho_transicion_embudo` |
| 3 | Carga por ejecutivo | ejecutivo × período | `hecho_asignacion_prospecto` + `dim_prospecto` |
| 4 | Valor del pipeline ponderado por etapa | etapa × período | `dim_prospecto` |
| 5 | Motivos de pérdida por etapa de abandono | motivo × etapa | `hecho_transicion_embudo` |

**#2 incluye el tramo abierto** (research D3): la etapa vigente al final del período cuenta **hasta
el fin del período**. Sin eso, los prospectos estancados —los que el informe existe para encontrar—
no aparecerían en la medida.

**#5 agrupa motivo y etapa juntos**: el mismo motivo significa cosas distintas en «Contactado» que en
«Negociación».

### OT01 — La captación *(3 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 6 | Volumen de captación por canal | canal × período | `dim_prospecto` |
| 7 | Tasa de conversión por canal | canal × período | `dim_prospecto` |
| 8 | Clientes convertidos por canal | canal × período | `dim_prospecto` |

⚠️ **#8 no es el CAC** y no devuelve ninguna columna de coste, ni siquiera vacía (research D7).

### OT03 — La nutrición *(5 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 9 | Intensidad de uso de la demo | prospecto × período | `hecho_interaccion_demo` |
| 10 | Secciones más visitadas | sección | `hecho_interaccion_demo` |
| 11 | Efectividad de la nutrición | con demo / sin demo | `dim_prospecto` + `hecho_interaccion_demo` |
| 12 | Latencia de reacción comercial | período | `hecho_notificacion_ventas` + `hecho_transicion_embudo` |
| 13 | Reglas de disparo por tasa de acierto | regla | `hecho_notificacion_ventas` |

⚠️ **Los cinco operan hoy sobre fuentes vacías**, por entorno y no por diseño (research D6).

---

## 2. Las ampliaciones del modelo

### 2.1 `dim_prospecto` ⚠️ **sin dato personal**

```sql
CREATE TABLE IF NOT EXISTS dim_prospecto (
    idprospecto        Int32,
    empresa            String,            -- unidad de NEGOCIO, no persona
    tipo_organizacion  Nullable(String),  -- aseguradora | municipio | …
    canal              String,            -- de dónde vino; "Desconocido" si no consta
    etapa_actual       Nullable(String),
    desenlace          String,            -- convertido | perdido | en_curso
    motivo_perdida     Nullable(String),
    valor_estimado     Nullable(Decimal(12, 2)),
    tiene_demo         UInt8,
    fecha_registro     Nullable(DateTime),
    fecha_conversion   Nullable(DateTime),
    idcliente          Nullable(Int32),   -- si convirtió
    version            DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idprospecto
```

⚠️ **`desenlace` es la columna que resuelve el defecto del origen** (research D1). Se deriva al
cargar de `motivo_inactividad` y `etapa_actual`; **ninguna consulta lee `activo`**, que cubre a la
vez convertido y perdido.

⚠️ **No se copian**: nombres, apellidos, correo, teléfono ni cargo. Es la tabla con más dato personal
del sistema, y ningún informe del catálogo necesita saber quién es el prospecto.

**No es versionada**, a diferencia de la unidad y la región: el desenlace de un prospecto es
terminal —convertido o perdido no se deshacen— y su etapa histórica ya vive en el hecho de
transición. Versionarla duplicaría ese historial.

### 2.2 `dim_canal`

```sql
CREATE TABLE IF NOT EXISTS dim_canal (
    idcanal    Int32,
    canal      String,
    agrupacion Nullable(String),   -- digital | referido | directo
    version    DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idcanal
```

El origen guarda el canal como **texto libre** en `como_nos_conocio`. La dimensión lo normaliza y
permite agrupar, con su **fila desconocida** para los prospectos sin canal declarado — que **cuentan
en los totales**, no se descartan.

### 2.3 `hecho_transicion_embudo` — transacción, grano **una transición**

```sql
CREATE TABLE IF NOT EXISTS hecho_transicion_embudo (
    idtransicion       Int32,
    fecha              Date,
    fechahora          DateTime,

    idprospecto        Int32,
    empresa            String,
    canal              String,
    tipo_organizacion  Nullable(String),

    etapa_anterior     Nullable(String),
    etapa_nueva        String,
    es_avance          UInt8,             -- 0 = retroceso de etapa
    es_terminal        UInt8,             -- llegó a Ganado o Perdido
    motivo_perdida     Nullable(String),

    segundos_en_etapa_anterior Nullable(Int32),

    cargado_en         DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idprospecto, idtransicion)
```

**`es_avance` distingue el retroceso**, que existe y afecta al porcentaje de paso.

⚠️ **`notas` no se copia**: es texto libre escrito por el ejecutivo.

⚠️ **`segundos_en_etapa_anterior` va ausente en la primera transición** de cada prospecto: no había
etapa anterior. Cero significaría «pasó al instante».

### 2.4 `hecho_asignacion_prospecto` — transacción, grano **una asignación**

```sql
CREATE TABLE IF NOT EXISTS hecho_asignacion_prospecto (
    idasignacion       Int32,
    fecha              Date,
    fechahora          DateTime,

    idprospecto        Int32,
    empresa            String,
    idejecutivo        Int32,             -- ejecutivo ENTRANTE
    idejecutivo_previo Nullable(Int32),
    tipo_asignacion    String,            -- inicial | reasignación
    motivo             Nullable(String),

    cargado_en         DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idprospecto, idasignacion)
```

⚠️ **Es el primer historial del proyecto que el origen sí guarda bien** (research D4). La atribución
por ejecutivo es **exacta desde el primer día**, sin la marca de «inicio no real» que necesitan la
unidad y la región.

**El ejecutivo se identifica por su clave**, no por su nombre: es su función dentro del informe de
carga, que es el único donde el desglose por ejecutivo **es el objeto del informe**.

### 2.5 `hecho_interaccion_demo` — transacción *(fuente vacía hoy)*

```sql
CREATE TABLE IF NOT EXISTS hecho_interaccion_demo (
    idinteraccion Int32,
    fecha         Date,
    fechahora     DateTime,
    idprospecto   Int32,
    empresa       String,
    canal         String,
    tipo_evento   String,
    seccion       Nullable(String),
    cargado_en    DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idprospecto, idinteraccion)
```

⚠️ **`metadata` no se copia**: es un campo libre cuyo contenido nadie garantiza.

### 2.6 `hecho_notificacion_ventas` — transacción *(fuente vacía hoy)*

```sql
CREATE TABLE IF NOT EXISTS hecho_notificacion_ventas (
    idnotificacion    Int32,
    fecha             Date,
    fechahora         DateTime,
    idprospecto       Int32,
    empresa           String,
    regla_disparada   String,
    canal_aviso       String,
    hubo_avance       UInt8,               -- 0 = sin reacción posterior
    segundos_a_reaccion Nullable(Int32),
    cargado_en        DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idprospecto, idnotificacion)
```

⚠️ **`hubo_avance = 0` y `segundos_a_reaccion` ausente** es un aviso **sin reacción**, no una reacción
instantánea. Es la distinción que hace útil el informe de latencia: sin ella, los avisos ignorados
mejorarían la media.

⚠️ **`estado_envio` no se copia**: el catálogo ya retiró el informe que la usaba porque **ningún
código la escribe**.

### 2.7 Lo que NO se añade

| Se pidió | No se añade | Motivo |
|---|---|---|
| Identidad y contacto del prospecto | Nada | Dato personal; ningún informe lo necesita |
| Notas de transición, metadata de demo | Nada | Texto libre |
| Columna de coste por canal | **Nada, ni vacía** | Invitaría a rellenarla desde fuera |
| `estado_envio` de notificaciones | Nada | Ningún código la escribe |
| Versionado de `dim_prospecto` | Nada | El historial de etapas ya vive en el hecho de transición |

---

## 3. Reglas de consulta

| Regla | Aplicada aquí |
|---|---|
| **Versión final** | Obligatoria en `dim_prospecto` y `dim_canal`. **Prohibida** en los cuatro hechos, todos de transacción |
| **El desenlace nunca sale de `activo`** | Se lee `desenlace`, de tres valores |
| **El grano del embudo es la transición** | No el prospecto |
| **Ausencia ≠ cero** | Primera transición sin duración, aviso sin reacción, canal sin prospectos |
| **Lo desconocido cuenta** | Prospectos sin canal aparecen como `Desconocido` y suman |
