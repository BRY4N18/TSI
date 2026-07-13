# Tasks: Autenticacion y RBAC

**Input**: Design documents from `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/auth-rbac.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explicito; cada tarea de servicio/repositorio tiene test asociado siguiendo `.specify/docs/architecture/testing.md` con markers `unit/repository/service/api` y patron AAA.

**Organization**: Tareas agrupadas por historia de usuario para implementacion y validacion independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`, `US2`, `US3`, `US4`)
- Cada descripcion incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializacion y alineacion de artefactos con constitution/patrones.

- [X] T001 Crear estructura de carpetas backend/frontend para auth-rbac en `backend/apps/cuentas_clientes/{views,services,tests}` y `backend/core/repositories/cuentas_clientes/` y `frontend/src/app/modules/cuentas-clientes/auth/{pages,services,guards}`
- [X] T002 [P] Crear paquete de tests con markers en `backend/pytest.ini` (unit, repository, service, api) alineado a `.specify/docs/architecture/testing.md`
- [X] T003 [P] Crear fixtures base de auth en `backend/conftest.py` (`mock_kafka`, `api_client`, `auth_headers`)
- [X] T004 [P] Generar cliente tipado del contrato en `frontend/src/app/modules/cuentas-clientes/auth/services/auth-api.types.ts` desde `contracts/auth-rbac.openapi.yaml`
- [X] T005 Crear matriz de trazabilidad OE/OT/OP/CU->RF/RNF/CA en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura bloqueante para todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T006 Validar contrato OpenAPI como gate inicial en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/contracts/auth-rbac.openapi.yaml`
- [X] T007 Implementar adaptador Kafka de escritura para auth-rbac en `backend/core/repositories/cuentas_clientes/kafka_writer.py`
- [X] T008 [P] Crear test de repositorio (marker: repository, AAA) para `kafka_writer.py` en `backend/apps/cuentas_clientes/tests/repositories/test_kafka_writer.py`
- [X] T009 Implementar repositorio de sesion base en `backend/core/repositories/cuentas_clientes/session_repository.py`
- [X] T010 [P] Crear test de repositorio (marker: repository, AAA) para `session_repository.py` en `backend/apps/cuentas_clientes/tests/repositories/test_session_repository.py`
- [X] T011 Implementar servicio de validacion JWT+sesion por request en `backend/apps/cuentas_clientes/services/session_validation_service.py`
- [X] T012 [P] Crear test de servicio (marker: service, AAA) para `session_validation_service.py` en `backend/apps/cuentas_clientes/tests/services/test_session_validation_service.py`
- [X] T013 Implementar auditoria base de seguridad (login/logout/revoke/reset) en `backend/apps/cuentas_clientes/services/audit_service.py`
- [X] T014 [P] Crear test de servicio (marker: service, AAA) para `audit_service.py` en `backend/apps/cuentas_clientes/tests/services/test_audit_service.py`
- [X] T015 Implementar interceptor frontend para Bearer token en `frontend/src/app/core/interceptors/auth.interceptor.ts`
- [X] T016 [P] Crear test unitario (marker: unit, AAA) para `auth.interceptor.ts` en `frontend/src/app/core/interceptors/auth.interceptor.spec.ts`
- [X] T017 Implementar respuesta de error uniforme API (`error/detail/code`) en `backend/apps/cuentas_clientes/views/error_response.py`
- [X] T018 Registrar decision log para RNF-AUT-005 diferido en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/decision-log.md`

**Checkpoint**: Base contract-first, seguridad transversal y trazabilidad listas.

---

## Phase 3: User Story 1 - Iniciar/Cerrar/Revocar sesion (Priority: P1)

**Goal**: Entregar flujo completo de login, logout y revoke-session con validacion de sesion por request.

**Independent Test**: Usuario valida login exitoso y logout/revocacion invalidan acceso en siguiente request protegida.

**Measurable Criteria**: Cumplir CA-AUT-001, CA-AUT-008, CA-AUT-009.

### Tests for User Story 1

