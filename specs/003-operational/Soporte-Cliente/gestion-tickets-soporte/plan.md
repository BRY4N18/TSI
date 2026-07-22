# Implementation Plan: Gestión de Tickets de Soporte e Incidencias

**Branch**: `gestion-tickets-soporte` | **Date**: 2026-07-21 | **Spec**: `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/spec.md`

**Input**: Feature specification from `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/spec.md` (clarificaciones Session 2026-07-21 integradas).

## Summary

Implementar el módulo de gestión de tickets de soporte con enfoque **contract-first**: primero el contrato OpenAPI REST (`contracts/gestion-tickets-soporte.openapi.yaml`) alineado a `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka**; finalmente frontend Angular 17+ con servicios tipados y guards. Cubre CU-O91, O92, O95, O96, O97 y RF-TIC-001–007.

## Traceability

- **Objetivo operacional:** canalizar y resolver incidencias de clientes dentro de los SLA contractuales (BSC — retención y satisfacción de clientes).
- **UC cubiertos:** CU-O91, O92, O95, O96, O97.
- **Dependencias:** `autenticacion-y-rbac` (roles), `incorporacion-clientes` (cliente con cuenta activa), `billing-and-auto-renewal` (`Fact_Suscripcion`/`idplan`).
- **Consumidores downstream:** ninguno declarado en el spec (módulo terminal del módulo Soporte-Cliente).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, JWT RS256, Kafka producer/consumer, Celery/APScheduler (job CU-O96), RxJS

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal escritura dominio)

**Testing**: pytest + contract tests OpenAPI; Jasmine/Karma servicios y guards

**Target Platform**: Linux containerizado (API + job) + SPA (cliente, agente, administrador)

**Project Type**: Web application (backend + frontend)

**Performance Goals**: Registro de ticket <3s (RNF-TIC-003); job de monitoreo SLA cada 1 min (RNF-TIC-001, clarificación)

**Constraints**: API `/api/v1/`, envelope estándar, idempotencia en escrituras, Vista→Servicio→Repositorio, Kafka-only-write, notas internas nunca expuestas al Cliente (RN-TIC-002)

**Scale/Scope**: Camino no crítico (no forma parte del camino crítico de despacho); volumen de tickets proporcional a clientes activos, sin límite de reintentos de reasignación como en despacho

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | CU-O91–O97 + CA-TIC-001–013 trazables al contrato y data-model |
| Reliability | PASS | Historial append-only (RNF-TIC-002), job idempotente, SLA independiente del estado del ticket (RN-TIC-001) |
| Performance Efficiency | PASS | RNF-TIC-001 (job 1 min), RNF-TIC-003 (registro <3s) declarados como criterios medibles |
| Interaction Capability | PASS | Dashboard RF-TIC-007; UI cliente/agente/admin diferenciada por rol |
| Security | PASS | JWT + RBAC por rol; notas internas filtradas server-side (RN-TIC-002, no solo frontend) |
| Compatibility | PASS | Contract-first OpenAPI; SLA depende de `idplan` de `billing-and-auto-renewal` vía integración de datos, no API directa |
| Maintainability | PASS | Vista→Servicio→Repositorio; servicios por CU; app nueva `apps/soporte_cliente/` sin `queries.py` (CRUD simple) |
| Flexibility | PASS | `Dim_SLAConfig` versionado temporal permite nuevos planes/prioridades sin migración de tickets existentes |
| Safety | Not applicable | Este módulo no participa en el camino crítico de despacho ni en decisiones que afecten la seguridad física de personas en un accidente (Additional Constraints de la constitution) |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** documentado en `research.md` (Functional Suitability vs Maintainability en la regla de clasificación automática — Safety no aplica, ver Decision 4 y cierre de `research.md`).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── traceability.md
├── contracts/
│   └── gestion-tickets-soporte.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── soporte_cliente/
│       ├── views.py                          # Rutas REST (tickets, sla-config, dashboard)
│       ├── urls.py
│       ├── permissions.py                    # IsCliente, IsSoporteAgente, IsAdministradorSLA, IsSupervisorSoporte, etc.
│       ├── services/
│       │   ├── registrar_ticket_service.py         # O91
│       │   ├── clasificacion_automatica_service.py # O91 paso 2 (Decision 4)
│       │   ├── asignacion_sla_service.py            # O91 paso 4 + O97 renovación (Decision 5, 8)
│       │   ├── tomar_ticket_service.py              # O92
│       │   ├── comentar_ticket_service.py           # O92
│       │   ├── escalar_ticket_service.py            # O92 (manual)
│       │   ├── resolver_ticket_service.py           # O92
│       │   ├── confirmar_cierre_service.py          # O92 / RF-TIC-006
│       │   ├── configurar_sla_service.py            # O95
│       │   ├── monitoreo_sla_service.py             # O96 (job)
│       │   ├── reabrir_ticket_service.py            # O97
│       │   └── dashboard_soporte_service.py         # RF-TIC-007
│       ├── jobs/
│       │   └── monitoreo_sla_job.py                 # O96, cada 1 min
│       └── tests/
│           ├── api/
│           ├── services/
│           ├── jobs/
│           └── repositories/
└── core/
    └── repositories/
        └── soporte/
            ├── reclamo_repository.py
            ├── historial_ticket_repository.py
            ├── sla_config_repository.py
            ├── archivo_adjunto_reclamo_repository.py
            └── supervisor_soporte_repository.py      # Decision 6

frontend/
└── src/app/
    ├── modules/soporte-cliente/
    │   ├── pages/
    │   │   ├── mis-tickets/              # Cliente
    │   │   ├── cola-agente/              # Soporte al cliente
    │   │   ├── detalle-ticket/           # Todos los roles (vista filtrada)
    │   │   ├── configuracion-sla/        # Administrador
    │   │   └── dashboard-soporte/        # RF-TIC-007
    │   ├── services/
    │   │   ├── ticket-api.service.ts
    │   │   ├── sla-config-api.service.ts
    │   │   └── models/soporte.types.ts
    │   ├── guards/
    │   │   ├── cliente-soporte.guard.ts
    │   │   ├── agente-soporte.guard.ts
    │   │   └── administrador-sla.guard.ts
    │   └── soporte-cliente.routes.ts
    └── core/
        └── interceptors/                 # JWT (reutilizar auth)
```

