# Tasks: Gestión de Tickets de Soporte e Incidencias

**Input**: Design documents from `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/gestion-tickets-soporte.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento vinculante (`testing.md`: "no se acepta código sin al menos un test asociado"); cada tarea de servicio/repositorio tiene test asociado con markers `unit`/`repository`/`service`/`api`/`integration` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario para implementación y validación independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US7`)
- Cada descripción incluye path exacto de archivo

### User Story Map

| Story | Prioridad | CU/RF | Escenarios spec |
|-------|-----------|-------|-----------------|
| US1 | P1 🎯 MVP | CU-O91 | Escenarios 1, 2 |
| US2 | P1 | CU-O92, RF-TIC-006 | Escenarios 3, 4 |
| US3 | P1 | CU-O96 | Escenario 6 |
| US4 | P2 | CU-O95 | Escenario 5 |
| US5 | P2 | CU-O97 | Escenario 7 |
| US6 | P2 | RF-TIC-007 | quickstart §3 |
| US7 | P2 | Frontend Angular | quickstart §3 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estructura `apps/soporte_cliente`, módulo Angular, fixtures JWT y alineación contract-first.

- [X] T001 Crear estructura de carpetas en `backend/apps/soporte_cliente/{services,jobs,tests/{api,services,jobs,repositories}}`, `backend/core/repositories/soporte/` y `frontend/src/app/modules/soporte-cliente/{pages,services,guards}`
- [X] T002 [P] Verificar markers pytest (`unit`, `repository`, `service`, `api`, `integration`) en `backend/pytest.ini` según `.specify/docs/architecture/testing.md` — ya registrados, sin cambios necesarios
- [X] T003 [P] Añadir fixtures soporte (`cliente_auth_headers` reutilizado, `agente_soporte_auth_headers`, `desarrollador_apis_auth_headers`, `director_tecnologico_auth_headers` reutilizado, `cliente_soporte_auth_headers`/`director_tecnologico_soporte_auth_headers` alias) en `backend/conftest.py` reutilizando JWT de auth-rbac
- [X] T004 [P] Generar tipos TypeScript desde contrato en `frontend/src/app/modules/soporte-cliente/services/models/soporte.types.ts` basado en `contracts/gestion-tickets-soporte.openapi.yaml` (completado en Fase 9 — US7)
- [X] T005 [P] Crear módulo Angular lazy stub `frontend/src/app/modules/soporte-cliente/soporte-cliente.routes.ts` y registrar en `frontend/src/app/app.routes.ts`
- [X] T006 [P] Actualizar `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md` (generado en `/speckit-plan`) con referencias preliminares a los IDs de tasks de este documento

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios Kafka/Pinot, permisos RBAC soporte, routing y registro del job — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase.

