# Data Model — Evidencia en Sitio y Disponibilidad de Unidad

## Entidades principales

### 1) `Dim_EvidenciaFoto`

- **PK:** `idevidenciafoto` (INT)
- **FKs:** `idaccidente` → `Fact_Accidente`, `idusuario` → `Dim_Usuarios`
- **Campos:** `urlevidenciafoto` (STRING, URL Azure Blob), `sincronizado` (BOOLEAN, siempre `true` en backend), `fechahora` (epoch ms captura)
- **Reglas:**
  - Solo INSERT vía Kafka; sin UPDATE/DELETE.
  - Vinculación solo por `idaccidente` (RN-EVI-004).
  - Caso debe estar activo (no Cerrado/Descartado) — RN-EVI-006.
  - Binario en Azure Blob; Pinot solo metadata.

### 2) `Dim_NotaAccidente` (notas de campo CU-O27)

- **PK:** `idnotaaccidentes` (INT)
- **FKs:** `idaccidente`, `idusuario`
- **Campos:** `nota` (STRING), `tipo` (STRING enum campo), `sincronizado` (BOOLEAN, `true` en backend), `fechahora`, `fecha_actualizacion`
- **Tipos de campo (`tipo`):** Observación general, Declaración de testigo, Daños materiales, Condiciones del sitio
- **Reglas:**
  - INSERT-only en backend (RN-EVI-005).
  - Comparte tabla con notas `tipo=escalamiento` de `registro-accidente` (O40); filtrar por `tipo` en consultas.
  - Mismo topic Kafka `Dim_NotaAccidente_topic`.

### 3) `Fact_HistorialEstadoUnidad`

- **PK:** `idhistorialestadosunidadesemergencias` (INT)
- **FKs:** `idunidademergencia` → `Dim_UnidadEmergencia`, `idestadounidademergencia` → `Dim_EstadoUnidadEmergencia`, `idusuario` → `Dim_Usuarios`
- **Campos:** `estadoanterior`, `estadonuevo` (STRING), `fechahora` (epoch ms)
- **Reglas:**
  - Append-only inmutable (RN-EVI-003); sin UPDATE/DELETE.
  - Estado actual = fila con `fechahora` máxima por `idunidademergencia` (RN-EVI-010).
  - Sin historial → estado derivado **Fuera de servicio** (RN-EVI-011).
  - Compartida con `despacho-inteligente` (Ocupada al confirmar) y `seguimiento-cierre-de-casos` (Activa al cerrar).

### 4) `Dim_EstadoUnidadEmergencia` (catálogo lectura)

- Valores: Activa, Ocupada, En Misión, Fuera de servicio
- "En Misión" es de asignación exclusiva del sistema (no declarable vía POST manual, HTTP 422 si se intenta)
- Mapeo `estadonuevo` API ↔ `idestadounidademergencia`

### 5) `Dim_UnidadEmergencia` (catálogo lectura)

- Usado para validar `idunidademergencia` de sesión y filtros de flota
- `activo=true` requerido para despacho (consumido por `despacho-inteligente`)

## Almacenamiento local (cliente móvil — no en Pinot)

| Entidad local | Campos clave | Reglas |
|---------------|--------------|--------|
| `LocalEvidenciaFoto` | `local_id`, `idaccidente`, `blob_local`, `sincronizado=false`, `fechahora` | Solo dispositivo capturador (RN-EVI-013) |
| `LocalNotaAccidente` | `local_id`, `idaccidente`, `nota`, `tipo`, `sincronizado=false`, `fechahora` | Idem |

## Transiciones de disponibilidad

```text
Activa ←→ Ocupada            (manual)
Activa ←→ Fuera de servicio  (manual)
Activa → En Misión           (automático — despacho-inteligente)
En Misión → Activa           (automático — cierre caso / retiro, seguimiento-cierre-de-casos)
En Misión → Fuera de servicio  (automático, avería en atención)
Fuera de servicio → Activa   (manual)
(sin historial) → Fuera de servicio  (default derivado)
```

