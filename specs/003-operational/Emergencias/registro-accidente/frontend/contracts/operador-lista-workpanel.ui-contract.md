# UI Contract: Operador — Lista y Workpanel

**Capa**: `registro-accidente/frontend`  
**Date**: 2026-07-30  
**API**: sin endpoints nuevos — `../backend/contracts/registro-accidente.openapi.yaml`

## Navegación

| Origen | Destino |
|--------|---------|
| Ojo | `/accidentes/{id}` |
| Lápiz | `/accidentes/{id}?focus=edit` |
| Detalles → galería | `/evidencia-unidad/accidentes/{id}/galeria?mode=view` |
| Detalles → siniestro | `/evidencia-unidad/accidentes/{id}/enriquecimiento?mode=view` |
| Editar → Completar en sitio | `/evidencia-unidad/accidentes/{id}/enriquecimiento` (sin `mode=view`) |
| Nuevo registro | `/accidentes/registro` |

## Lista

- ID: texto (`text-text-primary`), no `<a>`
- Acciones ≥44×44; `aria-label` Ver detalles / Editar caso
- `lastId` en sessionStorage (`tsi.accidentes.lista.lastId`)

## Workpanel

- `focus≠edit`: título Detalles; sin Guardar; inputs Impacto disabled
- `focus=edit`: título Editar caso; Guardar arriba (`btn-save-header`)

## Registro — borrador

- Key: `tsi.registro-accidente.draft`
- Banner `draft-restored` + CTA Descartar borrador
- Confirmación: `¿Descartar el borrador y empezar de nuevo?`
