# Tasks: Autenticación y RBAC — Frontend

**Input**: `frontend/spec.md`, `frontend/plan.md`, Depends-on `../backend/`
**Prerequisites**: Backend OpenAPI y CA-AUT-* disponibles.

## Phase 1: Infra transversal (FR-UI-003…005, 009)

- [X] T-FE-001 `AuthInterceptor` en `frontend/src/app/core/interceptors/auth.interceptor.ts`
- [X] T-FE-002 Jasmine interceptor spec
- [X] T-FE-003 `SessionGuard` + spec en `auth/guards/session.guard.ts`
- [X] T-FE-004 `RoleGuard` + spec en `auth/guards/role.guard.ts`
- [X] T-FE-005 `AuthApiService` + tipos OpenAPI en `auth/services/`

## Phase 2: Login y post-login (FR-UI-001, 002, 008)

- [X] T-FE-006 Pantalla `login.page.ts` con logout
- [X] T-FE-007 `post-login-home.ts` + spec — home por rol
- [X] T-FE-008 Jasmine login.page.spec.ts

## Phase 3: Recuperación y cambio obligatorio (FR-UI-006, 007)

- [X] T-FE-009 `password-reset.page.ts` + `password-reset.service.ts`
- [X] T-FE-010 Jasmine password-reset specs
- [X] T-FE-011 Redirect cambio obligatorio post-login (FR-UI-006)

## Phase 4: Servicios admin (FR-UI-010)

- [X] T-FE-012 `user-role-admin.service.ts` + spec
- [X] T-FE-013 `server-access-admin.service.ts` + spec

## Phase 5: Polish (FR-UI-011)

- [X] T-FE-014 Mensajes error alineados envelope API en login/reset

**Checkpoint**: FR-UI-001…011 cubiertos en código (Fase B 2026-07-30).
