# Tasks: Evidencia en Sitio y Gestión de Disponibilidad de Unidad

**Input**: Design documents from `specs/003-operational/Emergencias/evidencia-unidad/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/evidencia-unidad.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing.md` + usuario); cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (CU-O30, CU-O27, CU-O43, frontend) para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US4`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización de extensiones `accidentes`/`despacho`, módulo Angular y alineación contract-first.

- [X] T001 Crear estructura de carpetas en `backend/core/repositories/evidencia/`, `backend/core/storage/`, `backend/apps/accidentes/{views,services,tests/{api,services,repositories,unit}}`, `backend/apps/despacho/{views,services,tests/{api,services,repositories,unit}}` y `frontend/src/app/modules/evidencia-unidad/{pages,services,guards}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `critical_path`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Añadir fixtures evidencia-unidad (`tecnico_auth_headers`, `unidad_auth_headers`, `admin_auth_headers`, `despacho_service_auth_headers`) en `backend/conftest.py` reutilizando JWT de auth-rbac
- [X] T004 [P] Generar tipos TypeScript desde contrato en `frontend/src/app/modules/evidencia-unidad/services/models/evidencia-unidad.types.ts` basado en `contracts/evidencia-unidad.openapi.yaml`
- [X] T005 [P] Crear módulo Angular lazy `evidencia-unidad.routes.ts` stub en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.ts` y registrar en `frontend/src/app/app.routes.ts`
- [X] T006 [P] Crear matriz de trazabilidad CU/RF/CA→tasks en `specs/003-operational/Emergencias/evidencia-unidad/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot, Blob Storage, permisos RBAC y routing — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Emergencias/evidencia-unidad/contracts/evidencia-unidad.openapi.yaml`
- [X] T008 Implementar repositorio lectura/escritura `Dim_EvidenciaFoto` en `backend/core/repositories/evidencia/evidencia_foto_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: repository, AAA) para `evidencia_foto_repository.py` en `backend/apps/accidentes/tests/repositories/test_evidencia_foto_repository.py`
- [X] T010 Implementar repositorio `Dim_NotaAccidente` (tipos campo) en `backend/core/repositories/evidencia/nota_campo_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: repository, AAA) para `nota_campo_repository.py` en `backend/apps/accidentes/tests/repositories/test_nota_campo_repository.py`
- [X] T012 Implementar repositorio precondición caso activo en `backend/core/repositories/evidencia/accidente_read_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: repository, AAA) para `accidente_read_repository.py` en `backend/apps/accidentes/tests/repositories/test_accidente_read_repository.py`
- [X] T014 Implementar repositorio `Fact_HistorialEstadoUnidad` en `backend/core/repositories/despacho/historial_estado_unidad_repository.py`
- [X] T015 [P] Crear test de repositorio (marker: repository, AAA) para `historial_estado_unidad_repository.py` en `backend/apps/despacho/tests/repositories/test_historial_estado_unidad_repository.py`
- [X] T016 Implementar repositorio `Dim_UnidadEmergencia` lectura flota en `backend/core/repositories/despacho/unidad_emergencia_repository.py`
- [X] T017 [P] Crear test de repositorio (marker: repository, AAA) para `unidad_emergencia_repository.py` en `backend/apps/despacho/tests/repositories/test_unidad_emergencia_repository.py`
- [X] T018 Implementar `BlobStorageService` (contenedor `evidencia-accidentes`) en `backend/core/storage/blob_storage_service.py`
- [X] T019 [P] Crear test de servicio (marker: service, AAA) para `blob_storage_service.py` en `backend/apps/accidentes/tests/services/test_blob_storage_service.py`
- [X] T020 Implementar permisos evidencia `IsTecnicoCampoOrUnidadOrAdmin` en `backend/apps/accidentes/permissions.py`
- [X] T021 [P] Crear test unitario (marker: unit, AAA) para permisos evidencia en `backend/apps/accidentes/tests/unit/test_evidencia_permissions.py`
- [X] T022 Implementar permisos disponibilidad (`IsUnidadEmergenciaOwn`, `IsAdministradorOrDespachoService`, `IsUnidadEmergenciaSelfOrAdmin`) en `backend/apps/despacho/permissions.py`
- [X] T023 [P] Crear test unitario (marker: unit, AAA) para permisos disponibilidad en `backend/apps/despacho/tests/unit/test_disponibilidad_permissions.py`
- [X] T024 Registrar rutas evidencia en `backend/apps/accidentes/views/urls.py` y rutas disponibilidad en `backend/apps/despacho/views/urls.py`; incluir en `backend/config/urls.py`

