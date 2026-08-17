# Tasks: Informes Compuestos de Emergencias — Frontend

**Input**: Design documents from `specs/002-tactico/Emergencias/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: un 100 % eterno, un ratio 0 donde no hay quién atienda, o una desviación pintada como SLA, se leen como dato. Las pruebas existen para eso, no para cubrir líneas.

**Organization**: agrupadas por user story de [`spec.md`](spec.md). US1 y US2 son P1; US3 es P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US3 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Tres pantallas nuevas, no el workpanel.** `/emergencias/informes/{registro,despacho,seguimiento}` se ignora. Añadir tarjetas ahí, o reutilizar `InformeCardComponent` como grilla, viola FR-UI-001 y SC-F09.

**Una cáscara Z + tres definiciones.** Tres HTML distintos garantizarían que la tercera olvide el vacío. Red Operativa copiará este patrón (FR-UI-016).

**El guard de workpanels no sirve.** Ese admite Operador y **deja fuera al Director**. Esta capa existe para el Director.

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Reutilizar `emergenciasInformesGuard`** | Dejaría entrar al Operador y echaría al Director |
| **Pintar `ratio: 0` cuando no hay unidades** | Dice «capacidad de sobra»; es lo contrario (D7, FR-UI-009) |
| **Mostrar 0 % en `data: []`** | Convierte un período vacío en alarma (FR-UI-006) |
| **Añadir Chart.js / D3 / mapas / exportar / CTA operativa** | Fuera de alcance; el visual es barra Tailwind (D5) |

**Depends-on**: los 13 publicados del backend. Esta capa no calcula cifras ni toca OpenAPI.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con workpanels ni listados simples.

- [X] T001 Crear el árbol `frontend/src/app/modules/emergencias/gestion/{guards,definiciones,services,models,pages}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en `pages/workpanel-*`
- [X] T002 [P] Crear `frontend/src/app/modules/emergencias/gestion/models/informes-compuestos.types.ts` con `PeriodoVista`, `EstadoZona` (`carga | dato | vacio | error | sin_dato`), `ZonaZ`, `DefinicionPantalla` (`id`: `calidad` \| `despacho` \| `cierre`) según [`data-model.md`](data-model.md)
- [X] T003 [P] Crear `frontend/src/app/modules/emergencias/gestion/definiciones/pantallas-gestion.definiciones.ts` con la constante `PUBLICADOS_UI` (los **13** slugs de `PUBLICADOS` en `backend/apps/informes_tacticos/services/emergencias_compuestos_service.py`) y el esqueleto `PANTALLAS` con los tres `id`. Las zonas se rellenan en US1–US3

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: cáscara Z, HTTP, guard y rutas. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: el Operador no entra. Si el guard copia el de workpanels, US1 «pasa» para la persona equivocada.

