# Tasks: Registro de Accidentes en Tiempo Real

**Input**: Design documents from `specs/003-operational/Emergencias/registro-accidente/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/registro-accidente.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing.md` + usuario); cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (CU-O21, consulta/edición, O32, O41, O40) para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US5`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del módulo `accidentes` y alineación contract-first.

- [X] T001 Crear estructura de carpetas en `backend/apps/accidentes/{views,services,tests/{api,services,repositories}}`, `backend/core/repositories/accidentes/` y `frontend/src/app/modules/accidentes/{pages,services,guards}`
- [X] T002 [P] Registrar app Django `accidentes` en `backend/config/settings.py` y stub `backend/apps/accidentes/apps.py`
- [X] T003 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `critical_path`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T004 [P] Añadir fixtures accidentes (`operador_auth_headers`, `unidad_auth_headers`) en `backend/conftest.py` reutilizando JWT de auth-rbac
- [X] T005 [P] Generar tipos TypeScript desde contrato en `frontend/src/app/modules/accidentes/services/models/accidente.types.ts` basado en `contracts/registro-accidente.openapi.yaml`
- [X] T006 [P] Crear matriz de trazabilidad CU/RF/CA→tasks en `specs/003-operational/Emergencias/registro-accidente/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura Kafka/repositorios base, permisos y auditoría — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Emergencias/registro-accidente/contracts/registro-accidente.openapi.yaml`
- [X] T008 Implementar adaptador Kafka escritura accidentes en `backend/core/repositories/accidentes/kafka_writer.py`
- [X] T009 [P] Crear test de repositorio (marker: repository, AAA) para `kafka_writer.py` en `backend/apps/accidentes/tests/repositories/test_kafka_writer.py`
- [X] T010 Implementar repositorio lectura/escritura `Fact_Accidente` en `backend/core/repositories/accidentes/accidente_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: repository, AAA) para `accidente_repository.py` en `backend/apps/accidentes/tests/repositories/test_accidente_repository.py`
- [X] T012 Implementar repositorio `Fact_AccidenteTipoEstadoAccidente` en `backend/core/repositories/accidentes/estado_accidente_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: repository, AAA) para `estado_accidente_repository.py` en `backend/apps/accidentes/tests/repositories/test_estado_accidente_repository.py`
- [X] T014 Implementar repositorio cobertura regional en `backend/core/repositories/accidentes/region_operativa_repository.py`
- [X] T015 [P] Crear test de repositorio (marker: repository, AAA) para `region_operativa_repository.py` en `backend/apps/accidentes/tests/repositories/test_region_operativa_repository.py`
- [X] T016 Implementar permisos DRF `OperadorEmergenciasPermission` y `UnidadEmergenciaPermission` en `backend/apps/accidentes/permissions.py`
- [X] T017 [P] Crear test unitario (marker: unit, AAA) para `permissions.py` en `backend/apps/accidentes/tests/unit/test_permissions.py`
- [X] T018 Implementar servicio de auditoría accidentes en `backend/apps/accidentes/services/audit_accidente_service.py`
- [X] T019 [P] Crear test de servicio (marker: service, AAA) para `audit_accidente_service.py` en `backend/apps/accidentes/tests/services/test_audit_accidente_service.py`
- [X] T020 Implementar envelope de respuesta/error estándar en `backend/apps/accidentes/views/response_envelope.py`
- [X] T021 Registrar rutas base API v1 accidentes en `backend/apps/accidentes/views/urls.py` y `backend/config/urls.py`

**Checkpoint**: Kafka, repositorios core, permisos y routing listos.

---

## Phase 3: User Story 1 — Registrar accidente y confirmar reporte (Priority: P1) 🎯 MVP

**Goal**: CU-O21 + RF-REG-006 geocodificación + RF-REG-010 confirmar BORRADOR→REPORTADO con promoción condicional.

**Independent Test**: Operador registra accidente sin advertencias → `REPORTADO`; con advertencias forzadas → `BORRADOR` + confirmación manual → `REPORTADO`.

**Measurable Criteria**: CA-REG-001, CA-REG-002, CA-REG-003, CA-REG-006, CA-REG-013, CA-REG-014; Escenarios 1, 2, 5, 9.

### Tests for User Story 1

- [X] T022 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes` en `backend/apps/accidentes/tests/api/test_registrar_accidente_contract.py`
- [X] T023 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes/geocodificacion-inversa` en `backend/apps/accidentes/tests/api/test_geocodificacion_contract.py`
- [X] T024 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{id}/confirmar-reporte` en `backend/apps/accidentes/tests/api/test_confirmar_reporte_contract.py`
- [X] T025 [P] [US1] Crear test de servicio (marker: service, AAA) para `validacion_accidente_service.py` en `backend/apps/accidentes/tests/services/test_validacion_accidente_service.py`
- [X] T026 [P] [US1] Crear test de servicio (marker: service, AAA) para `cobertura_operativa_service.py` en `backend/apps/accidentes/tests/services/test_cobertura_operativa_service.py`
- [X] T027 [P] [US1] Crear test de servicio (marker: service, AAA) para `geocodificacion_inversa_service.py` en `backend/apps/accidentes/tests/services/test_geocodificacion_inversa_service.py`
- [X] T028 [P] [US1] Crear test de servicio (marker: service, AAA) para `registro_accidente_service.py` en `backend/apps/accidentes/tests/services/test_registro_accidente_service.py`
- [X] T029 [P] [US1] Crear test de servicio (marker: service, AAA) para `confirmar_reporte_service.py` en `backend/apps/accidentes/tests/services/test_confirmar_reporte_service.py`
- [X] T030 [P] [US1] Crear test de repositorio (marker: repository, AAA) para puentes climáticos en `backend/apps/accidentes/tests/repositories/test_elemento_climatico_repository.py`
- [X] T031 [P] [US1] Crear test de repositorio (marker: repository, AAA) para puentes físicos en `backend/apps/accidentes/tests/repositories/test_elemento_fisico_repository.py`
- [X] T032 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `OperadorEmergenciasGuard` en `frontend/src/app/modules/accidentes/guards/operador-emergencias.guard.spec.ts`

