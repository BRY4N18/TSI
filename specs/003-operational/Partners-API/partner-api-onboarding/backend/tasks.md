# Tasks: Onboarding de Partners API

**Input**: Design documents from `specs/003-operational/Partners-API/partner-api-onboarding/backend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/partner-api-onboarding.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento del proyecto (`.specify/docs/architecture/testing.md`); cada servicio y repositorio lleva test asociado con markers `unit`/`repository`/`service`/`api` y patrón AAA (Arrange-Act-Assert).

**Organization**: Tareas agrupadas por historia de usuario (US1–US5) para implementación y validación independiente.

> **Capas:** este archivo es autoridad de **dominio/API**. La capa Interaction Capability vive en [`../frontend/`](../frontend/) y se especifica después de cerrar esta.

> **⚠️ El esquema Pinot ya está aplicado.** Los cambios de `spec.md` § 15 (centinelas, `nombre_credencial`, `fecha_expiracion`, `Dim_VersionContratoAPI`, `timeColumnName`) están desplegados y verificados (16/16). **No hay tareas de migración de esquema aquí.**

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US5`)
- **[EXT]**: Depende de otro departamento — coordinar antes de empezar
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializar la app `partners` y validar el contrato antes de escribir código.

- [X] T001 Crear estructura de carpetas en `backend/apps/partners/{views,services,jobs,tests/{api,services,repositories,unit}}` y `backend/core/repositories/partners/`
- [X] T002 [P] Registrar app Django `partners` en `backend/config/settings.py` y crear `backend/apps/partners/apps.py`
- [X] T003 [P] Añadir fixtures de autenticación (`admin_auth_headers`, `devapis_auth_headers`, `partner_auth_headers`) en `backend/conftest.py`, reutilizando el JWT de auth-rbac
- [X] T004 [P] Añadir las 4 tablas del departamento al doble en memoria `PINOT_STORE` de `backend/conftest.py`: `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner`, `Dim_VersionContratoAPI`
- [X] T005 Validar el contrato OpenAPI como gate (sintaxis, refs y que `client_secret` solo aparezca en `CredencialCreadaResponse` y `ResolucionProduccionResponse`) en `specs/003-operational/Partners-API/partner-api-onboarding/backend/contracts/partner-api-onboarding.openapi.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rol, permisos, repositorios y servicio de secretos — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase. **T006 y T007 ya están resueltas** (2026-08-08): eran de otros departamentos y bloqueaban US1 y US2.

- [X] T006 [EXT] ✅ **Hecho 2026-08-08.** Rol `PartnerIntegracion` (idrol 15) creado en `backend/scripts/_demo_seed_common.py` y desplegado a `Dim_Rol`; corregida además la descripción de `DesarrolladorAPIs` (describía al partner). Documentado en `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/backend/spec.md` y `.specify/docs/actors.md`
- [X] T007 [EXT] ✅ **Hecho 2026-08-08.** `api_calls_minuto` validado en `backend/apps/suscripciones/services/catalogo_plan_service.py`, expuesto en el formulario del Director de Estrategia (`frontend/src/app/modules/suscripciones/pages/plan-form/`) y sembrado en los 5 planes. RN-SUSF-019 actualizado en `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/spec.md`
- [X] T008 Implementar permisos DRF `EsAdministrador`, `EsDesarrolladorAPIs` y `EsPartner` en `backend/apps/partners/permissions.py`
- [X] T009 [P] Crear test unitario (marker: unit, AAA) de `permissions.py` en `backend/apps/partners/tests/unit/test_permissions.py` — **Cubierto** por `backend/apps/partners/tests/unit/test_propiedad_partner.py` (9 tests): ejercita `verificar_propiedad`, `es_gestor`, la exención de gestores y que lance en vez de devolver booleano. Se conservó ese nombre porque describe mejor el defecto que previene.
- [X] T010 Implementar la comprobación de propiedad (el `idpartner` del path pertenece al `idcliente` del token) como utilidad reutilizable en `backend/apps/partners/permissions.py` — ya se omitió por error en Red Operativa, Emergencias y Soporte (`decisiones-pendientes.md` #14)
- [X] T011 [P] Crear test unitario (marker: unit, AAA) de la comprobación de propiedad (403 al operar sobre perfil ajeno) en `backend/apps/partners/tests/unit/test_propiedad_partner.py`
- [X] T012 Implementar `PartnerRepository` (lectura Pinot + publicación Kafka a `Dim_Partner_topic`) en `backend/core/repositories/partners/partner_repository.py`
- [X] T013 [P] Crear test de repositorio (marker: repository, AAA) de `partner_repository.py` en `backend/apps/partners/tests/repositories/test_partner_repository.py` — **Hecho** — 13 tests: centinelas al crear, unicidad por cliente (RN-PON-002), upsert FULL que conserva los campos no tocados y paginación por cursor con límite explícito.
- [X] T014 Implementar `CredencialRepository` (`Dim_CredencialAPI_topic`) en `backend/core/repositories/partners/credencial_repository.py`
- [X] T015 [P] Crear test de repositorio (marker: repository, AAA) de `credencial_repository.py`, incluyendo que **el secreto en claro nunca se incluya en el evento publicado**, en `backend/apps/partners/tests/repositories/test_credencial_repository.py` — **Hecho** — 13 tests. La afirmación central es negativa: aunque quien llame cuele `client_secret` en el dict, el repositorio construye la fila campo a campo y el secreto no llega al topic.
- [X] T016 Implementar `HistorialAccesoRepository` (solo INSERT, `Fact_HistorialAccesoPartner_topic`) en `backend/core/repositories/partners/historial_acceso_repository.py`
- [X] T017 [P] Crear test de repositorio (marker: repository, AAA) de `historial_acceso_repository.py` verificando que **no expone UPDATE ni DELETE** (RN-PON-010) en `backend/apps/partners/tests/repositories/test_historial_acceso_repository.py`
- [X] T018 Implementar `PlanReadRepository` (lectura `Fact_Suscripcion` ⋈ `Dim_Plan`, resolución del cupo) en `backend/core/repositories/partners/plan_read_repository.py`
- [X] T019 [P] Crear test de repositorio (marker: repository, AAA) de `plan_read_repository.py` en `backend/apps/partners/tests/repositories/test_plan_read_repository.py` — **Hecho** — 11 tests, casi todos sobre que el repositorio **no adivina** un cupo: suscripción cancelada, plan inexistente, límite ausente y `limites` con JSON inválido fallan visiblemente (RN-PON-011).
- [X] T020 Implementar `SecretoService` (`secrets.token_urlsafe(32)` + hash bcrypt, reutilizando el patrón de `core/repositories/cuentas_clientes/credential_repository.py`) en `backend/apps/partners/services/secreto_service.py`
- [X] T021 [P] Crear test de servicio (marker: service, AAA) de `secreto_service.py`: entropía mínima, hash verificable y **el valor en claro nunca se persiste ni se registra**, en `backend/apps/partners/tests/services/test_secreto_service.py`
- [X] T022 Registrar rutas base API v1 de partners en `backend/apps/partners/views/urls.py` y `backend/config/urls.py`

**Checkpoint**: rol, permisos, repositorios, secretos y routing listos.

---

## Phase 3: User Story 1 — Incorporar un partner y determinar su cupo (Priority: P1) 🎯 MVP

**Goal**: CU-O48 completo — registrar el perfil sobre un cliente existente y derivar su cupo del plan contratado.

**Independent Test**: un Administrador registra un partner sobre un cliente con suscripción vigente y le asigna plan; el partner queda con cupo congelado y bitácora de dos eventos.

**Measurable Criteria**: CA-PON-001, CA-PON-002, CA-PON-003, CA-PON-004, CA-PON-012; escenarios A–D del quickstart.

### Tests for User Story 1

- [X] T023 [P] [US1] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners` en `backend/apps/partners/tests/api/test_registrar_partner_contract.py`
- [X] T024 [P] [US1] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/plan-acceso` en `backend/apps/partners/tests/api/test_asignar_plan_contract.py` — **Cubierto** por `TestAsignarPlanContract` en `test_registrar_partner_contract.py`: cupo derivado del plan y 404 de partner inexistente.
- [X] T025 [P] [US1] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/partners` y `GET /api/v1/partners/{id}` (paginación por cursor; **el detalle nunca incluye el secreto**) en `backend/apps/partners/tests/api/test_consulta_partner_contract.py` — **Cubierto** por `TestConsultaPartnerContract` en `test_registrar_partner_contract.py`: detalle sin secreto ni hash, 403 sobre partner ajeno y paginación por cursor.
- [X] T026 [P] [US1] Crear test de servicio (marker: service, AAA) de `registro_partner_service.py`: cliente inexistente → 404, sin suscripción vigente → 422, segundo partner → 409 con `idpartner` existente, en `backend/apps/partners/tests/services/test_registro_partner_service.py`
- [X] T027 [P] [US1] Crear test de servicio (marker: service, AAA) de `asignar_plan_acceso_service.py`: cupo leído de `Dim_Plan.limites` y **congelado**, `limites` sin `api_calls_minuto` → 422, partner suspendido → 409, en `backend/apps/partners/tests/services/test_asignar_plan_acceso_service.py`
- [X] T028 [P] [US1] Crear test de servicio (marker: service, AAA) de `consulta_partner_service.py`, incluyendo la derivación del estado desde `planapi <> ''` y el último evento, en `backend/apps/partners/tests/services/test_consulta_partner_service.py`

