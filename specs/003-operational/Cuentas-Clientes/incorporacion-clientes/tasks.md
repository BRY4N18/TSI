# Tasks: Incorporación de Clientes

**Input**: Design documents from `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/incorporacion-clientes.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing-expert` + `testing.md`). Cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (CU-O01, O12, O02/O09, O08, recordatorios) para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US5`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización de carpetas, tipos, fixtures y trazabilidad para incorporación de clientes.

- [X] T001 Crear estructura de carpetas incorporacion-clientes en `backend/apps/cuentas_clientes/{views/onboarding_views.py,services,management/commands,tests/api,tests/services,tests/repositories}` y `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/{models,services,guards,pages/{registro,configuracion,onboarding-wizard}}`
- [X] T002 [P] Añadir fixtures de onboarding en `backend/conftest.py` (`mock_onboarding_etapas`, `mock_cuenta_pendiente_onboarding`, `onboarding_cliente_auth_headers`)
- [X] T003 [P] Generar tipos TypeScript del contrato en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/models/incorporacion-cliente.contract.ts` desde `contracts/incorporacion-clientes.openapi.yaml`
- [X] T004 Crear matriz de trazabilidad CU→RF/RNF/CA→Task IDs en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios, topic Kafka, permisos, auditoría y alineación de membresía bloqueantes para todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T005 Validar contrato OpenAPI como gate inicial en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/contracts/incorporacion-clientes.openapi.yaml`
- [X] T006 Registrar topic `onboarding: Fact_Onboarding_topic` en `backend/config/settings.py` → `KAFKA_TOPICS`
- [X] T007 Extender `ClienteRepository` con `create()` y `find_by_admin_local()` en `backend/core/repositories/cuentas_clientes/cliente_repository.py`
- [X] T008 [P] Crear test de repositorio (marker: repository, AAA) para `create`/`find_by_admin_local` en `backend/apps/cuentas_clientes/tests/repositories/test_cliente_repository_onboarding.py`
- [X] T009 Implementar `OnboardingRepository` (Fact_Onboarding lectura/escritura Kafka) en `backend/core/repositories/cuentas_clientes/onboarding_repository.py`
- [X] T010 [P] Crear test de repositorio (marker: repository, AAA) para `onboarding_repository.py` en `backend/apps/cuentas_clientes/tests/repositories/test_onboarding_repository.py`
- [X] T011 Implementar permisos DRF de onboarding (Admin en O01/O12; admin_local scope en O02/O08) en `backend/apps/cuentas_clientes/onboarding_permissions.py`
- [X] T012 [P] Crear test unitario (marker: unit, AAA) para `onboarding_permissions.py` en `backend/apps/cuentas_clientes/tests/unit/test_onboarding_permissions.py`
- [X] T013 Extender auditoría de onboarding (registro, configuración, etapas, invitación, recordatorio, fallo SMTP) en `backend/apps/cuentas_clientes/services/audit_service.py`
- [X] T014 [P] Crear test de servicio (marker: service, AAA) para eventos de auditoría de onboarding en `backend/apps/cuentas_clientes/tests/services/test_audit_onboarding_service.py`
- [X] T015 Refactorizar `CuentaUsuarioRepository` para resolver membresía solo vía `admin_local_id` en `backend/core/repositories/cuentas_clientes/cuenta_usuario_repository.py`
- [X] T016 [P] Actualizar test de repositorio (marker: repository, AAA) en `backend/apps/cuentas_clientes/tests/repositories/test_cuenta_usuario_repository.py` al modelo `admin_local_id`
- [X] T017 Registrar rutas stub de incorporación en `backend/apps/cuentas_clientes/views/urls.py` apuntando a `onboarding_views.py`

**Checkpoint**: Repositorios base, topic Kafka, permisos, membresía alineada y contrato validado.

---

## Phase 3: User Story 1 - Registro de cuenta (Priority: P1) 🎯 MVP

**Goal**: Entregar CU-O01 — crear `Dim_Cliente` con `estado=Activo`, admin local, credencial temporal, rol Cliente y email de invitación.

**Independent Test**: Administrador registra cuenta con NIT único → 201 con `idcliente`, `estado=Activo`, `admin_local_id`; eventos Kafka en topics de cliente/usuario/credencial/rol; NIT duplicado → 409.

**Measurable Criteria**: Cumplir CA-ONB-001.

### Tests for User Story 1

- [X] T018 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes` en `backend/apps/cuentas_clientes/tests/api/test_registro_cuenta_contract.py`
- [X] T019 [P] [US1] Crear test de servicio (marker: service, AAA) para registro en `backend/apps/cuentas_clientes/tests/services/test_registro_cuenta_service.py`
- [X] T020 [P] [US1] Crear test de servicio (marker: service, AAA) para notificaciones SMTP de onboarding en `backend/apps/cuentas_clientes/tests/services/test_onboarding_notificacion_service.py`
- [X] T021 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `IncorporacionClienteApiService.registrarCuenta` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/services/incorporacion-cliente-api.service.spec.ts`

### Implementation for User Story 1

- [X] T022 [US1] Implementar servicio de notificaciones SMTP de onboarding en `backend/apps/cuentas_clientes/services/onboarding_notificacion_service.py`
- [X] T023 [US1] Implementar servicio de registro de cuenta en `backend/apps/cuentas_clientes/services/registro_cuenta_service.py`
- [X] T024 [US1] Implementar vista DRF `RegistrarCuentaView` en `backend/apps/cuentas_clientes/views/onboarding_views.py`
- [X] T025 [US1] Registrar ruta `POST /cuentas-clientes` en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T026 [US1] Implementar `IncorporacionClienteApiService` (método registro) en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/services/incorporacion-cliente-api.service.ts`
- [X] T027 [US1] Implementar página de registro (solo Administrador) en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/pages/registro/registro.page.ts`
- [X] T028 [US1] Configurar ruta lazy de registro con `AdministradorGuard` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/incorporacion-clientes.routes.ts`