**Checkpoint**: Repositorios, Blob, permisos y routing listos.

---

## Phase 3: User Story 1 — Gestionar disponibilidad de unidad (Priority: P1) 🎯 MVP

**Goal**: CU-O30 + RF-EVI-001/004 — unidad declara estado; consulta propia/flota; default Fuera de servicio sin historial.

**Independent Test**: Unidad cambia a Ocupada vía `POST /mi-unidad-emergencia/disponibilidad`; consulta refleja estado; Admin lista flota; Técnico recibe 403.

**Measurable Criteria**: CA-EVI-001, CA-EVI-002, CA-EVI-009; Escenarios 1, 6; RNF-EVI-003, RNF-EVI-006.

### Tests for User Story 1

- [X] T025 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/mi-unidad-emergencia/disponibilidad` en `backend/apps/despacho/tests/api/test_declarar_mi_disponibilidad_contract.py`
- [X] T026 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/mi-unidad-emergencia/disponibilidad` en `backend/apps/despacho/tests/api/test_consultar_mi_disponibilidad_contract.py`
- [X] T027 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/unidades-emergencia` en `backend/apps/despacho/tests/api/test_listar_unidades_contract.py`
- [X] T028 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/unidades-emergencia/{id}/historial-estado` en `backend/apps/despacho/tests/api/test_historial_estado_contract.py`
- [X] T029 [P] [US1] Crear test de servicio (marker: service, AAA) para `disponibilidad_unidad_service.py` en `backend/apps/despacho/tests/services/test_disponibilidad_unidad_service.py`
- [X] T030 [P] [US1] Crear test de servicio (marker: service, AAA) para `consulta_flota_service.py` en `backend/apps/despacho/tests/services/test_consulta_flota_service.py`

### Implementation for User Story 1

- [X] T031 [US1] Implementar `disponibilidad_unidad_service.py` (declarar estado, resolver actual, default Fuera de servicio) en `backend/apps/despacho/services/disponibilidad_unidad_service.py`
- [X] T032 [US1] Implementar `consulta_flota_service.py` en `backend/apps/despacho/services/consulta_flota_service.py`
- [X] T033 [US1] Implementar vistas disponibilidad en `backend/apps/despacho/views/disponibilidad_views.py` (`/mi-unidad-emergencia/*`, `/unidades-emergencia/*`)
- [X] T034 [US1] Implementar `DisponibilidadUnidadApiService` en `frontend/src/app/modules/evidencia-unidad/services/disponibilidad-unidad-api.service.ts`
- [X] T035 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `disponibilidad-unidad-api.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/disponibilidad-unidad-api.service.spec.ts`
- [X] T036 [US1] Implementar `UnidadEmergenciaDisponibilidadGuard` en `frontend/src/app/modules/evidencia-unidad/guards/unidad-emergencia-disponibilidad.guard.ts`
- [X] T037 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para guard en `frontend/src/app/modules/evidencia-unidad/guards/unidad-emergencia-disponibilidad.guard.spec.ts`
- [X] T038 [US1] Implementar página panel disponibilidad en `frontend/src/app/modules/evidencia-unidad/pages/panel-disponibilidad/panel-disponibilidad.page.ts`

**Checkpoint**: US1 operativa — flota despachable con estados trazables.

**US1 Gate**:
- [X] T039 [US1] Validar CA-EVI-001, CA-EVI-002, CA-EVI-009 contra `specs/003-operational/Emergencias/evidencia-unidad/traceability.md`

---

## Phase 4: User Story 2 — Adjuntar evidencias en línea y galería (Priority: P1)

