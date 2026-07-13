# Implementation Plan: Despacho Inteligente y Asignación de Unidades

**Branch**: `despacho-inteligente` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Emergencias/despacho-inteligente/spec.md`

**Input**: Feature specification from `specs/003-operational/Emergencias/despacho-inteligente/spec.md` (clarificaciones Session 2026-07-09 integradas).

## Summary

Implementar el módulo de despacho inteligente con enfoque **contract-first**: primero el contrato OpenAPI REST (`contracts/despacho-inteligente.openapi.yaml`) alineado a `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka** y orquestación **event-driven** (O22 consumer, O35 job, O36 worker); finalmente frontend Angular 17+ con servicios tipados y guards. Cubre CU-O22–O24, O33–O36, O38, O45 y RF-DES-001–011.

## Traceability

- **Objetivo operacional:** minimizar tiempo de respuesta ante accidentes (BSC).
- **UC cubiertos:** CU-O22, O23, O24, O33, O34, O35, O36, O38, O45.
- **Dependencias:** `autenticacion-y-rbac`, `registro-accidente` (estado REPORTADO), `field-operations` / `evidencia-unidad` (disponibilidad unidad).
- **Consumidores downstream:** `seguimiento-cierre-de-casos` (despacho confirmado).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, JWT RS256, Kafka producer/consumer, Celery o APScheduler (job O35), RxJS, EventSource (SSE)

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal escritura dominio)

**Testing**: pytest + contract tests OpenAPI; Jasmine/Karma servicios, guards y SSE

**Target Platform**: Linux containerizado (API + workers) + SPA operadores + app móvil unidad

**Project Type**: Web application (backend + frontend)

**Performance Goals**: O22 <5s (CA-DES-001); confirmación P95 <2min (RNF-DES-001); push <5s, SMS <30s (RNF-DES-004)

**Constraints**: API `/api/v1/`, envelope estándar, idempotencia escrituras, Vista→Servicio→Repositorio, Kafka-only-write, SSE para monitoreo

**Scale/Scope**: Camino crítico TSI; N-N despachos; re-asignación ilimitada hasta agotar candidatas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | CU-O22–O45 + CA-DES-001–013 trazables al contrato y data-model |
| Reliability | PASS | Event-driven O35/O36, fail-fast O23, idempotencia, historial append-only |
| Performance Efficiency | PASS | RNF-DES-001/003/004; filtro condado reduce candidatas; métricas en quickstart |
| Interaction Capability | PASS | Monitoreo SSE RF-DES-011; UI operador + notificación unidad |
| Security | PASS | JWT + RBAC por rol; unidad solo `/mi-despacho` propio |
| Compatibility | PASS | Contract-first OpenAPI; integración Kafka con registro-accidente |
| Maintainability | PASS | Vista→Servicio→Repositorio; servicios por CU; extiende `apps/despacho/` |
| Flexibility | PASS | Parámetros RF-DES-010 configurables; escalamiento condado vecino |
| Safety | PASS | Re-asignación inmediata ante fallo entrega; timeout configurable |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** documentado en `research.md` (Maintainability vs Performance).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Emergencias/despacho-inteligente/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── despacho-inteligente.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── despacho/
│       ├── views/
│       │   ├── asignacion_views.py       # O33, O34, O38
│       │   ├── monitoreo_views.py        # RF-DES-011 + SSE stream
│       │   ├── mi_despacho_views.py      # O24, O45
│       │   ├── parametros_views.py       # RF-DES-010
│       │   ├── disponibilidad_views.py   # (existente CU-O30)
│       │   └── urls.py
│       ├── services/
│       │   ├── asignacion_inteligente_service.py   # O22 algoritmo
│       │   ├── asignacion_manual_service.py        # O33
│       │   ├── escalamiento_zona_service.py        # O34
│       │   ├── coordinacion_multiple_service.py    # O38
│       │   ├── notificacion_despacho_service.py    # O23
│       │   ├── confirmar_despacho_service.py       # O24
│       │   ├── rechazar_despacho_service.py        # O45
│       │   ├── reasignacion_despacho_service.py    # O36
│       │   ├── timeout_despacho_service.py         # O35
│       │   ├── monitoreo_despacho_service.py       # RF-DES-011
│       │   ├── parametros_despacho_service.py      # RF-DES-010
│       │   ├── concordancia_tipo_service.py
│       │   └── consulta_candidatas_service.py
│       ├── consumers/
│       │   ├── accidente_reportado_consumer.py     # dispara O22
│       │   └── despacho_timeout_consumer.py        # dispara O36 async
│       ├── jobs/
│       │   └── timeout_despacho_job.py             # O35
│       ├── permissions.py                          # + OperadorDespacho, etc.
│       └── tests/
│           ├── api/                                # Contract tests OpenAPI
│           ├── services/
│           ├── consumers/
│           └── repositories/
└── core/
    └── repositories/
        └── despacho/
            ├── despacho_repository.py
            ├── notificacion_despacho_repository.py
            ├── historial_despacho_repository.py
            ├── historial_estado_unidad_repository.py  # (existente)
            ├── unidad_emergencia_repository.py        # (existente)
            ├── ubicacion_unidad_repository.py
            ├── geografia_repository.py                # condado/vecinos
            ├── estado_accidente_repository.py         # lectura/escritura transiciones
            └── parametros_despacho_repository.py

