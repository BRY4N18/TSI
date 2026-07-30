# Quickstart: Seguimiento y Cierre — Frontend

## Apuntar Speckit

```json
"path": "specs/003-operational/Emergencias/seguimiento-cierre-de-casos/frontend"
```

## Rutas SPA

| Ruta | Rol | FR-UI |
|------|-----|-------|
| `/seguimiento/mapa` | Operador | 001–005 |
| `/seguimiento/mi-seguimiento` | Unidad | 006–008 |
| `/seguimiento/historial` | Operador | 012–013 |
| `/seguimiento/expedientes` | Cliente | 014–015 |
| `/seguimiento/expedientes/:id` | Cliente | 014–015 |

## Checks manuales

1. Mapa: SSE conectado; marcadores severidad; ETA actualiza sin refresh manual.
2. Cliente: redirect/403 en `/mapa`.
3. Cierre vs cancelar: formularios distintos.
4. PDF expediente descarga OK.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/seguimiento/**
```
