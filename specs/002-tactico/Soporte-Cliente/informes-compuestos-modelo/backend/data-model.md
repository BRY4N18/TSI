# Data Model — Informes Compuestos de Soporte al Cliente

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo consume el [modelo analítico](../../../modelo-analitico/), reutiliza dos tablas de
Suscripciones y añade **tres dimensiones y dos hechos**.

---

## 1. Los 9 informes

### OT19 — El cumplimiento *(4 informes, 1 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 1 | **Cumplimiento de SLA** — meta ≥95 % | período | `hecho_ticket` + `dim_sla_config` |
| 2 | Cumplimiento desglosado por plan | plan × período | `hecho_ticket` + `dim_plan` |
| 3 | Rendimiento por agente | agente × período | `hecho_ticket` + `hecho_accion_ticket` |
| 4 | Tickets por servicio afectado | servicio | `hecho_ticket` + `dim_servicio` |

**#1 devuelve el cumplimiento y la cobertura en la misma fila** (research D3). **#4 saldrá vacío**
—«sin servicio: 14»— y lo declara (research D7).

### OT20 — La cola en curso *(3 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 5 | Tablero de cola | estado × prioridad × tipo | `hecho_ticket` |
| 6 | Evolución temporal del incumplimiento | período | `hecho_ticket` + `dim_sla_config` |
| 7 | Tasa de escalado automático | tipo × prioridad | `hecho_accion_ticket` |

**#5 acepta corte temporal y desglose por agente**, que el tablero actual no admite.

### OT20 — Las tendencias *(2 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 8 | Carga entrante frente a resuelta | día | `hecho_ticket` |
| 9 | Reincidencia de clientes | cliente × eje | `hecho_ticket` + `dim_cliente` |

---

## 2. Las tablas nuevas

### 2.1 `dim_sla_config` — **versionada desde el origen** ⚠️

```sql
CREATE TABLE IF NOT EXISTS dim_sla_config (
    idslaconfig          Int32,
    idplan               Int32,
    tipo_incidencia      String,
    prioridad            String,

    segundos_respuesta_max  Int32,
    segundos_resolucion_max Int32,

    valido_desde         DateTime,
    valido_hasta         Nullable(DateTime),   -- NULL = vigente
    es_vigente           UInt8,

    version              DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY (idplan, tipo_incidencia, prioridad, valido_desde)
```

⚠️ **No lleva `inicio_es_real`, y es deliberado.** En `dim_unidad` y `dim_region` esa marca declara
que la historia empieza en la primera carga porque el origen no la guardaba. **Aquí sí la guarda**:
cada vigencia es un hecho registrado por la operación, no una reconstrucción.

⚠️ **No se carga con `versionado.py`.** Ese módulo **construye** historia comparando estados; usarlo
aquí reconstruiría la que ya existe y la marcaría como no real — la mentira que esa marca existe para
evitar, en la dirección contraria.

**El orden incluye `valido_desde`** porque la misma combinación (plan, incidencia, prioridad) tiene
varias versiones: es lo que permite resolver cuál estaba vigente en un instante.

### 2.2 `hecho_ticket` — **instantánea acumulada**

```sql
CREATE TABLE IF NOT EXISTS hecho_ticket (
    id_reclamo           Int32,
    fecha                Date,               -- de creación; clave de partición
    fechahora_creacion   DateTime,

    idcliente            Int32,
    tipo_cliente         Nullable(String),
    idplan               Nullable(Int32),
    plan                 Nullable(String),

    idagente             Nullable(Int32),    -- CLAVE, nunca nombre
    tiene_agente         UInt8,

    tipo                 Nullable(String),
    tipo_incidencia      Nullable(String),
    prioridad            Nullable(String),
    idservicio           Nullable(Int32),
    servicio             Nullable(String),
    estado               String,

    -- el compromiso vigente al crearse el ticket
    idslaconfig          Nullable(Int32),
    tiene_compromiso     UInt8,
    motivo_sin_compromiso Nullable(String),  -- pendiente_clasificar | sin_compromiso | sin_config
    segundos_respuesta_max  Nullable(Int32),
    segundos_resolucion_max Nullable(Int32),

    -- hitos  ⚠️ NULL = no alcanzado
    hora_primera_respuesta Nullable(DateTime),
    hora_resolucion      Nullable(DateTime),
    hora_cierre          Nullable(DateTime),
    hora_cierre_confirmado Nullable(DateTime),

    -- métricas derivadas  ⚠️ NULL si no hubo hito
    segundos_primera_respuesta Nullable(Int32),
    segundos_resolucion  Nullable(Int32),

    desenlace_sla        Nullable(String),   -- cumplido | incumplido | NULL si sin compromiso
    fue_reabierto        UInt8,
    reaperturas          UInt8,

    cargado_en           DateTime,
    version              DateTime
) ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, id_reclamo)
```

