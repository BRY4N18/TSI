# Tasks: Suscripciones — Frontend

**Input**: [`plan.md`](./plan.md), [`spec.md`](./spec.md), [`quickstart.md`](./quickstart.md)  
**Depends-on**: [`../backend/`](../backend/) — `GET /suscripciones/planes` cursor/limit/filtros + `meta.pagination` (**T096–T107 `[X]`**)  
**Prior work**: T-FE-001…018 (shell, portal, UX ojo/lápiz/detalle/form) — `[X]`.  
**Este delta**: filtros + paginación catálogo (FR-UI-019…021, US-FE-2 escenarios 8–9, SC-007…009).  
**Remediación 2026-07-30**: filtro Estado «Todas» — BE ya no fuerza `solo_activos=true` para Director; FE envía `solo_activos=false`.

**Tests**: Jasmine catálogo (filtros/pager/timeout) — plan/spec lo piden.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable  
- **[US2]** = US-FE-2 (catálogo Director)  
- Paths under `frontend/src/app/modules/suscripciones/` unless noted

### User Story Map (delta)

| Story | Prioridad | FR / SC | Independent test |
|-------|-----------|---------|------------------|
| US2 | P1 🎯 MVP delta | FR-UI-019…021, SC-007…009 | ≤20 filas; filtros reinician página; Siguiente; timeout→Reintentar |

---

## Phase 1–9: Baseline + UX piloto (done)

- [X] T-FE-001…009 Shell, portal Proveedor, catálogo/form, guards, tipos, rutas, skeletons
- [X] T-FE-010…018 Detalle RO, ojo/lápiz, Guardar cabecera, Jasmine V-PLAN-1…5, Docker

---

## Phase 10: Setup — Delta listado (Shared)

**Purpose**: Confirmar Depends-on BE + tipos cliente listos antes de UI.

- [X] T-FE-019 Verificar OpenAPI `listarPlanes` en `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/contracts/subscriptions-and-billing.openapi.yaml` (cursor, limit default 20, q/activo/nivel, `meta.pagination`)
- [X] T-FE-020 [P] Confirmar / completar `PlanListQuery` + `PlanListEnvelope.meta.pagination` en `services/models/suscripciones.types.ts` y que `services/plan-api.service.ts` `listar(PlanListQuery | boolean)` envía `HttpParams` (no dump implícito con `limit` omitido en el camino catálogo)

**Checkpoint**: Cliente tipado listo para catálogo paginado.

---

## Phase 11: Foundational — API catálogo (Blocking)

**Purpose**: Camino `listar` del catálogo usa siempre `limit=20` + cursor/filtros. Bloquea UI.

**CRITICAL**: No implementar filtros/pager UI hasta T-FE-021.

- [X] T-FE-021 Asegurar que el camino de catálogo **nunca** llama `listar(false|true)` sin `limit` acotado: preferir solo `listar(PlanListQuery)` con `limit: 20` desde `pages/catalogo-planes/catalogo-planes.page.ts` (compat boolean queda para detalle/form temporales si hace falta)

**Checkpoint**: Catálogo puede pedir página 1 sin cargar universo.

---

## Phase 12: User Story 2 — Filtrar y paginar catálogo (Priority: P1) 🎯 MVP delta

**Goal**: FR-UI-019…021 — Director filtra y pagina el catálogo sin dump en el cliente.

**Independent Test**: >20 planes filtrados → ≤20 filas visibles; Siguiente pide `cursor`; cambiar filtro → página 1; Actualizar reaplica; timeout → error+Reintentar.

### Implementation

- [X] T-FE-022 [US2] Añadir estado de query (`q`, `activo`: true|false|null Todas, `nivel`, `cursor`, stack de cursores previos, `limit=20`) en `pages/catalogo-planes/catalogo-planes.page.ts`
- [X] T-FE-023 [US2] Controles de filtro (texto nombre, estado Activo/Inactivo/Todas, nivel) en `pages/catalogo-planes/catalogo-planes.page.html`; al cambiar filtro reset `cursor`/stack y recargar
- [X] T-FE-024 [US2] Pager Anterior/Siguiente (o Más) según `meta.pagination.next_cursor` en `catalogo-planes.page.ts` / `.html`; «Actualizar» reaplica query actual
- [X] T-FE-025 [US2] Timeout ~10s + finalize + error+Reintentar en carga de listado (sin skeleton infinito) en `catalogo-planes.page.ts`
- [X] T-FE-026 [US2] Tras desactivar/reactivar, recargar con el `CatalogQueryState` actual (no pedir catálogo completo)

### Tests

- [X] T-FE-027 [P] [US2] Jasmine: filtros resetean cursor; pager; timeout/error — `pages/catalogo-planes/catalogo-planes.page.spec.ts`
- [X] T-FE-028 [P] [US2] Jasmine: `plan-api.service` (o spec existente) pasa query params / lee `meta.pagination` — `services/plan-api.service.spec.ts` (crear si no existe)

**Checkpoint**: SC-007…009 verificables en UI + Jasmine.

---

## Phase 13: Cross-story — Detalle / Form sin depender del dump

**Goal**: Ojo/lápiz siguen OK sin listar el universo en el catálogo.

**Independent Test**: Detalle y editar abren un plan por id aunque el catálogo solo tenga la página actual.

- [X] T-FE-029 [US2] `pages/plan-detalle/plan-detalle.page.ts` y `pages/plan-form/plan-form.page.ts`: cargar plan por id **sin** usar el listado del catálogo en memoria; si no hay `GET planes/{id}`, usar lectura acotada (`listar` con filtros/limit + find, o estrategia documentada) — **prohibido** paginar el catálogo completo en el cliente solo para abrir detalle

**Checkpoint**: US2 escenarios 1–2 + 8–9 coexisten.

---

## Phase 14: Polish

- [X] T-FE-030 [P] Extender [`quickstart.md`](./quickstart.md) con V-PLAN-6…8 (≤20 filas, filtros reinician página, pager/`meta.pagination`, Actualizar &lt;2s warm)
- [X] T-FE-031 Rebuild Docker: `docker compose -f docker/accidentes.yml up -d --build frontend` y verificar `accidentes-frontend` Up

---

## Dependencies & Execution Order

```text
[Histórico] T-FE-001…018 [X]
[Delta]
  T-FE-019 → T-FE-020
  → T-FE-021 (foundational)
  → T-FE-022…026 (US2 MVP) 🎯
  → T-FE-027 ∥ T-FE-028
  → T-FE-029 (detalle/form)
  → T-FE-030 ∥ → T-FE-031
```

### Parallel opportunities

- T-FE-019 ∥ T-FE-020  
- T-FE-027 ∥ T-FE-028 tras T-FE-025  
- T-FE-030 ∥ T-FE-029  

### Independent test criteria

| Story | Cómo probar solo |
|-------|------------------|
| US2 delta | Director: filtros + ≤20 filas + Siguiente; Jasmine T-FE-027; humo V-PLAN-6…8 |

---

## Implementation Strategy

### MVP delta (ship ahora)

T-FE-019…026 (+ T-FE-027) → catálogo filtrable/paginado.

### Luego

T-FE-029 detalle/form; T-FE-030–031 polish/Docker.

---

## Format validation

- Todas las tareas delta: `- [ ]`, ID `T-FE-nnn`, paths, `[US2]` en fases de historia.
- Histórico T-FE-001…018 permanece `[X]`.
