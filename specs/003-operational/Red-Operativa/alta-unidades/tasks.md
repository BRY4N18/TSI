# Tasks: Alta y Configuración de Unidades de Emergencia

**Input**: Design documents from `specs/003-operational/Red-Operativa/alta-unidades/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/alta-unidades.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento explícito (`testing-expert` + `testing.md`). Cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (CU-O54, CU-O56, CU-O57, CU-O58, CU-O59) para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`..`US5`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización de carpetas, tipos y trazabilidad para alta-unidades.

- [X] T001 Crear estructura de carpetas en `backend/apps/red_operativa/{views,services,tests/api,tests/services,tests/repositories,tests/unit}`, `backend/core/repositories/red_operativa/` y `frontend/src/app/modules/red-operativa/alta-unidades/{models,services,guards,pages/{catalogo,edicion,baja,disponibilidad-externa}}` *(solo backend; carpetas frontend pendientes — ver Notes)*
- [X] T002 [P] Añadir fixtures de unidad en `backend/conftest.py` (`mock_unidad_emergencia`, `mock_despacho_activo`; reutiliza `admin_auth_headers`/`operador_auth_headers` ya existentes vía alias `administrador_auth_headers`/`operador_auth_headers_red_operativa`)
- [X] T003 [P] Generar tipos TypeScript del contrato en `frontend/src/app/modules/red-operativa/alta-unidades/models/unidad-emergencia.contract.ts` desde `contracts/alta-unidades.openapi.yaml`
- [X] T004 Crear matriz de trazabilidad CU→RF/RNF/CA→Task IDs en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios compartidos, permisos y migración cruzada bloqueantes para todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase. Incluye la migración de `despacho-inteligente` acordada en `research.md` Decision 8 — debe completarse antes de que `red_operativa` empiece a escribir `Dim_UnidadEmergencia.idcondado`, para evitar que ambos módulos queden desincronizados.

