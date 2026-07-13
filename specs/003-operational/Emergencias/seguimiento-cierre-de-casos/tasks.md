# Tasks: Seguimiento y Cierre de Casos

**Input**: Design documents from `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/seguimiento-cierre-de-casos.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing.md` + usuario); cada tarea de servicio/repositorio/job tiene test asociado con markers `unit`/`repository`/`service`/`api`/`critical_path` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US8`)
- Cada descripción incluye path exacto de archivo

### User Story Map

| Story | Prioridad | CU/RF | Escenarios spec |
|-------|-----------|-------|-----------------|
| US1 | P1 🎯 MVP | CU-O25, O26 | Escenarios 1, 2, 3 |
| US2 | P1 | RF-SEG-007, RNF-SEG-001 | Escenarios 1, 6 |
| US3 | P1 | CU-O28, RF-SEG-004 | Escenario 4 |
| US4 | P2 | CU-O39 | Escenario 8 |
| US5 | P2 | CU-O42, O44 | Escenarios 9, 10 |
| US6 | P2 | CU-O29, RF-SEG-005/006 | Escenario 5 |
| US7 | P2 | CU-O37, RNF-SEG-004/005 | Escenario 7 |
| US8 | P2 | Frontend Angular | quickstart §3 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estructura `apps/seguimiento`, módulo Angular, fixtures JWT y alineación contract-first.

- [X] T001 Crear estructura de carpetas en `backend/apps/seguimiento/{views,services,jobs,tests/{api,services,repositories,jobs,unit,integration}}`, `backend/core/repositories/seguimiento/` y `frontend/src/app/modules/seguimiento/{pages,services,guards,models}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `critical_path`, `integration`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Añadir fixtures seguimiento (`operador_seguimiento_auth_headers`, `unidad_seguimiento_auth_headers`, `cliente_expediente_auth_headers`) en `backend/conftest.py` reutilizando JWT de auth-rbac
- [X] T004 [P] Generar tipos TypeScript desde contrato en `frontend/src/app/modules/seguimiento/models/seguimiento.types.ts` basado en `contracts/seguimiento-cierre-de-casos.openapi.yaml`
- [X] T005 [P] Crear módulo Angular lazy stub `frontend/src/app/modules/seguimiento/seguimiento.routes.ts` y registrar en `frontend/src/app/app.routes.ts`
- [X] T006 [P] Crear matriz de trazabilidad CU/RF/CA→tasks en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot seguimiento, permisos RBAC, topics, routing y utilidades compartidas — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/contracts/seguimiento-cierre-de-casos.openapi.yaml`
- [X] T008 Registrar app `seguimiento` y topics Kafka (`historial_ubicacion_unidad`, `unidad_emergencia_snapshot`, `despacho_abortado`) en `backend/config/settings.py` → `KAFKA_TOPICS` e `INSTALLED_APPS`
- [X] T009 Implementar repositorio `Dim_HistorialUbicacionUnidadEmergencia` (lectura/escritura Kafka) en `backend/core/repositories/seguimiento/historial_ubicacion_repository.py`
- [X] T010 [P] Crear test de repositorio (marker: repository, AAA) para `historial_ubicacion_repository.py` en `backend/apps/seguimiento/tests/repositories/test_historial_ubicacion_repository.py`
- [X] T011 Implementar repositorio snapshot `Dim_UnidadEmergencia` en `backend/core/repositories/seguimiento/unidad_snapshot_repository.py`
- [X] T012 [P] Crear test de repositorio (marker: repository, AAA) para `unidad_snapshot_repository.py` en `backend/apps/seguimiento/tests/repositories/test_unidad_snapshot_repository.py`
- [X] T013 Implementar repositorio consultas expediente/historial en `backend/core/repositories/seguimiento/expediente_repository.py`
- [X] T014 [P] Crear test de repositorio (marker: repository, AAA) para `expediente_repository.py` en `backend/apps/seguimiento/tests/repositories/test_expediente_repository.py`
- [X] T015 Implementar repositorio parámetros seguimiento en `backend/core/repositories/seguimiento/parametros_seguimiento_repository.py`
- [X] T016 [P] Crear test de repositorio (marker: repository, AAA) para `parametros_seguimiento_repository.py` en `backend/apps/seguimiento/tests/repositories/test_parametros_seguimiento_repository.py`
- [X] T017 Implementar utilidad geofencing (radio 100m, histéresis 30s) en `backend/apps/seguimiento/services/geofencing_evaluator.py`
- [X] T018 [P] Crear test de servicio (marker: service, AAA) para `geofencing_evaluator.py` en `backend/apps/seguimiento/tests/services/test_geofencing_evaluator.py`
- [X] T019 Implementar `eta_calculo_service.py` (Haversine lineal, distancia remanente) en `backend/apps/seguimiento/services/eta_calculo_service.py`
- [X] T020 [P] Crear test de servicio (marker: service, AAA) para `eta_calculo_service.py` en `backend/apps/seguimiento/tests/services/test_eta_calculo_service.py`
- [X] T021 Implementar permisos seguimiento (`IsOperadorSeguimiento`, `IsUnidadSeguimiento`, `IsClienteExpediente`) en `backend/apps/seguimiento/permissions.py`
- [X] T022 [P] Crear test unitario (marker: unit, AAA) para permisos seguimiento en `backend/apps/seguimiento/tests/unit/test_seguimiento_permissions.py`
- [X] T023 Registrar rutas seguimiento stub en `backend/apps/seguimiento/views/urls.py` y verificar inclusión en `backend/config/urls.py`
- [X] T024 [P] Configurar registro jobs seguimiento en `backend/apps/seguimiento/apps.py`

**Checkpoint**: Repositorios, permisos, geofencing, ETA y routing base listos.

---

## Phase 3: User Story 1 — Rastreo GPS y llegada al sitio (Priority: P1) 🎯 MVP

**Goal**: CU-O25 + O26 — unidad envía GPS cada 10s; llegada manual o geofencing; caso → EN_ATENCION.

**Independent Test**: Despacho Confirmado → `POST /mi-seguimiento/posicion` persiste Kafka + snapshot; `POST .../llegada` o geofencing registra En_sitio y `fechahorallegada`.

**Measurable Criteria**: CA-SEG-001, CA-SEG-003, CA-SEG-004; Escenarios 1, 2, 3; RNF-SEG-002.

### Tests for User Story 1

- [X] T025 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/mi-seguimiento/posicion` en `backend/apps/seguimiento/tests/api/test_registrar_posicion_contract.py`
- [X] T026 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/mi-seguimiento/despachos/{iddespacho}/llegada` en `backend/apps/seguimiento/tests/api/test_registrar_llegada_contract.py`
- [X] T027 [P] [US1] Crear test de servicio (marker: service, AAA) para `registrar_posicion_gps_service.py` en `backend/apps/seguimiento/tests/services/test_registrar_posicion_gps_service.py`
- [X] T028 [P] [US1] Crear test de servicio (marker: service, AAA) para `registrar_llegada_service.py` en `backend/apps/seguimiento/tests/services/test_registrar_llegada_service.py`
- [X] T029 [US1] Crear test integración (marker: critical_path, AAA) GPS→geofencing→EN_ATENCION en `backend/apps/seguimiento/tests/integration/test_gps_llegada_integration.py`

### Implementation for User Story 1

- [X] T030 [US1] Implementar `registrar_llegada_service.py` (O26 manual, historial En_sitio, fechahorallegada) en `backend/apps/seguimiento/services/registrar_llegada_service.py`
- [X] T031 [US1] Implementar `registrar_posicion_gps_service.py` (O25 Kafka GPS + snapshot + geofencing O26 + ETA) en `backend/apps/seguimiento/services/registrar_posicion_gps_service.py`
- [X] T032 [US1] Implementar vistas mi-seguimiento GPS/llegada en `backend/apps/seguimiento/views/mi_seguimiento_views.py` y registrar en `backend/apps/seguimiento/views/urls.py`

**Checkpoint**: US1 operativa — rastreo GPS y llegada al sitio end-to-end.

**US1 Gate**:
- [X] T033 [US1] Validar CA-SEG-001, CA-SEG-003, CA-SEG-004 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 4: User Story 2 — Mapa operador y SSE (Priority: P1)

**Goal**: RF-SEG-007 + RNF-SEG-001 — mapa accidentes activos, unidades, rutas, ETA vía SSE.

**Independent Test**: Operador `GET /seguimiento/mapa` + `GET /seguimiento/stream`; eventos `seguimiento.posicion`/`seguimiento.eta` tras GPS unidad.

**Measurable Criteria**: CA-SEG-002; Escenarios 1, 6; RNF-SEG-001, RNF-SEG-003.

### Tests for User Story 2

- [X] T034 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/seguimiento/mapa` en `backend/apps/seguimiento/tests/api/test_mapa_seguimiento_contract.py`
- [X] T035 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/seguimiento/stream` en `backend/apps/seguimiento/tests/api/test_seguimiento_sse_contract.py`
- [X] T036 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes/{idaccidente}/seguimiento` en `backend/apps/seguimiento/tests/api/test_seguimiento_accidente_contract.py`
- [X] T037 [P] [US2] Crear test de servicio (marker: service, AAA) para `mapa_seguimiento_service.py` en `backend/apps/seguimiento/tests/services/test_mapa_seguimiento_service.py`
- [X] T038 [P] [US2] Crear test de servicio (marker: service, AAA) para `seguimiento_sse_service.py` en `backend/apps/seguimiento/tests/services/test_seguimiento_sse_service.py`

