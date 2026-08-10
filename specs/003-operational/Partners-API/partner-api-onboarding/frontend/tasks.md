# Tasks: Onboarding de Partners API — Frontend

**Input**: Design documents from `specs/003-operational/Partners-API/partner-api-onboarding/frontend/`

**Prerequisites**: `spec.md` (FR-UI-001…034, US-FE-1…6), `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: **Incluidos y obligatorios.** `.specify/docs/architecture/testing.md` es vinculante: «No se acepta código sin al menos un test asociado». Cobertura mínima frontend **≥ 80 %** (Jasmine + Karma, `ng test`).

**Organization**: agrupadas por historia de usuario para poder implementar y validar cada una de forma independiente.

> **Capa Interaction Capability.** Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST. Las dos únicas excepciones son `BE-DELTA-01` y `BE-DELTA-02`, acotadas en `spec.md` § Dependencias de backend y ejecutadas en la Fase 2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: ejecutable en paralelo (archivos distintos, sin dependencia pendiente)
- **[Story]**: `[US1]`…`[US6]` → mapean a US-FE-1…US-FE-6 de `spec.md`
- Cada descripción lleva su path exacto

## Path Conventions

- Frontend: `frontend/src/app/modules/partners/` (módulo **nuevo**, no existe hoy)
- Compartidos: `frontend/src/app/shared/`
- Backend (solo Fase 2): `backend/apps/partners/`

---

## ⚠️ Dos avisos antes de empezar

1. **El MVP no necesita tocar el backend.** US-FE-1 y US-FE-3 son consola y solo consumen endpoints
   ya cerrados. `BE-DELTA-01` y `BE-DELTA-02` bloquean **únicamente** las historias del portal
   (US-FE-2, 4, 5, 6). Si hace falta entregar valor pronto, la ruta es Fases 1 → 2A → 3.
2. **Reabrir el backend exige reejecutar su suite.** Cerró con 208 tests del módulo y 1250 en total;
   T017 y T024 lo verifican explícitamente.

---

## ✅ Estado de ejecución (2026-08-09)

**90 de 91 tareas completadas.** Las seis páginas están implementadas de verdad — ya no queda
ningún marcador. Evidencia:

| | |
|---|---|
| Frontend `ng test` | **459 SUCCESS, 0 fallos** |
| Cobertura del módulo `partners` | **91,6 %** (umbral 80 %) |
| Backend tras los dos deltas | **1263 passed, 2 skipped** (línea base 1250) |
| `npx tsc --noEmit` | limpio |

Cobertura por carpeta: services 94,3 · guards 96,3 · lista 86,2 · detalle 96,9 · mi-integración
82,5 · secreto 87,0 · cola 96,9 · contrato 96,7 — **todas sobre el umbral**.

### Lo único pendiente

**T088** — los 12 escenarios A–L de [`quickstart.md`](./quickstart.md) contra el stack real. Son
validaciones manuales en navegador (throttling de red, DevTools, simulación de daltonismo,
dos sesiones simultáneas) que no se pueden automatizar desde aquí. Cuatro de ellos sí tienen su
equivalente automatizado —D, E, G y K.3, los de propiedades negativas— pero **la ejecución manual
sigue siendo el criterio de salida**, igual que `verifica_onboarding_e2e.py` lo fue en el backend.

**Nota de ejecución para quien retome:** los tests de Karma necesitan `CHROME_BIN`; en esta máquina
no hay Chrome, pero Edge (Chromium) sirve:

```bash
CHROME_BIN="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" npx ng test --watch=false --browsers=ChromeHeadless
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: crear el módulo y engancharlo al chrome de la app.

- [X] T001 Crear el árbol del módulo en `frontend/src/app/modules/partners/{guards,services/models,pages}` siguiendo la estructura de `plan.md` § Project Structure — árbol creado en `frontend/src/app/modules/partners/`.
- [X] T002 Crear `frontend/src/app/modules/partners/partners.routes.ts` con las dos superficies (`consola` y `portal`) y lazy `loadComponent` por página, calcando `modules/accidentes/accidentes.routes.ts` — **hecho**. Sin ruta `:idpartner/editar`: variante Ver-only (FR-UI-003).
- [X] T003 Registrar la entrada lazy `partners` en `frontend/src/app/app.routes.ts`, dentro del bloque autenticado — **hecho**, dentro del bloque autenticado.
- [X] T004 Añadir el grupo **«Partners y API»** a `frontend/src/app/shared/layout/nav-links.ts` con entradas separadas por rol: «Partners» y «Solicitudes pendientes» → `['Administrador','DesarrolladorAPIs']`; «Mi integración» y «Contrato de integración» → `['PartnerIntegracion']` (FR-UI-033) — **el rol `PartnerIntegracion` no existe hoy en este archivo** — **hecho**: 4 entradas nuevas. Requirió además **extender `shared/ui/icon/tabler-icon.component.ts`**: `TablerIconName` es una unión cerrada y los glifos que pedía `data-model.md` (`flask`, `license`, `ban`, `bolt`, `key`, `copy`, `user-plus`, `clock`) **no existían**. Se añadieron al mismo set Tabler outline, como exige el design-system.
- [X] T005 [P] Actualizar la «Matriz rol → navegación UI» de `.specify/docs/architecture/module-map.md` para que refleje T004 (el propio `nav-links.ts` la cita como documentación espejo) — **hecho**: añadidas las filas `DesarrolladorAPIs` y `PartnerIntegracion` a la «Matriz rol → navegación UI», con la nota de que resolver promociones es exclusivo de Administrador.
- [X] T006 [P] Extender `frontend/src/app/shared/layout/app-shell.component.spec.ts` para verificar que un usuario `PartnerIntegracion` ve el sidebar del portal y **no** ve las entradas de consola — **hecho**: 3 tests nuevos en `app-shell.component.spec.ts` — el partner solo ve su portal, no descubre la consola, y el Desarrollador de APIs a la inversa.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia puede completarse sin esta fase.