**Goal**: CU-O27 + RF-EVI-002/003/005 — subida foto/nota con caso activo; galería con RBAC; multi-unidad.

**Independent Test**: Técnico sube 3 fotos y 1 nota; `GET evidencias` retorna items sincronizados; rol no autorizado → 403; caso cerrado → 422.

**Measurable Criteria**: CA-EVI-003, CA-EVI-005, CA-EVI-007, CA-EVI-008; Escenarios 2, 5; RNF-EVI-002.

### Tests for User Story 2

- [X] T040 [P] [US2] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/accidentes/{id}/evidencias` en `backend/apps/accidentes/tests/api/test_listar_evidencias_contract.py`
- [X] T041 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{id}/evidencias/fotos` en `backend/apps/accidentes/tests/api/test_subir_foto_contract.py`
- [X] T042 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{id}/evidencias/notas` en `backend/apps/accidentes/tests/api/test_registrar_nota_contract.py`
- [X] T043 [P] [US2] Crear test de servicio (marker: service, AAA) para `evidencia_foto_service.py` en `backend/apps/accidentes/tests/services/test_evidencia_foto_service.py`
- [X] T044 [P] [US2] Crear test de servicio (marker: service, AAA) para `nota_campo_service.py` en `backend/apps/accidentes/tests/services/test_nota_campo_service.py`
- [X] T045 [P] [US2] Crear test de servicio (marker: service, AAA) para `consulta_evidencia_service.py` en `backend/apps/accidentes/tests/services/test_consulta_evidencia_service.py`

### Implementation for User Story 2

- [X] T046 [US2] Implementar `evidencia_foto_service.py` (validación caso activo, compresión, Blob→Kafka) en `backend/apps/accidentes/services/evidencia_foto_service.py`
- [X] T047 [US2] Implementar `nota_campo_service.py` en `backend/apps/accidentes/services/nota_campo_service.py`
- [X] T048 [US2] Implementar `consulta_evidencia_service.py` (solo sincronizados, filtro tipo, RBAC) en `backend/apps/accidentes/services/consulta_evidencia_service.py`
- [X] T049 [US2] Implementar vistas evidencia en `backend/apps/accidentes/views/evidencia_views.py`
- [X] T050 [US2] Implementar `EvidenciaApiService` (listar, subirFoto, registrarNota) en `frontend/src/app/modules/evidencia-unidad/services/evidencia-api.service.ts`
- [X] T051 [P] [US2] Crear test unitario frontend (marker: unit, AAA) para `evidencia-api.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/evidencia-api.service.spec.ts`
- [X] T052 [US2] Implementar `EvidenciaGalleryGuard` en `frontend/src/app/modules/evidencia-unidad/guards/evidencia-gallery.guard.ts`
- [X] T053 [P] [US2] Crear test unitario frontend (marker: unit, AAA) para guard en `frontend/src/app/modules/evidencia-unidad/guards/evidencia-gallery.guard.spec.ts`
- [X] T054 [US2] Implementar `AdministradorFlotaGuard` en `frontend/src/app/modules/evidencia-unidad/guards/administrador-flota.guard.ts`
- [X] T055 [P] [US2] Crear test unitario frontend (marker: unit, AAA) para guard en `frontend/src/app/modules/evidencia-unidad/guards/administrador-flota.guard.spec.ts`
- [X] T056 [US2] Implementar página galería evidencias en `frontend/src/app/modules/evidencia-unidad/pages/galeria-evidencias/galeria-evidencias.page.ts`
- [X] T057 [US2] Implementar página captura evidencia en `frontend/src/app/modules/evidencia-unidad/pages/captura-evidencia/captura-evidencia.page.ts`

**Checkpoint**: US2 operativa — evidencia en línea consultable con RBAC.

**US2 Gate**:
- [X] T058 [US2] Validar CA-EVI-003, CA-EVI-005, CA-EVI-007, CA-EVI-008 en `specs/003-operational/Emergencias/evidencia-unidad/traceability.md`

---

## Phase 5: User Story 3 — Sincronización diferida offline (Priority: P2)

**Goal**: CU-O43 + RF-EVI-006 — batch sync parcial; reintento automático; evidencia local solo en capturador.

**Independent Test**: Cliente envía 3 ítems pendientes; 1 falla Blob → 2 sincronizados + 1 pendiente; galería local fusiona pendientes; otro usuario solo ve sincronizados.

**Measurable Criteria**: CA-EVI-004, CA-EVI-006; Escenarios 3, 4, 4b; RNF-EVI-004, RNF-EVI-005.

### Tests for User Story 3

- [X] T059 [P] [US3] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{id}/evidencias/sincronizar` en `backend/apps/accidentes/tests/api/test_sincronizar_evidencia_contract.py`
- [X] T060 [P] [US3] Crear test de servicio (marker: service, AAA) para `sincronizar_evidencia_service.py` en `backend/apps/accidentes/tests/services/test_sincronizar_evidencia_service.py`
- [X] T061 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `evidencia-offline-store.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.spec.ts`