### Implementation for User Story 1

- [X] T033 [US1] Implementar `validacion_accidente_service.py` en `backend/apps/accidentes/services/validacion_accidente_service.py`
- [X] T034 [US1] Implementar `cobertura_operativa_service.py` en `backend/apps/accidentes/services/cobertura_operativa_service.py`
- [X] T035 [US1] Implementar `geocodificacion_inversa_service.py` (adaptador Nominatim) en `backend/apps/accidentes/services/geocodificacion_inversa_service.py`
- [X] T036 [US1] Implementar repositorio `Dim_ElementoClimaticosAccidente` en `backend/core/repositories/accidentes/elemento_climatico_repository.py`
- [X] T037 [US1] Implementar repositorio `Dim_ElementoFisicoAccidente` en `backend/core/repositories/accidentes/elemento_fisico_repository.py`
- [X] T038 [US1] Implementar `registro_accidente_service.py` (promoción condicional BORRADOR/REPORTADO) en `backend/apps/accidentes/services/registro_accidente_service.py`
- [X] T039 [US1] Implementar `confirmar_reporte_service.py` en `backend/apps/accidentes/services/confirmar_reporte_service.py`
- [X] T040 [US1] Implementar vistas `POST /accidentes`, `GET geocodificacion-inversa` en `backend/apps/accidentes/views/accidente_views.py`
- [X] T041 [US1] Implementar vista `POST confirmar-reporte` en `backend/apps/accidentes/views/accion_views.py`
- [X] T042 [US1] Implementar `AccidenteApiService.registrar()` y `confirmarReporte()` en `frontend/src/app/modules/accidentes/services/accidente-api.service.ts`
- [X] T043 [US1] Implementar `GeocodificacionApiService` en `frontend/src/app/modules/accidentes/services/geocodificacion-api.service.ts`
- [X] T044 [US1] Implementar `OperadorEmergenciasGuard` en `frontend/src/app/modules/accidentes/guards/operador-emergencias.guard.ts`
- [X] T045 [US1] Implementar página registro con manejo advertencias/retrospectivo en `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`
- [X] T045b [US1] Implementar persistencia local (draft en localStorage), indicador de sincronización ("En vivo"/"Reconectando…"/"Sin conexión — guardado localmente") y restauración automática en `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`, según RNF-REG-006 y `.specify/docs/design/design-system.md` §2 (resiliencia de captura en campo)
- [X] T045c [P] [US1] Crear test unitario frontend (marker: unit, AAA) para persistencia local/restauración/`syncStatus` de `registro-accidente.page.ts` en `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.spec.ts`

