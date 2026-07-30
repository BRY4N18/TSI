# Data Model — Despacho Inteligente

## Entidades principales (escritura vía Kafka)

### 1) `Fact_Despacho` (N-N caso ↔ unidad)

- **PK:** `iddespacho` (INT)
- **FKs:** `idaccidente` → `Fact_Accidente`, `idunidademergencia` → `Dim_UnidadEmergencia`, `idnotificaciondespacho` → `Fact_NotificacionDespacho`, `idorigendespacho` → `Dim_OrigenDespacho`
- **Campos:** `activo` (BOOLEAN), `fechahoradespacho`, `fechahorallegada`, `fechahoraretiro`, `fecha_actualizacion`
- **Reglas:**
  - Una fila por intento de asignación (RN-DES-009).
  - `activo=true` mientras Pendiente o Confirmado; `false` en Rechazado, Timeout o fallo entrega (clarificación Session 2026-07-09).
  - Una unidad solo un `activo=true` global (RN-DES-002).
  - Un caso puede tener múltiples `activo=true` (despacho múltiple O38).

### 2) `Fact_NotificacionDespacho`

- **PK:** `idnotificaciondespacho` (INT)
- **FKs:** `idaccidente`, `idunidaddemergencia` *(nombre esquema Pinot)*
- **Campos:** `estadonotificaciondespacho` (Pendiente | Notificada | Confirmada | Rechazada | No_entregada), `motivo`, `numheridos`, `numvehiculos`, `activo`, `fecha_actualizacion`
- **Reglas:** Una notificación por intento; motivo obligatorio en Rechazada; fallo O23 → No_entregada.

### 3) `Fact_HistorialDespachoUnidad`

- **PK:** `idhistorialdespachounidad` (INT)
- **FKs:** `iddespacho`, `idestadodespacho` → `Dim_EstadoDespacho`
- **Campos:** `estadoanterior`, `estadonuevo`, `fechahora`, `fecha_actualizacion`
- **Estados:** Pendiente, Confirmado, Rechazado, Timeout, Abortado, En_sitio, Retirado
- **Regla:** Append-only; estado actual = última fila por `fechahora`.

### 4) `Fact_HistorialEstadoUnidad`

- **PK:** `idhistorialestadounidad` (INT)
- **FKs:** `idunidademergencia`, `idestadounidademergencia` → `Dim_EstadoUnidadEmergencia`
- **Reglas:** Confirmación O24 → En Misión; rechazo mantiene Activa (RN-DES-006).

### 5) `Fact_AccidenteTipoEstadoAccidente`

- **Transiciones despacho:** REPORTADO → BUSCANDO_UNIDAD (primer despacho) → ASIGNADO (primer Confirmado).

### 6) `Dim_NotaAccidente`

- **Uso O34:** alerta "Sin unidades disponibles en condado ni condados vecinos" (`tipo=alerta`).

## Entidades de lectura

| Entidad | Uso en módulo |
|---------|---------------|
| `Fact_Accidente` | Trigger O22, coordenadas, severidad, `idcalle`, `descripcion` |
| `Dim_UnidadEmergencia` | Candidatas, `latitud`/`longitud`, `idcondado` (reemplaza a `zonacobertura`, ver migración 2026-07-21), `tipounidademergencia` |
| `Dim_HistorialUbicacionUnidadEmergencia` | GPS más reciente que snapshot (RN-DES-010) |
| `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado` | Filtro condado O22; vecinos O34 |
| `Dim_Severidad` | Concordancia tipo unidad |
| `Dim_EstadoDespacho`, `Dim_OrigenDespacho`, `Dim_EstadoUnidadEmergencia` | Catálogos |

## Parámetros configurables (RF-DES-010)

Persistencia propuesta: tabla/config Pinot `Dim_ParametrosDespacho` o clave en servicio de configuración con audit log. Campos:

| Parámetro | Default | Rango |
|-----------|---------|-------|
| `timeout_respuesta_seg` | 90 | 30–300 |
| `peso_distancia_pct` | 60 | 40–80 |
| `peso_concordancia_pct` | 25 | — |
| `peso_disponibilidad_pct` | 15 | — |
| `prioridades_por_severidad` | JSON mapping | — |
| `keywords_severidad_moderada` | `["herido","ambulancia"]` | — |

## Transiciones de estado

### Caso (`Dim_TipoEstadoAccidente`)

```text
REPORTADO → BUSCANDO_UNIDAD   (primer Fact_Despacho creado)
BUSCANDO_UNIDAD → ASIGNADO    (primer despacho Confirmado)
BUSCANDO_UNIDAD → (alerta)    (sin candidatas / escalamiento fallido)
```

### Despacho (por `iddespacho`)

```text
Pendiente → Confirmado     (O24) — activo=true
Pendiente → Rechazado      (O45) — activo=false → O36 síncrono
Pendiente → Timeout        (O35) — activo=false → evento → O36 async
Pendiente → No_entregada   (O23 fallo) — activo=false → O36 síncrono
```

## Eventos Kafka

### Topics de tabla (Pinot ingest)

| Topic | Productor | Disparador |
|-------|-----------|------------|
| `Fact_Despacho_topic` | `DespachoRepository` | O22, O33, O34, O36, O38 |
| `Fact_NotificacionDespacho_topic` | `NotificacionDespachoRepository` | O22–O23, O24, O45 |
| `Fact_HistorialDespachoUnidad_topic` | `HistorialDespachoRepository` | Todas transiciones |
| `Fact_HistorialEstadoUnidad_topic` | `HistorialEstadoUnidadRepository` | O24 confirmación |
| `Fact_AccidenteTipoEstadoAccidente_topic` | `EstadoAccidenteRepository` | BUSCANDO_UNIDAD, ASIGNADO |
| `Dim_NotaAccidente_topic` | `NotaAccidenteRepository` | O34 sin unidades |

### Topic de dominio (solo orquestación)

| Topic | Productor | Consumidor |
|-------|-----------|------------|
| `DespachoTimeout_topic` | Job O35 | Worker `ReasignacionDespachoConsumer` (O36) |
| `AccidenteReportado_topic` *(o filtro en estado topic)* | registro-accidente | `AsignacionAutomaticaConsumer` (O22) |

## Índices / consultas Pinot críticas

- Candidatas activas por condado: join unidad + último historial estado + sin `Fact_Despacho.activo` global.
- Despachos pendientes timeout: `Fact_Despacho.activo=true` + último historial Pendiente + `fechahoradespacho` < now - timeout.
- Monitoreo caso: todos los `Fact_Despacho` + historial + notificaciones por `idaccidente`.
