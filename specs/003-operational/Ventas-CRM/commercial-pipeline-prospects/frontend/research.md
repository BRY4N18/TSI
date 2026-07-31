# Research: Pipeline Comercial — Frontend (delta workpanel)

**Date**: 2026-07-30  
**Spec**: [`spec.md`](./spec.md) (clarifications workpanel CRUD)

## R1 — Layout workpanel

**Decision**: Lista + **página dedicada** workpanel modo Ver (patrón Accidentes). Sin modal. Split-view lista+panel **no** obligatorio en este delta.

**Rationale**: Clarificación Q1; reduce rework vs inventar split; alinea piloto terminado.

**Alternatives considered**: Split ~640–720px (design-system literal) — diferido. Páginas detalle/form separadas con lápiz (Planes) — no aplica sin PATCH.

## R2 — Sin lápiz / sin Guardar de ficha

**Decision**: Solo ícono `eye` en listado y board. Workpanel título «Detalles»; campos disabled; **sin** botón Guardar de ficha. Acciones de dominio (pipeline, Perdido, conversión, asignación) según rol/estado.

**Rationale**: OpenAPI Depends-on no expone PATCH de contacto; clarificación Q2. Inventar edición violaría capa FE.

**Alternatives considered**: Lápiz → «modo operar» — rechazado (rompe semántica design-system). Ampliar BE con PATCH — fuera de alcance FE.

## R3 — CTA crear en listado

**Decision**: Solo **Administrador** ve CTA header «Entrada directa» → `/ventas-crm/entrada-directa`. Gerente: sin CTA de alta en listado. Registro inbound sigue en `/ventas-crm/registro` (público).

**Rationale**: Clarificación Q3; RF-CPP-007.

**Alternatives considered**: Gerente → link a registro público — rechazado (ruido en CRM autenticado).

## R4 — Pipeline board

**Decision**: Columnas por etapa; botones avance adyacente + Perdido (modal motivo); ícono ojo → workpanel; **sin** drag-and-drop.

**Rationale**: Clarificación Q4; mutaciones usan mismos endpoints que workpanel; DnD añade coste sin valor MVP.

**Alternatives considered**: Drag adyacente — diferido. Board solo RO — rechazado (FR-UI-006 pide operar desde board).

## R5 — Filtros y paginación listado

**Decision**: Query `activo`, `etapa_actual`, `cursor`, `limit` (default **20**). Cambiar filtro → `cursor=null` / stack reset. `ProspectoApiService.listar` ya tipa params; asegurar `HttpParams` explícitos (no dump objeto crudo si Angular omite `false`).

**Rationale**: Clarificación Q5; OpenAPI listarProspectos; piloto planes/unidades.

**Alternatives considered**: Sin filtros UI — rechazado. Filtrar en cliente tras traer todo — rechazado.

## R6 — HTTP 409

**Decision**: En transición/asignación/conversión: toast con detalle + CTA/acción **Refrescar** que re-GET detalle o listado/board.

**Rationale**: Spec FR-UI-008; clarificación UI previa.

**Alternatives considered**: Ignorar 409 — rechazado.

## R7 — Credenciales demo (validación manual)

**Decision**: Documentar en quickstart:

| Rol | Email | Password | Notas |
|-----|-------|----------|-------|
| Administrador | `carlos.mendoza.admin@demo.tsi.com` | `password123` | Tras `seed_demo_usuarios_roles.py` |
| GerenteVentas | *no hay seed demo dedicado aún* | — | Solo fixture tests `gerente.ventas@tsi.com` / `password123` en pytest; para humo Gerente hace falta seed o usar Admin |

Rutas públicas (sin login): `/ventas-crm/planes`, `/ventas-crm/registro`.

**Rationale**: Scripts existentes; evitar inventar usuario Gerente no sembrado en Pinot runtime.

**Alternatives considered**: Asumir `gerente.ventas@tsi.com` en Docker — rechazado (solo conftest).