**Checkpoint**: US1 operativa como MVP — alta de cuenta B2B.

**US1 Gate (must pass before next story)**:
- [X] T029 [US1] Validar cumplimiento de `CA-ONB-001` en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`

---

## Phase 4: User Story 2 - Configuración de cuenta (Priority: P1)

**Goal**: Entregar CU-O12 — `plan_suscripcion`, `logo_url`, `estado_onboarding=Pendiente` vía Azure Blob.

**Independent Test**: Administrador configura cuenta creada en US1 → 200 con `estado_onboarding=Pendiente`; logo vía upload-url + PATCH configuración.

**Measurable Criteria**: Cumplir CA-ONB-002.

### Tests for User Story 2

- [X] T030 [P] [US2] Crear test de contrato API (marker: api, AAA) para `PATCH /api/v1/cuentas-clientes/{idcliente}/configuracion` en `backend/apps/cuentas_clientes/tests/api/test_configuracion_cuenta_contract.py`
- [X] T031 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes/{idcliente}/logo/upload-url` (onboarding) en `backend/apps/cuentas_clientes/tests/api/test_onboarding_logo_upload_url_contract.py`
- [X] T032 [P] [US2] Crear test de servicio (marker: service, AAA) para configuración en `backend/apps/cuentas_clientes/tests/services/test_configuracion_cuenta_service.py`

### Implementation for User Story 2

- [X] T033 [US2] Implementar servicio de configuración de cuenta en `backend/apps/cuentas_clientes/services/configuracion_cuenta_service.py`
- [X] T034 [US2] Extender vistas DRF con configuración y logo upload en `backend/apps/cuentas_clientes/views/onboarding_views.py`
- [X] T035 [US2] Registrar rutas US2 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T036 [US2] Extender `IncorporacionClienteApiService` con configuración y logo en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/services/incorporacion-cliente-api.service.ts`
- [X] T037 [US2] Implementar página de configuración en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/pages/configuracion/configuracion.page.ts`
- [X] T038 [US2] Registrar ruta de configuración en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/incorporacion-clientes.routes.ts`

**Checkpoint**: US2 funcional — cuenta lista para onboarding.

**US2 Gate (must pass before next story)**:
- [X] T039 [US2] Validar cumplimiento de `CA-ONB-002` en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`

