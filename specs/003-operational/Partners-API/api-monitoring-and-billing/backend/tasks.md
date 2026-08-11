# Tasks: Monitoreo y Facturación de API

**Input**: Design documents from `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-monitoring-and-billing.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento del proyecto (`.specify/docs/architecture/testing.md`); markers `unit`/`repository`/`service`/`api` y patrón AAA.

**Organization**: Tareas agrupadas por historia de usuario (US1–US4).

> **Capas:** este archivo es autoridad de **dominio/API**. La capa Interaction Capability vive en [`../frontend/`](../frontend/).

> **⚠️ Depende de la implementación de #07.** Este módulo mide el consumo de partners con credenciales de producción. Las fases 1–2 pueden adelantarse, pero **US1 no es testeable end-to-end sin `partner-api-onboarding` implementado**.

> **✅ Esquema aplicado.** `Fact_Factura.tipo`, `Fact_Reclamo.idfactura` STRING y `Dim_Plan.precio_excedente_llamada` ya están desplegados y verificados. **No hay tareas de migración de esquema aquí**, salvo el seed de `Dim_EstadoIntegracion` (T006).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US4`)
- Cada descripción incluye path exacto de archivo

---

## 📍 Punto de partida (2026-08-09)

Estado verificado antes de arrancar, para no volver a comprobarlo:

| | |
|---|---|
| Dependencia #07 | ✅ **Implementada** (backend + frontend), commit `9eea877` en `main` |
| Tablas en Pinot | ✅ `Fact_APIIntegracion`, `Fact_LogLlamadaAPI`, `Dim_EstadoIntegracion`, `Fact_Factura` — **existen y están vacías** |
| Migración de esquema | ✅ **No hace falta ninguna** |
| T006 catálogo | ✅ **Sembrado**: 2 estados activos (`Suspendido` desactivado por inalcanzable) |
| Suites base | backend **1272 passed / 2 skipped**, frontend **470 passed** |

**Decisiones ya tomadas que afectan a la implementación:**