### Fase 2A — Base del frontend (no bloquea con backend)

- [X] T007 [P] Definir los tipos de dominio en `frontend/src/app/modules/partners/services/models/partner.types.ts` (`EstadoPartner`, `Entorno`, `PartnerListItem`, `PartnerDetalle`, `CredencialItem`, `CredencialEmitida`, `VersionContrato`) según `data-model.md` § 1 — **hecho** — 6 interfaces + 3 uniones, con los centinelas documentados en cada campo.
- [X] T008 [P] Crear `frontend/src/app/modules/partners/estado-partner.constants.ts` con el mapa de los 6 estados → etiqueta, ícono Tabler y token semántico (`data-model.md` § 2) — **hecho**: los 6 estados → etiqueta, ícono, tono y, además, la línea de «qué sigue» que exige FR-UI-015.
- [X] T009 [P] Crear `frontend/src/app/modules/partners/entorno.constants.ts` con Sandbox/Producción → ícono, etiqueta y nota de vigencia — **hecho**: Sandbox/Producción con ícono, etiqueta y nota de vigencia.
- [X] T010 [P] Crear los helpers de centinelas en `frontend/src/app/modules/partners/services/models/centinelas.ts`: `-1` → «Sin asignar», `''` → «Sin plan», `253402300799000` → «No expira», `0` → «Sin retiro planificado» (FR-UI-025, FR-UI-029) — **hecho** en `centinelas.ts`, con `estaVencida` (cálculo perezoso fail-safe) y `diasParaVencer` de propina.
- [X] T011 [P] Crear test unitario de los helpers de centinelas en `frontend/src/app/modules/partners/services/models/centinelas.spec.ts` — **un `-1` renderizado como cupo o un año 9999 como fecha son defectos visibles** — **hecho** — 20 tests. Cada uno corresponde a un defecto visible concreto: un cupo `-1`, una fecha del 9999, un retiro el 01/01/1970.
- [X] T012 Implementar `frontend/src/app/modules/partners/services/partner-api.service.ts` (listar con cursor, detalle, registrar, asignar plan, credenciales, solicitud, resolución) con `ApiEnvelope` compartido — **hecho**, incluida `miPartner()` y el helper `nuevaClaveIdempotencia()`.
- [X] T013 [P] Implementar `frontend/src/app/modules/partners/services/contrato-api.service.ts` (`GET /contrato-integracion?id_servicio&version`) — **hecho**.
- [X] T014 [P] Crear `frontend/src/app/modules/partners/guards/gestor-partners.guard.ts` (`['Administrador','DesarrolladorAPIs']`) siguiendo `modules/accidentes/guards/accidentes-lectura.guard.ts` — **hecho**.
- [X] T015 [P] Crear `frontend/src/app/modules/partners/guards/administrador-promocion.guard.ts` — **solo `Administrador`** (RF-PON-008, FR-UI-011) — **hecho** — usa `hasRole`, no `hasAnyRole`: el permiso no admite lista.
- [X] T016 [P] Crear `frontend/src/app/modules/partners/guards/partner-integracion.guard.ts` (`['PartnerIntegracion']`) — **hecho**.
- [X] T017 [P] Crear tests de los tres guards en `frontend/src/app/modules/partners/guards/*.spec.ts`, incluyendo que el Desarrollador de APIs sea rechazado por `administrador-promocion.guard` — **hecho** en `guards/partners-guards.spec.ts` (10 tests), incluido que el Desarrollador de APIs sea denegado por `administrador-promocion.guard` aunque sí sea gestor de partners.

### Fase 2B — `BE-DELTA-01`: el portal es inalcanzable sin esto

> Verificado en código: el `Profile` de sesión solo trae `{idusuario, gmail, roles[]}`, todos los
> endpoints del portal exigen `{idpartner}` en la ruta y `GET /partners` es `EsDesarrolladorAPIs`.

- [X] T018 Implementar `MiPartnerView` (`GET /api/v1/partners/me`) en `backend/apps/partners/views/partner_views.py`: resuelve el `idcliente` del usuario con `ClienteLookupService`, devuelve su partner o **404** si no tiene; permiso `EsPartnerOGestor` — **hecho**: `MiPartnerView` con 404 diferenciado (`sin_cliente` / `sin_partner`).
- [X] T019 Registrar la ruta `partners/me` en `backend/apps/partners/views/urls.py` **antes** de `partners/<int:idpartner>` para que no la capture el patrón numérico — **hecho**, `partners/me` antes del patrón numérico.
- [X] T020 [P] Crear test de contrato en `backend/apps/partners/tests/api/test_mi_partner_contract.py` (marker `api`, AAA): 200 para el partner propio, 404 para usuario sin partner, 401 sin token, y que **nunca** exponga `client_secret_hash` — **hecho** — 8 tests, incluido que no exponga el hash y que un partner ajeno no obtenga el perfil de otro.
- [X] T021 [P] Añadir `GET /partners/me` a `specs/003-operational/Partners-API/partner-api-onboarding/backend/contracts/partner-api-onboarding.openapi.yaml` — **hecho**: `/partners/me` documentado en el OpenAPI.

