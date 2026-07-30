# Tasks: Pipeline Comercial y Prospectos

**Input**: Design documents from `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/commercial-pipeline-prospects.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento del usuario (`testing-expert` + `testing.md`): cada tarea de **servicio** o **repositorio** trae su test con markers `unit` / `repository` / `service` / `api`, patrón **AAA** (Arrange-Act-Assert). Umbrales: repos ≥85%, services ≥80%, views/API ≥75%.

**Organization**: Tareas por historia de usuario (mapeadas desde CU/RF del spec; el spec no usa etiquetas P1/P2 literales — prioridad derivada del embudo).


> **Capas:** este archivo es autoridad de **dominio/API**.
> Tareas con paths `frontend/src` o marcadas `[Histórico-UI]` son del monolito pre-split;
> la autoridad Interaction Capability es [`../frontend/tasks.md`](../frontend/tasks.md) (`T-FE-*`).
> No reabrir ni re-implementar `[Histórico-UI]` desde la capa backend.
> `[Bridge-FE]` = tipos/cliente tipado generado desde OpenAPI del backend (sigue anclado al contrato BE).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: `US1`–`US8`
- Cada descripción incluye path exacto

### User Story Map

| Story | Prioridad | CU/RF | Independent Test | Estado |
|-------|-----------|-------|------------------|--------|
| US1 | P1 🎯 MVP | O116, O117 auto | POST público crea prospecto `Nuevo` e intenta asignación automática | ✅ |
| US2 | P1 | RF-CPP-008 | Gerente lista solo propios; Admin todos; ajeno → 403 | ✅ |
| US3 | P1 | O117 manual | Admin asigna huérfano; dueño/Admin reasigna con motivo; Gerente no dueño → 403 | ✅ |
| US4 | P1 | O119 | Avance adyacente + Perdido; rechazo salto/retroceso/Ganado; 409 optimistic | ✅ |
| US5 | P1 | O121 | Conversión desde Negociación crea cliente; NIT dup → 409; Idempotency-Key | ✅ |
| US6 | P2 | RF-CPP-007 | Admin entrada directa `idprospecto=null`; Gerente → 403 | ✅ |
| US7 | P2 | Frontend embudo | Módulo Angular lazy: registro, listado, pipeline, conversión, entrada directa | ✅ |
| **US8** | **P1** | **RF-CPP-000** | **GET `/planes` sin JWT: solo `activo=true`, severidades derivadas; cero Kafka write** | ✅ |

> **Delta 2026-07-26:** T001–T069 completan el embudo previo. T070+ implementan el portal público de planes (antes fuera de alcance; ahora en plan/research Decision 10).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: App `ventas_crm`, módulo Angular, fixtures JWT y contract-first.

- [X] T001 [Histórico-UI] Crear estructura `backend/apps/ventas_crm/{views,services,tests/{api,services,repositories,unit}}`, `backend/core/repositories/ventas_crm/` y `frontend/src/app/modules/ventas-crm/{pages,services,guards,models}` según `plan.md`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Sembrar roles JWT `GerenteVentas`, `GerenteCuentasPublicas` y `Sistema` en el catálogo/`Dim_Rol` de autenticacion-y-rbac (si aún no existen) y añadir fixtures `gerente_ventas_auth_headers`, `gerente_cuentas_publicas_auth_headers`, `admin_crm_auth_headers` en `backend/conftest.py` — **bloqueante** antes de US1
- [X] T004 [Bridge-FE] [P] Generar DTOs TypeScript desde OpenAPI en `frontend/src/app/modules/ventas-crm/models/prospectos.types.ts` basados en `contracts/commercial-pipeline-prospects.openapi.yaml`
- [X] T005 [Histórico-UI] [P] Crear stub lazy `frontend/src/app/modules/ventas-crm/ventas-crm.routes.ts` y registrar en `frontend/src/app/app.routes.ts`
- [X] T006 [P] Registrar app `ventas_crm` en `backend/config/settings.py` (`INSTALLED_APPS` + topics Kafka `Dim_Prospecto_topic`, `Fact_Asignacion_topic`, `Fact_Pipeline_topic`, `Dim_Cliente_topic`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot, permisos, throttle, routing — bloquea todas las historias.

**CRITICAL**: Ninguna US puede empezar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/contracts/commercial-pipeline-prospects.openapi.yaml`
- [X] T008 Implementar `ProspectoRepository` (lectura Pinot + publish Kafka) en `backend/core/repositories/ventas_crm/prospecto_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_prospecto_repository.py`
- [X] T010 Implementar `AsignacionRepository` (insert-only) en `backend/core/repositories/ventas_crm/asignacion_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_asignacion_repository.py` — assert sin `update()`/`delete()` físicos
- [X] T012 Implementar `PipelineRepository` (insert-only) en `backend/core/repositories/ventas_crm/pipeline_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_pipeline_repository.py` — assert insert-only
- [X] T014 Extender `ClienteRepository` en `backend/core/repositories/cuentas_clientes/cliente_repository.py` para co-escritura CRM: `create` acepta `idprospecto` opcional y `admin_local_id` nullable; añadir `exists_by_nit_any(nit)` (RN-CPP-010 — cualquier `estado`, sin excluir `Rechazado_Anulado`). **No** crear `ventas_crm/cliente_escritura_repository.py`
- [X] T015 [P] Crear/actualizar test de repositorio (marker: `repository`, AAA) en `backend/apps/cuentas_clientes/tests/repositories/test_cliente_repository.py` (o archivo de test existente del repo) cubriendo `exists_by_nit_any` + create con `idprospecto` / sin `admin_local_id`
- [X] T016 Implementar permisos `IsGerenteVentas`, `IsGerenteCuentasPublicas`, `IsAdministradorCrm`, `IsProspectoOwnerOrAdmin` en `backend/apps/ventas_crm/permissions.py`
- [X] T017 [P] Crear test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_ventas_crm_permissions.py`
- [X] T018 Implementar `ProspectoRegistroThrottle` (10/min/IP) en `backend/apps/ventas_crm/throttles.py`
- [X] T019 [P] Crear test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_prospecto_registro_throttle.py`
- [X] T020 Registrar `backend/apps/ventas_crm/urls.py` e incluir bajo `/api/v1/ventas-crm/` en `backend/config/urls.py`

