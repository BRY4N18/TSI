# Tasks: Gestión de Cuenta de Cliente

**Input**: Design documents from `specs/003-operational/Cuentas-Clientes/gestion-cuentas/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/gestion-cuentas.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing-expert` + `testing.md`). Cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (CU-O03, CU-O10, CU-O11) para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`, `US2`, `US3`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización de carpetas, tipos y trazabilidad para gestión de cuenta.

- [X] T001 Crear estructura de carpetas gestion-cuenta en `backend/apps/cuentas_clientes/{views,services,tests/api,tests/services,tests/repositories}` y `backend/core/repositories/cuentas_clientes/` y `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/{models,services,guards,pages/{perfil,preferencias,transferencia,baja}}`
- [X] T002 [P] Añadir fixtures de cuenta en `backend/conftest.py` (`mock_cliente`, `mock_preferencias`, `cliente_auth_headers`, `admin_auth_headers`)
- [X] T003 [P] Generar tipos TypeScript del contrato en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/models/cuenta-cliente.contract.ts` desde `contracts/gestion-cuentas.openapi.yaml`
- [X] T004 Crear matriz de trazabilidad CU→RF/RNF/CA→Task IDs en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios compartidos, permisos y auditoría bloqueantes para todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T005 Validar contrato OpenAPI como gate inicial en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/contracts/gestion-cuentas.openapi.yaml`
- [X] T006 Implementar repositorio de lectura/escritura Kafka de `Dim_Cliente` en `backend/core/repositories/cuentas_clientes/cliente_repository.py`
- [X] T007 [P] Crear test de repositorio (marker: repository, AAA) para `cliente_repository.py` en `backend/apps/cuentas_clientes/tests/repositories/test_cliente_repository.py`
- [X] T008 Implementar repositorio de `Dim_Preferencias_Cliente` en `backend/core/repositories/cuentas_clientes/preferencias_cliente_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: repository, AAA) para `preferencias_cliente_repository.py` en `backend/apps/cuentas_clientes/tests/repositories/test_preferencias_cliente_repository.py`
- [X] T010 Implementar repositorio de membresía usuario↔cuenta en `backend/core/repositories/cuentas_clientes/cuenta_usuario_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: repository, AAA) para `cuenta_usuario_repository.py` en `backend/apps/cuentas_clientes/tests/repositories/test_cuenta_usuario_repository.py`
- [X] T012 Implementar permisos DRF de cuenta (scope Cliente/Admin, admin local) en `backend/apps/cuentas_clientes/cuenta_permissions.py`
- [X] T013 [P] Crear test unitario (marker: unit, AAA) para `cuenta_permissions.py` en `backend/apps/cuentas_clientes/tests/unit/test_cuenta_permissions.py`
- [X] T014 Extender auditoría de cuenta (perfil, preferencias, transferencia, baja, fallo SMTP) en `backend/apps/cuentas_clientes/services/audit_service.py`
- [X] T015 [P] Crear test de servicio (marker: service, AAA) para eventos de auditoría de cuenta en `backend/apps/cuentas_clientes/tests/services/test_audit_cuenta_service.py`
- [X] T016 Registrar rutas stub de gestión de cuenta en `backend/apps/cuentas_clientes/views/urls.py`

**Checkpoint**: Repositorios base, permisos y auditoría listos; contrato validado.

---

## Phase 3: User Story 1 - Perfil y preferencias de cuenta (Priority: P1) 🎯 MVP

**Goal**: Entregar CU-O03 — ver/editar perfil corporativo, preferencias operativas y flujo de logo vía Azure Blob.

**Independent Test**: Cliente autenticado actualiza `razon_social` y `telefono_sms`; cambios persisten vía Kafka y quedan en logs; campos readonly no mutables.

**Measurable Criteria**: Cumplir CA-CTA-001.

### Tests for User Story 1

- [X] T017 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET/PATCH /api/v1/cuentas-clientes/{idcliente}/perfil` en `backend/apps/cuentas_clientes/tests/api/test_cuenta_perfil_contract.py`
- [X] T018 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET/PATCH /api/v1/cuentas-clientes/{idcliente}/preferencias` en `backend/apps/cuentas_clientes/tests/api/test_cuenta_preferencias_contract.py`
- [X] T019 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes/{idcliente}/logo/upload-url` en `backend/apps/cuentas_clientes/tests/api/test_logo_upload_url_contract.py`
- [X] T020 [P] [US1] Crear test de servicio (marker: service, AAA) para perfil en `backend/apps/cuentas_clientes/tests/services/test_cuenta_perfil_service.py`
- [X] T021 [P] [US1] Crear test de servicio (marker: service, AAA) para preferencias en `backend/apps/cuentas_clientes/tests/services/test_cuenta_preferencias_service.py`
- [X] T022 [P] [US1] Crear test de servicio (marker: service, AAA) para logo upload URL en `backend/apps/cuentas_clientes/tests/services/test_logo_upload_service.py`
- [X] T023 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `CuentaClienteApiService` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/services/cuenta-cliente-api.service.spec.ts`
- [X] T024 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `CuentaScopeGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/guards/cuenta-scope.guard.spec.ts`

### Implementation for User Story 1

- [X] T025 [US1] Implementar servicio de perfil corporativo en `backend/apps/cuentas_clientes/services/cuenta_perfil_service.py`
- [X] T026 [US1] Implementar servicio de preferencias en `backend/apps/cuentas_clientes/services/cuenta_preferencias_service.py`
- [X] T027 [US1] Implementar servicio de URL firmada para logo Azure Blob en `backend/apps/cuentas_clientes/services/logo_upload_service.py`
- [X] T028 [US1] Implementar vistas DRF de perfil/preferencias/logo en `backend/apps/cuentas_clientes/views/cuenta_views.py`
- [X] T029 [US1] Registrar rutas US1 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T030 [US1] Implementar `CuentaClienteApiService` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/services/cuenta-cliente-api.service.ts`
- [X] T031 [US1] Implementar `CuentaClienteFacadeService` (flujo logo upload + patch perfil) en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/services/cuenta-cliente-facade.service.ts`
- [X] T032 [US1] Implementar `CuentaScopeGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/guards/cuenta-scope.guard.ts`
- [X] T033 [US1] Implementar página de perfil en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/perfil/perfil.page.ts`
- [X] T034 [US1] Implementar página de preferencias en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/preferencias/preferencias.page.ts`
- [X] T035 [US1] Configurar rutas lazy de gestion-cuenta en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/gestion-cuenta.routes.ts`