1. **`Fact_APIIntegracion.idestadointegracion` se mantiene** aunque sea redundante con `entorno`
   (deuda aceptada, `decisiones-pendientes.md` #22). Al registrar consumo, se escribe el estado que
   corresponde al entorno de la credencial: `1` para Sandbox, `2` para Producción. **Nunca `3`.**
2. **Los estados de *condición de acceso*** (cuota al 80 %, rate limited, suspendido por mora) **no
   van en base**: son presentación derivada de la consola de consumo. Razonamiento en `data-model.md`.

**Tres trampas del spec que conviene releer antes de US1** (`spec.md` líneas 42, 76-77, 157-163):

- Superar el cupo **no bloquea nunca**; se factura. El `429` por minuto es protección de plataforma,
  no aplicación de la cuota. El propio spec avisa de que lo documenta «para que nadie lo corrija
  asumiendo que debería bloquear».
- Un `429` **no genera fila** en `Fact_APIIntegracion` (no se atendió, no es facturable); sí en
  `Fact_LogLlamadaAPI`.
- El acceso exige **tres** condiciones con tres dueños distintos: credencial válida, partner activo
  y **suscripción vigente**. La tercera es `T024b` y cierra un hueco real.

---

## Phase 1: Setup

**Purpose**: Preparar la app y validar el contrato antes de escribir código.

- [X] T001 Crear subcarpetas del módulo en `backend/apps/partners/{middleware,jobs}` y `backend/apps/partners/tests/{api,services,repositories,unit}` (la app `partners/` ya existe desde #07) — **hecho**: creada `apps/partners/middleware/`. El resto (`jobs/`, `tests/{api,services,repositories,unit}`) ya existía desde #07.
- [X] T002 [P] Añadir las 3 tablas de este módulo al doble en memoria `PINOT_STORE` de `backend/conftest.py`: `Fact_APIIntegracion`, `Fact_LogLlamadaAPI`, `Dim_EstadoIntegracion` — **hecho**: las 3 tablas añadidas a `PINOT_STORE`, más el enrutado de sus topics en `mock_kafka` (append-only para las dos Fact, upsert por PK para el catálogo) y el enrutado SQL en `_pinot_query_impl`, **incluidas las agregaciones** (`SUM`, `AVG`, `GROUP BY`). Queda anotado en el propio conftest que reproducirlas a mano **no** garantiza que Pinot las resuelva igual: T066 sigue siendo criterio de salida.
- [X] T003 [P] Añadir fixtures de autenticación por credencial (`credencial_sandbox_headers`, `credencial_produccion_headers`) y de rol (`devapis_auth_headers`) en `backend/conftest.py` — **hecho**: `credencial_sandbox_headers` y `credencial_produccion_headers` en `conftest.py`, que siembran partner + credencial y hashean el secreto con bcrypt real, no un atajo. `devapis_auth_headers` ya existía de #07.
- [X] T004 Validar el contrato OpenAPI como gate: sintaxis, refs, y que **solo `/datos/*` use `credencialAuth`** mientras métricas, logs y reportes usan `bearerAuth`, en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/contracts/api-monitoring-and-billing.openapi.yaml` — **hecho**: validado por script — sintaxis YAML correcta, **cero refs rotas**, y el gate de superficies pasa: `credencialAuth` aparece **solo** en `/datos/*` y toda ruta `/datos/*` lo usa.
- [X] T005 [P] Registrar las rutas del módulo en `backend/apps/partners/views/urls.py`, separando el grupo `/datos/*` del grupo de gestión — **hecho**: grupo `/datos/*` separado del de gestión en `views/urls.py`. La separación no es cosmética: es la única superficie con autenticación de máquina, y el prefijo es lo que el middleware usa para saber qué medir.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Catálogo, autenticación, throttle y repositorios — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase. **T006 bloquea todo el registro de consumo**: sin el catálogo sembrado, `Fact_APIIntegracion.idestadointegracion` apunta a nada.

- [X] T006 Sembrar `Dim_EstadoIntegracion` con `Pruebas activo`, `Producción activa` y `Suspendido` (hoy la tabla tiene **0 filas**), alineados con los estados derivados de `partner-api-onboarding` § 9, en `database/seed_estado_integracion.py` — **hecho 2026-08-09**: 3 estados sembrados en Pinot, reejecución idempotente confirmada. Se evaluó y **descartó** sembrar aquí una taxonomía de condición de acceso (cuota al 80 %, rate limited, suspendido por mora): choca con RN-APM-003, con § 15 D2 y con la propiedad de #09 — razonamiento completo en `data-model.md`. **Duda resuelta el mismo día**: se confirmó que el estado 3 `Suspendido` **es inalcanzable** —un partner suspendido recibe 403 y su llamada no genera fila— y quedó **desactivado** (`activo = false`), con la razón escrita en su propia descripción. El catálogo opera con **2 estados**: `1` Pruebas activo (Sandbox) y `2` Producción activa (Producción). Al registrar consumo se escribe el que corresponde al entorno de la credencial; **nunca `3`**
- [X] T007 Implementar `EstadoIntegracionRepository` (lectura del catálogo + resolución del estado vigente del partner) en `backend/core/repositories/partners/estado_integracion_repository.py` — **hecho** — solo lectura (el catálogo lo siembra el script) y `estado_para_entorno()` resuelve del **entorno**, no del estado derivado: son los dos únicos valores que una llamada atendida puede tener.
- [X] T008 [P] Crear test de repositorio (marker: repository, AAA) de `estado_integracion_repository.py` en `backend/apps/partners/tests/repositories/test_estado_integracion_repository.py` — **hecho** — 11 tests, incluido que **nunca** se resuelva al estado 3 y que un entorno desconocido lance en vez de adivinar.
- [X] T009 Implementar `ApiIntegracionRepository` con publicación a `Fact_APIIntegracion_topic` y **agregaciones con `entorno='Producción'` y `LIMIT` explícito obligatorios** (Pinot aplica `LIMIT 10` implícito y silencioso) en `backend/core/repositories/partners/api_integracion_repository.py` — **hecho**: append-only sin `update`/`delete`, `llamadas` siempre 1, y `EntornoRequeridoError` que hace **imposible** agregar sin filtrar por entorno.
- [X] T010 [P] Crear test de repositorio (marker: repository, AAA) de `api_integracion_repository.py`, verificando que **ninguna agregación omite el filtro de entorno ni el `LIMIT`**, en `backend/apps/partners/tests/repositories/test_api_integracion_repository.py` — **hecho** — 16 tests. Incluye un guardián que recorre las agregaciones públicas y falla si alguna no exige `entorno` en su firma: caza el defecto antes que la revisión de código.
- [X] T011 Implementar `LogLlamadaRepository` (`Fact_LogLlamadaAPI_topic`, append-only) en `backend/core/repositories/partners/log_llamada_repository.py` — **hecho**: append-only, y `ip_a_entero()` porque el esquema declara `iporigen` como INT, no STRING.
- [X] T012 [P] Crear test de repositorio (marker: repository, AAA) de `log_llamada_repository.py` verificando que **no expone UPDATE ni DELETE** (RNF-APM-005) en `backend/apps/partners/tests/repositories/test_log_llamada_repository.py` — **hecho** — 14 tests, incluido que un `429` **sí** se registre aquí y **no** en `Fact_APIIntegracion`: es la distinción entre «te limité el ritmo» y «te cobro esta llamada».
- [X] T013 Implementar `CredencialAPIAuthentication` (resuelve `client_id` + `client_secret` contra `Dim_CredencialAPI` verificando el hash **bcrypt**; rechaza inexistente, `activo=false` y vencida por comparación `fecha_expiracion < ahora`) en `backend/apps/partners/authentication.py` — **hecho** en `authentication.py`: resuelve `X-Client-Id`/`X-Client-Secret` contra `Dim_CredencialAPI` con verificación bcrypt, y rechaza inexistente, revocada y vencida. La vigencia se **deriva del dato** (`fecha_expiracion < ahora`), no de que un job la haya marcado.
- [X] T014 [P] Crear test unitario (marker: unit, AAA) de `authentication.py`: credencial válida, inexistente, revocada, vencida, y **que un JWT humano NO autentique en la API de datos**, en `backend/apps/partners/tests/unit/test_credencial_authentication.py` — **hecho** — 16 tests. El bloque que más importa es `TestUnJwtHumanoNoAutenticaAqui`: sin cabeceras de credencial devuelve `None` (no falla), que es lo que hace que DRF responda 401 y no 403, y un `Authorization: Bearer` no abre esta puerta.
- [X] T015 Añadir el throttle rate del partner a `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES` en `backend/config/settings.py` (hoy hay tres rates y ninguno de partners) — **hecho**: rate `partner_api` añadido, con el comentario de que es techo de plataforma y **no** la cuota comercial.
- [X] T016 Implementar `PartnerRateThrottle` que lee `Dim_Partner.limitellamadasminuto` y devuelve **429 con `Retry-After`**, en `backend/apps/partners/throttling.py` — documentar en el docstring que es **protección de plataforma, NO aplicación de la cuota comercial** (§ 15 D2) — **hecho**: lee `Dim_Partner.limitellamadasminuto`, no throttlea con el centinela `-1`, y `wait()` nunca devuelve 0 —un `Retry-After: 0` invita a reintentar y volver a chocar—. El docstring deja escrito que **no** es la aplicación de la cuota comercial.
- [X] T017 [P] Crear test unitario (marker: unit, AAA) de `throttling.py`: se respeta `limitellamadasminuto`, cupo `-1` (centinela) no throttlea, y la respuesta incluye `Retry-After`, en `backend/apps/partners/tests/unit/test_partner_throttling.py` — **hecho** — 12 tests: límite por partner, contadores independientes entre partners, el centinela `-1` no throttlea pero el `0` **sí** es un límite real, y los usuarios humanos no pasan por aquí.

**Checkpoint**: catálogo sembrado, autenticación por credencial, throttle y repositorios listos.

---

## Phase 3: User Story 1 — Consumir datos de forma segura y medida (Priority: P1) 🎯 MVP

**Goal**: CU-O51 completo + la escritura de CU-O52. La API que el partner consume, con sus filtros de seguridad, y cada llamada registrada.

**Independent Test**: un partner con credencial de producción consulta expedientes, recibe solo los de sus severidades y zonas contratadas, y la llamada queda registrada en las dos tablas.

**Measurable Criteria**: CA-APM-001, CA-APM-002, CA-APM-003, CA-APM-004, CA-APM-005, CA-APM-015, CA-APM-016; escenarios A–D, F, G, N.

### Tests for User Story 1

- [X] T018 [P] [US1] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/datos/accidentes` en `backend/apps/partners/tests/api/test_consumo_datos_contract.py` — **hecho** — 9 tests: camino feliz, `meta` con el alcance aplicado, 403 por severidad fuera de plan, y que la llamada quede en **las dos** tablas con latencia > 0 (un 0 delataría que la medición no envuelve la petición).
- [X] T019 [P] [US1] Crear test de API (marker: api, AAA) de los rechazos de acceso: credencial revocada → 401, credencial vencida → 401, partner suspendido → 403, **cliente sin suscripción vigente → 403**, y que **ninguno deje fila en `Fact_APIIntegracion`**, en `backend/apps/partners/tests/api/test_consumo_rechazos.py` — **hecho** — 9 tests. **Encontró un defecto real**: un `403` quedaba registrado como consumo facturable, porque la autenticación había tenido éxito y solo falló el permiso. Corregido con `CODIGOS_NO_ATENDIDOS = {401, 403, 429}` en `registro_consumo_service`: rechazado en la puerta no es servicio prestado.
- [X] T020 [P] [US1] Crear test de servicio (marker: service, AAA) de `consumo_datos_service.py`: severidad no habilitada → **403, no lista vacía**; cliente sin zonas → **conjunto vacío (fail-closed)**, en `backend/apps/partners/tests/services/test_consumo_datos_service.py` — **hecho** — 12 tests. El núcleo es que los dos filtros fallan **distinto**: severidad fuera de plan lanza (403) y cliente sin zonas devuelve vacío (fail-closed).
- [X] T021 [P] [US1] Crear test de servicio (marker: service, AAA) de `registro_consumo_service.py`: escribe **una fila en cada tabla**, `errores` derivado del `codigohttp`, `idestadointegracion` congelado, en `backend/apps/partners/tests/services/test_registro_consumo_service.py` — **hecho** — 13 tests: una fila en cada tabla, `errores` derivado del código y `idestadointegracion` congelado según el entorno (nunca el 3).
- [X] T022 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique la **regla contable del 429**: deja fila en `Fact_LogLlamadaAPI` y **ninguna** en `Fact_APIIntegracion` (§ 15 D2), en `backend/apps/partners/tests/services/test_throttle_no_es_consumo.py` — **cubierto** en `test_registro_consumo_service.py::TestReglaContableDel429`: 10 llamadas throttleadas dejan 10 filas de log y **ninguna** facturable.
- [X] T023 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique que **un fallo al publicar el consumo NO altera la respuesta al partner** y queda registrado para reconciliación (RN-APM-005), en `backend/apps/partners/tests/services/test_registro_no_rompe_respuesta.py` — **cubierto** en `TestElRegistroNoRompeLaRespuesta`: falla el consumo, falla el log, fallan ambos — nunca propaga, y el fallo queda en el log de aplicación para reconciliación.

### Implementation for User Story 1

- [X] T024 [US1] Implementar `ConsumoDatosService` (RF-APM-002 nivel de acceso por `Dim_Plan.severidades_desbloqueadas`; RF-APM-003 zonas **reutilizando `HistorialEmergenciasService.condados_desde_preferencias()`**, no un mecanismo nuevo) en `backend/apps/partners/services/consumo_datos_service.py` — **hecho**, con **tres correcciones sobre lo que decía el spec**, todas verificadas contra la base real: (a) las severidades se leen de `Fact_Suscripcion`, no de `Dim_Plan` —los 5 planes tienen el centinela `'null'` y leer de ahí dejaría a todo partner sin datos—; (b) `Dim_Preferencias_Cliente` usa `id_cliente`, no `idcliente`; (c) **`Fact_Accidente` no tiene `idcondado`**, así que el condado se resuelve desde `idcalle` con `GeografiaRepository`, que es justo el mecanismo que RF-APM-003 manda reutilizar.
- [X] T024b [US1] Añadir a la autenticación la comprobación de **suscripción vigente** (`Fact_Suscripcion.estado`) además del estado del partner, en `backend/apps/partners/authentication.py` — **decisión D2 de `partner-access-management`**: las dos suspensiones son independientes y el acceso exige ambas. Cierra el hueco de que un cliente con la suscripción suspendida siguiera consumiendo — **adelantado a la Fase 2**: se implementó como el permiso `PartnerHabilitado` en `authentication.py`. Va en un permiso y no en `authenticate()` porque son **autorización, no identidad**: la spec pide 403 para ambas condiciones, y DRF solo devuelve 403 desde un permiso. Cubre partner activo **y** suscripción vigente — el hueco por el que un cliente con la suscripción suspendida seguía consumiendo. 4 tests en `test_credencial_authentication.py`.
- [X] T025 [US1] Implementar `RegistroConsumoService` (escribe las dos filas en el mismo instante, resuelve `idestadointegracion`) en `backend/apps/partners/services/registro_consumo_service.py` — **hecho**: escribe en las dos tablas, resuelve el estado congelado desde el entorno y **nunca propaga** un fallo de publicación.
- [X] T026 [US1] Implementar el middleware de registro que mide latencia y publica **fuera del camino crítico, en `try/except` que nunca propaga**, en `backend/apps/partners/middleware/registro_consumo.py` — registra **todas** las peticiones, incluidas 4xx/5xx (RN-APM-009), y omite `Fact_APIIntegracion` solo en el caso 429 — **hecho**: mide la latencia que el partner percibe de verdad, se limita a `/api/v1/datos/` y **nunca altera la respuesta** (`try/except` que no propaga). Va en middleware y no en cada vista para que una vista nueva quede medida sin que su autor se acuerde, y para capturar también los rechazos que DRF genera antes de entrar a la vista.
- [X] T027 [US1] Registrar el middleware en `backend/config/settings.py`, acotado al grupo de rutas `/datos/*` — **hecho**: registrado el **último** de la cadena, para que la latencia medida incluya a todos los demás middlewares.
- [X] T028 [US1] Implementar `ConsultarAccidentesView` con `CredencialAPIAuthentication` y `PartnerRateThrottle`, exponiendo `meta.zonas_aplicadas` para que un resultado vacío sea explicable, en `backend/apps/partners/views/datos_views.py` — **hecho**: `CredencialAPIAuthentication` + `PartnerHabilitado` + `PartnerRateThrottle`, y expone `meta.zonas_aplicadas` y `meta.severidades_aplicadas` para que un resultado vacío sea explicable sin abrir la base.

**Checkpoint**: US1 operativa — el partner consume datos y cada llamada se mide.

**US1 Gate**:
- [X] T029 [US1] Marcar CA-APM-001–005, CA-APM-015 y CA-APM-016 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md` — **hecho** en `traceability.md`.

---

## Phase 4: User Story 2 — Ver el consumo (Priority: P1)

**Goal**: la parte de lectura de CU-O52 — métricas del partner, consola del Desarrollador de APIs y reporte mensual.

**Independent Test**: tras generar consumo en ambos entornos, el partner ve **solo producción** en sus métricas, el Desarrollador de APIs ve el detalle de cada llamada, y un mes sin consumo devuelve ceros.

**Measurable Criteria**: CA-APM-006, CA-APM-007, CA-APM-008, CA-APM-009; escenarios G, H.

### Tests for User Story 2

- [X] T030 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/partners/{id}/metricas` en `backend/apps/partners/tests/api/test_metricas_contract.py` — **hecho** — 5 tests en `test_metricas_contract.py`.
- [X] T031 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/logs-api` con filtros y paginación por cursor en `backend/apps/partners/tests/api/test_consola_logs_contract.py` — **cubierto** en `TestConsolaLogsContract` (5 tests): solo Desarrollador de APIs, filtro de errores y paginación por cursor.
- [X] T032 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/reportes-consumo`, incluyendo que **un mes sin consumo devuelve ceros y no error**, en `backend/apps/partners/tests/api/test_reporte_consumo_contract.py` — **cubierto** en `TestReporteConsumoContract` (4 tests), incluido que **un mes sin consumo devuelve ceros y no 404**: que el partner no consumiera es una respuesta válida.
- [X] T033 [P] [US2] Crear test de servicio (marker: service, AAA) que verifique la **separación de entornos**: un partner con consumo en `Sandbox` y `Producción` ve solo producción en métricas y reporte (RN-APM-001), en `backend/apps/partners/tests/services/test_separacion_entornos.py` — **cubierto** en `TestSeparacionDeEntornos` (3 tests). El más útil: con 500 llamadas de sandbox y cupo 100, contarlas daría **400 de excedente facturable que el partner no debe**.
- [X] T034 [P] [US2] Crear test de API (marker: api, AAA) del control de propiedad: consultar métricas de otro partner → **403**; partner **suspendido** consultando las suyas → **200** (RN-APM-017), en `backend/apps/partners/tests/api/test_propiedad_metricas.py` — **cubierto** en `TestPropiedadDeLasMetricas`: 403 sobre partner ajeno, y **200 para un partner suspendido consultando las suyas** (RN-APM-017) — negárselo lo castigaría dos veces.

### Implementation for User Story 2

- [X] T035 [US2] Implementar `MetricasConsumoService` (agregaciones de llamadas, errores y latencia; `excedente_estimado`; `datos_hasta` para no prometer latencia cero) en `backend/apps/partners/services/metricas_consumo_service.py` — **hecho**: agregaciones, `excedente_estimado` y `datos_hasta`. Tres decisiones documentadas: solo producción por defecto; `datos_hasta` resta la ventana de ingesta de Kafka en vez de prometer tiempo real; y sin tarifa configurada el estimado es `None`, **no 0.0** — un 0 haría creer al partner que su exceso es gratis.
- [X] T036 [US2] Implementar `MetricasPartnerView` con control de propiedad en `backend/apps/partners/views/metricas_views.py` — **hecho**, con control de propiedad y **sin** comprobar `activo`: un suspendido sí lee las suyas.
- [X] T037 [P] [US2] Implementar `ConsolaLogsView` (solo Desarrollador de APIs) en `backend/apps/partners/views/consola_views.py` — **hecho**: exclusiva del Desarrollador de APIs, con paginación por cursor.
- [X] T038 [P] [US2] Implementar `ReporteConsumoView` (el Cliente solo el suyo; el Administrador cualquiera) en `backend/apps/partners/views/reportes_views.py` — **hecho**: mes natural completo, ceros cuando no hubo consumo.

**Checkpoint**: US2 operativa — el consumo es visible para los tres actores.

**US2 Gate**:
- [X] T039 [US2] Marcar CA-APM-006–009 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md` — **hecho** en `traceability.md`.

---

## Phase 5: User Story 3 — Límites y alertas (Priority: P2)

**Goal**: CU-O53 — comparar el consumo contra el cupo y avisar, **sin bloquear nunca**.

**Independent Test**: un partner que cruza el 80 % del cupo recibe aviso; al alcanzarlo recibe otro; al superarlo **sus llamadas se siguen atendiendo** y no se duplican avisos.

**Measurable Criteria**: CA-APM-010; escenario E.

### Tests for User Story 3

- [X] T040 [P] [US3] Crear test de servicio (marker: service, AAA) de `limites_consumo_service.py`: alerta al aproximarse (80 %) y al alcanzar el cupo, **sin duplicar dentro del mismo período** (RN-APM-010), en `backend/apps/partners/tests/services/test_limites_consumo_service.py` — **hecho** — 14 tests en `test_limites_consumo_service.py`: umbrales 80/100, no duplicación por período, y que cruzar el 100 **sí** emite aviso nuevo (haber avisado del 80 no consume el 100).
- [X] T041 [P] [US3] Crear test de API (marker: api, AAA) que verifique que **superar el cupo mensual NO interrumpe el servicio**: las llamadas posteriores devuelven 200 y se registran como consumo (RN-APM-002), en `backend/apps/partners/tests/api/test_cuota_no_bloquea.py` — **hecho** — 4 tests en `test_cuota_no_bloquea.py`. Con el cupo superado 20 veces, cinco llamadas seguidas devuelven **200** y **cada una se registra como consumo**: no bloquear y facturar el exceso son la misma moneda; si no se registrara, el exceso sería gratis.
- [X] T042 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que un partner con cupo `-1` (centinela «sin cupo asignado») **no dispara alertas** en `backend/apps/partners/tests/services/test_cupo_sin_asignar.py` — **cubierto** en `TestCupoSinAsignar`: el centinela `-1` devuelve `aplica: False`. Tratarlo como límite avisaría «superaste tu cupo» en la primera llamada.

### Implementation for User Story 3

- [X] T043 [US3] Implementar `LimitesConsumoService` (agrega el consumo del período y lo compara contra `Dim_Partner.limitellamadasmes`; **nunca restringe**) en `backend/apps/partners/services/limites_consumo_service.py` — **hecho**. Incluye un **guardián de la regla**: un test comprueba que el servicio no expone ningún método que suene a bloquear/restringir/cortar/denegar. RN-APM-002 deja de depender de que nadie lo olvide.
- [X] T044 [US3] Implementar el job de alertas de cuota, con comprobación de no duplicación contra los avisos ya emitidos en el período, en `backend/apps/partners/jobs/alertas_cuota_job.py` — **hecho**, fail-open por partner: un fallo evaluando a uno no impide avisar a los demás, y el job informa de cuántos fallaron. Un test lo verifica con un partner que revienta.
- [X] T045 [US3] Implementar el comando de gestión que dispara el job en `backend/apps/partners/management/commands/run_alertas_cuota_job.py` — **hecho**: idempotente, pensado para cron/Airflow. Ejecutarlo de más no molesta al partner porque los avisos no se duplican.

**Checkpoint**: US3 operativa — el partner sabe cuánto lleva consumido antes de que le llegue la factura.

**US3 Gate**:
- [X] T046 [US3] Marcar CA-APM-010 como cubierto en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md` — **hecho** en `traceability.md`.

---

## Phase 6: User Story 4 — Tarificar el excedente (Priority: P2)

**Goal**: CU-O54 — el corte mensual que convierte el consumo medido en dinero.

**Independent Test**: un partner con 12 500 llamadas sobre un cupo de 10 000 genera una factura de excedente por 2 500 × tarifa; un segundo corte del mismo período **no emite una segunda factura**.

**Measurable Criteria**: CA-APM-011, CA-APM-012, CA-APM-013, CA-APM-014; escenarios I–M.

### Tests for User Story 4

- [X] T047 [P] [US4] Crear test de servicio (marker: service, AAA) de `tarificacion_excedente_service.py`: separa incluido de excedente y calcula `excedente × precio_excedente_llamada`; dentro del cupo **no emite factura**, en `backend/apps/partners/tests/services/test_tarificacion_excedente_service.py` — **hecho** — 18 tests en `test_tarificacion_excedente_service.py`: separa incluido de excedente y calcula el importe.
- [X] T048 [P] [US4] Crear test de servicio (marker: service, AAA) de **no duplicación**: con factura previa de ese `id_cliente`+`periodo`+`tipo='excedente_api'`, el corte **no emite una segunda** (RN-APM-012), en `backend/apps/partners/tests/services/test_no_duplicacion_factura.py` — **cubierto** en `TestNoDuplicacion` (3 tests). Incluye el caso real —el job corre dos veces por un reintento mal contado— y que una factura de **suscripción** del mismo período **no** bloquee la de excedente: son cobros distintos.
- [X] T049 [P] [US4] Crear test de servicio (marker: service, AAA) de los **reintentos persistidos**: fallos sucesivos programan 1 h → 6 h → 24 h actualizando `reintentos` y `resultado_ultimo_reintento`; agotados → pendiente de emisión manual + alerta a Administrador y Desarrollador de APIs. **Se simula adelantando el reloj, no esperando**, en `backend/apps/partners/tests/services/test_reintentos_facturacion.py` — **cubierto** en `TestReintentosPersistidos`: los escalones son exactamente 1 h → 6 h → 24 h, cada intento persiste su resultado, y agotados los tres queda pendiente de emisión manual con alerta. Se simula **adelantando el reloj** (`ahora_ms`), nunca esperando.
- [X] T050 [P] [US4] Crear test de servicio (marker: service, AAA) del centinela de tarifa: `precio_excedente_llamada = -1.0` → **alerta y NO emite factura de importe cero** (§ 15 D1), en `backend/apps/partners/tests/services/test_tarifa_sin_configurar.py` — **cubierto** en `TestCentinelaDeTarifa`: con `-1.0` **no se emite factura** y se alerta. Facturar cero sería ingreso real no cobrado en silencio. Un precio negativo cuenta igual.
- [X] T051 [P] [US4] Crear test de servicio (marker: service, AAA) que verifique que una factura **en disputa** queda excluida del cobro automático (RN-APM-016) en `backend/apps/partners/tests/services/test_factura_en_disputa.py` — **cubierto** en `TestFacturaEnDisputa`: no se reemite, no entra en los reintentos, y un guardián comprueba que este módulo **no expone** métodos para abrir o resolver disputas — solo respeta la exclusión.
- [X] T052 [P] [US4] Crear test de servicio (marker: service, AAA) de **determinismo** (RNF-APM-001): dos ejecuciones del corte sobre el mismo período y los mismos datos producen el mismo importe, en `backend/apps/partners/tests/services/test_corte_determinista.py` — **cubierto** por `test_es_determinista`: dos cálculos sobre los mismos datos devuelven diccionarios idénticos. Es la base de poder discutir una factura con el cliente.

### Implementation for User Story 4

- [X] T053 [US4] Implementar `TarificacionExcedenteService` (agregación del período, separación incluido/excedente, cálculo del importe, verificación de no duplicación, y emisión vía `FacturaRepository` de Suscripciones) en `backend/apps/partners/services/tarificacion_excedente_service.py` — **hecho**. Cuatro reglas documentadas en el propio módulo, todas protegiendo al cliente antes que al negocio.
- [X] T054 [US4] Implementar la política de reintentos **por estado persistido** —nunca con `sleep`, para que sobreviva a un reinicio del contenedor— en `backend/apps/partners/services/tarificacion_excedente_service.py`, siguiendo el patrón de `backend/apps/suscripciones/jobs/dunning_job.py` — **hecho**: reintentos por **estado persistido en la propia factura**. Un test lee el código fuente y falla si aparece un `sleep` — con `sleep`, un reinicio del contenedor perdería el reintento y el cobro quedaría a medias sin rastro.
- [X] T055 [US4] Implementar el job de corte, que en cada ejecución procesa los cortes pendientes **y los reintentos ya vencidos**, en `backend/apps/partners/jobs/facturacion_excedente_job.py` — **hecho**: cada ejecución procesa los cortes pendientes **y** los reintentos vencidos, porque el reintento no es un proceso aparte sino el mismo corte más tarde.
- [X] T056 [US4] Implementar el comando de gestión (ejecución **horaria**, para que los escalones de 1 h/6 h/24 h se respeten) en `backend/apps/partners/management/commands/run_facturacion_excedente_job.py` — **hecho**, con ejecución **horaria** y corte del mes anterior por defecto. Con ejecución mensual el primer reintento (1 h) llegaría treinta días tarde. Los dos casos que exigen intervención humana —sin tarifa y cortes fallidos— salen por `stderr`, no se quedan en un log.
- [X] T057 [US4] Implementar las alertas de excepción de facturación al Administrador y al Desarrollador de APIs en `backend/apps/partners/services/tarificacion_excedente_service.py`, reutilizando el mecanismo de notificación existente — **verificar cuál antes de implementar** — **hecho** en el propio servicio: alerta de «no tarificable» y de «reintentos agotados», ambas fail-open (un buzón caído no tumba el corte).

**Checkpoint**: US4 operativa — el departamento ya genera ingreso exigible.

**US4 Gate**:
- [X] T058 [US4] Marcar CA-APM-011–014 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md` — **hecho** en `traceability.md`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: cierre de calidad, seguridad y verificación real.

- [X] T059 [P] Crear test de servicio (marker: service, AAA) que verifique que **`Fact_APIIntegracion` y `Fact_LogLlamadaAPI` son append-only**: ningún repositorio del módulo expone UPDATE ni DELETE (RNF-APM-005), en `backend/apps/partners/tests/services/test_append_only_consumo.py` — **hecho** en `test_invariantes_modulo.py`: ningún repositorio de consumo expone `update`/`delete`/`desactivar`, y el único camino de escritura es `registrar`. Es un guardián: falla el día que alguien añada un método destructivo.
- [X] T060 [P] Crear test de API (marker: api, AAA) que verifique la **separación de superficies**: un JWT humano no autentica en `/datos/*` y una credencial de API no autentica en `/logs-api`, en `backend/apps/partners/tests/api/test_separacion_superficies.py` — **hecho** — 4 tests: un JWT humano no entra en `/datos/*`, una credencial de máquina no entra en las pantallas, y el throttle está solo donde debe (aplicarlo a las pantallas limitaría a un operador por mirar sus métricas).
- [X] T061 [P] Añadir auditoría estructurada de los intentos de emisión y su resultado en `backend/apps/partners/services/tarificacion_excedente_service.py` (RNF-APM-006) — **hecho**: `_auditar()` deja rastro estructurado del intento, de la emisión y del caso no tarificable. Facturar es la acción con más consecuencias del módulo: si un cliente discute un cobro, esto permite reconstruir qué se calculó y con qué cifras.
- [X] T062 **Crear `database/verifica_monitoreo_api.py`** contra Pinot real con las 6 comprobaciones de `quickstart.md` §5: exactitud de `SUM(llamadas)`, separación de entornos, regla contable del 429, centinela de tarifa, mes vacío y `LIMIT` explícito — **hecho** — `database/verifica_monitoreo_api.py` con las 6 comprobaciones. **Pendiente de ejecutar** (T066): requiere el contenedor encendido.
- [X] T063 Medir p95 de `GET /datos/accidentes` **con y sin** el registro activo, para aislar su coste y el de bcrypt (RNF-APM-002), y registrar la evidencia en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md` — **hecho: p95 = 214 ms** con el registro activo (umbral 2000). El coste aislado del registro salió **negativo (−29 ms)**: está por debajo del ruido de medición con n=20 porque bcrypt domina. La conclusión honesta es «despreciable frente a bcrypt», no un número.
- [X] T064 Medir la capacidad de escritura sostenida (RNF-APM-003) y registrarla en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md` — **hecho: 21 254 registros/s** (umbral 50). **Ojo**: medido contra el doble en memoria, así que mide el sobrecoste del servicio, no el rendimiento real de Kafka.
- [X] T065 Verificar cobertura ≥ 80 % con `pytest --cov=apps/partners/services` desde `backend/` (RNF-APM-008) — **hecho: cobertura de servicios 93 %** (umbral 80 %). Por servicio: límites 100 · registro de consumo 100 · tarificación 93 · consumo de datos 90 · métricas 87.
- [X] T066 **Ejecutar `python database/verifica_monitoreo_api.py` contra Pinot real** — criterio de salida **obligatorio**, no sustituible por `pytest`: este módulo vive de agregaciones y el doble de `conftest.py` no las reproduce (`decisiones-pendientes.md` #18) — **hecho: 9/9 contra Pinot real.** Incluye lo que un mock no puede probar: que el `LIMIT 10` implícito **no trunca** la agregación (37 > 10) y que el filtro de entorno excluye de verdad el sandbox (sin él darían 48). Cierra `decisiones-pendientes.md` #18 para este módulo.
- [X] T067 Ejecutar la suite completa desde `backend/` (`python -m pytest -q`, config en `backend/pytest.ini`) y confirmar que no hay regresiones sobre la línea base de **1042 passed, 2 skipped** — **hecho**: **1430 passed, 2 skipped** antes del polish; el módulo `partners` tiene **396 tests**. Cero regresiones sobre la línea base de 1272.
- [X] T068 Limpiar los datos de prueba con `python database/limpia_datos_prueba.py` y confirmar que los datos reales siguen intactos — **hecho**, tras **extender el script**: la versión de #07 no incluía `Fact_APIIntegracion` ni `Fact_LogLlamadaAPI` y dejaba 48 filas de consumo que habrían falseado métricas y excedentes. Las 7 tablas a 0; datos reales intactos (`Fact_Reclamo` 8, `Fact_Historial_Ticket` 9).
- [X] T069 Actualizar el estado del módulo en `.specify/docs/architecture/module-map.md` §4 y cerrar los ítems de `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/checklists/requirements.md` — **hecho**: `module-map.md` § 4 actualizado con las cifras reales y con lo que queda pendiente de verificación.
- [X] T070 Cambiar `.specify/feature.json` a `…/api-monitoring-and-billing/frontend` para abrir la capa de Interaction Capability — **hecho**: `.specify/feature.json` apunta a `…/api-monitoring-and-billing/frontend`.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
   └─► Phase 2 (Foundational)   ◄── T006 (seed) bloquea todo el registro de consumo
          └─► Phase 3 (US1)  🎯 MVP   ◄── requiere #07 implementado para probarse E2E
                 ├─► Phase 4 (US2)   necesita consumo escrito para poder leerlo
                 ├─► Phase 5 (US3)   necesita consumo escrito para comparar contra el cupo
                 └─► Phase 6 (US4)   necesita consumo escrito para tarificar
                        └─► Phase 7 (Polish)
```

### User Story Dependencies

| Historia | Depende de | Motivo |
|---|---|---|
| US1 | Phase 2 + **#07 implementado** | Sin credenciales de producción no hay nada que medir |
| US2 | US1 | Lee lo que US1 escribe |
| US3 | US1 | Compara contra el consumo que US1 registra |
| US4 | US1 | Tarifica el consumo que US1 registra |

**US2, US3 y US4 son independientes entre sí**: una vez cerrada US1, las tres pueden avanzar en paralelo.

### Parallel Opportunities

- **Phase 2**: los pares test↔implementación de repositorios (T007–T012) son independientes entre sí; T013–T017 (auth y throttle) tampoco dependen de ellos.
- **US2, US3 y US4 en paralelo** tras US1 — es la mayor oportunidad del módulo.
- **Phase 7**: T059–T061 en paralelo.

### Parallel Example: tras cerrar US1

```bash
# Tres frentes independientes:
Phase 4 (US2)  métricas, consola y reporte
Phase 5 (US3)  límites y alertas
Phase 6 (US4)  tarificación del excedente
```

---

## Implementation Strategy

### MVP First (User Story 1)

US1 entrega lo esencial: **el partner consume datos con los filtros de seguridad correctos y cada llamada queda medida**. Sin ella, las otras tres historias no tienen sobre qué operar — no hay consumo que mostrar, que limitar ni que facturar.

### Incremental Delivery

1. **Phase 1 + 2** → catálogo, autenticación por credencial, throttle y repositorios.
2. **+ US1** → 🎯 MVP: la API de datos funciona y se mide.
3. **+ US2** → el consumo es visible para partner, Desarrollador de APIs y Cliente.
4. **+ US3** → nadie se lleva una sorpresa en la factura: avisos antes de llegar al cupo.
5. **+ US4** → **el excedente se cobra**; la línea de ingresos por consumo pasa a ser exigible.
6. **+ Phase 7** → cierre de calidad y apertura de la capa frontend.

---

## Notes

- **Superar el cupo NO bloquea** (RN-APM-002). Es la regla que más fácil se implementa mal, porque la intuición dice lo contrario. El SRS la blinda explícitamente. T041 existe para protegerla.
- **El 429 sí rechaza, pero no es consumo facturable** (§ 15 D2): deja log, no deja fila de consumo. Cobrar peticiones no servidas sería cobrar de más. T022 lo verifica.
- **Los reintentos viven en los datos, no en el proceso** (T054): un `sleep` de 24 h muere con el contenedor y la factura quedaría sin crearse en silencio.
- **Una tarifa sin configurar alerta, no factura cero** (T050): facturar cero sería ingreso real no cobrado y sin rastro.
- **El filtro de zonas falla hacia el lado cerrado** (T020): sin zonas configuradas, conjunto vacío. Exponer siniestralidad no contratada es una fuga.
- **Toda agregación lleva `entorno='Producción'` y `LIMIT` explícito** (T010): Pinot aplica `LIMIT 10` implícito y no lo señala.
- **T066 es el criterio de salida que `pytest` no puede sustituir.** Este módulo vive de agregaciones reales.
