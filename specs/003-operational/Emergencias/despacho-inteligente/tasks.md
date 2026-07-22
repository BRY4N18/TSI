# Tasks: Despacho Inteligente y Asignación de Unidades

**Input**: Design documents from `specs/003-operational/Emergencias/despacho-inteligente/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/despacho-inteligente.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing.md` + usuario); cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api`/`critical_path` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US6`)
- Cada descripción incluye path exacto de archivo

### User Story Map

| Story | Prioridad | CU/RF | Escenarios spec |
|-------|-----------|-------|-----------------|
| US1 | P1 🎯 MVP | CU-O22, O23 | Escenario 1 |
| US2 | P1 | CU-O24, O45 | Escenarios 2, 9 |
| US3 | P1 | CU-O35, O36 | Escenarios 3, 4, 10 |
| US4 | P2 | CU-O33, O34, O38, RF-DES-011 | Escenarios 6, 7, 8 |
| US5 | P2 | RF-DES-010 | Escenario 5 |
| US6 | P2 | Frontend Angular | quickstart §3 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estructura `apps/despacho`, módulo Angular, fixtures JWT y alineación contract-first.

- [X] T001 Crear estructura de carpetas en `backend/apps/despacho/{views,services,consumers,jobs,tests/{api,services,repositories,consumers,unit,integration}}`, `backend/core/repositories/despacho/` y `frontend/src/app/modules/despacho/{pages,services,guards}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `critical_path`, `integration`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Añadir fixtures despacho (`operador_despacho_auth_headers`, `unidad_despacho_auth_headers`, `director_tecnologico_auth_headers`) en `backend/conftest.py` reutilizando JWT de auth-rbac
- [X] T004 [P] Generar tipos TypeScript desde contrato en `frontend/src/app/modules/despacho/services/models/despacho.types.ts` basado en `contracts/despacho-inteligente.openapi.yaml`
- [X] T005 [P] Crear módulo Angular lazy stub `frontend/src/app/modules/despacho/despacho.routes.ts` y registrar en `frontend/src/app/app.routes.ts`
- [X] T006 [P] Crear matriz de trazabilidad CU/RF/CA→tasks en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot, permisos RBAC despacho, routing y registro consumers/jobs — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Emergencias/despacho-inteligente/contracts/despacho-inteligente.openapi.yaml`
- [X] T008 Implementar repositorio `Fact_Despacho` (lectura/escritura Kafka) en `backend/core/repositories/despacho/despacho_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: repository, AAA) para `despacho_repository.py` en `backend/apps/despacho/tests/repositories/test_despacho_repository.py`
- [X] T010 Implementar repositorio `Fact_NotificacionDespacho` en `backend/core/repositories/despacho/notificacion_despacho_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: repository, AAA) para `notificacion_despacho_repository.py` en `backend/apps/despacho/tests/repositories/test_notificacion_despacho_repository.py`
- [X] T012 Implementar repositorio `Fact_HistorialDespachoUnidad` en `backend/core/repositories/despacho/historial_despacho_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: repository, AAA) para `historial_despacho_repository.py` en `backend/apps/despacho/tests/repositories/test_historial_despacho_repository.py`
- [X] T014 Implementar repositorio posición efectiva unidad en `backend/core/repositories/despacho/ubicacion_unidad_repository.py` (RN-DES-010)
- [X] T015 [P] Crear test de repositorio (marker: repository, AAA) para `ubicacion_unidad_repository.py` en `backend/apps/despacho/tests/repositories/test_ubicacion_unidad_repository.py`
- [X] T016 Implementar repositorio geografía condado/vecinos en `backend/core/repositories/despacho/geografia_repository.py`
- [X] T017 [P] Crear test de repositorio (marker: repository, AAA) para `geografia_repository.py` en `backend/apps/despacho/tests/repositories/test_geografia_repository.py`
- [X] T018 Implementar repositorio transiciones caso despacho en `backend/core/repositories/despacho/estado_accidente_despacho_repository.py`
- [X] T019 [P] Crear test de repositorio (marker: repository, AAA) para `estado_accidente_despacho_repository.py` en `backend/apps/despacho/tests/repositories/test_estado_accidente_despacho_repository.py`
- [X] T020 Implementar repositorio parámetros algoritmo en `backend/core/repositories/despacho/parametros_despacho_repository.py`
- [X] T021 [P] Crear test de repositorio (marker: repository, AAA) para `parametros_despacho_repository.py` en `backend/apps/despacho/tests/repositories/test_parametros_despacho_repository.py`
- [X] T022 Extender `unidad_emergencia_repository.py` con consulta candidatas por condado en `backend/core/repositories/despacho/unidad_emergencia_repository.py`
- [X] T023 [P] Crear test de repositorio (marker: repository, AAA) para candidatas por condado en `backend/apps/despacho/tests/repositories/test_unidad_emergencia_candidatas_repository.py`
- [X] T024 Implementar permisos despacho (`IsOperadorDespacho`, `IsUnidadDespachoOwn`, `IsDirectorTecnologicoOrAdmin`) en `backend/apps/despacho/permissions.py`
- [X] T025 [P] Crear test unitario (marker: unit, AAA) para permisos despacho en `backend/apps/despacho/tests/unit/test_despacho_permissions.py`
- [X] T026 Registrar rutas despacho en `backend/apps/despacho/views/urls.py` (stubs) y verificar inclusión en `backend/config/urls.py`
- [X] T027 [P] Configurar topic dominio `DespachoTimeout_topic` y registro consumers/jobs en `backend/apps/despacho/apps.py`

**Checkpoint**: Repositorios, permisos, routing y orquestación base listos.

---

## Phase 3: User Story 1 — Asignación automática y notificación (Priority: P1) 🎯 MVP

**Goal**: CU-O22 + O23 — consumer `AccidenteReportado` ejecuta algoritmo (condado, Haversine, scoring), persiste despacho y notifica push/SMS.

**Independent Test**: Accidente REPORTADO dispara consumer; se crean filas Kafka en `Fact_Despacho`, `Fact_NotificacionDespacho`, `Fact_HistorialDespachoUnidad`; caso → `BUSCANDO_UNIDAD`; notificación entregada en <5s (CA-DES-001).

**Measurable Criteria**: CA-DES-001, CA-DES-002, CA-DES-003; Escenario 1; RNF-DES-003.

### Tests for User Story 1

- [X] T028 [P] [US1] Crear test de servicio (marker: service, AAA) para `concordancia_tipo_service.py` en `backend/apps/despacho/tests/services/test_concordancia_tipo_service.py`
- [X] T029 [P] [US1] Crear test de servicio (marker: service, AAA) para `consulta_candidatas_service.py` en `backend/apps/despacho/tests/services/test_consulta_candidatas_service.py`
- [X] T030 [P] [US1] Crear test de servicio (marker: service, AAA) para `asignacion_inteligente_service.py` en `backend/apps/despacho/tests/services/test_asignacion_inteligente_service.py`
- [X] T031 [P] [US1] Crear test de servicio (marker: service, AAA) para `notificacion_despacho_service.py` en `backend/apps/despacho/tests/services/test_notificacion_despacho_service.py`
- [X] T032 [P] [US1] Crear test de consumer (marker: service, AAA) para `accidente_reportado_consumer.py` en `backend/apps/despacho/tests/consumers/test_accidente_reportado_consumer.py`
- [X] T033 [US1] Crear test integración camino crítico (marker: critical_path, AAA) O22 en `backend/apps/despacho/tests/integration/test_asignacion_automatica_integration.py`

### Implementation for User Story 1

- [X] T034 [US1] Implementar `concordancia_tipo_service.py` (severidad, keywords moderada RF-DES-010) en `backend/apps/despacho/services/concordancia_tipo_service.py`
- [X] T035 [US1] Implementar `consulta_candidatas_service.py` (filtro condado, exclusión rechazos RN-DES-006) en `backend/apps/despacho/services/consulta_candidatas_service.py`
- [X] T036 [US1] Implementar `asignacion_inteligente_service.py` (Haversine, scoring, persistencia Kafka) en `backend/apps/despacho/services/asignacion_inteligente_service.py`
- [X] T037 [US1] Implementar `notificacion_despacho_service.py` (push/SMS, reintento, fail-fast O36 RN-DES-011) en `backend/apps/despacho/services/notificacion_despacho_service.py`
- [X] T038 [US1] Implementar `accidente_reportado_consumer.py` en `backend/apps/despacho/consumers/accidente_reportado_consumer.py`

**Checkpoint**: US1 operativa — asignación automática end-to-end desde REPORTADO.

**US1 Gate**:
- [X] T039 [US1] Validar CA-DES-001, CA-DES-002, CA-DES-003 en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`