**Checkpoint**: US1 operativa — MVP de entrada al camino crítico.

**US1 Gate**:
- [X] T046 [US1] Validar CA-REG-001, CA-REG-002, CA-REG-003, CA-REG-006, CA-REG-013, CA-REG-014 en `specs/003-operational/Emergencias/registro-accidente/traceability.md`
- [X] T046b [US1] Validar RNF-REG-006 (resiliencia de captura) en `specs/003-operational/Emergencias/registro-accidente/traceability.md`

---

## Phase 4: User Story 2 — Consulta, detalle y edición (Priority: P1)

**Goal**: RF-REG-005 lista activos, detalle con historial, edición complementaria y campos críticos con confirmación.

**Independent Test**: Operador lista/filtra accidentes activos, ve detalle y edita `numvehiculos` con log de auditoría.

**Measurable Criteria**: CA-REG-005, CA-REG-007; Escenarios 4.

### Tests for User Story 2

- [X] T047 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes` en `backend/apps/accidentes/tests/api/test_listar_accidentes_contract.py`
- [X] T048 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes/{id}` en `backend/apps/accidentes/tests/api/test_detalle_accidente_contract.py`
- [X] T049 [P] [US2] Crear test de contrato API (marker: api, AAA) para `PATCH /api/v1/accidentes/{id}` en `backend/apps/accidentes/tests/api/test_actualizar_accidente_contract.py`
- [X] T050 [P] [US2] Crear test de servicio (marker: service, AAA) para `consulta_accidente_service.py` en `backend/apps/accidentes/tests/services/test_consulta_accidente_service.py`
- [X] T051 [P] [US2] Crear test unitario frontend (marker: unit, AAA) para `AccidenteApiService` list/detail/patch en `frontend/src/app/modules/accidentes/services/accidente-api.service.spec.ts`

### Implementation for User Story 2

- [X] T052 [US2] Implementar `consulta_accidente_service.py` (list cursor, detalle, patch) en `backend/apps/accidentes/services/consulta_accidente_service.py`
- [X] T053 [US2] Extender `accidente_views.py` con `GET list`, `GET detail`, `PATCH` en `backend/apps/accidentes/views/accidente_views.py`
- [X] T054 [US2] Implementar página lista con filtros en `frontend/src/app/modules/accidentes/pages/lista-accidentes/lista-accidentes.page.ts`
- [X] T055 [US2] Implementar página detalle/edición en `frontend/src/app/modules/accidentes/pages/detalle-accidente/detalle-accidente.page.ts`
- [X] T056 [US2] Registrar rutas lazy en `frontend/src/app/modules/accidentes/accidentes.routes.ts` y `frontend/src/app/app.routes.ts`

**Checkpoint**: US2 funcional e independiente de US3–US5.

**US2 Gate**:
- [X] T057 [US2] Validar CA-REG-005 y CA-REG-007 en `specs/003-operational/Emergencias/registro-accidente/traceability.md`

---

## Phase 5: User Story 3 — Descartar caso en BORRADOR (Priority: P2)

**Goal**: CU-O32 descarte antes de despacho.

**Independent Test**: Caso BORRADOR → descartar → `DESCARTADO`, `activo=false`, HTTP 409 si no BORRADOR.

**Measurable Criteria**: CA-REG-009; Escenario 6.

### Tests for User Story 3

- [X] T058 [P] [US3] Crear test de contrato API (marker: api, AAA) para `POST .../descartar` en `backend/apps/accidentes/tests/api/test_descartar_caso_contract.py`
- [X] T059 [P] [US3] Crear test de servicio (marker: service, AAA) para `descartar_caso_service.py` en `backend/apps/accidentes/tests/services/test_descartar_caso_service.py`

