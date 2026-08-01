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

Persistencia: defaults en `settings.SEGUIMIENTO_PARAMETROS` (config compartida / env).
Overrides auditables opcionales vía topic `Dim_ParametrosSeguimiento_topic` — **no** es tabla de dominio
del módulo seguimiento (contrato Fase 4: 0 tablas propias de dominio). Ver
`flujoscorreguidos/flujo-emergencias-canonico.md`.

## Tablas puente consumidas (no propias del módulo)

Agregadas al modelo el 2026-07-31: el código productivo ya las consultaba, pero no estaban
declaradas en `database/esquemas.json` ni creadas en Pinot, así que
`GET /api/v1/cliente/expedientes` respondía **500** (`TableDoesNotExistError`).
Ver `.specify/docs/changelog.md` D2.

| Tabla | Columnas | Clave primaria | Quién la consume |
|---|---|---|---|
| `Dim_Usuario_Cliente` | `idusuariocliente`, `idusuario`, `idcliente`, `activo`, `fecha_actualizacion` | `idusuariocliente` | `cliente_expediente_views._condados_cliente` (RF-SEG-006, RN-SEG-005) y `soporte_cliente/services/cliente_lookup_service` |
| `Dim_CondadoVecino` | `idcondadovecinorel`, `idcondado`, `idcondadovecino`, `activo`, `fecha_actualizacion` | `idcondadovecinorel` | `despacho/repositories/geografia_repository.list_condados_vecinos` (CU-O34, escalamiento de zona) |

`Dim_CondadoVecino` almacena la adyacencia en **ambos sentidos** (si A limita con B, existe
también la fila B→A), para que la consulta por `idcondado` funcione desde cualquiera de los
dos. Seed de referencia: `database/seed_vinculos.py`.

> **Nota de método:** estas tablas sí existían en el doble en memoria de `backend/conftest.py`,
> por lo que la suite de contratos pasaba al 100% mientras el endpoint real devolvía 500. Al
> agregar tablas al modelo, verificar que el doble y `database/esquemas.json` coincidan.

## Lectura paginada de históricos de alto volumen

Agregado el 2026-07-31 (ver `.specify/docs/changelog.md` B6/B7).

`Dim_HistorialUbicacionUnidadEmergencia` es la tabla de mayor crecimiento del sistema:
una unidad en misión publica una posición cada ~10 s, es decir ~2.900 filas por jornada
de 8 h **por unidad**. `Fact_HistorialEstadoUnidad` crece con cada cambio de estado.

Ninguna de las dos puede leerse completa desde un repositorio:

| Repositorio | Método | Contrato |
|---|---|---|
| `HistorialUbicacionRepository` | `list_by_unidad(id, desde?, hasta?, limit, cursor)` | Devuelve `(filas, cursor_siguiente)`; ventana temporal, orden y tope en el SQL; keyset sobre `idhistorialubicacion` |
| `HistorialUbicacionRepository` | `iter_by_unidad(id, desde?, hasta?)` | Generador que recorre la traza completa por bloques, para consumidores que sí la necesitan (depuración GPS, geofence, expediente) |
| `HistorialEstadoUnidadRepository` | `list_by_unidad(id, limit, cursor)` | Orden `fechahora DESC` y tope en el SQL; `get_current_estado` se apoya en `LIMIT 1` |

> **Por qué importa:** antes ambas se leían sin `LIMIT` y Pinot las recortaba en silencio
> a 10 filas (ver D1). El efecto no era de rendimiento sino de **corrección**: el estado
> vigente de una unidad se decidía sobre 10 filas arbitrarias de su historial, y el job de
> depuración GPS elegía qué puntos conservar mirando solo los 10 primeros de la traza.

