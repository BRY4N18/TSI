# Tasks: Pipeline Comercial â€” Frontend (delta workpanel)

**Input**: [`plan.md`](./plan.md), [`spec.md`](./spec.md), [`research.md`](./research.md), [`data-model.md`](./data-model.md), [`contracts/prospectos-lista-workpanel.ui-contract.md`](./contracts/prospectos-lista-workpanel.ui-contract.md), [`quickstart.md`](./quickstart.md)  
**Depends-on**: [`../backend/`](../backend/) â€” listado/detalle/pipeline/asignaciÃ³n/conversiÃ³n/entrada-directa (sin PATCH ficha)  
**Prior work**: T-FE-001â€¦010 (portal pÃºblico, stubs CRM, guards, API services) â€” `[X]`.  
**Este delta**: lista + workpanel Ver + filtros/pager + board botones (FR-UI-004â€¦008, 012, 015; US-FE-3/4/6; SC-001â€¦005).

**Tests**: Jasmine listado/workpanel/board â€” plan lo pide.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable  
- **[US3]** = US-FE-3 (listado + workpanel Ver)  
- **[US4]** = US-FE-4 (board)  
- **[US5]** = US-FE-5 (entrada directa polish)  
- **[US6]** = US-FE-6 (conversiÃ³n en workpanel)  
- Paths under `frontend/src/app/modules/ventas-crm/` unless noted

### User Story Map (delta)

| Story | Prioridad | FR / SC | Independent test |
|-------|-----------|---------|------------------|
| US3 | P1 ðŸŽ¯ MVP delta | FR-UI-004, 005, 007, 008, 012, 015; SC-001â€¦005 | Tabla+ojo; sin lÃ¡piz; filtros reinician pÃ¡gina; Admin CTA; Detalles sin Guardar |
| US4 | P1 | FR-UI-006, 007, 008 | Board botones + ojo; sin drag; 409+Refrescar |
| US6 | P1 | FR-UI-005 (convertir), RF-CPP-006 | Convertir desde workpanel en NegociaciÃ³n |
| US5 | P2 | FR-UI-009, 015 | Admin Entrada directa usable desde CTA listado |

---

## Phase 1â€“4: Baseline embudo (done)

- [X] T-FE-001â€¦003 Portal pÃºblico planes + registro + rutas
- [X] T-FE-004â€¦007 Stubs listado/detalle/board + 409/motivo + guards
- [X] T-FE-008â€¦010 Entrada directa + API services + lazy nav

---

## Phase 5: Setup â€” Delta workpanel (Shared)

**Purpose**: Confirmar contrato UI + tipos de query antes de tocar pÃ¡ginas.

- [X] T-FE-011 Verificar UI contract [`contracts/prospectos-lista-workpanel.ui-contract.md`](./contracts/prospectos-lista-workpanel.ui-contract.md) vs OpenAPI `listarProspectos` / `obtenerProspecto` / pipeline / asignaciÃ³n / conversiÃ³n en `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/contracts/commercial-pipeline-prospects.openapi.yaml`
- [X] T-FE-012 [P] Completar tipos de query listado (`activo`, `etapa_actual`, `cursor`, `limit`) + lectura `meta.pagination` en `models/prospectos.types.ts` si faltan aliases claros para el estado UI (`ListadoProspectosQueryState` en data-model)
- [X] T-FE-013 [P] Asegurar `services/prospecto-api.service.ts` `listar(...)` envÃ­a `HttpParams` explÃ­citos (`limit` default 20; `activo=false` no se pierde; omitir params vacÃ­os)

**Checkpoint**: Cliente tipado listo para listado filtrado/paginado.

---

## Phase 6: Foundational â€” camino listar acotado (Blocking)

**Purpose**: NingÃºn listado autenticado pide dump sin `limit`.

**CRITICAL**: No UI de filtros/tabla hasta T-FE-014.

- [X] T-FE-014 Garantizar que `pages/listado-prospectos/listado-prospectos.page.ts` y `pages/pipeline-board/pipeline-board.page.ts` solo llaman `listar` con `limit` acotado (â‰¤20 o documentado â‰¤100 para board) â€” **prohibido** listar sin tope

**Checkpoint**: Listado puede pedir pÃ¡gina 1 sin cargar universo.

---