### Implementation for User Story 3

- [X] T060 [US3] Implementar `descartar_caso_service.py` en `backend/apps/accidentes/services/descartar_caso_service.py`
- [X] T061 [US3] Implementar vista `POST descartar` en `backend/apps/accidentes/views/accion_views.py`
- [X] T062 [US3] Añadir acción descartar en `frontend/src/app/modules/accidentes/pages/detalle-accidente/detalle-accidente.page.ts` vía `AccidenteApiService.descartar()`

**Checkpoint**: US3 completa.

**US3 Gate**:
- [X] T063 [US3] Validar CA-REG-009 en `specs/003-operational/Emergencias/registro-accidente/traceability.md`

---

## Phase 6: User Story 4 — Fusionar reportes duplicados (Priority: P2)

**Goal**: CU-O41 con detección duplicados, padre preseleccionado (más antiguo) y fusión confirmada.

**Independent Test**: 409 duplicado con sugerencias → fusión → duplicado `FUSIONADO` con `idaccidenteorigen`.

**Measurable Criteria**: CA-REG-004, CA-REG-011; Escenarios 3, 8.

### Tests for User Story 4

- [X] T064 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST .../fusionar` en `backend/apps/accidentes/tests/api/test_fusionar_reportes_contract.py`
- [X] T065 [P] [US4] Crear test de servicio (marker: service, AAA) para `fusionar_reportes_service.py` en `backend/apps/accidentes/tests/services/test_fusionar_reportes_service.py`
- [X] T066 [P] [US4] Crear test de servicio (marker: service, AAA) para detección duplicados 50m/5min en `backend/apps/accidentes/tests/services/test_duplicado_detection.py`

### Implementation for User Story 4

- [X] T067 [US4] Implementar lógica detección duplicados en `backend/apps/accidentes/services/validacion_accidente_service.py` (extensión RN-REG-005/010b)
- [X] T068 [US4] Implementar `fusionar_reportes_service.py` en `backend/apps/accidentes/services/fusionar_reportes_service.py`
- [X] T069 [US4] Implementar vista `POST fusionar` en `backend/apps/accidentes/views/accion_views.py`
- [X] T070 [US4] Implementar modal fusión con padre preseleccionado en `frontend/src/app/modules/accidentes/pages/registro-accidente/duplicado-fusion.dialog.ts`

**Checkpoint**: US4 completa.

**US4 Gate**:
- [X] T071 [US4] Validar CA-REG-004 y CA-REG-011 en `specs/003-operational/Emergencias/registro-accidente/traceability.md`

---

## Phase 7: User Story 5 — Escalar severidad en sitio (Priority: P2)

**Goal**: CU-O40 en ASIGNADO/EN_ATENCIÓN con despacho confirmado; incremento heridos/fallecidos.

**Independent Test**: Unidad escala severidad → nota `escalamiento`, estado sin cambio; 422 si decremento; 409 sin despacho.

**Measurable Criteria**: CA-REG-010, CA-REG-012; Escenario 7.

### Tests for User Story 5

- [X] T072 [P] [US5] Crear test de contrato API (marker: api, AAA) para `POST .../escalar-severidad` en `backend/apps/accidentes/tests/api/test_escalar_severidad_contract.py`
- [X] T073 [P] [US5] Crear test de repositorio (marker: repository, AAA) para `despacho_read_repository.py` en `backend/apps/accidentes/tests/repositories/test_despacho_read_repository.py`
- [X] T074 [P] [US5] Crear test de repositorio (marker: repository, AAA) para `nota_accidente_repository.py` en `backend/apps/accidentes/tests/repositories/test_nota_accidente_repository.py`
- [X] T075 [P] [US5] Crear test de servicio (marker: service, AAA) para `escalar_severidad_service.py` en `backend/apps/accidentes/tests/services/test_escalar_severidad_service.py`
- [X] T076 [P] [US5] Crear test unitario frontend (marker: unit, AAA) para `UnidadEmergenciaGuard` en `frontend/src/app/modules/accidentes/guards/unidad-emergencia.guard.spec.ts`

### Implementation for User Story 5

- [X] T077 [US5] Implementar repositorio lectura `Fact_Despacho` en `backend/core/repositories/accidentes/despacho_read_repository.py`
- [X] T078 [US5] Implementar repositorio `Dim_NotaAccidente` en `backend/core/repositories/accidentes/nota_accidente_repository.py`
- [X] T079 [US5] Implementar `escalar_severidad_service.py` en `backend/apps/accidentes/services/escalar_severidad_service.py`
- [X] T080 [US5] Implementar vista `POST escalar-severidad` en `backend/apps/accidentes/views/accion_views.py`
- [X] T081 [US5] Implementar `UnidadEmergenciaGuard` en `frontend/src/app/modules/accidentes/guards/unidad-emergencia.guard.ts`
- [X] T082 [US5] Implementar `AccidenteApiService.escalarSeveridad()` y UI escalamiento en `frontend/src/app/modules/accidentes/pages/detalle-accidente/escalar-severidad.panel.ts`

**Checkpoint**: US5 completa.

**US5 Gate**:
- [X] T083 [US5] Validar CA-REG-010 y CA-REG-012 en `specs/003-operational/Emergencias/registro-accidente/traceability.md`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Camino crítico, performance, quickstart y trazabilidad final.

- [X] T084 [P] Crear test integración camino crítico registro (marker: critical_path, AAA) en `backend/apps/accidentes/tests/integration/test_registro_critical_path.py`
- [X] T085 [P] Crear test performance registro p95 ≤ 500ms (marker: slow) en `backend/apps/accidentes/tests/performance/test_registro_accidente_p95.py`
- [X] T086 [P] Documentar evidencia RNF-REG-005 (<2s validaciones) en `specs/003-operational/Emergencias/registro-accidente/quickstart.md`
- [X] T087 [P] Actualizar mapeo RF/RNF/CA→Task IDs en `specs/003-operational/Emergencias/registro-accidente/traceability.md`
- [X] T088 Ejecutar validación E2E escenarios A–G de `specs/003-operational/Emergencias/registro-accidente/quickstart.md`
- [X] T089 Validar CA-REG-008 (403 roles) y cobertura pytest ≥80% servicios en `backend/apps/accidentes/tests/`
- [X] T090 [P] Validar conformidad de páginas frontend (registro, lista, detalle, modal fusión) con `.specify/docs/design/design-system.md`: componente de feedback correcto por acción, estados de carga/vacío/error, iconografía semántica de severidad (Tabler). Resuelto en Phase 11: sistema `NotificationService`/`ToastHostComponent`/`AlertHostComponent` + íconos de severidad consistentes en registro y lista. **Snackbar con [Deshacer] para CU-O32/CU-O41 queda pendiente** — no existe endpoint de reversión en el backend; se usa Toast (sin acción) en su lugar (ver Phase 11). Accesibilidad (contraste ambos temas) sigue sin verificación formal — modo oscuro diferido.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — inicio inmediato
- **Foundational (Phase 2)**: Depende de Setup — **bloquea** US1–US5
- **US1 (Phase 3)**: Depende de Foundational — **MVP**
- **US2 (Phase 4)**: Depende de Foundational + repositorios T010–T013 (puede paralelizarse tras US1 parcial)
- **US3–US5 (Phases 5–7)**: Dependen de Foundational; US4 extiende validación US1; US5 independiente de US3/US4
- **Polish (Phase 8)**: Depende de US1–US5 deseadas

### User Story Dependencies

| Historia | CU/RF | Depende de |
|----------|-------|------------|
| US1 | O21, RF-REG-010, geocodificación | Phase 2 |
| US2 | RF-REG-005 | Phase 2 (+ accidentes existentes de US1 para demo) |
| US3 | O32 | Phase 2, casos BORRADOR |
| US4 | O41 | US1 validación duplicados |
| US5 | O40 | Phase 2, seed `Fact_Despacho` |

### Within Each User Story

1. Tests (contrato/servicio/repositorio) **antes** de implementación — deben fallar primero (TDD)
2. Repositorios → servicios → vistas → frontend
3. Gate de CA antes de siguiente historia

### Parallel Opportunities

- **Phase 1**: T002–T006 en paralelo tras T001
- **Phase 2**: Tests T009, T011, T013, T015, T017, T019 en paralelo tras su implementación
- **US1**: T022–T032 (todos tests) en paralelo; T025–T031 en paralelo
- **US2–US5**: Tests marcados [P] por historia en paralelo
- **Equipos**: Tras Phase 2, US3/US5 pueden avanzar en paralelo con US2/US4

### Parallel Example: User Story 1

```bash
# Tests de contrato en paralelo:
pytest backend/apps/accidentes/tests/api/test_registrar_accidente_contract.py -m api -v
pytest backend/apps/accidentes/tests/api/test_geocodificacion_contract.py -m api -v
pytest backend/apps/accidentes/tests/api/test_confirmar_reporte_contract.py -m api -v

