# Tasks: Notificación de Prospectos a Ventas

**Input**: Design documents from `specs/003-operational/Ventas-CRM/notificacion-ventas/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/notificacion-ventas.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento del usuario (`testing-expert` + `testing.md`): cada tarea de **servicio** o **repositorio** trae su test con markers `unit` / `repository` / `service` / `api`, patrón **AAA** (Arrange-Act-Assert). Umbrales: repos ≥85%, services ≥80%, views/API ≥75% (RNF-NV-006).

**Organization**: Tareas por historia de usuario (mapeadas desde CU/RF/escenarios del spec; prioridad derivada del flujo demo→alerta→consulta).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: `US1`–`US5`
- Cada descripción incluye path exacto

### User Story Map

| Story | Prioridad | CU/RF | Independent Test |
|-------|-----------|-------|------------------|
| US1 | P1 🎯 MVP | O118 / RF-NV-001 (sesión) | `POST /demo/sesiones` con grant → token + `demo_expiracion`; resume sin nuevo `inicio_sesion`; grant malo → 401 |
| US2 | P1 | O118 / RF-NV-001 (interacciones) | `POST /demo/interacciones` con demo session → 201; JWT usuario → 401; >60/min → 429 |
| US3 | P1 | O122 / RF-NV-002 / RF-NV-003 | Job evalúa sesión histórica; con `idusuario` inserta notificación + email/push; sin dueño no inserta; dedup día UTC; re-eval ≤7d |
| US4 | P1 | RF-NV-004 | Gerente lista solo propias; Admin todas; cursor pagination |
| US5 | P2 | Frontend | Demo Angular + listado notificaciones (skeleton/vacío/error) |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extender `ventas_crm`, secrets demo, fixtures y contract-first.

- [X] T001 Extender estructura de tests/páginas según `plan.md`: asegurar dirs `backend/apps/ventas_crm/tests/{api,services,repositories,unit}/`, `frontend/src/app/modules/ventas-crm/{pages/demo-interactiva,pages/notificaciones-ventas,interceptors,services}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md`
- [X] T003 [P] Añadir settings `DEMO_GRANT_SECRET` y `DEMO_SESSION_SECRET` en `backend/config/settings.py` (+ env example si aplica)
- [X] T004 [P] Añadir fixtures `demo_grant_factory`, `demo_session_auth_headers` en `backend/conftest.py` (HMAC grant + Bearer typ=demo_session)
- [X] T005 [P] Generar DTOs TypeScript desde OpenAPI en `frontend/src/app/modules/ventas-crm/models/notificacion-ventas.types.ts` basados en `contracts/notificacion-ventas.openapi.yaml`
- [X] T006 [P] Registrar topics Kafka `Fact_Interaccion_Demo_topic` y `Fact_NotificacionVentas_topic` en config Kafka del proyecto (settings / topic registry existente)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios, auth demo, throttles, permisos, handoff `demo_grant`, routing — bloquea todas las historias.

**CRITICAL**: Ninguna US puede empezar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Ventas-CRM/notificacion-ventas/contracts/notificacion-ventas.openapi.yaml`
- [X] T008 Extender `ProspectoRepository` en `backend/core/repositories/ventas_crm/prospecto_repository.py` con `update_demo_expiracion(idprospecto, iso_utc)` vía Kafka `Dim_Prospecto_topic` (sin tocar otros campos)
- [X] T009 [P] Crear/actualizar test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_prospecto_repository_demo_expiracion.py`
- [X] T010 Implementar `InteraccionDemoRepository` (lectura Pinot + publish Kafka) en `backend/core/repositories/ventas_crm/interaccion_demo_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_interaccion_demo_repository.py`
- [X] T012 Implementar `NotificacionVentasRepository` (lectura Pinot + publish Kafka + `exists_dedup_dia_utc`) en `backend/core/repositories/ventas_crm/notificacion_ventas_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: `repository`, AAA) en `backend/apps/ventas_crm/tests/repositories/test_notificacion_ventas_repository.py` — assert dedup query + publish
- [X] T014 Implementar `DemoSessionAuthentication` + utilidades grant HMAC en `backend/apps/ventas_crm/authentication.py` (claims `typ=demo_session`, `idprospecto`, `exp`)
- [X] T015 [P] Crear test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_demo_session_authentication.py`
- [X] T016 [P] Crear test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_demo_grant_hmac.py` (firma válida/inválida, id mismatch)
- [X] T017 Extender permisos `IsGerenteOrAdminNotificaciones` en `backend/apps/ventas_crm/permissions.py`
- [X] T018 [P] Crear/actualizar test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_ventas_crm_permissions.py` cubriendo listado notificaciones
- [X] T019 Implementar `DemoSesionIpThrottle` y `DemoInteraccionTokenThrottle` (60/min por token) en `backend/apps/ventas_crm/throttles.py`
- [X] T020 [P] Crear test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_demo_throttles.py`
- [X] T021 Extender emisión de `demo_grant` en `backend/apps/ventas_crm/services/registro_prospecto_service.py` y en la vista/respuesta de `POST /ventas-crm/prospectos`; actualizar el contrato OpenAPI de `#04` en `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/contracts/commercial-pipeline-prospects.openapi.yaml` (campo aditivo `data.demo_grant`, sin breaking change) y alinear DTOs/fixtures de registro si aplica
- [X] T022 [P] Crear/actualizar test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_registro_prospecto_service.py` assert `demo_grant` presente y verificable; actualizar test API de registro (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_registro_prospecto_contract.py` para el campo `demo_grant`
- [X] T023 Registrar rutas en `backend/apps/ventas_crm/urls.py` para `/demo/sesiones`, `/demo/interacciones`, `/notificaciones` apuntando a vistas aún no implementadas: hasta completar US1/US2/US4 las rutas pueden devolver 404/501 **sin** lógica de dominio ni acceso a Kafka/Pinot en la vista

