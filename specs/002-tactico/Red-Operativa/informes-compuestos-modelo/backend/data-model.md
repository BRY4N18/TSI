# Data Model — Informes Compuestos de Red Operativa

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo **no define un modelo propio**: consume el
[modelo analítico](../../../modelo-analitico/) y le añade dos dimensiones y dos hechos.

---

## 1. Los 15 informes

**Cobertura:** ✅ el modelo lo sostiene hoy · 🟡 exige un atributo nuevo · 🆕 exige una tabla nueva.

### OT12 — Flota vigente y disponible *(8 informes)*

| # | Informe | Grano de salida | Fuente en el modelo | Cobertura |
|--:|---|---|---|:--:|
| 1 | Unidades por estado operativo | estado × período | `hecho_estado_unidad` | ✅ |
| 2 | Unidades de lote pendientes de primer acceso | unidad | `dim_unidad` | 🟡 alta y acceso |
| 3 | Rendimiento por proveedor | proveedor × período | `hecho_despacho` | ✅ |
| 4 | Cobertura de flota por región | región × condado × estado | `hecho_estado_unidad` + `dim_region` | 🆕 |
| 5 | Disponibilidad declarada | unidad × período | `hecho_estado_unidad` | ✅ |
| 6 | Condados en cobertura crítica, con vecinos | condado | `dim_geografia` + `dim_unidad` | 🟡 vecindad |
| 7 | Rotación de flota: altas frente a bajas | proveedor × período | `hecho_baja_unidad` + `dim_unidad` | 🆕 |
| 8 | Bajas forzadas con caso en curso | proveedor × período | `hecho_baja_unidad` | 🆕 |

**#1 y #5 se apoyan en el hecho de estado, no en el catálogo del origen** (research D2). El estado se
agrupa **por su texto**, así que «En Misión» aparece pese a no estar definido en
`Dim_EstadoUnidadEmergencia`.

**#5 mide tiempo, no transiciones** (research D4). Una unidad activa todo el período **no tiene
ninguna transición dentro de él**: medida por transiciones, su disponibilidad saldría 0 %, que es lo
contrario de la verdad.

### OT11 — Abrir regiones *(4 informes)*

| # | Informe | Grano de salida | Fuente en el modelo | Cobertura |
|--:|---|---|---|:--:|
| 9 | Tiempo de puesta en operación `[NORMATIVO ≤30 días]` | región | `dim_region` | 🆕 |
| 10 | Mercados activos: regiones con ≥1 cliente activo | región | `dim_region` | 🆕 |
| 11 | Tasa de aprobación al primer intento, **por región** | región | `hecho_validacion_region` | 🆕 |
| 12 | Motivos de rechazo más frecuentes | motivo | `hecho_validacion_region` | 🆕 |

**#11 entrega menos de lo que pide el catálogo**: sin desglose por validador, que es identidad de
persona. Misma decisión que con el técnico de campo en Emergencias.

**#9 solo mide las regiones que llegaron a producción.** Una región que aún no ha llegado no lleva
«0 días» ni incumple el indicador normativo: queda fuera y se cuenta aparte.

### OT13 — Retirar regiones *(3 informes)*

| # | Informe | Grano de salida | Fuente en el modelo | Cobertura |
|--:|---|---|---|:--:|
| 13 | Regiones en riesgo: publicadas bajo el umbral | región | `dim_region` + `hecho_estado_unidad` | 🆕 |
| 14 | Casos activos al despublicar, por región | región | `dim_region` + `hecho_accidente` | 🆕 ⚠️ |
| 15 | Tiempo entre pérdida de cobertura y despublicación | región | `dim_region` + `hecho_estado_unidad` | 🆕 ⚠️ |

⚠️ **#14 y #15 miden desde la primera carga del modelo.** El origen nunca guardó cuándo cambiaba el
estado de una región, así que no hay despublicaciones anteriores que mostrar. Ambos informes lo
declaran (FR-034) en vez de presentar un histórico vacío como si significara «nunca pasó».

---

## 2. Las ampliaciones del modelo

### 2.1 `dim_region` — dimensión **versionada**

```sql
CREATE TABLE IF NOT EXISTS dim_region (
    sk_region         UInt64,          -- clave de la VERSIÓN
    idregionoperativa Int32,           -- clave de negocio
    nombre_region     String,
    estado_ciclo_vida String,          -- Definida | En validación | Producción | Despublicada
    idestado_geo      Nullable(Int32),
    estado_geo        Nullable(String),
    pais              Nullable(String),

    valido_desde      DateTime,
    valido_hasta      Nullable(DateTime),
    es_vigente        UInt8,
    inicio_es_real    UInt8,           -- 0 = "desde la primera carga"
    version           DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY (idregionoperativa, valido_desde)
```

