# Research: Alta de Unidades — Frontend (paginación + filtros + perf)

**Date**: 2026-07-30  
**Spec**: [`spec.md`](./spec.md) (US-FE-7, FR-UI-022…025, SC-007…009)

## R1 — Paginación: cursor por `idunidademergencia`

**Decision**: `GET …/unidades?cursor=&limit=20` donde `cursor` es el último `idunidademergencia` visto (entero, como `RegionListView`). Respuesta: `data.items` + `meta.pagination = { next_cursor, limit }`. Default `limit=20` (máx. razonable 100).

**Rationale**: api-standards exige cursor (no offset page). Ya hay patrón en `red_operativa` regiones y otros módulos. Spec pide página 20.

**Alternatives considered**: Offset `page=N` — rechazado (standards). Solo slice en Angular tras `SELECT *` — rechazado (SC-007 / Network: el coste es servidor/Pinot, no el JSON de 3 KB).

## R2 — Filtros server-side

**Decision**: Query params:

| Param | Meaning |
|-------|---------|
| `q` | Texto libre: coincide en `placa` **o** `unidademergencia` (contains / case-insensitive según capacidades Pinot; si Pinot limita, igualdad/prefijo documentado en OpenAPI) |
| `activo` | `true` \| `false` \| omitido (= Todas) |
| `tipounidademergencia` | enum tipounidad o omitido |

Cambiar filtros en UI → reset `cursor` (primera página).

**Rationale**: FR-UI-023; filtrar en cliente sobre flota completa no escala y contradice el hallazgo Network (TTFB).

**Alternatives considered**: Solo filtro client-side — rechazado.

## R3 — Query Pinot de lista

**Decision**: `list_by_cliente` proyecta columnas de fila de catálogo (no `SELECT *` si el broker lo permite); `WHERE idcliente = ?` + filtros; orden `idunidademergencia ASC`; `LIMIT limit+1` o `LIMIT limit` + next_cursor = último id si hay más. Preferir filtro en SQL vs filtrar en Python tras traer todo.

**Rationale**: testing.md Pinot SELECT con filtro ≤100ms p95; evidencia DevTools payload pequeño pero wait largo → reducir trabajo broker.

**Alternatives considered**: Traer todo y paginar en memoria — rechazado.

## R4 — Timeout UI / loading

**Decision**: Catálogo: timeout observable ~**10s**; al vencer → `loading=false`, mensaje error + Reintentar. `finalize` siempre baja skeleton. Prohibido skeleton infinito (FR-UI-024).

**Rationale**: Spec + analyze; Pinot client HTTP timeout 10s — alinear UX.

**Alternatives considered**: Sin timeout — rechazado (hang observado).

## R5 — Performance verification

**Decision**: (1) pytest `test_list_unidades_p95` (marker slow) sobre servicio/repo con flota seed. (2) Humo: DevTools Timing → Waiting (TTFB) en Actualizar &lt;2s warm. (3) SC-007 es criterio de producto (UI); umbral Pinot 100ms es gate técnico interno.

**Rationale**: Constitución III + Validation Metric.

## R6 — Navegación / lastId con paginación

**Decision**: lastId solo resalta si la fila está en `items` de la página actual. Si no, no forzar salto de página automático (spec edge case); el usuario usa filtro por placa.

**Rationale**: Evita magia de navegación; asunciones del spec.

## R7 — SMTP / páginas full (sin cambio)

**Decision**: Mantener R1–R3 de research previo (páginas Detalles/Formulario; gmail required; SMTP + reenviar).

**Rationale**: Ya implementado; este plan es delta listado.
