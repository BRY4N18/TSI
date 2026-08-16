# Data Model — Informes Compuestos de Partners y API

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo consume el [modelo analítico](../../../modelo-analitico/), **reutiliza dos tablas de
Suscripciones** y añade **tres dimensiones y dos hechos**.

---

## 1. Los 13 informes en alcance

### OT09 — El consumo *(7 informes, 2 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo | Hoy |
|--:|---|---|---|---|
| 1 | Métricas de consumo por partner | partner × período | `hecho_llamada_api` | 🟡 solo media |
| 2 | Reporte mensual de consumo | partner × mes | `hecho_llamada_api` | 🟢 |
| 3 | Consumo por endpoint y método | endpoint × método | `hecho_llamada_api` | ⚪ |
| 4 | **Latencia p95 por endpoint** | endpoint | `hecho_llamada_api` | ⚪ |
| 5 | Taxonomía de errores y evolución | código × período | `hecho_llamada_api` | ⚪ |
| 6 | Comparativa entre partners | partner | `hecho_llamada_api` + `dim_partner` | ⚪ |
| 7 | **Participación de ingresos por API** | partner × mes | `hecho_factura` + `dim_partner` | ⚪ |

**#4 es imposible sobre una agregación previa**: un percentil necesita las observaciones, y por eso
la métrica actual solo puede dar media (research D2).

**#7 reutiliza `hecho_factura` de Suscripciones** — primera vez que un módulo compuesto consume un
hecho de otro.

### OT08 — La incorporación *(4 informes, 1 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 8 | Motivo por el que una credencial está inactiva | motivo × partner | `dim_credencial_api` |
| 9 | Tiempo de incorporación por etapa | partner | `hecho_cambio_acceso` |
| 10 | **Adopción de versiones del contrato** | servicio × versión | `hecho_llamada_api` + `dim_version_contrato` |
| 11 | Tasa de rechazo de solicitudes de producción | motivo × período | `hecho_cambio_acceso` |

**#8 solo es posible derivando el motivo al cargar**: la credencial no lo guarda (research D3).

**#10 agrupa por (servicio, versión)**, no por versión sola: dos servicios comparten `'v1'`.

### OT10 — La entrega *(2 informes, 1 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 12 | **Clientes con integración API activa** — meta ≥70 % | período | `hecho_llamada_api` + `dim_cliente` |
| 13 | Volumen de expedientes por cliente y canal | cliente × canal | `hecho_llamada_api` + `hecho_accidente` |

**#12 reutiliza `dim_cliente` de Suscripciones**, y su denominador son **todos los clientes**: si
fueran solo los que tienen partner, el indicador daría siempre 100 %.

⚠️ **El informe 14 del catálogo —alcance efectivo— queda fuera** (research D7).

---

## 2. Las ampliaciones del modelo

### 2.1 `hecho_llamada_api` — transacción, grano **una llamada** ⚠️

```sql
CREATE TABLE IF NOT EXISTS hecho_llamada_api (
    idlog              Int32,
    fecha              Date,               -- clave de partición
    fechahora          DateTime,

    idpartner          Int32,
    partner            String,
    idcliente          Nullable(Int32),
    plan_api           Nullable(String),

    idcredencial       Nullable(Int32),
    entorno            Nullable(String),   -- Producción | Sandbox

    endpoint_path      String,             -- sin cadena de consulta
    metodo_http        String,
    codigo_http        UInt16,
    clase_resultado    String,             -- exito | limite_cupo | autorizacion | error_servicio
    latencia_ms        Int32,

    servicio           Nullable(String),   -- derivado del path
    version_contrato   Nullable(String),   -- derivada del path
    version_es_derivada UInt8,             -- siempre 1 por ahora

    cargado_en         DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idpartner, endpoint_path)
```

⚠️ **`iporigen` no se copia.** Identifica a un consumidor concreto y ningún informe la necesita: los
patrones anómalos se describen con volumen, códigos y latencia (research D6).

⚠️ **`endpoint_path` va sin cadena de consulta.** El origen guarda
`/api/v1/datos/accidentes?idseveridad=4`, y agrupar por la cadena completa **fragmentaría el consumo
por endpoint en tantos grupos como combinaciones de parámetros haya**. El path se normaliza al
cargar.

⚠️ **`clase_resultado` distingue los tres problemas distintos** que el código HTTP mezcla:
`429` es límite de cupo —contrato—, `403` es autorización, `5xx` es fallo del servicio. Cada uno
tiene un responsable diferente, y un informe que los sume dice «hay errores» sin decir de quién.

**Es el hecho de mayor crecimiento del modelo**: una fila por petición. Hoy tiene 18.

### 2.2 `hecho_cambio_acceso` — transacción, grano **un cambio**

```sql
CREATE TABLE IF NOT EXISTS hecho_cambio_acceso (
    idhistorial      Int32,
    fecha            Date,
    fechahora        DateTime,

    idpartner        Int32,
    partner          String,
    idcredencial     Nullable(Int32),

    tipo_cambio      String,             -- registro | asignacion_plan | activacion_sandbox | …
    estado_anterior  Nullable(String),
    estado_nuevo     Nullable(String),
    es_cambio_efectivo UInt8,            -- 0 = el estado no cambió realmente
    motivo           Nullable(String),

    cargado_en       DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idpartner, idhistorial)
```