frontend/
└── src/app/
    ├── modules/despacho/
    │   ├── pages/
    │   │   ├── monitoreo-despacho/
    │   │   ├── asignacion-manual/
    │   │   ├── parametros-algoritmo/
    │   │   └── mi-despacho/              # app unidad
    │   ├── services/
    │   │   ├── despacho-api.service.ts
    │   │   ├── mi-despacho-api.service.ts
    │   │   ├── despacho-parametros-api.service.ts
    │   │   ├── despacho-sse.service.ts
    │   │   └── models/despacho.types.ts
    │   ├── guards/
    │   │   ├── operador-despacho.guard.ts
    │   │   ├── unidad-despacho.guard.ts
    │   │   └── director-tecnologico.guard.ts
    │   └── despacho.routes.ts
    └── core/
        └── interceptors/                 # JWT (reutilizar auth)
```

**Structure Decision:** Extender `apps/despacho/` y crear módulo Angular `despacho/` según `project-structure.md`. Repositorios compartidos en `core/repositories/despacho/`.

## Phase 0: Research (completado)

Ver `research.md` — resueltos: contract-first, capas Django, Kafka-only-write, eventos O35/O36, JWT/RBAC, algoritmo condado+Haversine, fail-fast notificaciones, SSE, Angular guards, keywords severidad moderada.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/despacho-inteligente.openapi.yaml`

| Rol | Endpoints |
|-----|-----------|
| Operador de emergencias / Despacho | Monitoreo, SSE, candidatas, asignar-manual, escalar-zona, coordinar |
| Unidad de emergencia | Listar pendientes, confirmar, rechazar |
| Administrador / Director Tecnológico | GET/PATCH parámetros algoritmo |

**Flujos sin endpoint HTTP (orquestación interna):**

| CU | Mecanismo |
|----|-----------|
| O22 | Consumer `AccidenteReportado` |
| O23 | `NotificacionDespachoService` (post-asignación) |
| O35 | Job programado 30s |
| O36 (timeout) | Consumer `DespachoTimeout_topic` |
| O36 (rechazo/fallo O23) | Llamada síncrona a `ReasignacionDespachoService` |

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|-------------|----------|------------------------|
| `MonitoreoDespachoView` | `MonitoreoDespachoService` | `DespachoRepository`, `HistorialDespachoRepository` |
| `DespachoSseView` | `MonitoreoDespachoService` | Pinot read + pub/sub interno |
| `ListarCandidatasView` | `ConsultaCandidatasService` | `UnidadEmergenciaRepository`, `GeografiaRepository`, `UbicacionUnidadRepository` |
| `AsignarManualView` | `AsignacionManualService` | `DespachoRepository`, `NotificacionDespachoRepository`, Kafka |
| `EscalarZonaView` | `EscalamientoZonaService` | `GeografiaRepository`, repos despacho |
| `CoordinarDespachoView` | `CoordinacionMultipleService` | repos despacho |
| `ListarPendientesView` | `MiDespachoService` | `NotificacionDespachoRepository` |
| `ConfirmarDespachoView` | `ConfirmarDespachoService` | repos despacho + estado unidad/caso |
| `RechazarDespachoView` | `RechazarDespachoService` + `ReasignacionDespachoService` | repos despacho |
| `ParametrosDespachoView` | `ParametrosDespachoService` | `ParametrosDespachoRepository` |
| `AccidenteReportadoConsumer` | `AsignacionInteligenteService` + `NotificacionDespachoService` | todos repos O22 |
| `TimeoutDespachoJob` | `TimeoutDespachoService` | `DespachoRepository`, Kafka `DespachoTimeout_topic` |
| `DespachoTimeoutConsumer` | `ReasignacionDespachoService` | repos O36 |

**Flujo escritura Kafka (ejemplo asignación automática O22):**

```text
AccidenteReportado event
  → AsignacionInteligenteService.ejecutar()
      → GeografiaRepository.filtrar_por_condado()
      → UbicacionUnidadRepository.posicion_efectiva()
      → scoring + selección
      → NotificacionDespachoRepository.publish_create()  → Fact_NotificacionDespacho_topic
      → DespachoRepository.publish_create()              → Fact_Despacho_topic
      → HistorialDespachoRepository.publish()              → Fact_HistorialDespachoUnidad_topic
      → EstadoAccidenteRepository.publish()                → Fact_AccidenteTipoEstadoAccidente_topic
  → NotificacionDespachoService.notificar()  → apps/notificaciones (push/SMS)
      → éxito: UPDATE Notificada vía Kafka
      → fallo ambos canales: No_entregada + ReasignacionDespachoService (síncrono)
```

### Frontend — servicios y guards (prioridad 2, post-contrato)

| Artefacto | Contrato consumido |
|-----------|-------------------|
| `DespachoApiService` | `/accidentes/{id}/despacho/*`, `/despacho/parametros` |
| `MiDespachoApiService` | `/mi-despacho/*` |
| `DespachoSseService` | `GET .../despacho/stream` |
| `DespachoParametrosApiService` | RF-DES-010 |
| `OperadorDespachoGuard` | Monitoreo, manual, escalamiento, coordinación |
| `UnidadDespachoGuard` | Confirmar/rechazar pendientes |
| `DirectorTecnologicoGuard` | Parámetros algoritmo |

## Phase 2: Tasks (siguiente comando)

Ejecutar `/speckit-tasks` para generar `tasks.md` ordenado por dependencias: contrato → repos → servicios → consumers/jobs → views → contract tests → Angular.

## Complexity Tracking

Sin violaciones de constitution que requieran excepción documentada.