---

## Phase 5: User Story 3 - Onboarding digital (Priority: P1)

**Goal**: Entregar CU-O02 + CU-O09 — wizard con etapas canónicas, progreso en `Fact_Onboarding`, creación de `Dim_Preferencias_Cliente` en etapa `preferencias`.

**Independent Test**: Cliente (admin local) completa `cambio_password` → `perfil_corporativo` → `preferencias`; reanuda tras logout sin perder progreso; `estado_onboarding=Completado` al final.

**Measurable Criteria**: Cumplir CA-ONB-003, CA-ONB-004 y CA-ONB-005.

### Tests for User Story 3

- [X] T040 [P] [US3] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/cuentas-clientes/{idcliente}/onboarding/progreso` en `backend/apps/cuentas_clientes/tests/api/test_onboarding_progreso_contract.py`
- [X] T041 [P] [US3] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes/{idcliente}/onboarding/etapas` en `backend/apps/cuentas_clientes/tests/api/test_onboarding_etapas_contract.py`
- [X] T042 [P] [US3] Crear test de servicio (marker: service, AAA) para onboarding en `backend/apps/cuentas_clientes/tests/services/test_onboarding_service.py`
- [X] T043 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `AdminLocalOnboardingGuard` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/guards/admin-local-onboarding.guard.spec.ts`
- [X] T044 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `OnboardingPendienteGuard` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/guards/onboarding-pendiente.guard.spec.ts`
- [X] T045 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `OnboardingCompletadoGuard` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/guards/onboarding-completado.guard.spec.ts`
- [X] T046 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `OnboardingFacadeService` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/services/onboarding-facade.service.spec.ts`

### Implementation for User Story 3

- [X] T047 [US3] Implementar servicio de onboarding en `backend/apps/cuentas_clientes/services/onboarding_service.py`
- [X] T048 [US3] Extender vistas DRF con progreso y completar etapa en `backend/apps/cuentas_clientes/views/onboarding_views.py`
- [X] T049 [US3] Registrar rutas US3 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T050 [US3] Implementar `OnboardingFacadeService` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/services/onboarding-facade.service.ts`
- [X] T051 [US3] Implementar `AdminLocalOnboardingGuard` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/guards/admin-local-onboarding.guard.ts`
- [X] T052 [US3] Implementar `OnboardingPendienteGuard` y `OnboardingCompletadoGuard` en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/guards/onboarding-pendiente.guard.ts` y `onboarding-completado.guard.ts`
- [X] T053 [US3] Implementar wizard de onboarding en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/pages/onboarding-wizard/onboarding-wizard.page.ts`
- [X] T054 [US3] Configurar rutas del wizard con guards en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/incorporacion-clientes.routes.ts`

**Checkpoint**: US3 completa — onboarding end-to-end con reanudación.

**US3 Gate (must pass before next story)**:
- [X] T055 [US3] Validar cumplimiento de `CA-ONB-003`, `CA-ONB-004` y `CA-ONB-005` en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`

---

## Phase 6: User Story 4 - Reenviar invitación (Priority: P1)

**Goal**: Entregar CU-O08 — contraseña temporal, `estadocredencial=Cambio contraseña`, email al gmail del usuario.

**Independent Test**: Administrador o Cliente reenvía invitación → 200; credencial actualizada en Kafka; próximo login fuerza cambio de contraseña.

**Measurable Criteria**: Cumplir CA-ONB-006.

### Tests for User Story 4