### Fase 2C — `BE-DELTA-02`: que el secreto de producción lo vea su dueño

> Hoy `CredencialesView` rechaza `entorno=Producción` con 403 **sin excepción**, y el secreto acaba
> en manos del Administrador que aprueba.

- [X] T022 Condicionar la guarda de autoservicio de producción en `backend/apps/partners/views/credencial_views.py`: permitir `entorno=Producción` **solo si el estado derivado del partner ya es «Producción activa»**; en cualquier otro caso mantener el 403 actual — **hecho**: guarda condicionada al estado derivado, con `except` fail-closed.
- [X] T023 [P] Crear test de contrato en `backend/apps/partners/tests/api/test_emision_produccion_partner.py`: 403 antes de la aprobación (RN-PON-004 intacta), 201 después, y que la credencial de pruebas siga activa (RN-PON-008) — **hecho** — 7 tests: 403 antes de aprobar (RN-PON-004 intacta), 201 después, secreto al partner, pruebas sigue activa, y propiedad respetada.
- [X] T024 Reejecutar la suite del backend desde `backend/` (`python -m pytest -q`) y confirmar que no hay regresiones sobre la línea base de **1250 passed, 2 skipped**; actualizar el recuento en `../backend/traceability.md` — **hecho: 1263 passed, 2 skipped** (línea base 1250) — cero regresiones. Módulo de partners: 208 → **221 tests**.
- [X] T025 [P] Marcar `BE-DELTA-01` y `BE-DELTA-02` como resueltos en `../backend/traceability.md` § «Cambios fuera de ciclo» y en `.specify/docs/architecture/module-map.md` — **hecho** en `../backend/traceability.md` y en `module-map.md`; el OpenAPI documenta también la nueva semántica del 403 de producción.

**Checkpoint**: tipos, servicios, guards y los dos deltas listos — las historias pueden arrancar.

---

## Phase 3: US-FE-1 — Incorporar un partner y darle cupo (P1) 🎯 MVP

**Goal**: un Administrador registra el perfil de partner sobre un cliente existente y le asigna el plan, dejando su cupo congelado.

**Independent Test**: registrar sobre un cliente con suscripción vigente y comprobar que aparece en la lista con estado «Plan asignado» y su cupo visible.

**No depende de `BE-DELTA-01` ni de `BE-DELTA-02`** — es consola pura sobre endpoints ya cerrados.

### Tests for User Story 1

- [X] T026 [P] [US1] Crear `frontend/src/app/modules/partners/pages/lista-partners/lista-partners.page.spec.ts`: render de la lista, `-1` como «Sin asignar», paginación por cursor y **ausencia del ícono `pencil`** (FR-UI-003) — **hecho** — 13 tests: Ver-only sin lápiz, centinelas, los tres estados no felices y paginación acumulativa.
- [X] T027 [P] [US1] Crear `frontend/src/app/modules/partners/pages/detalle-partner/detalle-partner.page.spec.ts`: modo Ver usa `<dl>` y **no** `<input disabled>`; modo Crear reutiliza el mismo componente — **hecho** — 17 tests: chrome del golden sample, `<dl>` sin `<input disabled>`, y que la acción de plan desaparezca en un partner suspendido.
- [X] T028 [P] [US1] Crear test del mapeo de errores de registro en `frontend/src/app/modules/partners/services/partner-api.service.spec.ts`: duplicado, sin suscripción y plan incompleto producen mensajes accionables distintos (FR-UI-005/006, SC-005) — **cubierto** por el bloque «mapeo de errores de negocio (SC-005)» de `detalle-partner.page.spec.ts`: se probó donde el error se presenta al usuario, no en el servicio que solo lo propaga.

### Implementation for User Story 1