---

## Phase 4: User Story 2 — Confirmar y rechazar despacho (Priority: P1)

**Goal**: CU-O24 + O45 — unidad confirma o rechaza vía `/mi-despacho/*`; rechazo dispara O36 síncrono.

**Independent Test**: Unidad `GET /mi-despacho/pendientes` → `POST .../confirmar` → caso ASIGNADO, unidad En Misión; rechazo con motivo → `activo=false` + re-asignación.

**Measurable Criteria**: CA-DES-004, CA-DES-005; Escenarios 2, 9.

### Tests for User Story 2

- [X] T040 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/mi-despacho/pendientes` en `backend/apps/despacho/tests/api/test_listar_pendientes_contract.py`
- [X] T041 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/mi-despacho/{id}` en `backend/apps/despacho/tests/api/test_detalle_despacho_unidad_contract.py`
- [X] T042 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/mi-despacho/{id}/confirmar` en `backend/apps/despacho/tests/api/test_confirmar_despacho_contract.py`
- [X] T043 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/mi-despacho/{id}/rechazar` en `backend/apps/despacho/tests/api/test_rechazar_despacho_contract.py`
- [X] T044 [P] [US2] Crear test de servicio (marker: service, AAA) para `confirmar_despacho_service.py` en `backend/apps/despacho/tests/services/test_confirmar_despacho_service.py`
- [X] T045 [P] [US2] Crear test de servicio (marker: service, AAA) para `rechazar_despacho_service.py` en `backend/apps/despacho/tests/services/test_rechazar_despacho_service.py`

