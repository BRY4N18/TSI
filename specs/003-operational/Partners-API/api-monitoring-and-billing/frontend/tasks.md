# Tasks: Monitoreo y Facturación de API — Frontend

**Input**: Design documents from `specs/003-operational/Partners-API/api-monitoring-and-billing/frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/*.ui-contract.md`, `quickstart.md`

**Tests**: Incluidos por requerimiento del proyecto (`.specify/docs/architecture/testing.md`). Karma + Jasmine, `*.spec.ts` junto al componente.

> **Capas:** este archivo es autoridad de **Interaction Capability**. El dominio vive en [`../backend/`](../backend/) y **no se redefine aquí**.

> **⚠️ `tsc --noEmit` NO valida plantillas de Angular.** El gate real es `ng test`. En #07 se coló cinco veces un `@else if (…; as x)` inválido que TypeScript compilaba sin quejarse.

> **⚠️ Sin Chrome en esta máquina.** `CHROME_BIN="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: Historia (`US1`–`US6`, mapean a `US-FE-1`…`US-FE-6` de `spec.md`)
- Cada descripción incluye path exacto de archivo

---

## Phase 1: Setup

**Purpose**: preparar el terreno dentro del módulo `partners/` que ya existe.

- [X] T001 Añadir los glifos que faltan (`chart-bar`, `report-money`, `refresh`, `filter`, `alert-square-rounded`) a `frontend/src/app/shared/ui/icon/tabler-icon.component.ts` — el componente solo expone los que declara, y una plantilla que pida uno inexistente renderiza vacío **sin fallar**
- [X] T002 [P] Crear `frontend/src/app/modules/partners/services/models/monitoreo.types.ts` con los tipos de las cuatro respuestas (`ConsumoPartner`, `LogLlamada`, `ReporteMensual`, `ExcepcionFacturacion`) según `data-model.md`
- [X] T003 [P] Crear `frontend/src/app/modules/partners/guards/administrador.guard.ts` — las excepciones de facturación son **solo Administrador**, y los guards de #07 no cubren ese caso (`gestorPartnersGuard` admite también a DevAPIs)
- [X] T004 Registrar las cuatro rutas nuevas en `frontend/src/app/modules/partners/partners.routes.ts` con `loadComponent` y su guard

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: la traducción de centinelas y los servicios HTTP. Bloquean todas las historias.

**CRITICAL**: **T005 es el corazón de esta capa.** Si la traducción de `null` se reparte por las plantillas, el primero que se olvide imprimirá un `0` donde el backend dijo «no aplica» — y un `0 %` afirma algo falso.

- [X] T005 Implementar el helper de centinelas en `frontend/src/app/modules/partners/services/models/monitoreo.types.ts`: `null` → `{ valor: null, leyenda }`, `0` → `{ valor: 0 }`. **Un solo sitio**, nunca en plantillas (`data-model.md` § 1)
- [X] T006 [P] Crear test unitario (AAA) del helper en `frontend/src/app/modules/partners/services/models/monitoreo.types.spec.ts`: `null` y `0` **no colapsan**; `porcentaje_consumido: null` produce «No aplica», `0` produce «0 %»
- [X] T007 Implementar `MonitoreoApiService` (métricas, logs, reporte mensual) en `frontend/src/app/modules/partners/services/monitoreo-api.service.ts`, desenvolviendo el sobre `data`/`meta` con el `ApiEnvelope` compartido
- [X] T008 [P] Crear test de servicio con `HttpTestingController` en `frontend/src/app/modules/partners/services/monitoreo-api.service.spec.ts`: URLs y query params correctos, y mapeo de 400/403/404/5xx a los estados de `consola-monitoreo.ui-contract.md`
- [X] T009 Añadir al servicio la clasificación del código HTTP (`exito` / `ritmo` / `cliente` / `plataforma`) en `frontend/src/app/modules/partners/services/models/monitoreo.types.ts` — el **429 es su propia clase**, no un 4xx más (`data-model.md` § 2)
- [X] T010 [P] Crear test unitario (AAA) de la clasificación en `frontend/src/app/modules/partners/services/models/monitoreo.types.spec.ts`: 200→`exito`, 429→`ritmo`, 403→`cliente`, 500→`plataforma`

**Checkpoint**: los centinelas se traducen en un solo sitio y el 429 ya no se confunde con un error del partner.

---

## Phase 3: User Story 1 — El partner entiende su consumo y lo que va a pagar (P1) 🎯 MVP

**Goal**: FR-UI-101 a FR-UI-107 — la superficie más usada y la de mayor riesgo de comunicación.

**Independent Test**: un partner abre `/partners/portal/consumo` y ve sus métricas, su cupo y su excedente estimado sin abrir ninguna otra pantalla; con el cupo superado, **nada** en la pantalla sugiere que su servicio se cortó.

**Measurable Criteria**: SC-001, SC-002, SC-005; escenarios A, B, C, D, I.

### Tests for User Story 1

- [X] T011 [P] [US1] Crear test de página (AAA) del camino feliz en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.spec.ts`: resuelve `GET /partners/me` **antes** de pedir métricas, y pinta llamadas, errores y latencia
- [X] T012 [P] [US1] 🎯 Crear test de invariante en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo-sin-alarma.spec.ts`: con el cupo al **150 %**, la plantilla renderizada **no contiene** ningún token de severidad (`alerta-critica`, `alerta-alta`, `alerta-media`) ni las palabras «bloqueado», «cortado», «límite superado». **Es el test que impide que alguien «arregle» el medidor poniéndolo en rojo** (RN-APM-002)
- [X] T013 [P] [US1] Crear test (AAA) de los centinelas en pantalla en `mi-consumo.page.spec.ts`: cupo `null` → «No aplica — sin cupo configurado» y **nunca** `0 %`; excedente `null` → «No aplica — sin tarifa configurada» y **nunca** `0,00`
- [X] T014 [P] [US1] Crear test (AAA) en `mi-consumo.page.spec.ts` que verifique que un partner **suspendido** carga sus métricas con normalidad más un banner informativo (RN-APM-017, escenario I)
- [X] T015 [P] [US1] Crear test (AAA) en `mi-consumo.page.spec.ts` de los tres estados no felices con los componentes compartidos, y que un **404 de `/partners/me`** muestra «Tu usuario no está vinculado a ningún partner» **sin** botón Reintentar

### Implementation for User Story 1

- [X] T016 [US1] Implementar `MiConsumoPage` (resolución vía `/partners/me`, carga de métricas, badge de entorno en **texto** y marca `datos_hasta`) en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.ts`
- [X] T017 [US1] Implementar el **bloque de cupo** con sus cuatro estados (`sin-cupo`, `holgado`, `cerca`, `excedido`), **los cuatro con el token `informacion`**, en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.ts` — ver la lista de prohibiciones de `panel-consumo-partner.ui-contract.md`
- [X] T018 [US1] Implementar el bloque de **excedente estimado** con el copy de facturación («se facturará al cierre del período»), en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.ts`
- [X] T019 [US1] Implementar los tres estados no felices con `app-list-loading-skeleton` / `app-list-error-state` / `app-list-empty-state`, en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.ts`

**Checkpoint**: 🎯 MVP — el partner ve su consumo y su coste previsto, y nadie confunde un excedente con una interrupción.

**US1 Gate**:
- [X] T020 [US1] Marcar FR-UI-101…107 y SC-001/002/005 como cubiertos en `specs/003-operational/Partners-API/api-monitoring-and-billing/frontend/traceability.md`

---

## Phase 4: User Story 2 — El partner diagnostica sus propios errores (P1)

**Goal**: RN-APM-009 en pantalla — que el partner corrija su cliente sin abrir un ticket.

**Independent Test**: un partner con un 403, un 429 y un 500 recientes distingue los tres y entiende cuál es suyo.

**Measurable Criteria**: SC-003; escenario F.

### Tests for User Story 2

- [X] T021 [P] [US2] Crear test (AAA) en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo-errores.spec.ts`: la lista muestra endpoint, código, latencia y hora de cada llamada con código ≥ 400
- [X] T022 [P] [US2] 🎯 Crear test (AAA) en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo-errores.spec.ts` que verifique que el **429 se presenta como «Límite de ritmo»** con token neutro y con la nota de que **no cuenta como consumo facturable** — agruparlo con los 4xx haría creer al partner que sus peticiones están mal formadas
- [X] T023 [P] [US2] Crear test (AAA) en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo-errores.spec.ts` del vacío **en positivo**: «Sin errores en el período. Tu integración está respondiendo correctamente» — no el vacío gris de un fallo de carga