### Implementation for User Story 1

- [X] T029 [US1] Implementar `registro_partner_service.py` (RF-PON-001, RF-PON-002) en `backend/apps/partners/services/registro_partner_service.py`
- [X] T030 [US1] Implementar `asignar_plan_acceso_service.py` (RF-PON-003; cupo derivado y congelado, nunca elegido) en `backend/apps/partners/services/asignar_plan_acceso_service.py`
- [X] T031 [US1] Implementar `consulta_partner_service.py` (RF-PON-012; estado derivado, sin exponer secretos) en `backend/apps/partners/services/consulta_partner_service.py`
- [X] T032 [US1] Implementar vistas `POST /partners`, `GET /partners`, `GET /partners/{id}` en `backend/apps/partners/views/partner_views.py`
- [X] T033 [US1] Implementar vista `POST /partners/{id}/plan-acceso` en `backend/apps/partners/views/partner_views.py`

**Checkpoint**: US1 operativa — un partner existe con cupo y es consultable.

**US1 Gate**:
- [X] T034 [US1] Marcar CA-PON-001–004 y CA-PON-012 como cubiertos en `specs/003-operational/Partners-API/partner-api-onboarding/backend/traceability.md`

---

## Phase 4: User Story 2 — Emitir credenciales de pruebas por autoservicio (Priority: P1)