### Implementation for User Story 2

- [X] T046 [US2] Implementar `confirmar_despacho_service.py` (O24, transición ASIGNADO, En Misión) en `backend/apps/despacho/services/confirmar_despacho_service.py`
- [X] T047 [US2] Implementar `rechazar_despacho_service.py` (O45, activo=false, dispara O36 síncrono) en `backend/apps/despacho/services/rechazar_despacho_service.py`
- [X] T048 [US2] Implementar vistas mi-despacho en `backend/apps/despacho/views/mi_despacho_views.py` y registrar en `backend/apps/despacho/views/urls.py`

**Checkpoint**: US2 operativa — ciclo unidad confirma/rechaza completo.

**US2 Gate**:
- [X] T049 [US2] Validar CA-DES-004, CA-DES-005 en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`

---

## Phase 5: User Story 3 — Timeout y re-asignación (Priority: P1)

**Goal**: CU-O35 + O36 — job timeout publica `DespachoTimeout_topic`; consumer O36 re-asigna; agotamiento candidatas → alerta crítica.

**Independent Test**: Despacho Pendiente >90s → job O35 marca Timeout + evento → consumer crea nuevo intento; escenario sin candidatas genera alerta (Escenario 4).

**Measurable Criteria**: CA-DES-006, CA-DES-007, CA-DES-013; Escenarios 3, 4, 10.

### Tests for User Story 3

- [X] T050 [P] [US3] Crear test de servicio (marker: service, AAA) para `timeout_despacho_service.py` en `backend/apps/despacho/tests/services/test_timeout_despacho_service.py`
- [X] T051 [P] [US3] Crear test de servicio (marker: service, AAA) para `reasignacion_despacho_service.py` en `backend/apps/despacho/tests/services/test_reasignacion_despacho_service.py`
- [X] T052 [P] [US3] Crear test de consumer (marker: service, AAA) para `despacho_timeout_consumer.py` en `backend/apps/despacho/tests/consumers/test_despacho_timeout_consumer.py`
- [X] T053 [US3] Crear test integración (marker: critical_path, AAA) timeout→O36 en `backend/apps/despacho/tests/integration/test_timeout_reasignacion_integration.py`
- [X] T054 [P] [US3] Crear test integración (marker: critical_path, AAA) fallo entrega O23→O36 en `backend/apps/despacho/tests/integration/test_fallo_notificacion_integration.py`

### Implementation for User Story 3

- [X] T055 [US3] Implementar `reasignacion_despacho_service.py` (O36, exclusión rechazos, alerta crítica) en `backend/apps/despacho/services/reasignacion_despacho_service.py`
- [X] T056 [US3] Implementar `timeout_despacho_service.py` (O35, activo=false, publica evento) en `backend/apps/despacho/services/timeout_despacho_service.py`
- [X] T057 [US3] Implementar job `timeout_despacho_job.py` en `backend/apps/despacho/jobs/timeout_despacho_job.py`
- [X] T058 [US3] Implementar `despacho_timeout_consumer.py` en `backend/apps/despacho/consumers/despacho_timeout_consumer.py`

**Checkpoint**: US3 operativa — re-intentos automáticos por timeout, rechazo y fallo de entrega.

**US3 Gate**:
- [X] T059 [US3] Validar CA-DES-006, CA-DES-007, CA-DES-013 en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`