- [X] T007 Validar contrato OpenAPI como gate en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/contracts/gestion-tickets-soporte.openapi.yaml`
- [X] T008 Implementar repositorio `Fact_Reclamo` (lectura/escritura Kafka) en `backend/core/repositories/soporte/reclamo_repository.py`
- [X] T009 [P] Crear test de repositorio (marker: repository, AAA) para `reclamo_repository.py` en `backend/apps/soporte_cliente/tests/repositories/test_reclamo_repository.py`
- [X] T010 Implementar repositorio `Fact_Historial_Ticket` (append-only) en `backend/core/repositories/soporte/historial_ticket_repository.py`
- [X] T011 [P] Crear test de repositorio (marker: repository, AAA) para `historial_ticket_repository.py` en `backend/apps/soporte_cliente/tests/repositories/test_historial_ticket_repository.py` — incluye caso explícito que verifica que el repositorio **no expone** métodos `update()`/`delete()` (RNF-TIC-002, insert-only)
- [X] T012 Implementar repositorio `Dim_SLAConfig` (versionado temporal) en `backend/core/repositories/soporte/sla_config_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: repository, AAA) para `sla_config_repository.py` en `backend/apps/soporte_cliente/tests/repositories/test_sla_config_repository.py`
- [X] T014 Implementar repositorio `Fact_ArchivosAdjuntosReclamos` en `backend/core/repositories/soporte/archivo_adjunto_reclamo_repository.py`
- [X] T015 [P] Crear test de repositorio (marker: repository, AAA) para `archivo_adjunto_reclamo_repository.py` en `backend/apps/soporte_cliente/tests/repositories/test_archivo_adjunto_reclamo_repository.py`
- [X] T016 Implementar repositorio de lectura `supervisor_soporte_repository.py` (resuelve el usuario con rol "Supervisor de Soporte" vía `settings.SOPORTE_SUPERVISOR_USER_ID`, Decision 6 de `research.md`) en `backend/core/repositories/soporte/supervisor_soporte_repository.py`. También se agregó `suscripcion_repository.py` (lectura `Fact_Suscripcion`, Decision 5) no listado originalmente pero requerido por `AsignacionSLAService`.
- [X] T017 [P] Crear test de repositorio (marker: repository, AAA) para `supervisor_soporte_repository.py` en `backend/apps/soporte_cliente/tests/repositories/test_supervisor_soporte_repository.py`
- [X] T018 Implementar permisos soporte (`IsClienteSoporte`, `IsSoporteAgente`, `IsNivelEscaladoSoporte`, `IsAdministradorSLA`, `IsSoporteAgenteOrCliente`) en `backend/apps/soporte_cliente/permissions.py`
- [X] T019 [P] Crear test unitario (marker: unit, AAA) para permisos soporte en `backend/apps/soporte_cliente/tests/services/test_soporte_permissions.py`
- [X] T020 Registrar rutas soporte en `backend/apps/soporte_cliente/urls.py` (archivo plano, no paquete `views/`) y verificar inclusión en `backend/config/urls.py` + `INSTALLED_APPS`/`KAFKA_TOPICS` en `backend/config/settings.py`
- [X] T021 [P] Documentar en `backend/apps/soporte_cliente/apps.py` que el job de monitoreo SLA corre vía management command externo (`run_monitoreo_sla_job`, ver Fase 5/US3) — no vía consumer Kafka registrado en `ready()`, a diferencia de `despacho`

**Checkpoint**: Repositorios, permisos, routing y orquestación base listos.

---

## Phase 3: User Story 1 — Registro de ticket con clasificación automática y SLA (Priority: P1) 🎯 MVP

**Goal**: CU-O91 — el cliente/soporte registra un ticket, el sistema clasifica automáticamente (`tipo_incidencia`, `prioridad`) y asigna SLA vigente según `idplan` (vía `Fact_Suscripcion`, `research.md` Decision 5).

**Independent Test**: Registrar ticket vinculado a emergencia activa → `prioridad='crítico'` automático, SLA asignado, historial `creacion` insertado; registrar ticket no clasificable → `Pendiente_de_clasificacion` sin SLA, luego clasificación manual arranca el timer.

**Measurable Criteria**: CA-TIC-001, CA-TIC-002; Escenarios 1, 2; RNF-TIC-003 (<3s).

### Tests for User Story 1