# Tests de servicio en paralelo:
pytest backend/apps/accidentes/tests/services/test_validacion_accidente_service.py -m service -v
pytest backend/apps/accidentes/tests/services/test_registro_accidente_service.py -m service -v
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1 + Phase 2
2. Completar Phase 3 (US1)
3. **STOP y validar** Escenarios 1, 2, 5, 9 + confirmar reporte
4. Demo: accidente en `REPORTADO` listo para despacho-inteligente

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 → registro MVP
3. US2 → operación consulta/edición
4. US3 → descarte
5. US4 → fusión duplicados
6. US5 → escalamiento unidad
7. Polish → camino crítico + performance

---

## Notes

- Todos los tests backend usan patrón AAA con comentarios `# Arrange` / `# Act` / `# Assert`
- Repositorios: mock `mock_pinot` + `mock_kafka` de `conftest.py`
- Servicios: repos mockeados; sin I/O real salvo marker `integration`
- API: DRF `APIClient` + `operador_auth_headers` / `unidad_auth_headers`
- Frontend: Jasmine + `HttpClientTestingModule` para servicios/guards
- Escrituras: verificar publicación Kafka, nunca INSERT directo Pinot

---

## Phase 9: UI Shell & Location Catalog (conformidad design-system.md + RF-REG-006 punto 3)

