# Implementation Plan: Pipeline Comercial y Prospectos

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../commercial-pipeline-prospects.md`](../commercial-pipeline-prospects.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — stub Fase A; no duplicar OpenAPI/data-model en FE.


**Branch**: `commercial-pipeline-prospects` | **Date**: 2026-07-25 (rev. 2026-07-26 RF-CPP-000) | **Spec**: `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/spec.md`

**Input**: Feature specification from `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/spec.md` (clarificaciones Session 2026-07-25 + Session 2026-07-26 portal público de planes / RF-CPP-000).

**Skills / constraints del usuario**: `django-expert` + `api-authentication` (backend JWT/RBAC); contract-first REST según `api-standards.md`; luego `angular-architect` + `typescript-expert` (servicios/guards tipados); `architectural-patterns.md`: Vista→Servicio→Repositorio; Kafka único canal de escritura (lecturas Pinot permiten entidades ajenas en solo lectura).

## Summary

**Autoridad UI:** Interaction Capability en [`../frontend/plan.md`](../frontend/plan.md) / [`../frontend/tasks.md`](../frontend/tasks.md). Este plan BE no es superficie de trabajo UI.


Implementar el embudo comercial de prospectos (**RF-CPP-000** portal público de planes + **O116, O117, O119, O121** + entrada directa + consulta) con enfoque **contract-first**: OpenAPI en `contracts/commercial-pipeline-prospects.openapi.yaml`; app Django `apps/ventas_crm/` en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka** (`Dim_Prospecto_topic`, `Fact_Asignacion_topic`, `Fact_Pipeline_topic`, `Dim_Cliente_topic`) y **lectura Pinot** de `Dim_Plan` (propiedad Suscripciones-Facturación, sin escritura); módulo Angular `ventas-crm` con página pública de planes + registro, y área autenticada con guards (`GerenteVentas`, `GerenteCuentasPublicas`, `Administrador`).

**Delta 2026-07-26:** el portal de planes deja de estar en §15 Fuera de alcance y pasa a **RF-CPP-000** (precondición informativa del embudo, Visitante sin JWT). El embudo O116–O121 + RF-CPP-007/008 ya está implementado; este plan incorpora el diseño del delta pendiente.

## Traceability

- **Objetivo operacional:** adquisición comercial (consulta de planes → embudo pre-venta → cuenta cliente) — `module-map.md` #4.
- **UC cubiertos:** O116, O117, O119, O121 (+ RF-CPP-007/008 sin CU dedicado). **RF-CPP-000** alias documental CU-O123 — **ID canónico a definir** en `module-map.md` (mismo trato que otros alias de fuente).
- **Dependencias:** `#01 autenticacion-y-rbac` (JWT RS256, roles, sesión — no aplica a RF-CPP-000 ni registro público). **Lectura** de `Dim_Plan` desde Suscripciones-Facturación (`subscriptions-and-billing` #06) — este módulo **no escribe** en `Dim_Plan` / `Dim_Plan_topic`. Continuación onboarding en Cuentas-Clientes tras `estado_onboarding='Pendiente'`.
- **Consumidores downstream:** `notificacion-ventas` (#05) lee `Dim_Prospecto.idusuario`.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, SimpleJWT/RS256 (proyecto), Kafka producer, RxJS, standalone Angular

**Storage**: Apache Pinot (lectura vía `core/repositories/`), Kafka (único canal de escritura de dominio). RF-CPP-000: **solo Pinot read** sobre `Dim_Plan`.

**Testing**: pytest (markers `api`/`service`/`repository`/`unit`) + contract tests OpenAPI; Jasmine/Karma según stack frontend del repo

**Target Platform**: Linux containerizado (API) + SPA Angular

**Project Type**: Web application (backend + frontend)

**Performance Goals**: Endpoint completo ≤500ms P95 (CA-CPP-009 / RNF-CPP-003); Pinot simple ≤100ms P95; Kafka publish ≤50ms; `GET /planes` tratado como consulta Pinot simple

**Constraints**: `/api/v1/ventas-crm/`; envelope estándar; Idempotency-Key obligatorio en conversión; rate limit registro 10/min/IP; dueño estricto; optimistic concurrency (RN-CPP-011); sin saltos/retrocesos de etapa; Kafka-only-write para entidades de este módulo; **RF-CPP-000 sin JWT y sin Kafka publish**

**Scale/Scope**: Módulo comercial no crítico de despacho; volumen típico B2B; app `ventas_crm` + módulo Angular `ventas-crm` **ya existen** (embudo implementado); delta = catálogo público + página Visitante

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | RF-CPP-000 + O116/O117/O119/O121 + RF-CPP-001–008 y CA-CPP-000…012 trazables a contrato y data-model |
| Reliability | PASS | `Fact_Asignacion`/`Fact_Pipeline` insert-only; RN-CPP-011; portal planes sin escrituras (cero riesgo de corrupción de `Dim_Plan`) |
| Performance Efficiency | PASS | Umbrales RNF-CPP-003 / testing.md; `GET /planes` = lectura Pinot filtrada `activo=true` |
| Interaction Capability | PASS | Portal/listados con loading/vacío/error (RNF-CPP-005); catálogo vacío = vacío accionable hacia registro |
| Security | PASS | JWT Bearer + RBAC en mutaciones; **GET /planes** y registro públicos; planes desactivados no se filtran al Visitante |
| Compatibility | PASS | Contract-first OpenAPI `/api/v1/`; co-escritura `Dim_Cliente`; lectura `Dim_Plan` sin usurpar ownership de Suscripciones |
| Maintainability | PASS | Vista→Servicio→Repositorio; un servicio por caso de uso; mapa `nivel→severidades` en servicio (Decision 10) |
| Flexibility | Not applicable | Spec RNF-CPP-008 |
| Safety | Not applicable | Spec RNF-CPP-009 |

**Post-Design Gate:** PASS — sin violaciones. RF-CPP-000 no introduce escritura cruzada de módulo.

**Tie-Breaker:** Maintainability + Functional Suitability para el mapa de severidades en código de servicio (sin schema nuevo ni duplicar administración de planes).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
├── contracts/
│   └── commercial-pipeline-prospects.openapi.yaml
└── tasks.md                    # ampliar con /speckit-converge o /speckit-tasks (delta RF-CPP-000)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── ventas_crm/
│       ├── views/
│       │   ├── plan_views.py                # NUEVO — GET /planes (AllowAny)
│       │   ├── prospecto_views.py
│       │   ├── asignacion_views.py
│       │   ├── pipeline_views.py
│       │   ├── conversion_views.py
│       │   └── entrada_directa_views.py
│       ├── urls.py                          # + path planes
│       ├── permissions.py
│       ├── throttles.py
│       ├── services/
│       │   ├── consulta_planes_publicos_service.py  # NUEVO — RF-CPP-000
│       │   ├── registro_prospecto_service.py
│       │   ├── asignacion_automatica_service.py
│       │   ├── asignacion_manual_service.py
│       │   ├── pipeline_service.py
│       │   ├── conversion_cliente_service.py
│       │   ├── entrada_directa_service.py
│       │   └── consulta_prospecto_service.py
│       └── tests/
│           ├── api/          # + test_planes_publicos_contract.py
│           ├── services/     # + test_consulta_planes_publicos_service.py
│           ├── repositories/ # + test plan read (si repo propio)
│           └── e2e/
├── core/
│   └── repositories/
│       ├── ventas_crm/
│       │   ├── prospecto_repository.py
│       │   ├── asignacion_repository.py
│       │   ├── pipeline_repository.py
│       │   └── plan_lectura_repository.py   # NUEVO — Pinot read-only Dim_Plan (o reutilizar repo Suscripciones si existe)
│       └── cuentas_clientes/
│           └── cliente_repository.py
└── config/urls.py

frontend/
└── src/app/modules/ventas-crm/
    ├── ventas-crm.routes.ts                 # + ruta pública /planes (o /ventas-crm/planes)
    ├── guards/                              # no aplican a portal
    ├── services/
    │   ├── planes-api.service.ts            # NUEVO
    │   ├── prospecto-api.service.ts
    │   ├── pipeline-api.service.ts
    │   └── conversion-api.service.ts
    ├── models/                              # + PlanPublico DTO
    └── pages/
        ├── catalogo-planes/                 # NUEVO — Visitante
        ├── registro-publico/
        ├── listado-prospectos/
        ├── detalle-prospecto/
        ├── pipeline-board/
        └── entrada-directa/
```

**Structure Decision**: Misma app `ventas_crm`. **No** crear app de facturación aquí. Lectura de `Dim_Plan` vía repositorio de solo lectura (preferir reutilizar un `PlanRepository` de Suscripciones si ya existe en el repo; si no, `plan_lectura_repository` bajo `ventas_crm` **sin** método publish/Kafka). Administración de planes permanece en Suscripciones-Facturación.

## Phase 0: Research

Ver `research.md` — Decisiones 1–9 (embudo) + **Decision 10** (portal público / mapa severidades / ownership de lectura).

## Phase 1: Design & Contracts

| Artefacto | Contenido |
|-----------|-----------|
| `contracts/commercial-pipeline-prospects.openapi.yaml` | **8** paths REST: + `GET /ventas-crm/planes` público; embudo previo intacto |
| `data-model.md` | + `Dim_Plan` lectura referencial; mapa nivel→severidades; sin topic write |
| `quickstart.md` | Paso 0 = catálogo público; luego registro → … |

### Mapa Vista → Servicio → Repositorio

| Endpoint | Vista | Servicio | Repositorio / Kafka |
|----------|-------|----------|---------------------|
| `GET /planes` | plan_views | consulta_planes_publicos_service | Pinot **read** `Dim_Plan` (`activo=true`) — **sin Kafka** |
| `POST /prospectos` | prospecto_views | registro_prospecto_service → asignacion_automatica_service | Dim_Prospecto + Fact_Asignacion topics |
| `GET /prospectos` | prospecto_views | consulta_prospecto_service | Pinot read Dim_Prospecto |
| `GET /prospectos/{id}` | prospecto_views | consulta_prospecto_service | Pinot + historiales |
| `PATCH .../asignacion` | asignacion_views | asignacion_manual_service | Fact_Asignacion + Dim_Prospecto |
| `POST .../pipeline` | pipeline_views | pipeline_service | Fact_Pipeline + Dim_Prospecto |
| `POST .../conversion` | conversion_views | conversion_cliente_service | Fact_Pipeline + `ClienteRepository` + Dim_Prospecto |
| `POST .../entrada-directa` | entrada_directa_views | entrada_directa_service | `ClienteRepository` (`cuentas_clientes`) |

### Auth (api-authentication)

- Público: `GET /planes` (RF-CPP-000) + `POST /prospectos` (throttle IP solo en registro).
- Bearer JWT RS256; roles claim `roles[]` ∈ `Administrador` \| `GerenteVentas` \| `GerenteCuentasPublicas`.
- RF-CPP-002: interno (Sistema); no endpoint público.

### Frontend (angular-architect + typescript-expert)

- Ruta **pública** de catálogo de planes (sin guard JWT) con CTA hacia registro público.
- Lazy module autenticado `ventas-crm` para gerentes/admin (sin cambios de RBAC del embudo).
- Estados loading / empty / error en portal (RNF-CPP-005).

## Phase 2: Tasks

Ver `tasks.md`. T001–T069 = embudo previo (completado). **Siguiente:** `/speckit-converge` o `/speckit-tasks` para añadir US/tasks del delta RF-CPP-000 (tests → service → view → Angular → quickstart).

## Complexity Tracking

> Sin violaciones constitucionales que requieran excepción. Tabla vacía a propósito.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
