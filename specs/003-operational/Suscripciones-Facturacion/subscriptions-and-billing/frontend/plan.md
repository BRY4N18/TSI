# Implementation Plan: Suscripciones — Frontend

**Capa**: `subscriptions-and-billing/frontend` | **Date**: 2026-07-30  
**Spec**: [`spec.md`](./spec.md)  
**Depends-on**: [`../backend/plan.md`](../backend/plan.md) — listado `GET /suscripciones/planes` con cursor/limit/filtros + `meta.pagination` (RNF-SUSF-005a).

## Summary

### Ya entregado (UX piloto)

1. Catálogo + Detalles RO + Form; ojo/lápiz; Guardar en cabecera; sin workpanel split (FR-UI-014…018).

### Delta pendiente (tras BE listado)

1. Consumir `listar(params)` con `cursor|limit|q|activo|nivel` y `meta.pagination` (FR-UI-019…021).
2. Controles de filtro + pager en `catalogo-planes`; **prohibido** cachear catálogo completo en el cliente para paginar.
3. Jasmine + humo V-PLAN filtros/pager; timeout → error+Reintentar.
4. Rebuild Docker frontend.

## Technical Context

**Language/Version**: Angular 17+ TypeScript  
**Primary Dependencies**: Router, forms, Tabler, NotificationService; `PlanApiService` tipado desde OpenAPI  
**Testing**: Jasmine catálogo (filtros/página); humo quickstart  
**Target Platform**: Docker `accidentes-frontend`  
**Performance Goals**: SC-007/008 — ≤20 filas; &lt;2 s p95 al ver catálogo  
**Constraints**: Depends-on BE; solo Director CRUD; sin dump en memoria cliente  
**Scale/Scope**: Misma página 20 que backend

## Constitution Check

| Characteristic | Gate | Notes |
|---|---|---|
| I Functional Suitability | PASS | FR-UI citan RF-SUSF-001 listado |
| II Reliability | PASS | Timeout + Reintentar |
| III Performance | PASS (condicionado) | SC-007/008; medición humo |
| IV Interaction Capability | PASS | Filtros + pager |
| V Security | PASS | Guards existentes |
| VI Compatibility | PASS | meta.pagination |
| VII Maintainability | PASS | Facade/API params |
| VIII Flexibility | N/A | — |
| IX Safety | N/A | — |

## Source Code (delta listado)

```text
frontend/src/app/modules/suscripciones/
├── pages/catalogo-planes/catalogo-planes.page.*
├── services/plan-api.service.ts
└── services/models/suscripciones.types.ts
```

## Phases (→ `/speckit-tasks` en capa frontend, después de BE)

1. Types + PlanApiService query params / pagination meta  
2. Catálogo: filtros + pager + timeout  
3. Jasmine + humo + Docker  

## NEEDS CLARIFICATION

Ninguno — Depends-on backend Decision 13.