- [X] T056 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes/{idcliente}/invitacion/reenviar` en `backend/apps/cuentas_clientes/tests/api/test_reenviar_invitacion_contract.py`
- [X] T057 [P] [US4] Crear test de servicio (marker: service, AAA) para invitación en `backend/apps/cuentas_clientes/tests/services/test_invitacion_service.py`

### Implementation for User Story 4

- [X] T058 [US4] Implementar servicio de reenvío de invitación en `backend/apps/cuentas_clientes/services/invitacion_service.py`
- [X] T059 [US4] Extender vista DRF de reenvío en `backend/apps/cuentas_clientes/views/onboarding_views.py`
- [X] T060 [US4] Registrar ruta US4 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T061 [US4] Añadir acción de reenvío de invitación en `frontend/src/app/modules/cuentas-clientes/incorporacion-clientes/pages/configuracion/configuracion.page.ts`

**Checkpoint**: US4 funcional e independiente.

**US4 Gate (must pass before next story)**:
- [X] T062 [US4] Validar cumplimiento de `CA-ONB-006` en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`

---

## Phase 7: User Story 5 - Recordatorios de onboarding (Priority: P2)

**Goal**: Entregar RN-ONB-004 / CA-ONB-007 — job semanal de correo al admin local desde día 30.

**Independent Test**: Cuenta con onboarding incompleto >30 días recibe un correo al ejecutar command; cuenta `Completado` no recibe; fallo SMTP solo loguea.

**Measurable Criteria**: Cumplir CA-ONB-007.

### Tests for User Story 5

- [X] T063 [P] [US5] Crear test de servicio (marker: service, AAA) para lógica de recordatorios en `backend/apps/cuentas_clientes/tests/services/test_onboarding_reminder_service.py`
- [X] T064 [P] [US5] Crear test de comando (marker: service, AAA) para `send_onboarding_reminders` en `backend/apps/cuentas_clientes/tests/services/test_send_onboarding_reminders_command.py`

### Implementation for User Story 5

- [X] T065 [US5] Implementar servicio de recordatorios en `backend/apps/cuentas_clientes/services/onboarding_reminder_service.py`
- [X] T066 [US5] Implementar management command en `backend/apps/cuentas_clientes/management/commands/send_onboarding_reminders.py`

**Checkpoint**: US5 completa — recordatorios automatizados.

**US5 Gate**:
- [X] T067 [US5] Validar cumplimiento de `CA-ONB-007` en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Performance, documentación y validación E2E.

- [X] T068 [P] Añadir test de performance registro p95 ≤ 800 ms en `backend/apps/cuentas_clientes/tests/performance/test_registro_cuenta_p95.py` (marker: slow)
- [X] T069 [P] Añadir test de performance etapa onboarding p95 ≤ 500 ms en `backend/apps/cuentas_clientes/tests/performance/test_onboarding_etapa_p95.py` (marker: slow)
- [X] T070 [P] Actualizar mapeo RF/RNF/CA→Task IDs en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/traceability.md`
- [X] T071 Ejecutar validación end-to-end según `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/quickstart.md`
- [X] T072 Verificar integración post-onboarding con gestion-cuentas (`GET /perfil` tras onboarding `Completado`) documentado en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/quickstart.md` §7

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): inicia inmediatamente.
- Phase 2 (Foundational): depende de Phase 1; bloquea todas las historias.
- Phases 3–7 (US1–US5): dependen de Phase 2; secuencia recomendada US1 → US2 → US3 → US4 → US5.
- Phase 8 (Polish): depende de completar historias objetivo.

### User Story Dependencies

- **US1 (P1)**: depende solo de Foundational; define MVP (CU-O01).
- **US2 (P1)**: depende de US1 (cuenta creada para configurar).
- **US3 (P1)**: depende de US2 (`estado_onboarding=Pendiente`).
- **US4 (P1)**: depende de US1 (usuario/credencial existente); integrable tras US1.
- **US5 (P2)**: depende de US1+US3 (cuentas con estado onboarding conocido).

### Within Each User Story