**Checkpoint**: Repos, permisos, throttle y routing listos.

---

## Phase 3: User Story 1 — Registro público + asignación automática (Priority: P1) 🎯 MVP

**Goal**: O116 + O117 auto — visitante registra prospecto; Sistema intenta pool+menor carga.

**Independent Test**: `POST /ventas-crm/prospectos` → 201 `Nuevo`; con pool → `idusuario` set; pool vacío → huérfano; gmail dup → 409; >10/min/IP → 429.

**Measurable Criteria**: CA-CPP-001, CA-CPP-002, CA-CPP-011 (parcial huérfano); Escenarios 1–4; RNF-CPP-002.

### Tests for User Story 1

- [X] T021 [P] [US1] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_registro_prospecto_service.py` (debe fallar antes de implementar)
- [X] T022 [P] [US1] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_asignacion_automatica_service.py` (pool, empate, vacío)
- [X] T023 [P] [US1] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_registro_prospecto_contract.py` alineado al OpenAPI

### Implementation for User Story 1

- [X] T024 [US1] Implementar `RegistroProspectoService` en `backend/apps/ventas_crm/services/registro_prospecto_service.py` (RN-CPP-001 gmail unique)
- [X] T025 [US1] Implementar `AsignacionAutomaticaService` en `backend/apps/ventas_crm/services/asignacion_automatica_service.py` (Decision 2 research)
- [X] T026 [US1] Implementar `POST` registro en `backend/apps/ventas_crm/views/prospecto_views.py` + wire throttle
- [X] T027 [US1] Asegurar T021–T023 verdes (AAA, markers) tras implementación

**Checkpoint**: MVP registro+auto-asignación operable vía API.

---

## Phase 4: User Story 2 — Consulta de prospectos y pipeline (Priority: P1)

**Goal**: RF-CPP-008 — listado cursor y detalle con historiales; filtro dueño vs Admin.

**Independent Test**: Gerente solo ve `idusuario=él`; Admin todos; GET ajeno → 403; detalle incluye historiales.

**Measurable Criteria**: CA-CPP-010; Escenario 13; CA-CPP-009 (≤500ms P95 en ambiente de prueba).

### Tests for User Story 2

- [X] T028 [P] [US2] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_consulta_prospecto_service.py`
- [X] T029 [P] [US2] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_consulta_prospecto_contract.py`

### Implementation for User Story 2

- [X] T030 [US2] Implementar `ConsultaProspectoService` en `backend/apps/ventas_crm/services/consulta_prospecto_service.py`
- [X] T031 [US2] Implementar `GET /prospectos` y `GET /prospectos/{id}` en `backend/apps/ventas_crm/views/prospecto_views.py`
- [X] T032 [US2] Asegurar T028–T029 verdes

**Checkpoint**: Consulta RBAC operable.

---

## Phase 5: User Story 3 — Asignación / reasignación manual (Priority: P1)

**Goal**: O117 manual — Admin primera asignación huérfano; dueño/Admin reasignan con motivo + optimistic `idusuario_esperado`.

**Independent Test**: Huérfano solo Admin; reasignación sin motivo → 400; Gerente no dueño → 403; idusuario_esperado obsoleto → 409.

**Measurable Criteria**: CA-CPP-003, CA-CPP-011; Escenarios 5, 11, 14; RN-CPP-007/009/011.

### Tests for User Story 3

- [X] T033 [P] [US3] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_asignacion_manual_service.py`
- [X] T034 [P] [US3] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_asignacion_manual_contract.py`

### Implementation for User Story 3

- [X] T035 [US3] Implementar `AsignacionManualService` en `backend/apps/ventas_crm/services/asignacion_manual_service.py`
- [X] T036 [US3] Implementar `PATCH .../asignacion` en `backend/apps/ventas_crm/views/asignacion_views.py`
- [X] T037 [US3] Asegurar T033–T034 verdes

**Checkpoint**: Asignación manual y huérfanos cubiertos.

---

## Phase 6: User Story 4 — Pipeline y pérdida (Priority: P1)

**Goal**: O119 — avance adyacente, Perdido con motivo, sin saltos/retrocesos/Ganado; optimistic `etapa_actual_esperada`.

**Independent Test**: Nuevo→Contactado OK; salto/retroceso/Ganado rechazados; Perdido terminal; etapa esperada obsoleta → 409.

**Measurable Criteria**: CA-CPP-004, CA-CPP-005, CA-CPP-007, CA-CPP-012; Escenarios 6, 6b, 7, 8, 16.

### Tests for User Story 4

- [X] T038 [P] [US4] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_pipeline_service.py`
- [X] T039 [P] [US4] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_pipeline_contract.py`

### Implementation for User Story 4

- [X] T040 [US4] Implementar `PipelineService` (adyacencias + pérdida) en `backend/apps/ventas_crm/services/pipeline_service.py`
- [X] T041 [US4] Implementar `POST .../pipeline` en `backend/apps/ventas_crm/views/pipeline_views.py`
- [X] T042 [US4] Asegurar T038–T039 verdes

**Checkpoint**: Máquina de estados de pipeline enforceable vía API.

---

## Phase 7: User Story 5 — Conversión a cliente (Priority: P1)

**Goal**: O121 — conversión atómica desde Negociación; NIT único; Idempotency-Key obligatorio.

**Independent Test**: Negociación → 201 cliente `Activo`/`Pendiente` + prospecto `convertido`; NIT dup → 409; etapa ≠ Negociación → rechazo; sin Idempotency-Key → 400.

**Measurable Criteria**: CA-CPP-006, CA-CPP-008 (parcial NIT), CA-CPP-012; Escenarios 9, 10, 15.

### Tests for User Story 5

- [X] T043 [P] [US5] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_conversion_cliente_service.py`
- [X] T044 [P] [US5] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_conversion_contract.py`

### Implementation for User Story 5

- [X] T045 [US5] Implementar `ConversionClienteService` en `backend/apps/ventas_crm/services/conversion_cliente_service.py`
- [X] T046 [US5] Implementar `POST .../conversion` en `backend/apps/ventas_crm/views/conversion_views.py`
- [X] T047 [US5] Asegurar T043–T044 verdes

**Checkpoint**: Embudo completo hasta cliente.

---

## Phase 8: User Story 6 — Entrada directa (Priority: P2)

**Goal**: RF-CPP-007 — Admin crea `Dim_Cliente` sin prospecto.

**Independent Test**: Admin 201 `idprospecto=null`; Gerente 403; NIT dup 409.

**Measurable Criteria**: CA-CPP-008; Escenario 12.

### Tests for User Story 6

- [X] T048 [P] [US6] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_entrada_directa_service.py`
- [X] T049 [P] [US6] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_entrada_directa_contract.py`

### Implementation for User Story 6

- [X] T050 [US6] Implementar `EntradaDirectaService` en `backend/apps/ventas_crm/services/entrada_directa_service.py`
- [X] T051 [US6] Implementar `POST /clientes/entrada-directa` en `backend/apps/ventas_crm/views/entrada_directa_views.py`
- [X] T052 [US6] Asegurar T048–T049 verdes

**Checkpoint**: Vía institucional sin embudo cubierta.

---

## Phase 9: User Story 7 — Frontend Angular Ventas-CRM (Priority: P2)

**Goal**: Consumir contrato con servicios tipados, guards y UI loading/vacío/error (RNF-CPP-005).

**Independent Test**: Flujo quickstart §Frontend smoke (registro → listado dueño → etapas → conversión; Admin entrada directa / huérfano).

**Measurable Criteria**: RNF-CPP-005; quickstart §7.

### Implementation for User Story 7

- [X] T053 [Histórico-UI] [P] [US7] Implementar guards `gerente-ventas.guard.ts`, `gerente-cuentas-publicas.guard.ts`, `admin-o-gerente-crm.guard.ts` en `frontend/src/app/modules/ventas-crm/guards/`
- [X] T054 [Histórico-UI] [P] [US7] Crear test unitario de guards (AAA) en `frontend/src/app/modules/ventas-crm/guards/*.spec.ts`
- [X] T055 [Histórico-UI] [P] [US7] Implementar `ProspectoApiService` en `frontend/src/app/modules/ventas-crm/services/prospecto-api.service.ts`
- [X] T056 [Histórico-UI] [P] [US7] Crear test unitario del servicio API (AAA) en `frontend/src/app/modules/ventas-crm/services/prospecto-api.service.spec.ts`
- [X] T057 [Histórico-UI] [P] [US7] Implementar `PipelineApiService` + `ConversionApiService` en `frontend/src/app/modules/ventas-crm/services/`
- [X] T058 [P] [US7] Crear tests unitarios (AAA) de `pipeline-api.service.spec.ts` y `conversion-api.service.spec.ts`
- [X] T059 [Histórico-UI] [US7] Página registro público `frontend/src/app/modules/ventas-crm/pages/registro-publico/` (estados loading/error)
- [X] T060 [Histórico-UI] [US7] Página listado `frontend/src/app/modules/ventas-crm/pages/listado-prospectos/` (skeleton/vacío/error)
- [X] T061 [Histórico-UI] [US7] Página detalle + acciones pipeline/asignación `frontend/src/app/modules/ventas-crm/pages/detalle-prospecto/`
- [X] T062 [Histórico-UI] [US7] Board/pipeline UI `frontend/src/app/modules/ventas-crm/pages/pipeline-board/` con manejo 409 reintento
- [X] T063 [Histórico-UI] [US7] Página entrada directa Admin `frontend/src/app/modules/ventas-crm/pages/entrada-directa/`
- [X] T064 [Histórico-UI] [US7] Completar rutas lazy y navegación en `frontend/src/app/modules/ventas-crm/ventas-crm.routes.ts`

**Checkpoint**: UI operable contra API real/mock según quickstart.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Cobertura, quickstart E2E, mapa y calidad.

- [X] T065 Ejecutar suite `pytest -m "repository or service or api"` en `backend/apps/ventas_crm/tests/` y corregir gaps bajo umbrales testing.md
- [X] T066 [P] Añadir test de performance listado (marker: `api` o `slow`) documentando P95 ≤500ms en `backend/apps/ventas_crm/tests/api/test_listado_prospectos_p95.py` (o skip condicional si CI sin Pinot)
- [X] T067 Validar escenarios de `quickstart.md` contra API local; anotar resultados en `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/quickstart.md` (checklist Done when)
- [X] T068 [P] Actualizar estado en `.specify/docs/architecture/module-map.md` (#4) a implementado cuando backend+frontend pasen
- [X] T069 [P] Revisar que no queden TODOs bloqueantes en `backend/apps/ventas_crm/` ni leaks de lógica Kafka fuera de repositorios

---

## Phase 11: User Story 8 — Portal público de planes (RF-CPP-000) ⏳

**Goal**: Visitante sin JWT consulta el catálogo activo de `Dim_Plan` (nombre, precio, límites, severidades desbloqueadas). Precondición informativa del embudo; **cero escrituras** (sin `Dim_Plan_topic`). Alias documental CU-O123 (ID canónico a definir).

**Independent Test**: `GET /api/v1/ventas-crm/planes` → `200` solo `activo=true`; mapa nivel→severidades (Decision 10); plan inactivo oculto; lista vacía válida; mock Kafka sin publishes a `Dim_Plan_topic`. UI pública con loading/vacío/error + CTA a registro.

### Foundational delta (bloquea US8)

- [X] T070 Alinear seed `Dim_Plan` en `backend/conftest.py` a niveles canónicos `Básico` / `Profesional` / `Empresarial` (reemplazar `premium`) + al menos un plan `activo=false` para negativos; extender mirror Pinot query `FROM DIM_PLAN` + filtro `ACTIVO` si falta
- [X] T071 [Bridge-FE] [P] Extender DTOs TypeScript `PlanPublico` / envelope en `frontend/src/app/modules/ventas-crm/models/prospectos.types.ts` (o `planes.types.ts`) desde `contracts/commercial-pipeline-prospects.openapi.yaml`

### Tests for User Story 8 (FAIL first — TDD)

- [X] T072 [P] [US8] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_plan_lectura_repository.py` — lista solo `activo=true`; assert **sin** métodos `create`/`update`/`publish` Kafka
- [X] T073 [P] [US8] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_consulta_planes_publicos_service.py` — mapa Básico→[Baja], Profesional→[Baja,Media], Empresarial→[Baja,Media,Alta], nivel desconocido→[] pero plan incluido
- [X] T074 [P] [US8] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_planes_publicos_contract.py` — sin Authorization → 200; ocultar inactivos; alineado a OpenAPI `GET /ventas-crm/planes`

### Implementation for User Story 8

- [X] T075 [US8] Implementar `PlanLecturaRepository` (Pinot read-only) en `backend/core/repositories/ventas_crm/plan_lectura_repository.py` — **sin** KafkaWriter/publish (research Decision 10)
- [X] T076 [US8] Implementar `ConsultaPlanesPublicosService` en `backend/apps/ventas_crm/services/consulta_planes_publicos_service.py` (proyección + mapa severidades)
- [X] T077 [US8] Implementar `PlanListView` (`AllowAny`) en `backend/apps/ventas_crm/views/plan_views.py` y registrar `GET ventas-crm/planes` en `backend/apps/ventas_crm/urls.py`
- [X] T078 [US8] Asegurar T072–T074 verdes tras implementación
- [X] T079 [Histórico-UI] [P] [US8] Implementar `PlanesApiService` en `frontend/src/app/modules/ventas-crm/services/planes-api.service.ts`
- [X] T080 [Histórico-UI] [P] [US8] Crear test unitario (AAA) en `frontend/src/app/modules/ventas-crm/services/planes-api.service.spec.ts`
- [X] T081 [Histórico-UI] [US8] Página `frontend/src/app/modules/ventas-crm/pages/catalogo-planes/` (loading / vacío accionable → registro / error con reintento; CTA a registro público)
- [X] T082 [Histórico-UI] [US8] Registrar ruta **pública** del catálogo (sin guard JWT) en `frontend/src/app/modules/ventas-crm/ventas-crm.routes.ts` y/o `frontend/src/app/app.routes.ts` según patrón de registro-publico

**Checkpoint**: `GET /planes` + UI Visitante verificables según quickstart §0.

---

## Phase 12: Polish delta RF-CPP-000

**Purpose**: E2E, quickstart Done when, cobertura del delta.

- [X] T083 [P] Extender E2E quickstart con paso 0 en `backend/apps/ventas_crm/tests/e2e/test_commercial_pipeline_quickstart_e2e.py` (o `test_planes_publicos_quickstart_e2e.py`) — marker `api`/`slow`
- [X] T084 Actualizar checklist / resultados en `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/quickstart.md` (Done when RF-CPP-000)
- [X] T085 [P] Ejecutar `pytest apps/ventas_crm/tests/ -k "plan or planes"` y corregir gaps de cobertura del delta bajo umbrales `testing.md`
- [X] T086 [P] Verificar en `.specify/docs/architecture/module-map.md` (#4) que el estado del embudo sigue coherente (lectura `Dim_Plan` documentada si aplica)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)** → **Foundational (2)** → bloquea US1–US7 *(completado)*
- **US1 (MVP)** habilita datos para US2–US5 *(completado)*
- **US2** puede ir en paralelo con US3 tras US1 *(completado)*
- **US3** antes de demos de huérfano; **US4** antes de **US5** *(completado)*
- **US6** independiente tras Foundational *(completado)*
- **US7** tras contratos US1–US6 *(completado)*
- **Polish embudo (Phase 10)** *(completado)*
- **US8** independiente del embudo (solo requiere T070 seed + mirror Pinot); puede ejecutarse sin tocar US1–US7
- **Polish delta (Phase 12)** tras US8

### User Story Dependencies

| Story | Depende de |
|-------|------------|
| US1–US7 | Phase 2 *(hecho)* |
| **US8** | T070–T071 (seed + DTOs); **no** depende de prospectos |
| Polish delta | US8 |

### Within US8

1. Tests repo/servicio/API (fallan) → 2. Repo lectura → 3. Servicio → 4. Vista/URL → 5. Tests verdes → 6. Angular service + página + rutas

### Parallel Opportunities (delta)

```text
# Foundational delta
T070 ; T071 [P]

# US8 tests
T072 || T073 || T074

# US8 frontend (tras API estable)
T079 || T080
T081 → T082

# Polish delta
T083 || T085 || T086 ; T084
```

---

## Parallel Example: User Story 8

```bash
# Tests primero (deben fallar):
pytest backend/apps/ventas_crm/tests/repositories/test_plan_lectura_repository.py -m repository
pytest backend/apps/ventas_crm/tests/services/test_consulta_planes_publicos_service.py -m service
pytest backend/apps/ventas_crm/tests/api/test_planes_publicos_contract.py -m api

# Luego T075–T077 y re-run hasta verde; después Angular T079–T082
```

---

## Implementation Strategy

### MVP First (histórico: US1)

1. Phase 1 + Phase 2  
2. Phase 3 (US1)  
3. **STOP** — validar quickstart §1 (registro + auto-asignación / huérfano)  

### Incremental Delivery (estado actual)

1. US1–US7 + Polish embudo — **hecho**  
2. **Siguiente MVP delta:** US8 (portal planes) → Polish Phase 12 → quickstart §0  

### Parallel Team Strategy (delta)

- Dev A: T070 + T072 + T075 (repo)  
- Dev B: T073 + T076 (servicio mapa)  
- Dev C: T074 + T077 (API)  
- Dev D: T071 + T079–T082 (Angular) tras contrato verde

---

## Notes

- Markers obligatorios: `@pytest.mark.repository` / `service` / `api` / `unit`; cuerpo AAA.
- No escribir Pinot/SQL fuera de `core/repositories/ventas_crm/` (salvo reutilizar repo Suscripciones solo-lectura si aparece).
- **RF-CPP-000:** prohibido `KafkaWriter` / publish a `Dim_Plan_topic` (Decision 10).
- `Ganado` solo vía conversión (US5); pipeline (US4) debe rechazarlo.
- Roles JWT: `GerenteVentas`, `GerenteCuentasPublicas`, `Administrador` (research Decision 5); seed obligatorio en T003.
- `Dim_Cliente`: un solo writer — `cuentas_clientes/cliente_repository.py` (T014/T015); no `cliente_escritura_repository` en ventas_crm.
- Mapa severidades: Básico→[Baja]; Profesional→[Baja,Media]; Empresarial→[Baja,Media,Alta]; desconocido→[] (plan igual se lista).
- Siguiente comando: `/speckit-implement` (o `/speckit-analyze` si se desea gate previo del delta).

---

---

> **Histórico-UI:** las fases/tareas Angular de este archivo quedan como registro pre-split. Trabajo UI nuevo → capa [`../frontend/`](../frontend/).
