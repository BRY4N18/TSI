# UI Contract: Enriquecimiento en Sitio (CU-O46)

**Capa**: `evidencia-unidad/frontend` | **Date**: 2026-07-30
**API**: paths `/accidentes/{id}/enriquecimiento/*`, `/catalogos/*`

## Layout (paneles)

1. **Clima/período** — selects catálogo; un vínculo activo
2. **Elementos físicos** — multi-select + chips/lista; soft-delete confirmado
3. **Conductor** — form PII + 4 checkboxes estado
4. **Vehículo** — form separado; tipovehiculo requerido
5. **Implicados** — tipo + estado + género/edad opcionales (sin identidad)

## Conductor — checkboxes → catálogo

| UI | Campo catálogo |
|----|----------------|
| Sobrio | `estadosobriedad` |
| Atento | `nivelatencion` |
| Ileso | `condicionfisica` |
| Con seguridad | `usoseguridad` |

## mode=view

- Ocultar formularios y CTAs Guardar/Eliminar
- Listas en solo lectura

## Offline

- Colas locales clima/físico/implicado sin cifrado
- Conductor: AES-GCM obligatorio; error claro si falla
- Sync batch incluye campo `enriquecimiento` multipart