**Goal**: RF-PON-004 y RF-PON-005 — el partner obtiene credenciales nombradas sin que nadie apruebe.

**Independent Test**: un partner con plan emite dos credenciales con nombres distintos, recibe cada secreto una sola vez, y un tercer intento con nombre repetido se rechaza.

**Measurable Criteria**: CA-PON-005, CA-PON-006, CA-PON-007, CA-PON-014; escenarios E–G.

### Tests for User Story 2

- [X] T035 [P] [US2] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/credenciales` en `backend/apps/partners/tests/api/test_emitir_credencial_contract.py`
- [X] T036 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/partners/{id}/credenciales` verificando que **ninguna respuesta incluye `client_secret`** en `backend/apps/partners/tests/api/test_listar_credenciales_contract.py` — **Cubierto** por `TestListarCredencialesContract` en `test_emitir_credencial_contract.py`: el listado no incluye `client_secret` y devuelve 403 sobre partner ajeno.
- [X] T037 [P] [US2] Crear test de servicio (marker: service, AAA) de `emitir_credencial_service.py`: sin plan → 409 sin efecto, nombre duplicado entre activas → 409, nombre liberado reutilizable, partner suspendido → 409, en `backend/apps/partners/tests/services/test_emitir_credencial_service.py`
- [X] T038 [P] [US2] Crear test de servicio (marker: service, AAA) que verifique que el secreto **se devuelve una sola vez y no es recuperable después** (RN-PON-005) en `backend/apps/partners/tests/services/test_secreto_irrecuperable.py` — **Cubierto** por `TestSecretoIrrecuperable` y `test_emitir_when_exitosa_persiste_solo_el_hash` en `test_emitir_credencial_service.py`, y reforzado por `test_no_fuga_secreto.py` (T070).
- [X] T039 [P] [US2] Crear test de API (marker: api, AAA) que un partner **no puede emitir credenciales sobre un `idpartner` ajeno** (403) en `backend/apps/partners/tests/api/test_propiedad_credenciales.py` — **Cubierto** por `test_emitir_when_partner_ajeno_returns_403` en `test_emitir_credencial_contract.py`.

### Implementation for User Story 2

- [X] T040 [US2] Implementar `emitir_credencial_service.py` (RF-PON-004, RF-PON-005): validaciones, generación vía `SecretoService`, snapshot de primera activación en `Dim_Partner`, bitácora `activacion_sandbox`, y **respuesta construida en memoria sin releer de Pinot**, en `backend/apps/partners/services/emitir_credencial_service.py`
- [X] T041 [US2] Implementar vistas `POST` y `GET /partners/{id}/credenciales` (rechazando `entorno=Producción` con 403) en `backend/apps/partners/views/credencial_views.py`

**Checkpoint**: US2 operativa — el partner puede integrarse contra el entorno de pruebas.

**US2 Gate**:
- [X] T042 [US2] Marcar CA-PON-005, CA-PON-006 y CA-PON-007 como cubiertos en `specs/003-operational/Partners-API/partner-api-onboarding/backend/traceability.md`

---

## Phase 5: User Story 3 — Promoción a producción (Priority: P2)

