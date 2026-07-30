# Quickstart: Incorporación de Clientes — Frontend

## Rutas SPA

| Ruta | Rol |
|------|-----|
| `/cuentas-clientes/incorporacion-clientes/autorregistro` | Público (O14) |
| `/cuentas-clientes/incorporacion-clientes/solicitudes` | Administrador (O16) |
| `/cuentas-clientes/incorporacion-clientes/:id/onboarding` | Admin local, cuenta Activo (O02) |

## Checks manuales

1. Autorregistro → estado Pendiente_Aprobación; login permitido pero wizard bloqueado.
2. Admin aprueba → admin local ve wizard con etapa cambio_password.
3. Completar tres etapas → onboarding Completado; guard redirige fuera del wizard.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/incorporacion-clientes/**/*.spec.ts
```
