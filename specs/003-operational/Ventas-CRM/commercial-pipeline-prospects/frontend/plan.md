# Implementation Plan: Pipeline Comercial — Frontend (delta workpanel)

**Capa**: `commercial-pipeline-prospects/frontend` | **Date**: 2026-07-30  
**Spec**: [`spec.md`](./spec.md)  
**Depends-on**: [`../backend/`](../backend/) — RF-CPP-*, OpenAPI listado/detalle/pipeline/asignación/conversión/entrada-directa (sin PATCH de ficha).

## Summary

### Ya entregado (baseline embudo)

1. Portal público planes + registro; stubs autenticados listado/detalle/board/entrada-directa; guards; API services (FR-UI-001…014 histórico).

### Delta pendiente (piloto CRUD / clarificación workpanel)

1. Sustituir stubs de listado/detalle/board por UX piloto Accidentes: tabla + **ojo** → workpanel **Ver**; filtros `activo`/`etapa_actual`; pager cursor; CTA «Entrada directa» solo Admin.
2. Workpanel Ver: campos RO, acciones de dominio (avance, Perdido+motivo, convertir, asignar Admin); 409 → toast + Refrescar; **sin** lápiz ni Guardar de ficha.
3. Board: columnas + botones adyacentes/Perdido; ojo → workpanel; **sin** drag.
4. Jasmine + humo quickstart; rebuild Docker frontend.

### Phase 13 (pendiente — chrome Accidente + UX humano)

1. Workpanel Detalles = chrome Accidente (`← Volver`, `dl` tipográfico, no inputs disabled).
2. Entrada directa mismo shell/formularios.
3. Cruzado alta-unidades: Condado combobox por nombre; sin IDs cliente/condado visibles.
4. Ver UI contract + FR-UI-005/009/016 + tasks T-FE-039…052.

## Technical Context

**Language/Version**: Angular 17+ TypeScript (standalone, OnPush, signals)  
**Primary Dependencies**: Router, FormsModule/ReactiveForms, TablerIcon, NotificationService; services tipados desde OpenAPI  
**Testing**: Jasmine listado/workpanel/board (filtros, ojo, sin lápiz, CTA Admin); humo V-CRM  
**Target Platform**: Docker `accidentes-frontend` (:4200) + `accidentes-django` (:8000)  
**Performance Goals**: SC-005 filtros; listado usa cursor/limit BE (no dump cliente)  
**Constraints**: Depends-on sin PATCH ficha; Gerente sin CTA alta; sin split-view obligatorio; sin drag  
**Scale/Scope**: Misma paginación cursor del BE; UI default limit 20

## Constitution Check

| Characteristic | Gate | Notes |
|---|---|---|
| I Functional Suitability | PASS | FR-UI citan RF-CPP-* |
| II Reliability | PASS | 409 + Refrescar; timeout/error+Reintentar |
| III Performance | PASS (condicionado) | Paginación BE; humo listado |
| IV Interaction Capability | PASS | Workpanel Ver + filtros + SC-001…005 |
| V Security | PASS | Guards existentes; CTA Admin-only |
| VI Compatibility | PASS | Params OpenAPI; sin inventar PATCH |
| VII Maintainability | PASS | Reusar pages/services; design-system tokens |
| VIII Flexibility | N/A | — |
| IX Safety | N/A | CRM comercial, no despacho |

## Source Code (delta)

```text
frontend/src/app/modules/ventas-crm/
├── pages/listado-prospectos/listado-prospectos.page.ts (+ html/spec si se extrae)
├── pages/detalle-prospecto/detalle-prospecto.page.ts
├── pages/pipeline-board/pipeline-board.page.ts
├── pages/entrada-directa/entrada-directa.page.ts  # polish CTA destino
├── services/prospecto-api.service.ts
├── services/pipeline-api.service.ts
├── services/conversion-api.service.ts
└── models/prospectos.types.ts
```

## Phases (→ `/speckit-tasks`)

1. Research + UI contract + types query/pagination  
2. Listado: tabla, filtros, ojo, CTA Admin, pager  
3. Workpanel Ver: RO + acciones dominio + 409  
4. Board: botones + ojo; sin drag  
5. Jasmine + quickstart humo + Docker rebuild  

## NEEDS CLARIFICATION

Ninguno — Session 2026-07-30 (workpanel CRUD) cerrada (5/5).
