# Tasks: Gestión de Acceso de Partners

**Input**: Design documents from `specs/003-operational/Partners-API/partner-access-management/backend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/partner-access-management.openapi.yaml`, `quickstart.md`

**Tests**: Incluidos por requerimiento del proyecto (`.specify/docs/architecture/testing.md`); markers `unit`/`repository`/`service`/`api` y patrón AAA.

**Organization**: Tareas agrupadas por historia de usuario (US1–US3).

> **Capas:** este archivo es autoridad de **dominio/API**. La capa Interaction Capability vive en [`../frontend/`](../frontend/).

> **⚠️ Depende de #07 y #08 implementados.** El reemplazo de credencial reutiliza el servicio de emisión de #07, y la mora nace de las facturas de #08. Las fases 1–2 pueden adelantarse.

> **✅ Sin cambios de esquema.** Es el único de los tres módulos que se implementa entero sobre tablas y campos existentes. **No hay tareas de migración aquí.**

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US3`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup

**Purpose**: Preparar el módulo y validar el contrato antes de escribir código.

- [X] T001 Crear los archivos base del módulo en `backend/apps/partners/views/` y `backend/apps/partners/services/` (la app `partners/` y sus repositorios ya existen desde #07)
- [X] T002 [P] Añadir fixtures de partner suspendido y de credenciales en distintos estados (activa, revocada, expirada) en `backend/conftest.py`
- [X] T003 Validar el contrato OpenAPI como gate: sintaxis, refs, que **todos los endpoints usen `bearerAuth`** y que **`client_secret` solo aparezca en `RevocacionResponse`**, en `specs/003-operational/Partners-API/partner-access-management/backend/contracts/partner-access-management.openapi.yaml`
- [X] T004 [P] Registrar las rutas del módulo en `backend/apps/partners/views/urls.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: La lista de denegación y las lecturas de cascada — bloquean las historias.

**CRITICAL**: **T005 y T006 son el corazón de seguridad del módulo.** Sin la lista de denegación, la revocación deja una ventana de 5–15 s en la que una credencial comprometida sigue sirviendo datos.

- [X] T005 Implementar `DenylistCredenciales` (añadir `client_id` con TTL configurable de 60 s, consulta, y **retirada** para la reactivación) sobre el caché de Django, llaveada por `idcredencial` — `client_id` **no es columna** de `Dim_CredencialAPI`, se deriva como `tsi-p{idpartner}-c{idcredencial}` (`secreto_service.generar_client_id`) — en `backend/apps/partners/services/denylist_credenciales.py` — documentar en el docstring que es un **puente hasta que Pinot ingiere**, no una fuente de verdad paralela (RN-PAC-012)
- [X] T006 **Integrar la consulta de la lista de denegación en `CredencialAPIAuthentication` de #08**, en `backend/apps/partners/authentication.py` — **debe consultarse ANTES de cualquier caché positiva de bcrypt**: en el orden inverso, la caché de rendimiento *alarga* la ventana de exposición en vez de cerrarla (`research.md` Decision 2)
- [X] T007 [P] Crear test unitario (marker: unit, AAA) de `denylist_credenciales.py`: alta, consulta, expiración por TTL, en `backend/apps/partners/tests/unit/test_denylist_credenciales.py`
- [X] T008 [P] Crear test unitario (marker: unit, AAA) que **fije el contrato de orden**: una credencial en la lista de denegación se rechaza **aunque** esté cacheada como válida, en `backend/apps/partners/tests/unit/test_orden_denylist_cache.py` — **la caché positiva de bcrypt de #08 Decision 2 no llegó a implementarse**, así que hoy el test se escribe contra un doble de caché; existe para que, el día que se añada, no se coloque delante de la lista y **alargue** la ventana en vez de cerrarla
- [X] T009 Añadir a `HistorialAccesoRepository` las lecturas que necesita este módulo: último evento de suspensión de un partner, y filas `desactivacion_por_cascada` asociadas, en `backend/core/repositories/partners/historial_acceso_repository.py`
- [X] T010 [P] Crear test de repositorio (marker: repository, AAA) de las lecturas de cascada en `backend/apps/partners/tests/repositories/test_historial_cascada.py`
- [X] T011 Añadir el permiso `EsAdministrador` a los endpoints de suspensión y reactivación, y la comprobación de propiedad para la revocación, en `backend/apps/partners/permissions.py`
- [X] T012 [P] Crear test unitario (marker: unit, AAA) de los permisos del módulo: solo Administrador suspende/reactiva; el partner solo revoca lo suyo, en `backend/apps/partners/tests/unit/test_permisos_acceso.py`

