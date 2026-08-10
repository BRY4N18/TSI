# Implementation Plan: Evidencia en Sitio — Frontend

**Capa**: `evidencia-unidad/frontend` | **Date**: 2026-07-30
**Spec**: `frontend/spec.md`
**Depends-on**: `../backend/` (OpenAPI evidencia + enriquecimiento)

## Summary

Módulo Angular campo: disponibilidad unidad, galería con captura modal offline-first, enriquecimiento multi-panel CU-O75/CU-O76, integración `mode=view` con registro-accidente.

## Technical Context

**Stack**: TypeScript / Angular 17+, IndexedDB, Web Crypto (PII offline)
**Design**: `.specify/docs/design/design-system.md` (RNF-EVI-010)
**Código**: `frontend/src/app/modules/evidencia-unidad/`

## Project Structure (docs)

```text
evidencia-unidad/
├── evidencia-unidad.md
├── backend/
└── frontend/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── quickstart.md
    └── contracts/
        ├── galeria-evidencia.ui-contract.md
        └── enriquecimiento-campo.ui-contract.md
```

## Constitution Check

| Característica | Estado |
|---|---|
| Interaction Capability | PASS — offline + enriquecimiento |
| Functional Suitability | PASS — Depends-on backend |
| Security | PASS — PII cifrado local |
| Maintainability | PASS — capa FE separada |

## Phases → FR-UI

| Phase | FR-UI | Código (backend/tasks.md) |
|---|---|---|
| 1 Disponibilidad | 001–003 | `panel-disponibilidad.page.*`, `disponibilidad-unidad-api.service.ts` (T034–T038) |
| 2 Galería + captura | 004–008 | `galeria-evidencias.page.*`, modals, offline store/sync (T050–T068) |
| 3 Rutas/guards/nav | 018–019 | `evidencia-unidad.routes.ts`, guards, `nav-links.ts` (T071–T072b) |
| 4 Enriquecimiento | 009–017 | `enriquecimiento-accidente.page.*`, `enriquecimiento-api.service.ts` (T111–T127) |
| 5 Implicados ontología | 013 | remediación T144–T147 |
