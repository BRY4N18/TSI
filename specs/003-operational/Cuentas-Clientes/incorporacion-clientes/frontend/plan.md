# Implementation Plan: Incorporación de Clientes — Frontend

**Capa**: `incorporacion-clientes/frontend` | **Date**: 2026-07-30
**Depends-on**: `../backend/`

## Summary

UI de alta B2B: autorregistro público, bandeja Admin O16 y wizard onboarding O02/O09 con guards de elegibilidad.

## Technical Context

**Código**: `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/`
**Rutas públicas**: `autorregistro` en `app.routes.ts`

## Phases

1. Autorregistro público (FR-UI-001) — US6 backend tasks
2. Aprobación solicitudes (FR-UI-002, 003, 008) — US5
3. Wizard + guards (FR-UI-004…007, 009, 010) — US3
4. Polish: sin rutas O01/O12 (FR-UI-011)