## Phase 7: User Story 3 â€” Listado + workpanel Ver (Priority: P1) ðŸŽ¯ MVP delta

**Goal**: FR-UI-004, 005, 015 â€” tabla piloto, ojo â†’ Detalles RO, filtros, pager, CTA Admin.

**Independent Test**: Admin login â†’ listado tabla; filtros activo/etapa; ojo â†’ Detalles sin Guardar/lÃ¡piz; nombre texto plano; CTA Entrada directa solo Admin.

### Implementation

- [X] T-FE-015 [US3] Reescribir `pages/listado-prospectos/listado-prospectos.page.ts` (+ extraer template HTML si procede): estado query (`filtroActivo`, `filtroEtapa`, `cursor`, stack, `limit=20`), timeout ~10s, skeleton/vacÃ­o/error+Reintentar, tokens design-system
- [X] T-FE-016 [US3] Tabla + filtros activo/etapa + pager Anterior/Siguiente + Actualizar; al cambiar filtro reset cursor/stack; nombre/empresa texto plano en `listado-prospectos.page.ts` / template
- [X] T-FE-017 [US3] AcciÃ³n fila solo `eye` â‰¥44Ã—44 (`aria-label="Ver detalles"`) â†’ `/ventas-crm/prospectos/:id`; **MUST NOT** renderizar lÃ¡piz; TablerIcon en listado
- [X] T-FE-018 [US3] CTA header Â«Entrada directaÂ» solo si `hasRole('Administrador')` â†’ `/ventas-crm/entrada-directa`; Gerente sin CTA alta (`listado-prospectos.page.ts`)
- [X] T-FE-019 [US3] Reescribir `pages/detalle-prospecto/detalle-prospecto.page.ts` como workpanel **Ver**: tÃ­tulo Â«DetallesÂ»; campos RO/disabled; **sin** Guardar ficha; Volver al listado; design-system
- [X] T-FE-020 [US3] Acciones de dominio en workpanel: avance adyacente + Perdido (modal motivo FR-UI-007) vÃ­a `PipelineApiService`; asignaciÃ³n huÃ©rfano/reasignaciÃ³n visible segÃºn Admin/dueÃ±o (`ProspectoApiService.asignar`); 409 â†’ toast + Refrescar (re-GET)

### Tests

- [X] T-FE-021 [P] [US3] Jasmine listado: filtros resetean cursor; sin lÃ¡piz; CTA Admin vs no-Admin; ojo presente â€” `pages/listado-prospectos/listado-prospectos.page.spec.ts` (crear)
- [X] T-FE-022 [P] [US3] Jasmine workpanel: tÃ­tulo Detalles; sin Guardar ficha; 409 dispara refresco/mensaje â€” `pages/detalle-prospecto/detalle-prospecto.page.spec.ts` (crear)
- [X] T-FE-023 [P] [US3] Jasmine `prospecto-api.service.spec.ts`: `listar` envÃ­a `limit`/`activo`/`etapa_actual`/`cursor` como query params

**Checkpoint**: SC-001, SC-002, SC-004, SC-005 verificables en listado + workpanel.

---

## Phase 8: User Story 6 â€” ConversiÃ³n desde workpanel (Priority: P1)

**Goal**: FR-UI-005 / US-FE-6 â€” convertir en NegociaciÃ³n desde Detalles.

**Independent Test**: Prospecto en NegociaciÃ³n â†’ formulario tipo+NIT â†’ Ã©xito o 409 NIT; no visible fuera de NegociaciÃ³n/activo.

- [X] T-FE-024 [US6] UI conversiÃ³n en `pages/detalle-prospecto/detalle-prospecto.page.ts` (solo etapa NegociaciÃ³n + activo) vÃ­a `ConversionApiService`; errores/409 con feedback + Refrescar
- [X] T-FE-025 [P] [US6] Jasmine: conversiÃ³n visible solo en NegociaciÃ³n; submit llama API â€” `pages/detalle-prospecto/detalle-prospecto.page.spec.ts`

**Checkpoint**: SC-003 cubre convertir cuando aplica.

---

## Phase 9: User Story 4 â€” Pipeline board (Priority: P1)

**Goal**: FR-UI-006 â€” board operativo con botones + ojo; sin drag.

