# Tasks: Evidencia en Sitio y Gestión de Disponibilidad de Unidad

**Input**: Design documents from `specs/003-operational/Emergencias/evidencia-unidad/backend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/evidencia-unidad.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing.md` + usuario); cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (CU-O78, CU-O74, CU-O77, frontend, **CU-O75/CU-O76 enriquecimiento**, **remediación Dim_Implicado ontología**) para implementación y validación independiente.


> **Capas:** este archivo es autoridad de **dominio/API**.
> Tareas con paths `frontend/src` o marcadas `[Histórico-UI]` son del monolito pre-split;
> la autoridad Interaction Capability es [`../frontend/tasks.md`](../frontend/tasks.md) (`T-FE-*`).
> No reabrir ni re-implementar `[Histórico-UI]` desde la capa backend.
> `[Bridge-FE]` = tipos/cliente tipado generado desde OpenAPI del backend (sigue anclado al contrato BE).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US6`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización de extensiones `accidentes`/`despacho`, módulo Angular y alineación contract-first.

- [X] T001 [Histórico-UI] Crear estructura de carpetas en `backend/core/repositories/evidencia/`, `backend/core/storage/`, `backend/apps/accidentes/{views,services,tests/{api,services,repositories,unit}}`, `backend/apps/despacho/{views,services,tests/{api,services,repositories,unit}}` y `frontend/src/app/modules/evidencia-unidad/{pages,services,guards}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `critical_path`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Añadir fixtures evidencia-unidad (`tecnico_auth_headers`, `unidad_auth_headers`, `admin_auth_headers`, `despacho_service_auth_headers`) en `backend/conftest.py` reutilizando JWT de auth-rbac
- [X] T004 [Bridge-FE] [P] Generar tipos TypeScript desde contrato en `frontend/src/app/modules/evidencia-unidad/services/models/evidencia-unidad.types.ts` basado en `contracts/evidencia-unidad.openapi.yaml`
- [X] T005 [Histórico-UI] [P] Crear módulo Angular lazy `evidencia-unidad.routes.ts` stub en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.ts` y registrar en `frontend/src/app/app.routes.ts`
- [X] T006 [P] Crear matriz de trazabilidad CU/RF/CA→tasks en `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot, Blob Storage, permisos RBAC y routing — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Emergencias/evidencia-unidad/backend/contracts/evidencia-unidad.openapi.yaml`
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

**Goal**: CU-O78 + RF-EVI-001/004 — unidad declara estado; consulta propia/flota; default Fuera de servicio sin historial.

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
- [X] T034 [Histórico-UI] [US1] Implementar `DisponibilidadUnidadApiService` en `frontend/src/app/modules/evidencia-unidad/services/disponibilidad-unidad-api.service.ts`
- [X] T035 [Histórico-UI] [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `disponibilidad-unidad-api.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/disponibilidad-unidad-api.service.spec.ts`
- [X] T036 [Histórico-UI] [US1] Implementar `UnidadEmergenciaDisponibilidadGuard` en `frontend/src/app/modules/evidencia-unidad/guards/unidad-emergencia-disponibilidad.guard.ts`
- [X] T037 [Histórico-UI] [P] [US1] Crear test unitario frontend (marker: unit, AAA) para guard en `frontend/src/app/modules/evidencia-unidad/guards/unidad-emergencia-disponibilidad.guard.spec.ts`
- [X] T038 [Histórico-UI] [US1] Implementar página panel disponibilidad en `frontend/src/app/modules/evidencia-unidad/pages/panel-disponibilidad/panel-disponibilidad.page.ts`

**Checkpoint**: US1 operativa — flota despachable con estados trazables.

**US1 Gate**:
- [X] T039 [US1] Validar CA-EVI-001, CA-EVI-002, CA-EVI-009 contra `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md`

---

## Phase 4: User Story 2 — Adjuntar evidencias en línea y galería (Priority: P1)

**Goal**: CU-O74 + RF-EVI-002/003/005 — subida foto/nota con caso activo; galería con RBAC; multi-unidad.

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
- [X] T050 [Histórico-UI] [US2] Implementar `EvidenciaApiService` (listar, subirFoto, registrarNota) en `frontend/src/app/modules/evidencia-unidad/services/evidencia-api.service.ts`
- [X] T051 [Histórico-UI] [P] [US2] Crear test unitario frontend (marker: unit, AAA) para `evidencia-api.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/evidencia-api.service.spec.ts`
- [X] T052 [Histórico-UI] [US2] Implementar `EvidenciaGalleryGuard` en `frontend/src/app/modules/evidencia-unidad/guards/evidencia-gallery.guard.ts`
- [X] T053 [Histórico-UI] [P] [US2] Crear test unitario frontend (marker: unit, AAA) para guard en `frontend/src/app/modules/evidencia-unidad/guards/evidencia-gallery.guard.spec.ts`
- [X] T054 [Histórico-UI] [US2] Implementar `AdministradorFlotaGuard` en `frontend/src/app/modules/evidencia-unidad/guards/administrador-flota.guard.ts`
- [X] T055 [Histórico-UI] [P] [US2] Crear test unitario frontend (marker: unit, AAA) para guard en `frontend/src/app/modules/evidencia-unidad/guards/administrador-flota.guard.spec.ts`
- [X] T056 [Histórico-UI] [US2] Implementar página galería evidencias en `frontend/src/app/modules/evidencia-unidad/pages/galeria-evidencias/galeria-evidencias.page.ts`
- [X] T057 [Histórico-UI] [US2] Implementar página captura evidencia en `frontend/src/app/modules/evidencia-unidad/pages/captura-evidencia/captura-evidencia.page.ts`

**Checkpoint**: US2 operativa — evidencia en línea consultable con RBAC.

**US2 Gate**:
- [X] T058 [US2] Validar CA-EVI-003, CA-EVI-005, CA-EVI-007, CA-EVI-008 en `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md`

---

## Phase 5: User Story 3 — Sincronización diferida offline (Priority: P2)

**Goal**: CU-O77 + RF-EVI-006 — batch sync parcial; reintento automático; evidencia local solo en capturador.

**Independent Test**: Cliente envía 3 ítems pendientes; 1 falla Blob → 2 sincronizados + 1 pendiente; galería local fusiona pendientes; otro usuario solo ve sincronizados.

**Measurable Criteria**: CA-EVI-004, CA-EVI-006; Escenarios 3, 4, 4b; RNF-EVI-004, RNF-EVI-005.

### Tests for User Story 3

- [X] T059 [P] [US3] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/accidentes/{id}/evidencias/sincronizar` en `backend/apps/accidentes/tests/api/test_sincronizar_evidencia_contract.py`
- [X] T060 [P] [US3] Crear test de servicio (marker: service, AAA) para `sincronizar_evidencia_service.py` en `backend/apps/accidentes/tests/services/test_sincronizar_evidencia_service.py`
- [X] T061 [Histórico-UI] [P] [US3] Crear test unitario frontend (marker: unit, AAA) para `evidencia-offline-store.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.spec.ts`

