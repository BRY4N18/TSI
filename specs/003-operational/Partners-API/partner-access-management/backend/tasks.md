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

- [ ] T001 Crear los archivos base del módulo en `backend/apps/partners/views/` y `backend/apps/partners/services/` (la app `partners/` y sus repositorios ya existen desde #07)
- [ ] T002 [P] Añadir fixtures de partner suspendido y de credenciales en distintos estados (activa, revocada, expirada) en `backend/conftest.py`
- [ ] T003 Validar el contrato OpenAPI como gate: sintaxis, refs, que **todos los endpoints usen `bearerAuth`** y que **`client_secret` solo aparezca en `RevocacionResponse`**, en `specs/003-operational/Partners-API/partner-access-management/backend/contracts/partner-access-management.openapi.yaml`
- [ ] T004 [P] Registrar las rutas del módulo en `backend/apps/partners/views/urls.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: La lista de denegación y las lecturas de cascada — bloquean las historias.

**CRITICAL**: **T005 y T006 son el corazón de seguridad del módulo.** Sin la lista de denegación, la revocación deja una ventana de 5–15 s en la que una credencial comprometida sigue sirviendo datos.

- [ ] T005 Implementar `DenylistCredenciales` (añadir `client_id` con TTL configurable de 60 s, y consulta) sobre el caché de Django, en `backend/apps/partners/services/denylist_credenciales.py` — documentar en el docstring que es un **puente hasta que Pinot ingiere**, no una fuente de verdad paralela (RN-PAC-012)
- [ ] T006 **Integrar la consulta de la lista de denegación en `CredencialAPIAuthentication` de #08**, en `backend/apps/partners/authentication.py` — **debe consultarse ANTES de cualquier caché positiva de bcrypt**: en el orden inverso, la caché de rendimiento *alarga* la ventana de exposición en vez de cerrarla (`research.md` Decision 2)
- [ ] T007 [P] Crear test unitario (marker: unit, AAA) de `denylist_credenciales.py`: alta, consulta, expiración por TTL, en `backend/apps/partners/tests/unit/test_denylist_credenciales.py`
- [ ] T008 [P] Crear test unitario (marker: unit, AAA) que verifique el **orden**: una credencial en la lista de denegación se rechaza **aunque** esté cacheada como válida, en `backend/apps/partners/tests/unit/test_orden_denylist_cache.py`
- [ ] T009 Añadir a `HistorialAccesoRepository` las lecturas que necesita este módulo: último evento de suspensión de un partner, y filas `desactivacion_por_cascada` asociadas, en `backend/core/repositories/partners/historial_acceso_repository.py`
- [ ] T010 [P] Crear test de repositorio (marker: repository, AAA) de las lecturas de cascada en `backend/apps/partners/tests/repositories/test_historial_cascada.py`
- [ ] T011 Añadir el permiso `EsAdministrador` a los endpoints de suspensión y reactivación, y la comprobación de propiedad para la revocación, en `backend/apps/partners/permissions.py`
- [ ] T012 [P] Crear test unitario (marker: unit, AAA) de los permisos del módulo: solo Administrador suspende/reactiva; el partner solo revoca lo suyo, en `backend/apps/partners/tests/unit/test_permisos_acceso.py`

**Checkpoint**: la ventana de exposición está cerrada y la cascada es reconstruible.

---

## Phase 3: User Story 1 — Revocar una credencial comprometida (Priority: P1) 🎯 MVP

**Goal**: RF-PAC-001 y RF-PAC-002 — respuesta inmediata ante un incidente de seguridad, con reemplazo en el mismo acto.

**Independent Test**: un partner con tres credenciales revoca una, recibe el reemplazo con el mismo nombre y su secreto, las otras dos siguen operando, y la revocada **deja de servir de inmediato** sin esperar a la ingesta.

**Measurable Criteria**: CA-PAC-001, CA-PAC-002, CA-PAC-003, CA-PAC-004, CA-PAC-005, CA-PAC-015; escenarios A–E.

### Tests for User Story 1

- [ ] T013 [P] [US1] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/credenciales/{id}/revocar` en `backend/apps/partners/tests/api/test_revocar_credencial_contract.py`
- [ ] T014 [P] [US1] 🎯 Crear test de API (marker: api, AAA) que verifique que la credencial revocada **deja de servir inmediatamente**, **sin ninguna espera ni `sleep`** — si solo pasa con espera, la ventana de exposición sigue abierta (RNF-PAC-001), en `backend/apps/partners/tests/api/test_revocacion_inmediata.py`
- [ ] T015 [P] [US1] Crear test de API (marker: api, AAA) de los rechazos: credencial ajena → 403, credencial ya inactiva → 409 **sin segunda entrada en bitácora**, `motivo` vacío → 400, en `backend/apps/partners/tests/api/test_revocar_rechazos.py`
- [ ] T016 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique que el reemplazo lleva **el mismo entorno y el mismo nombre**, y que la unicidad de nombre **no da colisión falsa** con la recién revocada (`research.md` Decision 4), en `backend/apps/partners/tests/services/test_reemplazo_mismo_nombre.py`
- [ ] T017 [P] [US1] Crear test de servicio (marker: service, AAA) que verifique que **las demás credenciales del partner no se tocan** (RF-O55.2) en `backend/apps/partners/tests/services/test_revocacion_no_afecta_otras.py`
- [ ] T018 [P] [US1] Crear test de API (marker: api, AAA) que verifique que **una credencial de API no puede revocar** (solo JWT): evita darle al atacante la herramienta de sabotaje, en `backend/apps/partners/tests/api/test_revocar_solo_jwt.py`

### Implementation for User Story 1

- [ ] T019 [US1] Implementar `RevocarCredencialService`: validaciones, marcado `activo=false`, alta en la lista de denegación, y **reemplazo invocando el servicio de emisión de #07** (no duplicar la generación de secretos), en `backend/apps/partners/services/revocar_credencial_service.py`
- [ ] T020 [US1] Registrar el evento `revocacion_credencial` con el `idcredencial` exacto, `ejecutado_por="Partner"` y el motivo, en `backend/apps/partners/services/revocar_credencial_service.py`
- [ ] T021 [US1] Implementar `RevocarCredencialView` con control de propiedad e `Idempotency-Key`, en `backend/apps/partners/views/revocacion_views.py`

**Checkpoint**: US1 operativa — el partner puede responder a un incidente sin esperar a nadie.

**US1 Gate**:
- [ ] T022 [US1] Marcar CA-PAC-001–005 y CA-PAC-015 como cubiertos en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`

---

## Phase 4: User Story 2 — Suspender y reactivar el acceso (Priority: P1)

**Goal**: RF-PAC-004, RF-PAC-005 y RF-PAC-006 — la cascada y su inversa selectiva, que es el corazón funcional del módulo.

**Independent Test**: un partner con credenciales A y B activas y C revocada por él mismo es suspendido (las tres quedan inactivas) y luego reactivado: **A y B vuelven, C no**.

**Measurable Criteria**: CA-PAC-008, CA-PAC-009, CA-PAC-010, CA-PAC-011; escenarios H–L.

### Tests for User Story 2

- [ ] T023 [P] [US2] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/suspender` en `backend/apps/partners/tests/api/test_suspender_contract.py`
- [ ] T024 [P] [US2] Crear test de contrato API (marker: api, AAA) de `POST /api/v1/partners/{id}/reactivar` en `backend/apps/partners/tests/api/test_reactivar_contract.py`
- [ ] T025 [P] [US2] Crear test de servicio (marker: service, AAA) de la **cascada directa**: se desactivan **todas** las credenciales de ambos entornos y se escribe **una fila `desactivacion_por_cascada` por cada una**, en `backend/apps/partners/tests/services/test_cascada_suspension.py`
- [ ] T026 [P] [US2] 🎯 Crear test de servicio (marker: service, AAA) de la **reactivación selectiva**: partner con A y B activas y C revocada previamente → al reactivar vuelven **A y B**, y **C permanece inactiva**. Es el test más importante del módulo: si C revive, se ha resucitado una credencial comprometida, en `backend/apps/partners/tests/services/test_reactivacion_selectiva.py`
- [ ] T027 [P] [US2] 🎯 Crear test de servicio (marker: service, AAA) que verifique que **el sistema no reactiva solo**: tras regularizar el pago, el partner **sigue suspendido** (RN-PAC-009). Protege de un refactor del tipo «si ya pagó, ¿por qué no reactivarlo?», que además chocaría con RN-SUSF-011 de Suscripciones, en `backend/apps/partners/tests/services/test_no_reactiva_solo.py`
- [ ] T028 [P] [US2] Crear test de API (marker: api, AAA) de los rechazos: suspender sin motivo → 400, reactivar un partner no suspendido → 409 **sin entrada en bitácora**, suspender uno ya suspendido → 409, rol distinto de Administrador → 403, en `backend/apps/partners/tests/api/test_suspension_rechazos.py`

### Implementation for User Story 2

- [ ] T029 [US2] Implementar `SuspenderPartnerService`: lectura previa de credenciales activas, cascada con una fila de bitácora por credencial, y actualización de `Dim_Partner` con su snapshot, en `backend/apps/partners/services/suspender_partner_service.py`
- [ ] T030 [US2] Implementar `ReactivarPartnerService`: lectura de las filas `desactivacion_por_cascada` del último evento de suspensión y restitución **solo** de ese conjunto, en `backend/apps/partners/services/reactivar_partner_service.py`
- [ ] T031 [US2] Añadir al reactivar la limpieza del snapshot de suspensión (`fecha_suspension` y `motivo_suspension` al centinela `""`, nunca `NULL`) en `backend/apps/partners/services/reactivar_partner_service.py`
- [ ] T032 [US2] Implementar `SuspenderPartnerView` y `ReactivarPartnerView` con el permiso de Administrador, exponiendo el desglose `credenciales_restituidas` / `credenciales_no_restituidas`, en `backend/apps/partners/views/suspension_views.py`

**Checkpoint**: US2 operativa — el acceso se corta y se restituye sin resucitar lo comprometido.

**US2 Gate**:
- [ ] T033 [US2] Marcar CA-PAC-008–011 como cubiertos en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`

---

## Phase 5: User Story 3 — Avisar y suspender por mora (Priority: P2)

**Goal**: RF-PAC-003 y RF-PAC-007 — el sistema avisa dos veces antes de actuar, y suspende solo si el partner no reacciona.

**Independent Test**: un partner con factura de excedente impagada recibe aviso en T-10 y T-5 sin duplicados; si paga entre ambos, el segundo nunca se envía; si no paga, se le suspende al superar el límite.

**Measurable Criteria**: CA-PAC-006, CA-PAC-007, CA-PAC-012; escenarios F, G, M.

### Tests for User Story 3

- [ ] T034 [P] [US3] Crear test de servicio (marker: service, AAA) de los avisos: se envían en T-10 y T-5, y **ninguno se duplica** al reejecutar el job en el mismo ciclo (RN-PAC-006), en `backend/apps/partners/tests/services/test_avisos_mora.py`
- [ ] T035 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que los avisos **no cambian el estado del partner** (`estado_anterior` = `estado_nuevo`) en `backend/apps/partners/tests/services/test_aviso_no_cambia_estado.py`
- [ ] T036 [P] [US3] Crear test de servicio (marker: service, AAA) de la **regularización entre avisos**: si el partner paga tras T-10, el aviso T-5 **nunca se envía** y el ciclo se cierra sin suspensión — debe funcionar **sin lógica de cancelación** (RN-PAC-007), en `backend/apps/partners/tests/services/test_regularizacion_entre_avisos.py`
- [ ] T037 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que una **factura en disputa no cuenta como mora** (RN-PAC-015) en `backend/apps/partners/tests/services/test_disputa_no_genera_mora.py`
- [ ] T038 [P] [US3] Crear test de servicio (marker: service, AAA) que verifique que **solo cuentan las facturas `tipo='excedente_api'`**: una factura de suscripción impagada no suspende al partner aquí (§ 15 D2), en `backend/apps/partners/tests/services/test_solo_excedente_genera_mora.py`

### Implementation for User Story 3

- [ ] T039 [US3] Implementar `EvaluacionMoraService`: cálculo de días de mora sobre facturas `tipo='excedente_api'` impagadas, exclusión de las que están en disputa, y decisión (avisar T-10, avisar T-5, suspender), en `backend/apps/partners/services/evaluacion_mora_service.py`
- [ ] T040 [US3] Añadir la comprobación de no duplicación consultando la bitácora por (`idpartner`, `aviso_previo_suspension`, `motivo`) dentro del ciclo de mora vigente, en `backend/apps/partners/services/evaluacion_mora_service.py`
- [ ] T041 [US3] Implementar el job diario que evalúa la mora y dispara avisos o suspensión (reutilizando `SuspenderPartnerService`) en `backend/apps/partners/jobs/evaluacion_mora_job.py`
- [ ] T042 [US3] Implementar el comando de gestión que dispara el job en `backend/apps/partners/management/commands/run_evaluacion_mora_job.py`
- [ ] T043 [US3] Hacer configurables los momentos de aviso (T-10, T-5) y el límite de mora (15 días) en `backend/config/settings.py`, sin constantes en el servicio (RNF-PAC-005)

**Checkpoint**: US3 operativa — nadie se lleva una suspensión por sorpresa.

**US3 Gate**:
- [ ] T044 [US3] Marcar CA-PAC-006, CA-PAC-007 y CA-PAC-012 como cubiertos en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: consulta de estado, verificación real y cierre del departamento.

- [ ] T045 [P] Implementar `EstadoAccesoView` y su servicio de lectura (estado, mora derivada, avisos enviados, credenciales e historial) en `backend/apps/partners/views/estado_acceso_views.py`
- [ ] T046 [P] Crear test de API (marker: api, AAA) del estado de acceso: el partner **suspendido** puede consultar el suyo (200), consultar el de otro → 403 (RN-PAC-016), en `backend/apps/partners/tests/api/test_estado_acceso_contract.py`
- [ ] T047 [P] Crear test de servicio (marker: service, AAA) que verifique que la bitácora es **append-only**: ninguna operación del módulo ejecuta UPDATE ni DELETE sobre `Fact_HistorialAccesoPartner` (RN-PAC-013), en `backend/apps/partners/tests/services/test_bitacora_append_only.py`
- [ ] T048 [P] Crear test de API (marker: api, AAA) de la **frontera con Suscripciones** (§ 15 D2): un cliente con suscripción suspendida y partner activo recibe **403** al consumir la API de #08, y reactivar la suscripción **no** reactiva al partner suspendido por su propia mora, en `backend/apps/partners/tests/api/test_frontera_suscripcion.py`
- [ ] T049 **Crear `database/verifica_acceso_partners.py`** contra Pinot real con las 6 comprobaciones de `quickstart.md` §5: sin credenciales activas tras suspender, nº de filas de cascada = nº de activas previas, la revocada sigue inactiva tras reactivar, `Dim_Partner` y credenciales sin contradicción, snapshot al centinela, y revocación efectiva antes de la ingesta
- [ ] T050 Medir el tiempo desde que se acepta la revocación hasta que la credencial deja de servir (RNF-PAC-001, p95 ≤ 2 s) **sin esperas artificiales**, y registrar la evidencia en `specs/003-operational/Partners-API/partner-access-management/backend/traceability.md`
- [ ] T051 Verificar cobertura ≥ 80 % con `pytest --cov=apps/partners/services` desde `backend/` (RNF-PAC-006)
- [ ] T052 **Ejecutar `python database/verifica_acceso_partners.py` contra Pinot real** — criterio de salida **obligatorio**: la cascada y la reactivación tocan estado en tres tablas a la vez y el doble de `conftest.py` no lo reproduce (`decisiones-pendientes.md` #18)
- [ ] T053 Ejecutar la suite completa desde `backend/` (`python -m pytest -q`, config en `backend/pytest.ini`) y confirmar que no hay regresiones sobre la línea base de **1042 passed, 2 skipped**
- [ ] T054 Limpiar los datos de prueba con `python database/limpia_datos_prueba.py` y confirmar que los datos reales siguen intactos
- [ ] T055 Actualizar el estado del módulo en `.specify/docs/architecture/module-map.md` §4 y cerrar los ítems de `specs/003-operational/Partners-API/partner-access-management/backend/checklists/requirements.md`
- [ ] T056 Cambiar `.specify/feature.json` a `…/partner-access-management/frontend` para abrir la capa de Interaction Capability y cerrar el backend del departamento

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
