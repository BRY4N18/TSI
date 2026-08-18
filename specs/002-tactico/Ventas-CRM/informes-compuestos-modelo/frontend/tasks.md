# Tasks: Informes Compuestos de Ventas y CRM — Frontend

**Input**: Design documents from `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: reusar el guard de listados deja entrar a Cuentas Públicas; pintar OT03 vacío como 0 % afirma que se midió el producto; titular «CAC» completa un indicador que el sistema no tiene. Las pruebas existen para eso.

**Organization**: agrupadas por user story de [`spec.md`](spec.md). US1, US2 y US4 son P1; US3 es P2. El MVP es US1 (Embudo) más el alcance visible (cáscara + US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US4 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Acotamiento por titularidad.** Emergencias y Red Operativa no lo tienen en compuestos. Aquí Director y Gerente de Ventas ven las **mismas** tres historias; `meta.acotado_a` tiene que verse. Inferirlo del rol en el cliente se desincroniza del backend.

**Tres pantallas nuevas, no los listados ni el pipeline.** `/ventas-crm/informes` y `/ventas-crm/pipeline` se ignoran. El guard de listados admite `GerenteCuentasPublicas`; el de compuestos **no**.

**Una cáscara Z copiada, no extraída.** No se toca `emergencias/gestion` ni `red-operativa/gestion` (D1).

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Reusar `informes-ventas-crm.guard`** | Admite Cuentas Públicas; el backend de compuestos responde 403 (D2, FR-UI-019) |
| **Titular CAC o pintar coste** | Completa un indicador que el sistema no sostiene (D6, FR-UI-013) |
| **Mostrar 0 % en `data: []` de nutrición** | Convierte «no hubo demos» en «hubo y no se usó» (D12, FR-UI-014) |
| **Resolver `idejecutivo` a un nombre** | Salta Depends-on y la exclusión constitucional (D11, FR-UI-017) |

**Depends-on**: los 13 publicados del backend. Esta capa no calcula cifras ni toca OpenAPI. No extrae la cáscara Z a `shared/` (D1).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con listados, pipeline ni `emergencias/gestion`.

- [X] T001 Crear el árbol `frontend/src/app/modules/ventas-crm/gestion/{guards,definiciones,services,models,pages}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en `frontend/src/app/modules/ventas-crm/informes/` ni en `pages/pipeline-board/`
- [X] T002 [P] Crear `frontend/src/app/modules/ventas-crm/gestion/models/informes-compuestos.types.ts` con `PeriodoVista`, `EstadoZona` (`carga | dato | vacio | error | sin_dato`), `DefinicionPantalla` (`id`: `embudo` \| `captacion` \| `nutricion`) y `MetaInforme` con `acotado_a` (`todos` \| `propios`) y `filtros` según [`data-model.md`](data-model.md)
- [X] T003 [P] Crear `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.ts` con `PUBLICADOS_UI` (los **13** slugs de `CATALOGO` en `backend/apps/informes_tacticos/services/ventas_crm_compuestos_service.py`) y el esqueleto `PANTALLAS` con los tres `id`. Las zonas se rellenan en US1–US3

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: cáscara Z, HTTP, guard y rutas. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: si el guard copia el de listados, US1 «pasa» para Cuentas Públicas. La prueba de esta fase es esa exclusión, no solo la entrada.