**Checkpoint**: US1 operativa como MVP — perfil, preferencias y logo.

**US1 Gate (must pass before next story)**:
- [X] T036 [US1] Validar cumplimiento de `CA-CTA-001` en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/traceability.md`

---

## Phase 4: User Story 2 - Transferencia de propiedad (Priority: P1)

**Goal**: Entregar CU-O10 — transferencia inmediata de `admin_local_id` con notificación SMTP a involucrados.

**Independent Test**: Admin local transfiere a usuario activo de la misma cuenta; nuevo admin adquiere privilegios; anterior pierde admin local; emails enviados (o log si SMTP falla).

**Measurable Criteria**: Cumplir CA-CTA-002 y parte de CA-CTA-006 (transferencia).

### Tests for User Story 2

- [X] T037 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/cuentas-clientes/{idcliente}/usuarios-elegibles` en `backend/apps/cuentas_clientes/tests/api/test_usuarios_elegibles_contract.py`
- [X] T038 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes/{idcliente}/transferencia-propiedad` en `backend/apps/cuentas_clientes/tests/api/test_transferencia_propiedad_contract.py`
- [X] T039 [P] [US2] Crear test de servicio (marker: service, AAA) para transferencia en `backend/apps/cuentas_clientes/tests/services/test_transferencia_propiedad_service.py`
- [X] T040 [P] [US2] Crear test de servicio (marker: service, AAA) para notificaciones SMTP de cuenta en `backend/apps/cuentas_clientes/tests/services/test_cuenta_notificacion_service.py`
- [X] T041 [P] [US2] Crear test unitario frontend (marker: unit, AAA) para `AdminLocalGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/guards/admin-local.guard.spec.ts`

### Implementation for User Story 2

- [X] T042 [US2] Implementar servicio de notificaciones SMTP de cuenta en `backend/apps/cuentas_clientes/services/cuenta_notificacion_service.py`
- [X] T043 [US2] Implementar servicio de transferencia de propiedad en `backend/apps/cuentas_clientes/services/transferencia_propiedad_service.py`
- [X] T044 [US2] Extender vistas DRF con usuarios-elegibles y transferencia en `backend/apps/cuentas_clientes/views/cuenta_views.py`
- [X] T045 [US2] Registrar rutas US2 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T046 [US2] Implementar `AdminLocalGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/guards/admin-local.guard.ts`
- [X] T047 [US2] Implementar página de transferencia en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/transferencia/transferencia.page.ts`