### Implementation for User Story 3

- [X] T062 [US3] Implementar `sincronizar_evidencia_service.py` (batch parcial, fechahora preservada) en `backend/apps/accidentes/services/sincronizar_evidencia_service.py`
- [X] T063 [US3] Añadir vista `POST .../evidencias/sincronizar` en `backend/apps/accidentes/views/evidencia_views.py`
- [X] T064 [US3] Implementar `EvidenciaOfflineStoreService` (IndexedDB, `sincronizado=false` local) en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.ts`
- [X] T065 [US3] Extender `EvidenciaApiService.sincronizarPendientes()` y merge galería local+servidor en `frontend/src/app/modules/evidencia-unidad/services/evidencia-api.service.ts`
- [X] T066 [US3] Integrar auto-sync al reconectar en `frontend/src/app/modules/evidencia-unidad/services/evidencia-sync-scheduler.service.ts`
- [X] T067 [P] [US3] Crear test unitario frontend (marker: unit, AAA) para scheduler en `frontend/src/app/modules/evidencia-unidad/services/evidencia-sync-scheduler.service.spec.ts`
- [X] T068 [US3] Actualizar galería para indicador pendiente/sincronizado en `frontend/src/app/modules/evidencia-unidad/pages/galeria-evidencias/galeria-evidencias.page.ts`

**Checkpoint**: US3 operativa — offline-first con reintento resiliente.

**US3 Gate**:
- [X] T069 [US3] Validar CA-EVI-004, CA-EVI-006 en `specs/003-operational/Emergencias/evidencia-unidad/traceability.md`

---

## Phase 6: User Story 4 — Integración frontend y rutas (Priority: P2)

**Goal**: Módulo Angular completo con lazy loading, guards por rol y navegación operativa.

**Independent Test**: Técnico accede galería/captura; Unidad accede panel disponibilidad; Admin accede flota; rutas protegidas redirigen sin rol.

**Measurable Criteria**: RN-EVI-012, RN-EVI-015; quickstart sección 3.

### Tests for User Story 4

- [X] T070 [P] [US4] Crear test unitario frontend (marker: unit, AAA) para rutas lazy en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.spec.ts`

### Implementation for User Story 4

