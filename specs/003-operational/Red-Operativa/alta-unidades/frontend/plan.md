# Implementation Plan: Alta de Unidades — Frontend (lista paginada + filtros)

**Branch / capa**: `alta-unidades/frontend` | **Date**: 2026-07-30 | **Spec**: [`spec.md`](./spec.md)

**Input**: Spec post-analyze: lista + Detalles + Formulario **sin workpanel**; gmail/SMTP; y delta **paginación (20) + filtros + SC-007 (&lt;2s p95)**.  
**Depends-on**: [`../backend/`](../backend/) — OpenAPI `listUnidades` con `cursor`/`limit`/filtros; repo Pinot acotado; create/SMTP/reenviar ya entregados.

## Summary

1. **Backend list delta**: `GET /red-operativa/unidades` pasa de “todas las filas” a **cursor + limit (default 20)** + filtros `q` / `activo` / `tipounidademergencia`, con `meta.pagination` (api-standards). Query Pinot **sin `SELECT *` masivo**; proyección de columnas de lista.  
2. **Frontend catálogo**: controles de filtro + paginación; Actualizar respeta estado; timeout UI → error+Reintentar (FR-UI-022…025, SC-007…009).  
3. Mantener rutas `catalogo` / `detalle/:id` / `nueva` / `editar/:id`, SMTP UI y lastId.  
4. Perf: test p95 lista + humo Timing (TTFB); meta UI &lt;2s p95; consulta Pinot alineada a `testing.md` (≤100ms p95 ideal en filtro simple).

## Technical Context

**Language/Version**: Angular 17+ TypeScript; Django/DRF (delta list)  
**Primary Dependencies**: Router, forms, Tabler, NotificationService; Pinot via repositories; envelope `meta.pagination`  
**Storage**: Pinot read (lista); Kafka write (ya existente en altas); sessionStorage lastId  
**Testing**: Jasmine catálogo (filtros/página); contract API list; pytest performance list p95 (marker slow)  
**Target Platform**: Docker `accidentes-frontend` / `accidentes-django`  
**Project Type**: Web FE + delta BE listado  
**Performance Goals**: SC-007 — 95% aperturas/Actualizar muestran resultado &lt;2s; Pinot list query p95 ≤100ms (testing.md); timeout UI ~8–15s con error  
**Constraints**: api-standards cursor pagination; flota propia JWT; no password en UI; sin workpanel; rebuild Docker  
**Scale/Scope**: Flotas decenas–cientos unidades/proveedor; página 20  

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Characteristic | Gate | Notes |
|---|---|---|
| I Functional Suitability | PASS | O54–58 + catálogo operable (US-FE-7) |
| II Reliability | PASS | Timeout + Reintentar; SMTP fail visible |
| III Performance | **PASS (condicionado)** | SC-007 declarado; diseño lista acotada; gate post-implement exige medición |
| IV Interaction Capability | PASS | Filtros + paginación; lista no comprimida por workpanel |
| V Security | PASS | Solo flota propia; secretos fuera UI |
| VI Compatibility | PASS | Cursor/`meta.pagination` = api-standards |
| VII Maintainability | PASS | Un form; un read; list facade parametrizado |
| VIII Flexibility | N/A | Sin multi-ciudad en este delta |
| IX Safety | PASS (indirecta) | Catálogo correcto → despacho |

**Conflictos**: Ninguno documentado. Performance deja de ser N/A (spec).  
**Post-design**: PASS — research + contracts alineados.

## Project Structure

### Documentation (this feature)

```text
specs/.../alta-unidades/frontend/
├── plan.md                 # this file
├── research.md             # Phase 0
├── data-model.md           # Phase 1
├── quickstart.md           # Phase 1
├── contracts/
│   └── proveedor-flota-lista-alta.ui-contract.md
└── tasks.md                # /speckit-tasks (not this command)

../backend/contracts/alta-unidades.openapi.yaml   # delta listUnidades
```

### Source Code (repository)

```text
backend/
├── apps/red_operativa/views/unidad_views.py          # GET query params + meta.pagination
├── core/repositories/.../unidad_emergencia_repository.py  # list_by_cliente(cursor, limit, filters)
└── apps/red_operativa/tests/
    ├── api/test_list_unidades_contract.py
    └── performance/test_list_unidades_p95.py

frontend/src/app/modules/red-operativa/alta-unidades/
├── pages/catalogo/catalogo.page.ts                   # filtros + paginación + timeout
├── models/unidad-emergencia.contract.ts
├── services/unidad-emergencia-api.service.ts
└── services/unidad-emergencia-facade.service.ts
```

## Complexity Tracking

| Violation | Why Needed | Alternative rejected |
|-----------|------------|----------------------|
| Delta BE desde plan FE | FR-UI-022/023 + api-standards; FE no puede paginar de verdad sin API | Solo slice client-side sobre flota completa — incumple SC-007 a escala y standards |

## Phases (→ `/speckit-tasks`)

1. OpenAPI + repo + view: cursor/limit/filtros + meta.pagination  
2. Contract + p95 tests lista  
3. FE contract/facade/API params  
4. Catálogo UI: filtros, pager, timeout  
5. Jasmine + quickstart V8–V11 + Docker rebuild  

## NEEDS CLARIFICATION

Ninguno — resueltos en research (cursor id-based como regiones; filtros q/activo/tipo).
