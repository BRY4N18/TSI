# Tasks: Alta de Unidades — Frontend (paginación + filtros + perf)

**Input**: [`plan.md`](./plan.md), [`spec.md`](./spec.md), [`research.md`](./research.md), [`data-model.md`](./data-model.md), [`contracts/proveedor-flota-lista-alta.ui-contract.md`](./contracts/proveedor-flota-lista-alta.ui-contract.md), [`quickstart.md`](./quickstart.md)  
**Depends-on**: [`../backend/contracts/alta-unidades.openapi.yaml`](../backend/contracts/alta-unidades.openapi.yaml) v1.3.0 (`listUnidades`)  
**Prior work**: US-FE-1…6 (páginas Detalles/Formulario, SMTP, baja, lote, lastId) ya implementados — esta lista es el **delta listado**.

**Tests**: Plan pide contract API list + p95 + Jasmine catálogo (incluir).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable  
- **[US1]…[US7]** = US-FE-1…US-FE-7  
- Paths under `frontend/src/app/modules/red-operativa/alta-unidades/` unless prefixed `backend/`

---

## Phase 1: Setup

**Purpose**: Alinear contratos del delta

- [X] T001 Verify OpenAPI `listUnidades` in `specs/003-operational/Red-Operativa/alta-unidades/backend/contracts/alta-unidades.openapi.yaml` documents `cursor`, `limit` (default 20), `q`, `activo`, `tipounidademergencia`, `meta.pagination.next_cursor`
- [X] T002 [P] Verify UI contract `frontend/contracts/proveedor-flota-lista-alta.ui-contract.md` matches paginación + filtros + timeout

---

## Phase 2: Foundational (Blocking)

**Purpose**: API list paginada — MUST before FE catálogo

**⚠️ CRITICAL**: Blocks US1/US7 (y cualquier `listar()` del módulo)

- [X] T003 Extend `list_by_cliente` in `backend/core/repositories/red_operativa/unidad_emergencia_repository.py` with `cursor`, `limit`, filters `q` / `activo` / `tipounidademergencia`; project list columns (avoid unbounded `SELECT *`); order by `idunidademergencia ASC`; return page + enough info for `next_cursor`
- [X] T004 Update `UnidadListCreateView.get` in `backend/apps/red_operativa/views/unidad_views.py` to parse query params and return `success_response({"items": ...}, meta={"pagination": {"next_cursor": ..., "limit": ...}})`
- [X] T005 [P] Contract tests for paginated/filtered list in `backend/apps/red_operativa/tests/api/test_list_unidades_contract.py` (limit≤20 items, next_cursor, q/activo/tipo, ownership JWT)
- [X] T006 [P] Performance test p95 list under threshold in `backend/apps/red_operativa/tests/performance/test_list_unidades_p95.py` (marker `slow`; align to testing.md Pinot filter ≤100ms where measurable)

**Checkpoint**: `GET /api/v1/red-operativa/unidades?limit=20` returns `meta.pagination`; filters work

---

## Phase 3: User Story 7 — Filtrar y paginar (Priority: P1) 🎯 MVP delta

**Goal**: Catálogo con filtros + páginas (FR-UI-022…025, SC-008/009)

**Independent Test**: Filtro estado/texto/tipo; Siguiente ≤20 filas; vacío claro; Actualizar respeta query

- [X] T007 [US7] Extend `models/unidad-emergencia.contract.ts` with list query params + `pagination: { next_cursor, limit }` on list envelope
- [X] T008 [US7] Update `services/unidad-emergencia-api.service.ts` `listar(params?)` to pass `cursor|limit|q|activo|tipounidademergencia` as HttpParams
- [X] T009 [US7] Update `services/unidad-emergencia-facade.service.ts` `listar` to accept `CatalogQueryState` and surface pagination in `OperationResult`
- [X] T010 [US7] Add filter controls (q, estado Activa/Baja/Todas, tipo) + reset cursor on change in `pages/catalogo/catalogo.page.ts`
- [X] T011 [US7] Add pager (Anterior/Siguiente or Más) driven by `next_cursor` / cursor stack in `pages/catalogo/catalogo.page.ts`
- [X] T012 [US7] Wire loading timeout (~10s) + finalize + error+Reintentar on list in `pages/catalogo/catalogo.page.ts` (no infinite skeleton)

**Checkpoint**: MVP delta — Proveedor pagina y filtra flota

---

## Phase 4: User Story 1 — Explorar flota (Priority: P1)

**Goal**: Primera página del catálogo + ojo → Detalles sigue OK con API paginada

**Independent Test**: Abrir catálogo ≤20 filas; ojo → Detalles sin Guardar

- [X] T013 [US1] Ensure initial `cargarUnidades()` uses `limit=20` and `cursor=null` in `pages/catalogo/catalogo.page.ts`
- [X] T014 [P] [US1] Confirm `pages/detalle/detalle.page.ts` still loads by id (no dependency on full list)

**Checkpoint**: US1 humo con listado acotado

---

## Phase 5: User Story 2 — Crear (Priority: P1)