### Implementation for User Story 2

- [X] T024 [US2] Implementar el bloque «Errores de tu integración» (`solo_errores=true`) con los badges de clase, en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.ts` — encabezado «Errores», **nunca** «Incidencias»
- [X] T025 [US2] Enlazar el contador de errores del bloque 2 con este bloque (no con la consola del Desarrollador de APIs: el partner no tiene acceso a esa ruta), en `frontend/src/app/modules/partners/pages/mi-consumo/mi-consumo.page.ts`

**Checkpoint**: US2 operativa — el partner se autodiagnostica.

**US2 Gate**:
- [X] T026 [US2] Marcar SC-003 como cubierto en `traceability.md`

---

## Phase 5: User Story 3 — El Desarrollador de APIs vigila la plataforma (P1)

**Goal**: FR-UI-111 a FR-UI-116 — consola de registros con autodiagnóstico y filtros honestos.

**Independent Test**: el DevAPIs elige un partner, filtra por errores y por código, abre el detalle de una llamada, y en ningún momento la interfaz promete datos instantáneos ni ofrece paginar.

**Measurable Criteria**: SC-005; escenarios F y G.

### Tests for User Story 3

- [X] T027 [P] [US3] Crear test de contrato de página (AAA) en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.spec.ts`: la tabla lista los registros del partner elegido, más recientes primero
- [X] T028 [P] [US3] Crear test (AAA) en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.spec.ts` del escenario G: **sin partner elegido** se muestra un `empty-state` que lo pide, y **no** se llama al endpoint (que devolvería 400)
- [X] T029 [P] [US3] Crear test (AAA) en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.spec.ts` de los filtros: `solo_errores` viaja **al servidor**; código HTTP y rango temporal filtran **en cliente** y la UI rotula «sobre los últimos N cargados» (`research.md` Decision 3)
- [X] T030 [P] [US3] Crear test (AAA) en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.spec.ts` que verifique que **no se renderiza ningún control de paginación** mientras `BE-DELTA-06` no exista — un «Cargar más» que no carga es peor que su ausencia
- [X] T031 [P] [US3] Crear test (AAA) en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.spec.ts` del auto-refresco: existe y está **apagado** al entrar; `datos_hasta` visible con la leyenda del retraso de ingesta
- [X] T032 [P] [US3] Crear test (AAA) del workpanel en `frontend/src/app/modules/partners/pages/detalle-log/detalle-log.page.spec.ts`: modo **Ver** con `<dl>`, **sin** `<input disabled>`, sin botón de guardado y sin acciones de dominio

