# Tasks: Informes Compuestos de Soporte al Cliente — Frontend

**Input**: Design documents from `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: reusar el guard de listados deja entrar al Cliente; pintar el 11 % sin cobertura afirma una crisis; sumar automático y humano borra la señal; un envelope copiado de Ventas deja las zonas vacías con 200. Las pruebas existen para eso.

**Organization**: agrupadas por user story de [`spec.md`](spec.md). US1, US2 y US4 son P1; US3 es P2. El MVP es US1 (Cumplimiento) más el alcance visible (cáscara + US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US4 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Acotamiento por titularidad.** Como Ventas, no como Suscripciones: Gerente y agente ven las **mismas** tres historias; `meta.acotado_a` tiene que verse. Inferirlo del rol en el cliente se desincroniza del backend.

**Tres pantallas nuevas, no los listados ni el dashboard operativo.** `/soporte-cliente/informes` y `/soporte-cliente/dashboard` se ignoran. El guard de listados admite Cliente; el de cola/dashboard **no incluye al Gerente** e incluye `DesarrolladorAPIs` / `DirectorTecnologico`, que el backend de compuestos **no** admite.

**El envelope no es el de Ventas.** `data` es `{ resultados, declaraciones }`, no un array. Copiar `EnvelopeInforme.data: Record[]` deja las zonas vacías con 200 OK (D5).

**Una cáscara Z copiada, no extraída.** No se toca `emergencias/gestion` ni `ventas-crm/gestion` (D1).

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Reusar `informesTicketsGuard` o `agenteSoporteGuard`** | El primero admite Cliente; el segundo deja fuera al Gerente y mete roles 403 (D2, FR-UI-022) |
| **Pintar cumplimiento sin `pct_sin_compromiso` en el mismo bloque** | El 11 % solo se lee como crisis; es el incentivo que FR-013 ya impide (D7, FR-UI-008) |
| **Sumar automático + humano, o pintar `resultados: []` como 0 %** | Borra la señal de SLA o dispara una alarma BSC falsa (D16, D15) |
| **Resolver `id_agente` / `id_cliente` a un nombre, o abrir el detalle del ticket** | Salta Depends-on y reintroduce asunto/mensajes (D14, FR-UI-019) |

**Depends-on**: los 9 publicados del backend. Esta capa no calcula cifras ni toca OpenAPI. No extrae la cáscara Z a `shared/` (D1).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con listados, dashboard, cola del agente ni `emergencias/gestion`.

- [X] T001 Crear el árbol `frontend/src/app/modules/soporte-cliente/gestion/{guards,definiciones,services,models,pages}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en `frontend/src/app/modules/soporte-cliente/informes/` ni en `pages/dashboard-soporte/` ni en `pages/cola-agente/`
- [X] T002 [P] Crear `frontend/src/app/modules/soporte-cliente/gestion/models/informes-compuestos.types.ts` con `PeriodoVista`, `EstadoZona` (`carga | dato | vacio | error | sin_dato`), `DefinicionPantalla` (`id`: `cumplimiento` \| `cola` \| `tendencias`), `CuerpoInforme` (`resultados`, `declaraciones`) y `MetaInforme` con `acotado_a` (`todos` \| `propios`) según [`data-model.md`](data-model.md). **`data` no es un array** (D5)
- [X] T003 [P] Crear `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.ts` con `PUBLICADOS_UI` (los **9** slugs de `CATALOGO` en `backend/apps/informes_tacticos/services/soporte_compuestos_service.py`) y el esqueleto `PANTALLAS` con los tres `id`. Las zonas se rellenan en US1–US3. Incluir `RUTA_HTTP` con `cumplimiento-sla-por-plan` → `cumplimiento-sla/por-plan` (D6)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: cáscara Z, HTTP, guard y rutas. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: si el guard copia el de listados, US1 «pasa» para el Cliente. Si copia el de la cola, el Gerente no entra. La prueba de esta fase es esa exclusión, no solo la entrada.

