# Quickstart: Registro Accidente — Frontend

**Capa**: `frontend/` | **API**: ver `../backend/quickstart.md` y OpenAPI.

## Rutas SPA

| Ruta | Modo |
|------|------|
| `/accidentes/lista` | Acciones ojo / lápiz |
| `/accidentes/:id` | Detalles (default) |
| `/accidentes/:id?focus=edit` | Editar |
| `/evidencia-unidad/accidentes/:id/galeria?mode=view` | Galería solo lectura |
| `/evidencia-unidad/accidentes/:id/enriquecimiento?mode=view` | Datos siniestro solo lectura |
| `/accidentes/registro` | Formulario + borrador local |

## Checks manuales

1. Lista: ID no es link; ojo vs lápiz cambian título/Guardar.
2. Desde Detalles: «Ver datos del siniestro» sin formularios de escritura.
3. Registro con borrador: Descartar borrador → confirmación → form vacío.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/lista-accidentes.page.spec.ts --include=**/detalle-accidente.page.spec.ts --include=**/registro-accidente.page.spec.ts
```