### Implementation for User Story 3

- [X] T033 [US3] Implementar `ConsolaLogsPage` con el selector de partner **por nombre** (combobox sobre `GET /partners`), nunca tecleando su id, en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.ts`
- [X] T034 [US3] Implementar el filtrado en dos capas y su rótulo de alcance, en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.ts`
- [X] T035 [US3] Implementar la tabla `md:table` + cards mobile con la columna de acción **solo `eye`** (append-only: sin `pencil` ni `trash`), en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.ts`
- [X] T036 [US3] Implementar los badges de código según `data-model.md` § 2, con el **429 en token neutro**, en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.ts`
- [X] T037 [US3] Implementar el botón «Actualizar», el conmutador de auto-refresco (30 s, apagado) y el indicador de sincronización con `datos_hasta`, en `frontend/src/app/modules/partners/pages/consola-logs/consola-logs.page.ts`
- [X] T038 [US3] Implementar `DetalleLogPage` como página dedicada con el chrome del golden sample (link «← Volver a los registros», eyebrow «Detalles», `h1` + badge) en `frontend/src/app/modules/partners/pages/detalle-log/detalle-log.page.ts`
- [X] T039 [US3] Formatear `iporigen` de INT a notación con puntos en `frontend/src/app/modules/partners/services/models/monitoreo.types.ts` — el esquema lo declara entero y sin convertir sería un número sin sentido en pantalla