Transiciones automáticas por otros módulos (fuera de implementación directa de este plan, pero mismo topic):

- `despacho-inteligente` → En Misión al confirmar despacho
- `seguimiento-cierre-de-casos` → Activa al cerrar caso

## Transiciones de sincronización evidencia

```text
(local) sincronizado=false  →  (backend) sincronizado=true  [INSERT Kafka tras Blob OK]
(backend) sincronizado=true →  terminal (no revierte — RN-EVI-008)
```

## Eventos Kafka (escritura)

| Topic | Disparadores (este módulo) |
|-------|---------------------------|
| `Dim_EvidenciaFoto_topic` | Subida foto en línea; ítem exitoso en sync diferida |
| `Dim_NotaAccidente_topic` | Nota campo en línea; ítem exitoso en sync diferida |
| `Fact_HistorialEstadoUnidad_topic` | Declaración disponibilidad CU-O30 (`/mi-unidad-emergencia` o `/unidades-emergencia/{id}`) |

**Nota:** Escrituras de disponibilidad por `despacho-inteligente` y `seguimiento-cierre-de-casos` usan el mismo topic; este módulo no los duplica.

Lecturas: queries Pinot vía repositorios en `core/repositories/evidencia/` y `core/repositories/despacho/`.

## Azure Blob Storage

| Contenedor | Ruta sugerida | Campo Pinot |
|------------|---------------|-------------|
| `evidencia-accidentes` | `{idaccidente}/{idevidenciafoto\|local_id}.jpg` | `Dim_EvidenciaFoto.urlevidenciafoto` |

Compresión automática en cliente/servidor antes de subir (RNF-EVI-002).

## Validaciones de dominio

| Validación | HTTP | Regla |
|------------|------|-------|
| Caso inactivo (Cerrado/Descartado) | 422 | RN-EVI-006 |
| Foto > 10 MB | 413 | RNF-EVI-002 |
| `idaccidente` inexistente | 404 | RN-EVI-004 |
| Rol sin permiso galería | 403 | RN-EVI-012 |
| Unidad consulta otra unidad | 403 | RN-EVI-015 |
| Técnico consulta disponibilidad | 403 | RN-EVI-015 |
| Transición estado inválida | 422 | Diagrama sección 9 spec |

## RBAC resumen

| Recurso | Técnico de campo | Unidad de emergencia | Administrador | Servicio despacho |
|---------|------------------|----------------------|---------------|-------------------|
| Galería evidencia | ✓ | ✓ | ✓ | ✗ |
| Captura evidencia | ✓ | ✓ | ✗ | ✗ |
| Propia disponibilidad | ✗ | ✓ | ✗ | ✗ |
| Flota disponibilidad | ✗ | ✗ | ✓ | ✓ |

## Mapeo API ↔ persistencia

| Endpoint | Escritura | Lectura |
|----------|-----------|---------|
| `GET /accidentes/{id}/evidencias` | — | `Dim_EvidenciaFoto`, `Dim_NotaAccidente` (sincronizado=true) |
| `POST .../evidencias/fotos` | Blob + `Dim_EvidenciaFoto_topic` | — |
| `POST .../evidencias/notas` | `Dim_NotaAccidente_topic` | — |
| `POST .../evidencias/sincronizar` | Blob (fotos) + topics por ítem exitoso | — |
| `GET /unidades-emergencia` | — | `Dim_UnidadEmergencia` + último `Fact_HistorialEstadoUnidad` |
| `GET/POST .../disponibilidad` | `Fact_HistorialEstadoUnidad_topic` (POST) | `Fact_HistorialEstadoUnidad` (GET) |
| `GET .../historial-estado` | — | `Fact_HistorialEstadoUnidad` |

## Auditoría

Log estructurado: `captura_foto`, `captura_nota`, `sync_evidencia`, `cambio_disponibilidad` con `idusuario`, `idaccidente`/`idunidademergencia`, timestamp, resultado.