### Implementation for User Story 3

- [X] T062 [US3] Implementar `sincronizar_evidencia_service.py` (batch parcial, fechahora preservada) en `backend/apps/accidentes/services/sincronizar_evidencia_service.py`
- [X] T063 [US3] Añadir vista `POST .../evidencias/sincronizar` en `backend/apps/accidentes/views/evidencia_views.py`
- [X] T064 [Histórico-UI] [US3] Implementar `EvidenciaOfflineStoreService` (IndexedDB, `sincronizado=false` local) en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.ts`
- [X] T065 [Histórico-UI] [US3] Extender `EvidenciaApiService.sincronizarPendientes()` y merge galería local+servidor en `frontend/src/app/modules/evidencia-unidad/services/evidencia-api.service.ts`
- [X] T066 [Histórico-UI] [US3] Integrar auto-sync al reconectar en `frontend/src/app/modules/evidencia-unidad/services/evidencia-sync-scheduler.service.ts`
- [X] T067 [Histórico-UI] [P] [US3] Crear test unitario frontend (marker: unit, AAA) para scheduler en `frontend/src/app/modules/evidencia-unidad/services/evidencia-sync-scheduler.service.spec.ts`
- [X] T068 [Histórico-UI] [US3] Actualizar galería para indicador pendiente/sincronizado en `frontend/src/app/modules/evidencia-unidad/pages/galeria-evidencias/galeria-evidencias.page.ts`

**Checkpoint**: US3 operativa — offline-first con reintento resiliente.

**US3 Gate**:
- [X] T069 [US3] Validar CA-EVI-004, CA-EVI-006 en `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md`

---

## Phase 6: User Story 4 — Integración frontend y rutas (Priority: P2)

**Goal**: Módulo Angular completo con lazy loading, guards por rol y navegación operativa.

**Independent Test**: Técnico accede galería/captura; Unidad accede panel disponibilidad; Admin accede flota; rutas protegidas redirigen sin rol.

**Measurable Criteria**: RN-EVI-012, RN-EVI-015; quickstart sección 3.

### Tests for User Story 4

- [X] T070 [Histórico-UI] [P] [US4] Crear test unitario frontend (marker: unit, AAA) para rutas lazy en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.spec.ts`