---

## Phase 6: User Story 4 — Acciones operador y monitoreo (Priority: P2)

**Goal**: CU-O33, O34, O38 + RF-DES-011 — asignación manual, escalamiento condado vecino, despacho múltiple, monitoreo REST + SSE.

**Independent Test**: Operador consulta estado despacho, lista candidatas, asigna manualmente, escala zona, coordina segunda unidad; SSE emite eventos en tiempo real.

**Measurable Criteria**: CA-DES-008, CA-DES-010, CA-DES-011, CA-DES-012; Escenarios 6, 7, 8.

### Tests for User Story 4

- [X] T060 [P] [US4] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes/{id}/despacho` en `backend/apps/despacho/tests/api/test_monitoreo_despacho_contract.py`
- [X] T061 [P] [US4] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes/{id}/despacho/unidades-candidatas` en `backend/apps/despacho/tests/api/test_listar_candidatas_contract.py`
- [X] T062 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST .../asignar-manual` en `backend/apps/despacho/tests/api/test_asignar_manual_contract.py`
- [X] T063 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST .../escalar-zona` en `backend/apps/despacho/tests/api/test_escalar_zona_contract.py`
- [X] T064 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST .../coordinar` en `backend/apps/despacho/tests/api/test_coordinar_despacho_contract.py`
- [X] T065 [P] [US4] Crear test de servicio (marker: service, AAA) para `asignacion_manual_service.py` en `backend/apps/despacho/tests/services/test_asignacion_manual_service.py`
- [X] T066 [P] [US4] Crear test de servicio (marker: service, AAA) para `escalamiento_zona_service.py` en `backend/apps/despacho/tests/services/test_asignacion_manual_service.py`
- [X] T067 [P] [US4] Crear test de servicio (marker: service, AAA) para `coordinacion_multiple_service.py` en `backend/apps/despacho/tests/services/test_asignacion_manual_service.py`
- [X] T068 [P] [US4] Crear test de servicio (marker: service, AAA) para `monitoreo_despacho_service.py` en `backend/apps/despacho/tests/services/test_asignacion_manual_service.py`

### Implementation for User Story 4

- [X] T069 [US4] Implementar `asignacion_manual_service.py` (O33, origen Manual) en `backend/apps/despacho/services/asignacion_manual_service.py`
- [X] T070 [US4] Implementar `escalamiento_zona_service.py` (O34, condados vecinos, Dim_NotaAccidente) en `backend/apps/despacho/services/escalamiento_zona_service.py`
- [X] T071 [US4] Implementar `coordinacion_multiple_service.py` (O38, validación N-N) en `backend/apps/despacho/services/coordinacion_multiple_service.py`
- [X] T072 [US4] Implementar `monitoreo_despacho_service.py` (historial intentos, SSE pub/sub) en `backend/apps/despacho/services/monitoreo_despacho_service.py`
- [X] T073 [US4] Implementar vistas asignación en `backend/apps/despacho/views/asignacion_views.py`
- [X] T074 [US4] Implementar vistas monitoreo + SSE en `backend/apps/despacho/views/monitoreo_views.py` y completar `backend/apps/despacho/views/urls.py`

**Checkpoint**: US4 operativa — operador controla y monitorea despacho en tiempo real.

**US4 Gate**:
- [X] T075 [US4] Validar CA-DES-008, CA-DES-010, CA-DES-011, CA-DES-012 en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`

