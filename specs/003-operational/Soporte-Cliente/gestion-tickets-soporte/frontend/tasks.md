# Tasks: Gestión de Tickets de Soporte — Frontend

**Input**: `frontend/spec.md`, `frontend/plan.md`, Depends-on `../backend/`
**Prerequisites**: Backend OpenAPI, US7/US8 completados en `../backend/tasks.md`.

## Phase 0: Stub (Fase A)

- [X] T-FE-000 Crear capa `frontend/` con stub spec/plan/tasks/quickstart (2026-07-30)

## Phase 1: Servicios, guards y rutas (FR-UI-016)

- [X] T-FE-001 Tipos OpenAPI en `services/models/soporte.types.ts` (backend T004)
- [X] T-FE-002 `TicketApiService` + spec (backend T073, T069)
- [X] T-FE-003 `SlaConfigApiService` + spec (backend T074, T070)
- [X] T-FE-004 Guards cliente/agente/admin + specs (backend T075, T071)
- [X] T-FE-005 Rutas lazy `soporte-cliente.routes.ts` + spec (backend T076, T072)

## Phase 2: Páginas por rol (FR-UI-010–015)

- [X] T-FE-006 Página Mis tickets Cliente (backend T077)
- [X] T-FE-007 Esqueleto cola agente (backend T078 — base US8)
- [X] T-FE-008 Detalle ticket deep-link (backend T079)
- [X] T-FE-009 Configuración SLA Administrador (backend T080)
- [X] T-FE-010 Dashboard soporte (backend T081)
- [X] T-FE-011 Entradas nav por rol en `nav-links.ts` (backend T082)

## Phase 3: Cola master-detail (FR-UI-001–009, 017)

- [X] T-FE-012 Rediseño master-detail `cola-agente.page.*` (backend T091)
- [X] T-FE-013 Filtros prioridad/estado + empty state (backend T092)
- [X] T-FE-014 Responsive RNF-TIC-004 (backend T093)
- [X] T-FE-015 `TicketApiService.listar` con query params (backend T090, T089)
- [X] T-FE-016 Jasmine layout/filtros cola (backend T088)

## Phase 4: Catálogo servicios (FR-UI-012)

- [X] T-FE-017 Select `idservicio` opcional en Mis tickets (backend T098)

## Phase 5: Polish

- [X] T-FE-018 Validación build/tsc módulo soporte-cliente (backend T086)
- [X] T-FE-019 Documentar Interaction en `frontend/spec.md` (Fase B 2026-07-30)

**Checkpoint**: FR-UI-001…017 implementados en código Angular (US7+US8 backend tasks).