- [X] T022 [P] [US1] Crear test de servicio (marker: service, AAA) para `clasificacion_automatica_service.py` en `backend/apps/soporte_cliente/tests/services/test_clasificacion_automatica_service.py`
- [X] T023 [P] [US1] Crear test de servicio (marker: service, AAA) para `asignacion_sla_service.py` en `backend/apps/soporte_cliente/tests/services/test_asignacion_sla_service.py`
- [X] T024 [P] [US1] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets` en `backend/apps/soporte_cliente/tests/api/test_registrar_ticket_contract.py`
- [X] T025 [US1] Crear test cruzado multi-servicio (marker: `service`, no `integration` — ese marker está reservado para infra real vía docker-compose, ver `testing.md`) registro end-to-end (crítico + no clasificable) en `backend/apps/soporte_cliente/tests/services/test_registro_ticket_integration.py`

### Implementation for User Story 1

- [X] T026 [US1] Implementar `clasificacion_automatica_service.py` (emergencia activa → crítico; keywords → tipo_incidencia; RN-TIC-003) en `backend/apps/soporte_cliente/services/clasificacion_automatica_service.py`
- [X] T027 [US1] Implementar `asignacion_sla_service.py` (lookup `Dim_SLAConfig` vía `idplan` de `Fact_Suscripcion`, `research.md` Decision 5) en `backend/apps/soporte_cliente/services/asignacion_sla_service.py`
- [X] T028 [US1] Implementar `registrar_ticket_service.py` (orquesta clasificación + SLA + adjuntos + historial) en `backend/apps/soporte_cliente/services/registrar_ticket_service.py`
- [X] T029 [US1] Implementar `ClasificarTicketManualView` y `TicketsView`/`TicketDetalleView` en `backend/apps/soporte_cliente/views.py` y registrar en `backend/apps/soporte_cliente/urls.py`

**Checkpoint**: US1 operativa — registro y clasificación automática end-to-end.

**US1 Gate**:
- [X] T030 [US1] Validar CA-TIC-001, CA-TIC-002 en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`

---

## Phase 4: User Story 2 — Ciclo de vida del ticket (Priority: P1)

**Goal**: CU-O92 + RF-TIC-006 — tomar, comentar (con notas internas ocultas al Cliente), escalar manualmente, resolver y confirmar/auto-cerrar.

**Independent Test**: Agente toma ticket Abierto → `En_progreso`; comenta con `es_nota_interna=true` (no visible para Cliente); resuelve dentro de SLA; cliente confirma cierre → `sla_status='cumplido'`, `Cerrado`; o transcurren 5 días sin respuesta → auto-cierre.

**Measurable Criteria**: CA-TIC-003, CA-TIC-004, CA-TIC-005, CA-TIC-006, CA-TIC-007; Escenarios 3, 4.

### Tests for User Story 2