**Purpose**: Documentar a posteriori el trabajo de shell/diseño y de selección de ubicación en cascada
realizado durante la iteración de UX de `registro-accidente`, para que `tasks.md` refleje el código real
(hallazgo E1 de `/speckit-analyze`). No introduce requisitos nuevos: todo aquí deriva de
`design-system.md` (shell/header/sidebar) y de RF-REG-006 punto 3 / Escenario 5 de `spec.md` (cascada
manual de ubicación) ya existentes.

- [X] T091 [P] Adoptar Tailwind CSS como sistema de utilidades CSS del frontend (`frontend/postcss.config.js` o equivalente, `frontend/src/styles.css`), documentado en `.specify/docs/infra/infrastructure.md`
- [X] T092 [P] Implementar `AppShellComponent` (sidebar por rol agrupado, header, drawer mobile) en `frontend/src/app/shared/layout/app-shell.component.ts` y `nav-links.ts`, conforme a `design-system.md` §5
- [X] T093 [P] Migrar `LoginPage`, `PasswordResetPage`, `HomePage` a Tailwind, manteniendo comportamiento existente
- [X] T094 [P] Implementar `LocationPickerMapComponent` (Leaflet + OpenStreetMap, decisión documentada en `.specify/docs/infra/infrastructure.md` §6) en `frontend/src/app/shared/ui/map/location-picker-map.component.ts`, integrado en `registro-accidente.page.ts` para reemplazar la captura manual de lat/lon
- [X] T095 [P] Implementar cascada de selección manual de ubicación (país→estado→condado→ciudad→calle, RF-REG-006 punto 3 / Escenario 5): contrato OpenAPI (`GET /accidentes/paises|estados|condados|ciudades|calles`), backend (`ubicacion_catalogo_repository.py`, `ubicacion_catalogo_service.py`, `ubicacion_catalogo_views.py`) y frontend (`ubicacion-catalogo-api.service.ts`, cascada en `registro-accidente.page.ts`)
- [X] T096 [P] Tests de la cascada de ubicación: repositorio, servicio y contrato API (`backend/apps/accidentes/tests/{repositories,services,api}/test_ubicacion_catalogo_*.py`)
- [X] T097 Completar campos opcionales de RF-REG-002 en el formulario de registro (vehículos, heridos, víctimas, fallecidos, tipo de reporte) en `registro-accidente.page.ts`

