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
  - `EvidenciaFotoRepository.list_by_accidente` filtra `sincronizado`, ordena por
    `fechahora DESC` y pagina por cursor (`idevidenciafoto`) **en el SQL**, no en
    Python. Corregido 2026-07-31 (`.specify/docs/changelog.md` B9): antes la
    consulta base no declaraba `LIMIT` y Pinot la recortaba a 10 filas antes de
    que el filtro/orden se aplicara — un accidente con más de 10 fotos podía
    perder evidencia real de la galería sin error visible.

### 2) `Dim_NotaAccidente` (notas de campo CU-O74)

- **PK:** `idnotaaccidentes` (INT)
- **FKs:** `idaccidente`, `idusuario`
- **Campos:** `nota` (STRING), `tipo` (STRING enum campo), `sincronizado` (BOOLEAN, `true` en backend), `fechahora`, `fecha_actualizacion`
- **Tipos de campo (`tipo`):** Observación general, Declaración de testigo, Daños materiales, Condiciones del sitio
- **Reglas:**
  - INSERT-only en backend (RN-EVI-005).
  - Comparte tabla con notas `tipo=escalamiento` de `registro-accidente` (O73); filtrar por `tipo` en consultas.
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

### 6) `Dim_ElementoClimaticosAccidente` (CU-O75 — clima/período en sitio)

- **PK:** `idelementoclimaticoaccidente` (INT)
- **FKs:** `idaccidente` → `Fact_Accidente`, `idperiododia` → `Dim_PeriodosDias`, `idestadoclima` → `Dim_EstadosClimas`, `idusuario` → `Dim_Usuarios`
- **Campos:** `activo` (BOOLEAN), `fecha_actualizacion`
- **Reglas:** Como máximo una fila `activo=true` por `idaccidente` (RN-EVI-017). Upsert vía Kafka. **Dueño exclusivo de escritura:** Técnico/Unidad en este módulo (CU-O75). Sin precarga desde `registro-accidente`.
- **Topic:** `Dim_ElementoClimaticosAccidente_topic`.

### 7) `Dim_ElementoFisicoAccidente` (CU-O75 — elementos físicos)

- **PK:** `idelementosfisicosaccidente` (INT)
- **FKs:** `idaccidente`, `idelementofisico` → `Dim_Elementos_Fisicos`, `idusuario`
- **Campos:** `activo`, `fecha_actualizacion`
- **Reglas:** N elementos por accidente; soft-delete con `activo=false`. Escritura solo CU-O75.
- **Topic:** `Dim_ElementoFisicoAccidente_topic`.

### 8) Catálogos de lectura (enriquecimiento)

| Tabla | Uso |
|-------|-----|
| `Dim_PeriodosDias` | Selector `idperiododia` |
| `Dim_EstadosClimas` | Selector `idestadoclima` |
| `Dim_Elementos_Fisicos` | Selector `idelementofisico` |
| `Dim_Estado_Conductor` | 4 checkboxes (flags BOOLEAN); `idestadoconductor` por match exacto (seed 16 combinaciones) |

### 9) `Dim_Conductor` / `Dim_Vehiculo` / `Fact_Conductor_Accidente` (CU-O76)

#### `Dim_Conductor`
- **PK:** `idconductor`
- **Campos:** `apellidos`, `nombres`, `identificacion`, `genero`, `tipolicencia`, `estadolicencia`, `ciudadresidencia`, `aniosexperiencia`, `activo`, `fecha_actualizacion` (auditoría Kafka/Pinot; no en ER de negocio)
- **Captura UI:** required = `identificacion`, `nombres`, `apellidos`; resto opcionales (RF-EVI-009)
- **Regla:** Reutilizar por `identificacion` activa (RN-EVI-019). Topic propuesto: `Dim_Conductor_topic`.

#### `Dim_Vehiculo`
- **PK:** `idvehiculo`
- **Campos:** `tipovehiculo`, `modelovehiculo`, `categoriausovehiculo`, `mercanciapeligrosa`, `ejes`, `activo`, `fecha_actualizacion` (auditoría)
- **Captura UI:** required = `tipovehiculo`; resto opcionales (RF-EVI-009)
- Topic propuesto: `Dim_Vehiculo_topic`.

#### `Fact_Conductor_Accidente`
- **PK:** `idconductoraccidente`
- **FKs:** `idaccidente`, `idconductor`, `idestadoconductor`, `idvehiculo`, `idusuario`
- **Campos:** `activo`, `fecha_actualizacion`
- **Reglas:** Hasta `numvehiculos` del caso (RN-EVI-022); soft-delete `activo=false`. Topic propuesto: `Fact_Conductor_Accidente_topic`.

### 10) `Dim_Implicado` (CU-O76 — involucrados no conductores)

Alineado a ontología dimensional / `database/esquemas.json` (autoridad confirmada 2026-07-29).

- **PK:** `idimplicado` (INT)
- **FK:** `idaccidente` → `Fact_Accidente` (STRING en runtime Pinot)
- **Campos de negocio:**
  - `tipoimplicado` (STRING: Peaton / Pasajero / Testigo / Otro) — requerido
  - `genero` (STRING) — opcional
  - `estadoimplicado` (STRING: Ileso / Lesionado / Fallecido / Desconocido) — requerido
  - `edad` (INT ≥ 0) — opcional
  - `activo` (BOOLEAN)
