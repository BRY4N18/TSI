# Data Model (UI): Alta de Unidades — Frontend

**Date**: 2026-07-30  
**Authority**: [`../backend/data-model.md`](../backend/data-model.md) + OpenAPI list delta + [`spec.md`](./spec.md).

## CatalogQueryState (UI)

| Campo | Tipo lógico | Default | Notas |
|-------|-------------|---------|--------|
| q | string | `""` | Texto placa y/o nombre |
| activo | `true` \| `false` \| `null` | `null` (Todas) | |
| tipounidademergencia | enum \| null | `null` | |
| cursor | string/number \| null | `null` | Inicio de página |
| limit | number | **20** | |
| next_cursor | string/number \| null | from API | Pager |

Cambiar `q` / `activo` / `tipounidademergencia` → `cursor = null`.

## UnidadFlotaRow

Campos de lista: `idunidademergencia`, `placa`, `unidademergencia`, `tipounidademergencia`, `activo`, (+ opcionales si ya se muestran). Sin password.

## CatalogPageResult

- `items: UnidadFlotaRow[]` (≤ limit)  
- `pagination: { next_cursor, limit }`  

## InvitacionResultado

`invitacion_enviada`, `invitacion_error?` — sin cambio.

## UnidadDetallePage / UnidadFormularioPage

Sin cambio material vs spec (read vs create/edit; gmail required en create).

## UI states

```text
Lista (query + page) → detalle/:id
Lista → nueva | editar/:id
Form/Detalle → Lista (+ lastId si visible)
Lista → Alert baja/reactivar
Lista → filtros / siguiente página / Actualizar
```