**Checkpoint**: US3 operativa — la plataforma se vigila sin prometer lo que no puede cumplir.

**US3 Gate**:
- [X] T040 [US3] Marcar FR-UI-111…116 como cubiertos en `traceability.md`

---

## Phase 6: User Story 4 — Rendir cuentas de un mes y compararlo (P2)

**Goal**: FR-UI-121 a FR-UI-124.

**Independent Test**: se consulta un mes, se compara con otro, y un mes sin consumo se lee como cero y no como avería.

**Measurable Criteria**: escenario E.

### Tests for User Story 4

- [X] T041 [P] [US4] Crear test (AAA) en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.spec.ts`: llamadas, errores y latencia del período elegido, con la leyenda de que **solo incluye producción**
- [X] T042 [P] [US4] Crear test (AAA) en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.spec.ts` de la comparación: dos períodos, variación absoluta y porcentual
- [X] T043 [P] [US4] Crear test (AAA) en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.spec.ts` de la **división por cero**: si el período comparado tuvo 0 llamadas, la variación porcentual es **«sin base de comparación»**, nunca `Infinity` ni `100 %`
- [X] T044 [P] [US4] 🎯 Crear test (AAA) en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.spec.ts` del escenario E: un mes sin consumo muestra **ceros** con `app-list-empty-state` y el copy «no es un error» — **nunca** `app-list-error-state` ni botón Reintentar
- [X] T045 [P] [US4] Crear test (AAA) en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.spec.ts` que verifique que el período viaja en la **URL** como query param y sobrevive a un refresco

### Implementation for User Story 4

- [X] T046 [US4] Implementar `ReporteConsumoPage` con selectores de partner, año y mes, y el período en la URL, en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.ts`
- [X] T047 [US4] Implementar la comparación opcional (segunda llamada solo si se elige período de comparación; sin comparar contra cero por defecto), en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.ts`
- [X] T048 [US4] Implementar el estado de mes sin consumo con su copy propio (`research.md` Decision 7), en `frontend/src/app/modules/partners/pages/reporte-consumo/reporte-consumo.page.ts`

**Checkpoint**: US4 operativa — un mes se explica y se compara.

**US4 Gate**:
- [X] T049 [US4] Marcar FR-UI-121…124 como cubiertos en `traceability.md`

---

## Phase 7: User Story 5 — El Administrador resuelve lo que no se pudo facturar (P2) 🎯

**Goal**: FR-UI-131 a FR-UI-135 — la única superficie donde no mirar cuesta dinero.

> **🔴 Las dos primeras tareas son BACKEND y bloquean toda la fase.** Reabren la capa `backend/`, cerrada con 71/71. Sin ellas esta historia **no tiene de dónde leer**.

**Independent Test**: el Administrador ve en una sola pantalla las facturas con reintentos agotados y los partners no tarificables, distinguidos, con su acción sugerida.

**Measurable Criteria**: SC-004; escenario H.

### Backend deltas (bloqueantes)

- [X] T050 [US5] 🔴 **`BE-DELTA-04`** — implementar `GET /api/v1/facturacion/excepciones` (Administrador y Desarrollador de APIs) leyendo de `Fact_Factura` las de `tipo='excedente_api'` cuyo `resultado_ultimo_reintento` empiece por `agotados:`, en `backend/apps/partners/views/facturacion_views.py` + la lectura en `backend/core/repositories/suscripciones/factura_repository.py` + ruta en `backend/apps/partners/views/urls.py`
- [X] T051 [US5] 🔴 **`BE-DELTA-05`** — incluir en la misma respuesta los partners **no tarificables** del período (tarifa en el centinela `-1.0`), derivados del cálculo que ya hace `backend/apps/partners/services/tarificacion_excedente_service.py`, con un discriminador `tipo` — hoy **solo existen como un correo**, que es el silencio que RN-APM-014 prohíbe
- [X] T052 [P] [US5] Crear test de contrato (marker: api, AAA) en `backend/apps/partners/tests/api/test_excepciones_facturacion_contract.py`: devuelve los dos tipos distinguidos, un partner no puede consultarlo (403), y el no tarificable **no lleva importe** (no `0.0`)
- [X] T053 [US5] Añadir el path al contrato en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/contracts/api-monitoring-and-billing.openapi.yaml` y documentar los dos deltas en `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/spec.md`