### Implementation for User Story 4

- [X] T071 [Histórico-UI] [US4] Completar rutas lazy con guards en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.ts`
- [X] T072 [Histórico-UI] [US4] Registrar entradas sidebar por rol en `frontend/src/app/core/sidebar/evidencia-unidad-menu.config.ts`
- [X] T072b [Histórico-UI] [US4] Corrección post-auditoría: `evidencia-unidad-menu.config.ts` nunca se conectó al sidebar real (`frontend/src/app/shared/layout/app-shell.component.ts` usa `NAV_LINKS` de `nav-links.ts`, no `menuItemsForRoles()`). Se elimina el config muerto; se añade rol `Tecnico` a la entrada "Lista de accidentes" en `nav-links.ts` y se crea `accidentesLecturaGuard` (roles: Operador, Tecnico, Administrador) para las rutas `lista`/`:idaccidente` en `frontend/src/app/modules/accidentes/accidentes.routes.ts`, habilitando el flujo Lista → Detalle → "Ver galería completa" → "Capturar evidencia" para el Técnico de Campo.

**Checkpoint**: US4 operativa — UX integrada en app operacional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Auditoría, quickstart E2E, cobertura y documentación.

- [X] T073 Implementar servicio auditoría evidencia/disponibilidad en `backend/apps/accidentes/services/audit_evidencia_service.py`
- [X] T074 [P] Crear test de servicio (marker: service, AAA) para `audit_evidencia_service.py` en `backend/apps/accidentes/tests/services/test_audit_evidencia_service.py`
- [X] T075 [P] Crear test integración camino crítico disponibilidad→despacho (marker: critical_path, AAA) en `backend/apps/despacho/tests/integration/test_disponibilidad_despacho_integration.py`
- [X] T076 Ejecutar y documentar escenarios A–I de `specs/003-operational/Emergencias/evidencia-unidad/backend/quickstart.md` en `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md`
- [X] T077 [P] Verificar cobertura ≥80% servicios y ≥85% repositorios con `pytest --cov apps/accidentes apps/despacho core/repositories/evidencia core/storage --cov-report=term-missing`
- [X] T078 [P] Actualizar nota extensión Emergencias en `.specify/docs/architecture/project-structure.md` (evidencia en accidentes, disponibilidad declarada en despacho)

---

## Phase 8: User Story 5 — Enriquecimiento estructurado en sitio (Priority: P1) 🎯 CU-O75/CU-O76

**Goal**: CU-O75/CU-O76 + RF-EVI-007/008/009 — Técnico (o Unidad) registra clima/período, elementos físicos y conductores/vehículos; catálogos; sync offline ampliada; consulta enriquecimiento.

**Independent Test**: Técnico en caso activo hace PUT clima + POST elemento físico + POST conductor; GET enriquecimiento refleja datos; caso cerrado → 422; rol sin permiso → 403; misma `identificacion` reutiliza `idconductor`.

**Measurable Criteria**: CA-EVI-010, CA-EVI-011, CA-EVI-012; Escenarios 7, 8, 9; RN-EVI-016–019; RNF-EVI-007, RNF-EVI-008.

### Foundational delta (bloquea US5)

- [X] T079 Validar contrato OpenAPI extendido (paths Enriquecimiento + Catalogos) en `specs/003-operational/Emergencias/evidencia-unidad/backend/contracts/evidencia-unidad.openapi.yaml`
- [X] T080 [P] Registrar topics Kafka `Dim_Conductor_topic`, `Dim_Vehiculo_topic`, `Fact_Conductor_Accidente_topic` en `backend/config/settings.py` (`KAFKA_TOPICS`)
- [X] T081 [Bridge-FE] [P] Regenerar tipos TypeScript desde contrato en `frontend/src/app/modules/evidencia-unidad/services/models/evidencia-unidad.types.ts`
- [X] T082 [P] Implementar repositorio catálogos enriquecimiento (periodos, climas, elementos físicos, estados conductor) en `backend/core/repositories/evidencia/catalogo_enriquecimiento_repository.py`
- [X] T083 [P] Crear test de repositorio (marker: repository, AAA) para catálogos en `backend/apps/accidentes/tests/repositories/test_catalogo_enriquecimiento_repository.py`
- [X] T084 Reutilizar/extender escritura puente clima en `backend/core/repositories/accidentes/elemento_climatico_repository.py` (lectura por `idaccidente` + upsert activo único RN-EVI-017) para consumo desde servicios evidencia
- [X] T085 [P] Extender `backend/core/repositories/accidentes/elemento_fisico_repository.py` con listado activos, soft-delete `activo=false`
- [X] T086 Implementar repositorio `Dim_Conductor` en `backend/core/repositories/evidencia/conductor_repository.py` (find_by_identificacion, create)
- [X] T087 [P] Crear test de repositorio (marker: repository, AAA) para `conductor_repository.py` en `backend/apps/accidentes/tests/repositories/test_conductor_repository.py`
- [X] T088 Implementar repositorio `Dim_Vehiculo` en `backend/core/repositories/evidencia/vehiculo_repository.py`
- [X] T089 [P] Crear test de repositorio (marker: repository, AAA) para `vehiculo_repository.py` en `backend/apps/accidentes/tests/repositories/test_vehiculo_repository.py`
- [X] T090 Implementar repositorio `Fact_Conductor_Accidente` en `backend/core/repositories/evidencia/conductor_accidente_repository.py`
- [X] T091 [P] Crear test de repositorio (marker: repository, AAA) para `conductor_accidente_repository.py` en `backend/apps/accidentes/tests/repositories/test_conductor_accidente_repository.py`
- [X] T092 Extender permisos escritura enriquecimiento (`IsTecnicoCampoOrUnidad`) y lectura (`IsTecnicoCampoOrUnidadOrAdmin`) en `backend/apps/accidentes/permissions.py`
- [X] T093 [P] Crear test unitario (marker: unit, AAA) para permisos enriquecimiento en `backend/apps/accidentes/tests/unit/test_enriquecimiento_permissions.py`

### Tests for User Story 5

- [X] T094 [P] [US5] Crear test de contrato API (marker: api, AAA) para `GET/PUT .../enriquecimiento/clima` en `backend/apps/accidentes/tests/api/test_enriquecimiento_clima_contract.py`
- [X] T095 [P] [US5] Crear test de contrato API (marker: api, AAA) para elementos físicos en `backend/apps/accidentes/tests/api/test_enriquecimiento_elementos_fisicos_contract.py`
- [X] T096 [P] [US5] Crear test de contrato API (marker: api, AAA) para conductores en `backend/apps/accidentes/tests/api/test_enriquecimiento_conductores_contract.py`
- [X] T097 [P] [US5] Crear test de contrato API (marker: api, AAA) para `GET .../enriquecimiento` en `backend/apps/accidentes/tests/api/test_consultar_enriquecimiento_contract.py`
- [X] T098 [P] [US5] Crear test de contrato API (marker: api, AAA) para catálogos en `backend/apps/accidentes/tests/api/test_catalogos_enriquecimiento_contract.py`
- [X] T099 [P] [US5] Crear test de servicio (marker: service, AAA) para `enriquecimiento_clima_service.py` en `backend/apps/accidentes/tests/services/test_enriquecimiento_clima_service.py`
- [X] T100 [P] [US5] Crear test de servicio (marker: service, AAA) para `enriquecimiento_elemento_fisico_service.py` en `backend/apps/accidentes/tests/services/test_enriquecimiento_elemento_fisico_service.py`
- [X] T101 [P] [US5] Crear test de servicio (marker: service, AAA) para `enriquecimiento_conductor_service.py` (RN-EVI-019 reuso identificación) en `backend/apps/accidentes/tests/services/test_enriquecimiento_conductor_service.py`
- [X] T102 [P] [US5] Crear test de servicio (marker: service, AAA) para sync enriquecimiento en `backend/apps/accidentes/tests/services/test_sincronizar_enriquecimiento_service.py`

### Implementation for User Story 5

- [X] T103 [US5] Implementar `enriquecimiento_clima_service.py` en `backend/apps/accidentes/services/enriquecimiento_clima_service.py`
- [X] T104 [US5] Implementar `enriquecimiento_elemento_fisico_service.py` en `backend/apps/accidentes/services/enriquecimiento_elemento_fisico_service.py`
- [X] T105 [US5] Implementar `enriquecimiento_conductor_service.py` en `backend/apps/accidentes/services/enriquecimiento_conductor_service.py`
- [X] T106 [US5] Implementar `consulta_enriquecimiento_service.py` en `backend/apps/accidentes/services/consulta_enriquecimiento_service.py`
- [X] T107 [US5] Extender `sincronizar_evidencia_service.py` para procesar campo multipart `enriquecimiento` en `backend/apps/accidentes/services/sincronizar_evidencia_service.py`
- [X] T108 [US5] Implementar vistas enriquecimiento + catálogos en `backend/apps/accidentes/views/enriquecimiento_views.py`
- [X] T109 [US5] Registrar rutas `/accidentes/{id}/enriquecimiento/*` y `/catalogos/*` en `backend/apps/accidentes/views/urls.py` y `backend/config/urls.py`
- [X] T110 [US5] Extender auditoría (`enriquecer_clima`, `enriquecer_elemento_fisico`, `registrar_conductor_accidente`) en `backend/apps/accidentes/services/audit_evidencia_service.py`
- [X] T111 [Histórico-UI] [US5] Implementar `EnriquecimientoApiService` en `frontend/src/app/modules/evidencia-unidad/services/enriquecimiento-api.service.ts`
- [X] T112 [Histórico-UI] [P] [US5] Crear test unitario frontend (marker: unit, AAA) para `enriquecimiento-api.service.spec.ts` en `frontend/src/app/modules/evidencia-unidad/services/enriquecimiento-api.service.spec.ts`
- [X] T113 [Histórico-UI] [US5] Extender `evidencia-offline-store.service.ts` con colas locales clima/físico/conductor **cifrando PII** (`LocalConductorAccidente` vía Web Crypto; RN-EVI-020/021, RNF-EVI-009) en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.ts`
- [X] T114 [Histórico-UI] [US5] Extender sync scheduler para enriquecer pendientes y **borrar borradores PII tras sync OK** en `frontend/src/app/modules/evidencia-unidad/services/evidencia-sync-scheduler.service.ts`
- [X] T115 [Histórico-UI] [US5] Implementar página enriquecimiento en sitio en `frontend/src/app/modules/evidencia-unidad/pages/enriquecimiento-accidente/enriquecimiento-accidente.page.ts`
- [X] T116 [Histórico-UI] [US5] Registrar ruta lazy reutilizando **`EvidenciaGalleryGuard`** (Decision 12; no crear guard nuevo) en `frontend/src/app/modules/evidencia-unidad/evidencia-unidad.routes.ts`
- [X] T117 [Histórico-UI] [US5] Añadir entrada de navegación Técnico/Unidad hacia enriquecimiento en `frontend/src/app/shared/layout/nav-links.ts` (flujo desde detalle accidente)

**Checkpoint**: US5 operativa — Técnico completa datos estructurados del siniestro en campo.

**US5 Gate**:
- [X] T118 [US5] Validar CA-EVI-010, CA-EVI-011, CA-EVI-012, **CA-EVI-013, CA-EVI-014** + escenarios 7–9 en `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md`
- [X] T119 [P] [US5] Verificar cobertura ≥80% servicios enriquecimiento con pytest `--cov` sobre `apps/accidentes/services/enriquecimiento_*` y repos evidencia
- [X] T120 [P] Documentar escenarios J–L (clima, físico, conductores) + **M (PII offline cifrado)** en `specs/003-operational/Emergencias/evidencia-unidad/backend/quickstart.md`
- [X] T121 [Histórico-UI] [P] [US5] Crear test unitario frontend (marker: unit, AAA) que **falla si PII conductor se persiste en claro** en IndexedDB en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.spec.ts`
- [X] T122 [Histórico-UI] [US5] Validar conformidad UI enriquecimiento con `.specify/docs/design/design-system.md` (RNF-EVI-010 / CA-EVI-014) en `frontend/src/app/modules/evidencia-unidad/pages/enriquecimiento-accidente/enriquecimiento-accidente.page.ts`
- [X] T123 [P] [US5] Documentar checklist cifrado at-rest Pinot/backups (RNF-EVI-009 servidor) en `specs/003-operational/Emergencias/evidencia-unidad/backend/quickstart.md` § Security
- [X] T124 [P] [US5] Añadir smoke p95 catálogos ≤2s y alta conductor ≤3s (RNF-EVI-007/008, marker: slow) en `backend/apps/accidentes/tests/performance/test_enriquecimiento_p95.py`
- [X] T125 [US5] Extender audit service con eventos `consultar_conductores_accidente` / `desactivar_conductor_accidente` en `backend/apps/accidentes/services/audit_evidencia_service.py`
- [X] T126 [Histórico-UI] [US5] Remediación RF-EVI-009: UI captura campos opcionales `Dim_Conductor`/`Dim_Vehiculo` + clarificar required/optional en `spec.md`/`data-model.md` (`enriquecimiento-accidente.page.ts/html`)
- [X] T127 [Histórico-UI] [US5] Reorganizar UI enriquecimiento: paneles separados Conductor vs Vehículo + lista registrada con columnas (`enriquecimiento-accidente.page.html`)

---

## Phase 9: User Story 6 — Implicados no conductores (Priority: P1) 🎯 CU-O75/CU-O76 / RF-EVI-010

**Goal**: Técnico registra `Dim_Implicado` por `idaccidente` (sin `iddespacho`), offline+sync, mismo RBAC que conductores.

**Independent Test**: POST implicado → listar en GET enriquecimiento; soft-delete; sync diferida. *(Modelo PII inicial T128–T136; **superseded** por Phase 10 ontología.)*

### Tests (fallan primero)

- [X] T128 [P] [US6] Crear test contrato API implicados en `backend/apps/accidentes/tests/api/test_enriquecimiento_implicados_contract.py`
- [X] T129 [P] [US6] Crear test servicio implicados en `backend/apps/accidentes/tests/services/test_enriquecimiento_implicado_service.py`
- [X] T130 [P] [US6] Crear test repositorio `Dim_Implicado` en `backend/apps/accidentes/tests/repositories/test_implicado_repository.py`

### Implementation

- [X] T131 [US6] Implementar `implicado_repository.py` en `backend/core/repositories/evidencia/implicado_repository.py` + topic Kafka
- [X] T132 [US6] Implementar `enriquecimiento_implicado_service.py` en `backend/apps/accidentes/services/enriquecimiento_implicado_service.py`
- [X] T133 [US6] Extender vistas/rutas `/enriquecimiento/implicados` en `enriquecimiento_views.py` / `urls.py`
- [X] T134 [US6] Integrar implicados en `consulta_enriquecimiento_service.py` y sync CU-O77
- [X] T135 [US6] Extender `EnriquecimientoApiService` + offline store (PII cifrada) + UI panel Implicados en `enriquecimiento-accidente.page.*`
- [X] T136 [US6] Actualizar `traceability.md` / `quickstart.md` con CA/escenarios RF-EVI-010

**Checkpoint**: US6 — implicados en sitio operativos *(payload a remediación Phase 10)*.

---

## Phase 10: Remediación US6 — `Dim_Implicado` → ontología (Priority: P1) 🎯 RF-EVI-010 / Decision 13

**Goal**: Alinear código/tests/FE al diagrama y `database/esquemas.json` (`tipoimplicado`, `genero`, `estadoimplicado`, `edad`, `activo`). **Sin** PII de identidad. **Sin** modificar `database/esquemas.json` ni `tablas.json`.

**Independent Test (CA-EVI-015)**: POST `{ tipoimplicado, estadoimplicado, genero?, edad? }` → 201 sin `identificacion`/`nombres`; GET enriquecimiento lista campos ontología; soft-delete; offline LocalImplicado sin AES-GCM; Kafka payload ⊆ schema Pinot.

### Tests (TDD — actualizar fixtures; deben fallar contra código PII actual)

- [X] T137 [P] [US6] Reescribir contract test ontología en `backend/apps/accidentes/tests/api/test_enriquecimiento_implicados_contract.py` (body/asserts `estadoimplicado`/`edad`; rechazar payload solo-PII)
- [X] T138 [P] [US6] Reescribir service test ontología en `backend/apps/accidentes/tests/services/test_enriquecimiento_implicado_service.py` (requeridos tipo+estado; enum `estadoimplicado`; sin identificacion)
- [X] T139 [P] [US6] Reescribir repository test ontología en `backend/apps/accidentes/tests/repositories/test_implicado_repository.py` (assert keys payload = schema Pinot)

### Implementation backend

- [X] T140 [US6] Remediat `create`/`soft_delete` en `backend/core/repositories/evidencia/implicado_repository.py` al payload ontología (quitar PII/`idusuario` de negocio)
- [X] T141 [US6] Remediat validación/alta en `backend/apps/accidentes/services/enriquecimiento_implicado_service.py` (`ESTADOS_IMPLICADO`, opcionales `genero`/`edad`)
- [X] T142 [US6] Remediat sync batch implicados en `backend/apps/accidentes/services/sincronizar_evidencia_service.py` (mapear solo campos ontología)
- [X] T143 [US6] Ajustar passthrough/views si validan body PII en `backend/apps/accidentes/views/enriquecimiento_views.py`

### Implementation frontend

- [X] T144 [Histórico-UI] [P] [US6] Alinear tipos `RegistrarImplicadoRequest` / `ImplicadoItem` / offline en `frontend/src/app/modules/evidencia-unidad/services/models/evidencia-unidad.types.ts`
- [X] T145 [Histórico-UI] [P] [US6] Remediat `EnriquecimientoApiService` + specs en `frontend/src/app/modules/evidencia-unidad/services/enriquecimiento-api.service.ts` (+ `.spec.ts`)
- [X] T146 [Histórico-UI] [US6] Remediat `LocalImplicado` sin cifrado PII en `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.ts` (+ `.spec.ts`)
- [X] T147 [Histórico-UI] [US6] Remediat UI form/lista implicados (tipo + estado + género/edad; quitar cédula/nombres/lesionado) en `frontend/src/app/modules/evidencia-unidad/pages/enriquecimiento-accidente/enriquecimiento-accidente.page.ts` y `.html`

### Polish remediación

- [X] T148 [P] [US6] Cerrar CA-EVI-015 / Escenario N en `specs/003-operational/Emergencias/evidencia-unidad/backend/traceability.md` y verificar `quickstart.md`
- [X] T149 [P] [US6] Marcar gap #12 cerrado en `flujoscorreguidos/flujo-emergencias-canonico.md` tras tests verdes
- [X] T150 [US6] Verificar **no** hay diff en `database/esquemas.json` / `database/tablas.json` por esta remediación; correr pytest implicados (+ sync si aplica)

**Checkpoint**: App = OpenAPI = Pinot = diagrama. Listo para `/speckit-implement` Phase 10.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — iniciar de inmediato
- **Foundational (Phase 2)**: Depende de Setup — **bloquea** US1–US4
- **US1 (Phase 3)**: Depende de Foundational — MVP despacho
- **US2 (Phase 4)**: Depende de Foundational — paralelo a US1 tras Phase 2
- **US3 (Phase 5)**: Depende de US2 (servicios evidencia + API base)
- **US4 (Phase 6)**: Depende de US1 + US2 (guards y páginas)
- **Polish (Phase 7)**: Depende de US1–US4 (histórico; ya cerrado)
- **US5 (Phase 8)**: Depende de Phase 2 + US2 (caso activo / permisos evidencia); puede avanzar tras T079–T093. Extiende US3 sync (T107)
- **US6 (Phase 9)**: Depende de US5 — impl. inicial (histórico; payload PII)
- **US6 remediación (Phase 10)**: Depende de Phase 9 + spec/plan Decision 13 — **siguiente incremento ejecutable**

### User Story Dependencies

```text
Phase 2 (Foundational)
    ├── US1 (CU-O78 disponibilidad) ──┐
    └── US2 (CU-O74 evidencia línea) ─┼── US4 (frontend integración)
              └── US3 (CU-O77 sync) ──┘
                    └── US5 (CU-O75/CU-O76 enriquecimiento)
                          └── US6 (implicados) ── Phase 10 remediación ontología
```

### Within Each User Story

1. Tests de contrato/servicio/repositorio **antes** de implementación (fallan primero)
2. Repositorios (Phase 2 / T079–T093) → Servicios → Vistas → Frontend
3. Cada servicio/repositorio: implementación + test emparejado (AAA)
4. **Phase 10:** T137–T139 en paralelo → T140–T143 secuencial backend → T144–T145 paralelo FE types/API → T146–T147 offline/UI → T148–T150 polish

### Parallel Opportunities

- Phase 1: T002–T006 en paralelo
- Phase 2: tests T009, T011, T013, T015, T017, T019, T021, T023 en paralelo tras su implementación
- US1 y US2 pueden avanzar en paralelo tras Phase 2 (equipos distintos)
- US5: T082–T091 repos/tests en paralelo; T094–T102 contract/service tests en paralelo; T103–T105 servicios en paralelo tras repos
- **Phase 10:** T137–T139 [P]; T144–T145 [P]; T148–T149 [P]
- Tests marcados [P] dentro de cada fase son paralelizables

### Parallel Example: Phase 10 (tests ontología)

```bash
pytest backend/apps/accidentes/tests/api/test_enriquecimiento_implicados_contract.py -v
pytest backend/apps/accidentes/tests/services/test_enriquecimiento_implicado_service.py -v
pytest backend/apps/accidentes/tests/repositories/test_implicado_repository.py -v
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1 + Phase 2
2. Completar Phase 3 (CU-O78 disponibilidad)
3. **VALIDAR**: CA-EVI-001, CA-EVI-002 — unidad operativa para despacho
4. Demo: cambio Activa→Ocupada reflejado en ≤5s

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 disponibilidad → MVP camino crítico despacho
3. US2 evidencia en línea → valor documental inmediato
4. US3 sync offline → operación en campo sin cobertura
5. US4 + Polish → integración UX y auditoría
6. **US5 CU-O75/CU-O76** → enriquecimiento estructurado (clima, físicos, conductores) por Técnico
7. **US6** → implicados (T128–T136)
8. **Phase 10** → remediación ontología Dim_Implicado (T137–T150) ← **siguiente**

### Suggested MVP Scope (histórico)

**US1 (CU-O78)** — gestión de disponibilidad es prerequisito Safety para `despacho-inteligente` (RNF-EVI-003).

### Suggested next increment (2026-07-29)

**Phase 10** — alinear app a ontología `Dim_Implicado` (Decision 13 / CA-EVI-015). No tocar Pinot DDL.

---

## Notes

- Patrón AAA obligatorio en todos los tests; usar fixtures `mock_pinot`, `mock_kafka`, `auth_headers` de `backend/conftest.py`
- Blob es escritura externa; no viola regla Kafka-only para dominio Pinot
- `Dim_NotaAccidente` compartida con registro-accidente (tipo `escalamiento` vs tipos campo)
- Puentes clima/físico compartidos con `registro-accidente`; dueño de flujo campo = este módulo (CU-O75/CU-O76)
- Topics nuevos conductor/vehículo deben añadirse a seed/ingest Pinot si aún no están cableados
- **PII conductores:** nunca persistir `identificacion`/nombres en claro en IndexedDB (RN-EVI-020); ver Decision 11
- **`Dim_Implicado`:** sin PII de identidad; offline sin AES-GCM; ver Decision 13 / RF-EVI-010 reescrito 2026-07-29
- Contrato OpenAPI y `data-model.md` ya reflejan ontología; Phase 10 solo código/tests/FE
- Commit sugerido tras cada par implementación+test o al cerrar cada checkpoint

---

---

> **Histórico-UI:** las fases/tareas Angular de este archivo quedan como registro pre-split. Trabajo UI nuevo → capa [`../frontend/`](../frontend/).
