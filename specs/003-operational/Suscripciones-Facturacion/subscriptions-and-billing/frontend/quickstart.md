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
| `/suscripciones/planes/:idplan` | DirectorEstrategia (Detalles RO) |
| `/suscripciones/planes/:idplan/editar` | DirectorEstrategia |
| `/suscripciones/aprobaciones-downgrade` | Administrador |

## Checks manuales

1. Login DirectorEstrategia → redirect catálogo planes.
2. Proveedor alta suscripción + método → factura generada si backend aplica.
3. Admin no accede a formulario crear plan.

### Humo delta UX catálogo (V-PLAN)

| ID | Check |
|----|--------|
| V-PLAN-1 | Ojo → `/planes/:idplan` Detalles; **sin** Guardar; campos RO |
| V-PLAN-2 | Lápiz → `/planes/:idplan/editar`; nombre en lista no es el único enlace |
| V-PLAN-3 | «Crear plan» en header del catálogo |
| V-PLAN-4 | En form, Guardar/Publicar visible en **cabecera** (viewport ≥1280px sin scroll al pie) |
| V-PLAN-5 | Desactivar requiere confirmación; Admin denegado en `planes/nuevo` |
| V-PLAN-6 | Con &gt;20 planes filtrados, la tabla muestra **≤20** filas; «Siguiente» pide otra página |
| V-PLAN-7 | Cambiar texto/estado/nivel reinicia a la primera página; conjunto visible refleja el filtro |
| V-PLAN-8 | «Actualizar» reaplica filtros+página; en warm, filas/vacío/error en &lt;2 s (SC-008) |

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/suscripciones/**/*.spec.ts
```
