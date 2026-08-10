# Tasks: Suscripciones y Facturación

**Input**: Design documents from `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/subscriptions-and-billing.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento del usuario + `testing.md` / skill `testing-expert`: **cada tarea de servicio o repositorio trae su test asociado** con markers `unit` / `repository` / `service` / `api` (y `integration` solo si aplica docker), patrón **AAA** (Arrange-Act-Assert). No se acepta código de dominio sin test.

**Organization**: Tareas agrupadas por historia de usuario para implementación y validación independiente.


> **Capas:** este archivo es autoridad de **dominio/API**.
> Tareas con paths `frontend/src` o marcadas `[Histórico-UI]` son del monolito pre-split;
> la autoridad Interaction Capability es [`../frontend/tasks.md`](../frontend/tasks.md) (`T-FE-*`).
> No reabrir ni re-implementar `[Histórico-UI]` desde la capa backend.
> `[Bridge-FE]` = tipos/cliente tipado generado desde OpenAPI del backend (sigue anclado al contrato BE).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US9`)
- Cada descripción incluye path exacto de archivo

### User Story Map

| Story | Prioridad | CU/RF | Escenarios spec / quickstart |
|-------|-----------|-------|------------------------------|
| US1 | P1 🎯 MVP | RF-001 O26/O27, RF-010 O28 | Esc. 0, 15; quickstart A (parcial) |
| US9 | P1 🎯 MVP delta | RF-001 listado + RNF-005a / CA-016 | Esc. 15b, 15c; quickstart **H** (reopen US1 listado) |
| US2 | P1 | RF-002 O29 | Esc. 1, 1b, 2 |
| US3 | P1 | RF-004 O30, RF-005 O31 | Esc. 6, 6b, 7–9; jobs facturación/dunning |
| US4 | P1 | RF-007 O35/O36 | Esc. 10, 11, 11b; quickstart D |
| US5 | P2 | RF-003 O33/O34 | Esc. 3–5, 4b, 4c |
| US6 | P2 | RF-008 O32, RF-009 O37 | Esc. 12, 13; renovación + cancelación |
| US7 | P2 | RF-006 O38 | Esc. 14; quickstart F |
| US8 | P2 | Frontend Angular | guards + pages + API services |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: App Django `suscripciones`, módulo Angular, fixtures JWT/billing y markers pytest.