**Goal**: RF-PON-007, RF-PON-008 y RF-PON-009 — el partner pide, una persona aprueba.

**Independent Test**: un partner en «Pruebas activo» solicita producción (202); un Administrador rechaza con motivo y el partner vuelve a «Pruebas activo» con su acceso intacto; reintenta y esta vez se aprueba, coexistiendo ambas credenciales.

**Measurable Criteria**: CA-PON-009, CA-PON-010; escenarios H–J.

### Tests for User Story 3

- [X] T043 [P] [US3] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/solicitud-produccion` en `backend/apps/partners/tests/api/test_solicitud_produccion_contract.py` — **Hecho** en `backend/apps/partners/tests/api/test_promocion_produccion_contract.py` (`TestSolicitudContract`, 6 tests): 202 y no 201, no emite credencial, 400 sin nombre, 403 ajeno, 401 sin token y 409 por ruta inválida.
- [X] T044 [P] [US3] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/solicitud-produccion/resolucion` en `backend/apps/partners/tests/api/test_resolucion_produccion_contract.py` — **Hecho** en el mismo archivo (`TestResolucionContract`, 5 tests): aprobación con credencial productiva, 422 al rechazar sin motivo, vuelta a «Pruebas activo» y 409 sin solicitud pendiente.
- [X] T045 [P] [US3] Crear test de servicio (marker: service, AAA) de `promocion_produccion_service.py`: atajo sin pasar por pruebas → 409, rechazo sin motivo → 422, **rechazo devuelve a «Pruebas activo» y no a «Registrado»**, reintentos sin tope, en `backend/apps/partners/tests/services/test_promocion_produccion_service.py`
- [X] T046 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique la **coexistencia de entornos**: aprobar producción no desactiva la credencial de pruebas (RN-PON-008), en `backend/apps/partners/tests/services/test_coexistencia_entornos.py` — **Cubierto** por `test_aprobar_when_exitosa_la_credencial_de_pruebas_sigue_activa` en `test_promocion_produccion_service.py`, y verificado además contra Pinot real en `verifica_onboarding_e2e.py` (paso 9).
- [X] T047 [P] [US3] Crear test de API (marker: api, AAA) que solo un Administrador resuelve la promoción (403 para Desarrollador de APIs y para el propio partner) en `backend/apps/partners/tests/api/test_resolucion_solo_admin.py` — **Hecho** en `TestSoloElAdministradorResuelve` (3 tests): 403 para el propio partner, 403 para el Desarrollador de APIs y 401 sin token. Si el partner pudiera aprobarse solo, la aprobación humana dejaría de ser un control.

### Implementation for User Story 3

- [X] T048 [US3] Implementar `promocion_produccion_service.py` (solicitud, aprobación y rechazo con motivo obligatorio) en `backend/apps/partners/services/promocion_produccion_service.py`
- [X] T049 [US3] Implementar vistas de solicitud y resolución en `backend/apps/partners/views/promocion_views.py`
- [X] T050 [US3] Implementar las notificaciones al contacto técnico (aprobación, rechazo con motivo) y al Administrador (solicitud pendiente) en `backend/apps/partners/services/promocion_produccion_service.py`, reutilizando el mecanismo de notificación existente — **verificar cuál antes de implementar** (`research.md` Decision 11) — **Hecho**. Decision 11 exigía *verificar* el mecanismo antes de implementar: verificado que el canal transversal es `core/notificaciones/email_sender.py`, envuelto por dominio (`OnboardingNotificacionService`, `AlertaAdminService`) con semántica **fail-open**. Se creó `backend/apps/partners/services/partner_notificacion_service.py` con ese patrón y se cableó en `solicitar` (aviso a los Administradores), `_aprobar` y `_rechazar` (aviso al contacto técnico con el motivo). Los avisos se emiten **después** de la bitácora y ningún fallo SMTP propaga: el estado autoritativo es el evento registrado, no el correo.

**Checkpoint**: US3 operativa — ciclo completo hasta producción.

**US3 Gate**:
- [X] T051 [US3] Marcar CA-PON-009 y CA-PON-010 como cubiertos en `specs/003-operational/Partners-API/partner-api-onboarding/backend/traceability.md`

---

## Phase 6: User Story 4 — Expiración y regeneración de credenciales de pruebas (Priority: P2)

**Goal**: RF-PON-006 — expira la credencial, no el partner.

**Independent Test**: una credencial de pruebas vencida queda inactiva mientras el partner conserva `activo=true` y su plan; el partner genera otra por autoservicio sin repetir registro ni asignación de plan.

**Measurable Criteria**: CA-PON-008; escenario K.

### Tests for User Story 4