### Tests for User Story 5

- [X] T054 [P] [US5] Crear test de servicio con `HttpTestingController` en `frontend/src/app/modules/partners/services/facturacion-api.service.spec.ts`
- [X] T055 [P] [US5] 🎯 Crear test (AAA) en `frontend/src/app/modules/partners/pages/excepciones-facturacion/excepciones-facturacion.page.spec.ts`: los **dos tipos** aparecen distinguidos por badge, y el no tarificable lleva la columna de importe **vacía** — un `0,00` diría «se facturó nada» cuando la verdad es que no se pudo calcular
- [X] T056 [P] [US5] Crear test (AAA) en `frontend/src/app/modules/partners/pages/excepciones-facturacion/excepciones-facturacion.page.spec.ts` de la acción sugerida por tipo: emitir manualmente vs. configurar la tarifa del plan
- [X] T057 [P] [US5] Crear test (AAA) en `frontend/src/app/modules/partners/pages/excepciones-facturacion/excepciones-facturacion.page.spec.ts` que verifique que **no existe ningún botón de emitir** (FR-UI-135): no hay endpoint, y un botón que no hace nada es peor que su ausencia
- [X] T058 [P] [US5] Crear test (AAA) en `frontend/src/app/modules/partners/pages/excepciones-facturacion/excepciones-facturacion.page.spec.ts` del vacío **en positivo**: «No hay excepciones de facturación pendientes» — aquí vacío es la buena noticia

### Implementation for User Story 5

- [X] T059 [US5] Implementar `FacturacionApiService` en `frontend/src/app/modules/partners/services/facturacion-api.service.ts`
- [X] T060 [US5] Implementar `ExcepcionesFacturacionPage` con la tabla de dos tipos y sus acciones sugeridas, en `frontend/src/app/modules/partners/pages/excepciones-facturacion/excepciones-facturacion.page.ts`

**Checkpoint**: US5 operativa — ningún excedente se pierde en un correo.

**US5 Gate**:
- [X] T061 [US5] Marcar FR-UI-131…135 y SC-004 como cubiertos en `traceability.md`

---

## Phase 8: User Story 6 — Cada rol ve solo lo suyo (P2)

**Goal**: FR-UI-142, FR-UI-143 — sidebars por rol, sin exponer lo que el rol no puede usar.

**Independent Test**: los tres roles ven exactamente sus superficies, y escribir la ruta a mano no salta el guard.

**Measurable Criteria**: SC-006; escenario J.

### Tests for User Story 6

