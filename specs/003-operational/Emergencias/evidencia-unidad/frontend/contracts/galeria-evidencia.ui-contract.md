# UI Contract: Galería de Evidencias

**Capa**: `evidencia-unidad/frontend` | **Date**: 2026-07-30
**API**: `../backend/contracts/evidencia-unidad.openapi.yaml`

## Navegación

| Origen | Destino |
|--------|---------|
| Detalle accidente | `/evidencia-unidad/accidentes/{id}/galeria` |
| Operador consulta | `…/galeria?mode=view` |
| Captura | Modal desde galería (no ruta separada) |

## Galería

- Orden: `fechahora` descendente
- Badge: **Sincronizado** (servidor) vs **Pendiente** (solo local capturador)
- Filtro notas por `tipo`
- Visor foto en modal

## Captura modal

- Foto: input cámara/archivo; compresión ≤10 MB — RNF-EVI-002
- Nota: texto + tipo catálogo
- Offline: persiste IndexedDB `sincronizado=false`; no visible otros usuarios

## Sync

- Scheduler reconexión → `POST …/evidencias/sincronizar`
- UI contador pendientes; no bloquear exitosos por fallo parcial