- [X] T019 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/auth/login` en `backend/apps/cuentas_clientes/tests/api/test_auth_login_contract.py`
- [X] T020 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/auth/logout` en `backend/apps/cuentas_clientes/tests/api/test_auth_logout_contract.py`
- [X] T021 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/auth/revoke-session` en `backend/apps/cuentas_clientes/tests/api/test_auth_revoke_contract.py`
- [X] T022 [P] [US1] Crear test de servicio (marker: service, AAA) para autenticacion login en `backend/apps/cuentas_clientes/tests/services/test_auth_service.py`
- [X] T023 [P] [US1] Crear test de servicio (marker: service, AAA) para logout dedicado (RF-AUT-008) en `backend/apps/cuentas_clientes/tests/services/test_logout_service.py`
- [X] T024 [P] [US1] Crear test de servicio (marker: service, AAA) para revocacion de sesion en `backend/apps/cuentas_clientes/tests/services/test_revoke_session_service.py`
- [X] T025 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `SessionGuard` en `frontend/src/app/modules/cuentas-clientes/auth/guards/session.guard.spec.ts`

### Implementation for User Story 1

- [X] T026 [US1] Implementar servicio de autenticacion login en `backend/apps/cuentas_clientes/services/auth_service.py`
- [X] T027 [US1] Implementar servicio de logout en `backend/apps/cuentas_clientes/services/logout_service.py`
- [X] T028 [US1] Implementar servicio de revocacion en `backend/apps/cuentas_clientes/services/revoke_session_service.py`
- [X] T029 [US1] Implementar vistas DRF de `login/logout/revoke-session` en `backend/apps/cuentas_clientes/views/auth_views.py`
- [X] T030 [US1] Registrar rutas API v1 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T031 [US1] Implementar `AuthApiService` en `frontend/src/app/modules/cuentas-clientes/auth/services/auth-api.service.ts`
- [X] T032 [US1] Implementar `SessionGuard` en `frontend/src/app/modules/cuentas-clientes/auth/guards/session.guard.ts`
- [X] T033 [US1] Implementar pantalla de login con flujo de logout en `frontend/src/app/modules/cuentas-clientes/auth/pages/login.page.ts`

**Checkpoint**: US1 operativa y demostrable como MVP.

**US1 Gate (must pass before next story)**:
- [X] T069 [US1] Validar cumplimiento de `CA-AUT-001`, `CA-AUT-008` y `CA-AUT-009` en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`

---

## Phase 4: User Story 2 - Gestion de usuarios y roles de negocio (Priority: P1)

**Goal**: Permitir al Administrador crear/editar/desactivar usuarios y asignar roles de negocio.

**Independent Test**: Admin gestiona usuario/rol; usuario desactivado no autentica; rol determina autorizacion.

**Measurable Criteria**: Cumplir CA-AUT-004, CA-AUT-005 y regla RN-AUT-001.

### Tests for User Story 2

- [X] T034 [P] [US2] Crear test de contrato API (marker: api, AAA) para gestion de usuarios en `backend/apps/cuentas_clientes/tests/api/test_users_contract.py`
- [X] T035 [P] [US2] Crear test de contrato API (marker: api, AAA) para gestion de roles negocio en `backend/apps/cuentas_clientes/tests/api/test_roles_contract.py`
- [X] T036 [P] [US2] Crear test de repositorio (marker: repository, AAA) para `Dim_Usuarios` en `backend/apps/cuentas_clientes/tests/repositories/test_user_repository.py`
- [X] T037 [P] [US2] Crear test de repositorio (marker: repository, AAA) para `Dim_Rol/Dim_Usuario_Rol` en `backend/apps/cuentas_clientes/tests/repositories/test_role_repository.py`
- [X] T038 [P] [US2] Crear test de servicio (marker: service, AAA) para gestion de usuarios en `backend/apps/cuentas_clientes/tests/services/test_user_management_service.py`
- [X] T039 [P] [US2] Crear test de servicio (marker: service, AAA) para RBAC de negocio en `backend/apps/cuentas_clientes/tests/services/test_business_rbac_service.py`
- [X] T040 [P] [US2] Crear test unitario frontend (marker: unit, AAA) para `RoleGuard` en `frontend/src/app/modules/cuentas-clientes/auth/guards/role.guard.spec.ts`

### Implementation for User Story 2

