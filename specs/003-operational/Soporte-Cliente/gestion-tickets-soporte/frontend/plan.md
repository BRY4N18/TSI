# Implementation Plan: Gestión de Tickets de Soporte — Frontend

**Capa**: `gestion-tickets-soporte/frontend` | **Date**: 2026-07-30
**Spec**: `frontend/spec.md`
**Depends-on**: `../backend/` (OpenAPI + RF-TIC-008 / RNF-TIC-004)

## Summary

UI Angular 17+ para Cliente (Mis tickets), Agente (Cola de soporte master-detail), Administrador (SLA + dashboard). Servicios tipados contra OpenAPI; guards RBAC; sin endpoints nuevos.

## Technical Context

**Stack**: TypeScript / Angular 17+, Tailwind, design tokens
**Design**: `.specify/docs/design/design-system.md`
**Código**: `frontend/src/app/modules/soporte-cliente/`

## Project Structure (docs)

```text
gestion-tickets-soporte/
├── gestion-tickets-soporte.md
├── backend/
└── frontend/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── quickstart.md
    └── contracts/
        └── cola-master-detail.ui-contract.md
```

## Constitution Check

| Característica | Estado |
|---|---|
| Interaction Capability | PASS — cola master-detail (Fase B) |
| Functional Suitability | PASS — Depends-on backend |
| Security | PASS — guards + RN-TIC-002 UI |
| Maintainability | PASS — capa FE separada |

## Phases → FR-UI

| Phase | FR-UI | Código Angular (refs backend/tasks.md) |
|---|---|---|
| 1 Servicios/guards/rutas | 016 | `services/ticket-api.service.ts`, `sla-config-api.service.ts`, `guards/*`, `soporte-cliente.routes.ts` (T073–T076) |
| 2 Páginas base | 012–013, 014–015 | `pages/mis-tickets/`, `detalle-ticket/`, `configuracion-sla/`, `dashboard-soporte/` (T077–T081) |
| 3 Cola master-detail | 001–011, 017 | `pages/cola-agente/cola-agente.page.*` (T088–T094) |
| 4 Catálogo servicios | 012 | select en `mis-tickets` (T098) |
| 5 Nav + polish | 001 | `shared/layout/nav-links.ts` (T082, T093) |