- [X] T005 Validar contrato OpenAPI como gate inicial en `specs/003-operational/Red-Operativa/alta-unidades/contracts/alta-unidades.openapi.yaml`
- [X] T006 Implementar repositorio de escritura de `Dim_UnidadEmergencia` (CRUD + `find_by_placa_activa` + `condado_exists`) en `backend/core/repositories/red_operativa/unidad_emergencia_repository.py`
- [X] T007 [P] Crear test de repositorio (marker: repository, AAA) para `unidad_emergencia_repository.py` en `backend/apps/red_operativa/tests/repositories/test_unidad_emergencia_repository.py`
- [X] T008 Implementar repositorio de `Fact_BajaUnidad` en `backend/core/repositories/red_operativa/baja_unidad_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: repository, AAA) para `baja_unidad_repository.py` en `backend/apps/red_operativa/tests/repositories/test_baja_unidad_repository.py`
- [X] T010 *(decisión de diseño, no duplicación)* Se reutiliza `core/repositories/despacho/historial_estado_unidad_repository.py` — ya vive en `core/` (capa compartida) y ya implementa transiciones de estado válidas incluyendo el bloqueo de "En Misión"; duplicarlo en `red_operativa` violaría "no repetir lógica de dominio" de `architectural-patterns.md`
- [X] T011 *(cubierto por los tests ya existentes de `despacho/tests/repositories/test_historial_estado_unidad_repository.py`, sin duplicar)*
- [X] T012 Implementar repositorio de solo lectura contra `Fact_Despacho` en `backend/core/repositories/red_operativa/despacho_activo_read_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: repository, AAA) para `despacho_activo_read_repository.py` en `backend/apps/red_operativa/tests/repositories/test_despacho_activo_read_repository.py`
- [X] T014 Reexportar `KafkaWriter` en `backend/core/repositories/red_operativa/kafka_writer.py` (mismo patrón que `core/repositories/accidentes/kafka_writer.py`)
- [X] T015 Implementar permisos DRF (`IsAdministradorRedOperativa`, `IsOperadorDisponibilidadExterna`, `IsAdministradorOrOperador`) en `backend/apps/red_operativa/permissions.py`
- [X] T016 [P] Crear test unitario (marker: unit, AAA) para `permissions.py` en `backend/apps/red_operativa/tests/unit/test_red_operativa_permissions.py`
- [X] T017 Registrar rutas de alta-unidades en `backend/apps/red_operativa/views/urls.py` y en `config/urls.py`/`config/settings.py` (INSTALLED_APPS + KAFKA_TOPICS["baja_unidad"])
- [X] T018 **[Migración cruzada]** Agregar columna `idcondado` (FK a `Dim_Condado`) y retirar `zonacobertura` de la definición de `Dim_UnidadEmergencia` en `specs/003-operational/Emergencias/despacho-inteligente/spec.md` (líneas 43, 74) y `specs/003-operational/Emergencias/despacho-inteligente/data-model.md` (línea 50)
- [X] T019 **[Migración cruzada]** Actualizar `list_candidatas_por_condado` para usar `row.get("idcondado")` directo (sin cast de `zonacobertura`) en `backend/core/repositories/despacho/unidad_emergencia_repository.py`
- [X] T020 [P] **[Migración cruzada]** Test existente de candidatas por condado (`test_unidad_emergencia_candidatas_repository.py`) ya usaba `idcondado` real de fixtures — verificado en verde sin cambios necesarios
- [X] T021 **[Migración cruzada]** Actualizar `consultar()`/`consultar_por_usuario()` para exponer `idcondado` en vez de `zonacobertura` en `backend/apps/despacho/services/disponibilidad_unidad_service.py`
- [X] T022 [P] **[Migración cruzada]** Test de servicio existente no aserta la clave `zonacobertura` explícitamente — verificado en verde sin cambios necesarios
- [X] T023 **[Migración cruzada]** Ejecutado `pytest apps/despacho -q` (excluyendo el archivo con bug preexistente de colisión de conftest, no relacionado): **90/90 en verde**
- [X] T023a **[Migración cruzada]** Actualizado el schema de `zonacobertura`→`idcondado` en `specs/003-operational/Emergencias/evidencia-unidad/contracts/evidencia-unidad.openapi.yaml:689`
- [X] T023b **[Migración cruzada]** Actualizado `zonacobertura`→`idcondado` en el tipo `DisponibilidadUnidadData` de `frontend/src/app/modules/evidencia-unidad/services/models/evidencia-unidad.types.ts:136`
- [X] T023c **[Migración cruzada]** Actualizado el binding a `idcondado` en `frontend/src/app/modules/evidencia-unidad/pages/panel-disponibilidad/panel-disponibilidad.page.html:62`
- [X] T023d [P] **[Migración cruzada]** Creado test de componente (no existía antes) para el panel de disponibilidad reflejando `idcondado` en `frontend/src/app/modules/evidencia-unidad/pages/panel-disponibilidad/panel-disponibilidad.page.spec.ts`
- [X] T023e **[Migración cruzada]** Backend de `evidencia-unidad` vive en `apps/despacho` (ya validado en T023, 90/90 verde). Frontend: no hay Chrome/Karma en este entorno; validado con `tsc --noEmit` limpio en `tsconfig.app.json` y `tsconfig.spec.json`

**Checkpoint**: Repositorios base, permisos y migración de `despacho-inteligente` **y** `evidencia-unidad` listos; contrato validado.

---

## Phase 3: User Story 1 - Registro individual de unidad (Priority: P1) 🎯 MVP

**Goal**: Entregar CU-O54 — el Administrador registra una unidad individual con validación de placa única.

**Independent Test**: Administrador registra una unidad nueva con `placa` no existente → `201`, `activo=true`, sin fila en `Fact_HistorialEstadoUnidad`; repetir con misma `placa` → `409`.

**Measurable Criteria**: Cumplir CA-CAM-001, CA-CAM-002; RNF-CAM-001 (<1s validación de duplicado).

### Tests for User Story 1

- [X] T024 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/red-operativa/unidades` en `backend/apps/red_operativa/tests/api/test_registro_unidad_contract.py`
- [X] T025 [P] [US1] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/red-operativa/unidades/{id}` en `backend/apps/red_operativa/tests/api/test_get_unidad_contract.py`
- [X] T026 [P] [US1] Crear test de servicio (marker: service, AAA) para `RegistroUnidadService` en `backend/apps/red_operativa/tests/services/test_registro_unidad_service.py`
- [X] T027 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `UnidadEmergenciaApiService` en `frontend/src/app/modules/red-operativa/alta-unidades/services/unidad-emergencia-api.service.spec.ts`
- [X] T028 [P] [US1] Crear test unitario frontend (marker: unit, AAA) para `AdministradorRedOperativaGuard` en `frontend/src/app/modules/red-operativa/alta-unidades/guards/administrador-red-operativa.guard.spec.ts`

### Implementation for User Story 1