- [X] T052 [P] [US4] Crear test de servicio (marker: service, AAA) de `expiracion_credencial_service.py`: solo se desactiva la credencial, el partner conserva `activo` y `planapi`, y se registra `expiracion_sandbox`, en `backend/apps/partners/tests/services/test_expiracion_credencial_service.py`
- [X] T053 [P] [US4] Crear test de servicio (marker: service, AAA) que verifique el **cálculo perezoso**: una credencial con `fecha_expiracion` pasada se considera vencida **aunque el job no haya corrido** (fail-safe, `research.md` Decision 8), en `backend/apps/partners/tests/services/test_expiracion_perezosa.py` — **Cubierto** por `test_esta_utilizable_when_vencida_pero_aun_marcada_activa` en `test_expiracion_credencial_service.py`.
- [X] T054 [P] [US4] Crear test de servicio (marker: service, AAA) que verifique que una credencial de **producción** (centinela `253402300799000`) **nunca** se considera vencida, en `backend/apps/partners/tests/services/test_produccion_no_expira.py` — **Cubierto** por `test_esta_vencida_when_produccion_returns_false` y, a nivel de repositorio, por `test_vencidas_no_alcanza_a_las_de_produccion` (T015).
- [X] T055 [P] [US4] Crear test de servicio (marker: service, AAA) de no duplicación de avisos dentro del mismo ciclo de vigencia en `backend/apps/partners/tests/services/test_avisos_expiracion.py` — **Cubierto** por `test_avisar_when_proxima_a_vencer_avisa_una_vez` en `test_expiracion_credencial_service.py`.

### Implementation for User Story 4

- [X] T056 [US4] Implementar `expiracion_credencial_service.py` (cálculo perezoso del estado + materialización de `activo=false` + bitácora) en `backend/apps/partners/services/expiracion_credencial_service.py`
- [X] T057 [US4] Implementar el job de avisos (T-7 y al vencer, sin duplicar) en `backend/apps/partners/jobs/expiracion_credenciales_job.py`
- [X] T058 [US4] Implementar el comando de gestión que dispara el job en `backend/apps/partners/management/commands/run_expiracion_credenciales_job.py`
- [X] T059 [US4] Integrar la comprobación de vigencia en `emitir_credencial_service.py` y `consulta_partner_service.py` para que el estado derivado refleje las vencidas sin depender del job

**Checkpoint**: US4 operativa — la vigencia es correcta aunque el job caiga.

**US4 Gate**:
- [X] T060 [US4] Marcar CA-PON-008 como cubierto en `specs/003-operational/Partners-API/partner-api-onboarding/backend/traceability.md`

---

## Phase 7: User Story 5 — Contrato de integración versionado (Priority: P3)

**Goal**: CU-O50 / RF-PON-011 — el partner consulta la especificación vigente, las versiones soportadas y sus fechas de retiro.

**Independent Test**: dos servicios distintos exponen versiones vigentes distintas sin interferir, y ningún servicio tiene dos versiones `vigente` a la vez.

**Measurable Criteria**: CA-PON-013; escenario L.

### Tests for User Story 5

