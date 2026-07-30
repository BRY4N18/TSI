# Implementation Plan: Autenticación y RBAC — Frontend

**Capa**: `autenticacion-y-rbac/frontend` | **Date**: 2026-07-30
**Spec**: `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/frontend/spec.md`
**Depends-on**: `../backend/` (OpenAPI + RF/CA)

## Summary

Capa transversal Angular: login/logout, interceptor JWT, guards de sesión y rol, recuperación/cambio de contraseña y routing post-login por rol. Sin endpoints nuevos.

## Technical Context

**Stack**: TypeScript / Angular 17+, Tailwind, Jasmine/Karma
**Design**: `.specify/docs/design/design-system.md`
**Código**: `frontend/src/app/modules/cuentas-clientes/auth/`, `frontend/src/app/core/interceptors/auth.interceptor.ts`, `post-login-home.ts`

## Project Structure (docs)

```text
specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/
├── autenticacion-y-rbac.md
├── backend/
└── frontend/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    └── quickstart.md
```

## Constitution Check

| Característica | Estado |
|---|---|
| Interaction Capability | PASS — núcleo |
| Functional Suitability | PASS — depende backend |
| Security | PASS — guards + interceptor |
| Maintainability | PASS — capa FE separada |

## Phases

1. Infra transversal (FR-UI-003…005, 009) — interceptor + guards
2. Login/logout + post-login (FR-UI-001, 002, 008) — hecho en backend tasks T015–T033
3. Password reset / cambio obligatorio (FR-UI-006, 007) — T063–T064
4. Servicios admin RBAC (FR-UI-010) — T047, T055
5. Polish: Jasmine + mensajes error (FR-UI-011)
