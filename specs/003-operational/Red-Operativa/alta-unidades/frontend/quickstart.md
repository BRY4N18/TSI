# Quickstart: Alta de Unidades — Frontend

## Rutas SPA

| Ruta | Rol |
|------|-----|
| `/red-operativa/alta-unidades/catalogo` | Proveedor |
| `/red-operativa/alta-unidades/editar/:id` | Proveedor dueño |
| `/red-operativa/alta-unidades/baja/:id` | Proveedor dueño |

## Checks manuales

1. Login Proveedor → post-login home catálogo flota.
2. Lote: fila inválida → insertadas=0 con detalle.
3. Editar unidad ajena → 403.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/alta-unidades/**/*.spec.ts
```