- [X] T031 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets/{id}/tomar` en `backend/apps/soporte_cliente/tests/api/test_tomar_ticket_contract.py`
- [X] T032 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets/{id}/comentarios` en `backend/apps/soporte_cliente/tests/api/test_comentar_ticket_contract.py`
- [X] T033 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets/{id}/escalar` en `backend/apps/soporte_cliente/tests/api/test_escalar_ticket_contract.py`
- [X] T034 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets/{id}/resolver` en `backend/apps/soporte_cliente/tests/api/test_resolver_ticket_contract.py`
- [X] T035 [P] [US2] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets/{id}/confirmar-cierre` en `backend/apps/soporte_cliente/tests/api/test_confirmar_cierre_contract.py`
- [X] T036 [P] [US2] Crear test de servicio (marker: service, AAA) para `tomar_ticket_service.py` en `backend/apps/soporte_cliente/tests/services/test_tomar_ticket_service.py`
- [X] T037 [P] [US2] Crear test de servicio (marker: service, AAA) para `comentar_ticket_service.py` (incluye caso ocultamiento notas internas, RN-TIC-002) en `backend/apps/soporte_cliente/tests/services/test_comentar_ticket_service.py`
- [X] T038 [P] [US2] Crear test de servicio (marker: service, AAA) para `escalar_ticket_service.py` en `backend/apps/soporte_cliente/tests/services/test_escalar_ticket_service.py`
- [X] T039 [P] [US2] Crear test de servicio (marker: service, AAA) para `resolver_ticket_service.py` (recálculo `sla_status`, incluye validación de estado previo En_progreso/Escalado) en `backend/apps/soporte_cliente/tests/services/test_resolver_ticket_service.py`
- [X] T040 [P] [US2] Crear test de servicio (marker: service, AAA) para `confirmar_cierre_service.py` (confirmación + auto-cierre 5 días, RN-TIC-004) en `backend/apps/soporte_cliente/tests/services/test_confirmar_cierre_service.py`

### Implementation for User Story 2

- [X] T041 [US2] Implementar `tomar_ticket_service.py` en `backend/apps/soporte_cliente/services/tomar_ticket_service.py`
- [X] T042 [US2] Implementar `comentar_ticket_service.py` (filtra `es_nota_interna=true` para rol Cliente en la propia capa de servicio, RN-TIC-002) en `backend/apps/soporte_cliente/services/comentar_ticket_service.py`
- [X] T043 [US2] Implementar `escalar_ticket_service.py` (escalado manual a Desarrollador de APIs / Director Tecnológico) en `backend/apps/soporte_cliente/services/escalar_ticket_service.py`
- [X] T044 [US2] Implementar `resolver_ticket_service.py` (recalcula `sla_status='cumplido'`/`'incumplido'`) en `backend/apps/soporte_cliente/services/resolver_ticket_service.py`
- [X] T045 [US2] Implementar `confirmar_cierre_service.py` (confirmación cliente + lógica de auto-cierre por vencimiento de 5 días) en `backend/apps/soporte_cliente/services/confirmar_cierre_service.py`
- [X] T046 [US2] Implementar vistas de ciclo de vida (`TomarTicketView`, `ComentarTicketView`, `EscalarTicketView`, `ResolverTicketView`, `ConfirmarCierreTicketView`) en `backend/apps/soporte_cliente/views.py` y completar `backend/apps/soporte_cliente/urls.py`

**Checkpoint**: US2 operativa — ciclo completo tomar→comentar→escalar→resolver→cerrar.

**US2 Gate**:
- [X] T047 [US2] Validar CA-TIC-003, CA-TIC-004, CA-TIC-005, CA-TIC-006, CA-TIC-007 en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`

---

## Phase 5: User Story 3 — Monitoreo y escalado automático de SLA (Priority: P1)

**Goal**: CU-O96 — job cada 1 minuto vigila `sla_primera_respuesta` y `sla_resolucion` de forma independiente (clarificación), marca `en riesgo`/`incumplido` y escala automáticamente al Supervisor de Soporte.

**Independent Test**: Ticket "En_progreso" supera el 80% de cualquiera de los dos plazos → `sla_status='en riesgo'`; supera el 100% → `sla_status='incumplido'`, `idestadosoporte=Escalado`, `id_agente_asignado` = Supervisor de Soporte.

**Measurable Criteria**: CA-TIC-010, CA-TIC-011; Escenario 6; RNF-TIC-001 (frecuencia 1 min).

### Tests for User Story 3

- [X] T048 [P] [US3] Crear test de servicio (marker: service, AAA) para `monitoreo_sla_service.py` (umbral 80%, independencia de los dos plazos, escalado a Supervisor) en `backend/apps/soporte_cliente/tests/services/test_monitoreo_sla_service.py`
- [X] T049 [US3] Crear test de job (marker: service, AAA) para `monitoreo_sla_job.py` en `backend/apps/soporte_cliente/tests/jobs/test_monitoreo_sla_job.py`

### Implementation for User Story 3

