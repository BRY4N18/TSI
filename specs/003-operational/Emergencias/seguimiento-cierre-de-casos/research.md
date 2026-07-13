# Phase 0 Research — Seguimiento y Cierre de Casos

## Decision 1: Contract-first OpenAPI bajo `/api/v1/seguimiento`, `/api/v1/mi-seguimiento`, `/api/v1/emergencias` y `/api/v1/cliente`

- **Decision:** Definir primero `contracts/seguimiento-cierre-de-casos.openapi.yaml` con endpoints HTTP para CU-O25/O26/O28/O29/O39/O42/O44 y RF-SEG-005–007; flujos O37 (job GPS), geofencing O26 y depuración GPS (RNF-SEG-004) como jobs/servicios internos sin endpoint público.
- **Rationale:** Orden solicitado (contrato REST → Django → Angular); constitution API-First; habilita contract tests y tipos TypeScript.
- **Alternatives considered:**
  - Reutilizar solo rutas `/despacho/*` (rechazado: despacho cubre asignación; seguimiento tiene ciclo de vida distinto post-confirmación).
  - Contrato Markdown sin OpenAPI (rechazado: sin validación automática).

## Decision 2: Nueva app Django `apps/seguimiento/` (tercera app Emergencias)

- **Decision:** Crear `apps/seguimiento/` con Vista → Servicio → Repositorio; repositorios en `core/repositories/seguimiento/` reutilizando lectura de `core/repositories/despacho/` donde aplique (`DespachoRepository`, `HistorialDespachoRepository`, `GeografiaRepository`).
- **Rationale:** `module-map.md` lista spec propio; volumen CU-O25–O44 y jobs independientes justifican separación de `despacho/` (misma excepción documentada que accidentes/despacho en `project-structure.md`).
- **Alternatives considered:**
  - Extender solo `apps/despacho/` (rechazado: acoplamiento y mezcla asignación vs. cierre).

## Decision 3: Escritura exclusiva vía Kafka

- **Decision:** Mutaciones en `Dim_HistorialUbicacionUnidadEmergencia`, `Dim_UnidadEmergencia`, `Fact_Despacho`, `Fact_HistorialDespachoUnidad`, `Fact_HistorialEstadoUnidad`, `Fact_Accidente`, `Fact_AccidenteTipoEstadoAccidente`, `Dim_NotaAccidente` publican a `{Tabla}_topic`.
- **Rationale:** Regla vinculante `architectural-patterns.md`; añadir `historial_ubicacion_unidad` y `unidad_emergencia_snapshot` a `KAFKA_TOPICS` en settings.
- **Alternatives considered:**
  - INSERT directo Pinot para GPS 10s (rechazado: viola arquitectura).

## Decision 4: SSE para mapa operador (clarificación Session 2026-07-09)

- **Decision:** `GET /api/v1/seguimiento/stream` con `Accept: text/event-stream`; eventos `seguimiento.posicion`, `seguimiento.eta`, `seguimiento.estado`, `seguimiento.alerta_gps`. Pub/sub interno al recibir GPS o cambio de estado.
- **Rationale:** Alineado RF-SEG-007, `api-standards.md` y patrón RF-DES-011.
- **Alternatives considered:**
  - Polling REST cada 10s (rechazado en clarify).

## Decision 5: JWT + RBAC (skills `api-authentication`, `django-expert`)

- **Decision:** Bearer JWT RS256; permisos DRF en `apps/seguimiento/permissions.py`:
  - `Operador de emergencias` → mapa, SSE, historial completo, cerrar, cancelar, forzar retiro O44.
  - `Unidad de emergencia` → `mi-seguimiento/*` (GPS, llegada, abortar, cerrar/cancelar propio caso).
  - `Cliente` → solo `cliente/expedientes/*` (cerrados, filtro condado); HTTP 403 en mapa/SSE/activos.
- **Rationale:** RN-SEG-005/006; validación servidor obligatoria.
- **Alternatives considered:**
  - Guards Angular únicamente (rechazado: seguridad).

## Decision 6: Geofencing O26 en pipeline de ingestión GPS