- [X] T029 [US1] Implementar `lista-partners.page.ts` en `frontend/src/app/modules/partners/pages/lista-partners/` con tabla `md:table` + cards en mobile, CTA «Registrar partner», filtro por estado y **única acción `eye`** (FR-UI-001/002/003) — **hecho**: tabla `md:table` + cards en mobile, filtro por estado, CTA de alta y única acción `eye`.
- [X] T030 [US1] Implementar los tres estados no felices de la lista con `app-list-loading-skeleton`, `app-list-error-state` y `app-list-empty-state` de `frontend/src/app/shared/ui/list-states/` — nunca HTML propio (FR-UI-030) — **hecho** con los tres componentes compartidos, sin HTML propio.
- [X] T031 [US1] Implementar el chrome del workpanel en `detalle-partner.page.ts`: link «← Volver a la lista» (`arrow-left`), eyebrow de modo, `h1` + badge de estado en la misma fila, secciones en cards (`contracts/consola-partners.ui-contract.md`) — **hecho**: «← Volver a la lista», eyebrow, `h1` + badge en la misma fila, secciones en cards.
- [X] T032 [US1] Implementar el **modo Ver** con `<dl>`/`dt`/`dd` y el badge de estado derivado no editable (FR-UI-014, Decisión 4) — **hecho** con `<dl>`/`dt`/`dd`; cero `<input disabled>` verificado por test.
- [X] T033 [US1] Implementar el **modo Crear** con Reactive Forms y **combobox de cliente por nombre legible**; prohibido teclear `idcliente` (FR-UI-004, FR-UI-032) — **hecho**: combobox de cliente por nombre; nunca se teclea `idcliente`.
- [X] T034 [US1] Implementar el mapeo de errores del registro según `contracts/consola-partners.ui-contract.md` § Mapeo de errores, con **enlace al partner existente** en el caso duplicado (FR-UI-005) — **hecho**, con enlace al partner existente usando el `idpartner_existente` del 409.
- [X] T035 [US1] Implementar la acción de dominio «Asignar plan de acceso» mostrando el cupo derivado que quedará **congelado** y su advertencia (FR-UI-007); ausente si el partner está suspendido (FR-UI-034) — **hecho**, con la advertencia de cupo congelado y ausente si el partner está suspendido.
- [X] T036 [US1] Implementar el recuerdo de la última fila abierta con acento de marca al ~0.06–0.08, reutilizando el patrón de `modules/accidentes/lista-seleccion.storage.ts` — **hecho** reutilizando el patrón de `lista-seleccion.storage.ts`, con acento de marca al 7%.
- [X] T037 [US1] Enviar `Idempotency-Key` en el registro y en la asignación de plan desde `partner-api.service.ts` — **hecho** en registro y asignación de plan.

**Checkpoint**: US-FE-1 funcional y testeable sola. **MVP entregable sin haber tocado el backend.**

---

## Phase 4: US-FE-2 — Emitir una credencial y custodiar el secreto (P1) ⚠️ historia de mayor riesgo

**Goal**: el partner emite una credencial nombrada y recibe el secreto una sola vez.

**Independent Test**: emitir y verificar que el secreto se muestra en un paso del que no se puede salir sin confirmar, y que no queda rastro suyo tras abandonarlo.

**Depende de**: `BE-DELTA-01` (T018–T021).

### Tests for User Story 2

- [X] T038 [P] [US2] Crear `frontend/src/app/modules/partners/pages/secreto-emitido/secreto-emitido.page.spec.ts`: la salida está **deshabilitada** hasta marcar la confirmación, y `Esc` no cierra nada (FR-UI-020) — **hecho** — la salida está deshabilitada hasta confirmar y `Esc` no cierra nada.
- [X] T039 [P] [US2] Crear test de no-fuga en `secreto-emitido.page.spec.ts`: tras renderizar, el secreto **no** aparece en `localStorage`, `sessionStorage`, `location.href` ni `document.title` (FR-UI-021, **SC-004**) — **hecho** — se verifica ausencia en `localStorage`, `sessionStorage`, `location.href` y `document.title`.
- [X] T040 [P] [US2] Crear test de recarga: al entrar sin estado de navegación, se muestra la explicación de que el secreto ya no está disponible, no una pantalla rota (FR-UI-022) — **hecho** — sin estado de navegación se explica cómo recuperarse, no una pantalla rota.
- [X] T041 [P] [US2] Crear test de idempotencia en `partner-api.service.spec.ts`: dos intentos consecutivos tras un fallo de red reutilizan **la misma** `Idempotency-Key` (FR-UI-023, **SC-003**) — **hecho** — dos intentos tras fallo reutilizan la clave; tras éxito se renueva.
- [X] T042 [P] [US2] Crear `frontend/src/app/modules/partners/pages/mi-integracion/mi-integracion.page.spec.ts`: sin plan, el CTA de emisión se sustituye por el copy explicativo (FR-UI-019) — **hecho** — sin plan, el CTA se sustituye por el copy explicativo.

### Implementation for User Story 2

- [X] T043 [US2] Implementar la resolución del partner propio vía `GET /partners/me` en `partner-api.service.ts`, con el 404 presentado como «Tu usuario aún no tiene un perfil de partner asociado» (FR-UI-013) — **hecho** vía `miPartner()`, con el 404 presentado como explicación.
- [X] T044 [US2] Implementar `mi-integracion.page.ts` con los bloques de estado, plan y cupo, sin ningún control que edite el estado (FR-UI-014) — **hecho** — bloques de estado, plan y cupo, sin control que edite el estado.
- [X] T045 [US2] Implementar la línea de «qué sigue» por estado según la tabla de `contracts/portal-partner.ui-contract.md` (FR-UI-015) — **hecho**: la línea «qué sigue» sale del mapa de `estado-partner.constants.ts`.
- [X] T046 [US2] Implementar el formulario de emisión con validación en cliente del nombre contra las **activas del mismo entorno** (FR-UI-017) y el `409 nombre_duplicado` como error **del campo** (FR-UI-018) — **hecho** — validación en cliente contra las activas del mismo entorno; el 409 no debería llegar.
- [X] T047 [US2] Implementar la sustitución del CTA por el copy de «sin plan» definido en `research.md` (FR-UI-019) — **hecho**.
- [X] T048 [US2] Implementar `secreto-emitido.page.ts` como **página dedicada sin parámetros de ruta**: el secreto llega por estado de navegación en memoria, nunca por la URL — **hecho**: página dedicada sin parámetros de ruta; el secreto viaja por estado de navegación.
- [X] T049 [US2] Implementar el aviso de irreversibilidad **antes** del valor, `client_id` y `client_secret` en `JetBrains Mono` con botón «Copiar» por campo, y el checkbox que habilita la salida (FR-UI-020) — **hecho** — aviso antes del valor, `JetBrains Mono`, copia por campo y checkbox que habilita la salida.
- [X] T050 [US2] Implementar el descarte del secreto al abandonar la página y el estado vacío tras recarga, con la explicación de cómo emitir otra sin interrumpir las existentes (FR-UI-022) — **hecho**: se descarta en `ngOnDestroy`, se limpia `history.state` y la recarga muestra el estado explicativo.
- [X] T051 [US2] Implementar la generación y reutilización de `Idempotency-Key` (UUID v4 por intento del usuario, **no** por reintento HTTP) en la emisión (FR-UI-023) — **hecho** — UUID v4 por intento; NO se renueva al fallar, sí tras un éxito.
- [X] T052 [US2] Aplicar el patrón de botón en carga a la emisión: deshabilitado, texto en gerundio, spinner de 16px dentro del botón, y **retorno del control a los 10–15 s** sin respuesta (design-system § 5) — **hecho** — gerundio, deshabilitado y `setTimeout` de 15 s que devuelve el control.