- [X] T062 [P] [US6] Crear test unitario (AAA) del guard en `frontend/src/app/modules/partners/guards/administrador.guard.spec.ts`: solo `Administrador`; un `DesarrolladorAPIs` **no** pasa
- [X] T063 [P] [US6] Crear test (AAA) de la matriz rol→navegación en `frontend/src/app/shared/layout/nav-links.spec.ts`: partner ve «Mi consumo» y no la consola; DevAPIs ve consola y reporte y no excepciones; Administrador ve excepciones

### Implementation for User Story 6

- [X] T064 [US6] Añadir las cuatro entradas al grupo «Partners y API» en `frontend/src/app/shared/layout/nav-links.ts` con sus roles e iconos

**Checkpoint**: US6 operativa — nadie descubre en su menú algo que no puede abrir.

**US6 Gate**:
- [X] T065 [US6] Marcar SC-006 como cubierto en `traceability.md`

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T066 [P] Crear el **guard de cableado** en `frontend/src/app/modules/partners/monitoreo-cableado.spec.ts`: las cuatro rutas existen, cargan su componente, tienen su guard, y sus entradas de navegación apuntan a rutas reales — es el mismo test que se creó en #07 tras el incidente de `decisiones-pendientes.md` #21, donde dos archivos se revirtieron y nada lo delató
- [X] T067 [P] Verificar que las cuatro superficies usan los componentes compartidos `app-list-*` y no reproducen el patrón con HTML propio (el `changelog.md` ya registra 10 páginas que lo hicieron)
- [X] T068 Ejecutar `npx ng test --watch=false --browsers=ChromeHeadless` desde `frontend/` y confirmar que no hay regresiones sobre la línea base de **459 tests** de #07
- [X] T069 Verificar la cobertura del módulo `partners` y registrar la cifra en `traceability.md`
- [X] T070 Crear `specs/003-operational/Partners-API/api-monitoring-and-billing/frontend/traceability.md` con la matriz FR-UI → tarea → test y el estado de los SC
- [X] T071 Actualizar el estado del módulo en `.specify/docs/architecture/module-map.md` §4 y cerrar los ítems de `specs/003-operational/Partners-API/api-monitoring-and-billing/frontend/checklists/requirements.md`
- [X] T072 Ejecutar la suite **backend** desde `backend/` (`python -m pytest -q`) y confirmar que los deltas T050/T051 no rompen la línea base de **1569 passed**
- [X] T073 **`BE-DELTA-06` implementado** (decisión del usuario 2026-08-10): `GET /logs-api` acepta `cursor`, `codigohttp`, `desde`, `hasta`, `idcredencialapi` y `endpoint`, en `backend/apps/partners/views/metricas_views.py` y `backend/core/repositories/partners/log_llamada_repository.py`. **Ningún filtro se resuelve en memoria**: cada cambio es una consulta, como en el resto del sistema
- [X] T074 **Verificación manual ejecutada 2026-08-10**: escenarios B, E, F, H e I verificados en la app real con `database/seed_monitoreo_demo.py`. Encontró **6 defectos** que la suite no veía — ver `traceability.md`

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
   └─► Phase 2 (Foundational)   ◄── T005: la traducción de centinelas
          ├─► Phase 3 (US1) 🎯 MVP    panel de consumo
          │      └─► Phase 4 (US2)    errores del partner (vive en la misma página)
          ├─► Phase 5 (US3)           consola de registros
          ├─► Phase 6 (US4)           reporte mensual
          └─► Phase 7 (US5)           excepciones — BLOQUEADA por T050/T051 (backend)
                 └─► Phase 8 (US6) ──► Phase 9 (Polish)