- [X] T001 [Histórico-UI] Crear estructura de carpetas en `backend/apps/suscripciones/{views,services,services/pasarela,jobs,tests/{api,services,jobs,repositories,unit}}`, `backend/core/repositories/suscripciones/` y `frontend/src/app/modules/suscripciones/{pages,services,guards,services/models}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `integration`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Añadir fixtures billing en `backend/conftest.py`: `proveedor_billing_auth_headers`, `admin_billing_auth_headers`; alinear seed `Dim_Plan`/`Fact_Suscripcion` a Title Case (`Activa`, `Básico`, …) y campos `fecha_fin` / `limites` JSON
- [X] T004 [P] Crear stub app `backend/apps/suscripciones/apps.py` + `__init__.py` y registrar en `backend/config/settings.py` (`INSTALLED_APPS`, topics Kafka del data-model)
- [X] T005 [Bridge-FE] [P] Generar tipos TypeScript stub en `frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts` desde `contracts/subscriptions-and-billing.openapi.yaml`
- [X] T006 [Histórico-UI] [P] Crear módulo Angular lazy stub `frontend/src/app/modules/suscripciones/suscripciones.routes.ts` y registrar en `frontend/src/app/app.routes.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot, pasarela simulada, permisos RBAC, routing, evaluación de acceso — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/contracts/subscriptions-and-billing.openapi.yaml`
- [X] T008 Implementar `PlanRepository` (lectura Pinot + publish Kafka) en `backend/core/repositories/suscripciones/plan_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/suscripciones/tests/repositories/test_plan_repository.py`
- [X] T010 Implementar `MetodoPagoRepository` en `backend/core/repositories/suscripciones/metodo_pago_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/suscripciones/tests/repositories/test_metodo_pago_repository.py`
- [X] T012 Implementar `SuscripcionRepository` canónico (lectura/escritura; Title Case; RN-017 helpers) en `backend/core/repositories/suscripciones/suscripcion_repository.py` y documentar deprecación/adaptación de `backend/core/repositories/soporte/suscripcion_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/suscripciones/tests/repositories/test_suscripcion_repository.py`
- [X] T014 Implementar `FacturaRepository` (seq `numero_factura` max+1 + retry RN-026) en `backend/core/repositories/suscripciones/factura_repository.py`
- [X] T015 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/suscripciones/tests/repositories/test_factura_repository.py`
- [X] T016 Implementar `SolicitudCambioPlanRepository` en `backend/core/repositories/suscripciones/solicitud_cambio_plan_repository.py`
- [X] T017 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/suscripciones/tests/repositories/test_solicitud_cambio_plan_repository.py`
- [X] T018 Implementar puerto `PasarelaPagoPort` en `backend/apps/suscripciones/services/pasarela/base.py` y `SimuladorPasarela` (RN-024) en `backend/apps/suscripciones/services/pasarela/simulador_pasarela.py`
- [X] T019 [P] Crear test unitario (marker: `unit`, AAA) del simulador en `backend/apps/suscripciones/tests/unit/test_simulador_pasarela.py`
- [X] T020 Implementar `EvaluacionAccesoService` (RN-017) en `backend/apps/suscripciones/services/evaluacion_acceso_service.py`
- [X] T021 [P] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_evaluacion_acceso_service.py`
- [X] T022 Implementar permisos `IsProveedorCuenta`, `IsAdministradorBilling` en `backend/apps/suscripciones/permissions.py`
- [X] T023 [P] Crear test unitario (marker: `unit`, AAA) en `backend/apps/suscripciones/tests/unit/test_suscripciones_permissions.py`
- [X] T024 Crear `backend/apps/suscripciones/urls.py` + package `views/__init__.py` y registrar include en `backend/config/urls.py` bajo `api/v1/`
- [X] T086 Implementar manejo de header `Idempotency-Key` (api-standards) para escrituras billing en `backend/apps/suscripciones/idempotency.py` (o reutilizar utilidad `core/` si existe) y aplicarlo en views de escritura
- [X] T087 [P] Crear test API (marker: `api`, AAA) de idempotencia HTTP en `backend/apps/suscripciones/tests/api/test_idempotency_key_contract.py`
- [X] T088 [P] Configurar throttling DRF billing (research Decision 11: ~60 req/min Proveedor escrituras; ~100 req/min Admin) en `backend/apps/suscripciones/throttles.py` y referenciarlo desde views en `backend/apps/suscripciones/views/`
- [X] T089 [P] Crear test unitario (marker: `unit`, AAA) de throttles en `backend/apps/suscripciones/tests/unit/test_suscripciones_throttles.py`

**Checkpoint**: Repos, pasarela, permisos, acceso, routing, Idempotency-Key y throttles listos.

---

## Phase 3: User Story 1 — Catálogo de planes + alta de suscripción (Priority: P1) 🎯 MVP

**Goal**: Director de Estrategia gestiona `Dim_Plan` (RF-001); Proveedor contrata suscripción inicial (RF-010) con sync `plan_suscripcion` y ciclo Guayaquil.

**Independent Test**: Crear plan Básico activo → `POST /suscripciones` crea `Activa` con `fecha_fin = +1 mes`; segunda alta con `activo=true` existente → 409.

**Measurable Criteria**: CA-SUSF-001, CA-SUSF-010, CA-SUSF-011; Escenarios 0, 15.

### Tests for User Story 1

- [X] T025 [P] [US1] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_catalogo_plan_service.py`
- [X] T026 [P] [US1] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_alta_suscripcion_service.py`
- [X] T027 [P] [US1] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_planes_contract.py`
- [X] T028 [P] [US1] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_alta_suscripcion_contract.py`