- [X] T004 Implementar `frontend/src/app/modules/emergencias/gestion/services/informes-compuestos-api.service.ts`: un `GET` parametrizado a `/api/v1/informes-tacticos/emergencias/{informe}?desde=&hasta=`. **Un método, no trece.** No llama a vigilados
- [X] T005 [P] Prueba en `frontend/src/app/modules/emergencias/gestion/services/informes-compuestos-api.service.spec.ts` de que la URL incluye el slug y el período, y de que **no** hay un método por informe vigilado
- [X] T006 Crear `frontend/src/app/modules/emergencias/gestion/guards/emergencias-gestion.guard.ts` con **solo** `DirectorOperaciones` y `Administrador` (D4). No autenticado → login; otro rol → `access-denied`
- [X] T007 ⚠️ Prueba en `frontend/src/app/modules/emergencias/gestion/guards/emergencias-gestion.guard.spec.ts`: **Operador, Cliente y Partner denegados**; **DirectorOperaciones y Administrador pasan**. Un guard de unión con el de workpanels fallaría esta prueba en silencio
- [X] T008 Crear `frontend/src/app/modules/emergencias/gestion/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. **Nunca** mapear vacío a 0
- [X] T009 [P] Prueba en `frontend/src/app/modules/emergencias/gestion/models/estado-zona.spec.ts` de que `[]` no es `dato` con ceros, y de que `pct_completitud: null` es `sin_dato` y no `0`
- [X] T010 Implementar la cáscara `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`: una sola página, resuelve `PANTALLAS` por el segmento de ruta, pinta las cuatro zonas con `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`. Reutilizar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.ts`. **Prohibido** importar `InformeCardComponent`. Cada zona dispara su GET en paralelo (D8)
- [X] T011 Prueba en `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.spec.ts`: un error en una zona deja las otras visibles; cambiar el período vuelve a pedir **todas** las zonas de la definición
- [X] T012 Crear `frontend/src/app/modules/emergencias/gestion/emergencias-gestion.routes.ts` con `calidad`, `despacho`, `cierre` → la misma `PantallaZPage`, `canActivate: [emergenciasGestionGuard]` (D3)
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'emergencias/gestion'`. **No** colgar estas rutas de `emergencias.routes.ts` (ese fichero usa el guard de Operador)
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/emergencias/gestion/emergencias-gestion-cableado.spec.ts`: las tres rutas de gestión usan `emergenciasGestionGuard`; `frontend/src/app/modules/emergencias/emergencias.routes.ts` **no** cambia de guard ni gana tarjetas

**Checkpoint**: foundation ready — se puede abrir la cáscara (vacía de cifras) solo con Director/Admin.

---

## Phase 3: User Story 1 — Calidad del registro (Priority: P1) 🎯 MVP

**Goal**: el Director ve si el expediente se llena de verdad. Completitud que **baja** cuando falta severidad o condado; la lectura nombra esos campos (D6).

**Independent Test**: período con al menos un incompleto → héroe **no** es 100 %; visual muestra el hueco; lectura dice severidad y condado. Operador no entra. Período sin casos → vacío, no 0 %.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/emergencias/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `calidad.camposComprobados` es exactamente `['severidad', 'condado']` (D6, FR-UI-008). Es la copia inevitable: el backend no emite la lista
- [X] T016 [US1] En `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.spec.ts`: `data: []` no pinta 0 %; con `completos < casos` el héroe es &lt; 100 % y el visual no omite incompletos; las cuatro `data-testid` del Z están presentes

### Implementation for User Story 1

