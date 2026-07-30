# Quickstart: Gestión de Cuentas — Frontend

## Rutas SPA

| Ruta | Rol |
|------|-----|
| `/cuentas-clientes/gestion-cuenta` | Administrador (hub) |
| `/cuentas-clientes/gestion-cuenta/:id/perfil` | Cliente / Admin scope |
| `/cuentas-clientes/gestion-cuenta/:id/preferencias` | Cliente / Admin scope |
| `/cuentas-clientes/gestion-cuenta/:id/transferencia` | Admin local |
| `/cuentas-clientes/gestion-cuenta/:id/baja` | Administrador |

## Checks manuales

1. Perfil: NIT y tipo no editables.
2. Transferencia: confirmación → nuevo admin local inmediato.
3. Baja: cuenta no operable tras confirmación.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/gestion-cuenta/**/*.spec.ts
```