### Implementation for User Story 2

- [X] T039 [US2] Implementar `seguimiento_sse_service.py` (pub/sub eventos GPS/ETA/estado) en `backend/apps/seguimiento/services/seguimiento_sse_service.py`
- [X] T040 [US2] Implementar `mapa_seguimiento_service.py` (marcadores severidad, unidades, rutas) en `backend/apps/seguimiento/services/mapa_seguimiento_service.py`
- [X] T041 [US2] Implementar vistas mapa + SSE en `backend/apps/seguimiento/views/mapa_views.py` y completar `backend/apps/seguimiento/views/urls.py`
- [X] T042 [US2] Integrar emisión SSE desde `registrar_posicion_gps_service.py` en `backend/apps/seguimiento/services/registrar_posicion_gps_service.py`

**Checkpoint**: US2 operativa — operador monitorea mapa en tiempo real.

**US2 Gate**:
- [X] T043 [US2] Validar CA-SEG-002 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 5: User Story 3 — Cierre multi-despacho (Priority: P1)

**Goal**: CU-O28 + RF-SEG-004 — validar todos Retirado, auto-retiro con idusuario ejecutor, horafin/duracionminutos, liberar unidades.

**Independent Test**: Caso 2 despachos; uno Retirado → `POST .../cerrar` auto-retira pendiente, CERRADO, tiempos SLA inmutables.