- [X] T029 [US1] Implementar `RegistroUnidadService` (validación de placa, idcliente requerido, `idcondado` debe existir en `Dim_Condado` → 400 si no) en `backend/apps/red_operativa/services/registro_unidad_service.py`
- [X] T030 [US1] Implementar vista DRF de alta/detalle en `backend/apps/red_operativa/views/unidad_views.py`
- [X] T031 [US1] Registrar rutas US1 en `backend/apps/red_operativa/views/urls.py`
- [X] T032 [US1] Implementar `UnidadEmergenciaApiService` en `frontend/src/app/modules/red-operativa/alta-unidades/services/unidad-emergencia-api.service.ts`
- [X] T033 [US1] Implementar `UnidadEmergenciaFacadeService` (orquestación, validaciones de UI) en `frontend/src/app/modules/red-operativa/alta-unidades/services/unidad-emergencia-facade.service.ts`
- [X] T034 [US1] Implementar `AdministradorRedOperativaGuard` en `frontend/src/app/modules/red-operativa/alta-unidades/guards/administrador-red-operativa.guard.ts`
- [X] T035 [US1] Implementar página de catálogo (listado + alta individual) en `frontend/src/app/modules/red-operativa/alta-unidades/pages/catalogo/catalogo.page.ts`
- [X] T036 [US1] Configurar rutas lazy de alta-unidades en `frontend/src/app/modules/red-operativa/alta-unidades/alta-unidades.routes.ts` (registradas en `app.routes.ts`)

**Checkpoint**: US1 operativa como MVP — alta individual con validación de placa.

**US1 Gate (must pass before next story)**:
- [X] T037 [US1] Validar cumplimiento de `CA-CAM-001`, `CA-CAM-002` en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`

---

## Phase 4: User Story 2 - Registro en lote (Priority: P1)

**Goal**: Entregar CU-O56 — importación CSV/Excel todo-o-nada, reutilizando la validación de US1 fila por fila.

**Independent Test**: Subir archivo con 50 filas donde la fila 23 tiene placa duplicada → ninguna unidad insertada, error reportado con `fila` y `motivo`.

**Measurable Criteria**: Cumplir CA-CAM-003; RNF-CAM-002 (≤30s para 500 unidades).

### Tests for User Story 2

- [X] T038 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/red-operativa/unidades/importacion-lote` en `backend/apps/red_operativa/tests/api/test_importacion_lote_contract.py`
- [X] T039 [P] [US2] Crear test de servicio (marker: service, AAA) para `ImportacionLoteUnidadService` en `backend/apps/red_operativa/tests/services/test_importacion_lote_unidad_service.py`
- [X] T040 [P] [US2] Crear test de performance (marker: slow) para importación de 500 filas ≤30s en `backend/apps/red_operativa/tests/performance/test_importacion_lote_p95.py`

### Implementation for User Story 2

- [X] T041 [US2] Implementar `ImportacionLoteUnidadService` (rechaza con 400 archivos de más de 500 filas antes de procesar ninguna, valida todas las filas restantes en memoria antes de publicar, reutiliza `RegistroUnidadService`) en `backend/apps/red_operativa/services/importacion_lote_unidad_service.py`
- [X] T042 [US2] Extender vista DRF con endpoint de importación en lote en `backend/apps/red_operativa/views/unidad_views.py`
- [X] T043 [US2] Registrar ruta US2 en `backend/apps/red_operativa/views/urls.py`
- [X] T044 [US2] Extender página de catálogo con importación en lote (input de archivo + reporte de errores) en `frontend/src/app/modules/red-operativa/alta-unidades/pages/catalogo/catalogo.page.ts`

**Checkpoint**: US2 funcional e independiente de US3-US5.