- [X] T004 Implementar `frontend/src/app/modules/ventas-crm/gestion/services/informes-compuestos-api.service.ts`: un `GET` parametrizado a `/api/v1/informes-tacticos/ventas-crm/{informe}?desde=&hasta=`. **Un método, no trece.** No envía `pesos_etapa` ni `top` (D7)
- [X] T005 [P] Prueba en `frontend/src/app/modules/ventas-crm/gestion/services/informes-compuestos-api.service.spec.ts` de que la URL incluye el slug y el período, el prefijo es `ventas-crm` (no `emergencias`), y de que **no** hay un método por informe
- [X] T006 Crear `frontend/src/app/modules/ventas-crm/gestion/guards/ventas-crm-gestion.guard.ts` con **solo** `DirectorMarketing`, `GerenteVentas` y `Administrador` (D2). No autenticado → login; otro rol → `access-denied`. **Prohibido** incluir `GerenteCuentasPublicas`
- [X] T007 ⚠️ Prueba en `frontend/src/app/modules/ventas-crm/gestion/guards/ventas-crm-gestion.guard.spec.ts`: **GerenteCuentasPublicas, Operador y Cliente denegados**; **DirectorMarketing, GerenteVentas y Administrador pasan**. Un guard copiado de listados fallaría esta prueba en silencio
- [X] T008 Crear `frontend/src/app/modules/ventas-crm/gestion/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. **Nunca** mapear vacío a 0. Conservar `meta.acotado_a` también en `vacio`
- [X] T009 [P] Prueba en `frontend/src/app/modules/ventas-crm/gestion/models/estado-zona.spec.ts` de que `[]` no es `dato` con ceros, de que `pct_conversion: null` es `sin_dato` y no `0`, y de que un envelope vacío **sigue exponiendo** `acotado_a`
- [X] T010 Implementar la cáscara `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`: una sola página, resuelve `PANTALLAS` por el segmento de ruta, pinta las zonas con `data-testid` `zona-heroe`, `zona-periodo`, `zona-alcance`, `zona-visual`, `zona-lectura`. Reutilizar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.ts`. **Prohibido** importar `InformeCardComponent`. Cada zona dispara su GET en paralelo (D8). `zona-alcance` pinta `meta.acotado_a` del envelope, **no** el rol (D4)
- [X] T011 Prueba en `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.spec.ts`: un error en una zona deja las otras visibles; cambiar el período vuelve a pedir **todas** las zonas de la definición; `acotado_a: 'propios'` se lee en `zona-alcance` aunque el usuario mockeado sea Director
- [X] T012 Crear `frontend/src/app/modules/ventas-crm/gestion/ventas-crm-gestion.routes.ts` con `embudo`, `captacion`, `nutricion` → la misma `PantallaZPage`, `canActivate: [ventasCrmGestionGuard]` (D3)
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'ventas-crm/gestion'`. **No** colgar estas rutas de `frontend/src/app/modules/ventas-crm/ventas-crm.routes.ts` ni de `informes/ventas-crm-informes.routes.ts`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/ventas-crm/gestion/ventas-crm-gestion-cableado.spec.ts`: las tres rutas de gestión usan `ventasCrmGestionGuard`; `ventas-crm-informes.routes.ts` **no** cambia de guard ni gana pantallas Z

**Checkpoint**: foundation ready — se puede abrir la cáscara (vacía de cifras) solo con Director / Gerente de Ventas / Admin.

---

## Phase 3: User Story 1 — Embudo comercial (Priority: P1) 🎯 MVP

**Goal**: el Director ve dónde se atasca el pipeline. Paso entre etapas como héroe; permanencia con tramo abierto (el estancado es el más lento); motivos **con etapa de abandono**; carga y pipeline plegados, pesos como convención.

**Independent Test**: período con un estancado → `abiertos` visible y esa etapa no parece la más rápida. Convertido y perdido no son un grupo de inactivos. Operador no entra. Período 1999 → vacío, no 0 %. Vista principal ≤ 8 bloques.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `embudo` cita exactamente `embudo-conversion`, `permanencia-por-etapa`, `motivos-perdida`, `carga-por-ejecutivo`, `pipeline-ponderado`
- [X] T016 [US1] En `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.spec.ts`: `data: []` no pinta 0 %; `abiertos` se muestra; no hay etiqueta «inactivos»; `nota_pesos` visible al abrir el apoyo; las `data-testid` del Z (incluido `zona-alcance`) están presentes
- [X] T017 [P] [US1] Prueba en `frontend/src/app/modules/ventas-crm/gestion/pages/apoyo-plegable.component.spec.ts`: el bloque nace **plegado**; al abrirse muestra carga y pipeline y no sustituye el visual grande

### Implementation for User Story 1

- [X] T018 [US1] Crear `frontend/src/app/modules/ventas-crm/gestion/pages/apoyo-plegable.component.ts` (y template) para carga por ejecutivo y pipeline ponderado (D9)
- [X] T019 [US1] Rellenar la definición `embudo` en `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T020 [US1] Pintar las zonas de embudo en `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Barras Tailwind (D5). Carga: `idejecutivo` como clave, **sin** nombre (D11). Pipeline: `meta.filtros.nota_pesos` junto a la cifra (D7)
- [X] T021 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Embudo comercial» → `/ventas-crm/gestion/embudo`, roles `DirectorMarketing`, `GerenteVentas`, `Administrador`, grupo Ventas CRM. **No** tocar «Informes comerciales», Prospectos ni Pipeline
- [X] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §3 (estancado; 1999 vacío)

**Checkpoint**: US1 usable sola. Captación y nutrición aún no tienen enlace. El alcance ya se pinta (cáscara); US4 comprueba los valores.