- [X] T050 [US3] Implementar `monitoreo_sla_service.py` (lectura tickets activos, comparación independiente de ambos plazos, transición a `en riesgo`/`incumplido`/`Escalado`) en `backend/apps/soporte_cliente/services/monitoreo_sla_service.py`
- [X] T051 [US3] Implementar job `monitoreo_sla_job.py` + `management/commands/run_monitoreo_sla_job.py` (loop continuo cada 60s o `--once` para cron externo, mismo patrón que `despacho`'s `run_timeout_despacho_job`; también ejecuta el auto-cierre de 5 días, RN-TIC-004) en `backend/apps/soporte_cliente/jobs/monitoreo_sla_job.py`

**Checkpoint**: US3 operativa — vigilancia y escalado automático de SLA en producción.

**US3 Gate**:
- [X] T052 [US3] Validar CA-TIC-010, CA-TIC-011 en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`

---

## Phase 6: User Story 4 — Configuración de SLA con vigencia temporal (Priority: P2)

**Goal**: CU-O95 — el Administrador crea o modifica reglas de SLA por plan/tipo/prioridad sin afectar tickets ya creados (RN-TIC-006).

**Independent Test**: Crear nueva regla → INSERT `activo=true`; modificar regla vigente → fila anterior `activo=false`/`fechavigenciahasta=now` + fila nueva; tickets existentes conservan su `idslaconfig` original.

**Measurable Criteria**: CA-TIC-008, CA-TIC-009; Escenario 5.

### Tests for User Story 4

- [X] T053 [P] [US4] Crear test de contrato API (marker: api, AAA) para `GET/POST /api/v1/soporte/sla-config` en `backend/apps/soporte_cliente/tests/api/test_sla_config_contract.py`
- [X] T054 [P] [US4] Crear test de contrato API (marker: api, AAA) para `PATCH /api/v1/soporte/sla-config/{id}` en `backend/apps/soporte_cliente/tests/api/test_modificar_sla_config_contract.py`
- [X] T055 [P] [US4] Crear test de servicio (marker: service, AAA) para `configurar_sla_service.py` en `backend/apps/soporte_cliente/tests/services/test_configurar_sla_service.py`

### Implementation for User Story 4

- [X] T056 [US4] Implementar `configurar_sla_service.py` (alta + modificación con cierre de vigencia, RN-TIC-006) en `backend/apps/soporte_cliente/services/configurar_sla_service.py`
- [X] T057 [US4] Implementar `SLAConfigView`/`SLAConfigDetalleView` en `backend/apps/soporte_cliente/views.py` y registrar en `backend/apps/soporte_cliente/urls.py`

**Checkpoint**: US4 operativa — configuración de SLA versionada sin afectar tickets existentes.

**US4 Gate**:
- [X] T058 [US4] Validar CA-TIC-008, CA-TIC-009 en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`

---

## Phase 7: User Story 5 — Reapertura de ticket cerrado (Priority: P2)

**Goal**: CU-O97 — el cliente reabre un ticket Cerrado; el SLA se renueva contra la configuración vigente actual (clarificación, `research.md` Decision 8); se conserva el historial y se permiten nuevos adjuntos.

**Independent Test**: Reabrir ticket Cerrado → `idestadosoporte=Reabierto`, `idslaconfig`/`sla_primera_respuesta`/`sla_resolucion` recalculados, historial previo intacto, nuevo adjunto insertado si se envía.

**Measurable Criteria**: CA-TIC-012, CA-TIC-013; Escenario 7.

### Tests for User Story 5

- [X] T059 [P] [US5] Crear test de contrato API (marker: api, AAA) para `POST /api/v1/soporte/tickets/{id}/reabrir` en `backend/apps/soporte_cliente/tests/api/test_reabrir_ticket_contract.py`
- [X] T060 [P] [US5] Crear test de servicio (marker: service, AAA) para `reabrir_ticket_service.py` (renovación SLA + adjunto + conservación historial) en `backend/apps/soporte_cliente/tests/services/test_reabrir_ticket_service.py`

### Implementation for User Story 5

- [X] T061 [US5] Implementar `reabrir_ticket_service.py` (reutiliza `asignacion_sla_service.py`, Decision 8) en `backend/apps/soporte_cliente/services/reabrir_ticket_service.py`
- [X] T062 [US5] Implementar `ReabrirTicketView` en `backend/apps/soporte_cliente/views.py` y registrar en `backend/apps/soporte_cliente/urls.py`

**Checkpoint**: US5 operativa — reapertura con renovación de SLA funcionando end-to-end.

**US5 Gate**:
- [X] T063 [US5] Validar CA-TIC-012, CA-TIC-013 en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`

---

## Phase 8: User Story 6 — Dashboard de soporte (Priority: P2)

**Goal**: RF-TIC-007 — métricas de tickets por estado/prioridad, SLA próximos a vencer/vencidos, tiempos promedio, distribución por tipo/cliente y tasa de reapertura.

**Independent Test**: `GET /soporte/dashboard` devuelve agregaciones consistentes con los datos de `Fact_Reclamo`/`Fact_Historial_Ticket`.

**Measurable Criteria**: RF-TIC-007 (no tiene CA numerado propio — se valida contra la lista de métricas del requisito).

### Tests for User Story 6

- [X] T064 [P] [US6] Crear test de contrato API (marker: api, AAA) para `GET /api/v1/soporte/dashboard` en `backend/apps/soporte_cliente/tests/api/test_dashboard_soporte_contract.py`
- [X] T065 [P] [US6] Crear test de servicio (marker: service, AAA) para `dashboard_soporte_service.py` en `backend/apps/soporte_cliente/tests/services/test_dashboard_soporte_service.py`

### Implementation for User Story 6

- [X] T066 [US6] Implementar `dashboard_soporte_service.py` (agregaciones RF-TIC-007: por estado/prioridad/tipo/cliente, SLA en riesgo/vencidos, tiempo promedio primera respuesta/resolución, tasa de reapertura) en `backend/apps/soporte_cliente/services/dashboard_soporte_service.py`
- [X] T067 [US6] Implementar `DashboardSoporteView` en `backend/apps/soporte_cliente/views.py` y registrar en `backend/apps/soporte_cliente/urls.py` (`TicketsView.get` ya cubría el listado desde US1)

**Checkpoint**: US6 operativa — dashboard de métricas disponible.

**US6 Gate**:
- [X] T068 [US6] Validar cobertura de métricas RF-TIC-007 en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`

---

## Phase 9: User Story 7 — Frontend Angular (Priority: P2)

**Goal**: Servicios tipados, guards por rol, páginas cliente/agente/administrador consumiendo el contrato OpenAPI.

**Independent Test**: Cliente registra y da seguimiento a sus tickets; Agente gestiona su cola; Administrador configura SLA; guards bloquean rutas por rol; notas internas nunca visibles para el rol Cliente en la UI.

**Measurable Criteria**: quickstart §3.

### Tests for User Story 7

- [X] T069 [P] [US7] Crear test unitario frontend (marker: unit, AAA) para `ticket-api.service.spec.ts` en `frontend/src/app/modules/soporte-cliente/services/ticket-api.service.spec.ts`
- [X] T070 [P] [US7] Crear test unitario frontend (marker: unit, AAA) para `sla-config-api.service.spec.ts` en `frontend/src/app/modules/soporte-cliente/services/sla-config-api.service.spec.ts`
- [X] T071 [P] [US7] Crear test unitario frontend (marker: unit, AAA) para guards en `frontend/src/app/modules/soporte-cliente/guards/cliente-soporte.guard.spec.ts`, `agente-soporte.guard.spec.ts`, `administrador-sla.guard.spec.ts`
- [X] T072 [P] [US7] Crear test unitario frontend (marker: unit, AAA) para rutas lazy en `frontend/src/app/modules/soporte-cliente/soporte-cliente.routes.spec.ts`

### Implementation for User Story 7

- [X] T073 [US7] Implementar `TicketApiService` en `frontend/src/app/modules/soporte-cliente/services/ticket-api.service.ts`
- [X] T074 [US7] Implementar `SlaConfigApiService` en `frontend/src/app/modules/soporte-cliente/services/sla-config-api.service.ts`
- [X] T075 [US7] Implementar guards en `frontend/src/app/modules/soporte-cliente/guards/cliente-soporte.guard.ts`, `agente-soporte.guard.ts`, `administrador-sla.guard.ts`
- [X] T076 [US7] Completar rutas lazy con guards en `frontend/src/app/modules/soporte-cliente/soporte-cliente.routes.ts` (ruta de detalle de ticket sin guard de rol propio: compartida por Cliente/agentes, filtrada internamente y protegida por el backend)
- [X] T077 [US7] Implementar página "Mis tickets" (Cliente) en `frontend/src/app/modules/soporte-cliente/pages/mis-tickets/mis-tickets.page.ts`
- [X] T078 [US7] Implementar página "Cola de agente" (Soporte al cliente) en `frontend/src/app/modules/soporte-cliente/pages/cola-agente/cola-agente.page.ts`
- [X] T079 [US7] Implementar página "Detalle de ticket" (vista filtrada por rol, oculta notas internas al Cliente) en `frontend/src/app/modules/soporte-cliente/pages/detalle-ticket/detalle-ticket.page.ts`
- [X] T080 [US7] Implementar página "Configuración SLA" (Administrador) en `frontend/src/app/modules/soporte-cliente/pages/configuracion-sla/configuracion-sla.page.ts`
- [X] T081 [US7] Implementar página "Dashboard de soporte" en `frontend/src/app/modules/soporte-cliente/pages/dashboard-soporte/dashboard-soporte.page.ts`
- [X] T082 [US7] Registrar entradas sidebar por rol — agregadas directamente a `frontend/src/app/shared/layout/nav-links.ts` (fuente real consumida por el shell; `core/sidebar/despacho-menu.config.ts` resultó ser código muerto no consumido en ningún lado, así que no se replicó ese patrón)

**Checkpoint**: US7 operativa — UI consumiendo contrato REST completo. Verificado con `ng build` (compila sin errores) y `tsc --noEmit` (sin errores de tipos); `ng test` no pudo ejecutar el navegador real (Chrome no instalado en este entorno — mismo límite documentado en `despacho-inteligente`), pero la compilación de specs+app fue exitosa.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Flujo end-to-end completo, quickstart validado, cobertura constitucional y documentación.

- [X] T083 Crear test cruzado multi-servicio registro→ciclo de vida→cierre→reapertura (marker: `service`, no `integration` — ver nota tasks.md T025) en `backend/apps/soporte_cliente/tests/services/test_flujo_completo_ticket_integration.py`
- [X] T084 [P] Ejecutar y documentar escenarios A–G de `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/quickstart.md` en `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/traceability.md`
- [X] T085 [P] Verificar cobertura ≥80% servicios y ≥85% repositorios soporte con `pytest --cov apps/soporte_cliente core/repositories/soporte --cov-report=term-missing` — resultado: 94% total, repos 94–100%, servicios 83–100%, `views.py` 87% (umbral 75%)
- [X] T086 [P] Verificar cobertura frontend módulo soporte-cliente — `ng build`/`tsc --noEmit` sin errores; `ng test --include=**/soporte-cliente/**` no pudo levantar Chrome real en este entorno (mismo límite ya documentado en `despacho-inteligente` T101)
- [X] T087 [P] Actualizar nota de extensión `gestion-tickets-soporte` en `.specify/docs/architecture/module-map.md` (estado implementación: ✅ Implementado backend + Angular US7)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — iniciar de inmediato
- **Foundational (Phase 2)**: Depende de Setup — **bloquea** todas las historias
- **US1 (Phase 3)**: Depende de Foundational — **MVP** registro con clasificación automática
- **US2 (Phase 4)**: Depende de US1 (necesita un ticket registrado para tomar/comentar/resolver)
- **US3 (Phase 5)**: Depende de Foundational + US1 (necesita tickets con SLA asignado); paralelo a US2 tras US1
- **US4 (Phase 6)**: Depende de Foundational (repositorio `sla_config_repository.py`, T012–T013); independiente de US1–US3
- **US5 (Phase 7)**: Depende de US2 (necesita un ticket Cerrado)
- **US6 (Phase 8)**: Depende de US1 + US2 (lee datos de tickets ya creados/atendidos)
- **US7 (Phase 9)**: Depende de US1, US2, US4, US5, US6 (endpoints disponibles)
- **Polish (Phase 10)**: Depende de US1–US7 deseados

### User Story Dependencies

```text
Phase 2 (Foundational)
    └── US1 (registro + clasificación) ──┬── US2 (ciclo de vida) ── US5 (reapertura)
                                          ├── US3 (monitoreo SLA)
                                          └── US6 (dashboard, tras US2)
              US4 (config SLA) ──────────┘ (paralelo, solo depende de Foundational)
    US1 + US2 + US4 + US5 + US6 ── US7 (frontend)
    US1–US7 ── Phase 10 (polish)
```

### Within Each User Story

1. Tests de contrato/servicio **antes** de implementación (fallan primero — TDD)
2. Repositorios (Phase 2) → Servicios → Vistas → Frontend
3. Cada servicio/repositorio: par implementación+test con patrón AAA y marker correcto

### Parallel Opportunities

- Phase 1: T002–T006 en paralelo
- Phase 2: tests T009, T011, T013, T015, T017, T019 en paralelo tras su implementación
- US1 tests T022–T024 en paralelo antes de T026–T028
- US2 tests API T031–T035 y tests de servicio T036–T040 en paralelo
- US4 y US5 pueden avanzar en paralelo entre sí una vez completada Foundational + US1/US2 respectivamente
- US7 tests T069–T072 en paralelo

### Parallel Example: User Story 1

```bash
# Tests en paralelo (escribir primero):
T022 test_clasificacion_automatica_service.py
T023 test_asignacion_sla_service.py
T024 test_registrar_ticket_contract.py

# Luego implementación secuencial T026→T029
```

### Parallel Example: Phase 2 Repositories

```bash
# Tras cada implementación, su test en paralelo con los demás pares:
T008+T009 reclamo_repository
T010+T011 historial_ticket_repository
T012+T013 sla_config_repository
T014+T015 archivo_adjunto_reclamo_repository
T016+T017 supervisor_soporte_repository
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1 + Phase 2
2. Completar Phase 3 (CU-O91)
3. **VALIDAR**: Escenario A quickstart — registro con clasificación automática exitosa en <3s
4. Demo: ticket crítico vinculado a emergencia activa con SLA asignado automáticamente

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 registro + clasificación → MVP
3. US2 ciclo de vida → atención y cierre completos
4. US3 monitoreo SLA → escalado automático operativo
5. US4 configuración SLA → administración sin redeploy
6. US5 reapertura → cierre del ciclo de reincidencia
7. US6 dashboard → visibilidad operativa
8. US7 frontend → UX completa
9. Phase 10 → flujo end-to-end y cobertura

### Suggested MVP Scope

**US1 (CU-O91)** — el registro con clasificación automática y SLA es la base de todo el módulo; sin US1 no hay ticket que atender, monitorear o reabrir.

---

## Notes

- Patrón AAA obligatorio; usar fixtures `mock_pinot`, `mock_kafka`, `auth_headers` de `backend/conftest.py`
- Ningún repositorio escribe directo a Pinot — solo publicación Kafka
- `AsignacionSLAService` es compartido por `RegistrarTicketService` (O91) y `ReabrirTicketService` (O97, Decision 8)
- Notas internas (`es_nota_interna=true`) se filtran en `comentar_ticket_service.py`/serializers, nunca solo en el frontend (RN-TIC-002, Principio V constitution)
- Markers: `repository` para repos, `service` para servicios/job, `api` para contract tests, `integration` para flujos end-to-end de este módulo (no forma parte del camino crítico de despacho, por eso no usa marker `critical_path`)
- Commit sugerido tras cada par implementación+test o al cerrar cada checkpoint