---

## Phase 7: User Story 5 — Parámetros del algoritmo (Priority: P2)

**Goal**: RF-DES-010 — Director Tecnológico / Administrador configura timeout, pesos y prioridades.

**Independent Test**: `PATCH /despacho/parametros` cambia timeout y pesos; despachos subsecuentes usan nuevos valores; audit log registrado.

**Measurable Criteria**: CA-DES-008; Escenario 5.

### Tests for User Story 5

- [X] T076 [P] [US5] Crear test de contrato API (marker: api, AAA) para `GET/PATCH /api/v1/despacho/parametros` en `backend/apps/despacho/tests/api/test_parametros_despacho_contract.py`
- [X] T077 [P] [US5] Crear test de servicio (marker: service, AAA) para `parametros_despacho_service.py` en `backend/apps/despacho/tests/services/test_parametros_despacho_service.py`

### Implementation for User Story 5

- [X] T078 [US5] Implementar `parametros_despacho_service.py` (validación rangos RN-DES-003, audit) en `backend/apps/despacho/services/parametros_despacho_service.py`
- [X] T079 [US5] Implementar vistas parámetros en `backend/apps/despacho/views/parametros_views.py`

**Checkpoint**: US5 operativa — algoritmo configurable sin redeploy.

**US5 Gate**:
- [X] T080 [US5] Validar CA-DES-008 en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`

---

## Phase 8: User Story 6 — Frontend Angular (Priority: P2)

**Goal**: Servicios tipados, guards por rol, páginas operador/unidad consumiendo contrato OpenAPI.

**Independent Test**: Operador accede monitoreo/asignación; Unidad confirma/rechaza; Director edita parámetros; guards bloquean roles incorrectos.

**Measurable Criteria**: quickstart §3; RF-DES-011 UX.

### Tests for User Story 6

- [X] T081 [P] [US6] Crear test unitario frontend (marker: unit, AAA) para `despacho-api.service.spec.ts` en `frontend/src/app/modules/despacho/services/despacho-api.service.spec.ts`
- [X] T082 [P] [US6] Crear test unitario frontend (marker: unit, AAA) para `mi-despacho-api.service.spec.ts` en `frontend/src/app/modules/despacho/services/mi-despacho-api.service.spec.ts`
- [X] T083 [P] [US6] Crear test unitario frontend (marker: unit, AAA) para `despacho-sse.service.spec.ts` en `frontend/src/app/modules/despacho/services/despacho-sse.service.spec.ts`
- [X] T084 [P] [US6] Crear test unitario frontend (marker: unit, AAA) para `despacho-parametros-api.service.spec.ts` en `frontend/src/app/modules/despacho/services/despacho-parametros-api.service.spec.ts`
- [X] T085 [P] [US6] Crear test unitario frontend (marker: unit, AAA) para guards en `frontend/src/app/modules/despacho/guards/operador-despacho.guard.spec.ts`, `unidad-despacho.guard.spec.ts`, `director-tecnologico.guard.spec.ts`
- [X] T086 [P] [US6] Crear test unitario frontend (marker: unit, AAA) para rutas lazy en `frontend/src/app/modules/despacho/despacho.routes.spec.ts`

### Implementation for User Story 6

- [X] T087 [US6] Implementar `DespachoApiService` en `frontend/src/app/modules/despacho/services/despacho-api.service.ts`
- [X] T088 [US6] Implementar `MiDespachoApiService` en `frontend/src/app/modules/despacho/services/mi-despacho-api.service.ts`
- [X] T089 [US6] Implementar `DespachoSseService` (EventSource) en `frontend/src/app/modules/despacho/services/despacho-sse.service.ts`
- [X] T090 [US6] Implementar `DespachoParametrosApiService` en `frontend/src/app/modules/despacho/services/despacho-parametros-api.service.ts`
- [X] T091 [US6] Implementar guards en `frontend/src/app/modules/despacho/guards/operador-despacho.guard.ts`, `unidad-despacho.guard.ts`, `director-tecnologico.guard.ts`
- [X] T092 [US6] Completar rutas lazy con guards en `frontend/src/app/modules/despacho/despacho.routes.ts`
- [X] T093 [US6] Implementar página monitoreo en `frontend/src/app/modules/despacho/pages/monitoreo-despacho/monitoreo-despacho.page.ts`
- [X] T094 [US6] Implementar página asignación manual en `frontend/src/app/modules/despacho/pages/asignacion-manual/asignacion-manual.page.ts`
- [X] T095 [US6] Implementar página mi-despacho unidad en `frontend/src/app/modules/despacho/pages/mi-despacho/mi-despacho.page.ts`
- [X] T095b [US6] Rediseño dashboard mi-despacho (single-incident): header con severidad/código/countdown de respuesta, mapa de solo-lectura con ruta real (`shared/ui/map/read-only-route-map.component.ts`, `shared/services/ruta.service.ts` — movido desde `seguimiento/` por ser transversal), sidebar "Estado de unidad" (`idunidademergencia`/`unidademergencia` agregados a `PendienteDespacho`/`DetalleDespachoUnidadData`), cola compacta para pendientes adicionales, botones Confirmar/Rechazar con estado de carga completo (gerundio+spinner, revert a 15s) per `design-system.md §5`. Completa CU-O24 (`spec.md:312`, mapa+ruta ya especificado, no implementado hasta ahora). Personal asignado/equipamiento crítico quedan fuera de alcance — no existen en el modelo de datos (`Dim_UnidadEmergencia`); requerirían un `/speckit-specify` previo antes de implementarse.
- [X] T096 [US6] Implementar página parámetros algoritmo en `frontend/src/app/modules/despacho/pages/parametros-algoritmo/parametros-algoritmo.page.ts`
- [X] T097 [US6] Registrar entradas sidebar por rol en `frontend/src/app/core/sidebar/despacho-menu.config.ts`

**Checkpoint**: US6 operativa — UI consumiendo contrato REST + SSE.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Cadena crítica completa, quickstart E2E, cobertura constitucional y documentación.

- [X] T098 Crear test integración cadena crítica registro→despacho→confirmación (marker: critical_path, AAA) en `backend/apps/despacho/tests/integration/test_cadena_critica_despacho_integration.py`
- [X] T099 [P] Ejecutar y documentar escenarios A–H de `specs/003-operational/Emergencias/despacho-inteligente/quickstart.md` en `specs/003-operational/Emergencias/despacho-inteligente/traceability.md`
- [X] T100 [P] Verificar cobertura ≥80% servicios y ≥85% repositorios despacho con `pytest --cov apps/despacho core/repositories/despacho --cov-report=term-missing`
- [X] T101 [P] Verificar cobertura frontend ≥80% módulo despacho con `ng test --include=**/despacho/**` (compilación verificada vía `ng build`; Karma requiere Chrome en CI)
- [X] T102 [P] Actualizar nota extensión despacho-inteligente en `.specify/docs/architecture/module-map.md` (estado implementación)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — iniciar de inmediato
- **Foundational (Phase 2)**: Depende de Setup — **bloquea** todas las historias
- **US1 (Phase 3)**: Depende de Foundational — **MVP** asignación automática
- **US2 (Phase 4)**: Depende de US1 (despacho creado para confirmar/rechazar)
- **US3 (Phase 5)**: Depende de US1 + US2 (ciclo completo de intentos)
- **US4 (Phase 6)**: Depende de Foundational + US1 (servicios base); paralelo a US2/US3 tras US1
- **US5 (Phase 7)**: Depende de Foundational (T020–T021); paralelo a US4
- **US6 (Phase 8)**: Depende de US2 + US4 + US5 (endpoints disponibles)
- **Polish (Phase 9)**: Depende de US1–US6 deseados

### User Story Dependencies

```text
Phase 2 (Foundational)
    └── US1 (O22/O23 automático) ──┬── US2 (O24/O45)
                                    ├── US3 (O35/O36)
                                    └── US4 (O33/O34/O38/monitoreo)
              US5 (RF-DES-010) ─────┘ (paralelo tras Phase 2)
    US2 + US4 + US5 ── US6 (frontend)
    US1–US6 ── Phase 9 (cadena crítica)
```

### Within Each User Story

1. Tests de contrato/servicio/repositorio/consumer **antes** de implementación (fallan primero — TDD)
2. Repositorios (Phase 2) → Servicios → Vistas/Consumers/Jobs → Frontend
3. Cada servicio/repositorio: par implementación+test con patrón AAA y marker correcto

### Parallel Opportunities

- Phase 1: T002–T006 en paralelo
- Phase 2: tests T009, T011, T013, T015, T017, T019, T021, T023, T025 en paralelo tras su implementación
- US1 tests T028–T032 en paralelo antes de T034–T038
- US4 tests API T060–T064 en paralelo
- US6 tests frontend T081–T086 en paralelo
- US4 y US5 pueden avanzar en paralelo tras US1

### Parallel Example: User Story 1

```bash
# Tests servicio en paralelo (escribir primero):
T028 test_concordancia_tipo_service.py
T029 test_consulta_candidatas_service.py
T030 test_asignacion_inteligente_service.py
T031 test_notificacion_despacho_service.py
T032 test_accidente_reportado_consumer.py

# Luego implementación secuencial T034→T038
```

### Parallel Example: Phase 2 Repositories

```bash
# Tras T008 implementación:
T009 test_despacho_repository.py

# En paralelo con otras parejas repo+test:
T010+T011 notificacion_despacho_repository
T012+T013 historial_despacho_repository
T014+T015 ubicacion_unidad_repository
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1 + Phase 2
2. Completar Phase 3 (CU-O22 + O23)
3. **VALIDAR**: Escenario A quickstart — accidente REPORTADO → despacho automático en <5s
4. Demo: primer intento notificado a unidad óptima del condado

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 asignación automática → MVP camino crítico
3. US2 confirmar/rechazar → ciclo unidad cerrado
4. US3 timeout/re-asignación → resiliencia operativa
5. US4 acciones operador → control humano + monitoreo SSE
6. US5 parámetros → tunability algoritmo
7. US6 frontend → UX operacional completa
8. Phase 9 → cadena crítica y cobertura

### Suggested MVP Scope

**US1 (CU-O22 + O23)** — asignación automática es el corazón del camino crítico; sin US1 no hay despacho que confirmar.

---

## Notes

- Patrón AAA obligatorio; usar fixtures `mock_pinot`, `mock_kafka`, `auth_headers` de `backend/conftest.py`
- Ningún repositorio escribe directo a Pinot — solo publicación Kafka
- Reutilizar `historial_estado_unidad_repository.py` y `unidad_emergencia_repository.py` existentes (evidencia-unidad)
- `ReasignacionDespachoService` compartido por O45 síncrono, O23 fail-fast y consumer O36
- Markers: `repository` para repos, `service` para servicios/consumers, `api` para contract tests, `critical_path` para integración despacho
- Commit sugerido tras cada par implementación+test o al cerrar cada checkpoint