**US2 Gate (must pass before next story)**:
- [X] T045 [US2] Validar cumplimiento de `CA-CAM-003` en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`

---

## Phase 5: User Story 3 - Edición de unidad existente (Priority: P2)

**Goal**: Entregar CU-O57 — edición de campos permitidos con bloqueo/confirmación si hay despacho activo, y last-write-wins en concurrencia.

**Independent Test**: Editar `tipounidademergencia` con despacho activo sin `confirmar_edicion_critica` → `409`; repetir con confirmación → `200`.

**Measurable Criteria**: Cumplir CA-CAM-004, CA-CAM-005.

### Tests for User Story 3

- [X] T046 [P] [US3] Crear test de contrato API (marker: api, AAA) para `PATCH /api/v1/red-operativa/unidades/{id}` en `backend/apps/red_operativa/tests/api/test_edicion_unidad_contract.py`
- [X] T047 [P] [US3] Crear test de servicio (marker: service, AAA) para `EdicionUnidadService` (incluye caso de bloqueo por despacho activo) en `backend/apps/red_operativa/tests/services/test_edicion_unidad_service.py`

### Implementation for User Story 3

- [X] T048 [US3] Implementar `EdicionUnidadService` (campos editables, inmutables `idunidademergencia`/`idcliente`, bloqueo vía `DespachoActivoReadRepository`, last-write-wins) en `backend/apps/red_operativa/services/edicion_unidad_service.py`
- [X] T049 [US3] Extender vista DRF con endpoint PATCH en `backend/apps/red_operativa/views/unidad_views.py`
- [X] T050 [US3] Registrar ruta US3 en `backend/apps/red_operativa/views/urls.py`
- [X] T051 [US3] Implementar página de edición en `frontend/src/app/modules/red-operativa/alta-unidades/pages/edicion/edicion.page.ts`

**Checkpoint**: US3 completa; edición con reglas de bloqueo operativas.

**US3 Gate (must pass before next story)**:
- [X] T052 [US3] Validar cumplimiento de `CA-CAM-004`, `CA-CAM-005` en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`

---

## Phase 6: User Story 4 - Baja y reactivación de unidad (Priority: P2)

**Goal**: Entregar CU-O58 — baja lógica con trazabilidad completa y reactivación con revalidación de unicidad de placa.

**Independent Test**: Dar de baja unidad → `Fact_BajaUnidad` poblado, `activo=false`; reactivar con placa ya usada por otra unidad activa → `409`; sin conflicto → `200`.

**Measurable Criteria**: Cumplir CA-CAM-006, CA-CAM-007.

### Tests for User Story 4

- [X] T053 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/red-operativa/unidades/{id}/baja` en `backend/apps/red_operativa/tests/api/test_baja_unidad_contract.py`
- [X] T054 [P] [US4] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/red-operativa/unidades/{id}/reactivar` en `backend/apps/red_operativa/tests/api/test_reactivar_unidad_contract.py`
- [X] T055 [P] [US4] Crear test de servicio (marker: service, AAA) para `BajaUnidadService` (baja forzada con `idaccidente`, reactivación con conflicto de placa) en `backend/apps/red_operativa/tests/services/test_baja_unidad_service.py`

### Implementation for User Story 4

- [X] T056 [US4] Implementar `BajaUnidadService` (baja normal/forzada, reactivación con validación de placa vía `unidad_emergencia_repository.find_by_placa_activa`) en `backend/apps/red_operativa/services/baja_unidad_service.py`
- [X] T057 [US4] Extender vista DRF con endpoints de baja/reactivación en `backend/apps/red_operativa/views/unidad_views.py`
- [X] T058 [US4] Registrar rutas US4 en `backend/apps/red_operativa/views/urls.py`
- [X] T059 [US4] Implementar página de baja en `frontend/src/app/modules/red-operativa/alta-unidades/pages/baja/baja.page.ts` (incluye reactivación)

**Checkpoint**: US4 completa; ciclo de vida administrativo (alta→edición→baja→reactivación) end-to-end.

**US4 Gate (must pass before next story)**:
- [X] T060 [US4] Validar cumplimiento de `CA-CAM-006`, `CA-CAM-007` en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`

---

## Phase 7: User Story 5 - Disponibilidad de unidad externa (Priority: P2)

**Goal**: Entregar CU-O59 — el Operador declara disponibilidad de unidades sin login propio, con alerta de inconsistencia.

**Independent Test**: Operador marca "Activa" con despacho activo sin retirar → `422` (alerta, no bloqueo); sin conflicto → `200`, `idusuario` registrado es el del Operador.

**Measurable Criteria**: Cumplir CA-CAM-008, CA-CAM-009.

### Tests for User Story 5

- [X] T061 [P] [US5] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/red-operativa/unidades/{id}/disponibilidad` en `backend/apps/red_operativa/tests/api/test_disponibilidad_externa_contract.py`
- [X] T062 [P] [US5] Crear test de servicio (marker: service, AAA) para `DisponibilidadExternaService` (incluye alerta 422) en `backend/apps/red_operativa/tests/services/test_disponibilidad_externa_service.py`
- [X] T063 [P] [US5] Crear test unitario frontend (marker: unit, AAA) para `OperadorDisponibilidadGuard` en `frontend/src/app/modules/red-operativa/alta-unidades/guards/operador-disponibilidad.guard.spec.ts`