**Checkpoint**: la ventana de exposición está cerrada y la cascada es reconstruible.

---

## Phase 3: User Story 1 — Revocar una credencial comprometida (Priority: P1) 🎯 MVP

**Goal**: RF-PAC-001 y RF-PAC-002 — respuesta inmediata ante un incidente de seguridad, con reemplazo en el mismo acto.

**Independent Test**: un partner con tres credenciales revoca una, recibe el reemplazo con el mismo nombre y su secreto, las otras dos siguen operando, y la revocada **deja de servir de inmediato** sin esperar a la ingesta.

**Measurable Criteria**: CA-PAC-001, CA-PAC-002, CA-PAC-003, CA-PAC-004, CA-PAC-005, CA-PAC-015; escenarios A–E.

### Tests for User Story 1

- [X] T013 [P] [US1] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/credenciales/{id}/revocar` en `backend/apps/partners/tests/api/test_revocar_credencial_contract.py`
- [X] T014 [P] [US1] 🎯 Crear test de API (marker: api, AAA) que verifique que la credencial revocada **deja de servir inmediatamente**, **sin ninguna espera ni `sleep`** — si solo pasa con espera, la ventana de exposición sigue abierta (RNF-PAC-001), en `backend/apps/partners/tests/api/test_revocacion_inmediata.py`
- [X] T015 [P] [US1] Crear test de API (marker: api, AAA) de los rechazos: credencial ajena → 403, credencial ya inactiva → 409 **sin segunda entrada en bitácora**, `motivo` vacío → 400, en `backend/apps/partners/tests/api/test_revocar_rechazos.py`
- [X] T016 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique que el reemplazo lleva **el mismo entorno y el mismo nombre**, y que la unicidad de nombre **no da colisión falsa** con la recién revocada (`research.md` Decision 4), en `backend/apps/partners/tests/services/test_reemplazo_mismo_nombre.py`
- [X] T017 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique que **las demás credenciales del partner no se tocan** (RF-O55.2) en `backend/apps/partners/tests/services/test_revocacion_no_afecta_otras.py`
- [X] T018 [P] [US1] Crear test de API (marker: api, AAA) que verifique que **una credencial de API no puede revocar** (solo JWT): evita darle al atacante la herramienta de sabotaje, en `backend/apps/partners/tests/api/test_revocar_solo_jwt.py`

### Implementation for User Story 1

- [X] T019 [US1] Implementar `RevocarCredencialService`: validaciones, marcado `activo=false`, alta en la lista de denegación, y **reemplazo invocando el servicio de emisión de #07** (no duplicar la generación de secretos), en `backend/apps/partners/services/revocar_credencial_service.py`
- [X] T020 [US1] Registrar el evento `revocacion_credencial` con el `idcredencial` exacto, `ejecutado_por="Partner"`, el motivo y `estado_anterior = estado_nuevo = "Activo"` (revocar una credencial **no** cambia el estado del partner; el vocabulario de esos campos está fijado en `data-model.md`), en `backend/apps/partners/services/revocar_credencial_service.py`
- [X] T021 [US1] Implementar `RevocarCredencialView` con control de propiedad e `Idempotency-Key`, en `backend/apps/partners/views/revocacion_views.py` — debe usar el **TTL corto de `idempotency.TTL_EMISION_SECONDS` (60 s)**, no el general de 300 s: la respuesta lleva el secreto del reemplazo y #07 separó ese TTL precisamente para no dejar secretos cacheados cinco minutos

**Checkpoint**: US1 operativa — el partner puede responder a un incidente sin esperar a nadie.

**US1 Gate**:
- [X] T022 [US1] Marcar CA-PAC-001–005 y CA-PAC-015 como cubiertos en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`

