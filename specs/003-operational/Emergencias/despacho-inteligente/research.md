# Phase 0 Research — Despacho Inteligente

## Decision 1: Contract-first OpenAPI bajo `/api/v1/despacho` y sub-recursos de accidente

- **Decision:** Definir primero `contracts/despacho-inteligente.openapi.yaml` con endpoints HTTP para CU-O24/O33/O34/O38/O45, RF-DES-010 y RF-DES-011; flujos O22/O23/O35/O36 documentados como consumidores Kafka/jobs (sin endpoint público).
- **Rationale:** Cumple constitution (Compatibility API-First) y orden solicitado: contrato REST → Django → Angular.
- **Alternatives considered:**
  - Exponer O22 como `POST` síncrono (rechazado: spec exige ejecución automática al REPORTADO vía evento).
  - Contrato solo Markdown (rechazado: sin contract tests ni tipos Angular).

## Decision 2: Django capas Vista → Servicio → Repositorio en `apps/despacho/`

- **Decision:** Extender app existente `apps/despacho/` con views thin, servicios por caso de uso (`AsignacionAutomaticaService`, `ReasignacionDespachoService`, etc.) y repositorios en `core/repositories/despacho/`.
- **Rationale:** `architectural-patterns.md` vinculante; `evidencia-unidad` ya usa `apps/despacho/` para disponibilidad.
- **Alternatives considered:**
  - Nueva app `asignacion/` (rechazado: `project-structure.md` consolida despacho en una app).
  - Lógica Haversine en vistas (rechazado: mantenibilidad y tests).

## Decision 3: Escritura exclusiva vía Kafka (sin INSERT directo a Pinot)

- **Decision:** Toda mutación de `Fact_Despacho`, `Fact_NotificacionDespacho`, `Fact_HistorialDespachoUnidad`, `Fact_HistorialEstadoUnidad`, `Fact_AccidenteTipoEstadoAccidente`, `Dim_NotaAccidente` publica al topic `{Tabla}_topic`.
- **Rationale:** Regla vinculante; repositorios existentes (`historial_estado_unidad_repository`) ya publican a Kafka.
- **Alternatives considered:**
  - Escritura directa Pinot para latencia O22 (rechazado: viola arquitectura).

## Decision 4: Event-driven entre pasos del camino crítico

- **Decision:**
  - **O22:** consumer `AccidenteReportado` (desde `Fact_AccidenteTipoEstadoAccidente_topic` estado REPORTADO).
  - **O35:** job Celery/APScheduler cada 30s; publica `DespachoTimeout_topic` (evento dominio, no tabla Pinot).
  - **O36 timeout:** worker consume `DespachoTimeout_topic` (asíncrono, clarificación Session 2026-07-09).
  - **O36 rechazo/fallo O23:** invocación síncrona al mismo `ReasignacionDespachoService`.
- **Rationale:** Alinea clarificaciones spec y desacopla job de timeout de re-asignación.
- **Alternatives considered:**
  - O35 invoca O36 en mismo ciclo (rechazado por usuario en clarify).

## Decision 5: JWT + RBAC (skills `api-authentication` + `django-expert`)

- **Decision:** Bearer JWT RS256 en todos los endpoints; permisos DRF reutilizando/extiendo `apps/despacho/permissions.py`:
  - `Operador de emergencias` / rol `Despacho` → monitoreo, asignación manual, escalamiento, coordinación.
  - `Unidad` → confirmar/rechazar despacho propio (`/mi-despacho/*`).
  - `Administrador` / `Director Tecnológico` → parámetros RF-DES-010.
  - Rol servicio `Despacho` para consumidores internos con API key o JWT máquina (mismo patrón auth-rbac).
- **Rationale:** Dependencia `autenticacion-y-rbac`; validación servidor en cada request.
- **Alternatives considered:**
  - Auth solo en Angular guards (rechazado: seguridad).

## Decision 6: Algoritmo de asignación — filtro condado + Haversine + scoring

- **Decision:** `AsignacionInteligenteService` implementa RF-DES-001 con clarificaciones:
  - Filtro geográfico: mismo `Dim_Condado` vía `idcalle` → jerarquía; O34 amplía condados vecinos (catálogo adyacencia en Pinot `Dim_Condado` o tabla auxiliar).
  - Posición unidad: snapshot `Dim_UnidadEmergencia` salvo historial GPS más reciente (`RN-DES-010`).
  - Scoring ponderado configurable (RF-DES-010).
  - Exclusión unidad que rechazó mismo caso (`RN-DES-006`); fallo entrega no excluye (`RN-DES-011`).
- **Rationale:** Clarificaciones formalizadas en spec; testeable unitariamente.
- **Alternatives considered:**
  - Radio fijo 10 km sin condado (rechazado en clarify).

## Decision 7: Notificaciones O23 — push + SMS con fail-fast a O36

- **Decision:** `NotificacionDespachoService` delega a `apps/notificaciones/` (transversal); un reintento por canal; si ambos fallan → `No_entregada`, `activo=false`, O36 síncrono.
- **Rationale:** Clarificación B Session 2026-07-09; evita 90s muertos en camino crítico.
- **Alternatives considered:**
  - Esperar timeout O35 (rechazado).

## Decision 8: Monitoreo tiempo real — SSE (no WebSocket)

- **Decision:** `GET /api/v1/accidentes/{idaccidente}/despacho/stream` con `Accept: text/event-stream`; eventos `despacho.actualizado`, `intento.fallido`, `unidad.confirmada`.
- **Rationale:** `api-standards.md` e `infrastructure.md` (SSE unidireccional operador).
- **Alternatives considered:**
  - Polling cada 5s (rechazado: mayor carga y latencia UI).

## Decision 9: Severidad Moderada — reglas por palabras clave en descripción

- **Decision:** Para `idseveridad=3` (Moderada), `ConcordanciaTipoService` evalúa keywords en `Fact_Accidente.descripcion` (`herido`, `ambulancia`, `grúa`, `daño material`) con mapping configurable en parámetros RF-DES-010.
- **Rationale:** Resuelve ambigüedad diferida del clarify sin NLP/ML en esta fase.
- **Alternatives considered:**
  - Operador elige tipo manualmente siempre (rechazado: rompe O22 automático).
  - Modelo ML severidad (rechazado: fuera de alcance y complejidad).

## Decision 10: Angular — servicios tipados + guards (skills `angular-architect`, `typescript-expert`)

- **Decision:** Módulo `frontend/src/app/modules/despacho/` con:
  - `DespachoApiService`, `MiDespachoApiService`, `DespachoParametrosApiService`, `DespachoSseService`
  - Tipos en `models/despacho.types.ts` generados/alineados al OpenAPI
  - `OperadorDespachoGuard`, `UnidadDespachoGuard`, `DirectorTecnologicoGuard`
  - Rutas lazy `despacho.routes.ts`; componentes sin lógica de dominio
- **Rationale:** Patrón `accidentes/` y `architectural-patterns.md`.
- **Alternatives considered:**
  - Servicio monolítico `EmergenciasService` (rechazado: acoplamiento).

## Tie-Breaker (constitution)

- **Conflicto:** Performance Efficiency (O22 <5s CA-DES-001) vs Maintainability (múltiples servicios + evento async O36).
- **Prioridad:** Maintainability — servicios separados; performance garantizada con cache lectura Pinot, filtro condado previo y job O35 desacoplado.
- **Safety:** fail-fast en fallo notificación (Decision 7) prioriza tiempo de respuesta sobre reintento prolongado.