**Independent Test**: Columnas; avance/Perdido por botones; ojo abre workpanel; empresa no es Ãºnico enlace; sin DnD handlers.

### Implementation

- [X] T-FE-026 [US4] Reescribir `pages/pipeline-board/pipeline-board.page.ts`: columnas etapas activas; cards con empresa texto plano; botones avance adyacente + Perdido (motivo); **sin** drag-and-drop
- [X] T-FE-027 [US4] Ojo â‰¥44Ã—44 por card â†’ workpanel; 409 en transiciÃ³n â†’ toast + Refrescar listado board; design-system / TablerIcon

### Tests

- [X] T-FE-028 [P] [US4] Jasmine board: sin drag; ojo presente; avance llama pipeline API â€” `pages/pipeline-board/pipeline-board.page.spec.ts` (crear)

**Checkpoint**: US-FE-4 + FR-UI-006.

---

## Phase 10: User Story 5 â€” Entrada directa polish (Priority: P2)

**Goal**: FR-UI-009 + CTA listado aterriza en form usable (no stub crudo si aÃºn lo es).

**Independent Test**: Admin CTA â†’ pÃ¡gina entrada-directa con form + estados async; Gerente guard 403/redirect.

- [X] T-FE-029 [US5] Alinear UX `pages/entrada-directa/entrada-directa.page.ts` al design-system (skeleton/error, labels, submit Idempotency si aplica) sin cambiar contrato BE
- [X] T-FE-030 [P] [US5] Jasmine: guard/pÃ¡gina Admin â€” `pages/entrada-directa/entrada-directa.page.spec.ts` (crear si no existe)

**Checkpoint**: SC-004 end-to-end Admin.

---

## Phase 11: Polish

- [X] T-FE-031 [P] Extender [`quickstart.md`](./quickstart.md) marcando V-CRM-1â€¦6 como checklist post-implement (credenciales Admin ya documentadas)
- [X] T-FE-032 Rebuild Docker: `docker compose -f docker/accidentes.yml up -d --build frontend` y verificar `accidentes-frontend` Up

---

## Phase 12: Polish — homogeneidad design-system (lista Accidentes)

- [X] T-FE-033 Shared `list-loading-skeleton` / `list-error-state` / `list-empty-state` + `list-table.styles.ts`
- [X] T-FE-034 Homogeneizar Prospectos listado + pipeline-board + notificaciones-ventas
- [X] T-FE-035 Homogeneizar Suscripciones listados (planes, facturas, métodos, aprobaciones, cambio-plan)
- [X] T-FE-036 Homogeneizar red-operativa catálogos + hub cuenta + config SLA
- [X] T-FE-037 design-system: cláusula Ver-only / puntero a `shared/ui/list-states`
- [X] T-FE-038 Rebuild Docker frontend post-homogeneización

---

## Phase 13: User Story 3/5 polish — Workpanel + forms chrome Accidente (P1) 🎯

**Goal**: FR-UI-005, 009, 016; SC-001, SC-006 — Detalles y Entrada directa dejan de verse “stub”; UX humano (sin IDs).

**Independent Test**: Ojo → Detalles: `← Volver`, título+badge, `dl` (cero inputs disabled de ficha), acciones con íconos; Admin Entrada directa mismo shell; asignación/gerente por combobox nombre si aplica.

### Foundational (docs already updated — verify before code)

- [X] T-FE-039 Verificar UI contract Phase 13 + FR-UI-005/009/016 en [`contracts/prospectos-lista-workpanel.ui-contract.md`](./contracts/prospectos-lista-workpanel.ui-contract.md) y [`spec.md`](./spec.md) vs golden `frontend/src/app/modules/accidentes/pages/detalle-accidente/detalle-accidente.page.html`

### Implementation — US3 workpanel

- [X] T-FE-040 [US3] Reescribir chrome `pages/detalle-prospecto/detalle-prospecto.page.ts`: shell `max-w-6xl`, link Volver+`arrow-left`, eyebrow Detalles, h1+badges, cards `p-6`, grid principal+historial; TablerIcon
- [X] T-FE-041 [US3] Sustituir inputs disabled de ficha por `<dl>`/`dt`/`dd` RO (empresa, email, teléfono, cargo, org, etc.) en `detalle-prospecto.page.ts`
- [X] T-FE-042 [US3] Acciones dominio + Perdido/convertir/asignar: botones Accidente-style + íconos; loading/error → shared `list-states`; si hay gerente: combobox nombre/email **no** input numérico ID en `detalle-prospecto.page.ts`
- [X] T-FE-043 [P] [US3] Actualizar Jasmine workpanel: sin inputs disabled de ficha; Volver link presente — `pages/detalle-prospecto/detalle-prospecto.page.spec.ts`

