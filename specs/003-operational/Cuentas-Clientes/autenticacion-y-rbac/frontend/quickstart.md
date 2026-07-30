# Quickstart: Autenticación y RBAC — Frontend

**Capa**: `frontend/` | **API**: ver `../backend/quickstart.md`.

## Rutas SPA

| Ruta | Acceso |
|------|--------|
| `/cuentas-clientes/auth/login` | Público |
| `/cuentas-clientes/auth/password-reset` | Público |
| Rutas bajo `AppShellComponent` | `SessionGuard` + `RoleGuard` según módulo |

## Checks manuales

1. Login Operador → redirect `/accidentes/lista` (post-login-home).
2. Login con credencial «Cambio contraseña» → pantalla cambio antes del home.
3. Logout → siguiente navegación protegida vuelve a login.
4. Usuario sin rol Administrador no accede a rutas `data.roles: ['Administrador']`.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/auth/**/*.spec.ts --include=**/auth.interceptor.spec.ts --include=**/post-login-home.spec.ts
```