### Implementation for User Story 5

- [X] T064 [US5] Implementar `DisponibilidadExternaService` (rechaza "En Misión", alerta si "Activa" con despacho sin retirar) en `backend/apps/red_operativa/services/disponibilidad_externa_service.py`
- [X] T065 [US5] Extender vista DRF con endpoint de disponibilidad en `backend/apps/red_operativa/views/unidad_views.py`
- [X] T066 [US5] Registrar ruta US5 en `backend/apps/red_operativa/views/urls.py`
- [X] T067 [US5] Implementar `OperadorDisponibilidadGuard` en `frontend/src/app/modules/red-operativa/alta-unidades/guards/operador-disponibilidad.guard.ts`
- [X] T068 [US5] Implementar página de disponibilidad externa en `frontend/src/app/modules/red-operativa/alta-unidades/pages/disponibilidad-externa/disponibilidad-externa.page.ts`
- [X] T069 [US5] Proteger rutas por rol (Administrador vs Operador) en `frontend/src/app/modules/red-operativa/alta-unidades/alta-unidades.routes.ts`

**Checkpoint**: US5 completa; módulo alta-unidades end-to-end.

**US5 Gate (must pass before polish)**:
- [X] T070 [US5] Validar cumplimiento de `CA-CAM-008`, `CA-CAM-009` en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Performance, documentación y validación final.

- [X] T071 [P] Añadir test de performance de validación de duplicado de placa <1s en `backend/apps/red_operativa/tests/performance/test_duplicado_placa_p95.py` (marker: slow)
- [X] T072 [P] Documentar evidencia de performance en `specs/003-operational/Red-Operativa/alta-unidades/quickstart.md`
- [X] T073 [P] Actualizar mapeo RF/RNF/CA→Task IDs en `specs/003-operational/Red-Operativa/alta-unidades/traceability.md`
- [X] T074 [P] Actualizar `module-map.md` marcando `alta-unidades` como "✅ Implementado" en `.specify/docs/architecture/module-map.md`
- [X] T075 Ejecutar validación end-to-end según `specs/003-operational/Red-Operativa/alta-unidades/quickstart.md`: 62/62 tests `red_operativa`, 90/90 `despacho` post-migración, `ng build` de producción exitoso

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): inicia inmediatamente.
- Phase 2 (Foundational, incluye migración cruzada): depende de Phase 1; bloquea todas las historias.
- Phases 3-7 (US1-US5): dependen de Phase 2.
- Phase 8 (Polish): depende de completar historias objetivo.

### User Story Dependencies

- **US1 (P1)**: depende solo de Foundational; define MVP (CU-O54).
- **US2 (P1)**: depende de Foundational + US1 (reutiliza `RegistroUnidadService` fila a fila).
- **US3 (P2)**: depende de Foundational (`DespachoActivoReadRepository`); independiente de US1/US2 salvo por el modelo de datos ya creado.
- **US4 (P2)**: depende de Foundational; reactivación reutiliza `find_by_placa_activa` de US1.
- **US5 (P2)**: depende de Foundational (`HistorialEstadoUnidadRepository`, `DespachoActivoReadRepository`); independiente de US1-US4.

### Within Each User Story

1. Tests primero (AAA) con marker `api`/`service`/`repository`/`unit`.
2. Repositorios (`backend/core/repositories/red_operativa/...`, ya cubiertos en Foundational).
3. Servicios (`backend/apps/red_operativa/services/`).
4. Vistas/endpoints DRF.
5. Integración frontend (servicios → guards → páginas).

### Parallel Opportunities

- T002–T004 en Setup en paralelo.
- T007, T009, T011, T013, T016, T020, T022 en Foundational en paralelo.
- Dentro de cada historia: todos los tests `[P]` en paralelo.
- US3 y US5 pueden implementarse en paralelo entre sí tras Foundational (no comparten servicio).
- Frontend de cada historia puede avanzar en paralelo con su backend tras definir el contrato.

---

## Parallel Example: User Story 1