⚠️ **`estado_ciclo_vida` y `estado_geo` son cosas distintas y el origen las confunde.** El primero es
Producción o Despublicada; el segundo es «Ciudad de Mexico». La tabla del origen llamada
`Dim_RegionOperativaEstadoRegion` guarda **el segundo**, pese a que el catálogo de informes la citaba
como fuente del primero. Nombrarlos distinto aquí es lo que impide repetir la confusión.

**Todas las versiones iniciales llevan `inicio_es_real = 0`**, igual que la unidad: el estado se
conoce, pero no desde cuándo.

**Atributos versionados** (un cambio en ellos abre versión): `estado_ciclo_vida`.

### 2.2 `dim_geografia` — dos atributos nuevos

```sql
ALTER TABLE dim_geografia ADD COLUMN condados_vecinos Array(Int32);
ALTER TABLE dim_geografia ADD COLUMN idregionoperativa Nullable(Int32);
```

La vecindad es una **relación estática entre entidades ya modeladas**: no tiene instante ni grano
propio, así que es un atributo y no un hecho (research D3).

### 2.3 `dim_unidad` — dos atributos nuevos

```sql
ALTER TABLE dim_unidad ADD COLUMN fecha_alta        Nullable(DateTime);
ALTER TABLE dim_unidad ADD COLUMN tuvo_primer_acceso UInt8;
```

⚠️ **No son atributos versionados**: el alta de una unidad no cambia, y su primer acceso ocurre una
vez. Incluirlos entre los versionados haría que cada primer acceso abriera una versión y llenara la
dimensión de ruido.

### 2.4 `hecho_baja_unidad` — hecho de transacción

```sql
CREATE TABLE IF NOT EXISTS hecho_baja_unidad (
    idbaja             Int32,
    fecha              Date,
    fechahora          DateTime,

    sk_unidad          UInt64,          -- versión vigente al darse de baja
    idunidademergencia Int32,
    unidad             String,
    proveedor          String,          -- el DE ESE MOMENTO
    idcondado          Nullable(Int32),
    condado            Nullable(String),

    tipo_baja          String,          -- Normal | Forzada | Forzada_con_reasignación
    motivo             Nullable(String),
    con_caso_en_curso  UInt8,
    idaccidente        Nullable(String),

    dias_en_flota      Nullable(Int32),

    cargado_en         DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idunidademergencia)
```

**`con_caso_en_curso` se deriva** de que la baja traiga un accidente asociado — el origen lo registra
en `idaccidente`. Es lo que distingue una baja ordenada de una que dejó un caso a medias.

**`motivo` se conserva** porque es un campo corto y clasificable del catálogo operativo, no una nota
libre del usuario. Si en el futuro admitiera texto redactado, saldría del modelo.

### 2.5 `hecho_validacion_region` — hecho de transacción

```sql
CREATE TABLE IF NOT EXISTS hecho_validacion_region (
    idvalidacion      Int32,
    fecha             Date,
    fechahora         DateTime,

    sk_region         UInt64,          -- versión de región vigente al validar
    idregionoperativa Int32,
    nombre_region     String,

    resultado         String,          -- Aprobada | Rechazada
    motivo            Nullable(String),
    numero_intento    UInt8,           -- 1 = primer intento sobre esa región

    cargado_en        DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idregionoperativa, idvalidacion)
```

**`numero_intento` es lo que hace calculable la tasa de aprobación al primer intento**, exactamente
igual que en el hecho de despacho: son los intentos con ordinal 1 y resultado aprobado. Sin él, una
región rechazada dos veces y aprobada a la tercera contaría como aprobada.

⚠️ **`idusuario` no se copia**, aunque el origen lo trae: el validador es una persona (FR-021).

### 2.6 Lo que NO se añade

| Se pidió | No se añade | Motivo |
|---|---|---|
| Dimensión de estado de unidad | Nada; se agrupa por texto | El catálogo del origen **no define el estado 4** |
| Hecho de vecindad entre condados | Atributo de `dim_geografia` | Sin instante ni grano propio; serían 2 filas con su DAG |
| Desglose por validador | Nada | Identidad de persona |
| Hecho de alta de unidad | Columna de `dim_unidad` | El alta no es un suceso con vida propia |

---

## 3. Reglas de consulta heredadas

| Regla | Aplicada aquí |
|---|---|
| **Versión final** | Obligatoria en `dim_region`, `dim_unidad` y `dim_geografia`. **Prohibida** en `hecho_estado_unidad`, `hecho_baja_unidad` y `hecho_validacion_region` |
| **Ausencia ≠ cero** | Disponibilidad sin transiciones, tiempo de puesta en operación de una región que no llegó a producción, tasa sobre cero validaciones |
| **Lo desconocido cuenta** | Un condado sin vecinos declarados aparece igualmente, señalado |
| **El grano es el intento** | En validaciones, igual que en despachos |