- [X] T017 [US1] Rellenar la definición `calidad` en `frontend/src/app/modules/emergencias/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe y visual → `completitud-campos-criticos`; lectura → constante de campos; pregunta de [`spec.md`](spec.md). Contrato: [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T018 [US1] Pintar héroe (`pct_completitud` / «sin dato»), barras completo vs incompleto (Tailwind, D5) y lectura con recuento + campos en `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.html` (y la lógica en `pantalla-z.page.ts`)
- [X] T019 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Calidad del registro» → `/emergencias/gestion/calidad`, roles `DirectorOperaciones` y `Administrador`, grupo Emergencias. **No** tocar las tres entradas de workpanel
- [X] T020 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–2 en el navegador (Director entra, Operador no; completitud no es 100 % eterno; 2019 vacío)

**Checkpoint**: US1 usable sola. Despacho y cierre aún no tienen enlace.

---

## Phase 4: User Story 2 — Despacho (Priority: P1)

**Goal**: primer intento como héroe (≥90 % como **contexto**, no semáforo `cumple` de OE3); desviación con advertencia de que **no es SLA**; pérdida de señal en la lectura; ratio con **sin capacidad**.

**Independent Test**: cambiar período refresca las cuatro zonas. Condado con demanda y sin unidades → «sin capacidad», no 0. Desviación sin referencia → ausente, no 0. Un 500 en pérdida de señal no borra el héroe.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T021 [P] [US2] Crear `frontend/src/app/modules/emergencias/gestion/models/sin-capacidad.spec.ts` con el caso `casos > 0` y (`unidades_vigentes = 0` o `ratio` nulo) → sin capacidad; `ratio: 0` con unidades vigentes **sí** es un cero real
- [X] T022 [US2] En `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.spec.ts`: desviación `null` → «sin dato»; texto de referencia histórica **no** SLA visible (`meta.nota_referencia` o el texto de FR-032); error de `perdida-senal` no vacía `zona-heroe`

### Implementation for User Story 2

- [X] T023 [US2] Implementar `frontend/src/app/modules/emergencias/gestion/models/sin-capacidad.ts` según D7
- [X] T024 [US2] Rellenar la definición `despacho` en `frontend/src/app/modules/emergencias/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `primer-intento`, visual `desviacion-llegada`, lectura `perdida-senal`, apoyo `ratio-demanda-capacidad`
- [X] T025 [US2] Pintar las cuatro zonas de despacho en `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Meta ≥90 % como texto de contexto, **sin** inventar `cumple`. Ratio: nunca pintar 0 ni ∞ cuando D7 aplica
- [X] T026 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Despacho (gestión)» → `/emergencias/gestion/despacho`, mismos roles. Distinto label que «Informes de Despacho» del Operador
- [X] T027 [US2] Recorrer [`quickstart.md`](quickstart.md) §3–4 (advertencia no-SLA, sin capacidad, fallo aislado)

**Checkpoint**: US1 y US2 independientes. Cierre aún sin enlace.

---

## Phase 5: User Story 3 — Evidencia y cierre (Priority: P2)

**Goal**: envejecimiento héroe; cobertura visual grande (`sin_evidencia` cuenta); resultados + retiros en la lectura; los otros cuatro **plegados** (D9). Vista principal ≤ 8 bloques.

**Independent Test**: no hay ocho bloques del mismo peso. Cierre sin evidencia baja la cobertura. Calificación ausente ≠ 0.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T028 [P] [US3] Prueba en `frontend/src/app/modules/emergencias/gestion/pages/apoyo-plegable.component.spec.ts`: el bloque nace **plegado**; al abrirse muestra los cuatro informes de apoyo y no sustituye el visual grande
- [X] T029 [US3] En `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.spec.ts`: `sin_evidencia` aparece en el visual; calificación `null` no se pinta como `0`; recuento de bloques de la vista principal (héroe, período, visual, lectura, control de apoyo) ≤ 8

### Implementation for User Story 3

- [X] T030 [US3] Crear `frontend/src/app/modules/emergencias/gestion/pages/apoyo-plegable.component.ts` (y template) para latencia, enriquecimiento, volumen por unidad y escaladas
- [X] T031 [US3] Rellenar la definición `cierre` en `frontend/src/app/modules/emergencias/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `envejecimiento-cartera`, visual `cobertura-evidencia`, lectura `distribucion-resultados` + `retiros-forzados-por-proveedor`, apoyo los cuatro restantes
- [X] T032 [US3] Pintar las zonas de cierre en `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Cartera vacía = vacío, no «no hay atraso»
- [X] T033 [US3] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Evidencia y cierre» → `/emergencias/gestion/cierre`, mismos roles
- [X] T034 [US3] Recorrer [`quickstart.md`](quickstart.md) §5

**Checkpoint**: las tres historias independientes y el patrón Z es el mismo tres veces.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido en una sola pantalla dejaría mentir al Director.

- [X] T035 [P] Completar `frontend/src/app/modules/emergencias/gestion/definiciones/pantallas-gestion.definiciones.spec.ts`: las tres pantallas solo citan slugs de `PUBLICADOS_UI`; **ningún vigilado**; unión = 13
- [X] T036 [P] Prueba en `frontend/src/app/modules/emergencias/gestion/pages/pantalla-z.page.spec.ts` de que **no** hay mapa, `leaflet`, exportar, ni botón de despachar/cerrar/forzar (FR-UI-011, FR-UI-012, FR-UI-014)
- [X] T037 Verificar en `frontend/src/app/modules/emergencias/pages/workpanel-registro/workpanel-registro.page.ts` (y despacho/seguimiento) que **no** se añadieron tarjetas. Diff vacío en esos ficheros
- [X] T038 Ejecutar la suite del frontend (`ng test` del módulo `gestion` / afectados) y `ng build` de producción sin errores nuevos
- [X] T039 Reconstruir `accidentes-frontend` con `docker compose -f docker/accidentes.yml up -d --build frontend` (el frontend se sirve desde nginx; no hay hot-reload)
- [X] T040 Recorrer [`quickstart.md`](quickstart.md) §6–7: workpanel del Operador intacto; ninguna coordenada ni nombre de implicado en las tres pantallas
- [X] T041 Documentar hallazgos en `.specify/docs/changelog.md` y marcar la capa frontend en `specs/002-tactico/Emergencias/informes-compuestos-modelo/informes-compuestos-modelo.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — **bloquea** US1–US3
- **US1 (Phase 3)**: depende de Phase 2 — MVP
- **US2 (Phase 4)**: depende de Phase 2; no necesita US1 para ser testeable, pero comparte `pantalla-z.page.*`
- **US3 (Phase 5)**: depende de Phase 2; el componente de apoyo es nuevo
- **Polish (Phase 6)**: las tres historias hechas