- [X] T041 [US2] Implementar repositorio de usuarios en `backend/core/repositories/cuentas_clientes/user_repository.py`
- [X] T042 [US2] Implementar repositorio de roles negocio en `backend/core/repositories/cuentas_clientes/role_repository.py`
- [X] T043 [US2] Implementar servicio de gestion de usuarios en `backend/apps/cuentas_clientes/services/user_management_service.py`
- [X] T044 [US2] Implementar servicio RBAC de negocio en `backend/apps/cuentas_clientes/services/business_rbac_service.py`
- [X] T045 [US2] Implementar vistas DRF de usuarios/roles en `backend/apps/cuentas_clientes/views/user_role_views.py`
- [X] T046 [US2] Implementar `RoleGuard` en `frontend/src/app/modules/cuentas-clientes/auth/guards/role.guard.ts`
- [X] T047 [US2] Implementar servicio frontend de admin usuarios/roles en `frontend/src/app/modules/cuentas-clientes/auth/services/user-role-admin.service.ts`

**Checkpoint**: US2 funcional e independiente.

**US2 Gate (must pass before next story)**:
- [X] T070 [US2] Validar cumplimiento de `CA-AUT-004` y `CA-AUT-005` en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`

---

## Phase 5: User Story 3 - Gestion de usuarios y roles de servidor (Priority: P2)

**Goal**: Habilitar capa tecnica de acceso a infraestructura para Administrador/Director Tecnologico.

**Independent Test**: Admin/Director gestiona usuarios/roles de servidor y asignaciones sin afectar RBAC de negocio.

**Measurable Criteria**: Cumplir CA-AUT-006 y aislamiento de capa tecnica vs negocio.

### Tests for User Story 3

- [X] T048 [P] [US3] Crear test de contrato API (marker: api, AAA) para CU-O15 en `backend/apps/cuentas_clientes/tests/api/test_server_access_contract.py`
- [X] T049 [P] [US3] Crear test de repositorio (marker: repository, AAA) para entidades de servidor en `backend/apps/cuentas_clientes/tests/repositories/test_server_access_repository.py`
- [X] T050 [P] [US3] Crear test de servicio (marker: service, AAA) para acceso servidor en `backend/apps/cuentas_clientes/tests/services/test_server_access_service.py`
- [X] T051 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para admin acceso servidor en `frontend/src/app/modules/cuentas-clientes/auth/services/server-access-admin.service.spec.ts`

### Implementation for User Story 3

- [X] T052 [US3] Implementar repositorio de acceso servidor en `backend/core/repositories/cuentas_clientes/server_access_repository.py`
- [X] T053 [US3] Implementar servicio de acceso servidor en `backend/apps/cuentas_clientes/services/server_access_service.py`
- [X] T054 [US3] Implementar vistas DRF de CU-O15 en `backend/apps/cuentas_clientes/views/server_access_views.py`
- [X] T055 [US3] Implementar servicio frontend de acceso servidor en `frontend/src/app/modules/cuentas-clientes/auth/services/server-access-admin.service.ts`

**Checkpoint**: US3 operativa sin romper US1/US2.

**US3 Gate (must pass before next story)**:
- [X] T071 [US3] Validar cumplimiento de `CA-AUT-006` en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`

---

## Phase 6: User Story 4 - Recuperar y restablecer contraseña (Priority: P1)

**Goal**: Soportar password-reset por contraseña temporal enviada por correo y forzar cambio al siguiente login.

**Independent Test**: Usuario solicita reset, recibe flujo de cambio obligatorio y no accede libremente hasta actualizar contraseña.

**Measurable Criteria**: Cumplir CA-AUT-003 y CA-AUT-007.

### Tests for User Story 4

