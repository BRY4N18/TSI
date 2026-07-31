# Implementation Plan: Suscripciones y Facturación — Backend

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.  
> **Índice:** [`../subscriptions-and-billing.md`](../subscriptions-and-billing.md).  
> **UI:** [`../frontend/spec.md`](../frontend/spec.md) / [`../frontend/plan.md`](../frontend/plan.md) — consume el listado; no redefine contrato.

**Branch / capa**: `subscriptions-and-billing/backend` | **Date**: 2026-07-30 | **Spec**: [`spec.md`](./spec.md)

**Input**: Enmienda listado catálogo planes (Clarification 2026-07-30 listado) — RF-SUSF-001 listado, RNF-SUSF-005a, RN-SUSF-001a, CA-SUSF-016. Módulo base T001–T090 + actor Director T091–T095 ya entregados.

## Summary

### Delta activo (este plan): listado `Dim_Plan` paginado en origen

1. **OpenAPI** `GET /suscripciones/planes`: `cursor` (idplan), `limit` (default **20**, max **100**), filtros `q` / `activo` / `nivel` (y compat `solo_activos` → `activo=true`), respuesta `data` + `meta.pagination.next_cursor` / `limit`.
2. **`PlanRepository.list`**: **dejar de** hacer `SELECT *` + filtrar/ordenar todo en Python. Aplicar filtros y tope de página en la consulta (o estrategia documentada en `research.md` Decision 13) de forma que **no** se materialice el catálogo completo en memoria de aplicación para “paginar”.
3. **Vista/servicio**: parsear query params; envelope `success_response(..., meta={"pagination": {...}})`.
4. **Tests**: contract list (≤limit, next_cursor, filtros, ownership); p95 list (marker `slow`) alineado a CA-016 / testing.md.
5. **FE** (capa frontend, post-BE): FR-UI-019…021 — fuera del código de este plan BE, pero el contrato debe bastar para el pager.

### Baseline (ya entregado)

Contrato-first SaaS RF-SUSF-001…010, Kafka-only-write, jobs Guayaquil, actor `DirectorEstrategia` en CRUD planes.

## Technical Context

**Language/Version**: Python 3.12 (Django 5 + DRF)  
**Primary Dependencies**: Pinot client (lectura), Kafka writer (mutaciones existentes), JWT RBAC  
**Storage**: Pinot `Dim_Plan` (lectura listado); sin cambio de topics  
**Testing**: pytest contract `test_planes_contract.py`; performance `test_list_planes_p95.py` (slow)  
**Target Platform**: Docker `accidentes-django`  
**Project Type**: Web API (delta list)  
**Performance Goals**: CA-SUSF-016 — p95 listado &lt; 2 s; página default 20; 0 dumps completos en memoria app  
**Constraints**: api-standards cursor pagination; RNF-005a; Pinot broker default LIMIT 10 → **siempre** `LIMIT` explícito en SQL; Director ve inactivos, Proveedor/Admin consulta típica `activo=true`  
**Scale/Scope**: Catálogo comercial (decenas–cientos de planes en horizonte; diseño no asume dump)

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Characteristic | Gate | Notes |
|---|---|---|
| I Functional Suitability | PASS | RF-SUSF-001 listado + CA-016 |
| II Reliability | PASS | Vacío/error sin dump; cursor estable por idplan |
| III Performance | **PASS (condicionado)** | RNF-005a; medición en test p95 / humo |
| IV Interaction Capability | PASS (vía FE Depends-on) | Contrato habilita filtros/pager UI |
| V Security | PASS | Mutaciones Director; GET según Decision 12 |
| VI Compatibility | PASS | cursor + `meta.pagination` = api-standards |
| VII Maintainability | PASS | Mismo `CatalogoPlanService` / `PlanRepository` |
| VIII Flexibility | N/A | Sin pricing regional |
| IX Safety | N/A | Spec §5 |

**Conflictos**: Ninguno. El anti-patrón dump-then-slice es deuda a cerrar, no excepción constitucional.  
**Post-design**: PASS — research Decision 13 + OpenAPI + data-model + quickstart H.

## Project Structure

### Documentation (this feature)

```text
specs/.../subscriptions-and-billing/backend/
├── plan.md                 # this file
├── research.md             # + Decision 13 listado
├── data-model.md           # + semántica listado Dim_Plan
├── quickstart.md           # + escenario H
├── contracts/subscriptions-and-billing.openapi.yaml
└── tasks.md                # /speckit-tasks (siguiente)
```

### Source Code (delta)

```text
backend/
├── apps/suscripciones/
│   ├── views/plan_views.py                 # GET query params + meta.pagination
│   ├── services/catalogo_plan_service.py   # listar(cursor, limit, filters)
│   └── tests/
│       ├── api/test_planes_contract.py
│       └── performance/test_list_planes_p95.py
└── core/repositories/suscripciones/plan_repository.py   # list paginado en origen
```

## Complexity Tracking

| Violation | Why Needed | Alternative rejected |
|-----------|------------|----------------------|
| Posible filtro residual en Python **solo** sobre la página Pinot ya acotada | Pinot SQL limitado (LIKE/`activo` según schema) | `SELECT *` sin LIMIT + slice en memoria — incumple RNF-005a |

## Phases (→ `/speckit-tasks`)

1. OpenAPI `listarPlanes` + envelope pagination  
2. Repo + service + view  
3. Contract + p95 tests  
4. Quickstart H + handoff FE  

## NEEDS CLARIFICATION

Ninguno — resueltos en Clarifications 2026-07-30 (listado) y research Decision 13.