```

### User Story Dependencies

| Historia | Depende de | Motivo |
|---|---|---|
| US1 | Phase 2 | El helper de centinelas y el servicio |
| US2 | **US1** | Es un bloque **dentro** de la misma página; no es una superficie aparte |
| US3 | Phase 2 | Independiente de US1 y US2 |
| US4 | Phase 2 | Independiente |
| US5 | Phase 2 + **T050/T051 (backend)** | Sin los deltas no hay datos que mostrar |
| US6 | US1, US3, US4, US5 | La matriz de navegación necesita que las rutas existan |

### Parallel Opportunities

- **Phase 2**: T006, T008 y T010 en paralelo.
- **US1, US3 y US4 en paralelo** tras la fase fundacional — son tres páginas independientes.
- **T050/T051 (backend) pueden adelantarse** desde el principio, en paralelo con todo lo demás: no comparten un solo archivo con el frontend.
- Dentro de cada historia, **todos los tests marcados [P]** pueden escribirse a la vez.

### Parallel Example: tras la Phase 2

```bash
# Tres frentes de frontend + uno de backend, sin solaparse:
Phase 3 (US1)  panel de consumo      ← MVP, empezar por aquí
Phase 5 (US3)  consola de registros
Phase 6 (US4)  reporte mensual
T050/T051      deltas de backend     ← desbloquean la Phase 7
```

---

## Implementation Strategy

### MVP First (User Story 1)

US1 entrega lo que más se mira y lo que peor se comunicaría si se hiciera mal: **el partner viendo su consumo y lo que va a pagar**. Es también la superficie que justifica el tie-breaker de toda la capa.

### Incremental Delivery

1. **Phase 1 + 2** → centinelas traducidos en un solo sitio, 429 clasificado aparte.
2. **+ US1** → 🎯 MVP: el partner entiende su coste previsto y nadie cree que le cortaron el servicio.
3. **+ US2** → se autodiagnostica sin abrir tickets.
4. **+ US3 y US4** → la plataforma se vigila y el mes se explica.
5. **+ US5** → ningún excedente se queda en un correo (requiere los deltas).
6. **+ US6 y Polish** → navegación por rol y cierre del departamento.

---

## Notes

- **T012 es el test más importante de esta capa.** Protege una regla contraintuitiva: superar el cupo **no** es un estado de alarma. Sin él, el primero que vea un 150 % en azul lo «arreglará» a rojo y romperá RN-APM-002 creyendo que corrige un bug.
- **T005 evita el fallo más silencioso**: un `0 %` donde el backend dijo `null` afirma que el partner no consumió, y es falso.
- **T030 y T073 son la misma deuda vista desde dos lados**: mientras el endpoint anuncie un cursor que no acepta, la UI no dibuja paginación y el contrato miente. Una de las dos cosas tiene que cambiar.
- **T050 y T051 reabren la capa backend**, cerrada con 71/71. Es deliberado y está justificado en `spec.md`: exponen datos y cálculos que ya existen, sin cambiar ninguna regla.
- **El 429 se trata aparte del resto de 4xx** en T009, T022 y T036. Agruparlos haría creer al partner que sus peticiones están mal formadas cuando solo se le está regulando el ritmo.
- **`ng test` es el gate, no `tsc --noEmit`.** Las plantillas de Angular no se validan con el compilador de TypeScript.

### Resultado (2026-08-10)

**74/74 menos la verificación manual.** 250 tests del módulo `partners`, suite frontend **574 passed** (base #07: 459), backend **1581 passed** tras los deltas (base 1569).

Pendientes a propósito:

| Tarea | Por qué |
|---|---|
| *(ninguna)* | Todas cerradas |

### Añadido tras la implementación (2026-08-10)

| Tarea | Qué cerró |
|---|---|
| **T075** | `BE-DELTA-06`: paginación por cursor y **todos** los filtros en la base. Test `test_consola_logs_paginacion.py` (11) |
| **T076** | Corregidos `latenciams` e `idcredencialapi` en la capa frontend: usaba `latencia` e `idcredencial`, que **no existen** en `Fact_LogLlamadaAPI`. La columna habría salido vacía en pantalla |