- [X] T056 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/auth/password-reset` en `backend/apps/cuentas_clientes/tests/api/test_password_reset_contract.py`
- [X] T057 [P] [US4] Crear test de repositorio (marker: repository, AAA) para credenciales en `backend/apps/cuentas_clientes/tests/repositories/test_credential_repository.py`
- [X] T058 [P] [US4] Crear test de servicio (marker: service, AAA) para password reset en `backend/apps/cuentas_clientes/tests/services/test_password_reset_service.py`
- [X] T059 [P] [US4] Crear test unitario frontend (marker: unit, AAA) para flujo reset en `frontend/src/app/modules/cuentas-clientes/auth/services/password-reset.service.spec.ts`

### Implementation for User Story 4

- [X] T060 [US4] Implementar repositorio de credenciales en `backend/core/repositories/cuentas_clientes/credential_repository.py`
- [X] T061 [US4] Implementar servicio de password reset en `backend/apps/cuentas_clientes/services/password_reset_service.py`
- [X] T062 [US4] Implementar vista DRF de password reset en `backend/apps/cuentas_clientes/views/password_reset_views.py`
- [X] T063 [US4] Implementar servicio frontend de reset en `frontend/src/app/modules/cuentas-clientes/auth/services/password-reset.service.ts`
- [X] T064 [US4] Implementar pantalla de recuperacion/cambio obligado en `frontend/src/app/modules/cuentas-clientes/auth/pages/password-reset.page.ts`

**Checkpoint**: US4 completa y verificable independientemente.

**US4 Gate (must pass before polish)**:
- [X] T072 [US4] Validar cumplimiento de `CA-AUT-003` y `CA-AUT-007` en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cierre de calidad, performance y alineacion final de artefactos.

- [X] T065 [P] Añadir test de performance login (k6/locust) con umbral p95 <= 500 ms en `backend/apps/cuentas_clientes/tests/performance/test_login_p95.py`
- [X] T066 [P] Documentar resultado de prueba de performance y disponibilidad (evidencia de `CA-AUT-010`) en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/quickstart.md`
- [X] T067 [P] Actualizar mapeo RF/RNF/CA->Task IDs en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`
- [X] T068 Ejecutar validacion final end-to-end de quickstart en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/quickstart.md`
- [X] T073 Validar cumplimiento final de `CA-AUT-010` (RNF-AUT-004) en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/traceability.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): inicia inmediatamente.
- Phase 2 (Foundational): depende de Phase 1; bloquea todas las historias.
- Phases 3-6 (US1-US4): dependen de Phase 2.
- Phase 7 (Polish): depende de completar historias objetivo.

### User Story Dependencies

- **US1 (P1)**: depende solo de Foundational; define MVP.
- **US2 (P1)**: depende de Foundational; paralelizable con US4.
- **US3 (P2)**: depende de Foundational y de estabilidad de auth base.
- **US4 (P1)**: depende de Foundational y del endpoint login para cambio obligatorio.

### Within Each User Story

- Primero tests (AAA) con marker correspondiente.
- Luego repositorios (`backend/core/repositories/...`).
- Luego servicios (`backend/apps/.../services`).
- Luego vistas/endpoints.
- Finalmente integración frontend.

### Parallel Opportunities

- Tareas `[P]` en Setup/Foundational en paralelo.
- Dentro de cada historia: tests `[P]` paralelos por capa.
- Frontend de una historia puede avanzar en paralelo con backend de otra si no comparten archivos.

---

## Parallel Example: User Story 1

```bash
Task: "T019 [US1] test_auth_login_contract.py (marker api, AAA)"
Task: "T022 [US1] test_auth_service.py (marker service, AAA)"
Task: "T023 [US1] test_logout_service.py (marker service, AAA)"
Task: "T025 [US1] session.guard.spec.ts (marker unit, AAA)"
```

---

## Implementation Strategy

### MVP First (US1)

1. Completar Phase 1 y Phase 2.
2. Completar Phase 3 (US1) end-to-end.
3. Verificar CA-AUT-001/008/009.
4. Demo tecnica de flujo auth base.

### Incremental Delivery

1. MVP con US1.
2. Agregar US2 (admin usuarios/roles).
3. Agregar US4 (password reset) para cerrar ciclo de identidad.
4. Agregar US3 (acceso servidor) como capacidad tecnica avanzada.
5. Cerrar con Phase 7 (performance + trazabilidad final).

### Team Parallel Strategy

1. Equipo completo en Phase 1-2.
2. Luego:
   - Dev A: US2
   - Dev B: US4
   - Dev C: US3
3. Integracion final y cierre de performance.

---

## Notes

- Repositorios alineados al patrón en `backend/core/repositories/...`.
- Todas las tareas de servicio/repositorio tienen su test asociado con marker y AAA.
- Se mantiene la regla: Kafka unico canal de escritura, sin escrituras directas a Pinot.