**Measurable Criteria**: CA-SEG-005, CA-SEG-006, CA-SEG-007; Escenario 4; RN-SEG-012.

### Tests for User Story 3

- [X] T044 [P] [US3] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{idaccidente}/cerrar` en `backend/apps/seguimiento/tests/api/test_cerrar_caso_contract.py`
- [X] T045 [P] [US3] Crear test de servicio (marker: service, AAA) para `cerrar_caso_service.py` en `backend/apps/seguimiento/tests/services/test_cerrar_caso_service.py`
- [X] T046 [US3] Crear test integración camino crítico (marker: critical_path, AAA) cierre multi-despacho en `backend/apps/seguimiento/tests/integration/test_cierre_multi_despacho_integration.py`

### Implementation for User Story 3

- [X] T047 [US3] Implementar `cerrar_caso_service.py` (O28, auto-retiro, RF-SEG-004, tiempos SLA) en `backend/apps/seguimiento/services/cerrar_caso_service.py`
- [X] T048 [US3] Implementar vista cierre en `backend/apps/seguimiento/views/cierre_views.py` y registrar en `backend/apps/seguimiento/views/urls.py`

**Checkpoint**: US3 operativa — cierre de caso con validación N-N.

**US3 Gate**:
- [X] T049 [US3] Validar CA-SEG-005, CA-SEG-006, CA-SEG-007 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 6: User Story 4 — Abortar misión en tránsito (Priority: P2)

**Goal**: CU-O39 — Abortado, unidad Activa, evento `DespachoAbortado_topic` → O36 en despacho.

**Independent Test**: Unidad `POST .../abortar` → historial Abortado, Kafka evento, consumer despacho re-asigna.

**Measurable Criteria**: CA-SEG-012; Escenario 8.

### Tests for User Story 4

- [X] T050 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/mi-seguimiento/despachos/{iddespacho}/abortar` en `backend/apps/seguimiento/tests/api/test_abortar_mision_contract.py`
- [X] T051 [P] [US4] Crear test de servicio (marker: service, AAA) para `abortar_mision_service.py` en `backend/apps/seguimiento/tests/services/test_abortar_mision_service.py`
- [X] T052 [P] [US4] Crear test de consumer (marker: service, AAA) para `despacho_abortado_consumer.py` en `backend/apps/despacho/tests/consumers/test_despacho_abortado_consumer.py`
- [X] T053 [US4] Crear test integración (marker: critical_path, AAA) aborto→O36 en `backend/apps/seguimiento/tests/integration/test_abortar_mision_integration.py`