**Checkpoint**: Repos, auth demo, throttles, grant handoff y routing listos.

---

## Phase 3: User Story 1 — Abrir / reanudar sesión de demo (Priority: P1) 🎯 MVP

**Goal**: O118 sesión — primer canje fija `demo_expiracion` + `inicio_sesion`; resume reemite token sin nuevo `inicio_sesion`.

**Independent Test**: Grant válido + `demo_expiracion` null → 200 `modo=primer_canje`; mismo grant con demo activa → `modo=resume`; grant inválido → 401; expirada → 403; inactivo → 403.

**Measurable Criteria**: CA-NV-001, CA-NV-008, CA-NV-009; Escenarios 1, 8, 9; RN-NV-006.

### Tests for User Story 1

- [X] T024 [P] [US1] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_demo_sesion_service.py` (primer canje, resume, expirada, inactivo) — debe fallar antes de implementar
- [X] T025 [P] [US1] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_demo_sesiones_contract.py` alineado a OpenAPI

### Implementation for User Story 1

- [X] T026 [US1] Implementar `DemoSesionService` en `backend/apps/ventas_crm/services/demo_sesion_service.py`
- [X] T027 [US1] Implementar `POST /demo/sesiones` en `backend/apps/ventas_crm/views/demo_views.py` + wire `DemoSesionIpThrottle`
- [X] T028 [US1] Asegurar T024–T025 verdes (AAA, markers) tras implementación

**Checkpoint**: MVP apertura/resume de demo operable vía API.

---

## Phase 4: User Story 2 — Ingesta de interacciones (Priority: P1)

**Goal**: O118 interacciones — persistir eventos con token de sesión; rate limit 60/min; sin evaluación síncrona.

**Independent Test**: Bearer demo → 201; user JWT → 401; token expirado → 403; >60/min → 429; `tiempo_seccion` sin `duracion_ms` → 400.

**Measurable Criteria**: CA-NV-007; Escenario 7; RNF-NV-004 (parcial).

### Tests for User Story 2

- [X] T029 [P] [US2] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_ingesta_interaccion_demo_service.py`
- [X] T030 [P] [US2] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_demo_interacciones_contract.py`

### Implementation for User Story 2

- [X] T031 [US2] Implementar `IngestaInteraccionDemoService` en `backend/apps/ventas_crm/services/ingesta_interaccion_demo_service.py`
- [X] T032 [US2] Implementar `POST /demo/interacciones` en `backend/apps/ventas_crm/views/demo_views.py` con `DemoSessionAuthentication` + `DemoInteraccionTokenThrottle`
- [X] T033 [US2] Asegurar T029–T030 verdes

**Checkpoint**: Telemetría de demo fluye a Kafka/Pinot.

---

## Phase 5: User Story 3 — Evaluación de reglas + despacho (Priority: P1)

**Goal**: O122 + RF-NV-003 — job ≤60s; agregación por sesión histórica; dedup día UTC; email/push; slack → error explícito sin fallback.

**Independent Test**: Sesión con ≥5min precios + `idusuario` → fila `tiempo_seccion_precios_5min` + EmailNotifier; 3× pricing → `visito_pricing_3x` + Push; sin `idusuario` → 0 inserts; segunda corrida mismo día → 0 dup; sesión con `demo_expiracion` en ≤7d y asignación tardía → notifica.

**Measurable Criteria**: CA-NV-002, CA-NV-003, CA-NV-004, CA-NV-005; Escenarios 2–5; RNF-NV-002/003; Decisiones 1–4 research.

### Tests for User Story 3

