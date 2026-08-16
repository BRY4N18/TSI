# Data Model — Informes Compuestos de Suscripciones y Facturación

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo consume el [modelo analítico](../../../modelo-analitico/) y le añade **dos dimensiones y
tres hechos**.

---

## 1. Los 13 informes

### OT06 — El ciclo de cobro *(6 informes, 3 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 1 | MRR y variación mes a mes | mes | `hecho_suscripcion` |
| 2 | Ingresos por período, plan y tipo de cliente | mes × plan × tipo | `hecho_factura` |
| 3 | Tasa de renovación | mes | `hecho_suscripcion` |
| 4 | Tasa de cobro al primer intento | mes | `hecho_factura` |
| 5 | Efectividad del dunning por escalón | escalón × mes | `hecho_factura` |
| 6 | Clientes sin método de pago activo | cliente | `dim_cliente` |

**#1 normaliza a mensual y descompone la variación en cuatro** —nuevo, expansión, contracción,
baja—: un MRR plano puede esconder una fuga compensada por altas.

**#6 es una diferencia de conjuntos**: el cliente que interesa es el que **no tiene ninguna fila** en
métodos de pago. Una unión ordinaria lo perdería, que es justo lo contrario de lo que el informe
busca.

### OT07 — Los movimientos de la cartera *(4 informes, 2 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 7 | Movimientos de plan con delta de ingreso | mes × tipo de movimiento | `hecho_solicitud_cambio_plan` |
| 8 | Retención neta de ingresos (NRR) | mes | `hecho_suscripcion` + `hecho_factura` |
| 9 | Tasa de suspensión y reactivación | mes | `hecho_suscripcion` |
| 10 | Tiempo medio de resolución de solicitudes | mes | `hecho_solicitud_cambio_plan` |

**#10 se entrega agregado, no por administrador** (FR-033): es identidad de persona.

### OT05 — El catálogo y su uso *(3 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 11 | Distribución de la cartera por plan y nivel | plan × nivel | `hecho_suscripcion` + `dim_plan` |
| 12 | Utilización de límites — **unidades y usuarios** | cliente × plan | `dim_plan` + `dim_unidad` |
| 13 | Severidades habilitadas frente a atendidas | plan × severidad | `dim_plan` + `hecho_accidente` |

⚠️ **#12 no incluye llamadas API**: pertenecen a Partners (research D7). **#13 cruza con
`hecho_accidente`**, ya construido — es el primer informe del proyecto que une el dominio financiero
con el operativo.

---

## 2. Las ampliaciones del modelo

### 2.1 `dim_plan` — con los límites desplegados

```sql
CREATE TABLE IF NOT EXISTS dim_plan (
    idplan                    Int32,
    nombre                    String,
    nivel                     Nullable(String),
    periodicidad              Nullable(String),
    precio_lista              Nullable(Decimal(12, 2)),
    precio_excedente_llamada  Nullable(Decimal(12, 4)),

    -- límites desplegados (research D5)
    limite_unidades           Nullable(Int32),
    limite_usuarios           Nullable(Int32),
    limite_llamadas_mes       Nullable(Int32),
    limite_llamadas_minuto    Nullable(Int32),

    severidades_habilitadas   Array(Int32),
    carga_lote_habilitada     UInt8,
    es_activo                 UInt8,
    version                   DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idplan
```

⚠️ **`precio_lista` es lo que el plan cuesta en catálogo, no lo que un cliente paga.** El nombre lo
dice a propósito: el MRR usa el precio de la suscripción, y hay planes del mismo nivel con precios
muy distintos.

### 2.2 `dim_cliente` — dimensión **conformada**, sin dato fiscal

```sql
CREATE TABLE IF NOT EXISTS dim_cliente (
    idcliente          Int32,
    nombre_comercial   String,
    tipo               Nullable(String),      -- aseguradora | municipio | …
    estado_comercial   Nullable(String),
    estado_onboarding  Nullable(String),
    tiene_metodo_pago  UInt8,
    metodo_pago_caduca Nullable(Date),
    fecha_alta         Nullable(DateTime),
    version            DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idcliente
```

⚠️ **Sin identificador fiscal, sin contacto, sin token de pasarela, sin últimos dígitos.** Se guarda
**si hay método vigente y cuándo caduca**, nunca cuál (research D6).

**Es una dimensión conformada**: la necesitan tres departamentos. Se crea aquí porque es el primero
que la requiere; **Cuentas y Clientes la ampliará, no la recreará**.

### 2.3 `hecho_suscripcion` — **instantánea acumulada**

```sql
CREATE TABLE IF NOT EXISTS hecho_suscripcion (
    id_suscripcion        Int32,
    fecha                 Date,              -- del alta; clave de partición
    idcliente             Int32,
    tipo_cliente          Nullable(String),
    idplan                Int32,
    plan                  String,
    nivel                 Nullable(String),

    -- hitos  ⚠️ NULL = no alcanzado
    fecha_alta            DateTime,
    fecha_fin_prevista    Nullable(DateTime),
    fecha_ultima_renovacion Nullable(DateTime),
    fecha_suspension      Nullable(DateTime),
    fecha_reactivacion    Nullable(DateTime),
    fecha_cancelacion     Nullable(DateTime),

    estado_derivado       String,            -- vigente | suspendida | cancelada | vencida
    motivo_cancelacion    Nullable(String),  -- SOLO si estado = cancelada

    precio                Decimal(12, 2),
    periodicidad          Nullable(String),
    precio_mensualizado   Nullable(Decimal(12, 2)),   -- NULL si no se pudo normalizar

    renovacion_automatica UInt8,
    idplan_programado     Nullable(Int32),   -- NULL = sin cambio programado
    severidades_contratadas Array(Int32),

    vigencia_inconsistente UInt8,            -- 1 = fin anterior a inicio

    cargado_en            DateTime,
    version               DateTime
) ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, id_suscripcion)
```