### Implementation — US5 entrada directa

- [X] T-FE-044 [US5] Alinear `pages/entrada-directa/entrada-directa.page.ts` al chrome Accidente (Volver link, card secciones, focus ring, submit carga, error+ícono); sin IDs técnicos
- [X] T-FE-045 [P] [US5] Jasmine entrada-directa chrome/submit — `pages/entrada-directa/entrada-directa.page.spec.ts`

### Cross-cutting UX (alta-unidades — mismo principio, no solo CRM)

- [X] T-FE-046 Condado = combobox por **nombre** (API/catálogo existente o endpoint lectura); ocultar/remover input «Condado (ID)» en `frontend/src/app/modules/red-operativa/alta-unidades/pages/formulario/formulario.page.ts`
- [X] T-FE-047 Cliente dueño: etiqueta legible (sesión/proveedor) — **MUST NOT** mostrar input editable `idcliente` numérico; chrome formulario cercano a Accidente Editar en `formulario.page.ts` + RO en `pages/detalle/detalle.page.ts` si muestra IDs crudos
- [X] T-FE-048 [P] Jasmine formulario: no requiere teclear idcondado crudo — `frontend/src/app/modules/red-operativa/alta-unidades/pages/formulario/formulario.page.spec.ts`
- [X] T-FE-049 Espejar tareas T046–T048 en `specs/003-operational/Red-Operativa/alta-unidades/frontend/tasks.md` (trazabilidad del módulo dueño)

### Polish

- [X] T-FE-050 [P] Extender design-system: Ver=`dl`; catálogos=combobox; chrome workpanel=detalle-accidente — `.specify/docs/design/design-system.md`
- [X] T-FE-051 [P] Humo quickstart: Detalles + Entrada directa + Editar unidad (combobox) en [`quickstart.md`](./quickstart.md)
- [X] T-FE-052 Rebuild Docker: `docker compose -f docker/accidentes.yml up -d --build frontend` (+ django si hay API catálogo condado)

**Checkpoint**: SC-006 verificable; usuario no ve formularios “feos” ni campos ID.

---

## Dependencies & Execution Order

```text
[Histórico] T-FE-001…038 [X]
[Phase 13]
  T-FE-039
  → T-FE-040 → T-FE-041 → T-FE-042 → T-FE-043
  → T-FE-044 → T-FE-045
  → T-FE-046 → T-FE-047 → T-FE-048 ∥ T-FE-049
  → T-FE-050 ∥ T-FE-051 → T-FE-052
```

### Parallel opportunities

- T-FE-012 ∥ T-FE-013  
- T-FE-021 ∥ T-FE-022 ∥ T-FE-023 tras T-FE-020  
- T-FE-043 ∥ T-FE-045 tras impl  
- T-FE-046…048 (unidades) ∥ T-FE-040…045 (CRM) tras T-FE-039  
- T-FE-050 ∥ T-FE-051  

### Independent test criteria

| Story | Cómo probar solo |
|-------|------------------|
| US3 MVP lista | Admin: filtros + ojo; Jasmine listado |
| US3 Phase 13 | Detalles = chrome Accidente + `dl` RO |
| US6 | Workpanel Negociación → convertir |
| US4 | Board botones + ojo |
| US5 Phase 13 | Entrada directa chrome Accidente |
| Cross UX | Editar unidad: condado por nombre, sin idcliente visible |

---

## Implementation Strategy

### MVP delta (ya shipped)

T-FE-011…038 → listado/board + list-states.

### Siguiente (Phase 13) 🎯

T-FE-039…052 → workpanel + entrada directa + formulario unidades (UX humano).

### Luego

`/speckit-implement` Phase 13; commit.

---

## Format validation

- Phase 13: `- [ ]`, ID `T-FE-nnn`, paths, `[USn]` en historias.
- Histórico T-FE-001…038 permanece `[X]`.