**Goal**: Post-alta refresca lista con query limpia / localizable

**Independent Test**: Alta → catálogo; unidad localizable (filtro placa si hace falta)

- [X] T015 [US2] After successful create in `pages/formulario/formulario.page.ts`, navigate to catalogo and trigger list with `cursor=null` (optional `q=placa`) so new unit can appear without requiring full dump

---

## Phase 6: User Story 3 — Editar (Priority: P1)

**Goal**: Editar no rompe listado paginado

**Independent Test**: Lápiz → form → Guardar → catálogo

- [X] T016 [US3] After edit save, return to catalogo and reload current filters/page (or page 1) in `pages/formulario/formulario.page.ts` / `catalogo.page.ts` as needed

---

## Phase 7: User Story 4 — Baja / reactivación (Priority: P1)

**Goal**: Tras baja/reactivar, refrescar página actual filtrada

**Independent Test**: Baja 2 pasos → lista actualizada

- [X] T017 [US4] After baja/reactivar success in `pages/catalogo/catalogo.page.ts`, call `cargarUnidades()` with current `CatalogQueryState`

---

## Phase 8: User Story 5 — Lote CSV (Priority: P2)

**Goal**: Lote no sustituye paginación

**Independent Test**: Import → refresh list page 1

- [X] T018 [US5] After lote import in `pages/catalogo/catalogo.page.ts`, reset cursor and reload first page

---

## Phase 9: User Story 6 — lastId (Priority: P2)

**Goal**: Highlight solo si fila visible en página actual

**Independent Test**: Volver con lastId en página → marca; si no visible → sin error

- [X] T019 [US6] Keep `filaClass` / lastId highlight only when id ∈ current `unidades` in `pages/catalogo/catalogo.page.ts` (no auto-jump page)

---

## Phase 10: Polish & Cross-Cutting

- [X] T020 [P] Jasmine: filters reset cursor + pager + timeout/error in `pages/catalogo/catalogo.page.spec.ts`
- [X] T021 [P] Update `services/unidad-emergencia-api.service.spec.ts` for list query params / pagination meta
- [X] T022 Run humo V8–V11 in [`quickstart.md`](./quickstart.md) (filtros, ≤20 filas, Actualizar Timing, meta.pagination)
- [X] T023 Rebuild Docker: `docker compose -f docker/accidentes.yml up -d --build django frontend` and verify containers Up

---

## Phase 11: Polish — Formulario UX humano + chrome Accidente (P1)

**Goal**: Usuario elige Condado por nombre; no ve `idcliente`/`idcondado` como campos técnicos; formulario alinea chrome a Accidente Editar.

**Independent Test**: Nueva/Editar unidad — select Condado legible; dueño como texto de sesión; sin inputs numéricos de PK.

- [X] T024 Cargar catálogo condados (lectura Pinot/API existente o endpoint mínimo GET) y poblar combobox en `pages/formulario/formulario.page.ts`
- [X] T025 Remover/ocultar inputs «Condado (ID)» y «Cliente (dueño)» numéricos; mostrar etiqueta dueño legible; payload sigue enviando IDs en `formulario.page.ts`
- [X] T026 [P] Detalle RO: mostrar nombre de condado (no solo id) en `pages/detalle/detalle.page.ts`
- [X] T027 Alinear chrome formulario (Volver/Cancelar, cards, focus ring) a patrón Accidente en `formulario.page.ts`
- [X] T028 [P] Jasmine: formulario no exige teclear idcondado — `pages/formulario/formulario.page.spec.ts`
- [X] T029 Rebuild Docker frontend (+ django si hubo API) y humo Nueva/Editar unidad

---

## Dependencies & Execution Order

```text
Phase 1 Setup
  → Phase 2 Foundational (BE list)  ← BLOCKING
      → US7 (MVP delta) + US1 in parallel after T004
      → US2–US6 adapt refreshes (after facade listar params)
      → Polish
```

### User Story Dependencies

- **US7**: after Phase 2 — primary delta  
- **US1**: after Phase 2 (uses paginated list)  
- **US2–US6**: after T009 (facade signature); mostly refresh wiring  
- **Polish**: after US7 UI stable  

### Parallel Opportunities

- T001 ∥ T002  
- T005 ∥ T006 after T003–T004  
- T014 ∥ T013 after foundation  
- T020 ∥ T021  

### Parallel Example

```text
Dev A: T003–T006 (backend list)
Dev B: T007–T009 (FE types/api/facade) once OpenAPI known
Then: T010–T012 catalog UI
```

---

## Implementation Strategy

### MVP (este delta)

T001–T012 (+ T013): API paginada + catálogo con filtros/pager/timeout.

### Incremental

US2–US6 refresh wiring → Jasmine/perf humo → Docker.

### Suggested first demo

**US7 + US1**: filtrar, paginar, abrir detalle; medir Actualizar &lt;2s warm.

---

## Notes

- No reimplementar Detalles/Formulario/SMTP salvo roturas por cambio de `listar()`.  
- Client-only slice over full list is **out of plan** (research R1).  
- Next: `/speckit-implement`.