### Implementation for User Story 4

- [X] T054 [US4] Implementar `abortar_mision_service.py` (O39, publica `DespachoAbortado_topic`) en `backend/apps/seguimiento/services/abortar_mision_service.py`
- [X] T055 [US4] Extender vista abortar en `backend/apps/seguimiento/views/mi_seguimiento_views.py`
- [X] T056 [US4] Implementar `despacho_abortado_consumer.py` (invoca `ReasignacionDespachoService`) en `backend/apps/despacho/consumers/despacho_abortado_consumer.py`

**Checkpoint**: US4 operativa — aborto dispara re-asignación O36.

**US4 Gate**:
- [X] T057 [US4] Validar CA-SEG-012 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 7: User Story 5 — Cancelación y forzar retiro (Priority: P2)

**Goal**: CU-O42 + O44 — cancelar falsa alarma (solo motivo); forzar retiro unitario con idusuario operador.

**Independent Test**: O42 sin RF-SEG-004 ni evidencia; O44 parcial deja EN_ATENCION o cierra si todos Retirado.

**Measurable Criteria**: CA-SEG-013, CA-SEG-014; Escenarios 9, 10; RN-SEG-010.

### Tests for User Story 5

- [X] T058 [P] [US5] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{idaccidente}/cancelar` en `backend/apps/seguimiento/tests/api/test_cancelar_caso_contract.py`
- [X] T059 [P] [US5] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/despachos/{iddespacho}/forzar-retiro` en `backend/apps/seguimiento/tests/api/test_forzar_retiro_contract.py`
- [X] T060 [P] [US5] Crear test de servicio (marker: service, AAA) para `cancelar_caso_service.py` en `backend/apps/seguimiento/tests/services/test_cancelar_caso_service.py`
- [X] T061 [P] [US5] Crear test de servicio (marker: service, AAA) para `forzar_retiro_service.py` en `backend/apps/seguimiento/tests/services/test_forzar_retiro_service.py`

### Implementation for User Story 5

- [X] T062 [US5] Implementar `cancelar_caso_service.py` (O42, motivo Dim_NotaAccidente, sin RF-SEG-004) en `backend/apps/seguimiento/services/cancelar_caso_service.py`
- [X] T063 [US5] Implementar `forzar_retiro_service.py` (O44, reevalúa O28) en `backend/apps/seguimiento/services/forzar_retiro_service.py`
- [X] T064 [US5] Completar vistas cancelar/forzar en `backend/apps/seguimiento/views/cierre_views.py`

**Checkpoint**: US5 operativa — cancelación y cierre forzado desde central.

**US5 Gate**:
- [X] T065 [US5] Validar CA-SEG-013, CA-SEG-014 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 8: User Story 6 — Historial y expedientes (Priority: P2)

**Goal**: CU-O29 + RF-SEG-005/006 — historial operador; expedientes cliente por condado + PDF.

**Independent Test**: Operador lista con filtros; cliente solo CERRADOS en `Dim_Condado`; HTTP 403 cliente en mapa.

