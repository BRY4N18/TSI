# Tasks: Informes Compuestos de Partners y API — Frontend

**Input**: Design documents from `specs/002-tactico/Partners-API/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: reusar el guard de listados deja entrar al Partner; pintar la p95 sin muestras afirma un indicador; sumar 429+403+5xx borra la señal; un envelope copiado de Ventas deja las zonas vacías con 200. Las pruebas existen para eso.

**Organization**: agrupadas por user story de [`spec.md`](spec.md). US1 y US4 son P1; US2 es P2; US3 es P3. El MVP es US1 (Consumo) más la exclusión de menú (cáscara + US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US4 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Sin acotamiento por titularidad.** El Partner **no entra**; no hay `meta.acotado_a`. Copiar `zona-alcance` de Soporte afirmaría un recorte que el envelope no envía (D4).

**Tres pantallas nuevas, no los listados ni el operativo.** `/partners/informes`, `/partners/consola/*` y `/partners/portal/*` se ignoran. El guard de listados admite `DesarrolladorAPIs` y `PartnerIntegracion`, que el backend de compuestos **no** admite.

**El envelope no es el de Soporte ni el de Ventas.** `data` es `{ resultados, periodo? }` y la nota va en `meta.nota_muestras`. Copiar `declaraciones` o `data: Record[]` deja la fiabilidad invisible o las zonas vacías con 200 OK (D5).

**Una cáscara Z copiada, no extraída.** No se toca `soporte-cliente/gestion` ni `suscripciones/gestion` (D1).

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Reusar el guard de `partners/informes/`** | Admite Partner y DesarrolladorAPIs; el backend responde 403 (D2, FR-UI-023) |
| **Pintar p95 sin `muestras` en el mismo bloque** | Dieciocho llamadas se leen como indicador de plataforma (D6, FR-UI-008) |
| **Sumar las tres clases de error, o colapsar adopción por `'v1'`** | Borra contrato vs servicio, o dos APIs distintas (D12, D13) |
| **Enlazar una fila a `/partners/consola/logs` o a «Mi consumo»** | Reintroduce IP y mezcla lecturas (D15, FR-UI-013) |

**Depends-on**: los 13 publicados del backend. Esta capa no calcula cifras ni toca OpenAPI. No extrae la cáscara Z a `shared/` (D1). El informe de alcance geográfico **no se pinta**.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con listados, consola, portal ni `soporte-cliente/gestion`.

- [X] T001 Crear el árbol `frontend/src/app/modules/partners/gestion/{guards,definiciones,services,models,pages}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en `frontend/src/app/modules/partners/informes/` ni en rutas de `partners.routes.ts` (consola/portal)
- [X] T002 [P] Crear `frontend/src/app/modules/partners/gestion/models/informes-compuestos.types.ts` con `PeriodoVista`, `EstadoZona` (`carga | dato | vacio | error | sin_dato`), `DefinicionPantalla` (`id`: `consumo` \| `incorporacion` \| `entrega`), `CuerpoInforme` (`resultados`, `periodo?`) y `MetaInforme` con `nota_muestras` opcional según [`data-model.md`](data-model.md). **`data` no es un array** y **no** hay `acotado_a` ni `declaraciones` (D4, D5)
- [X] T003 [P] Crear `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.ts` con `PUBLICADOS_UI` (los **13** slugs de `CATALOGO` en `backend/apps/informes_tacticos/services/partners_compuestos_service.py`) y el esqueleto `PANTALLAS` con los tres `id`. Las zonas se rellenan en US1–US3. **Ningún** slug de alcance geográfico

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: cáscara Z, HTTP, guard y rutas. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: si el guard copia el de listados, US1 «pasa» para el Partner. La prueba de esta fase es esa exclusión, no solo la entrada.

- [X] T004 Implementar `frontend/src/app/modules/partners/gestion/services/informes-compuestos-api.service.ts`: un `GET` parametrizado a `/api/v1/informes-tacticos/partners/{informe}?desde=&hasta=`. **Un método, no trece.** No envía `percentil`, `muestra_minima`, `mes` ni `dias_aviso_expiracion` (D8)
- [X] T005 [P] Prueba en `frontend/src/app/modules/partners/gestion/services/informes-compuestos-api.service.spec.ts` de que el prefijo es `partners` (no `soporte` ni `suscripciones`), de que **no** hay un método por informe, y de que el GET **no** manda `percentil` ni `muestra_minima`
- [X] T006 Crear `frontend/src/app/modules/partners/gestion/guards/partners-gestion.guard.ts` con **solo** `DirectorTecnologico` y `Administrador` (D2). No autenticado → login; otro rol → `access-denied`. **Prohibido** incluir `PartnerIntegracion` o `DesarrolladorAPIs`
- [X] T007 ⚠️ Prueba en `frontend/src/app/modules/partners/gestion/guards/partners-gestion.guard.spec.ts`: **PartnerIntegracion, DesarrolladorAPIs, Operador y Cliente denegados**; **DirectorTecnologico y Administrador pasan**. Un guard copiado de listados fallaría esta prueba en silencio
- [X] T008 Crear `frontend/src/app/modules/partners/gestion/models/estado-zona.ts`: `resultados: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. **Nunca** mapear vacío a 0. Conservar `meta.nota_muestras` también en `vacio`. Una fila con `llamadas = 0` o `percentil_fiable = 0` es **dato**, no vacío (D16)
- [X] T009 [P] Prueba en `frontend/src/app/modules/partners/gestion/models/estado-zona.spec.ts` de que `{ resultados: [] }` no es `dato` con ceros, de que `pct: null` es `sin_dato` y no `0`, de que `{ resultados: [{ llamadas: 0 }] }` es `dato`, de que `{ percentil_fiable: 0 }` es `dato`, y de que un envelope vacío **sigue exponiendo** `nota_muestras` si viene
- [X] T010 Implementar la cáscara `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`: una sola página, resuelve `PANTALLAS` por el segmento de ruta, pinta las zonas con `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`. **No** hay `zona-alcance` (D4). Reutilizar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.ts`. **Prohibido** importar `InformeCardComponent`. Cada zona dispara su GET en paralelo (D10) salvo el caso D9 (un GET, héroe+lectura) que se cablea en US3. Pintar `meta.nota_muestras` en `zona-nota-muestras` junto a la zona que lo pidió (D5)
- [X] T011 Prueba en `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.spec.ts`: un error en una zona deja las otras visibles; cambiar el período vuelve a pedir **todas** las zonas de la definición; **no** se infiere un alcance desde el rol
- [X] T012 Crear `frontend/src/app/modules/partners/gestion/partners-gestion.routes.ts` con `consumo`, `incorporacion`, `entrega` → la misma `PantallaZPage`, `canActivate: [partnersGestionGuard]` (D3)
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'partners/gestion'`, **antes** de `path: 'partners'` si hace falta para no capturarlo. **No** colgar estas rutas de `frontend/src/app/modules/partners/partners.routes.ts` ni de `informes/partners-informes.routes.ts`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/partners/gestion/partners-gestion-cableado.spec.ts`: las tres rutas de gestión usan `partnersGestionGuard`; `partners-informes.routes.ts` y `partners.routes.ts` **no** cambian de guard ni ganan pantallas Z; consola y portal siguen con sus guards

**Checkpoint**: foundation ready — se puede abrir la cáscara (vacía de cifras) solo con Director Tecnológico / Admin.

---

## Phase 3: User Story 1 — Consumo de la API (Priority: P1) 🎯 MVP

**Goal**: el Director ve p95 **junto** a media y muestras; taxonomía por clase; comparativa con partners en cero; apoyo plegado (métricas, reporte, endpoint, ingresos). Distinto del reporte operativo.

**Independent Test**: no existe un estado de pantalla con la p95 y sin el número de muestras en el mismo bloque. Fila no fiable visible. Partner/DesarrolladorAPIs no entran. Período 1999 → vacío, no 0 ms. Vista principal ≤ 8 bloques.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `consumo` cita exactamente `latencia-p95`, `taxonomia-errores`, `comparativa`, `metricas-consumo`, `reporte-mensual-consumo`, `consumo-por-endpoint`, `participacion-ingresos-api`
- [X] T016 [US1] En `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.spec.ts`: `resultados: []` no pinta 0 ms; `latencia_p95_ms`, `latencia_media_ms` y `muestras` están **los tres** en `zona-heroe`; `percentil_fiable: 0` **no** oculta la fila; `llamadas: 0` en comparativa se pinta; el template **no** suma las tres `clase_resultado`; las `data-testid` del Z (incluido `zona-nota-muestras` si hay nota) están presentes; recuento de bloques de la vista principal ≤ 8; **no** hay enlace a `/partners/consola/logs` ni a `/partners/portal/consumo`
- [X] T017 [P] [US1] Prueba en `frontend/src/app/modules/partners/gestion/pages/apoyo-plegable.component.spec.ts`: el bloque nace **plegado**; al abrirse muestra excedente **aparte** de ingreso base y no sustituye el visual grande

### Implementation for User Story 1

- [X] T018 [US1] Crear `frontend/src/app/modules/partners/gestion/pages/apoyo-plegable.component.ts` (y template) para los cuatro informes de segundo plano (D11)
- [X] T019 [US1] Rellenar la definición `consumo` en `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T020 [US1] Pintar las zonas de consumo en `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Héroe = **todas** las filas del trío + marca no fiable (D6). Barras Tailwind (D7). Taxonomía por `clase_resultado` **sin** total suma (D12). Comparativa: `partner` etiqueta, ceros visibles. Declaración de que esta latencia **no es** la media del operativo junto al período (D17)
- [X] T021 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Consumo de la API» → `/partners/gestion/consumo`, roles `DirectorTecnologico`, `Administrador`, grupo Partners y API. **No** tocar «Informes de partners», «Reporte de consumo», «Mi consumo» ni «Registros de API»
- [X] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–3 (Director entra, Partner no; el trío no se rompe; distinto del reporte operativo)

**Checkpoint**: US1 usable sola. Incorporación y entrega aún no tienen enlace. La exclusión de menú se cierra en US4.

---

## Phase 4: User Story 4 — El Administrador ve las tres; el partner no (Priority: P1)

**Goal**: el Administrador entra a las mismas pantallas. Partner y DesarrolladorAPIs **no** ven los enlaces ni entran. El Desarrollador sigue en consola.

**Independent Test**: misma URL de Consumo: Director y Admin entran; Partner → access-denied y **cero** enlaces `/partners/gestion/*` en el sidebar. DesarrolladorAPIs sigue viendo «Reporte de consumo» y no gestión.

### Tests for User Story 4 ⚠️ escribir primero, deben FALLAR

- [X] T023 [P] [US4] En `frontend/src/app/modules/partners/gestion/partners-gestion-cableado.spec.ts` (o spec de `nav-links`): los paths `/partners/gestion/*` **no** incluyen `PartnerIntegracion` ni `DesarrolladorAPIs` en `roles`; sí incluyen `DirectorTecnologico` y `Administrador`. `/partners/informes` **sigue** admitiendo Partner y DesarrolladorAPIs. `/partners/consola/reportes` **sigue** con Administrador y DesarrolladorAPIs
- [X] T024 [US4] En `frontend/src/app/modules/partners/gestion/guards/partners-gestion.guard.spec.ts` (si aún no cubre Admin): Administrador pasa a las tres rutas de gestión

### Implementation for User Story 4

- [X] T025 [US4] Verificar que `frontend/src/app/shared/layout/nav-links.ts` no añade ítems grises de gestión para Partner o DesarrolladorAPIs, y que los tres enlaces (cuando existan US2/US3) comparten los mismos dos roles
- [X] T026 [US4] Recorrer [`quickstart.md`](quickstart.md) §1 con Partner y con `maria.suarez.dev@demo.tsi.com`: gestión denegada; consola/portal intactos

**Checkpoint**: la exclusión se ve. US2 y US3 heredan el guard sin reimplementarlo.

---

## Phase 5: User Story 2 — Incorporación (Priority: P2)

**Goal**: adopción por **(servicio, versión)** declarada derivada; cuatro motivos de inactividad distintos; tiempo con en proceso aparte; rechazo por motivo, nunca por persona.

**Independent Test**: dos `'v1'` de servicios distintos no se colapsan. Revocada ≠ caducada. En proceso no se pinta como 0 días. Partner no entra.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T027 [P] [US2] Prueba en `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `incorporacion` cita exactamente `adopcion-versiones`, `motivo-credencial-inactiva`, `tiempo-incorporacion`, `tasa-rechazo-produccion`
- [X] T028 [US2] En `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.spec.ts`: dos filas con `version: 'v1'` y `servicio` distinto se pintan **dos** veces; `version_es_derivada` se declara; motivos distintos no se funden en «inactivas»; `en_proceso: 1` y `dias: null` **no** se pintan como 0; el template **no** contiene `ejecutado_por` ni IP

### Implementation for User Story 2

- [X] T029 [US2] Rellenar la definición `incorporacion` en `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md). Rechazo en apoyo plegado
- [X] T030 [US2] Pintar las zonas de incorporación en `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Adopción por `(servicio, version)` (D13). Motivos en grupos. Tiempo: en proceso aparte (D16). Apoyo = tasa de rechazo por `motivo`
- [X] T031 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Incorporación» → `/partners/gestion/incorporacion`, mismos roles que Consumo
- [X] T032 [US2] Recorrer [`quickstart.md`](quickstart.md) §4

**Checkpoint**: US1, US4 y US2 independientes. Entrega aún sin enlace.

---

## Phase 6: User Story 3 — Entrega contratada (Priority: P3)

**Goal**: % con integración activa frente a meta ≥70 %, denominador todos los clientes; portal y API separados; sin zona geográfica. Héroe y lectura comparten un GET.

**Independent Test**: con clientes sin partner el % es menor que 100 %. Ninguna zona de mapa o «fuera de zona». Vista principal ≤ 8 bloques.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T033 [P] [US3] Prueba en `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `entrega` cita exactamente `clientes-integracion-activa` y `volumen-expedientes`
- [X] T034 [US3] En `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.spec.ts`: un solo GET de `clientes-integracion-activa` alimenta héroe y lectura (D9); `meta` ≥70 % visible; `pct: null` → sin dato, no 0 %; canales `portal` y `api` por separado; el template **no** contiene mapa, `zona`, `leaflet` ni «fuera de zona»; `resultados: []` → vacío, no 0 %

### Implementation for User Story 3

- [X] T035 [US3] Rellenar la definición `entrega` en `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md). Héroe y lectura apuntan al **mismo** informe
- [X] T036 [US3] Pintar las zonas de entrega en `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Un GET compartido (D9). Visual = volumen por `canal`. Sin apoyo
- [X] T037 [US3] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Entrega contratada» → `/partners/gestion/entrega`, mismos roles
- [X] T038 [US3] Recorrer [`quickstart.md`](quickstart.md) §5

**Checkpoint**: las tres historias independientes y el patrón Z es el mismo tres veces.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido en una sola pantalla dejaría mentir al Director, o reabriría la consola operativa.

- [X] T039 [P] Completar `frontend/src/app/modules/partners/gestion/definiciones/pantallas-gestion.definiciones.spec.ts`: las tres pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 13; ningún slug de listados simples (`credenciales`, `alcance-datos`) ni de consola
- [X] T040 [P] Prueba en `frontend/src/app/modules/partners/gestion/pages/pantalla-z.page.spec.ts` de que **no** hay mapa, `leaflet`, exportar, botón de revocar/suspender/emitir, IP, secreto, contacto, ejecutor, ni enlace a `/partners/consola/logs` o `/partners/portal/consumo` (FR-UI-021, FR-UI-022, FR-UI-024)
- [X] T041 Verificar que `frontend/src/app/modules/partners/informes/` y `frontend/src/app/modules/partners/partners.routes.ts` **no** ganan tarjetas Z. Diff vacío en esos árboles salvo lo ajeno a esta capa
- [X] T042 Ejecutar la suite del frontend (`ng test` del módulo `partners/gestion` / afectados) y `ng build` de producción sin errores nuevos
- [X] T043 Reconstruir `accidentes-frontend` con `docker compose -f docker/accidentes.yml up -d --build frontend` (el frontend se sirve desde nginx; no hay hot-reload) y comprobar `docker ps --filter name=accidentes-` ambos `Up`
- [X] T044 Recorrer [`quickstart.md`](quickstart.md) §6–8: fallo aislado; listados, consola y portal intactos; Partner y DesarrolladorAPIs no ganan gestión; ninguna IP ni mapa
- [X] T045 Documentar hallazgos en `.specify/docs/changelog.md` y marcar la capa frontend en `specs/002-tactico/Partners-API/informes-compuestos-modelo/informes-compuestos-modelo.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — **bloquea** US1–US4
- **US1 (Phase 3)**: depende de Phase 2 — MVP de cifras
- **US4 (Phase 4)**: depende de Phase 2 y de que Consumo exista para recorrerla; no necesita US2/US3
- **US2 (Phase 5)**: depende de Phase 2; hereda guard y cáscara
- **US3 (Phase 6)**: depende de Phase 2; no necesita los cuatro apoyos de Consumo
- **Polish (Phase 7)**: las historias hechas

### User Story Dependencies

- **US1 (P1)**: tras Phase 2. Entregable solo (consumo + apoyo plegado).
- **US4 (P1)**: tras US1 para el recorrido; las pruebas de roles pueden escribirse en cuanto exista el guard (T006).
- **US2 (P2)**: tras Phase 2. Extiende la misma página; no rompe Consumo.
- **US3 (P3)**: tras Phase 2. Añade zonas de entrega; no cambia el héroe de US1/US2.

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
Task: "Prueba slugs de consumo en definiciones/pantallas-gestion.definiciones.spec.ts"
Task: "Prueba trío p95/media/muestras y vacío ≠ 0 ms en pages/pantalla-z.page.spec.ts"
Task: "Prueba apoyo plegado en pages/apoyo-plegable.component.spec.ts"
```

Luego, en serie: `apoyo-plegable` → rellenar `consumo` → pintar zonas → `nav-links` → quickstart §1–3.

---

## Implementation Strategy

### MVP First (User Story 1 + exclusión)

1. Phase 1 + Phase 2
2. Phase 3 (Consumo de la API)
3. Phase 4 (Partner / DesarrolladorAPIs fuera)
4. **STOP**: Director ve el trío p95/media/muestras; Partner no entra
5. Demo / validar SC-F01, SC-F02, SC-F03, SC-F06, SC-F11

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo MVP de cifras
3. US4 → la exclusión se ve
4. US2 → incorporación, motivos distintos, versión derivada
5. US3 → entrega con denominador de todos los clientes
6. Polish (13 slugs, listados/consola/portal intactos, Docker)

### Parallel Team Strategy

Un solo implementador: US1 → US4 → US2 → US3 por el fichero compartido `pantalla-z.page.ts`.

Si hay dos: A hace US1+US4; B prepara definiciones y pruebas de US2/US3 (ficheros `*.spec.ts` y el relleno de `PANTALLAS`) y se integra después de US1.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- No hay librería de charts (D7)
- No hay `acotado_a` (D4)
- `nota_muestras` se muestra, no se tira (D5)
- El recorrido en navegador (T022, T026, T032, T038, T044) no lo sustituye Karma: el proxy, el guard real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T043)