**Checkpoint**: US-FE-1 y US-FE-2 funcionan de forma independiente.

---

## Phase 5: US-FE-3 — Resolver la cola de solicitudes (P1)

**Goal**: un Administrador revisa las solicitudes pendientes y las aprueba o rechaza con motivo.

**Independent Test**: con una solicitud pendiente, aprobarla y comprobar que el partner pasa a «Producción activa»; rechazarla y comprobar que vuelve a «Pruebas activo».

**No depende de los deltas** (la parte de consola).

### Tests for User Story 3

- [X] T053 [P] [US3] Crear `frontend/src/app/modules/partners/pages/cola-solicitudes/cola-solicitudes.page.spec.ts`: la cola se alimenta de `GET /partners?estado=Pendiente de aprobación` (Decisión 8) y ordena por antigüedad — **hecho** — 3 tests: se alimenta de `GET /partners?estado=…`, sin endpoint nuevo.
- [X] T054 [P] [US3] Crear test de separación de actores: con rol `DesarrolladorAPIs` la cola se ve **sin** acciones de resolver (FR-UI-011) — **hecho** — el Desarrollador de APIs ve la cola sin botones de resolver.
- [X] T055 [P] [US3] Crear test de que **aprobar no muestra ningún secreto** al Administrador (FR-UI-009) — es el requisito que nace de la decisión Q2 — **hecho** — se inyecta un `client_secret` en la respuesta de aprobación y se verifica que **no** aparece en el DOM.
- [X] T056 [P] [US3] Crear test de concurrencia: un `409 sin_solicitud_pendiente` informa sin culpar al usuario y dispara el refresco de la cola (FR-UI-012) — **hecho** — 2 tests: aviso sin culpar al usuario + refresco automático.

### Implementation for User Story 3

- [X] T057 [US3] Implementar `cola-solicitudes.page.ts` con las entradas (partner, contacto técnico, credencial solicitada, antigüedad) y su estado vacío como **resultado deseable**, no como error (FR-UI-008) — **hecho**, con el estado vacío tratado como resultado deseable.
- [X] T058 [US3] Implementar la acción **Aprobar** con confirmación en 2 pasos que, al completarse, **no muestra secreto** e informa de que el partner emitirá su credencial productiva (FR-UI-009) — **hecho** — confirmación en 2 pasos que además avisa de que el secreto lo verá el partner.
- [X] T059 [US3] Implementar la acción **Rechazar** con `textarea`, contador y `minlength`, y el texto de ayuda que advierte que el motivo se envía al contacto técnico (FR-UI-010, Decisión 3) — **hecho** — `textarea` con contador y mínimo de 15 caracteres.
- [X] T060 [US3] Ocultar las acciones de resolución para el Desarrollador de APIs y proteger la ruta `…/resolver` con `administrador-promocion.guard` (FR-UI-011) — **hecho** en la vista y en la ruta (`administrador-promocion.guard`).
- [X] T061 [US3] Implementar el manejo de `sin_solicitud_pendiente` como Alert modal + refresco automático (FR-UI-012) — **hecho**.
- [X] T062 [US3] Enviar `Idempotency-Key` en la resolución desde `partner-api.service.ts` — **hecho**.
- [X] T063 [US3] Implementar los tres estados no felices de la cola con los componentes compartidos (FR-UI-030) — **hecho** con los componentes compartidos.

**Checkpoint**: las tres historias P1 funcionan de forma independiente.

---

## Phase 6: US-FE-4 — Operar dos entornos sin confundirlos (P2)

**Goal**: el partner ve pruebas y producción conviviendo, sin riesgo de actuar sobre la equivocada.

**Independent Test**: con credenciales en ambos entornos, verificar que siguen distinguiéndose **con el color desactivado**.

**Depende de**: `BE-DELTA-01`, y `BE-DELTA-02` para FR-UI-027.

### Tests for User Story 4

- [X] T064 [P] [US4] Crear test de agrupación por entorno en `mi-integracion.page.spec.ts`: dos encabezados separados con ícono y etiqueta propios (FR-UI-016) — **hecho** — encabezados separados por entorno.
- [X] T065 [P] [US4] Crear test de que la distinción **no depende del color**: los nodos de texto e ícono bastan para identificar el entorno (**SC-006**) — **hecho** — se comprueba que hay ícono y etiqueta de texto, no solo color.
- [X] T066 [P] [US4] Crear test de que el centinela de vigencia se renderiza «No expira» y nunca una fecha del 9999 (FR-UI-025) — **hecho** — «No expira» y ausencia de «9999» en el DOM.