1. Tests primero (AAA) con marker `api`/`service`/`repository`/`unit`.
2. Repositorios (`backend/core/repositories/...`) — en Foundational salvo extensiones puntuales.
3. Servicios (`backend/apps/.../services`).
4. Vistas/endpoints DRF.
5. Integración frontend (servicios → guards → páginas).

### Parallel Opportunities

- T002–T004 en Setup en paralelo.
- T008, T010, T012, T014, T016 en Foundational en paralelo.
- Dentro de cada historia: todos los tests `[P]` en paralelo.
- Frontend de US1 puede avanzar en paralelo con backend US1 tras contrato validado (T005).

---

## Parallel Example: User Story 1

```bash
# Tests backend en paralelo (AAA):
pytest apps/cuentas_clientes/tests/api/test_registro_cuenta_contract.py -v -m api
pytest apps/cuentas_clientes/tests/services/test_registro_cuenta_service.py -v -m service
pytest apps/cuentas_clientes/tests/services/test_onboarding_notificacion_service.py -v -m service

# Test frontend en paralelo:
npm test -- --include='**/incorporacion-clientes/services/incorporacion-cliente-api.service.spec.ts'
```

---

## Parallel Example: User Story 3

```bash
Task: "T040 [US3] test_onboarding_progreso_contract.py (marker api, AAA)"
Task: "T041 [US3] test_onboarding_etapas_contract.py (marker api, AAA)"
Task: "T042 [US3] test_onboarding_service.py (marker service, AAA)"
Task: "T043–T046 [US3] guards y facade .spec.ts (marker unit, AAA)"
```

---

## Implementation Strategy

### MVP First (US1)

1. Completar Phase 1 y Phase 2.
2. Completar Phase 3 (US1) end-to-end.
3. Verificar CA-ONB-001.
4. Demo: administrador registra aseguradora/municipio.

### Incremental Delivery

1. MVP con US1 (registro + admin local + email).
2. Agregar US2 (configuración plan/logo).
3. Agregar US3 (wizard onboarding 3 etapas).
4. Agregar US4 (reenvío invitación).
5. Agregar US5 (recordatorios semanales).
6. Cerrar con Phase 8 (performance + quickstart E2E + integración gestion-cuentas).

### Team Parallel Strategy

1. Equipo completo en Phase 1–2.
2. Tras US1:
   - Dev A: US2 backend (configuración)
   - Dev B: US2 frontend (configuracion.page)
   - Dev C: US4 backend (invitación) en paralelo si US1 estable
3. US3 requiere US2 completo; luego US5 en background.

---

## Notes

- Repositorios en `backend/core/repositories/cuentas_clientes/`; Kafka único canal de escritura.
- Cada servicio/repositorio nuevo tiene test emparejado con marker y AAA según `.specify/docs/architecture/testing.md`.
- `onboarding_notificacion_service` lo implementa US1; US4 y US5 lo reutilizan.
- Membresía solo `admin_local_id` (RN-ONB-007); refactor `CuentaUsuarioRepository` en Foundational (T014–T015).
- Credenciales SMTP vía variables de entorno (no commitear secretos).
- Depende de **autenticacion-y-rbac** (JWT + sesión); prerequisito de **gestion-cuentas**.

---

## Task Summary

| Métrica | Valor |
|---------|-------|
| **Total tareas** | 72 |
| **US1 (CU-O01)** | 12 tareas (T018–T029) |
| **US2 (CU-O12)** | 10 tareas (T030–T039) |
| **US3 (CU-O02/O09)** | 16 tareas (T040–T055) |
| **US4 (CU-O08)** | 7 tareas (T056–T062) |
| **US5 (Recordatorios)** | 5 tareas (T063–T067) |
| **Setup + Foundational** | 17 tareas (T001–T017) |
| **Polish** | 5 tareas (T068–T072) |
| **Tests emparejados repo/servicio** | 12 pares backend + 6 frontend unit |
| **MVP sugerido** | Phase 1 + 2 + US1 (T001–T029) |