- [X] T071 [US4] Completar rutas lazy con guards en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.ts`
- [X] T072 [US4] Registrar entradas sidebar por rol en `frontend/src/app/core/sidebar/evidencia-unidad-menu.config.ts`
- [X] T072b [US4] Corrección post-auditoría: `evidencia-unidad-menu.config.ts` nunca se conectó al sidebar real (`frontend/src/app/shared/layout/app-shell.component.ts` usa `NAV_LINKS` de `nav-links.ts`, no `menuItemsForRoles()`). Se elimina el config muerto; se añade rol `Tecnico` a la entrada "Lista de accidentes" en `nav-links.ts` y se crea `accidentesLecturaGuard` (roles: Operador, Tecnico, Administrador) para las rutas `lista`/`:idaccidente` en `frontend/src/app/modules/accidentes/accidentes.routes.ts`, habilitando el flujo Lista → Detalle → "Ver galería completa" → "Capturar evidencia" para el Técnico de Campo.

**Checkpoint**: US4 operativa — UX integrada en app operacional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Auditoría, quickstart E2E, cobertura y documentación.

- [X] T073 Implementar servicio auditoría evidencia/disponibilidad en `backend/apps/accidentes/services/audit_evidencia_service.py`
- [X] T074 [P] Crear test de servicio (marker: service, AAA) para `audit_evidencia_service.py` en `backend/apps/accidentes/tests/services/test_audit_evidencia_service.py`
- [X] T075 [P] Crear test integración camino crítico disponibilidad→despacho (marker: critical_path, AAA) en `backend/apps/despacho/tests/integration/test_disponibilidad_despacho_integration.py`
- [X] T076 Ejecutar y documentar escenarios A–I de `specs/003-operational/Emergencias/evidencia-unidad/quickstart.md` en `specs/003-operational/Emergencias/evidencia-unidad/traceability.md`
- [X] T077 [P] Verificar cobertura ≥80% servicios y ≥85% repositorios con `pytest --cov apps/accidentes apps/despacho core/repositories/evidencia core/storage --cov-report=term-missing`
- [X] T078 [P] Actualizar nota extensión Emergencias en `.specify/docs/architecture/project-structure.md` (evidencia en accidentes, disponibilidad declarada en despacho)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — iniciar de inmediato
- **Foundational (Phase 2)**: Depende de Setup — **bloquea** todas las historias
- **US1 (Phase 3)**: Depende de Foundational — MVP despacho
- **US2 (Phase 4)**: Depende de Foundational — paralelo a US1 tras Phase 2
- **US3 (Phase 5)**: Depende de US2 (servicios evidencia + API base)
- **US4 (Phase 6)**: Depende de US1 + US2 (guards y páginas)
- **Polish (Phase 7)**: Depende de US1–US4 deseados

### User Story Dependencies

```text
Phase 2 (Foundational)
    ├── US1 (CU-O30 disponibilidad) ──┐
    └── US2 (CU-O27 evidencia línea) ─┼── US4 (frontend integración)
              └── US3 (CU-O43 sync) ──┘
```

### Within Each User Story

1. Tests de contrato/servicio/repositorio **antes** de implementación (fallan primero)
2. Repositorios (Phase 2) → Servicios → Vistas → Frontend
3. Cada servicio/repositorio: implementación + test emparejado (AAA)

### Parallel Opportunities

- Phase 1: T002–T006 en paralelo
- Phase 2: tests T009, T011, T013, T015, T017, T019, T021, T023 en paralelo tras su implementación
- US1 y US2 pueden avanzar en paralelo tras Phase 2 (equipos distintos)
- Tests marcados [P] dentro de cada fase son paralelizables

### Parallel Example: User Story 2

```bash
# Tests API en paralelo:
T040 test_listar_evidencias_contract.py
T041 test_subir_foto_contract.py
T042 test_registrar_nota_contract.py

# Tests servicio en paralelo:
T043 test_evidencia_foto_service.py
T044 test_nota_campo_service.py
T045 test_consulta_evidencia_service.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1 + Phase 2
2. Completar Phase 3 (CU-O30 disponibilidad)
3. **VALIDAR**: CA-EVI-001, CA-EVI-002 — unidad operativa para despacho
4. Demo: cambio Activa→Ocupada reflejado en ≤5s

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 disponibilidad → MVP camino crítico despacho
3. US2 evidencia en línea → valor documental inmediato
4. US3 sync offline → operación en campo sin cobertura
5. US4 + Polish → integración UX y auditoría

### Suggested MVP Scope

**US1 (CU-O30)** — gestión de disponibilidad es prerequisito Safety para `despacho-inteligente` (RNF-EVI-003).

---

## Notes

- Patrón AAA obligatorio en todos los tests; usar fixtures `mock_pinot`, `mock_kafka`, `auth_headers` de `backend/conftest.py`
- Blob es escritura externa; no viola regla Kafka-only para dominio Pinot
- `Dim_NotaAccidente` compartida con registro-accidente (tipo `escalamiento` vs tipos campo)
- Commit sugerido tras cada par implementación+test o al cerrar cada checkpoint