**Las cinco columnas que resuelven los cinco defectos del origen** (research D1):

| Columna | Qué defecto neutraliza |
|---|---|
| `estado_derivado` | `activo = true` en suscripciones canceladas |
| `motivo_cancelacion` solo si canceló | Motivo poblado en suscripciones activas |
| `vigencia_inconsistente` | Fin anterior a inicio |
| `idplan_programado` nulo | Centinela `0` |
| `motivo` unificado | Tres formas de decir «sin motivo» |

⚠️ **`precio_mensualizado` ausente** cuando la periodicidad no consta: no se puede normalizar lo que
no se sabe cada cuánto se cobra. **Nunca cero** — eso diría que no aporta ingreso.

⚠️ **Es instantánea acumulada, así que sus consultas fuerzan versión final.** Omitirlo cuenta una
suscripción actualizada dos veces e **infla el MRR de forma intermitente**.

### 2.4 `hecho_factura` — transacción

```sql
CREATE TABLE IF NOT EXISTS hecho_factura (
    id_factura            String,
    fecha                 Date,              -- de emisión; clave de partición
    fecha_emision         DateTime,
    fecha_vencimiento     Nullable(DateTime),

    idcliente             Int32,
    tipo_cliente          Nullable(String),
    id_suscripcion        Nullable(Int32),
    idplan                Nullable(Int32),
    plan                  Nullable(String),

    estado_pago           String,            -- Pagada | Pendiente | En disputa | Anulada
    es_nota_credito       UInt8,
    id_factura_original   Nullable(String),
    signo                 Int8,              -- +1 factura, -1 nota de crédito

    monto_base            Decimal(12, 2),
    impuestos             Decimal(12, 2),
    monto_total           Decimal(12, 2),
    monto_con_signo       Decimal(12, 2),    -- monto_total * signo

    reintentos            UInt8,
    pagada_primer_intento UInt8,
    dias_mora             Nullable(Int32),

    cargado_en            DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idcliente, id_factura)
```

⚠️ **`monto_con_signo` existe para que sumar ingresos sea sumar** (FR-018): las notas de crédito
**restan**. Sin esa columna, cada consulta tendría que acordarse del signo, y la primera que lo
olvide inflará los ingresos.

⚠️ **`estado_pago = 'En disputa'` NO es impago** (FR-019). Son problemas distintos: uno comercial,
otro de cobro.

⚠️ **Sin `idmetodopago`, sin `desglose_cargos` y sin `motivo_anulacion`**: medio de cobro y texto
libre.

### 2.5 `hecho_solicitud_cambio_plan` — transacción

```sql
CREATE TABLE IF NOT EXISTS hecho_solicitud_cambio_plan (
    idsolicitud        Int32,
    fecha              Date,               -- de solicitud; clave de partición
    fecha_solicitud    DateTime,
    fecha_resolucion   Nullable(DateTime),

    idcliente          Int32,
    idplan_actual      Int32,
    plan_actual        String,
    idplan_solicitado  Int32,
    plan_solicitado    String,

    tipo_movimiento    String,             -- upgrade | downgrade | lateral
    delta_precio       Decimal(12, 2),
    estado             String,             -- pendiente | aprobada | rechazada | aplicada
    esta_resuelta      UInt8,
    segundos_resolucion Nullable(Int32),

    cargado_en         DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idcliente, idsolicitud)
```

⚠️ **`segundos_resolucion` ausente mientras esté pendiente** (FR-027): una solicitud abierta no se
resolvió en cero segundos.

⚠️ **`tipo_movimiento` se deriva del delta de precio**, no del nivel del plan: el catálogo tiene un
plan de nivel Empresarial más barato que uno Profesional, así que subir de nivel no siempre es subir
de precio.

⚠️ **Sin `idadminaprobador`** —identidad de persona— y sin `motivo_rechazo` —texto libre—.

### 2.6 Lo que NO se añade

| Se pidió | No se añade | Motivo |
|---|---|---|
| Medios de cobro | Nada; solo si hay y cuándo caduca | Dato financiero sensible |
| Identificador fiscal | Nada | Dato identificatorio |
| Desglose por administrador | Nada; se agrega | Identidad de persona |
| Textos libres de anulación y rechazo | Nada | Texto libre |
| Hecho de llamadas API | **Nada** | Pertenece a Partners (research D7) |

---

## 3. Reglas de consulta

| Regla | Aplicada aquí |
|---|---|
| **Versión final** | Obligatoria en `dim_plan`, `dim_cliente` y **`hecho_suscripcion`**. Prohibida en factura y solicitud |
| **El estado nunca sale de `activo`** | Se lee `estado_derivado` |
| **Ingresos con signo** | Se suma `monto_con_signo`; las notas de crédito restan solas |
| **En disputa ≠ impaga** | Estados separados |
| **Ausencia ≠ cero** | Precio no mensualizable, solicitud pendiente, denominador vacío |
| **Mes natural** | MRR, NRR y variación; el resto acepta rango libre |