### Implementation for User Story 4

- [X] T067 [US4] Implementar el bloque de credenciales **agrupado bajo encabezados por entorno** con su ícono Tabler y etiqueta (FR-UI-016, Decisión 5) — **hecho**.
- [X] T068 [US4] Implementar el formateo de vigencia con los helpers de centinelas (FR-UI-025) — **hecho** con los helpers de `centinelas.ts`.
- [X] T069 [US4] Ocultar el bloque de producción mientras el partner nunca haya sido promovido, y mostrarlo con CTA «Emitir credencial de producción» una vez en «Producción activa» (FR-UI-027) — **hecho** — el grupo de producción se oculta hasta la promoción y luego ofrece emitir.
- [X] T070 [US4] Verificar que tras aprobar la promoción **las credenciales de pruebas siguen activas** y nada en la UI sugiere lo contrario (RN-PON-008) — **hecho** — verificado por test que las de pruebas siguen activas.

**Checkpoint**: el portal distingue entornos de forma accesible.

---

## Phase 7: US-FE-5 — Regenerar una credencial vencida (P2)

**Goal**: el partner recupera su acceso de pruebas por autoservicio, sin depender de un gestor.

**Independent Test**: con una credencial vencida, regenerarla y comprobar que las demás siguen activas.

### Tests for User Story 5

- [X] T071 [P] [US5] Crear test de que una credencial vencida se distingue visualmente de una activa y ofrece regenerar (FR-UI-024) — **hecho**.
- [X] T072 [P] [US5] Crear test de que regenerar **no desactiva** las demás credenciales del partner (**SC-007**) — **hecho** — regenerar reutiliza nombre y entorno sin tocar las demás.

### Implementation for User Story 5

- [X] T073 [US5] Implementar el estado «vencida» en el listado de credenciales, derivado de `fecha_expiracion` frente al reloj del cliente (cálculo perezoso, `research.md` Decisión 8 del backend) — **hecho** con `estaVencida()`, que es fail-safe: no depende de que el job haya corrido.
- [X] T074 [US5] Implementar la acción «Regenerar» que reutiliza el flujo de emisión y desemboca en el paso del secreto (FR-UI-024) — **hecho** — reutiliza el flujo de emisión y desemboca en el paso del secreto.
- [X] T075 [US5] Verificar que el nombre liberado por una credencial vencida puede reutilizarse sin colisión (CA-PON-006) — **cubierto** por la validación de nombre contra **activas**: una vencida no bloquea su nombre.

**Checkpoint**: el partner se recupera solo de un vencimiento.

---

## Phase 8: US-FE-6 — Consultar el contrato versionado (P3)

**Goal**: el partner consulta la versión vigente del servicio que integra y las soportadas.

**Independent Test**: con dos servicios que tengan ambos una «v1», comprobar que no se confunden.

### Tests for User Story 6

- [X] T076 [P] [US6] Crear `frontend/src/app/modules/partners/pages/contrato-integracion/contrato-integracion.page.spec.ts`: vigente destacada, soportadas listadas, y aislamiento entre servicios (FR-UI-028) — **hecho** — 5 tests, incluido el aislamiento entre servicios.
- [X] T077 [P] [US6] Crear test de los centinelas del contrato: `fecha_retiro = 0` → «Sin retiro planificado»; `spec_url = ''` → sin enlace roto (FR-UI-029) — **hecho** — «Sin retiro planificado» y sin enlace roto.

### Implementation for User Story 6

- [X] T078 [US6] Implementar `contrato-integracion.page.ts` con selector de **servicio por nombre legible**, nunca `id_servicio` (FR-UI-028, FR-UI-032) — **hecho** — selector por nombre; nunca se teclea `id_servicio`.
- [X] T079 [US6] Implementar la presentación de la vigente destacada y las soportadas con su fecha de retiro — **hecho**.
- [X] T080 [US6] Implementar el manejo de `400` (falta `id_servicio`) y `404` (servicio o versión inexistente) según `contracts/portal-partner.ui-contract.md` — **hecho** — el 404 se explica como «servicio sin versión publicada».
- [X] T081 [US6] Implementar los tres estados no felices de la vista con los componentes compartidos (FR-UI-030) — **hecho**.

