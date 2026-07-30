# Quickstart: Notificación de Ventas — Frontend

## Rutas SPA

| Ruta | Acceso |
|------|--------|
| `/ventas-crm/demo` | Público con grant demo |
| `/ventas-crm/notificaciones` | Gerente CRM / Admin |

## Checks manuales

1. Demo: grant inválido → error claro; grant válido → token en interceptor.
2. Notificaciones gerente: solo filas con su `idusuariogerentenotificado`.
3. Lista vacía muestra estado accionable (no pantalla en blanco).

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/demo*.spec.ts --include=**/notificacion*.spec.ts
```