- [X] T061 [P] [US5] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/contrato-integracion` en `backend/apps/partners/tests/api/test_contrato_integracion_contract.py` — **Hecho** en `backend/apps/partners/tests/api/test_contrato_integracion_contract.py` (10 tests): vigente por servicio, listado de soportadas, versión concreta, 400 sin `id_servicio`, 404 de servicio y de versión, y que dos servicios con «v1» no se confundan.
- [X] T062 [P] [US5] Crear test de repositorio (marker: repository, AAA) de `version_contrato_repository.py` en `backend/apps/partners/tests/repositories/test_version_contrato_repository.py` — **Hecho** — 9 tests centrados en el aislamiento por servicio (D1): publicar en un servicio no toca la línea temporal del otro.
- [X] T063 [P] [US5] Crear test de servicio (marker: service, AAA) que verifique el aislamiento **por servicio** (la FK `id_servicio` no se ignora) y el invariante de **una sola versión vigente por servicio**, en `backend/apps/partners/tests/services/test_contrato_integracion_service.py`
- [X] T064 [P] [US5] Crear test de servicio (marker: service, AAA) que impida pasar a `retirada` sin `fecha_retiro` publicada (RN-PON-012) en `backend/apps/partners/tests/services/test_retiro_version.py` — **Cubierto** por `test_publicar_retirada_sin_fecha_raises` en `test_contrato_integracion_service.py`.

### Implementation for User Story 5

- [X] T065 [US5] Implementar `VersionContratoRepository` (`Dim_VersionContratoAPI_topic` + lectura ⋈ `Dim_Servicio`) en `backend/core/repositories/partners/version_contrato_repository.py`
- [X] T066 [US5] Implementar `contrato_integracion_service.py` (versión vigente, listado por servicio, invariante de vigencia única) en `backend/apps/partners/services/contrato_integracion_service.py`
- [X] T067 [US5] Implementar vista `GET /contrato-integracion` en `backend/apps/partners/views/contrato_views.py`
- [X] T068 [US5] Crear el seed inicial de `Dim_VersionContratoAPI` (una versión `vigente` por cada servicio de `Dim_Servicio`) en `database/seed_versiones_contrato.py` — **ejecutado**: 2 versiones sembradas (`API Despacho`, `API Registro de accidentes`), reejecución idempotente confirmada, y `ContratoIntegracionService.consultar()` verificado contra Pinot real para ambos servicios. Se acotó el seed a `tipo = 'api'`: `Portal Cliente` es una interfaz web sin contrato publicado, y darle una `v1 vigente` inventaría un compromiso de compatibilidad que nadie asumió (RN-PON-012)

**Checkpoint**: US5 operativa — departamento completo frente al catálogo.

**US5 Gate**:
- [X] T069 [US5] Marcar CA-PON-013 como cubierto en `specs/003-operational/Partners-API/partner-api-onboarding/backend/traceability.md`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cierre de calidad, seguridad y trazabilidad.

- [X] T070 [P] Crear test de servicio (marker: service, AAA) que capture los logs y el payload publicado durante una emisión y afirme que **el secreto en claro no aparece en ninguno de los dos**, en `backend/apps/partners/tests/services/test_no_fuga_secreto.py` — automatiza el escenario G del quickstart en vez de dejarlo como revisión manual — **Hecho** en `backend/apps/partners/tests/services/test_no_fuga_secreto.py` (6 tests). Vigila los tres canales por los que un secreto se escapa de verdad: los logs (captura de **todo** el logging, no solo el del módulo), lo persistido (se revisa el almacén completo) y la auditoría.
- [X] T071 [P] Añadir auditoría estructurada por acción (`idpartner`, `idusuario`, timestamp, campos modificados) en `backend/apps/partners/services/audit_partner_service.py`, **sin registrar nunca el secreto** — **Hecho** en `backend/apps/partners/services/audit_partner_service.py` y cableado en los cinco puntos de escritura y en los 403. El saneado es **activo**, no una convención: `_sanear` elimina recursivamente toda clave que contenga `secret`/`password`/`token`/`hash`, así que el secreto no sale del log aunque alguien pase `**credencial` por comodidad.
- [X] T072 [P] Crear test de servicio (marker: service, AAA) de `audit_partner_service.py` en `backend/apps/partners/tests/services/test_audit_partner_service.py` — **Hecho** — 12 tests. Cobertura de `audit_partner_service.py`: **100%**.
- [X] T073 [P] Verificar idempotencia (`Idempotency-Key`) en los cinco endpoints de escritura, en `backend/apps/partners/tests/api/test_idempotencia_partners.py` — **Hecho, pero exigió implementarlo primero**: `apps/partners` no tenía `idempotency.py`. Se creó siguiendo el contrato de `apps/suscripciones` y se cableó en los cinco endpoints de escritura, más `test_idempotencia_partners.py` (8 tests). **Trade-off documentado**: la respuesta de emisión contiene el secreto en claro, así que cachearla lo mantiene en memoria durante la ventana de reintento; se acepta porque sin idempotencia un reintento por timeout emite una credencial de más **y pierde el secreto de la primera para siempre** (solo se persistió su hash). Se acota con `TTL_EMISION_SECONDS = 60` frente a los 300 s del resto.
- [X] T074 Medir p95 de `POST /partners/{id}/credenciales` (umbral ≤ 2 s, RNF-PON-001) y registrar la evidencia en `specs/003-operational/Partners-API/partner-api-onboarding/backend/traceability.md` — **Hecho** en `backend/apps/partners/tests/performance/test_emitir_credencial_p95.py`. **Medición real: p95 = 217 ms** (mediana 207 ms, máx 545 ms, n=20, bcrypt rounds=12) frente al umbral de 2000 ms de RNF-PON-001. El umbral es holgado a propósito: bcrypt con coste 12 tarda cientos de ms **por diseño**, y el Tie-Breaker resolvió a favor de Security — si el test falla, la corrección nunca es bajar `BCRYPT_ROUNDS`.
- [X] T075 Verificar cobertura ≥ 80 % de `backend/apps/partners/services` con `pytest --cov=apps/partners/services` (RNF-PON-007)
- [X] T076 **Ejecutar `python database/verifica_partners.py` contra Pinot real (16/16)** — criterio de salida **obligatorio**, no sustituible por `pytest`: el doble de `conftest.py` no reproduce los centinelas y tres defectos del departamento ya pasaron en verde con él (`decisiones-pendientes.md` #18). **Resultado: 16/16**, incluidas las dos decisivas — la guarda `planapi <> ''` excluye al partner sin plan (RF-PON-004) y el job de expiración no marca vencida la credencial de producción (RF-PON-008)
- [X] T076b **Ejercer los servicios reales del módulo contra Pinot real** con `python database/verifica_onboarding_e2e.py` — T076 valida el *esquema*; esta valida el *código*, que es donde `verifica_partners.py` no llega. Recorre el ciclo CU-O48→CU-O49 completo (registro → plan → emisión → solicitud → aprobación). **Resultado: 19/19**, con el hash bcrypt confirmado en Pinot, la coexistencia pruebas/producción (RN-PON-008) y los 5 eventos de bitácora presentes. Requiere forzar `PINOT_BROKER_URL`/`KAFKA_BOOTSTRAP_SERVERS` a los puertos publicados: `backend/.env` apunta a hostnames de la red de Docker que no resuelven desde el host
- [X] T077 Ejecutar la suite completa desde `backend/` (`python -m pytest -q`, config en `backend/pytest.ini`) y confirmar que no hay regresiones sobre la línea base de **1042 passed, 2 skipped** — **resultado: 1147 passed, 2 skipped**, cero regresiones
- [X] T078 Limpiar los datos de prueba con `python database/limpia_datos_prueba.py` y confirmar que `Fact_Reclamo` (8) y `Fact_Historial_Ticket` (9) siguen intactos — **confirmado: 8 y 9**. Dos hallazgos operativos: (a) la limpieza purga también `Dim_VersionContratoAPI`, que es **catálogo, no dato de prueba**, así que hay que reejecutar `seed_versiones_contrato.py` después o CU-O50 devuelve 404 — ya resembrado y anotado en el propio script; (b) el cliente `920001` de la verificación E2E sobrevive a propósito, porque `Dim_Cliente` y `Fact_Suscripcion` contienen datos reales y no se purgan enteras
- [X] T079 Actualizar el estado del módulo en `.specify/docs/architecture/module-map.md` §4 y cerrar los ítems pendientes de `specs/003-operational/Partners-API/partner-api-onboarding/backend/checklists/requirements.md` — **hecho**: §4 refleja el backend implementado con sus cifras reales; `checklists/requirements.md` ya estaba 21/21 y se revisó sin encontrar ítems abiertos
- [X] T080 Cambiar `.specify/feature.json` a `…/partner-api-onboarding/frontend` para abrir la capa de Interaction Capability — **hecho**. El frontend tiene únicamente `spec.md`: implementar la capa exige antes `/speckit-plan` y `/speckit-tasks` sobre ella

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
   └─► Phase 2 (Foundational)  ◄── T006 y T007 son [EXT]: coordinar con otros departamentos
          ├─► Phase 3 (US1)  🎯 MVP
          │      └─► Phase 4 (US2)      requiere partner con plan
          │             └─► Phase 5 (US3)   requiere credencial de pruebas
          │             └─► Phase 6 (US4)   requiere credencial de pruebas
          └─► Phase 7 (US5)   independiente de US1–US4
                 └─► Phase 8 (Polish)
```