---

## Phase 4: User Story 2 — Suspender y reactivar el acceso (Priority: P1)

**Goal**: RF-PAC-004, RF-PAC-005 y RF-PAC-006 — la cascada y su inversa selectiva, que es el corazón funcional del módulo.

**Independent Test**: un partner con credenciales A y B activas y C revocada por él mismo es suspendido (las tres quedan inactivas) y luego reactivado: **A y B vuelven, C no**.

**Measurable Criteria**: CA-PAC-008, CA-PAC-009, CA-PAC-010, CA-PAC-011; escenarios H–L.

### Tests for User Story 2

- [X] T023 [P] [US2] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/suspender` en `backend/apps/partners/tests/api/test_suspender_contract.py`
- [X] T024 [P] [US2] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/reactivar` en `backend/apps/partners/tests/api/test_reactivar_contract.py`
- [X] T025 [P] [US2] Crear test de servicio (marker: service, AAA) de la **cascada directa**: se desactivan **todas** las credenciales de ambos entornos y se escribe **una fila `desactivacion_por_cascada` por cada una**, en `backend/apps/partners/tests/services/test_cascada_suspension.py`
- [X] T026 [P] [US2] 🎯 Crear test de servicio (marker: service, AAA) de la **reactivación selectiva**: partner con A y B activas y C revocada previamente → al reactivar vuelven **A y B**, y **C permanece inactiva**. Es el test más importante del módulo: si C revive, se ha resucitado una credencial comprometida, en `backend/apps/partners/tests/services/test_reactivacion_selectiva.py`
- [X] T027 [P] [US2] 🎯 Crear test de servicio (marker: service, AAA) que verifique que **el sistema no reactiva solo**: tras regularizar el pago, el partner **sigue suspendido** (RN-PAC-009). Protege de un refactor del tipo «si ya pagó, ¿por qué no reactivarlo?», que además chocaría con RN-SUSF-011 de Suscripciones, en `backend/apps/partners/tests/services/test_no_reactiva_solo.py`
- [X] T028 [P] [US2] Crear test de API (marker: api, AAA) de los rechazos: suspender sin motivo → 400, reactivar un partner no suspendido → 409 **sin entrada en bitácora**, suspender uno ya suspendido → 409, rol distinto de Administrador → 403, en `backend/apps/partners/tests/api/test_suspension_rechazos.py`

### Implementation for User Story 2

- [X] T029 [US2] Implementar `SuspenderPartnerService`: lectura previa de credenciales activas, cascada con una fila de bitácora por credencial, y actualización de `Dim_Partner` con su snapshot, en `backend/apps/partners/services/suspender_partner_service.py`
- [X] T030 [US2] Implementar `ReactivarPartnerService`: lectura de las filas `desactivacion_por_cascada` del último evento de suspensión y restitución **solo** de ese conjunto, en `backend/apps/partners/services/reactivar_partner_service.py`
- [X] T031 [US2] Añadir al reactivar la limpieza del snapshot de suspensión (`fecha_suspension` y `motivo_suspension` al centinela `""`, nunca `NULL`) en `backend/apps/partners/services/reactivar_partner_service.py`
- [X] T032 [US2] Implementar `SuspenderPartnerView` y `ReactivarPartnerView` con el permiso de Administrador, exponiendo el desglose `credenciales_restituidas` / `credenciales_no_restituidas`, en `backend/apps/partners/views/suspension_views.py`

