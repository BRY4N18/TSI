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

## Phase 1: Setup

**Purpose**: Preparar la app y validar el contrato antes de escribir código.

- [ ] T001 Crear subcarpetas del módulo en `backend/apps/partners/{middleware,jobs}` y `backend/apps/partners/tests/{api,services,repositories,unit}` (la app `partners/` ya existe desde #07)
- [ ] T002 [P] Añadir las 3 tablas de este módulo al doble en memoria `PINOT_STORE` de `backend/conftest.py`: `Fact_APIIntegracion`, `Fact_LogLlamadaAPI`, `Dim_EstadoIntegracion`
- [ ] T003 [P] Añadir fixtures de autenticación por credencial (`credencial_sandbox_headers`, `credencial_produccion_headers`) y de rol (`devapis_auth_headers`) en `backend/conftest.py`
- [ ] T004 Validar el contrato OpenAPI como gate: sintaxis, refs, y que **solo `/datos/*` use `credencialAuth`** mientras métricas, logs y reportes usan `bearerAuth`, en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/contracts/api-monitoring-and-billing.openapi.yaml`
- [ ] T005 [P] Registrar las rutas del módulo en `backend/apps/partners/views/urls.py`, separando el grupo `/datos/*` del grupo de gestión

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Catálogo, autenticación, throttle y repositorios — bloquea todas las historias.

**CRITICAL**: Ninguna historia puede arrancar sin esta fase. **T006 bloquea todo el registro de consumo**: sin el catálogo sembrado, `Fact_APIIntegracion.idestadointegracion` apunta a nada.

- [ ] T006 Sembrar `Dim_EstadoIntegracion` con `Pruebas activo`, `Producción activa` y `Suspendido` (hoy la tabla tiene **0 filas**), alineados con los estados derivados de `partner-api-onboarding` § 9, en `database/seed_estado_integracion.py`
- [ ] T007 Implementar `EstadoIntegracionRepository` (lectura del catálogo + resolución del estado vigente del partner) en `backend/core/repositories/partners/estado_integracion_repository.py`
- [ ] T008 [P] Crear test de repositorio (marker: repository, AAA) de `estado_integracion_repository.py` en `backend/apps/partners/tests/repositories/test_estado_integracion_repository.py`
- [ ] T009 Implementar `ApiIntegracionRepository` con publicación a `Fact_APIIntegracion_topic` y **agregaciones con `entorno='Producción'` y `LIMIT` explícito obligatorios** (Pinot aplica `LIMIT 10` implícito y silencioso) en `backend/core/repositories/partners/api_integracion_repository.py`
- [ ] T010 [P] Crear test de repositorio (marker: repository, AAA) de `api_integracion_repository.py`, verificando que **ninguna agregación omite el filtro de entorno ni el `LIMIT`**, en `backend/apps/partners/tests/repositories/test_api_integracion_repository.py`
- [ ] T011 Implementar `LogLlamadaRepository` (`Fact_LogLlamadaAPI_topic`, append-only) en `backend/core/repositories/partners/log_llamada_repository.py`
- [ ] T012 [P] Crear test de repositorio (marker: repository, AAA) de `log_llamada_repository.py` verificando que **no expone UPDATE ni DELETE** (RNF-APM-005) en `backend/apps/partners/tests/repositories/test_log_llamada_repository.py`
- [ ] T013 Implementar `CredencialAPIAuthentication` (resuelve `client_id` + `client_secret` contra `Dim_CredencialAPI` verificando el hash **bcrypt**; rechaza inexistente, `activo=false` y vencida por comparación `fecha_expiracion < ahora`) en `backend/apps/partners/authentication.py`
- [ ] T014 [P] Crear test unitario (marker: unit, AAA) de `authentication.py`: credencial válida, inexistente, revocada, vencida, y **que un JWT humano NO autentique en la API de datos**, en `backend/apps/partners/tests/unit/test_credencial_authentication.py`
- [ ] T015 Añadir el throttle rate del partner a `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES` en `backend/config/settings.py` (hoy hay tres rates y ninguno de partners)
- [ ] T016 Implementar `PartnerRateThrottle` que lee `Dim_Partner.limitellamadasminuto` y devuelve **429 con `Retry-After`**, en `backend/apps/partners/throttling.py` — documentar en el docstring que es **protección de plataforma, NO aplicación de la cuota comercial** (§ 15 D2)
- [ ] T017 [P] Crear test unitario (marker: unit, AAA) de `throttling.py`: se respeta `limitellamadasminuto`, cupo `-1` (centinela) no throttlea, y la respuesta incluye `Retry-After`, en `backend/apps/partners/tests/unit/test_partner_throttling.py`

**Checkpoint**: catálogo sembrado, autenticación por credencial, throttle y repositorios listos.

---

## Phase 3: User Story 1 — Consumir datos de forma segura y medida (Priority: P1) 🎯 MVP

**Goal**: CU-O51 completo + la escritura de CU-O52. La API que el partner consume, con sus filtros de seguridad, y cada llamada registrada.

**Independent Test**: un partner con credencial de producción consulta expedientes, recibe solo los de sus severidades y zonas contratadas, y la llamada queda registrada en las dos tablas.

**Measurable Criteria**: CA-APM-001, CA-APM-002, CA-APM-003, CA-APM-004, CA-APM-005, CA-APM-015, CA-APM-016; escenarios A–D, F, G, N.

### Tests for User Story 1

- [ ] T018 [P] [US1] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/datos/accidentes` en `backend/apps/partners/tests/api/test_consumo_datos_contract.py`
- [ ] T019 [P] [US1] Crear test de API (marker: api, AAA) de los rechazos de acceso: credencial revocada → 401, credencial vencida → 401, partner suspendido → 403, **cliente sin suscripción vigente → 403**, y que **ninguno deje fila en `Fact_APIIntegracion`**, en `backend/apps/partners/tests/api/test_consumo_rechazos.py`
- [ ] T020 [P] [US1] Crear test de servicio (marker: service, AAA) de `consumo_datos_service.py`: severidad no habilitada → **403, no lista vacía**; cliente sin zonas → **conjunto vacío (fail-closed)**, en `backend/apps/partners/tests/services/test_consumo_datos_service.py`
- [ ] T021 [P] [US1] Crear test de servicio (marker: service, AAA) de `registro_consumo_service.py`: escribe **una fila en cada tabla**, `errores` derivado del `codigohttp`, `idestadointegracion` congelado, en `backend/apps/partners/tests/services/test_registro_consumo_service.py`
- [ ] T022 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique la **regla contable del 429**: deja fila en `Fact_LogLlamadaAPI` y **ninguna** en `Fact_APIIntegracion` (§ 15 D2), en `backend/apps/partners/tests/services/test_throttle_no_es_consumo.py`
- [ ] T023 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique que **un fallo al publicar el consumo NO altera la respuesta al partner** y queda registrado para reconciliación (RN-APM-005), en `backend/apps/partners/tests/services/test_registro_no_rompe_respuesta.py`

### Implementation for User Story 1

- [ ] T024 [US1] Implementar `ConsumoDatosService` (RF-APM-002 nivel de acceso por `Dim_Plan.severidades_desbloqueadas`; RF-APM-003 zonas **reutilizando `HistorialEmergenciasService.condados_desde_preferencias()`**, no un mecanismo nuevo) en `backend/apps/partners/services/consumo_datos_service.py`
- [ ] T024b [US1] Añadir a la autenticación la comprobación de **suscripción vigente** (`Fact_Suscripcion.estado`) además del estado del partner, en `backend/apps/partners/authentication.py` — **decisión D2 de `partner-access-management`**: las dos suspensiones son independientes y el acceso exige ambas. Cierra el hueco de que un cliente con la suscripción suspendida siguiera consumiendo
- [ ] T025 [US1] Implementar `RegistroConsumoService` (escribe las dos filas en el mismo instante, resuelve `idestadointegracion`) en `backend/apps/partners/services/registro_consumo_service.py`
- [ ] T026 [US1] Implementar el middleware de registro que mide latencia y publica **fuera del camino crítico, en `try/except` que nunca propaga**, en `backend/apps/partners/middleware/registro_consumo.py` — registra **todas** las peticiones, incluidas 4xx/5xx (RN-APM-009), y omite `Fact_APIIntegracion` solo en el caso 429
- [ ] T027 [US1] Registrar el middleware en `backend/config/settings.py`, acotado al grupo de rutas `/datos/*`
- [ ] T028 [US1] Implementar `ConsultarAccidentesView` con `CredencialAPIAuthentication` y `PartnerRateThrottle`, exponiendo `meta.zonas_aplicadas` para que un resultado vacío sea explicable, en `backend/apps/partners/views/datos_views.py`

**Checkpoint**: US1 operativa — el partner consume datos y cada llamada se mide.

**US1 Gate**:
- [ ] T029 [US1] Marcar CA-APM-001–005, CA-APM-015 y CA-APM-016 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md`

---

## Phase 4: User Story 2 — Ver el consumo (Priority: P1)

**Goal**: la parte de lectura de CU-O52 — métricas del partner, consola del Desarrollador de APIs y reporte mensual.

**Independent Test**: tras generar consumo en ambos entornos, el partner ve **solo producción** en sus métricas, el Desarrollador de APIs ve el detalle de cada llamada, y un mes sin consumo devuelve ceros.

**Measurable Criteria**: CA-APM-006, CA-APM-007, CA-APM-008, CA-APM-009; escenarios G, H.

### Tests for User Story 2

- [ ] T030 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/partners/{id}/metricas` en `backend/apps/partners/tests/api/test_metricas_contract.py`
- [ ] T031 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/logs-api` con filtros y paginación por cursor en `backend/apps/partners/tests/api/test_consola_logs_contract.py`
- [ ] T032 [P] [US2] Crear test de contrato API (marker: api, AAA) de `GET /api/v1/reportes-consumo`, incluyendo que **un mes sin consumo devuelve ceros y no error**, en `backend/apps/partners/tests/api/test_reporte_consumo_contract.py`
- [ ] T033 [P] [US2] Crear test de servicio (marker: service, AAA) que verifique la **separación de entornos**: un partner con consumo en `Sandbox` y `Producción` ve solo producción en métricas y reporte (RN-APM-001), en `backend/apps/partners/tests/services/test_separacion_entornos.py`
- [ ] T034 [P] [US2] Crear test de API (marker: api, AAA) del control de propiedad: consultar métricas de otro partner → **403**; partner **suspendido** consultando las suyas → **200** (RN-APM-017), en `backend/apps/partners/tests/api/test_propiedad_metricas.py`

### Implementation for User Story 2

- [ ] T035 [US2] Implementar `MetricasConsumoService` (agregaciones de llamadas, errores y latencia; `excedente_estimado`; `datos_hasta` para no prometer latencia cero) en `backend/apps/partners/services/metricas_consumo_service.py`
- [ ] T036 [US2] Implementar `MetricasPartnerView` con control de propiedad en `backend/apps/partners/views/metricas_views.py`
- [ ] T037 [P] [US2] Implementar `ConsolaLogsView` (solo Desarrollador de APIs) en `backend/apps/partners/views/consola_views.py`
- [ ] T038 [P] [US2] Implementar `ReporteConsumoView` (el Cliente solo el suyo; el Administrador cualquiera) en `backend/apps/partners/views/reportes_views.py`

**Checkpoint**: US2 operativa — el consumo es visible para los tres actores.

**US2 Gate**:
- [ ] T039 [US2] Marcar CA-APM-006–009 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md`

---

## Phase 5: User Story 3 — Límites y alertas (Priority: P2)

**Goal**: CU-O53 — comparar el consumo contra el cupo y avisar, **sin bloquear nunca**.

**Independent Test**: un partner que cruza el 80 % del cupo recibe aviso; al alcanzarlo recibe otro; al superarlo **sus llamadas se siguen atendiendo** y no se duplican avisos.

**Measurable Criteria**: CA-APM-010; escenario E.

### Tests for User Story 3

- [ ] T040 [P] [US3] Crear test de servicio (marker: service, AAA) de `limites_consumo_service.py`: alerta al aproximarse (80 %) y al alcanzar el cupo, **sin duplicar dentro del mismo período** (RN-APM-010), en `backend/apps/partners/tests/services/test_limites_consumo_service.py`
- [ ] T041 [P] [US3] Crear test de API (marker: api, AAA) que verifique que **superar el cupo mensual NO interrumpe el servicio**: las llamadas posteriores devuelven 200 y se registran como consumo (RN-APM-002), en `backend/apps/partners/tests/api/test_cuota_no_bloquea.py`
- [ ] T042 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que un partner con cupo `-1` (centinela «sin cupo asignado») **no dispara alertas** en `backend/apps/partners/tests/services/test_cupo_sin_asignar.py`

### Implementation for User Story 3

- [ ] T043 [US3] Implementar `LimitesConsumoService` (agrega el consumo del período y lo compara contra `Dim_Partner.limitellamadasmes`; **nunca restringe**) en `backend/apps/partners/services/limites_consumo_service.py`
- [ ] T044 [US3] Implementar el job de alertas de cuota, con comprobación de no duplicación contra los avisos ya emitidos en el período, en `backend/apps/partners/jobs/alertas_cuota_job.py`
- [ ] T045 [US3] Implementar el comando de gestión que dispara el job en `backend/apps/partners/management/commands/run_alertas_cuota_job.py`

**Checkpoint**: US3 operativa — el partner sabe cuánto lleva consumido antes de que le llegue la factura.

**US3 Gate**:
- [ ] T046 [US3] Marcar CA-APM-010 como cubierto en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md`

---

## Phase 6: User Story 4 — Tarificar el excedente (Priority: P2)

**Goal**: CU-O54 — el corte mensual que convierte el consumo medido en dinero.

**Independent Test**: un partner con 12 500 llamadas sobre un cupo de 10 000 genera una factura de excedente por 2 500 × tarifa; un segundo corte del mismo período **no emite una segunda factura**.

**Measurable Criteria**: CA-APM-011, CA-APM-012, CA-APM-013, CA-APM-014; escenarios I–M.

### Tests for User Story 4

- [ ] T047 [P] [US4] Crear test de servicio (marker: service, AAA) de `tarificacion_excedente_service.py`: separa incluido de excedente y calcula `excedente × precio_excedente_llamada`; dentro del cupo **no emite factura**, en `backend/apps/partners/tests/services/test_tarificacion_excedente_service.py`
- [ ] T048 [P] [US4] Crear test de servicio (marker: service, AAA) de **no duplicación**: con factura previa de ese `id_cliente`+`periodo`+`tipo='excedente_api'`, el corte **no emite una segunda** (RN-APM-012), en `backend/apps/partners/tests/services/test_no_duplicacion_factura.py`
- [ ] T049 [P] [US4] Crear test de servicio (marker: service, AAA) de los **reintentos persistidos**: fallos sucesivos programan 1 h → 6 h → 24 h actualizando `reintentos` y `resultado_ultimo_reintento`; agotados → pendiente de emisión manual + alerta a Administrador y Desarrollador de APIs. **Se simula adelantando el reloj, no esperando**, en `backend/apps/partners/tests/services/test_reintentos_facturacion.py`
- [ ] T050 [P] [US4] Crear test de servicio (marker: service, AAA) del centinela de tarifa: `precio_excedente_llamada = -1.0` → **alerta y NO emite factura de importe cero** (§ 15 D1), en `backend/apps/partners/tests/services/test_tarifa_sin_configurar.py`
- [ ] T051 [P] [US4] Crear test de servicio (marker: service, AAA) que verifique que una factura **en disputa** queda excluida del cobro automático (RN-APM-016) en `backend/apps/partners/tests/services/test_factura_en_disputa.py`
- [ ] T052 [P] [US4] Crear test de servicio (marker: service, AAA) de **determinismo** (RNF-APM-001): dos ejecuciones del corte sobre el mismo período y los mismos datos producen el mismo importe, en `backend/apps/partners/tests/services/test_corte_determinista.py`

### Implementation for User Story 4

- [ ] T053 [US4] Implementar `TarificacionExcedenteService` (agregación del período, separación incluido/excedente, cálculo del importe, verificación de no duplicación, y emisión vía `FacturaRepository` de Suscripciones) en `backend/apps/partners/services/tarificacion_excedente_service.py`
- [ ] T054 [US4] Implementar la política de reintentos **por estado persistido** —nunca con `sleep`, para que sobreviva a un reinicio del contenedor— en `backend/apps/partners/services/tarificacion_excedente_service.py`, siguiendo el patrón de `backend/apps/suscripciones/jobs/dunning_job.py`
- [ ] T055 [US4] Implementar el job de corte, que en cada ejecución procesa los cortes pendientes **y los reintentos ya vencidos**, en `backend/apps/partners/jobs/facturacion_excedente_job.py`
- [ ] T056 [US4] Implementar el comando de gestión (ejecución **horaria**, para que los escalones de 1 h/6 h/24 h se respeten) en `backend/apps/partners/management/commands/run_facturacion_excedente_job.py`
- [ ] T057 [US4] Implementar las alertas de excepción de facturación al Administrador y al Desarrollador de APIs en `backend/apps/partners/services/tarificacion_excedente_service.py`, reutilizando el mecanismo de notificación existente — **verificar cuál antes de implementar**

**Checkpoint**: US4 operativa — el departamento ya genera ingreso exigible.

**US4 Gate**:
- [ ] T058 [US4] Marcar CA-APM-011–014 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: cierre de calidad, seguridad y verificación real.

- [ ] T059 [P] Crear test de servicio (marker: service, AAA) que verifique que **`Fact_APIIntegracion` y `Fact_LogLlamadaAPI` son append-only**: ningún repositorio del módulo expone UPDATE ni DELETE (RNF-APM-005), en `backend/apps/partners/tests/services/test_append_only_consumo.py`
- [ ] T060 [P] Crear test de API (marker: api, AAA) que verifique la **separación de superficies**: un JWT humano no autentica en `/datos/*` y una credencial de API no autentica en `/logs-api`, en `backend/apps/partners/tests/api/test_separacion_superficies.py`
- [ ] T061 [P] Añadir auditoría estructurada de los intentos de emisión y su resultado en `backend/apps/partners/services/tarificacion_excedente_service.py` (RNF-APM-006)
- [ ] T062 **Crear `database/verifica_monitoreo_api.py`** contra Pinot real con las 6 comprobaciones de `quickstart.md` §5: exactitud de `SUM(llamadas)`, separación de entornos, regla contable del 429, centinela de tarifa, mes vacío y `LIMIT` explícito
- [ ] T063 Medir p95 de `GET /datos/accidentes` **con y sin** el registro activo, para aislar su coste y el de bcrypt (RNF-APM-002), y registrar la evidencia en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md`
- [ ] T064 Medir la capacidad de escritura sostenida (RNF-APM-003) y registrarla en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/traceability.md`
- [ ] T065 Verificar cobertura ≥ 80 % con `pytest --cov=apps/partners/services` desde `backend/` (RNF-APM-008)
- [ ] T066 **Ejecutar `python database/verifica_monitoreo_api.py` contra Pinot real** — criterio de salida **obligatorio**, no sustituible por `pytest`: este módulo vive de agregaciones y el doble de `conftest.py` no las reproduce (`decisiones-pendientes.md` #18)
- [ ] T067 Ejecutar la suite completa desde `backend/` (`python -m pytest -q`, config en `backend/pytest.ini`) y confirmar que no hay regresiones sobre la línea base de **1042 passed, 2 skipped**
- [ ] T068 Limpiar los datos de prueba con `python database/limpia_datos_prueba.py` y confirmar que los datos reales siguen intactos
- [ ] T069 Actualizar el estado del módulo en `.specify/docs/architecture/module-map.md` §4 y cerrar los ítems de `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/checklists/requirements.md`
- [ ] T070 Cambiar `.specify/feature.json` a `…/api-monitoring-and-billing/frontend` para abrir la capa de Interaction Capability

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