**Checkpoint**: US2 funcional e independiente de US3.

**US2 Gate (must pass before next story)**:
- [X] T048 [US2] Validar cumplimiento de `CA-CTA-002` en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/traceability.md`

---

## Phase 5: User Story 3 - Baja de cuenta (Priority: P1)

**Goal**: Entregar CU-O11 — baja lógica, expulsión masiva de sesiones, motivo solo en logs, notificación al admin local.

**Independent Test**: Administrador da de baja cuenta; `estado='Dado de baja'`; sesiones expulsadas; usuarios no operan; datos históricos intactos.

**Measurable Criteria**: Cumplir CA-CTA-003, CA-CTA-004, CA-CTA-005 y CA-CTA-006 (baja).

### Tests for User Story 3

- [X] T049 [P] [US3] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/cuentas-clientes/{idcliente}/baja` en `backend/apps/cuentas_clientes/tests/api/test_baja_cuenta_contract.py`
- [X] T050 [P] [US3] Crear test de repositorio (marker: repository, AAA) para expulsión masiva de sesiones en `backend/apps/cuentas_clientes/tests/repositories/test_session_expel_by_cliente.py`
- [X] T051 [P] [US3] Crear test de servicio (marker: service, AAA) para baja de cuenta en `backend/apps/cuentas_clientes/tests/services/test_baja_cuenta_service.py`
- [X] T052 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `CuentaActivaGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/guards/cuenta-activa.guard.spec.ts`
- [X] T053 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para página de baja en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/baja/baja.page.spec.ts`

### Implementation for User Story 3

- [X] T054 [US3] Extender `SessionRepository.expel_all_by_cliente` en `backend/core/repositories/cuentas_clientes/session_repository.py`
- [X] T055 [US3] Implementar servicio de baja de cuenta en `backend/apps/cuentas_clientes/services/baja_cuenta_service.py`
- [X] T056 [US3] Extender vista DRF de baja en `backend/apps/cuentas_clientes/views/cuenta_views.py`
- [X] T057 [US3] Registrar ruta US3 en `backend/apps/cuentas_clientes/views/urls.py`
- [X] T058 [US3] Implementar `CuentaActivaGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/guards/cuenta-activa.guard.ts`
- [X] T059 [US3] Implementar página de baja (solo Administrador) en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/baja/baja.page.ts`
- [X] T060 [US3] Proteger ruta de baja con `AdministradorGuard` en `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/gestion-cuenta.routes.ts`

**Checkpoint**: US3 completa; módulo gestion-cuenta end-to-end.

**US3 Gate (must pass before polish)**:
- [X] T061 [US3] Validar cumplimiento de `CA-CTA-003`, `CA-CTA-004`, `CA-CTA-005` y `CA-CTA-006` en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/traceability.md`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Performance, documentación y validación final.

- [X] T062 [P] Añadir test de performance perfil/preferencias p95 ≤ 300 ms en `backend/apps/cuentas_clientes/tests/performance/test_cuenta_perfil_p95.py` (marker: slow)
- [X] T063 [P] Añadir test de performance transferencia/baja p95 ≤ 500 ms en `backend/apps/cuentas_clientes/tests/performance/test_cuenta_baja_p95.py` (marker: slow)
- [X] T064 [P] Documentar evidencia de performance y disponibilidad 99.9% en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/quickstart.md`
- [X] T065 [P] Actualizar mapeo RF/RNF/CA→Task IDs en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/traceability.md`
- [X] T066 Ejecutar validación end-to-end según `specs/003-operational/Cuentas-Clientes/gestion-cuentas/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): inicia inmediatamente.
- Phase 2 (Foundational): depende de Phase 1; bloquea todas las historias.
- Phases 3-5 (US1-US3): dependen de Phase 2.
- Phase 6 (Polish): depende de completar historias objetivo.