- [X] T004 Implementar `frontend/src/app/modules/soporte-cliente/gestion/services/informes-compuestos-api.service.ts`: un `GET` parametrizado a `/api/v1/informes-tacticos/soporte/{ruta}?desde=&hasta=` usando `RUTA_HTTP`. **Un método, no nueve.** No envía `granularidad`, `eje` ni `minimo` (D9). `agrupar_por` es query **opcional** del mismo método, solo cuando la zona del tablero lo pide
- [X] T005 [P] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/services/informes-compuestos-api.service.spec.ts` de que `cumplimiento-sla-por-plan` pega a `…/cumplimiento-sla/por-plan` (no al slug con guiones), de que el prefijo es `soporte` (no `ventas-crm`), de que **no** hay un método por informe, y de que el GET por defecto **no** manda `granularidad`
- [X] T006 Crear `frontend/src/app/modules/soporte-cliente/gestion/guards/soporte-gestion.guard.ts` con **solo** `GerenteExitoCliente`, `Soporte` y `Administrador` (D2). No autenticado → login; otro rol → `access-denied`. **Prohibido** incluir `Cliente`, `DesarrolladorAPIs` o `DirectorTecnologico`
- [X] T007 ⚠️ Prueba en `frontend/src/app/modules/soporte-cliente/gestion/guards/soporte-gestion.guard.spec.ts`: **Cliente, Operador, DesarrolladorAPIs y DirectorTecnologico denegados**; **GerenteExitoCliente, Soporte y Administrador pasan**. Un guard copiado de listados o de cola fallaría esta prueba en silencio
- [X] T008 Crear `frontend/src/app/modules/soporte-cliente/gestion/models/estado-zona.ts`: `resultados: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. **Nunca** mapear vacío a 0. Conservar `meta.acotado_a` y `declaraciones` también en `vacio`. Una fila de serie con `tickets = 0` o `creados = 0` es **dato**, no vacío (D15)
- [X] T009 [P] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/models/estado-zona.spec.ts` de que `{ resultados: [] }` no es `dato` con ceros, de que `pct_cumplimiento: null` es `sin_dato` y no `0`, de que `{ resultados: [{ tickets: 0 }] }` es `dato`, y de que un envelope vacío **sigue exponiendo** `acotado_a`
- [X] T010 Implementar la cáscara `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`: una sola página, resuelve `PANTALLAS` por el segmento de ruta, pinta las zonas con `data-testid` `zona-heroe`, `zona-periodo`, `zona-alcance`, `zona-visual`, `zona-lectura`. Reutilizar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.ts`. **Prohibido** importar `InformeCardComponent`. Cada zona dispara su GET en paralelo (D11) salvo el caso D10 (un GET, dos zonas) que se cablea en US3. `zona-alcance` pinta `meta.acotado_a` del envelope, **no** el rol (D4). Pintar `declaraciones[].mensaje` junto a la zona
- [X] T011 Prueba en `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.spec.ts`: un error en una zona deja las otras visibles; cambiar el período vuelve a pedir **todas** las zonas de la definición; `acotado_a: 'propios'` se lee en `zona-alcance` aunque el usuario mockeado sea Gerente
- [X] T012 Crear `frontend/src/app/modules/soporte-cliente/gestion/soporte-cliente-gestion.routes.ts` con `cumplimiento`, `cola`, `tendencias` → la misma `PantallaZPage`, `canActivate: [soporteGestionGuard]` (D3)
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'soporte-cliente/gestion'`. **No** colgar estas rutas de `frontend/src/app/modules/soporte-cliente/soporte-cliente.routes.ts` ni de `informes/soporte-cliente-informes.routes.ts`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/soporte-cliente/gestion/soporte-cliente-gestion-cableado.spec.ts`: las tres rutas de gestión usan `soporteGestionGuard`; `soporte-cliente-informes.routes.ts` y `soporte-cliente.routes.ts` **no** cambian de guard ni ganan pantallas Z; `dashboard` sigue con `agenteSoporteGuard`

**Checkpoint**: foundation ready — se puede abrir la cáscara (vacía de cifras) solo con Gerente / agente / Admin.

---

## Phase 3: User Story 1 — Cumplimiento de SLA (Priority: P1) 🎯 MVP

**Goal**: el Gerente ve si se atiende dentro de lo comprometido. El par cumplimiento/cobertura **en el mismo bloque**, con meta ≥95 %; desglose por plan; rendimiento por **clave** de agente con reaperturas; tickets por servicio plegados.