⚠️ **`ejecutado_por` no se copia**: es identidad de persona.

⚠️ **`es_cambio_efectivo`** repite la solución ya usada en `hecho_estado_unidad`: la bitácora
registra eventos con `Activo → Activo` y eventos duplicados a milisegundos. Sin esta marca, la tasa
de rechazo y el tiempo de incorporación contarían transiciones que no ocurrieron.

**`motivo` sí se conserva**: es un campo clasificable del catálogo operativo, y el informe de tasa de
rechazo agrupa **por motivo, nunca por persona**.

### 2.3 `dim_partner`

```sql
CREATE TABLE IF NOT EXISTS dim_partner (
    idpartner            Int32,
    nombre_partner       String,
    idcliente            Nullable(Int32),
    plan_api             Nullable(String),
    limite_llamadas_mes  Nullable(Int32),
    limite_llamadas_minuto Nullable(Int32),
    estado               String,          -- activo | suspendido
    fecha_suspension     Nullable(DateTime),
    sandbox_activado     Nullable(DateTime),
    sandbox_expiracion   Nullable(DateTime),
    version              DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idpartner
```

⚠️ **Sin `contacto_tecnico_nombre` ni `contacto_tecnico_gmail`**: dato personal.

**`plan_api` puede venir con el texto `'null'`** en el origen — es uno de los defectos ya
documentados del sistema (decisión #15 del proyecto). Se normaliza a ausente al cargar.

### 2.4 `dim_credencial_api` — con el motivo derivado ⚠️

```sql
CREATE TABLE IF NOT EXISTS dim_credencial_api (
    idcredencial       Int32,
    idpartner          Int32,
    idcliente          Nullable(Int32),
    nombre_credencial  String,
    entorno            String,

    esta_activa        UInt8,
    motivo_inactividad Nullable(String),   -- revocada | cascada | expirada | suspension_manual
    fecha_creacion     Nullable(DateTime),
    fecha_expiracion   Nullable(DateTime), -- NULL = nunca expira
    nunca_expira       UInt8,

    version            DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idcredencial
```

⚠️ **`client_secret_hash` no se copia.** Es un secreto aunque esté cifrado.

⚠️ **`motivo_inactividad` es la columna que resuelve el defecto del origen**: la credencial solo
guarda un indicador de actividad, y revocación, cascada y expiración son indistinguibles en ella. Se
deriva del último cambio de acceso efectivo que la afectó.

⚠️ **`fecha_expiracion` ausente y `nunca_expira = 1`** sustituyen al centinela del año 9999. Un
promedio de días hasta la expiración que lo incluyera daría **2,9 millones de días**.

### 2.5 `dim_version_contrato`

```sql
CREATE TABLE IF NOT EXISTS dim_version_contrato (
    idversion         Int32,
    id_servicio       Int32,
    servicio          Nullable(String),
    version           String,
    estado            String,             -- vigente | retirada
    fecha_publicacion Nullable(DateTime),
    fecha_retiro      Nullable(DateTime), -- NULL = no retirada
    version_carga     DateTime
) ENGINE = ReplacingMergeTree(version_carga)
ORDER BY (id_servicio, version)
```

⚠️ **La clave es (servicio, versión)**, no la versión sola: dos servicios distintos comparten `'v1'`.

⚠️ **`fecha_retiro` ausente** sustituye al centinela de época cero. Una versión «retirada en 1970»
ordenaría antes que cualquier otra y encabezaría con naturalidad un informe de versiones retiradas.

### 2.6 Lo que se reutiliza de otros módulos

| Tabla | La creó | Para qué se usa aquí |
|---|---|---|
| `dim_cliente` | Suscripciones | Clientes con integración activa (#12) |
| `hecho_factura` | Suscripciones | Participación de ingresos por API (#7) |
| `hecho_accidente` | Emergencias | Volumen de expedientes entregados (#13) |

**Es la primera vez que un módulo compuesto consume hechos y dimensiones de otros dos.** No se
recrean.

### 2.7 Lo que NO se añade

| Se pidió | No se añade | Motivo |
|---|---|---|
| Métricas de consumo preagregadas | **Nada** | Difieren del detalle en un orden de magnitud (research D1) |
| IP de origen | Nada | Identifica al consumidor; los patrones se ven con volumen y códigos |
| Hash del secreto | Nada | Es un secreto |
| Contacto técnico | Nada | Dato personal |
| Ejecutor del cambio de acceso | Nada | Identidad de persona |
| Zona consultada | **Nada, ni inferida** | El log no la registra (research D7) |

---

## 3. Reglas de consulta

| Regla | Aplicada aquí |
|---|---|
| **Versión final** | Obligatoria en las tres dimensiones. **Prohibida** en los dos hechos, ambos de transacción |
| **Una sola fuente de consumo** | El detalle; la preagregada no existe en el modelo |
| **Toda medida declara sus muestras** | p95, media y totales vienen con el número de llamadas |
| **429 ≠ 5xx ≠ 403** | Tres clases de resultado distintas, tres responsables distintos |
| **Ausencia ≠ cero** | Credencial sin expiración, versión sin retiro, partner sin llamadas |
| **La versión es derivada** | Y el informe lo declara |
