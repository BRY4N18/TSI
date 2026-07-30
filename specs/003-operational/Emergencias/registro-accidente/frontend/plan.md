# Implementation Plan: Registro de Accidentes — Frontend

**Capa**: `registro-accidente/frontend` | **Date**: 2026-07-30  
**Spec**: `specs/003-operational/Emergencias/registro-accidente/frontend/spec.md`  
**Depends-on**: `../backend/` (OpenAPI + RF/CA)

## Summary

UI Angular 17+ del Operador para lista/workpanel (Detalles vs Editar), registro con borrador local (RNF-REG-006 UI) y navegación a galería/enriquecimiento en `mode=view`. Sin endpoints nuevos.

## Technical Context

**Stack**: TypeScript / Angular 17+, Tailwind, Tabler icons, Jasmine/Karma  
**Design**: `.specify/docs/design/design-system.md`  
**Código**: `frontend/src/app/modules/accidentes/`, `evidencia-unidad/pages/{galeria,enriquecimiento}`

## Project Structure (docs)

```text
specs/003-operational/Emergencias/registro-accidente/
├── registro-accidente.md
├── backend/          # dominio + OpenAPI
└── frontend/         # esta capa
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    ├── quickstart.md
    └── contracts/
        └── operador-lista-workpanel.ui-contract.md
```

## Constitution Check

| Característica | Estado |
|---|---|
| Interaction Capability | PASS — núcleo |
| Functional Suitability | PASS — depende de backend |
| Security | PASS — guards existentes |
| Maintainability | PASS — capa FE separada |
| Resto | N/A o heredado |

## Phases

1. Lista/workpanel modos (FR-UI-001…004, 007–008) — hecho Phase 12 backend-tasks históricas / código actual  
2. Paneles `mode=view` (FR-UI-005/006) — hecho Phase 13  
3. Descartar borrador UI (FR-UI-009) — hecho Phase 13  
4. Polish: Jasmine + Docker rebuild