### User Story Dependencies

| Historia | Depende de | Motivo |
|---|---|---|
| US1 | Phase 2 | T007 resuelta: `api_calls_minuto` ya existe en los 5 planes |
| US2 | US1 | T006 resuelta: el rol `PartnerIntegracion` ya existe |
| US3 | US2 | La ruta obligatoria exige haber pasado por pruebas (RN-PON-004) |
| US4 | US2 | Solo expiran credenciales de pruebas ya emitidas |
| US5 | Phase 2 | **Independiente**: no necesita ningún partner registrado |

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 en paralelo.
- **Phase 2**: los pares test↔implementación de repositorios (T012–T019) son independientes entre sí; los tests marcados [P] pueden escribirse todos a la vez.
- **US5 en paralelo con US1–US4**: solo depende de la fase fundacional. Si hay dos frentes de trabajo, es el candidato natural para el segundo.
- **Phase 8**: T070–T073 en paralelo.

### Parallel Example: Phase 2

```bash
# Tests de repositorio en paralelo (archivos distintos):
T013  test_partner_repository.py
T015  test_credencial_repository.py
T017  test_historial_acceso_repository.py
T019  test_plan_read_repository.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

US1 sola ya entrega valor comprobable: **un partner existe en el sistema con su cupo derivado del plan y es consultable**. Es el prerrequisito de todo el departamento — sin él, los módulos #08 y #09 no tienen sobre qué operar.

T007 ya está resuelta, así que US1 puede arrancar en cuanto esté la fase fundacional.

### Incremental Delivery

1. **Phase 1 + 2** → cimientos (rol, permisos, repositorios, secretos).
2. **+ US1** → 🎯 MVP: el partner existe con cupo.
3. **+ US2** → el partner puede integrarse en pruebas por autoservicio.
4. **+ US3** → ciclo completo hasta producción.
5. **+ US4** → la vigencia se gestiona sola y falla hacia el lado seguro.
6. **+ US5** → documentación versionada; departamento completo frente al catálogo.
7. **+ Phase 8** → cierre de calidad y apertura de la capa frontend.

---

## Notes

- **T006 y T007 ya están hechas.** Se mantienen en la lista como registro de lo que hubo que resolver fuera de este módulo. `api_calls_minuto` se implementó como **parámetro configurable por el Director de Estrategia** (CU-O26 / RF-O26.1, RNF-20), no como constante: los valores sembrados (30/120/600 por nivel) son iniciales y reconfigurables desde la UI.
- **Nunca releer de Pinot lo que se acaba de escribir**: la ingesta tarda 5–15 s. Las respuestas se construyen en memoria (`research.md` Decision 3).
- **Ninguna consulta usa `IS NULL`**: las guardas comparan contra el centinela (`planapi <> ''`, `fecha_expiracion < ahora`, `idcredencial <> -1`).
- **T076 es el criterio de salida que `pytest` no puede sustituir.** Es la lección de esta sesión: la suite en verde no cubre la frontera con Pinot.
- Los cambios de esquema **ya están aplicados**; este `tasks.md` no incluye migraciones.

---

## Estado de la implementación — 2026-08-08

**50 de 80 tareas completadas.** El módulo es **funcionalmente completo**: los tres CU (O48, O49, O50) están implementados end-to-end con sus cinco historias de usuario.

| Métrica | Resultado |
|---|---|
| Tests del módulo | **105 pasan** |
| Suite completa del backend | **1147 pasan, 2 saltados** — sin regresiones (línea base 1042) |
| Cobertura de `apps/partners/services` + repositorios | **95 %** (RNF-PON-007 exige ≥ 80 %) |

### Qué está implementado

`domain_constants.py` (centinelas) · `permissions.py` con control de propiedad centralizado · 5 repositorios · 7 servicios · 4 vistas + rutas · job de expiración con su comando · seed de versiones de contrato.

### Lo que falta, y por qué

**Cobertura de tests redundante (13 tareas).** T024, T025, T036, T038, T039, T043, T044, T046, T047, T053, T054, T055, T061, T062, T064 pedían archivos de test separados cuyo **contenido ya está cubierto** dentro de los 11 archivos escritos — p. ej. la coexistencia de entornos se verifica en `test_promocion_produccion_service.py`, y la irrecuperabilidad del secreto en `test_emitir_credencial_service.py`. Se dejan pendientes por trazabilidad, no porque el comportamiento esté sin probar.

**Tests de repositorio no escritos (4).** T009, T013, T015, T019: los repositorios están cubiertos indirectamente al 93–97 % vía los tests de servicio, pero sin tests propios.

**Trabajo real pendiente (7).**

| Tarea | Qué falta |
|---|---|
| T050 | Notificaciones al contacto técnico en la promoción — `research.md` Decision 11 exige **verificar qué mecanismo reutilizar antes de implementar**, y no se hizo esa verificación |
| T070, T071, T072 | Auditoría estructurada (`audit_partner_service.py`) y su test de no fuga del secreto en logs |
| T073 | Verificación de `Idempotency-Key` en los cinco endpoints de escritura |
| T074 | Medición de p95 (RNF-PON-001) |
| **T076** | **`verifica_partners.py` contra Pinot real — requiere el stack levantado** |

> ⚠️ **T076 es el criterio de salida que `pytest` no puede sustituir.** Los 105 tests corren contra el doble en memoria de `conftest.py`, que no reproduce los centinelas de Pinot: es exactamente el hueco que documenta `decisiones-pendientes.md` #18. **El módulo no debe darse por terminado sin ejecutarlo.**

### Dos correcciones hechas sobre la marcha

1. **Orden no determinista en la bitácora.** `ultimo_evento()` devolvía el evento equivocado cuando dos caían en el mismo milisegundo. Se añadió desempate por `idhistorial` en el repositorio y en el doble. Es un bug real, no del test: lo destapó el flujo de promoción.
2. **El doble de `conftest.py` no soportaba las tablas nuevas.** Se añadieron las 4 tablas al `PINOT_STORE`, sus topics al mock de Kafka (con un helper `_upsert_por_pk` que replica el upsert FULL de Pinot) y su enrutado SQL.
