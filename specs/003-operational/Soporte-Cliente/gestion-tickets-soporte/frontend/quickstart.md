# Quickstart: Gestión de Tickets de Soporte — Frontend

**Capa**: `frontend/` | **API**: ver `../backend/quickstart.md` y OpenAPI.

## Apuntar Speckit

En `.specify/feature.json`:

```json
"path": "specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/frontend"
```

Luego: `/speckit-plan` → `/speckit-tasks` → `/speckit-implement` sobre esta capa (no redefine RF del backend).

## Rutas SPA

| Ruta | Rol | FR-UI |
|------|-----|-------|
| `/soporte-cliente/mis-tickets` | Cliente | 010–013 |
| `/soporte-cliente/cola` | Agente | 001–009, 017 |
| `/soporte-cliente/tickets/:id` | Cliente / Agente | 010–011 |
| `/soporte-cliente/configuracion-sla` | Administrador | 014 |
| `/soporte-cliente/dashboard` | Supervisor/Admin | 015 |

## Checks manuales

1. Cola ≥1024px: lista + detalle visibles; filtros recargan lista.
2. Cero tickets: «No hay tickets pendientes.» — sin CTA reembolso ni nuevo ticket.
3. Cliente: historial sin notas internas; agente: toggle nota interna visible.
4. Mis tickets: registro con select servicio opcional.

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/soporte-cliente/**
```
