# Data Model — Seguimiento y Cierre de Casos

## Entidades principales (escritura vía Kafka)

### 1) `Dim_HistorialUbicacionUnidadEmergencia` (trayectoria GPS)

- **PK:** `idhistorialubicacion` (INT) — propuesto
- **FKs:** `idunidademergencia`, `idaccidente`
- **Campos:** `latitud`, `longitud`, `fechahora` (epoch ms), `fecha_actualizacion`
- **Reglas:**
  - Append-only; una fila cada ~10s mientras despacho en estado Confirmado (RF-SEG-001).
  - Topic: `Dim_HistorialUbicacionUnidadEmergencia_topic` *(añadir a `KAFKA_TOPICS`)*.
  - Depuración post-90d: conservar 3 puntos por `iddespacho` (RNF-SEG-004).

### 2) `Dim_UnidadEmergencia` (snapshot posición)

- **Campos mutados:** `latitud`, `longitud`, `fecha_actualizacion`
- **Topic:** `Dim_UnidadEmergencia_topic` *(añadir a `KAFKA_TOPICS`)*.
- **Regla:** Actualizado en cada ingestión GPS O25.

### 3) `Fact_Despacho` (tiempos de seguimiento)

- **Campos mutados en este módulo:** `fechahorallegada`, `fechahoraretiro`, `fecha_actualizacion`
- **Topic:** `Fact_Despacho_topic` (existente).
- **Reglas:** N-N caso ↔ unidad; cierre caso cuando todos tienen `fechahoraretiro` (RN-SEG-008).

### 4) `Fact_HistorialDespachoUnidad`

- **Campos:** `iddespacho`, `idestadodespacho`, `idusuario` (operador/unidad ejecutor), `fechahora`
- **Transiciones este módulo:** Confirmado → En_sitio (O26), En_sitio → Retirado (O28/O42/O44), Confirmado → Abortado (O39)
- **Topic:** `Fact_HistorialDespachoUnidad_topic` (existente).
- **Regla:** Append-only (RNF-SEG-006).

### 5) `Fact_Accidente`

- **Campos mutados:** `horafin`, `duracionminutos`, `numvehiculos`, `numvictimas`, `numheridos`, `numfallecidos` (solo O28)
- **Topic:** `Fact_Accidente_topic` (existente).

### 6) `Fact_AccidenteTipoEstadoAccidente`

- **Transiciones:** ASIGNADO → EN_ATENCION (primera llegada O26), * → CERRADO (todos despachos Retirado)
- **Topic:** `Fact_AccidenteTipoEstadoAccidente_topic` (existente).

### 7) `Fact_HistorialEstadoUnidad`

- **Uso:** Liberar unidad a Activa (O28/O42) o restaurar Fuera de servicio (RN-SEG-003); Abortado O39 → Activa.
- **Topic:** `Fact_HistorialEstadoUnidad_topic` (existente).

### 8) `Dim_NotaAccidente`

- **Uso:** Motivo O42; alerta GPS O37 (`tipo=alerta`, `idusuario=Sistema`).
- **Topic:** `Dim_NotaAccidente_topic` (existente).

## Entidades de lectura

| Entidad | Uso en módulo |
|---------|---------------|
| `Fact_NotificacionDespacho` | Expediente O29 |
| `Dim_EstadoDespacho` | Historial despacho |
| `Dim_EvidenciaFoto` | Expediente (excluido O42) |
| `Dim_Preferencias_Cliente` | Filtro condado cliente |
| `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado` | Filtro expedientes + mapa |
| `Dim_TipoEstadoAccidente` | Estados caso |
| `Dim_Severidad` | Marcadores mapa por color |

## Campos de cierre O28 (RF-SEG-004)

Persistidos en `Fact_Accidente` y/o tabla auxiliar `Fact_CierreAccidente` si se normaliza en implementación:

| Campo | Tipo | O28 | O42 |
|-------|------|-----|-----|
| `resultado_atencion` | string | requerido | N/A |
| `calificacion` | int 1-5 | opcional | N/A |
| `observaciones_finales` | string | opcional | N/A |
| `motivo_cancelacion` | string | N/A | `Dim_NotaAccidente` |

## Transiciones de estado

### Caso

```text
ASIGNADO → EN_ATENCION     (primera llegada O26)
EN_ATENCION → CERRADO      (todos despachos Retirado — O28/O42/O44)
```

### Despacho (en este módulo)

```text
Confirmado → En_sitio      (O26 manual o geofencing)
Confirmado → Abortado      (O39) → evento DespachoAbortado → O36
En_sitio → Retirado        (O28, O42, O44)
```

## Eventos Kafka

### Topics de tabla

| Topic | Productor | Disparador |
|-------|-----------|------------|
| `Dim_HistorialUbicacionUnidadEmergencia_topic` | `HistorialUbicacionRepository` | O25 GPS |
| `Dim_UnidadEmergencia_topic` | `UnidadEmergenciaSnapshotRepository` | O25 GPS |
| `Fact_Despacho_topic` | `DespachoRepository` | O26/O28/O42/O44 tiempos |
| `Fact_HistorialDespachoUnidad_topic` | `HistorialDespachoRepository` | O26/O28/O39/O42/O44 |
| `Fact_HistorialEstadoUnidad_topic` | `HistorialEstadoUnidadRepository` | O28/O39/O42 liberación |
| `Fact_Accidente_topic` | `AccidenteRepository` | O28/O42 cierre |
| `Fact_AccidenteTipoEstadoAccidente_topic` | `EstadoAccidenteRepository` | EN_ATENCION, CERRADO |
| `Dim_NotaAccidente_topic` | `NotaAccidenteRepository` | O37, O42 |

### Topics de dominio (orquestación)

| Topic | Productor | Consumidor |
|-------|-----------|------------|
| `DespachoAbortado_topic` | `AbortarMisionService` (seguimiento) | `ReasignacionDespachoConsumer` (despacho O36) |

## Consultas Pinot críticas

- Mapa activo: accidentes estado ∉ {CERRADO} + unidades con último estado + posición snapshot/GPS.
- Unidades en camino sin GPS reciente: `MAX(fechahora)` historial vs now — job O37.
- Historial operador: `Fact_Accidente` + filtros fecha/estado/severidad/unidad.
- Expediente cliente: join completo + filtro condado vía `GeografiaRepository`.
- Depuración GPS: casos CERRADO con `horafin` < now - 90d.

## Parámetros configurables

| Parámetro | Default | RF/RNF |
|-----------|---------|--------|
| `gps_umbral_senal_perdida_seg` | 60 | RNF-SEG-005 |
| `gps_job_intervalo_seg` | 30 | RNF-SEG-005 |
| `geofence_radio_metros` | 100 | RNF-SEG-002 |
| `geofence_histéresis_seg` | 30 | RNF-SEG-002 |
| `gps_retencion_dias` | 90 | RNF-SEG-004 |

Persistencia propuesta: `Dim_ParametrosSeguimiento` o extensión de configuración existente con audit log.