- [X] T034 [P] [US3] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_evaluacion_reglas_demo_service.py` (catálogo MVP, sesión histórica, dedup, huérfano, ventana 7d)
- [X] T035 [P] [US3] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_despacho_notificacion_ventas_service.py` (email/push OK; slack → canal no disponible)
- [X] T036 [P] [US3] Crear test unitario (marker: `unit`, AAA) en `backend/apps/ventas_crm/tests/unit/test_reglas_demo_catalog.py` (umbrales 300_000 ms y count≥3)

### Implementation for User Story 3

- [X] T037 [US3] Implementar catálogo/evaluadores RN-NV-003 en `backend/apps/ventas_crm/services/reglas_demo_catalog.py`
- [X] T038 [US3] Implementar `EvaluacionReglasDemoService` en `backend/apps/ventas_crm/services/evaluacion_reglas_demo_service.py`
- [X] T039 [US3] Implementar `DespachoNotificacionVentasService` en `backend/apps/ventas_crm/services/despacho_notificacion_ventas_service.py` usando `core/notificaciones`
- [X] T040 [US3] Registrar Celery task + beat schedule ≤60s en `backend/apps/ventas_crm/tasks.py` y config Celery del proyecto
- [X] T041 [US3] Asegurar T034–T036 verdes; añadir test de tarea (marker: `service` o `unit`, AAA) en `backend/apps/ventas_crm/tests/services/test_evaluacion_reglas_demo_task.py` que invoque la task con mocks

**Checkpoint**: Motor de reglas notifica dentro del SLA ≤2 min en ambiente de prueba.

---

## Phase 6: User Story 4 — Consulta de notificaciones (Priority: P1)

**Goal**: RF-NV-004 — listado cursor con RBAC Gerente vs Admin.

**Independent Test**: Gerente solo `idusuariogerentenotificado=él`; Admin todas + filtro `?idusuario=`; sin JWT → 401; rol no CRM → 403.

**Measurable Criteria**: CA-NV-006; Escenario 6; RNF-NV-005 (API lista).

### Tests for User Story 4

- [X] T042 [P] [US4] Crear test de servicio (marker: `service`, AAA) en `backend/apps/ventas_crm/tests/services/test_consulta_notificacion_ventas_service.py`
- [X] T043 [P] [US4] Crear test de API (marker: `api`, AAA) en `backend/apps/ventas_crm/tests/api/test_notificaciones_ventas_contract.py`

### Implementation for User Story 4

- [X] T044 [US4] Implementar `ConsultaNotificacionVentasService` en `backend/apps/ventas_crm/services/consulta_notificacion_ventas_service.py`
- [X] T045 [US4] Implementar `GET /notificaciones` en `backend/apps/ventas_crm/views/notificacion_views.py`
- [X] T046 [US4] Asegurar T042–T043 verdes

**Checkpoint**: Auditoría de alertas operable vía API.

---

## Phase 7: User Story 5 — Frontend Angular demo + notificaciones (Priority: P2)

**Goal**: Consumir contrato con servicios tipados, interceptor demo, guards y UI loading/vacío/error (RNF-NV-005).

**Independent Test**: Flujo quickstart UI — abrir demo con grant → enviar interacciones → ver notificaciones como Gerente (skeleton/vacío/error).

**Measurable Criteria**: RNF-NV-005; quickstart §Frontend.

### Implementation for User Story 5

- [X] T047 [P] [US5] Implementar `DemoSessionInterceptor` en `frontend/src/app/modules/ventas-crm/interceptors/demo-session.interceptor.ts`
- [X] T048 [P] [US5] Crear test unitario (AAA) en `frontend/src/app/modules/ventas-crm/interceptors/demo-session.interceptor.spec.ts`
- [X] T049 [P] [US5] Implementar `DemoApiService` en `frontend/src/app/modules/ventas-crm/services/demo-api.service.ts`
- [X] T050 [P] [US5] Crear test unitario (AAA) en `frontend/src/app/modules/ventas-crm/services/demo-api.service.spec.ts`
- [X] T051 [P] [US5] Implementar `NotificacionApiService` en `frontend/src/app/modules/ventas-crm/services/notificacion-api.service.ts`
- [X] T052 [P] [US5] Crear test unitario (AAA) en `frontend/src/app/modules/ventas-crm/services/notificacion-api.service.spec.ts`
- [X] T053 [US5] Página demo interactiva `frontend/src/app/modules/ventas-crm/pages/demo-interactiva/` (grant → sesión → eventos; estados error)
- [X] T054 [US5] Página notificaciones `frontend/src/app/modules/ventas-crm/pages/notificaciones-ventas/` (skeleton / vacío accionable / error+retry)
- [X] T055 [US5] Completar rutas lazy demo + notificaciones en `frontend/src/app/modules/ventas-crm/ventas-crm.routes.ts` (reutilizar `admin-o-gerente-crm.guard.ts`)