⚠️ **`segundos_*` ausentes cuando no hay hito.** El origen los guarda como **`0`**, y un cero diría
que se respondió al instante: un promedio que los incluyera **mejoraría cuantos más tickets sin
atender hubiera**.

⚠️ **`segundos_resolucion_max` se copia del SLA vigente al crearse el ticket**, no del actual. Es lo
que hace que acortar un SLA **no reescriba** el cumplimiento pasado (research D1).

⚠️ **`motivo_sin_compromiso` separa tres cosas distintas**: un fallo del proceso, una decisión y un
hueco del catálogo.

⚠️ **Sin `asunto` ni `descripcion`.** Texto escrito por el cliente.

**Es instantánea acumulada, así que sus consultas fuerzan versión final.**

### 2.3 `hecho_accion_ticket` — transacción

```sql
CREATE TABLE IF NOT EXISTS hecho_accion_ticket (
    id_historial     Int32,
    fecha            Date,
    fechahora        DateTime,

    id_reclamo       Int32,
    idcliente        Nullable(Int32),
    idagente         Nullable(Int32),

    tipo_accion      String,             -- creacion | escalado_automatico_sla | reapertura | …
    es_escalado      UInt8,
    es_escalado_automatico UInt8,
    estado_anterior  Nullable(String),
    estado_nuevo     Nullable(String),
    es_cambio_efectivo UInt8,

    cargado_en       DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, id_reclamo, id_historial)
```

⚠️ **Sin `mensaje` y sin `es_nota_interna`.** Las notas internas son comentarios del equipo sobre el
cliente, escritos con la expectativa de que el cliente no los lea (research D5).

⚠️ **`es_escalado_automatico` distingue la señal del sistema de la decisión de una persona.** Es el
evento más frecuente del departamento: **13 de las 34 acciones**.

### 2.4 `dim_servicio` y `dim_estado_soporte`

```sql
CREATE TABLE IF NOT EXISTS dim_servicio (
    id_servicio Int32,
    nombre      String,
    tipo        Nullable(String),      -- api | portal
    es_activo   UInt8,
    version     DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY id_servicio;

CREATE TABLE IF NOT EXISTS dim_estado_soporte (
    id_estado_soporte Int32,
    nombre            String,
    es_activo         UInt8,
    version           DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY id_estado_soporte
```

⚠️ **`dim_servicio` tendrá 3 filas y ningún ticket apuntando a ellas.** Se carga igualmente: el
informe por servicio **es la evidencia de que la asignación no se está registrando** (research D7).

### 2.5 Lo que se reutiliza

| Tabla | La creó | Para qué se usa aquí |
|---|---|---|
| `dim_cliente` | Suscripciones | Reincidencia y desglose por tipo |
| `dim_plan` | Suscripciones | Cumplimiento por plan |

### 2.6 Lo que NO se añade

| Se pidió | No se añade | Motivo |
|---|---|---|
| Asunto y descripción del ticket | Nada | Texto del cliente |
| Mensajes del historial | Nada | Texto libre |
| **Notas internas** | Nada | Comentarios del equipo sobre el cliente |
| Nombre del agente | Nada; solo su clave | Identidad de persona |
| `inicio_es_real` en el SLA | **Nada** | Su historia **es real**: la guarda el origen |

---

## 3. Reglas de consulta

| Regla | Aplicada aquí |
|---|---|
| **Versión final** | Obligatoria en las cinco dimensiones y en `hecho_ticket`. **Prohibida** en `hecho_accion_ticket` |
| **El SLA vigente al crear el ticket** | Copiado en el hecho; nunca se une con la configuración actual |
| **Ausencia ≠ cero** | Tiempos sin hito, cumplimiento sin compromiso, denominador vacío |
| **La cobertura va con la cifra** | El cumplimiento devuelve el porcentaje sin compromiso en la misma fila |
| **Escalado automático ≠ humano** | Dos columnas, nunca sumadas |
| **Los días vacíos existen** | La serie de carga diaria incluye los días sin tickets con cero |
