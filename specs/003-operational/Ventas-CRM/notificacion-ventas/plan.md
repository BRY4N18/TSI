# Implementation Plan: Notificación de Prospectos a Ventas

**Branch**: `notificacion-ventas` | **Date**: 2026-07-25 | **Spec**: `specs/003-operational/Ventas-CRM/notificacion-ventas/spec.md`

**Input**: Feature specification from `specs/003-operational/Ventas-CRM/notificacion-ventas/spec.md` (clarificaciones Session 2026-07-25 integradas).

**Skills / constraints del usuario**: `django-expert` + `api-authentication` (backend JWT/RBAC + demo session auth); contract-first REST según `api-standards.md`; luego `angular-architect` + `typescript-expert` (servicios/guards tipados); `architectural-patterns.md`: Vista→Servicio→Repositorio; Kafka único canal de escritura.

## Summary

Implementar demo interactiva + alerta a ventas (**O118, O122** + consulta RF-NV-004) con enfoque **contract-first**: primero OpenAPI en `contracts/notificacion-ventas.openapi.yaml`; luego **extender** la app Django existente `apps/ventas_crm/` en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka** (`Fact_Interaccion_Demo_topic`, `Fact_NotificacionVentas_topic`, update parcial `Dim_Prospecto_topic`); job Celery ≤60s para evaluación/re-evaluación de reglas; despacho email/push vía `core/notificaciones`; finalmente Angular `ventas-crm` con flujo demo (token de sesión) y listado de notificaciones (guards de rol).

## Traceability

- **Objetivo operacional:** señalización comercial (demo → aviso al ejecutivo) — `module-map.md` #5.
- **UC cubiertos:** O118, O122 (+ RF-NV-003/004 derivados).
- **Dependencias:** `#04 commercial-pipeline-prospects` (`idusuario`, emisión `demo_grant` en registro); `#01 autenticacion-y-rbac` (JWT RS256, roles).
- **Downstream:** ninguno bloqueante; consume identidad de gerentes desde Cuentas-Clientes.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, SimpleJWT/RS256 (usuarios) + HS256 demo session, Celery beat, Kafka producer, `core/notificaciones`, RxJS, standalone Angular

**Storage**: Apache Pinot (lectura vía `core/repositories/`), Kafka (único canal de escritura de dominio); grant = HMAC (sin tabla Pinot nueva)

**Testing**: pytest (markers `api`/`service`/`repository`) + contract tests OpenAPI; Jasmine/Karma o Vitest según stack frontend del repo

**Target Platform**: Linux containerizado (API + worker) + SPA Angular

**Project Type**: Web application (backend + frontend)

**Performance Goals**: Notificación INSERT ≤ 2 min tras cumplimiento (RNF-NV-002); job ≤ 60 s; endpoints demo/consulta dentro de umbrales `testing.md` (completo ≤500ms P95 donde aplique)

**Constraints**: `/api/v1/ventas-crm/`; envelope estándar; rate limit interacciones 60/min/token; grant+resume; agregación por sesión histórica; dedup día UTC; Kafka-only-write; Slack enum-only sin envío MVP

**Scale/Scope**: Módulo comercial no crítico de despacho; telemetría de demos B2B; extensión de `ventas_crm` + páginas Angular demo/notificaciones

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | O118/O122 + RF-NV-001–004 y CA-NV-001–009 trazables a contrato y data-model |
| Reliability | PASS | Re-evaluación sesiones históricas 7 días; dedup día UTC; sin pérdida silenciosa (RNF-NV-003) |
| Performance Efficiency | PASS | SLA ≤2 min + job 60s (RNF-NV-002); fuera del camino crítico de despacho |
| Interaction Capability | PASS | Listado notificaciones skeleton/vacío/error (RNF-NV-005) |
| Security | PASS | Grant HMAC + demo session tipado; JWT RBAC en consulta; throttles IP/token (RNF-NV-004) |
| Compatibility | PASS | Contract-first OpenAPI `/api/v1/`; handoff aditivo `demo_grant` en #04 |
| Maintainability | PASS | Vista→Servicio→Repositorio; un servicio por caso de uso; cobertura por capa |
| Flexibility | Not applicable | Spec RNF-NV-008 |
| Safety | Not applicable | Spec RNF-NV-009 — fuera de accidente→despacho |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** Performance (latencia streaming) vs Maintainability (job periódico) — **Maintainability** gana; SLA ≤2 min aceptado. Documentado en `research.md` Decision 6.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Ventas-CRM/notificacion-ventas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
├── contracts/
│   └── notificacion-ventas.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── ventas_crm/                              # EXTENDER (ya existe por #04)
│       ├── authentication.py                    # NUEVO: DemoSessionAuthentication
│       ├── permissions.py                       # EXTENDER: IsGerenteOrAdminNotificaciones
│       ├── throttles.py                         # EXTENDER: DemoSesionIpThrottle, DemoInteraccionTokenThrottle
│       ├── views/
│       │   ├── demo_views.py                    # NUEVO: sesiones + interacciones
│       │   └── notificacion_views.py            # NUEVO: GET listado
│       ├── urls.py                              # EXTENDER rutas demo/ + notificaciones
│       ├── services/
│       │   ├── demo_sesion_service.py           # O118 abrir/resume + set demo_expiracion
│       │   ├── ingesta_interaccion_demo_service.py
│       │   ├── evaluacion_reglas_demo_service.py  # O122 + RF-NV-003 (invocado por Celery)
│       │   ├── despacho_notificacion_ventas_service.py  # core/notificaciones bridge
│       │   └── consulta_notificacion_ventas_service.py  # RF-NV-004
│       ├── tasks.py                             # NUEVO: celery beat entry
│       └── tests/
│           ├── api/
│           ├── services/
│           └── unit/
├── core/
│   ├── notificaciones/                          # REUTILIZAR EmailNotifier, PushNotifier
│   └── repositories/
│       └── ventas_crm/
│           ├── interaccion_demo_repository.py   # NUEVO
│           ├── notificacion_ventas_repository.py # NUEVO
│           └── prospecto_repository.py          # EXTENDER: update demo_expiracion + lecturas
└── config/                                      # celery beat schedule + DEMO_* secrets

