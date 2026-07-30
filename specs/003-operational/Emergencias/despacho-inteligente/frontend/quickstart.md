# Quickstart: Despacho Inteligente — Frontend

## Apuntar Speckit

```json
"path": "specs/003-operational/Emergencias/despacho-inteligente/frontend"
```

## Rutas SPA

| Ruta | Rol | FR-UI |
|------|-----|-------|
| `/despacho/monitoreo` | Operador | 001–005 |
| `/despacho/monitoreo/:idaccidente` | Operador | 002–007, 015 |
| `/despacho/asignacion/:idaccidente` | Operador | 010–011 |
| `/despacho/mi-despacho` | Unidad | 008–009 |
| `/despacho/parametros` | Director Tecnológico | 012–013 |

## Checks manuales

1. Monitoreo: historial intentos con motivos rechazo/timeout.
2. Mi despacho: rechazo sin motivo bloqueado en UI.
3. Asignación manual: confirma origen Manual.
4. Parámetros: validación rangos timeout/pesos.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/despacho/**
```
