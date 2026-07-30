# Quickstart: Suscripciones — Frontend

## Rutas SPA (bajo `/suscripciones`)

| Ruta | Rol |
|------|-----|
| `/suscripciones/mi-suscripcion` | Proveedor |
| `/suscripciones/metodos-pago` | Proveedor |
| `/suscripciones/historial-facturas` | Proveedor |
| `/suscripciones/cambio-plan` | Proveedor |
| `/suscripciones/catalogo-planes` | DirectorEstrategia (gestión) |
| `/suscripciones/planes/nuevo` | DirectorEstrategia |
| `/suscripciones/aprobaciones-downgrade` | Administrador |

## Checks manuales

1. Login DirectorEstrategia → redirect catálogo planes.
2. Proveedor alta suscripción + método → factura generada si backend aplica.
3. Admin no accede a formulario crear plan.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/suscripciones/**/*.spec.ts
```