### Implementation for User Story 1

- [X] T029 [US1] Implementar `CatalogoPlanService` en `backend/apps/suscripciones/services/catalogo_plan_service.py`
- [X] T030 [US1] Implementar `AltaSuscripcionService` en `backend/apps/suscripciones/services/alta_suscripcion_service.py` — sync `plan_suscripcion` **obligatorio** vía `ClienteRepository.update(...)` en `backend/core/repositories/cuentas_clientes/cliente_repository.py` → `Dim_Cliente_topic` (prohibido publicar Kafka/SQL desde el service)
- [X] T031 [US1] Implementar views `PlanListCreateView` / `PlanDetailView` en `backend/apps/suscripciones/views/plan_views.py`
- [X] T032 [US1] Implementar views `AltaSuscripcionView` / `MiSuscripcionView` en `backend/apps/suscripciones/views/suscripcion_views.py`
- [X] T033 [US1] Cablear rutas de planes y suscripción en `backend/apps/suscripciones/urls.py`

**Checkpoint**: MVP — plan + alta + GET mia con `acceso_permitido`.

---

## Phase 4: User Story 2 — Método de pago (Priority: P1)

**Goal**: Registrar/reemplazar método principal (RF-002); un solo `activo=true`; dispara regularización si hay mora (RN-021) cuando US4 exista — stub hook opcional.

**Independent Test**: Dos altas consecutivas dejan exactamente un método activo; no se persiste PAN/CVV.

**Measurable Criteria**: CA-SUSF-002; Escenarios 1, 2; RNF-001.

### Tests for User Story 2

- [X] T034 [P] [US2] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_metodo_pago_service.py`
- [X] T035 [P] [US2] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_metodo_pago_contract.py`

### Implementation for User Story 2

- [X] T036 [US2] Implementar `MetodoPagoService` en `backend/apps/suscripciones/services/metodo_pago_service.py` (tokenización vía simulador)
- [X] T037 [US2] Implementar `MetodoPagoListCreateView` en `backend/apps/suscripciones/views/metodo_pago_views.py` y rutas en `backend/apps/suscripciones/urls.py`

**Checkpoint**: Método de pago operable vía API.

---

## Phase 5: User Story 3 — Generación de facturas + cobro + dunning (Priority: P1)

**Goal**: Emitir facturas mensuales (RF-004) y cobrar con idempotencia (RF-005); jobs de facturación y dunning.

**Independent Test**: Suscripción Activa con método → una `Fact_Factura` por periodo; 3 fallos → `Fallida`; sin método → no factura + notificación mock.

**Measurable Criteria**: CA-SUSF-004, CA-SUSF-005, CA-SUSF-014, CA-SUSF-015; Escenarios 6–9.

### Tests for User Story 3

- [X] T038 [P] [US3] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_generacion_factura_service.py`
- [X] T039 [P] [US3] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_cobro_service.py`
- [X] T040 [P] [US3] Crear test de job (marker: `service`, AAA) en `backend/apps/suscripciones/tests/jobs/test_facturacion_mensual_job.py`
- [X] T041 [P] [US3] Crear test de job (marker: `service`, AAA) en `backend/apps/suscripciones/tests/jobs/test_dunning_job.py`

### Implementation for User Story 3

- [X] T042 [US3] Implementar `GeneracionFacturaService` en `backend/apps/suscripciones/services/generacion_factura_service.py` (`impuestos=0`, `FAC-{YYYYMM}-{seq}`)
- [X] T043 [US3] Implementar `CobroService` en `backend/apps/suscripciones/services/cobro_service.py` (claves `{id}-{reintentos}`)
- [X] T044 [US3] Implementar `facturacion_mensual_job.py` en `backend/apps/suscripciones/jobs/facturacion_mensual_job.py`
- [X] T045 [US3] Implementar `dunning_job.py` en `backend/apps/suscripciones/jobs/dunning_job.py`
- [X] T046 [US3] Añadir management commands `run_facturacion_mensual_job` y `run_dunning_job` bajo `backend/apps/suscripciones/management/commands/`