### User Story Dependencies

- **US1 (P1)**: depende solo de Foundational; define MVP (CU-O03).
- **US2 (P1)**: depende de Foundational + US1 (necesita cuenta/perfil operativo y `cliente_repository`).
- **US3 (P1)**: depende de Foundational; puede paralelizarse con US2 tras US1, pero requiere `cuenta_notificacion_service` (US2) para email de baja.

### Within Each User Story

1. Tests primero (AAA) con marker `api`/`service`/`repository`/`unit`.
2. Repositorios (`backend/core/repositories/...`).
3. Servicios (`backend/apps/.../services`).
4. Vistas/endpoints DRF.
5. Integración frontend (servicios → guards → páginas).

### Parallel Opportunities

- T002–T004 en Setup en paralelo.
- T007, T009, T011, T013, T015 en Foundational en paralelo.
- Dentro de cada historia: todos los tests `[P]` en paralelo.
- Frontend de US1 puede avanzar en paralelo con backend US1 tras definir contrato.

---

## Parallel Example: User Story 1

```bash
# Tests backend en paralelo (AAA):
pytest apps/cuentas_clientes/tests/api/test_cuenta_perfil_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_cuenta_preferencias_contract.py -v -m api
pytest apps/cuentas_clientes/tests/services/test_cuenta_perfil_service.py -v -m service
pytest apps/cuentas_clientes/tests/services/test_cuenta_preferencias_service.py -v -m service

# Tests frontend en paralelo:
ng test --include='**/gestion-cuenta/services/cuenta-cliente-api.service.spec.ts'
ng test --include='**/gestion-cuenta/guards/cuenta-scope.guard.spec.ts'
```

---

## Parallel Example: User Story 2

```bash
Task: "T037 [US2] test_usuarios_elegibles_contract.py (marker api, AAA)"
Task: "T039 [US2] test_transferencia_propiedad_service.py (marker service, AAA)"
Task: "T040 [US2] test_cuenta_notificacion_service.py (marker service, AAA)"
Task: "T041 [US2] admin-local.guard.spec.ts (marker unit, AAA)"
```

---

## Implementation Strategy

### MVP First (US1)

1. Completar Phase 1 y Phase 2.
2. Completar Phase 3 (US1) end-to-end.
3. Verificar CA-CTA-001.
4. Demo: cliente edita perfil y preferencias.

### Incremental Delivery

1. MVP con US1 (perfil + preferencias + logo).
2. Agregar US2 (transferencia inmediata + SMTP).
3. Agregar US3 (baja + expulsión sesiones + SMTP).
4. Cerrar con Phase 6 (performance + quickstart E2E).

### Team Parallel Strategy

1. Equipo completo en Phase 1-2.
2. Tras US1:
   - Dev A: US2 backend (transferencia + notificaciones)
   - Dev B: US2 frontend (transferencia.page + AdminLocalGuard)
   - Dev C: US3 backend (baja + expulsión sesiones)
3. Integración y Phase 6.

---

## Notes

- Repositorios en `backend/core/repositories/cuentas_clientes/`; Kafka único canal de escritura.
- Cada servicio/repositorio nuevo tiene test emparejado con marker y AAA según `.specify/docs/architecture/testing.md`.
- `cuenta_notificacion_service` lo implementa US2; US3 lo reutiliza para email de baja.
- Credenciales SMTP vía variables de entorno en implementación (no commitear secretos).
- Depende de **autenticacion-y-rbac** (JWT + sesión) y **incorporacion-clientes** (cuenta creada + membresía usuario↔cuenta).

---

## Task Summary

| Métrica | Valor |
|---------|-------|
| **Total tareas** | 66 |
| **US1 (CU-O03)** | 20 tareas (T017–T036) |
| **US2 (CU-O10)** | 12 tareas (T037–T048) |
| **US3 (CU-O11)** | 13 tareas (T049–T061) |
| **Setup + Foundational** | 16 tareas (T001–T016) |
| **Polish** | 5 tareas (T062–T066) |
| **Tests emparejados repo/servicio** | 14 pares backend + 5 frontend unit |
| **MVP sugerido** | Phase 1 + 2 + US1 (T001–T036) |