---

## Phase 4: User Story 4 — El ejecutivo ve lo mismo, acotado, y lo sabe (Priority: P1)

**Goal**: Gerente de Ventas entra a las mismas pantallas con `acotado_a: propios` visible. El Director lee `todos`. Cuentas Públicas no ve los enlaces ni entra.

**Independent Test**: mismo URL de Embudo: Director → todos; Gerente → propios, pintado desde el envelope. Cuentas Públicas → access-denied y **cero** enlaces `/ventas-crm/gestion/*` en el sidebar.

### Tests for User Story 4 ⚠️ escribir primero, deben FALLAR

- [X] T023 [P] [US4] En `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.spec.ts`: envelope `acotado_a: 'propios'` pinta propios **aunque** el rol mockeado sea `DirectorMarketing`; `todos` pinta todos con rol `GerenteVentas`. El alcance no se infiere del rol (D4)
- [X] T024 [US4] En `frontend/src/app/modules/ventas-crm/gestion/ventas-crm-gestion-cableado.spec.ts` (o spec de `nav-links`): los tres paths `/ventas-crm/gestion/*` **no** incluyen `GerenteCuentasPublicas` en `roles`; sí incluyen Director, Gerente de Ventas y Administrador. `/ventas-crm/informes` **sigue** admitiendo Cuentas Públicas

### Implementation for User Story 4

- [X] T025 [US4] Ajustar `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html` si hace falta para que `zona-alcance` tome `acotado_a` de la primera zona con `meta`, no de `AuthService.roles`
- [X] T026 [US4] Recorrer [`quickstart.md`](quickstart.md) §1–2 (Director entra y Cuentas Públicas no; Gerente ve propios)

**Checkpoint**: el acotamiento se ve. US2 y US3 heredan `zona-alcance` sin reimplementarla.

---

## Phase 5: User Story 2 — Captación por canal (Priority: P1)

**Goal**: volumen (Desconocido suma) como héroe; tasa con denominador; convertidos con `nota_indicador`. **No** se titula CAC ni se pinta coste.

**Independent Test**: suma de canales = total. Ninguna zona se llama CAC. Canal sin prospectos → sin dato, no 0 %.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T027 [P] [US2] Prueba en `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `captacion` cita exactamente `captacion-por-canal`, `conversion-por-canal`, `convertidos-por-canal`
- [X] T028 [US2] En `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.spec.ts`: fila `Desconocido` visible si viene en `data`; `pct_conversion: null` → «sin dato»; `nota_indicador` visible; el template **no** contiene `CAC`, `coste` ni `costo`

### Implementation for User Story 2

- [X] T029 [US2] Rellenar la definición `captacion` en `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md). Sin apoyo
- [X] T030 [US2] Pintar las zonas de captación en `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. La nota del indicador va **junto a** los convertidos (D6)
- [X] T031 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Captación por canal» → `/ventas-crm/gestion/captacion`, mismos roles que Embudo
- [X] T032 [US2] Recorrer [`quickstart.md`](quickstart.md) §4

**Checkpoint**: US1, US4 y US2 independientes. Nutrición aún sin enlace.

---

## Phase 6: User Story 3 — Nutrición del prospecto (Priority: P2)

**Goal**: efectividad en dos grupos con denominador; uso de demo por **empresa** (no ficha de `idprospecto`); latencia con ignorados fuera de la mediana; reglas de disparo plegadas. Vacío de entorno ≠ tablero de ceros.

**Independent Test**: período sin demos → vacío explícito. Aviso sin avance no aparece como latencia 0. Vista principal ≤ 8 bloques.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T033 [P] [US3] Prueba en `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `nutricion` cita exactamente `efectividad-nutricion`, `intensidad-demo`, `secciones-visitadas`, `latencia-reaccion`, `reglas-disparo`
- [X] T034 [US3] En `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.spec.ts`: `data: []` en efectividad → vacío, no 0 %; `sin_reaccion` no entra a la mediana pintada; el visual de intensidad usa `empresa` y **no** titula con `idprospecto`; recuento de bloques de la vista principal ≤ 8; reglas viven en `zona-apoyo` plegado

### Implementation for User Story 3

- [X] T035 [US3] Rellenar la definición `nutricion` en `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T036 [US3] Pintar las zonas de nutrición en `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Reutilizar `apoyo-plegable.component.ts` para `reglas-disparo` (D9, D12, D13)
- [X] T037 [US3] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Nutrición del prospecto» → `/ventas-crm/gestion/nutricion`, mismos roles
- [X] T038 [US3] Recorrer [`quickstart.md`](quickstart.md) §6