frontend/
└── src/app/modules/ventas-crm/                  # EXTENDER
    ├── ventas-crm.routes.ts
    ├── guards/
    │   └── admin-o-gerente-crm.guard.ts         # REUTILIZAR/EXTENDER
    ├── interceptors/
    │   └── demo-session.interceptor.ts          # NUEVO
    ├── services/
    │   ├── demo-api.service.ts                  # NUEVO
    │   └── notificacion-api.service.ts          # NUEVO
    ├── models/                                  # DTOs tipados desde OpenAPI
    └── pages/
        ├── demo-interactiva/                    # NUEVO (público / grant)
        └── notificaciones-ventas/               # NUEVO (JWT)
```

**Structure Decision**: Misma app `ventas_crm` y módulo Angular `ventas-crm` (`project-structure.md`). Repositorios nuevos bajo `core/repositories/ventas_crm/`. Sin app Django adicional. Grant HMAC evita tabla Pinot nueva (`research.md` Decision 4).

## Phase 0: Research

Ver `research.md` — grant HMAC, demo session auth, Celery 60s, Kafka-only-write, canales email/push, Angular guards/servicios.

## Phase 1: Design & Contracts

| Artefacto | Contenido |
|-----------|-----------|
| `contracts/notificacion-ventas.openapi.yaml` | 3 endpoints REST; demo session security scheme; listado cursor |
| `data-model.md` | Ownership, sesión histórica, catálogo reglas, topics Kafka |
| `quickstart.md` | Validación E2E grant→sesión→interacciones→job→listado |

### Mapa Vista → Servicio → Repositorio

| Endpoint / proceso | Vista / entry | Servicio | Repositorio / Kafka / externo |
|-------------------|---------------|----------|-------------------------------|
| `POST /demo/sesiones` | demo_views | demo_sesion_service | Dim_Prospecto_topic + Fact_Interaccion_Demo_topic (`inicio_sesion`) |
| `POST /demo/interacciones` | demo_views | ingesta_interaccion_demo_service | Fact_Interaccion_Demo_topic |
| Celery beat ≤60s | tasks.py | evaluacion_reglas_demo_service → despacho_notificacion_ventas_service | Pinot read + Fact_NotificacionVentas_topic + Email/PushNotifier |
| `GET /notificaciones` | notificacion_views | consulta_notificacion_ventas_service | Pinot read Fact_NotificacionVentas |

### Auth (api-authentication)

- Público: `POST /demo/sesiones` (grant HMAC) + throttle IP.
- Demo: `DemoSessionAuthentication` (Bearer, `typ=demo_session`) en interacciones.
- Usuario: Bearer JWT RS256; roles `GerenteVentas` \| `GerenteCuentasPublicas` \| `Administrador` en listado.
- Job: proceso interno `Sistema` — sin endpoint público de evaluación.

### Frontend (angular-architect + typescript-expert)

- Lazy routes demo (sin JWT usuario) + notificaciones (guard gerente/admin).
- Servicios tipados alineados al OpenAPI; interceptor de demo session token.
- Listado con loading / empty / error+retry (RNF-NV-005).

### Handoff `#04` (aditivo)

Extender `POST /ventas-crm/prospectos` response con `demo_grant`. Artefactos a tocar:

1. `backend/apps/ventas_crm/services/registro_prospecto_service.py` (+ vista de registro)
2. `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/contracts/commercial-pipeline-prospects.openapi.yaml` (campo aditivo en envelope de éxito)
3. Tests de registro existentes (`test_registro_prospecto_service.py`, `test_registro_prospecto_contract.py`)

Sin breaking change de campos existentes. Ver tasks T021–T022.

## Phase 2: Tasks

Ver `tasks.md` (generado por `/speckit-tasks`).

## Complexity Tracking

> Sin violaciones constitucionales que requieran excepción. Tabla vacía a propósito.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
