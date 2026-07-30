# Quickstart: Incorporación Regional — Frontend

## Rutas SPA

| Ruta | Rol |
|------|-----|
| `/red-operativa/incorporacion-regional/catalogo` | Administrador / DirectorTecnologico |
| `/red-operativa/incorporacion-regional/validacion` | Administrador / DirectorTecnologico |
| `/red-operativa/incorporacion-regional/reevaluacion/:id` | DirectorTecnologico |

## Checks manuales

1. Validación Aprobada → badge Producción en catálogo.
2. Rechazo con motivo → región permanece En_Validación.
3. Despublicar con casos activos → confirmación menciona continuidad operativa.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/incorporacion-regional/**/*.spec.ts
```