- **Decision:** `RegistrarPosicionGpsService` evalúa radio 100m + histéresis 30s tras cada POST posición; si cumple y no hay llegada previa, registra En_sitio automáticamente y notifica unidad.
- **Rationale:** RF-SEG-002/RNF-SEG-002; evita job separado y reduce latencia.
- **Alternatives considered:**
  - Job batch cada 10s (rechazado: mayor latencia llegada automática).

## Decision 7: O39 aborto → re-asignación O36 vía Kafka (sin llamada directa a despacho)

- **Decision:** `AbortarMisionService` publica evento dominio `DespachoAbortado_topic`; consumer en `apps/despacho/` invoca `ReasignacionDespachoService` (O36).
- **Rationale:** `architectural-patterns.md` — comunicación inter-módulo solo Kafka.
- **Alternatives considered:**
  - Import síncrono `ReasignacionDespachoService` (rechazado: acoplamiento).

## Decision 8: Cierre multi-despacho O28 con atribución auditoría

- **Decision:** `CerrarCasoService` auto-retira despachos pendientes con `idusuario` = ejecutor del cierre (clarificación B); distinto de O44 (forzado unitario por operador).
- **Rationale:** RN-SEG-012; trazabilidad SLA.
- **Alternatives considered:**
  - `idusuario=Sistema` en auto-retiros (rechazado en clarify).

## Decision 9: O42 cancelación — formulario mínimo

- **Decision:** Solo `motivo` + `horafin`/`duracionminutos`; sin RF-SEG-004 ni `Dim_EvidenciaFoto`.
- **Rationale:** Clarificación A Session 2026-07-09.
- **Alternatives considered:**
  - Mismo formulario O28 (rechazado).

## Decision 10: Filtro expedientes Cliente por condado

- **Decision:** `ExpedienteClienteService` resuelve `idcalle` → `Dim_Condado` y cruza con `Dim_Preferencias_Cliente.zonas_geograficas`.
- **Rationale:** Clarificación A; reutiliza `GeografiaRepository`.
- **Alternatives considered:**
  - Polígonos GeoJSON (rechazado en clarify).

## Decision 11: Jobs programados O37 y depuración GPS

- **Decision:**
  - **O37:** job cada 30s (`gps_senal_perdida_job`) — umbral configurable default 60s.
  - **Depuración:** job diario (`gps_depuracion_job`) — 90 días post-cierre, conserva 3 puntos por `iddespacho` (RNF-SEG-004).
- **Rationale:** RNF-SEG-004/005; operación desacoplada de HTTP.
- **Alternatives considered:**
  - Depuración manual (rechazado: riesgo operativo).

## Decision 12: Angular — módulo `seguimiento/` (skills `angular-architect`, `typescript-expert`)

- **Decision:** `SeguimientoApiService`, `MiSeguimientoApiService`, `SeguimientoSseService`, `ExpedienteClienteApiService`; tipos en `models/seguimiento.types.ts`; guards `OperadorSeguimientoGuard`, `UnidadSeguimientoGuard`, `ClienteExpedienteGuard`.
- **Rationale:** Patrón `despacho/`; componentes sin lógica de dominio.
- **Alternatives considered:**
  - Extender `DespachoApiService` (rechazado: responsabilidades mezcladas).

## Decision 13: PDF expediente

- **Decision:** `GET .../expediente/pdf` genera PDF server-side (WeasyPrint o reportlab) desde plantilla; datos agregados por `ExpedienteService`.
- **Rationale:** RF-SEG-006; detalle formato diferido a implementación pero endpoint fijado en contrato.
- **Alternatives considered:**
  - PDF solo cliente-side (rechazado: datos sensibles y consistencia).

## Tie-Breaker (constitution)

- **Conflicto:** Performance Efficiency (GPS cada 10s, latencia 5s RNF-SEG-001) vs Maintainability (app + jobs + SSE separados).
- **Prioridad:** Maintainability — app `seguimiento` dedicada; performance con ingestión Kafka asíncrona y SSE push; ETA calculado en servicio con Haversine reutilizado de despacho.
- **Safety:** geofencing con histéresis 30s prioriza evitar falsas llegadas sobre velocidad de transición.
