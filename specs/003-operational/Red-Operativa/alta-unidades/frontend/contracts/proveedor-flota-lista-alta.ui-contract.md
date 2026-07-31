# UI Contract: Proveedor — Lista paginada + Detalle + Formulario

**Capa**: `alta-unidades/frontend`  
**Date**: 2026-07-30  
**API**: [`../../backend/contracts/alta-unidades.openapi.yaml`](../../backend/contracts/alta-unidades.openapi.yaml) — **delta list**: `cursor`, `limit`, `q`, `activo`, `tipounidademergencia`, `meta.pagination`  
**Layout**: **sin workpanel**

## Navegación

| Origen | Destino |
|--------|---------|
| Catálogo | `…/catalogo` |
| Ojo | `…/detalle/:idunidademergencia` |
| Lápiz | `…/editar/:idunidademergencia` |
| Nueva unidad | `…/nueva` |
| Volver | `…/catalogo` + lastId (si fila visible) |
| Papelera | Alert 2 pasos en lista |
| Reenviar | API reenviar |

## Lista (FR-UI-022…025)

- ID/placa texto plano; acciones ≥44×44; CTA Nueva; lastId si visible.
- **Paginación**: `limit=20`; controles Anterior/Siguiente (o “Más”) según `next_cursor`.
- **Filtros**: texto `q`, estado Activa/Baja/Todas, tipo de unidad → reset cursor.
- Loading / empty / error+Reintentar; timeout ~10s; **no** skeleton infinito.
- Actualizar reenvía los mismos query params.

## Página Detalles

Título «Detalles»; campos disabled; sin Guardar; Volver; opcional «Editar» → formulario.

## Página Formulario

| Modo | Ruta | Título | Header |
|------|------|--------|--------|
| create | `/nueva` | Nueva unidad | Guardar; gmail required |
| edit | `/editar/:id` | Editar unidad | Guardar cambios |

Mismo componente; Cancelar → catálogo.

## Backend delta (list + previo)

| Área | Contrato |
|------|----------|
| List | `GET /unidades?cursor&limit&q&activo&tipounidademergencia` → `items` + `meta.pagination` |
| Create | gmail required; `invitacion_enviada` / `invitacion_error`; never password |
| Reenviar | `POST …/invitacion/reenviar` |
| Ownership | `idcliente` JWT / Pinot correcto |

## Humo

1. Ojo → Detalles sin Guardar.  
2. Nueva → `/nueva`.  
3. Lápiz → `/editar/:id` mismo form.  
4. Alta → unidad en flota propia.  
5. SMTP OK/fail + reenviar.  
6. Filtros + página siguiente (≤20 filas).  
7. Actualizar: Timing Waiting &lt;2s (warm) o error+Reintentar si timeout.