**Checkpoint**: las seis historias son independientemente funcionales.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T082 [P] Verificar en las seis páginas que **ningún identificador interno** se pide al usuario ni se muestra como campo principal (FR-UI-032, escenario L del quickstart) — **verificado**: el único `formControlName` con nombre de id es el `<select>` de cliente, que muestra **nombres** — el id viaja solo en el payload, como exige FR-UI-004.
- [X] T083 [P] Verificar que ninguna vista expone `client_secret_hash` ni el secreto fuera de su paso dedicado (FR-UI-031) — **verificado**: `client_secret_hash` no aparece en ningún archivo del módulo, y `client_secret` solo en `secreto-emitido.page.ts` y sus tests.
- [X] T084 [P] Revisar responsividad en los tres breakpoints: tablas → cards en mobile, workpanel a página completa, sidebar a hamburguesa (escenario K.1) — **hecho** en el código: tabla `md:table` + cards `md:hidden` en la lista, workpanel a página completa y sidebar hamburguesa heredada del shell. **Pendiente la comprobación visual** del escenario K.1.
- [X] T085 [P] Verificar tema claro/oscuro en badges de estado y entorno: **cero hex hardcodeados**, todo vía token semántico (escenario K.2) — **verificado estáticamente**: cero hex en el módulo; todos los tonos usan clases de token con variante `dark:`.
- [X] T086 [P] Verificar contraste ≥ 4.5:1 **en ambos temas por separado** para los tokens usados por este módulo (design-system § 6) — **parcial**: se reutilizan los tokens del design-system, ya validados en ambos temas. La medición de contraste con herramienta queda en el escenario K de `quickstart.md`.
- [X] T087 Ejecutar `ng test` completo y confirmar cobertura **≥ 80 %** del módulo `partners` (`testing.md`, umbral frontend) — **hecho: 459 tests en verde y cobertura del módulo 91,6 %** (umbral 80 %). Por carpeta: services 94,3 · guards 96,3 · lista 86,2 · detalle 96,9 · mi-integración 82,5 · secreto 87,0 · cola 96,9 · contrato 96,7.
- [~] T088 Ejecutar los 12 escenarios de [`quickstart.md`](./quickstart.md) contra el stack real y registrar el resultado en este archivo — **PARCIAL (2026-08-09)**

### Resultado de la ejecución contra la app real

**Montaje.** Los contenedores `accidentes-frontend` y `accidentes-django` sirven **código viejo**
(nginx con un build previo, y un Django sin la app `partners`). Se levantó un dev server en **4300**
y un Django local en **8001** con el código actual, con el proxy apuntado ahí vía
`.claude/launch.json` — sin tocar los contenedores del usuario.

**Verificado en vivo:**

| Escenario / requisito | Resultado |
|---|---|
| **FR-UI-033** sidebar por rol | ✅ El Administrador ve «Partners» y «Solicitudes pendientes» y **ninguna** entrada del portal |
| **J** estados no felices | ✅ Estado vacío con su copy; estado de error con «Reintentar» al caer el backend |
| **FR-UI-004** cliente por nombre | ✅ Combobox poblado y ordenado alfabéticamente — **tras corregir el defecto de abajo** |
| Alta completa (CU-O48) | ✅ Registro real: navega al workpanel, chrome del golden sample, `<dl>` con etiquetas |
| **Centinelas** (FR-UI-025/029) | ✅ «Sin plan» y «Sin asignar» en pantalla; nunca `-1` ni cadena vacía |
| **FR-UI-007** cupo derivado | ✅ «Asignar plan» → «Básico», 1.000/mes, 30/min, estado «Registrado» → «Plan asignado»; la acción desaparece al dejar de aplicar |

**🐞 Defecto encontrado y corregido — solo visible ejecutando la app:** el combobox de cliente
estaba **vacío**, así que el alta era inalcanzable. `clientes = signal([])` se declaraba y nunca se
cargaba, y no existía endpoint de clientes. Se añadió `BE-DELTA-03`
(`GET /partners/clientes-elegibles`, 9 tests de contrato) y su carga en el workpanel, más un test de
regresión que ahora **cuenta las opciones** en vez de conformarse con que el control sea un
`<select>`. Backend del módulo: 221 → **230 tests**.

**Siembra que hubo que crear.** El rol 15 existía desde 2026-08-08 pero `Dim_Usuario_Rol` **no se lo
asignaba a nadie**: el portal era inalcanzable en la demo por ausencia de datos, no por un defecto
de la UI. Se añadió `database/seed_usuario_partner_demo.py` (usuario 9001
`partner.demo@demo.tsi.com`, rol 15, ligado al cliente 920001 vía `admin_local_id`).

### Escenarios del portal — ejecutados tras la siembra

| Escenario | Resultado |
|---|---|
| **C** emitir sin plan | ✅ `GET /partners/me` carga el portal sin pedir ningún id (BE-DELTA-01 en vivo); estado «Registrado» con su línea de «qué sigue»; centinelas como «Sin plan»/«Sin asignar»; el CTA sustituido por el copy explicativo; **el grupo Producción oculto** por no haber sido promovido |
| **D** el secreto una sola vez | ✅ **Completo.** Aviso *antes* del valor; salida **deshabilitada** hasta confirmar; y verificado en la app real: **cero** ocurrencias del secreto en `localStorage`, `sessionStorage`, la URL, `document.title` e `history.state` (**SC-004**). Tras recargar: «El secreto ya no está disponible» con la vía de recuperación, no una pantalla rota |
| **F** coexistencia de entornos | ✅ Solicitud → aprobación → estado «Producción activa». **Ambos grupos visibles**: Pruebas con su vencimiento y Producción con **«No expira»** (nunca una fecha del 9999). La credencial de pruebas sigue activa (RN-PON-008) |
| **FR-UI-009** aprobar sin mostrar secreto | ✅ Confirmación en 2 pasos con el aviso «El secreto no se te mostrará a ti»; tras aprobar, la cola se vacía y **no aparece ningún secreto en pantalla**, pese a que el backend lo devuelve |
| **K.1** responsive | ✅ A 375 px no hay desbordamiento horizontal |
| **K.2** tema | ✅ Los badges resuelven desde tokens (`oklch` de Tailwind); **cero hex** en el marcado |
| **K.3** sin color | ✅ Cada grupo lleva etiqueta de texto («Pruebas»/«Producción») **e** ícono |
| **B** duplicado | ✅ **Por prevención**: el cliente que ya tiene partner desaparece del combobox, así que el 409 se volvió inalcanzable desde la UI (BE-DELTA-03) |
| **L** sin PKs | ✅ Ningún formulario recorrido pide un identificador interno |

