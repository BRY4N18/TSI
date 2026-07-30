# Quickstart: Evidencia en Sitio — Frontend

**Capa**: `frontend/` | **API**: `../backend/quickstart.md`

## Apuntar Speckit

```json
"path": "specs/003-operational/Emergencias/evidencia-unidad/frontend"
```

## Rutas SPA

| Ruta | Rol | FR-UI |
|------|-----|-------|
| `/evidencia-unidad/disponibilidad` | Unidad | 001–002 |
| `/evidencia-unidad/flota` | Administrador | 003 |
| `/evidencia-unidad/accidentes/:id/galeria` | Técnico/Unidad/Admin | 004–008 |
| `/evidencia-unidad/accidentes/:id/enriquecimiento` | Técnico/Unidad/Admin | 009–017 |
| `…?mode=view` | Operador (lectura) | 016 |

## Checks manuales

1. Galería offline: capturar sin red → badge Pendiente → reconectar → sync.
2. Enriquecimiento: 4 checkboxes conductor; implicado sin cédula/nombres.
3. Disponibilidad: no ofrecer «En Misión» manual.
4. Operador: desde detalle accidente, enriquecimiento en solo lectura.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/evidencia-unidad/**
```