**Measurable Criteria**: CA-SEG-008, CA-SEG-009, CA-SEG-010; Escenario 5; RN-SEG-005.

### Tests for User Story 6

- [X] T066 [P] [US6] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/emergencias/historial` en `backend/apps/seguimiento/tests/api/test_historial_emergencias_contract.py`
- [X] T067 [P] [US6] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/emergencias/historial/{idaccidente}/expediente` en `backend/apps/seguimiento/tests/api/test_expediente_operador_contract.py`
- [X] T068 [P] [US6] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/cliente/expedientes` en `backend/apps/seguimiento/tests/api/test_expedientes_cliente_contract.py`
- [X] T069 [P] [US6] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/cliente/expedientes/{idaccidente}/pdf` en `backend/apps/seguimiento/tests/api/test_expediente_pdf_contract.py`
- [X] T070 [P] [US6] Crear test de servicio (marker: service, AAA) para `historial_emergencias_service.py` en `backend/apps/seguimiento/tests/services/test_historial_emergencias_service.py`
- [X] T071 [P] [US6] Crear test de servicio (marker: service, AAA) para `expediente_service.py` (filtro condado) en `backend/apps/seguimiento/tests/services/test_expediente_service.py`
- [X] T072 [P] [US6] Crear test de servicio (marker: service, AAA) para `expediente_pdf_service.py` en `backend/apps/seguimiento/tests/services/test_expediente_pdf_service.py`

### Implementation for User Story 6

- [X] T073 [US6] Implementar `historial_emergencias_service.py` (RF-SEG-005, cursor pagination) en `backend/apps/seguimiento/services/historial_emergencias_service.py`
- [X] T074 [US6] Implementar `expediente_service.py` (join completo, filtro condado cliente) en `backend/apps/seguimiento/services/expediente_service.py`
- [X] T075 [US6] Implementar `expediente_pdf_service.py` en `backend/apps/seguimiento/services/expediente_pdf_service.py`
- [X] T076 [US6] Implementar vistas historial en `backend/apps/seguimiento/views/historial_views.py`
- [X] T077 [US6] Implementar vistas expediente cliente + PDF en `backend/apps/seguimiento/views/cliente_expediente_views.py`

**Checkpoint**: US6 operativa — historial operador y expedientes cliente.

**US6 Gate**:
- [X] T078 [US6] Validar CA-SEG-008, CA-SEG-009, CA-SEG-010 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 9: User Story 7 — Jobs GPS señal perdida y depuración (Priority: P2)

**Goal**: CU-O37 + RNF-SEG-004 — alerta GPS sin modificar despacho; depuración 90d conservando 3 puntos por despacho.

**Independent Test**: Sin GPS >60s → `Dim_NotaAccidente` alerta; job depuración conserva origen/llegada/cierre.

**Measurable Criteria**: CA-SEG-011; Escenario 7; RNF-SEG-004, RNF-SEG-005.

### Tests for User Story 7

- [X] T079 [P] [US7] Crear test de servicio (marker: service, AAA) para `gps_senal_perdida_service.py` en `backend/apps/seguimiento/tests/services/test_gps_senal_perdida_service.py`
- [X] T080 [P] [US7] Crear test de servicio (marker: service, AAA) para `gps_depuracion_service.py` en `backend/apps/seguimiento/tests/services/test_gps_depuracion_service.py`
- [X] T081 [P] [US7] Crear test de job (marker: service, AAA) para `gps_senal_perdida_job.py` en `backend/apps/seguimiento/tests/jobs/test_gps_senal_perdida_job.py`
- [X] T082 [P] [US7] Crear test de job (marker: service, AAA) para `gps_depuracion_job.py` en `backend/apps/seguimiento/tests/jobs/test_gps_depuracion_job.py`

### Implementation for User Story 7