- **Auditoría infra:** `fecha_actualizacion` (LONG epoch ms)
- **Fuera de esta tabla:** `identificacion`, `nombres`, `apellidos`, `rolobservado`, `lesionado`, `observacion`, `idusuario` (no pertenecen a la ontología)
- **Reglas:** Solo vinculación por `idaccidente` (nunca `iddespacho`). Soft-delete `activo=false`. RF-EVI-010. Sin PII de identidad → offline sin cifrado obligatorio (a diferencia de `Dim_Conductor`).
- **Topic:** `Dim_Implicado_topic` (ya en `tablas.json` / settings). **No alterar schema Pinot** salvo cambio explícito de ontología.

## Almacenamiento local (cliente móvil — no en Pinot)

| Entidad local | Campos clave | Reglas |
|---------------|--------------|--------|
| `LocalEvidenciaFoto` | `local_id`, `idaccidente`, `blob_local`, `sincronizado=false`, `fechahora` | Solo dispositivo capturador (RN-EVI-013) |
| `LocalNotaAccidente` | `local_id`, `idaccidente`, `nota`, `tipo`, `sincronizado=false`, `fechahora` | Idem |
| `LocalElementoClimatico` | `local_id`, `idaccidente`, `idperiododia`, `idestadoclima`, `sincronizado=false` | CU-O75 offline |
| `LocalElementoFisico` | `local_id`, `idaccidente`, `idelementofisico`, `sincronizado=false` | CU-O75 offline |
| `LocalConductorAccidente` | `local_id`, `idaccidente`, **payload_cifrado** (PII), `sincronizado=false`, `fechahora` | CU-O76 offline; **RN-EVI-020/021** — nunca PII en claro; borrar tras sync |
| `LocalImplicado` | `local_id`, `idaccidente`, `tipoimplicado`, `estadoimplicado`, `genero?`, `edad?`, `sincronizado=false`, `fechahora` | CU-O76 offline; **sin PII** (ontología) |

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
| `Dim_ElementoClimaticosAccidente_topic` | Upsert clima/período en sitio (CU-O75); sync diferida |
| `Dim_ElementoFisicoAccidente_topic` | Alta/soft-delete elemento físico (CU-O75); sync diferida |
| `Dim_Conductor_topic` | Alta conductor nuevo en sitio |
| `Dim_Vehiculo_topic` | Alta vehículo nuevo en sitio |
| `Fact_Conductor_Accidente_topic` | Vínculo conductor-vehículo-accidente; soft-delete |
| `Dim_Implicado_topic` | Alta / soft-delete implicado no conductor (CU-O76 RF-EVI-010); sync diferida |
| `Fact_HistorialEstadoUnidad_topic` | Declaración disponibilidad CU-O78 (`/mi-unidad-emergencia` o `/unidades-emergencia/{id}`) |

**Nota:** Escrituras de disponibilidad por `despacho-inteligente` y `seguimiento-cierre-de-casos` usan el mismo topic; este módulo no los duplica. **Este módulo es el único dueño de escritura** de puentes clima/físico, conductores e implicados en runtime (CU-O75/CU-O76); `registro-accidente` no precarga esos datos.

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
| Enriquecimiento clima/físico (CU-O75) | ✓ | ✓ | lectura | ✗ |
| Conductores/vehículos (CU-O76) | ✓ | ✓ | lectura | ✗ |
| Implicados no conductores (CU-O76) | ✓ | ✓ | lectura | ✗ |
| Propia disponibilidad | ✗ | ✓ | ✗ | ✗ |
| Flota disponibilidad | ✗ | ✗ | ✓ | ✓ |

## Mapeo API ↔ persistencia

| Endpoint | Escritura | Lectura |
|----------|-----------|---------|
| `GET /accidentes/{id}/evidencias` | — | `Dim_EvidenciaFoto`, `Dim_NotaAccidente` (sincronizado=true) |
| `POST .../evidencias/fotos` | Blob + `Dim_EvidenciaFoto_topic` | — |
| `POST .../evidencias/notas` | `Dim_NotaAccidente_topic` | — |
| `POST .../evidencias/sincronizar` | Blob (fotos) + topics por ítem exitoso (incl. enriquecimiento) | — |
| `GET/PUT .../enriquecimiento/clima` | `Dim_ElementoClimaticosAccidente_topic` | puente + catálogos |
| `GET/POST/PATCH .../enriquecimiento/elementos-fisicos` | `Dim_ElementoFisicoAccidente_topic` | puente + `Dim_Elementos_Fisicos` |
| `GET/POST/PATCH .../enriquecimiento/conductores` | `Dim_Conductor_topic`, `Dim_Vehiculo_topic`, `Fact_Conductor_Accidente_topic` | joins |
| `GET /catalogos/periodos-dias` etc. | — | catálogos Pinot |
| `GET /unidades-emergencia` | — | `Dim_UnidadEmergencia` + último `Fact_HistorialEstadoUnidad` |
| `GET/POST .../disponibilidad` | `Fact_HistorialEstadoUnidad_topic` (POST) | `Fact_HistorialEstadoUnidad` (GET) |
| `GET .../historial-estado` | — | `Fact_HistorialEstadoUnidad` |

## Auditoría

Log estructurado: `captura_foto`, `captura_nota`, `sync_evidencia`, `cambio_disponibilidad`, `enriquecer_clima`, `enriquecer_elemento_fisico`, `registrar_conductor_accidente` con `idusuario`, `idaccidente`/`idunidademergencia`, timestamp, resultado.