**Checkpoint**: las tres historias independientes y el patrón Z es el mismo tres veces.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido en una sola pantalla dejaría mentir al Director o al ejecutivo.

- [X] T039 [P] Completar `frontend/src/app/modules/ventas-crm/gestion/definiciones/pantallas-gestion.definiciones.spec.ts`: las tres pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 13; ningún slug de listados simples
- [X] T040 [P] Prueba en `frontend/src/app/modules/ventas-crm/gestion/pages/pantalla-z.page.spec.ts` de que **no** hay mapa, `leaflet`, exportar, botón de asignar/transicionar/disparar, ni texto `CAC` (FR-UI-013, FR-UI-016, FR-UI-018, FR-UI-021)
- [X] T041 Verificar que `frontend/src/app/modules/ventas-crm/informes/` y `frontend/src/app/modules/ventas-crm/pages/pipeline-board/` **no** ganan tarjetas Z. Diff vacío en esos árboles salvo lo ajeno a esta capa
- [X] T042 Ejecutar la suite del frontend (`ng test` del módulo `ventas-crm/gestion` / afectados) y `ng build` de producción sin errores nuevos
- [X] T043 Reconstruir `accidentes-frontend` con `docker compose -f docker/accidentes.yml up -d --build frontend` (el frontend se sirve desde nginx; no hay hot-reload)
- [X] T044 Recorrer [`quickstart.md`](quickstart.md) §5, §7 y §8: fallo aislado; listados y pipeline intactos; ninguna identidad ni mapa
- [X] T045 Documentar hallazgos en `.specify/docs/changelog.md` y marcar la capa frontend en `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/informes-compuestos-modelo.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — **bloquea** US1–US4
- **US1 (Phase 3)**: depende de Phase 2 — MVP de cifras
- **US4 (Phase 4)**: depende de Phase 2 y de que Embudo exista para recorrerla; no necesita US2/US3
- **US2 (Phase 5)**: depende de Phase 2; hereda `zona-alcance`
- **US3 (Phase 6)**: depende de Phase 2; reutiliza `apoyo-plegable` de US1
- **Polish (Phase 7)**: las historias hechas

### User Story Dependencies

- **US1 (P1)**: tras Phase 2. Entregable solo (embudo + apoyo plegado).
- **US4 (P1)**: tras US1 para el recorrido; las pruebas de `acotado_a` pueden escribirse en cuanto exista la cáscara (T010).
- **US2 (P1)**: tras Phase 2. Extiende la misma página; no rompe Embudo.
- **US3 (P2)**: tras Phase 2. Añade zonas de nutrición; no cambia el héroe de US1/US2.

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
Task: "Prueba slugs de embudo en definiciones/pantallas-gestion.definiciones.spec.ts"
Task: "Prueba vacío ≠ 0%, abiertos y no-inactivos en pages/pantalla-z.page.spec.ts"
Task: "Prueba apoyo plegado en pages/apoyo-plegable.component.spec.ts"
```

Luego, en serie: `apoyo-plegable` → rellenar `embudo` → pintar zonas → `nav-links` → quickstart §3.

---

## Implementation Strategy

### MVP First (User Story 1 + alcance)

1. Phase 1 + Phase 2
2. Phase 3 (Embudo comercial)
3. Phase 4 (alcance propios / todos)
4. **STOP**: Director ve el embudo honesto; Gerente ve propios; Cuentas Públicas no entra
5. Demo / validar SC-F01, SC-F02, SC-F03, SC-F09, SC-F11

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo MVP de cifras
3. US4 → el acotamiento se ve
4. US2 → captación sin CAC inventado
5. US3 → nutrición vacía honesta
6. Polish (13 slugs, listados intactos, Docker)

### Parallel Team Strategy

Un solo implementador: US1 → US4 → US2 → US3 por el fichero compartido `pantalla-z.page.ts`.

Si hay dos: A hace US1+US4; B prepara definiciones y pruebas de US2/US3 (ficheros `*.spec.ts` y el relleno de `PANTALLAS`) y se integra después de US1.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- No hay librería de charts (D5)
- `acotado_a` **sí** viene en el envelope; no se adivina (D4)
- `nota_indicador` y `nota_pesos` se muestran, no se reescriben (D6, D7)
- El recorrido en navegador (T022, T026, T032, T038, T044) no lo sustituye Karma: el proxy, el guard real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T043)
