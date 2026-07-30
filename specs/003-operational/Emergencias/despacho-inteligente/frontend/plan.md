# Implementation Plan: Despacho Inteligente — Frontend

**Capa**: `despacho-inteligente/frontend` | **Date**: 2026-07-30
**Spec**: `frontend/spec.md`
**Depends-on**: `../backend/`

## Summary

Monitoreo operador con SSE, respuesta unidad mi-despacho, asignación manual/múltiple, configuración parámetros algoritmo.

## Technical Context

**Código**: `frontend/src/app/modules/despacho/`
**Design**: `.specify/docs/design/design-system.md`

## Phases → FR-UI

| Phase | FR-UI | Código (backend/tasks.md US6) |
|---|---|---|
| 1 Servicios/guards | 005, 014 | `despacho-api.service.ts`, `mi-despacho-api.service.ts`, `despacho-sse.service.ts`, `despacho-parametros-api.service.ts`, guards (T087–T092) |
| 2 Monitoreo | 001–007, 015 | `pages/monitoreo-despacho/` (T093–T094) |
| 3 Mi despacho | 008–009 | `pages/mi-despacho/` (T095) |
| 4 Asignación manual | 010–011 | `pages/asignacion-manual/` (T094) |
| 5 Parámetros | 012–013 | `pages/parametros-algoritmo/` (T096–T097) |