### User Story Dependencies

- **US1 (P1)**: tras Phase 2. Entregable solo.
- **US2 (P1)**: tras Phase 2. Extiende la misma página; no rompe Calidad.
- **US3 (P2)**: tras Phase 2. Añade `apoyo-plegable`; no cambia el héroe de US1/US2.

US2 y US3 tocan `pantalla-z.page.ts` y `nav-links.ts`: en un solo implementador, **secuencial P1 → P1 → P2**. En paralelo, coordinar esos dos ficheros.

### Within Each User Story

- Pruebas primero y en rojo
- Definición de pantalla antes de pintar
- Pintado antes del enlace de sidebar (no anunciar una ruta vacía)
- Recorrido en navegador al cerrar la historia

### Parallel Opportunities

- T002 y T003
- T005, T007, T009 (tras existir los ficheros que prueban)
- T014 con T011–T013 cuando las rutas ya están
- T015 en paralelo con T016
- T021 en paralelo con T022
- T028 en paralelo con T029
- T035 y T036 en Polish

---

## Parallel Example: User Story 1

```text
Task: "Prueba campos_comprobados en definiciones/pantallas-gestion.definiciones.spec.ts"
Task: "Prueba vacío ≠ 0% e incompletos en pages/pantalla-z.page.spec.ts"
```

Luego, en serie: rellenar `calidad` → pintar zonas → `nav-links` → quickstart §1–2.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (Calidad del registro)
3. **STOP**: Director ve completitud honesta; Operador no entra
4. Demo / validar SC-F02, SC-F06, SC-F08, SC-F09

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo MVP
3. US2 → el despacho corregido se ve
4. US3 → el ciclo se cierra sin volverse catálogo
5. Polish (vigilados ausentes, workpanel intacto, Docker)

### Parallel Team Strategy

Un solo implementador: US1 → US2 → US3 por el fichero compartido `pantalla-z.page.ts`.

Si hay dos: A hace US1 completo; B prepara `sin-capacidad.ts` y `apoyo-plegable.component.ts` (ficheros distintos) y se integra después de US1.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- No hay librería de charts (D5)
- `campos_comprobados` y `sin_capacidad` **no** vienen en la fila: se declaran / derivan (D6, D7)
- El recorrido en navegador (T020, T027, T034, T040) no lo sustituye Karma: el proxy, el guard real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T039)