**Independent Test**: no existe un estado de pantalla con el % de cumplimiento y sin el % sin compromiso en el mismo bloque. Reapertura visible, no infla resoluciones. Operador/Cliente no entran. Período 1999 → vacío, no 0 %. Vista principal ≤ 8 bloques.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `cumplimiento` cita exactamente `cumplimiento-sla`, `cumplimiento-sla-por-plan`, `rendimiento-agentes`, `tickets-por-servicio`
- [X] T016 [US1] En `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.spec.ts`: `resultados: []` no pinta 0 %; `pct_cumplimiento` y `pct_sin_compromiso` están **ambos** en `zona-heroe`; `pct_cumplimiento: null` → «sin dato»; `reabiertos` visible; `id_agente` como clave **sin** nombre; las `data-testid` del Z (incluido `zona-alcance`) están presentes; recuento de bloques de la vista principal ≤ 8
- [X] T017 [P] [US1] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/pages/apoyo-plegable.component.spec.ts`: el bloque nace **plegado**; al abrirse muestra «sin servicio» y no sustituye el visual grande

### Implementation for User Story 1

- [X] T018 [US1] Crear `frontend/src/app/modules/soporte-cliente/gestion/pages/apoyo-plegable.component.ts` (y template) para tickets por servicio (D12)
- [X] T019 [US1] Rellenar la definición `cumplimiento` en `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T020 [US1] Pintar las zonas de cumplimiento en `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Héroe = **última** fila del par + motivos en tamaño menor (D7). Barras Tailwind (D8). Rendimiento: `id_agente` como clave, **sin** nombre y **sin** enlace a `/soporte-cliente/tickets/` (D14). Servicio plegado
- [X] T021 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Cumplimiento de SLA» → `/soporte-cliente/gestion/cumplimiento`, roles `GerenteExitoCliente`, `Soporte`, `Administrador`, grupo Soporte. **No** tocar «Informes de soporte», «Dashboard de soporte», «Cola de soporte» ni «Mis tickets»
- [X] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–2 (Gerente entra, Cliente no; el par no se rompe; 1999 vacío)

**Checkpoint**: US1 usable sola. Cola y tendencias aún no tienen enlace. El alcance ya se pinta (cáscara); US4 comprueba los valores.

---

## Phase 4: User Story 4 — El agente ve lo mismo, acotado, y lo sabe (Priority: P1)

**Goal**: el agente entra a las mismas pantallas con `acotado_a: propios` visible. El Gerente lee `todos`. Cliente no ve los enlaces ni entra.

**Independent Test**: mismo URL de Cumplimiento: Gerente → todos; agente → propios, pintado desde el envelope. Cliente → access-denied y **cero** enlaces `/soporte-cliente/gestion/*` en el sidebar.

### Tests for User Story 4 ⚠️ escribir primero, deben FALLAR

- [X] T023 [P] [US4] En `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.spec.ts`: envelope `acotado_a: 'propios'` pinta propios **aunque** el rol mockeado sea `GerenteExitoCliente`; `todos` pinta todos con rol `Soporte`. El alcance no se infiere del rol (D4)
- [X] T024 [US4] En `frontend/src/app/modules/soporte-cliente/gestion/soporte-cliente-gestion-cableado.spec.ts` (o spec de `nav-links`): los paths `/soporte-cliente/gestion/*` **no** incluyen `Cliente` ni `DesarrolladorAPIs` en `roles`; sí incluyen Gerente, Soporte y Administrador. `/soporte-cliente/informes` **sigue** admitiendo Cliente. `/soporte-cliente/dashboard` **sigue** con los roles de la cola operativa

### Implementation for User Story 4

- [X] T025 [US4] Ajustar `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html` si hace falta para que `zona-alcance` tome `acotado_a` de la primera zona con `meta`, no de `AuthService.roles`
- [X] T026 [US4] Recorrer [`quickstart.md`](quickstart.md) §1 y §3 (Gerente entra y Cliente no; agente ve propios)

**Checkpoint**: el acotamiento se ve. US2 y US3 heredan `zona-alcance` sin reimplementarla.

---

## Phase 5: User Story 2 — Cola en curso (Priority: P1)

**Goal**: tablero **con período** (no es el dashboard operativo); evolución con días en cero presentes; escalado automático y humano **por separado**. `agrupar_por` es control de la zona, no filtro global.

**Independent Test**: dos períodos distintos cambian el tablero. Un día sin tickets está en cero. No hay un total que sume los dos escalados. El dashboard operativo sigue existiendo y no se parece a esta pantalla.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T027 [P] [US2] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `cola` cita exactamente `tablero-cola`, `evolucion-incumplimiento`, `escalado-automatico`
- [X] T028 [US2] En `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.spec.ts`: cambiar `agrupar_por` re-pide **solo** `tablero-cola` (no las otras zonas); una fila de evolución con `tickets: 0` se pinta (no se omite); el template **no** contiene un total `escalados` ni suma las dos columnas; la declaración `periodo_acotado_difiere_del_tablero` se lee si viene; **no** hay enlace a `/soporte-cliente/dashboard` ni a `/soporte-cliente/tickets/`

### Implementation for User Story 2

- [X] T029 [US2] Rellenar la definición `cola` en `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md). Sin apoyo
- [X] T030 [US2] Pintar las zonas de cola en `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Control `agrupar_por` **dentro** de `zona-heroe` (D9). Serie de evolución sin omitir ceros (D15). Escalado: dos columnas, **sin** suma (D16). Si `agrupar_por=agente`, `clave` es id, no nombre
- [X] T031 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Cola en curso» → `/soporte-cliente/gestion/cola`, mismos roles que Cumplimiento. **No** reetiquetar «Dashboard de soporte»
- [X] T032 [US2] Recorrer [`quickstart.md`](quickstart.md) §4

**Checkpoint**: US1, US4 y US2 independientes. Tendencias aún sin enlace.

---

## Phase 6: User Story 3 — Tendencias (Priority: P2)

**Goal**: saldo/acumulado del último día como héroe; carga diaria (mismo GET) como visual, con días en cero; reincidencia por **clave** de cliente y tipo de incidencia, con el hueco de servicio declarado. Sin columna de servicio.

**Independent Test**: período sin tickets → vacío, no acumulado 0. Ninguna zona se titula por servicio. Vista principal ≤ 8 bloques.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T033 [P] [US3] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `tendencias` cita exactamente `carga-entrante-resuelta` y `reincidencia-clientes`
- [X] T034 [US3] En `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.spec.ts`: un solo GET de `carga-entrante-resuelta` alimenta héroe y visual (D10); días con `creados: 0` permanecen; `id_cliente` como clave **sin** nombre; el template **no** contiene una columna `servicio` ni el título «reincidencia por servicio»; `resultados: []` → vacío, no 0

### Implementation for User Story 3

- [X] T035 [US3] Rellenar la definición `tendencias` en `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md). Héroe y visual apuntan al **mismo** informe
- [X] T036 [US3] Pintar las zonas de tendencias en `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Un GET compartido (D10). Saldo del último día = `creados - resueltos` de esa fila, sin recalcular el acumulado. Declaración `eje_servicio_sustituido` / `servicio_no_registrado` visible
- [X] T037 [US3] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Tendencias» → `/soporte-cliente/gestion/tendencias`, mismos roles
- [X] T038 [US3] Recorrer [`quickstart.md`](quickstart.md) §6

**Checkpoint**: las tres historias independientes y el patrón Z es el mismo tres veces.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido en una sola pantalla dejaría mentir al Gerente o al agente, o reabriría el tablero operativo.

- [X] T039 [P] Completar `frontend/src/app/modules/soporte-cliente/gestion/definiciones/pantallas-gestion.definiciones.spec.ts`: las tres pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 9; ningún slug de listados simples (`tickets`, `escalados`)
- [X] T040 [P] Prueba en `frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.spec.ts` de que **no** hay mapa, `leaflet`, exportar, botón de asignar/responder/escalar/cerrar, texto de asunto/mensaje, ni enlace a `/soporte-cliente/tickets/` (FR-UI-019, FR-UI-021, FR-UI-024)
- [X] T041 Verificar que `frontend/src/app/modules/soporte-cliente/informes/`, `pages/dashboard-soporte/`, `pages/cola-agente/` y `pages/configuracion-sla/` **no** ganan tarjetas Z. Diff vacío en esos árboles salvo lo ajeno a esta capa
- [X] T042 Ejecutar la suite del frontend (`ng test` del módulo `soporte-cliente/gestion` / afectados) y `ng build` de producción sin errores nuevos
- [X] T043 Reconstruir `accidentes-frontend` con `docker compose -f docker/accidentes.yml up -d --build frontend` (el frontend se sirve desde nginx; no hay hot-reload) y comprobar `docker ps --filter name=accidentes-` ambos `Up`
- [X] T044 Recorrer [`quickstart.md`](quickstart.md) §5, §7 y §8: fallo aislado; listados, cola y dashboard intactos; `DesarrolladorAPIs` no gana gestión; ninguna identidad ni mapa
- [X] T045 Documentar hallazgos en `.specify/docs/changelog.md` y marcar la capa frontend en `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/informes-compuestos-modelo.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — **bloquea** US1–US4
- **US1 (Phase 3)**: depende de Phase 2 — MVP de cifras
- **US4 (Phase 4)**: depende de Phase 2 y de que Cumplimiento exista para recorrerla; no necesita US2/US3
- **US2 (Phase 5)**: depende de Phase 2; hereda `zona-alcance`
- **US3 (Phase 6)**: depende de Phase 2; no necesita apoyo plegado
- **Polish (Phase 7)**: las historias hechas

### User Story Dependencies

- **US1 (P1)**: tras Phase 2. Entregable solo (cumplimiento + apoyo plegado).
- **US4 (P1)**: tras US1 para el recorrido; las pruebas de `acotado_a` pueden escribirse en cuanto exista la cáscara (T010).
- **US2 (P1)**: tras Phase 2. Extiende la misma página; no rompe Cumplimiento.
- **US3 (P2)**: tras Phase 2. Añade zonas de tendencias; no cambia el héroe de US1/US2.

US1, US2, US3 y US4 tocan `pantalla-z.page.ts` y `nav-links.ts`: en un solo implementador, **secuencial US1 → US4 → US2 → US3**.

### Within Each User Story

- Pruebas primero y en rojo
- Definición de pantalla antes de pintar
- Pintado antes del enlace de sidebar (no anunciar una ruta vacía)
- Recorrido en navegador al cerrar la historia

### Parallel Opportunities

- T002 y T003
- T005, T007, T009 (tras existir los ficheros que prueban)
- T014 con T011–T013 cuando las rutas ya están
- T015, T016 y T017
- T023 en paralelo con T024
- T027 en paralelo con T028
- T033 en paralelo con T034
- T039 y T040 en Polish

---

## Parallel Example: User Story 1

```text
Task: "Prueba slugs de cumplimiento en definiciones/pantallas-gestion.definiciones.spec.ts"
Task: "Prueba par cobertura y vacío ≠ 0% en pages/pantalla-z.page.spec.ts"
Task: "Prueba apoyo plegado en pages/apoyo-plegable.component.spec.ts"
```

Luego, en serie: `apoyo-plegable` → rellenar `cumplimiento` → pintar zonas → `nav-links` → quickstart §1–2.

---

## Implementation Strategy

### MVP First (User Story 1 + alcance)

1. Phase 1 + Phase 2
2. Phase 3 (Cumplimiento de SLA)
3. Phase 4 (alcance propios / todos)
4. **STOP**: Gerente ve el par cumplimiento/cobertura; agente ve propios; Cliente no entra
5. Demo / validar SC-F01, SC-F02, SC-F03, SC-F09, SC-F11

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo MVP de cifras
3. US4 → el acotamiento se ve
4. US2 → cola con período, distinta del dashboard
5. US3 → tendencias sin fingir servicio
6. Polish (9 slugs, listados/dashboard intactos, Docker)

### Parallel Team Strategy

Un solo implementador: US1 → US4 → US2 → US3 por el fichero compartido `pantalla-z.page.ts`.

Si hay dos: A hace US1+US4; B prepara definiciones y pruebas de US2/US3 (ficheros `*.spec.ts` y el relleno de `PANTALLAS`) y se integra después de US1.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- No hay librería de charts (D8)
- `acotado_a` **sí** viene en el envelope; no se adivina (D4)
- `declaraciones` se muestran, no se filtran por el enum del OpenAPI (D5)
- El recorrido en navegador (T022, T026, T032, T038, T044) no lo sustituye Karma: el proxy, el guard real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T043)