**Checkpoint**: Shell, Tailwind, mapa y cascada de ubicación documentados y con tests.

---

## Phase 10: Filtros RF-REG-005 y rediseño de lista/detalle (design-system.md conformidad)

**Purpose**: Documentar a posteriori la extensión de filtros de `GET /accidentes` (ya declarados en el
contrato OpenAPI pero sin implementar) y el rediseño de `ListaAccidentesPage`/`DetalleAccidentePage`
conforme a `design-system.md` §"Tablas operativas".

- [X] T098 [P] Implementar filtros `estado`, `activo`, `fecha_desde`, `fecha_hasta`, `idciudad`, `idestadoregion` en `backend/core/repositories/accidentes/accidente_repository.py` (`list_activos`), `backend/apps/accidentes/services/consulta_accidente_service.py` y `backend/apps/accidentes/views/accidente_views.py`
- [X] T099 [P] Tests de los filtros nuevos (repositorio/servicio/API) en `backend/apps/accidentes/tests/{repositories,services,api}/test_accidente_repository.py|test_consulta_accidente_service.py|test_listar_accidentes_contract.py`
- [X] T100 [P] Agregar íconos `eye`/`alert-octagon`/`alert-triangle`/`alert-circle`/`circle-check`/`info-circle`/`refresh` a `TablerIconComponent`
- [X] T101 Reconstruir `ListaAccidentesPage` (tabla conforme a design-system.md: header mayúsculas, badges de severidad ícono+color, columna de acción con ojo 44×44, colapso a cards en mobile, estados carga/vacío/error) y `AccidenteApiService.listar()` con objeto de filtros
- [X] T102 [P] Crear `lista-accidentes.page.spec.ts` (no existía)
- [X] T103 Re-estilar `DetalleAccidentePage` con el mismo lenguaje visual (cards, badges, estados carga/error), sin cambiar su lógica/datos

**Checkpoint**: Lista y detalle conformes al design system, filtros del contrato completamente implementados.

---

## Phase 11: Sistema Toast/Alert (cierre de T090)

**Purpose**: Construir el sistema de feedback exigido por `design-system.md` §5 que faltaba por completo
— todos los mensajes de éxito/error eran banners estáticos, no Toast/Alert reales.

- [X] T104 [P] Implementar `NotificationService` (`frontend/src/app/shared/notifications/notification.service.ts`) con colas de `toast()`/`alert()` y auto-dismiss según tabla de `design-system.md`
- [X] T105 [P] Implementar `ToastHostComponent` y `AlertHostComponent`, montados una vez en `AppShellComponent`
- [X] T106 Rewire de mensajes en `registro-accidente.page.ts` y `detalle-accidente.page.ts`: éxito → Toast, fallo de guardado/conexión → Alert. Actualizar specs correspondientes.
- [X] T107 Agregar íconos de severidad (`circle-check`/`alert-circle`/`alert-triangle`/`alert-octagon`) a los botones de severidad en `registro-accidente.page.ts` (antes solo color, ahora consistente con `lista-accidentes.page.ts`)
- [ ] T108 **Pendiente, no fingido** (excepción abierta — revisión programada: 2026-08-15, dueño: Bryan Lombeida): Snackbar real con [Deshacer] para descarte (CU-O32) y fusión (CU-O41) — requiere un endpoint de reversión que hoy no existe en el backend (`descartar`/`fusionar` no tienen contraparte de "deshacer"). Mientras tanto, esas acciones usan Toast sin acción. Definir el endpoint de reversión (contract-first) antes de implementar el Snackbar real. Ver también G10 en `.specify/docs/changelog.md`.

**Checkpoint**: Toast/Alert funcionando en registro y detalle; iconografía de severidad consistente en toda la app.