**Structure Decision:** Nueva app `apps/soporte_cliente/` y módulo Angular `soporte-cliente/`, ya reservados en `project-structure.md`/`module-map.md`. App CRUD sin `queries.py` (sin lecturas complejas tipo Haversine). Repositorios en `core/repositories/soporte/`.

## Phase 0: Research (completado)

Ver `research.md` — resueltas: contract-first, capas Django, Kafka-only-write, clasificación automática por keywords, resolución de `idplan` vía `Fact_Suscripcion`, rol fijo Supervisor de Soporte, frecuencia de job (clarificación), renovación de SLA al reabrir (clarificación), JWT/RBAC, Angular guards.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/gestion-tickets-soporte.openapi.yaml`

| Rol | Endpoints |
|-----|-----------|
| Cliente | Registrar ticket, ver detalle propio, comentar, confirmar cierre, reabrir |
| Soporte al cliente (agente) | Listar/tomar/comentar (incl. notas internas)/escalar/resolver |
| Desarrollador de APIs / Director Tecnológico | Recibir tickets escalados a su nivel, comentar, resolver |
| Administrador | GET/POST/PATCH configuración SLA, dashboard completo |

**Flujo sin endpoint HTTP (orquestación interna):**

| CU | Mecanismo |
|----|-----------|
| O96 | Job programado cada 1 minuto (`monitoreo_sla_job.py`) |

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|-------------|----------|------------------------|
| `TicketsListView` / `DashboardView` | `DashboardSoporteService` | `ReclamoRepository`, `HistorialTicketRepository` |
| `RegistrarTicketView` | `RegistrarTicketService` + `ClasificacionAutomaticaService` + `AsignacionSLAService` | `ReclamoRepository`, `HistorialTicketRepository`, `ArchivoAdjuntoReclamoRepository`, `SLAConfigRepository`, lectura `Fact_Suscripcion`/`Fact_AccidenteTipoEstadoAccidente` |
| `ClasificarTicketManualView` | `AsignacionSLAService` | `ReclamoRepository`, `SLAConfigRepository` |
| `TomarTicketView` | `TomarTicketService` | `ReclamoRepository`, `HistorialTicketRepository` |
| `ComentarTicketView` | `ComentarTicketService` | `HistorialTicketRepository` |
| `EscalarTicketView` | `EscalarTicketService` | `ReclamoRepository`, `HistorialTicketRepository` |
| `ResolverTicketView` | `ResolverTicketService` | `ReclamoRepository`, `HistorialTicketRepository` |
| `ConfirmarCierreView` | `ConfirmarCierreService` | `ReclamoRepository`, `HistorialTicketRepository` |
| `ReabrirTicketView` | `ReabrirTicketService` + `AsignacionSLAService` | `ReclamoRepository`, `HistorialTicketRepository`, `ArchivoAdjuntoReclamoRepository`, `SLAConfigRepository` |
| `SLAConfigView` | `ConfigurarSLAService` | `SLAConfigRepository` |
| `MonitoreoSLAJob` | `MonitoreoSLAService` | `ReclamoRepository`, `HistorialTicketRepository`, `SupervisorSoporteRepository` |

**Flujo escritura Kafka (ejemplo registro de ticket, O91):**

```text
POST /soporte/tickets
  → RegistrarTicketService.ejecutar()
      → ClasificacionAutomaticaService.clasificar()  (Decision 4)
      → AsignacionSLAService.asignar() (si clasificable)  (Decision 5)
      → ReclamoRepository.publish_create()        → Fact_Reclamo_topic
      → ArchivoAdjuntoReclamoRepository.publish()  → Fact_ArchivosAdjuntosReclamos_topic (si hay adjuntos)
      → HistorialTicketRepository.publish()        → Fact_Historial_Ticket_topic (tipo_accion=creacion)
```

### Frontend — servicios y guards (prioridad 2, post-contrato)

| Artefacto | Contrato consumido |
|-----------|-------------------|
| `TicketApiService` | `/soporte/tickets/*` |
| `SlaConfigApiService` | `/soporte/sla-config*` |
| `ClienteSoporteGuard` | Mis tickets, reabrir |
| `AgenteSoporteGuard` | Cola de agente, tomar/comentar/escalar/resolver |
| `AdministradorSlaGuard` | Configuración SLA |

## Phase 2: Tasks (siguiente comando)

Ejecutar `/speckit-tasks` para generar `tasks.md` ordenado por dependencias: contrato → repos → servicios → job → views → contract tests → Angular.

## Complexity Tracking

Sin violaciones de constitution que requieran excepción documentada.