- [X] T083 [US7] Implementar `gps_senal_perdida_service.py` (O37, umbral configurable) en `backend/apps/seguimiento/services/gps_senal_perdida_service.py`
- [X] T084 [US7] Implementar `gps_depuracion_service.py` (3 puntos por iddespacho) en `backend/apps/seguimiento/services/gps_depuracion_service.py`
- [X] T085 [US7] Implementar job `gps_senal_perdida_job.py` en `backend/apps/seguimiento/jobs/gps_senal_perdida_job.py`
- [X] T086 [US7] Implementar job `gps_depuracion_job.py` en `backend/apps/seguimiento/jobs/gps_depuracion_job.py`

**Checkpoint**: US7 operativa — monitoreo y retención GPS automatizados.

**US7 Gate**:
- [X] T087 [US7] Validar CA-SEG-011 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`

---

## Phase 10: User Story 8 — Frontend Angular (Priority: P2)

**Goal**: Servicios tipados, guards y páginas consumiendo contrato REST + SSE.

**Independent Test**: quickstart §3 — mapa SSE, mi-seguimiento unidad, historial, expediente cliente PDF.

**Measurable Criteria**: RF-SEG-007 UI; guards RBAC.

### Tests for User Story 8

- [X] T088 [P] [US8] Crear test unitario (marker: unit, AAA) para `seguimiento-api.service.ts` en `frontend/src/app/modules/seguimiento/services/seguimiento-api.service.spec.ts`
- [X] T089 [P] [US8] Crear test unitario (marker: unit, AAA) para `mi-seguimiento-api.service.ts` en `frontend/src/app/modules/seguimiento/services/mi-seguimiento-api.service.spec.ts`
- [X] T090 [P] [US8] Crear test unitario (marker: unit, AAA) para `seguimiento-sse.service.ts` en `frontend/src/app/modules/seguimiento/services/seguimiento-sse.service.spec.ts`
- [X] T091 [P] [US8] Crear test unitario (marker: unit, AAA) para `expediente-cliente-api.service.ts` en `frontend/src/app/modules/seguimiento/services/expediente-cliente-api.service.spec.ts`
- [X] T092 [P] [US8] Crear test unitario (marker: unit, AAA) para guards en `frontend/src/app/modules/seguimiento/guards/operador-seguimiento.guard.spec.ts`, `unidad-seguimiento.guard.spec.ts`, `cliente-expediente.guard.spec.ts`

### Implementation for User Story 8

- [X] T093 [US8] Implementar `SeguimientoApiService` en `frontend/src/app/modules/seguimiento/services/seguimiento-api.service.ts`
- [X] T094 [US8] Implementar `MiSeguimientoApiService` en `frontend/src/app/modules/seguimiento/services/mi-seguimiento-api.service.ts`
- [X] T095 [US8] Implementar `SeguimientoSseService` (EventSource) en `frontend/src/app/modules/seguimiento/services/seguimiento-sse.service.ts`
- [X] T096 [US8] Implementar `ExpedienteClienteApiService` en `frontend/src/app/modules/seguimiento/services/expediente-cliente-api.service.ts`
- [X] T097 [US8] Implementar guards en `frontend/src/app/modules/seguimiento/guards/{operador-seguimiento,unidad-seguimiento,cliente-expediente}.guard.ts`
- [X] T098 [US8] Implementar página mapa en `frontend/src/app/modules/seguimiento/pages/mapa-seguimiento/mapa-seguimiento.page.ts`
- [X] T099 [US8] Implementar página mi-seguimiento unidad en `frontend/src/app/modules/seguimiento/pages/mi-seguimiento/mi-seguimiento.page.ts`
- [X] T100 [US8] Implementar páginas historial/expediente en `frontend/src/app/modules/seguimiento/pages/historial-emergencias/` y `detalle-expediente/`
- [X] T101 [US8] Completar rutas lazy y guards en `frontend/src/app/modules/seguimiento/seguimiento.routes.ts`

**Checkpoint**: US8 operativa — UI consumiendo contrato REST + SSE.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Validación E2E, cobertura camino crítico seguimiento→cierre, documentación.

- [X] T102 [P] Ejecutar escenarios quickstart A–I en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/quickstart.md` y documentar resultados
- [X] T103 Crear test integración camino crítico (marker: critical_path, AAA) despacho confirmado→GPS→cierre en `backend/apps/seguimiento/tests/integration/test_camino_critico_seguimiento_cierre_integration.py`
- [X] T104 [P] Verificar cobertura ≥80% servicios y ≥85% repositorios seguimiento con `pytest --cov apps/seguimiento core/repositories/seguimiento`
- [X] T105 [P] Completar matriz trazabilidad CA-SEG-001–014 en `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/traceability.md`
- [X] T106 Validar cliente HTTP 403 en `/seguimiento/mapa` (CA-SEG-010) en `backend/apps/seguimiento/tests/api/test_cliente_sin_mapa_contract.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — inicio inmediato
- **Foundational (Phase 2)**: Depende de Setup — **bloquea** todas las historias
- **US1 (Phase 3)**: Depende de Foundational — MVP GPS/llegada
- **US2 (Phase 4)**: Depende de US1 (datos GPS para mapa/SSE)
- **US3 (Phase 5)**: Depende de US1 (caso EN_ATENCION); independiente de US2
- **US4 (Phase 6)**: Depende de Foundational + despacho Confirmado
- **US5 (Phase 7)**: Depende de US3 (patrones cierre) o Foundational
- **US6 (Phase 8)**: Depende de US3 (casos CERRADOS para expedientes)
- **US7 (Phase 9)**: Depende de US1 (historial GPS); puede paralelizar con US4–US6
- **US8 (Phase 10)**: Depende de endpoints de US1–US6 según página
- **Polish (Phase 11)**: Depende de historias deseadas completas

### User Story Dependencies

```text
Foundational → US1 (GPS/llegada) → US2 (mapa/SSE)
                              ↘ US3 (cierre) → US6 (expedientes)
                              ↘ US4 (abortar) → despacho O36
                              ↘ US7 (jobs GPS)