- [X] T057 [US2] 🎯 Hacer que la **cascada alimente la lista de denegación** con cada credencial que desactiva, y que la reactivación **las retire** al restituirlas (§ 15 D4), en `backend/apps/partners/services/suspender_partner_service.py` y `reactivar_partner_service.py` — sin esto, un partner suspendido sigue consumiendo 5–15 s con **todas** sus credenciales, una fuga mayor que la que se cierra al revocar; sin la retirada, el reactivado seguiría rechazado hasta que caduque el TTL
- [X] T058 [P] [US2] Crear test de API (marker: api, AAA) del escenario Q: tras suspender, las tres credenciales del partner dejan de servir **sin ninguna espera**, y tras reactivar vuelven a servir también sin espera, en `backend/apps/partners/tests/api/test_suspension_inmediata.py`

**Checkpoint**: US2 operativa — el acceso se corta y se restituye sin resucitar lo comprometido, y el corte es inmediato en los dos sentidos.

**US2 Gate**:
- [X] T033 [US2] Marcar CA-PAC-008–011 y CA-PAC-017 como cubiertos en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`

---

## Phase 5: User Story 3 — Avisar y suspender por mora (Priority: P2)

**Goal**: RF-PAC-003 y RF-PAC-007 — el sistema avisa dos veces antes de actuar, y suspende solo si el partner no reacciona.

**Independent Test**: un partner con factura de excedente impagada recibe aviso en T-10 y T-5 sin duplicados; si paga entre ambos, el segundo nunca se envía; si no paga, se le suspende al superar el límite.

**Measurable Criteria**: CA-PAC-006, CA-PAC-007, CA-PAC-012; escenarios F, G, M.

### Tests for User Story 3

- [X] T034 [P] [US3] Crear test de servicio (marker: service, AAA) de los avisos: se envían en T-10 y T-5, y **ninguno se duplica** al reejecutar el job en el mismo ciclo (RN-PAC-006), en `backend/apps/partners/tests/services/test_avisos_mora.py`
- [X] T035 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que los avisos **no cambian el estado del partner** (`estado_anterior` = `estado_nuevo`) en `backend/apps/partners/tests/services/test_aviso_no_cambia_estado.py`
- [X] T036 [P] [US3] Crear test de servicio (marker: service, AAA) de la **regularización entre avisos**: si el partner paga tras T-10, el aviso T-5 **nunca se envía** y el ciclo se cierra sin suspensión — debe funcionar **sin lógica de cancelación** (RN-PAC-007), en `backend/apps/partners/tests/services/test_regularizacion_entre_avisos.py`
- [X] T037 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que una **factura en disputa no cuenta como mora** (RN-PAC-015) en `backend/apps/partners/tests/services/test_disputa_no_genera_mora.py`
- [X] T038 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que **solo cuentan las facturas `tipo='excedente_api'`**: una factura de suscripción impagada no suspende al partner aquí (§ 15 D2), en `backend/apps/partners/tests/services/test_solo_excedente_genera_mora.py`

### Implementation for User Story 3

- [X] T059 [US3] **Añadir a `FacturaRepository` la lectura que la mora necesita y hoy no existe**: facturas `tipo='excedente_api'` con `estado_pago='Pendiente'` y `fecha_vencimiento` pasada, para un conjunto de `id_cliente`, en `backend/core/repositories/suscripciones/factura_repository.py` — hoy solo hay `list_by_cliente(limit=20)` y `find_by_suscripcion_periodo`, y **ese `limit=20` no sirve** para un job que barre el padrón (§ 15 D3)
- [X] T060 [P] [US3] Crear test de repositorio (marker: repository, AAA) de esa lectura: encuentra la `Pendiente` vencida, **descarta la `Fallida`** (es de Suscripciones), la `Pagada` y la `En disputa`, en `backend/apps/partners/tests/repositories/test_facturas_vencidas_impagadas.py`
- [X] T039 [US3] Implementar `EvaluacionMoraService`: resolver `Dim_Partner.idcliente → Fact_Factura.id_cliente` (**`Fact_Factura` NO tiene `idpartner`**: consultarla por esa columna devolvería cero partners en mora **en silencio**, § 15 D3), calcular los días desde `fecha_vencimiento` de la factura vencida impagada **más antigua**, y decidir (avisar T-10, avisar T-5, suspender), en `backend/apps/partners/services/evaluacion_mora_service.py`
- [X] T040 [US3] Añadir la comprobación de no duplicación consultando la bitácora por (`idpartner`, `aviso_previo_suspension`, `motivo`) dentro del ciclo de mora vigente — **el ciclo lo delimita la factura vencida impagada más antigua**: si esa se paga y queda otra vencida, empieza un ciclo nuevo y los avisos cuentan desde cero, porque es deuda distinta (§ 15 D3) — en `backend/apps/partners/services/evaluacion_mora_service.py`
- [X] T041 [US3] Implementar el job diario que evalúa la mora y dispara avisos o suspensión (reutilizando `SuspenderPartnerService`) en `backend/apps/partners/jobs/evaluacion_mora_job.py`
- [X] T042 [US3] Implementar el comando de gestión que dispara el job en `backend/apps/partners/management/commands/run_evaluacion_mora_job.py`
- [X] T043 [US3] Hacer configurables los momentos de aviso (T-10, T-5) y el límite de mora (15 días) en `backend/config/settings.py`, sin constantes en el servicio (RNF-PAC-005)

**Checkpoint**: US3 operativa — nadie se lleva una suspensión por sorpresa.

**US3 Gate**:
- [X] T044 [US3] Marcar CA-PAC-006, CA-PAC-007, CA-PAC-012 y CA-PAC-018 como cubiertos en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: consulta de estado, verificación real y cierre del departamento.

- [X] T045 [P] Implementar `EstadoAccesoView` y su servicio de lectura (estado, mora derivada, avisos enviados, credenciales e historial) en `backend/apps/partners/views/estado_acceso_views.py`
- [X] T046 [P] Crear test de API (marker: api, AAA) del estado de acceso: el partner **suspendido** puede consultar el suyo (200), consultar el de otro → 403 (RN-PAC-016), en `backend/apps/partners/tests/api/test_estado_acceso_contract.py`
- [X] T047 [P] Crear test de servicio (marker: service, AAA) que verifique que la bitácora es **append-only**: ninguna operación del módulo ejecuta UPDATE ni DELETE sobre `Fact_HistorialAccesoPartner` (RN-PAC-013), en `backend/apps/partners/tests/services/test_bitacora_append_only.py`
- [X] T048 [P] Crear test de API (marker: api, AAA) de la **frontera con Suscripciones** (§ 15 D2): un cliente con suscripción suspendida y partner activo recibe **403** al consumir la API de #08, y reactivar la suscripción **no** reactiva al partner suspendido por su propia mora, en `backend/apps/partners/tests/api/test_frontera_suscripcion.py`
- [X] T061 [P] Implementar `ColaAccesoView` (`GET /partners/cola-acceso`, solo Administrador): partners suspendidos y en ciclo de mora con avisos enviados, con `dias_mora` y `ultimo_aviso` **derivados** —no hay columna «en mora» y no debe crearse (RN-PAC-012)— en `backend/apps/partners/views/estado_acceso_views.py`
- [X] T062 [P] Crear test de API (marker: api, AAA) del escenario P: la cola devuelve suspendidos y avisados con sus días de mora; un partner que la consulta recibe **403**, en `backend/apps/partners/tests/api/test_cola_acceso_contract.py`
- [X] T049 **Crear `database/verifica_acceso_partners.py`** contra Pinot real con las 9 comprobaciones de `quickstart.md` §5: sin credenciales activas tras suspender, nº de filas de cascada = nº de activas previas, la revocada sigue inactiva tras reactivar, `Dim_Partner` y credenciales sin contradicción, snapshot al centinela, y revocación efectiva antes de la ingesta
- [X] T050 Medir el tiempo desde que se acepta la revocación hasta que la credencial deja de servir (RNF-PAC-001, p95 ≤ 2 s) **sin esperas artificiales**, y registrar la evidencia en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`
- [X] T051 Verificar cobertura ≥ 80 % con `pytest --cov=apps/partners/services` desde `backend/` (RNF-PAC-006)
- [X] T052 **Ejecutar `python database/verifica_acceso_partners.py` contra Pinot real** — criterio de salida **obligatorio**: la cascada y la reactivación tocan estado en tres tablas a la vez y el doble de `conftest.py` no lo reproduce (`decisiones-pendientes.md` #18) — **hecho 2026-08-10: 10/10 contra Pinot real.** La cascada, la reactivación selectiva y el camino de la mora se comportan igual en el sistema real que con el doble. Incluye el desfase de milisegundo que había roto la primera versión de la lectura.
- [X] T053 Ejecutar la suite completa desde `backend/` (`python -m pytest -q`, config en `backend/pytest.ini`) y confirmar que no hay regresiones sobre la línea base de **1447 passed** (la que dejó #08 el 2026-08-09; el 1042 que figuraba aquí era anterior a #07 y #08)
- [X] T054 Limpiar los datos de prueba con `python database/limpia_datos_prueba.py` y confirmar que los datos reales siguen intactos — **hecho**: las 7 tablas a 0 y los datos reales intactos (`Fact_Historial_Ticket` 9, `Fact_Reclamo` 8). `Dim_VersionContratoAPI` resembrada, que la limpieza purga por diseño.
- [X] T063 Registrar en `traceability.md` la cobertura de **CA-PAC-016, CA-PAC-017 y CA-PAC-018** (los tres criterios que añadió el análisis previo a la implementación)
- [X] T055 Actualizar el estado del módulo en `.specify/docs/architecture/module-map.md` §4 y cerrar los ítems de `specs/003-operational/Partners-API/partner-access-management/backend/checklists/requirements.md`
- [X] T056 Cambiar `.specify/feature.json` a `…/partner-access-management/frontend` para abrir la capa de Interaction Capability y cerrar el backend del departamento

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
   └─► Phase 2 (Foundational)   ◄── T005+T006: la lista de denegación y su ORDEN
          ├─► Phase 3 (US1)  🎯 MVP    revocación con reemplazo
          ├─► Phase 4 (US2)            suspensión y reactivación selectiva
          └─► Phase 5 (US3)            mora: avisos y suspensión automática
                 └─► Phase 6 (Polish)
```

### User Story Dependencies

| Historia | Depende de | Motivo |
|---|---|---|
| US1 | Phase 2 + **#07 implementado** | El reemplazo reutiliza su servicio de emisión |
| US2 | Phase 2 | Independiente de US1: la cascada no necesita revocaciones previas… |
| US3 | US2 + **#08 implementado** | …aunque el **escenario I** de US2 sí necesita una credencial revocada, que produce US1. US3 reutiliza `SuspenderPartnerService` de US2 y necesita facturas de excedente |

> **Matiz:** US2 es implementable sin US1, pero su test más importante (reactivación selectiva, T026) necesita una credencial **revocada por el partner** para ser significativo. Si se implementan en paralelo, ese test se cierra al final.

### Parallel Opportunities

- **Phase 2**: T007, T008, T010 y T012 en paralelo (T005/T006 y T009/T011 son sus dependencias).
- **US1 y US2 en paralelo** tras la fase fundacional — son los dos frentes principales.
- Dentro de cada historia, **todos los tests marcados [P]** pueden escribirse a la vez.
- **Phase 6**: T045–T048 en paralelo.

### Parallel Example: tras la Phase 2

```bash
# Dos frentes independientes:
Phase 3 (US1)  revocación + reemplazo
Phase 4 (US2)  cascada + reactivación selectiva
# (cerrar T026 cuando US1 exista, para que el test sea significativo)
```

---

## Implementation Strategy

### MVP First (User Story 1)

US1 entrega la capacidad más urgente del módulo: **un partner con una credencial comprometida puede cortarla ya mismo y seguir operando**. Es lo único de aquí que responde a un incidente en curso.

### Incremental Delivery

1. **Phase 1 + 2** → ventana de exposición cerrada y cascada reconstruible.
2. **+ US1** → 🎯 MVP: respuesta inmediata ante credencial comprometida.
3. **+ US2** → el acceso se corta y se restituye **sin resucitar lo comprometido**.
4. **+ US3** → la mora avisa dos veces antes de suspender.
5. **+ Phase 6** → verificación real, cierre del backend del departamento.

---

## Notes

- **T006 tiene un orden crítico**: la lista de denegación debe consultarse **antes** de cualquier caché positiva de bcrypt de #08. En el orden inverso, la optimización de rendimiento **alarga** la ventana de exposición en lugar de cerrarla.
- **T014 y T050 no admiten `sleep`.** Si la revocación solo se verifica esperando, lo que se está midiendo es la ingesta de Pinot y la ventana sigue abierta.
- **T026 es el test más importante de los tres módulos del departamento.** Si la credencial revocada revive al reactivar, se ha resucitado una credencial comprometida.
- **T027 protege una regla contraintuitiva**: tras pagar, el partner **sigue suspendido**. Reactivar es siempre una decisión humana (RN-PAC-009), y automatizarlo chocaría con RN-SUSF-011 de Suscripciones.
- **T038 delimita la frontera**: solo las facturas de excedente suspenden aquí. La suscripción impagada la gestiona Suscripciones (§ 15 D2).
- **Ninguna consulta usa `IS NULL`**: las guardas comparan contra centinelas (`idcredencial = -1`, `motivo_suspension = ''`).
- Este módulo **no añade nada al esquema**: no hay tareas de migración.

### Tareas añadidas por `/speckit-analyze` (2026-08-10, antes de implementar)

| Tarea | Hallazgo que cierra |
|---|---|
| **T057, T058** | La suspensión no cerraba su ventana de ingesta: el partner suspendido seguía consumiendo 5–15 s con **todas** sus credenciales (§ 15 D4) |
| **T059, T060** | La mora no tenía camino de datos: `Fact_Factura` **no tiene `idpartner`**, y no existía ninguna lectura de vencidas impagadas (§ 15 D3) |
| **T061, T062** | RF-PAC-009 pedía **dos** lecturas y solo estaba cubierta la del partner: faltaba la cola de trabajo del Administrador |
| **T063** | Registrar los tres CA nuevos |

Total: **63 tareas** (56 originales + 7).

### ✅ Verificación contra Pinot real — completada 2026-08-10

`database/verifica_acceso_partners.py`: **10/10**. Lo que un mock no puede probar:

| Comprobación | Resultado |
|---|---|
| Tras suspender, ninguna credencial queda activa | ✅ |
| Nº de filas de cascada = nº de credenciales que estaban activas | ✅ `[960001, 960002]` |
| La credencial **revocada** no genera fila de cascada | ✅ por eso no revive |
| Tras reactivar, la revocada **sigue** inactiva | ✅ |
| Vuelven exactamente A y B | ✅ |
| El snapshot vuelve al centinela `''`, no a NULL | ✅ |
| La mora se resuelve por `id_cliente` y encuentra al moroso | ✅ |
| Una factura `Fallida` **no** cuenta como mora aquí | ✅ |
| Los seis `tipo_cambio` se persisten con su texto exacto | ✅ |

El escenario incluye a propósito el **desfase de milisegundo** entre las filas
de cascada y el evento de suspensión — el que rompió la primera versión de
`credenciales_de_la_ultima_cascada()`.

Limpieza (T054): las 7 tablas a **0**, datos reales intactos
(`Fact_Historial_Ticket` 9, `Fact_Reclamo` 8) y `Dim_VersionContratoAPI`
resembrada.