**Checkpoint**: Ciclo emitir→cobrar→dunning verificable por comando.

---

## Phase 6: User Story 4 — Mora: suspensión y reactivación (Priority: P1)

**Goal**: `Fallida` → `Suspendida` (RF-007); reintento auto tras método nuevo (RN-021) y acción `reintentar-cobro` (RN-028).

**Independent Test**: Tras 3 fallos acceso denegado; `POST .../reintentar-cobro` con éxito → `Activa`.

**Measurable Criteria**: CA-SUSF-007, CA-SUSF-012; Escenarios 10, 11, 11b; quickstart D.

### Tests for User Story 4

- [X] T047 [P] [US4] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_mora_suscripcion_service.py`
- [X] T048 [P] [US4] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_reintentar_cobro_contract.py`
- [X] T049 [P] [US4] Extender test de servicio método de pago (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_metodo_pago_service.py` para RN-021 (disparo regularización)

### Implementation for User Story 4

- [X] T050 [US4] Implementar `MoraSuscripcionService` en `backend/apps/suscripciones/services/mora_suscripcion_service.py` (clave `{id}-reactivacion-{idmetodopago}`)
- [X] T051 [US4] Enganchar suspensión desde `CobroService` al llegar a `Fallida` en `backend/apps/suscripciones/services/cobro_service.py`
- [X] T052 [US4] Enganchar RN-021 en `backend/apps/suscripciones/services/metodo_pago_service.py`
- [X] T053 [US4] Implementar `ReintentarCobroView` en `backend/apps/suscripciones/views/suscripcion_views.py` y ruta en `backend/apps/suscripciones/urls.py`
- [X] T054 [US4] Integrar notificaciones (mock/`core/notificaciones`) en suspensión/reactivación desde `backend/apps/suscripciones/services/mora_suscripcion_service.py`

**Checkpoint**: Mora end-to-end con acceso RN-017.

---

## Phase 7: User Story 5 — Cambio de plan (Priority: P2)

**Goal**: Upgrade auto / downgrade con aprobación admin (RF-003); una sola `Pendiente` (RN-023); solo desde `Activa` (RN-022).

**Independent Test**: Básico→Profesional autoaprueba; segunda solicitud con Pendiente → 409; Suspendida → 409.

**Measurable Criteria**: CA-SUSF-003, CA-SUSF-013; Escenarios 3–5, 4b, 4c.

### Tests for User Story 5

- [X] T055 [P] [US5] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`
- [X] T056 [P] [US5] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_cambio_plan_contract.py`

### Implementation for User Story 5

- [X] T057 [US5] Implementar `CambioPlanService` en `backend/apps/suscripciones/services/cambio_plan_service.py` (orden `nivel`; sync `plan_suscripcion` vía `ClienteRepository.update` en `backend/core/repositories/cuentas_clientes/cliente_repository.py` → `Dim_Cliente_topic`; sin Kafka directo desde el service)
- [X] T058 [US5] Implementar views de solicitud/aprobar/rechazar en `backend/apps/suscripciones/views/cambio_plan_views.py` y rutas en `backend/apps/suscripciones/urls.py`

**Checkpoint**: Cambio de plan completo vía API.

---

## Phase 8: User Story 6 — Renovación automática + cancelación (Priority: P2)

**Goal**: Extender ciclo y facturar (RF-008); cancelar con acceso residual (RF-009); job `activo=false` (RN-020).

**Independent Test**: Cancelar → sin renovación; job renovación no selecciona `Cancelada`; post-`fecha_fin` `activo=false`.

**Measurable Criteria**: CA-SUSF-008, CA-SUSF-009; Escenarios 12, 13.

### Tests for User Story 6

- [X] T059 [P] [US6] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_renovacion_service.py`
- [X] T060 [P] [US6] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_cancelacion_service.py`
- [X] T061 [P] [US6] Crear test de job (marker: `service`, AAA) en `backend/apps/suscripciones/tests/jobs/test_renovacion_job.py`
- [X] T062 [P] [US6] Crear test de job (marker: `service`, AAA) en `backend/apps/suscripciones/tests/jobs/test_mantenimiento_activo_job.py`
- [X] T063 [P] [US6] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_cancelacion_contract.py`

### Implementation for User Story 6

- [X] T064 [US6] Implementar `RenovacionService` en `backend/apps/suscripciones/services/renovacion_service.py`
- [X] T065 [US6] Implementar `CancelacionService` en `backend/apps/suscripciones/services/cancelacion_service.py`
- [X] T066 [US6] Implementar jobs `renovacion_job.py` y `mantenimiento_activo_job.py` en `backend/apps/suscripciones/jobs/`
- [X] T067 [US6] Management commands `run_renovacion_job` / `run_mantenimiento_activo_job` en `backend/apps/suscripciones/management/commands/`
- [X] T068 [US6] Implementar `CancelarSuscripcionView` en `backend/apps/suscripciones/views/suscripcion_views.py` y ruta en `backend/apps/suscripciones/urls.py`

**Checkpoint**: Ciclo de vida completo backend.

---

## Phase 9: User Story 7 — Historial de facturas (Priority: P2)

**Goal**: Consulta solo lectura con aislamiento por `idcliente` (RF-006); orden `fecha_emision` desc.

**Independent Test**: Proveedor no ve facturas ajenas; Admin sí con `?idcliente=`; lista ≤3 s en fixtures.

**Measurable Criteria**: CA-SUSF-006; Escenario 14; quickstart F.

### Tests for User Story 7

- [X] T069 [P] [US7] Crear test de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_consulta_factura_service.py`
- [X] T070 [P] [US7] Crear test API (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_facturas_contract.py`

### Implementation for User Story 7

- [X] T071 [US7] Implementar `ConsultaFacturaService` en `backend/apps/suscripciones/services/consulta_factura_service.py`
- [X] T072 [US7] Implementar `FacturaListView` / `FacturaDetailView` en `backend/apps/suscripciones/views/factura_views.py` y rutas en `backend/apps/suscripciones/urls.py`

**Checkpoint**: Contract OpenAPI de facturas cubierto.

---

## Phase 10: User Story 8 — Frontend Angular (Priority: P2)

**Goal**: Servicios tipados + guards + páginas mínimas consumiendo el contrato (skills `angular-architect`, `typescript-expert`).

**Independent Test**: Guard Director bloquea Admin/Proveedor en mutación de catálogo; historial muestra vacío/carga; mi-suscripción refleja `acceso_permitido`.

**Measurable Criteria**: RNF-SUSF-006; quickstart UI smoke.

### Tests for User Story 8

- [X] T073 [Histórico-UI] [P] [US8] Crear tests Jasmine (AAA) de `SuscripcionApiService` en `frontend/src/app/modules/suscripciones/services/suscripcion-api.service.spec.ts`
- [X] T074 [Histórico-UI] [P] [US8] Crear tests Jasmine (AAA) de guards en `frontend/src/app/modules/suscripciones/guards/proveedor-billing.guard.spec.ts` y `admin-billing.guard.spec.ts`

### Implementation for User Story 8

- [X] T075 [Histórico-UI] [P] [US8] Completar tipos desde OpenAPI en `frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts`
- [X] T076 [Histórico-UI] [P] [US8] Implementar `suscripcion-api.service.ts`, `plan-api.service.ts`, `metodo-pago-api.service.ts`, `factura-api.service.ts` en `frontend/src/app/modules/suscripciones/services/`
- [X] T077 [Histórico-UI] [US8] Implementar `proveedor-billing.guard.ts` y `admin-billing.guard.ts` en `frontend/src/app/modules/suscripciones/guards/`
- [X] T078 [Histórico-UI] [US8] Implementar pages stub funcionales `mi-suscripcion`, `metodos-pago`, `historial-facturas`, `cambio-plan`, `catalogo-planes`, `aprobaciones-downgrade` bajo `frontend/src/app/modules/suscripciones/pages/`
- [X] T079 [Histórico-UI] [US8] Cablear rutas lazy con guards en `frontend/src/app/modules/suscripciones/suscripciones.routes.ts`

**Checkpoint**: SPA billing usable contra API mock/real.

---

## Phase 11: Polish & Cross-Cutting

**Purpose**: Observabilidad, convergencia casing Soporte, quickstart E2E, cobertura.

- [X] T080 [P] Añadir logging estructurado de cobros/jobs (RNF-009) en `backend/apps/suscripciones/services/cobro_service.py` y jobs bajo `backend/apps/suscripciones/jobs/`
- [X] T081 [P] Crear test unitario (marker: `unit`, AAA) de logging/idempotencia edge en `backend/apps/suscripciones/tests/unit/test_cobro_idempotencia.py`
- [X] T082 Convertir `backend/core/repositories/soporte/suscripcion_repository.py` en **thin wrapper** que delega al repo canónico `backend/core/repositories/suscripciones/suscripcion_repository.py` (Title Case / RN-017); actualizar test en `backend/apps/soporte_cliente/tests/repositories/test_suscripcion_repository.py` (o crear si no existe)
- [X] T083 [P] Actualizar `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/quickstart.md` con comandos reales de management/pytest marcados
- [X] T084 Ejecutar suite `pytest backend/apps/suscripciones -m "not integration"` y corregir fallos de cobertura mínima repositorio ≥85% / servicio ≥80% según `testing.md`
- [X] T085 [P] Verificar `feature.json` apunta a `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing`
- [X] T090 [P] Smoke de performance no crítico: test `api`/`service` (marker: `api` o `slow`) que documente presupuesto CA-SUSF-006 (historial ≤3 s bajo fixtures) en `backend/apps/suscripciones/tests/api/test_facturas_latency_smoke.py`; RNF-SUSF-005 (job ≤30 min / 10k) queda como criterio de aceptación manual/load post-MVP documentado en el docstring del test

**Checkpoint**: Observabilidad, wrapper Soporte, cobertura, smoke latency y feature.json OK.

## Phase 12: Remediation — Actor RF-SUSF-001 → Director de Estrategia (2026-07-30)

**Goal**: Alinear RBAC y UI con `actors.md` / clarificación Session 2026-07-30: catálogo `Dim_Plan` solo `DirectorEstrategia`; Administrador conserva downgrades y facturas.

**Independent Test**: Usuario con rol `DirectorEstrategia` hace POST/PATCH planes → 2xx; Administrador en POST planes → 403; Admin sigue aprobando downgrade; FE muestra gestión de planes al Director (no stub solo-lectura).

- [X] T091 Extender `IsDirectorEstrategiaBilling` (rol JWT `DirectorEstrategia`) en `backend/apps/suscripciones/permissions.py`; POST/PATCH planes usan ese permiso (no `IsAdministradorBilling`); actualizar tests en `backend/apps/suscripciones/tests/unit/test_suscripciones_permissions.py` y `tests/api/test_planes_contract.py`
- [X] T092 [P] Seed `Dim_Rol` + usuario demo Director de Estrategia (script Kafka Pinot-compatible) en `backend/scripts/seed_demo_director_estrategia.py`
- [X] T093 [Histórico-UI] Guard FE `director-estrategia-billing.guard.ts` + tabs/nav: catálogo gestión solo `DirectorEstrategia`; Admin solo aprobaciones; redirect `/suscripciones` por rol (Director → catálogo, Admin → aprobaciones, Proveedor → mi-suscripcion) en `frontend/src/app/modules/suscripciones/`
- [X] T094 [US8 reopen] UI CRUD planes (crear/editar/desactivar) en `catalogo-planes` (o página `gestion-planes`) consumiendo `PlanApiService.crear`/`actualizar` — solo visible para `DirectorEstrategia`
- [X] T095 [Histórico-UI] [P] Tests Jasmine guards + página gestión planes; actualizar quickstart con login demo Director

**Checkpoint**: RF-SUSF-001 operable solo por Director de Estrategia end-to-end.

---

## Phase 12: Setup — Delta listado paginado (Shared)

**Purpose**: Gate de contrato OpenAPI v1.1.0 ya diseñado en `/speckit-plan`; confirmar alineación antes de código.

**Prior work**: T001–T095 entregados. Este bloque es el **delta** Clarification 2026-07-30 listado (Decision 13). UI pager → [`../frontend/tasks.md`](../frontend/tasks.md) tras este BE.

- [X] T096 Verificar que `listarPlanes` en `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/contracts/subscriptions-and-billing.openapi.yaml` documenta `cursor`, `limit` (default 20, max 100), `q`, `activo`, `nivel`, `solo_activos` deprecated, y `PlanListEnvelope.meta` → `PaginationMeta`

**Checkpoint**: Contrato listo para implementar.

---

## Phase 13: Foundational — Repo listado en origen (Blocking)

**Purpose**: Eliminar dump→slice en `PlanRepository.list`. Bloquea US9.

**CRITICAL**: No empezar vista/servicio de listado sin T097–T098.

- [X] T097 Reescribir `list` en `backend/core/repositories/suscripciones/plan_repository.py`: filtros `q` / `activo` / `nivel`, cursor `idplan > cursor`, `ORDER BY idplan ASC`, `LIMIT limit+1` (Decision 13); **prohibido** `SELECT * FROM Dim_Plan` sin tope + filtrar universo en Python; devolver filas de página (+ señal has_more / next_cursor)
- [X] T098 [P] Extender tests (marker: `repository`, AAA) en `backend/apps/suscripciones/tests/repositories/test_plan_repository.py`: ≤limit, next página, filtros q/activo/nivel, assert SQL/llamada Pinot con LIMIT (no dump)

**Checkpoint**: Repo lista páginas acotadas.

---

## Phase 14: User Story 9 — Listado paginado + filtros (Priority: P1) 🎯 MVP delta

**Goal**: `GET /suscripciones/planes` cumple RF-SUSF-001 listado, RNF-SUSF-005a, RN-SUSF-001a, Esc. 15b/15c, CA-SUSF-016.

**Independent Test**: JWT Director `GET .../planes?limit=20` → `data.length ≤ 20` + `meta.pagination`; filtros q/activo/nivel; Proveedor no ve inactivos; code/test prueba ausencia de dump completo.

### Tests (escribir / actualizar; fallan hasta T101)

- [X] T099 [P] [US9] Contract tests listado paginado/filtrado (marker: `api`, AAA) en `backend/apps/suscripciones/tests/api/test_planes_contract.py`: ≤limit, `next_cursor`, q/activo/nivel, compat `solo_activos`, rol no-Director fuerza activos, lista vacía coherente
- [X] T100 [P] [US9] Performance p95 listado &lt; 2 s (marker: `slow` / `performance`, AAA) en `backend/apps/suscripciones/tests/performance/test_list_planes_p95.py` (CA-SUSF-016; alinear a `.specify/docs/architecture/testing.md`)

### Implementation

- [X] T101 [US9] Extender `CatalogoPlanService.listar` en `backend/apps/suscripciones/services/catalogo_plan_service.py` con `cursor`, `limit`, filtros; devolver `{items, next_cursor, limit}` (o tupla equivalente); mapear `solo_activos` → `activo` si `activo` omitido; Director puede `activo` omitido/false; no-Director fuerza `activo=true`
- [X] T102 [P] [US9] Actualizar tests de servicio (marker: `service`, AAA) en `backend/apps/suscripciones/tests/services/test_catalogo_plan_service.py` para firma paginada + reglas de rol
- [X] T103 [US9] Actualizar `PlanListCreateView.get` en `backend/apps/suscripciones/views/plan_views.py`: parsear query params; `success_response(data, meta={"pagination": {"next_cursor": ..., "limit": ...}})`; validar `limit` 1..100 (default 20)
- [X] T104 [US9] Asegurar que mutaciones POST/PATCH y `find_by_id` siguen intactos; callers internos de `listar`/`list` (si los hay) migran a página o `find_by_id` — buscar usos en `backend/apps/suscripciones/` y ajustar

**Checkpoint**: Esc. 15b/15c vía API; CA-016 contract + p95.

---

## Phase 15: Polish — Delta listado

**Purpose**: Humo, bridge tipos, Docker.

- [X] T105 Ejecutar humo quickstart **H** en `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/quickstart.md` (páginas, filtros, rol)
- [X] T106 [P] [Bridge-FE] Extender tipos listado (`cursor|limit|q|activo|nivel` + `meta.pagination`) en `frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts` desde OpenAPI (UI pager = capa frontend)
- [X] T107 Rebuild Docker Django: `docker compose -f docker/accidentes.yml up -d --build django` y verificar `accidentes-django` Up

**Checkpoint**: Delta BE listo para `/speckit-tasks` + implement en capa frontend (FR-UI-019…021).

---

## Dependencies & Execution Order

### Story completion order (histórico + delta)

```text
[Histórico] Phase 1–2 → US1…US8 → Phase 11 Director (T091–T095)  [X]
[Delta activo]
  Phase 12 Setup (T096)
  → Phase 13 Foundational repo (T097–T098)
  → Phase 14 US9 (T099–T104) 🎯 MVP delta
  → Phase 15 Polish (T105–T107)
  → (siguiente capa) frontend FR-UI-019…021
```

### Parallel opportunities (delta)

- T099 ∥ T100 tras T096 (tests fallan hasta T103).
- T102 ∥ puede ir tras T101.
- T106 ∥ T105 tras T103.
- Tras T098: T101 → T103 en serie (mismo flujo GET).

### Independent test criteria (resumen)

| Story | Cómo probar solo |
|-------|------------------|
| US1 | API planes + POST `/suscripciones` + GET `/mia` |
| US9 | `GET /planes?limit=20` + filtros + `meta.pagination`; repo sin dump; p95 |
| US2 | POST/GET métodos-pago + assert un activo |
| US3 | management facturación/dunning + asserts Pinot fake |
| US4 | forzar Fallida → Suspendida → reintentar-cobro |
| US5 | upgrade/downgrade + 409 doble Pendiente |
| US6 | cancelar + renovacion_job no la toma |
| US7 | GET facturas aislamiento idcliente |
| US8 | Jasmine guards/services + smoke routes |

---

## Implementation Strategy

### MVP histórico (ya entregado)

Phase 1–2 + US1…US8 + Director T091–T095.

### MVP delta (ship ahora)

1. T096 → T097–T098 → T101–T104 (con T099–T100).
2. Validar quickstart **H** + T107.
3. Luego capa frontend: filtros/pager catálogo planes.

### Incremental delivery

US9 no reabre mutaciones de plan ni jobs; solo lectura listado. Callers internos migran o usan `find_by_id`.

---

## Format validation

- Todas las tareas usan `- [ ]` / `- [X]`, ID `Tnnn`, paths de repo, labels `[US9]` en fase de historia delta.
- Toda implementación de **servicio** o **repositorio** del delta tiene tarea de test pareja con marker y AAA.
- Remediation analyze 2026-07-26: C1–C4 / A1 (histórico). Enmienda listado 2026-07-30: T096–T107.

---

> **Histórico-UI:** las fases/tareas Angular de este archivo quedan como registro pre-split. Trabajo UI pager/filtros → capa [`../frontend/`](../frontend/) tras T107.