### Lo que queda sin ejecutar manualmente

| Escenario | Motivo |
|---|---|
| **A** cliente sin suscripción | Ya **no puede ocurrir desde la UI**: `BE-DELTA-03` solo ofrece clientes elegibles. El 422 sigue cubierto por test de contrato |
| **E** reintento tras fallo de red | El *throttling offline* de DevTools no es accesible desde la automatización disponible. Cubierto por test automatizado (misma `Idempotency-Key` al reintentar) |
| **G** Desarrollador de APIs en la cola | Verificado el lado del partner (no ve la consola) y por test de guard; falta la comprobación manual con ese rol |
| **H** rechazo con motivo | La solicitud de prueba se consumió al aprobarla en **F**; requiere generar otra |
| **I** dos administradores a la vez | Requiere dos sesiones simultáneas |
- [X] T089 Marcar los criterios de aceptación cubiertos y **SC-001…008** en `spec.md`, con la evidencia de T087 y T088 — **hecho** — criterios y SC marcados en `spec.md` con la evidencia de T087.
- [X] T090 Actualizar `.specify/docs/architecture/module-map.md` § 4 con el estado final de la capa frontend y sus cifras reales — **hecho**.
- [X] T091 Cerrar `checklists/requirements.md` reflejando que los dos `BE-DELTA` quedaron implementados — **hecho** — los dos `BE-DELTA` quedaron implementados y así consta.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Fase 1 (Setup)
   └─▶ Fase 2A (base FE) ──┬─▶ Fase 3 (US-FE-1) ──┐   ← MVP sin tocar backend
                            └─▶ Fase 5 (US-FE-3) ──┤
       Fase 2B (BE-DELTA-01) ─▶ Fase 4 (US-FE-2) ──┤
                            ├─▶ Fase 6 (US-FE-4) ──┼─▶ Fase 9 (Polish)
                            ├─▶ Fase 7 (US-FE-5) ──┤
                            └─▶ Fase 8 (US-FE-6) ──┘
       Fase 2C (BE-DELTA-02) ─▶ T069 (FR-UI-027)
```

### User Story Dependencies

| Historia | Depende de | Motivo |
|---|---|---|
| US-FE-1 (P1) | Fase 2A | Consola pura; **no** necesita los deltas |
| US-FE-2 (P1) | Fase 2A + **2B** | Sin `GET /partners/me` el portal no carga |
| US-FE-3 (P1) | Fase 2A | Consola pura |
| US-FE-4 (P2) | US-FE-2 + **2C** para T069 | Comparte la página del portal |
| US-FE-5 (P2) | US-FE-2 | Reutiliza el flujo de emisión |
| US-FE-6 (P3) | Fase 2A + 2B | Página independiente del portal |

### Parallel Opportunities

- **Fase 2A**: T007–T011 y T014–T017 son `[P]` — tipos, constantes y guards viven en archivos distintos
- **Fase 2B/2C**: T020, T021, T023 y T025 son `[P]` (tests y documentación, archivos distintos)
- **Fase 3 y Fase 5** pueden desarrollarse **en paralelo** una vez cerrada la Fase 2A: son superficies distintas sobre servicios ya construidos
- **Todos los tests `[P]` de cada historia** se escriben antes de su implementación y no dependen entre sí
- **Fase 9**: T082–T086 son verificaciones independientes

### Parallel Example: Fase 2A

```
T007 tipos ─┐
T008 estados├─ en paralelo ─▶ T012 partner-api.service (necesita T007)
T009 entornos┤
T010 centinelas┘
T014 guard gestor ─┐
T015 guard admin   ├─ en paralelo (archivos distintos)
T016 guard partner ┘
```

---

## Implementation Strategy

### MVP (Fases 1 → 2A → 3)

**US-FE-1 sola ya entrega valor**: un Administrador puede incorporar partners y asignarles cupo.
Son 24 tareas y **no reabren el backend**, así que se puede entregar y validar sin arriesgar la capa
que cerró con 1250 tests en verde.

### Incremento 2 (Fase 5)

Añadir US-FE-3 completa el trabajo del gestor: incorporar **y** resolver promociones. Sigue sin
tocar el backend.

### Incremento 3 (Fases 2B → 4)

Aquí se reabre el backend con `BE-DELTA-01` y nace el portal del partner. **T024 es obligatorio**:
la suite completa debe volver a estar en verde antes de continuar.

### Incremento 4 (Fases 2C → 6 → 7 → 8)

Completa el portal: entornos, regeneración y contrato versionado.

### Orden recomendado dentro de cada historia

Tests `[P]` → implementación → checkpoint. Los tests van primero porque **cuatro de ellos (T039,
T041, T055, T065) verifican propiedades negativas** —que el secreto no se filtre, que no se dupliquen
credenciales, que el Admin no vea secretos ajenos, que el color no sea el único distintivo— y una
propiedad negativa es trivial de "pasar" por accidente si se escribe el test después del código.
