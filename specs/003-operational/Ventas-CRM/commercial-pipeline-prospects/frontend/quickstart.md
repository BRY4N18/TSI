# Quickstart: Pipeline Comercial — Frontend

## Rutas SPA

| Ruta | Acceso |
|------|--------|
| `/ventas-crm/planes` | Público (RF-CPP-000) |
| `/ventas-crm/registro` | Público (RF-CPP-001) |
| `/ventas-crm/prospectos` | Gerente CRM / Admin |
| `/ventas-crm/prospectos/:id` | Dueño o Admin |
| `/ventas-crm/pipeline` | Dueño o Admin |
| `/ventas-crm/entrada-directa` | Administrador |

## Checks manuales

1. Catálogo público sin login.
2. Gerente solo ve prospectos asignados.
3. Board: 409 muestra refrescar tras conflicto concurrente.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/ventas-crm/**/*.spec.ts
```
