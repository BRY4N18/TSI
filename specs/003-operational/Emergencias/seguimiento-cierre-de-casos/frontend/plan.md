# Implementation Plan: Seguimiento y Cierre — Frontend

**Capa**: `seguimiento-cierre-de-casos/frontend` | **Date**: 2026-07-30
**Spec**: `frontend/spec.md`
**Depends-on**: `../backend/`

## Summary

Mapa operador SSE, app unidad mi-seguimiento, formularios cierre/cancelación, historial y expedientes Cliente con PDF.

## Technical Context

**Stack**: Angular 17+, EventSource SSE, mapa (Leaflet/similar)
**Design**: `.specify/docs/design/design-system.md`
**Código**: `frontend/src/app/modules/seguimiento/`

## Phases → FR-UI

| Phase | FR-UI | Código (backend/tasks.md US8) |
|---|---|---|
| 1 API + SSE | 004, 016 | `seguimiento-api.service.ts`, `seguimiento-sse.service.ts`, `mi-seguimiento-api.service.ts`, guards (T093–T097) |
| 2 Mapa | 001–005, 011, 017 | `pages/mapa-seguimiento/` (T098) |
| 3 Mi-seguimiento | 006–008 | `pages/mi-seguimiento/` (T099) |
| 4 Historial/expediente | 009–015 | `historial-emergencias/`, `detalle-expediente/`, `expediente-cliente-api.service.ts` (T100–T101) |
| 5 Rutas | 016 | `seguimiento.routes.ts` (T101) |