US3 → US5 (cancelar/forzar)
US1–US6 → US8 (frontend por feature)
```

### Parallel Opportunities

- **Phase 1**: T002–T006 en paralelo tras T001
- **Phase 2**: Tests repositorio T010/T012/T014/T016 en paralelo; T018/T020/T022 en paralelo
- **US1**: T025–T028 en paralelo antes de implementación
- **US2**: T034–T038 en paralelo
- **US6**: T066–T072 en paralelo
- **US7**: T079–T082 en paralelo
- **US8**: T088–T092 en paralelo; servicios T093–T096 en paralelo

### Parallel Example: User Story 1

```bash
# Tests US1 en paralelo (deben fallar antes de implementación):
pytest backend/apps/seguimiento/tests/api/test_registrar_posicion_contract.py -v
pytest backend/apps/seguimiento/tests/api/test_registrar_llegada_contract.py -v
pytest backend/apps/seguimiento/tests/services/test_registrar_posicion_gps_service.py -v
pytest backend/apps/seguimiento/tests/services/test_registrar_llegada_service.py -v
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 + 3)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (**crítico**)
3. Completar Phase 3: US1 — GPS y llegada
4. Completar Phase 4: US2 — mapa operador SSE
5. Completar Phase 5: US3 — cierre multi-despacho
6. **VALIDAR** quickstart escenarios A–D
7. Demo camino crítico: confirmar despacho → rastrear → cerrar

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 → rastreo unidad en campo
3. US2 → visibilidad operador
4. US3 → cierre formal y SLA
5. US4–US7 → aborto, cancelación, historial, jobs
6. US8 → UI completa

### Parallel Team Strategy

| Desarrollador | Historias |
|---------------|-----------|
| A | US1 → US2 (GPS + mapa) |
| B | US3 → US5 (cierre + cancelación) |
| C | US6 + US7 (expedientes + jobs) |
| D | US8 (frontend, tras contratos US1–US3) |

---

## Notes

- Orden dentro de cada historia: **tests primero** (fallan) → servicio/repositorio → vista → integración
- Cada servicio/repositorio/job tiene par test con marker y AAA explícito
- Reutilizar repos `core/repositories/despacho/` — no duplicar `Fact_Despacho` / historial despacho
- Consumer `despacho_abortado_consumer.py` vive en `apps/despacho/` (dueño O36)
- Sin escritura directa Pinot — solo Kafka
- Commit tras cada task o grupo lógico; validar checkpoint antes de siguiente historia