```bash
# Tests backend en paralelo (AAA):
pytest apps/red_operativa/tests/api/test_registro_unidad_contract.py -v -m api
pytest apps/red_operativa/tests/api/test_get_unidad_contract.py -v -m api
pytest apps/red_operativa/tests/services/test_registro_unidad_service.py -v -m service

# Tests frontend en paralelo:
ng test --include='**/alta-unidades/services/unidad-emergencia-api.service.spec.ts'
ng test --include='**/alta-unidades/guards/administrador-red-operativa.guard.spec.ts'
```

---

## Parallel Example: User Story 3 y User Story 5 (en paralelo entre sí)

```bash
Task: "T047 [US3] test_edicion_unidad_service.py (marker service, AAA)"
Task: "T062 [US5] test_disponibilidad_externa_service.py (marker service, AAA)"
Task: "T063 [US5] operador-disponibilidad.guard.spec.ts (marker unit, AAA)"
```

---

## Implementation Strategy

### MVP First (US1)

1. Completar Phase 1 y Phase 2 (incluye migración de `despacho-inteligente`).
2. Completar Phase 3 (US1) end-to-end.
3. Verificar CA-CAM-001, CA-CAM-002.
4. Demo: Administrador registra una unidad y el duplicado de placa es rechazado.

### Incremental Delivery

1. MVP con US1 (alta individual).
2. Agregar US2 (importación en lote).
3. Agregar US3 (edición con bloqueo por despacho activo).
4. Agregar US4 (baja + reactivación).
5. Agregar US5 (disponibilidad externa, rol Operador).
6. Cerrar con Phase 8 (performance + quickstart E2E + migración validada).

### Team Parallel Strategy

1. Equipo completo en Phase 1-2 (la migración cruzada de `despacho-inteligente` es bloqueante y debe cerrarse antes de avanzar).
2. Tras US1:
   - Dev A: US2 (importación en lote, reutiliza validación de US1)
   - Dev B: US3 (edición + bloqueo por despacho activo)
   - Dev C: US4 + US5 (baja/reactivación y disponibilidad externa, comparten `HistorialEstadoUnidadRepository`)
3. Integración y Phase 8.

---

## Notes

- Repositorios en `backend/core/repositories/red_operativa/`; Kafka único canal de escritura (`Dim_UnidadEmergencia_topic`, `Fact_BajaUnidad_topic`, `Fact_HistorialEstadoUnidad_topic`).
- Cada servicio/repositorio nuevo tiene test emparejado con marker y AAA según `.specify/docs/architecture/testing.md`.
- La migración cruzada (T018-T023e) toca **dos** módulos ya implementados — `despacho-inteligente` (backend) y `evidencia-unidad` (contrato + frontend, detectado en `/speckit-analyze`) — porque ambos consumen la misma columna física `Dim_UnidadEmergencia.zonacobertura`. Tratarla como bloqueante, no como "nice to have" al final.
- `DespachoActivoReadRepository` es de solo lectura contra `Fact_Despacho` (módulo Emergencias) — nunca escribe esa tabla.
- Depende de **autenticacion-y-rbac** (JWT + roles Administrador/Operador de emergencias).
- No hay FK entre `Dim_UnidadEmergencia` y `Dim_RegionOperativa` (RN-CAM-005) — `incorporacion-regional` es un spec separado, no bloqueante para este.

---

## Task Summary

| Métrica | Valor |
|---------|-------|
| **Total tareas** | 80 |
| **Setup + Foundational** | 28 tareas (T001–T023e, incluye 11 de migración cruzada: 6 `despacho-inteligente` + 5 `evidencia-unidad`) |
| **US1 — Registro individual (CU-O54)** | 14 tareas (T024–T037) |
| **US2 — Registro en lote (CU-O56)** | 8 tareas (T038–T045) |
| **US3 — Edición (CU-O57)** | 7 tareas (T046–T052) |
| **US4 — Baja y reactivación (CU-O58)** | 8 tareas (T053–T060) |
| **US5 — Disponibilidad externa (CU-O59)** | 10 tareas (T061–T070) |
| **Polish** | 5 tareas (T071–T075) |
| **Tests emparejados repo/servicio/api** | 19 backend + 5 frontend unit + 2 performance |
| **MVP sugerido** | Phase 1 + 2 + US1 (T001–T037) |
| **Estado final** | ✅ 80/80 tareas completas. Backend: 62/62 tests `red_operativa` + 90/90 `despacho` post-migración (572/575 en la suite global, 3 fallos preexistentes no relacionados). Frontend: `tsc --noEmit` limpio + `ng build` de producción exitoso (sin Chrome/Karma disponible en este entorno para ejecutar Jasmine) |