**Checkpoint**: UI operable contra API según quickstart.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cobertura, SLA, quickstart E2E, mapa y calidad.

- [X] T056 Ejecutar suite `pytest -m "repository or service or api"` en tests de notificacion-ventas / `ventas_crm` afectados y corregir gaps bajo umbrales `testing.md`
- [X] T057 [P] Añadir test de SLA evaluación (marker: `service` o `slow`, AAA) documentando INSERT ≤2 min / job ≤60s en `backend/apps/ventas_crm/tests/services/test_evaluacion_reglas_demo_sla.py` (mock reloj o skip condicional CI)
- [X] T058 Validar escenarios de `quickstart.md` contra API local; anotar checklist Done when en `specs/003-operational/Ventas-CRM/notificacion-ventas/quickstart.md`
- [X] T059 [P] Actualizar estado en `.specify/docs/architecture/module-map.md` (#5) a implementado cuando backend+frontend pasen
- [X] T060 [P] Revisar que no queden TODOs bloqueantes; Kafka solo en repositorios; sin adaptador Slack; sin columna `estado_envio`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)** → **Foundational (2)** → bloquea US1–US5
- **US1 (MVP)** habilita token/sesión para US2
- **US2** provee eventos para US3
- **US3** provee filas para US4
- **US4** independiente de UI; **US5** tras contratos US1+US4 estables (ideal US1–US4)
- **Polish** al final

### User Story Dependencies

| Story | Depende de |
|-------|------------|
| US1 | Phase 2 (grant handoff T021) |
| US2 | US1 (session token) |
| US3 | US2 (eventos) + Phase 2 repos |
| US4 | Phase 2 (+ datos US3 para demos) |
| US5 | Contratos US1–US4 preferible |

### Within Each Story

1. Tests servicio/API (fallan) → 2. Implementación servicio → 3. Vista/task → 4. Tests verdes  
Repos: Implementación repo → test repo AAA `[P]` en archivo dedicado.

### Parallel Opportunities

```text
# Phase 1
T002 || T003 || T004 || T005 || T006

# Phase 2 (pares repo+test)
T008→T009 || T010→T011 || T012→T013
T014→T015 || T016
T017→T018 || T019→T020

# US1 tests
T024 || T025

# US2 tests
T029 || T030

# US3 tests
T034 || T035 || T036

# US5
T047||T048 || T049||T050 || T051||T052
```

---

## Parallel Example: User Story 1

```bash
# Tests primero (deben fallar):
# - backend/apps/ventas_crm/tests/services/test_demo_sesion_service.py
# - backend/apps/ventas_crm/tests/api/test_demo_sesiones_contract.py

# Luego implementar:
# - services/demo_sesion_service.py
# - views/demo_views.py (POST sesiones)

# Verificar:
pytest -m "service or api" backend/apps/ventas_crm/tests/services/test_demo_sesion_service.py backend/apps/ventas_crm/tests/api/test_demo_sesiones_contract.py
```

---

## Implementation Strategy

### MVP First

1. Completar Phase 1–2  
2. Entregar **US1** (sesión demo) como MVP API  
3. Validar CA-NV-001/008/009  
4. Incremental: US2 → US3 → US4 → US5 → Polish  

### Incremental Delivery

- Tras US2: telemetría observable en Pinot  
- Tras US3: alertas reales email/push  
- Tras US4: auditoría Gerente  
- Tras US5: experiencia completa  

### Testing notes (`testing-expert`)

- Markers obligatorios por capa; nombres `test_{accion}_cuando_{condicion}`  
- AAA en todos los tests de repo/servicio/API/unit  
- Mock Pinot/Kafka vía fixtures `mock_pinot` / `mock_kafka`  
- No tests de integración real Kafka/Pinot requeridos para cerrar MVP (marker `integration` opcional fuera de alcance inmediato)

---

## Task Summary

| Métrica | Valor |
|---------|-------|
| **Total tasks** | 60 |
| **US1** | 5 (T024–T028) |
| **US2** | 5 (T029–T033) |
| **US3** | 8 (T034–T041) |
| **US4** | 5 (T042–T046) |
| **US5** | 9 (T047–T055) |
| **Setup + Foundational + Polish** | 28 (T001–T023, T056–T060) |
| **Parallel opportunities** | Pares repo/test, tests US en paralelo, servicios Angular en paralelo |
| **Suggested MVP** | Phase 1–2 + **US1** (abrir/resume demo) |
| **Format validation** | Todas las tareas: `- [ ]`, `Tnnn`, paths; stories con `[USx]`; `[P]` solo cuando aplica |
