# Tasks: OE6 — Tiempo de Respuesta y Vidas — Frontend

**Input**: Design documents from `specs/001-estrategico/OE6-respuesta-y-vidas/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Un 0 min fingido, un p95 de 3 casos, un ETA o un mapa no se ven en un 200. Constitución: cobertura ≥80 % en el módulo. Plan: Jasmine/Karma, `*.spec.ts` junto al fichero.

**Organization**: US1 P1 Llegada (MVP) · US5 P1 sin mapa/ETA/OE3 · US2 P2 Diagnóstico · US3 P3 Ejecución · US4 P4 Personas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: otro fichero, sin dependencia pendiente
- **[US1]–[US5]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Cuarta carpeta estratégica** en el SPA (`estrategico/oe6/`). Cuelga junto a OE1/OE2/OE5, no de táctico.

**Una sola autoridad.** Un guard (`DirectorOperaciones` · `Gerente`) en las cuatro rutas (D2). No es la unión prohibida de OE1/OE5.

**Envelope `{ data, meta }`**, no `data.resultados` táctico (D4).

**Cáscara Z copiada de OE5**, no extraída a `shared/` ni importada (D1, D17).

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Promedio como héroe** | La cola larga miente el tiempo de ambulancia |
| **Vacío = 0 min** | No hubo casos que medir |
| **p95 con n mínimo como percentil** | Es el caso más lento disfrazado |
| **Mapa / lat-lon / nombres** | Constitución §4.6 |
| **Título ETA** | La referencia es histórica |
| **Tasa sin denominador** | 12 % sobre 8 ≠ sobre 8 000 |
| **Importar `PantallaZPage` de OE5/OE1** | Acopla módulos |
| **Recuadros de OE3** | Dueño: OE3 |
| **Ítem gris para Partner/Finanzas** | Descubre la superficie |

**Depends-on**: 12 GET publicados. Docker al cerrar (regla de contenedores).

---

## Phase 1: Setup

**Purpose**: árbol del módulo. Sin esto no hay rutas.

**Independent Test**: existe `frontend/src/app/modules/estrategico/oe6/` y no hay import desde `estrategico/oe5`, `emergencias/` táctico ni Leaflet.

- [X] T001 Crear el árbol `frontend/src/app/modules/estrategico/oe6/{guards,definiciones,services,models,pages}`. **No** meter ficheros en `estrategico/oe5/` ni en `emergencias/`
- [X] T002 [P] Crear `frontend/src/app/modules/estrategico/oe6/models/informes-oe6.types.ts` con `IdPantalla` (`llegada` \| `diagnostico` \| `ejecucion` \| `personas`), envelope `{ data, meta }` (`cobertura`, `falta`, `alcance`, `objetivo`, `comparacion`). **`data` es array, no `resultados`**
- [X] T003 [P] Crear `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.ts` con `PUBLICADOS_UI` (los **12** slugs del OpenAPI, **sin** slugs de OE3) y el esqueleto `PANTALLAS`. Zonas se rellenan en US1–US4

---

## Phase 2: Foundational

**Purpose**: HTTP, un guard, cáscara Z, período+comparación. **Bloquea US1–US5.**

**Independent Test**: Operaciones entra a una cáscara de Llegada; un Partner no; el GET usa el prefijo `informes-estrategicos/oe6`.

- [X] T004 Implementar `frontend/src/app/modules/estrategico/oe6/services/informes-oe6-api.service.ts`: un `GET` a `/api/v1/informes-estrategicos/oe6/{informe}` con `desde`, `hasta`, `granularidad`, `comparacion`. **Un método, no doce.** No envía umbral de muestra
- [X] T005 [P] Prueba en `frontend/src/app/modules/estrategico/oe6/services/informes-oe6-api.service.spec.ts`: prefijo `informes-estrategicos/oe6`, no `informes-tacticos/` ni `oe3`; un solo método; query con los cuatro params
- [X] T006 Crear `frontend/src/app/modules/estrategico/oe6/guards/oe6.guard.ts` con **un** guard `oe6Guard` = `DirectorOperaciones` \| `Gerente`. **Prohibido** `Administrador`, `PartnerIntegracion`, `DirectorFinanciero`, `GerenteExitoCliente`
- [X] T007 Prueba en `frontend/src/app/modules/estrategico/oe6/guards/oe6.guard.spec.ts`: Operaciones y Gerente **pasan**; Financiero, Éxito de Cliente, Partner, Operador **fallan**; sin auth → login
- [X] T008 Crear `frontend/src/app/modules/estrategico/oe6/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`; vacío de tiempos **no** es 0 min
- [X] T009 [P] Prueba en `frontend/src/app/modules/estrategico/oe6/models/estado-zona.spec.ts`: vacío ≠ 0 min; envelope extrae `data` no `resultados`
- [X] T010 Copiar cáscara (no importar) a `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.ts` + `.html` desde `frontend/src/app/modules/estrategico/oe5/pages/`. Una página; `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`, `zona-parcial`, `zona-comparacion`. Controles `desde`/`hasta`/`granularidad`/`comparacion`. GET en paralelo. Pintar `meta.cobertura` / `meta.alcance` / comparación ausente. **Prohibido** `InformeCardComponent`. **Prohibido** importar `PantallaZPage`. **Prohibido** Leaflet
- [X] T011 Prueba en `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts`: error en una zona deja las otras; cambiar período o comparación vuelve a pedir
- [X] T012 Crear `frontend/src/app/modules/estrategico/oe6/oe6.routes.ts`: `llegada`, `diagnostico`, `ejecucion`, `personas` → todas `oe6Guard`; las cuatro cargan `PantallaZPage`
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'estrategico/oe6'`. **No** colgarlo de `emergencias` ni de `estrategico/oe3`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/estrategico/oe6/oe6-cableado.spec.ts`: las cuatro rutas usan `oe6Guard`; OE5 y táctico no ganan pantallas OE6

**Checkpoint**: cáscara sin cifras de negocio, solo con el rol correcto y los cuatro query params.

---

## Phase 3: User Story 1 — Llegada (Priority: P1) 🎯 MVP

**Goal**: mediana + p95 + recuento juntos; sin llegada aparte; vacío ≠ 0 min; p95 nulo si n bajo.

**Independent Test**: las tres cifras en el mismo bloque; período vacío no pinta 0 min; Financiero no ve el enlace; el compuesto táctico de Emergencias sigue distinto.

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.spec.ts`: `llegada` cita exactamente `tiempo-respuesta-global`, `tiempo-respuesta-por-severidad`
- [X] T016 [US1] En `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts`: héroe con mediana **y** p95 **y** recuento; p95 `null` → sin dato; `data: []` no pinta 0 min; `zona-parcial` si parcial; bloques ≤ 8; sin mapa ni promedio como héroe
- [X] T017 [P] [US1] Crear `frontend/src/app/modules/estrategico/oe6/pages/apoyo-plegable.component.ts` (+ spec): nace plegado (por si Ejecución lo usa)
- [X] T018 [US1] Rellenar definición `llegada` en `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.ts`
- [X] T019 [US1] Pintar zonas de llegada en `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.ts` / `.html`
- [X] T020 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Llegada» → `/estrategico/oe6/llegada`, roles `DirectorOperaciones` y `Gerente`, grupo `Estratégico`. **No** tocar enlaces tácticos de Emergencias
- [X] T021 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–3 como pruebas unitarias equivalentes en `frontend/src/app/modules/estrategico/oe6/`

**Checkpoint**: US1 usable sola.

---

## Phase 4: User Story 5 — Sin mapa, ETA ni OE3 (Priority: P1)

**Goal**: ninguna pantalla pinta mapa, coordenadas, nombres, ETA ni informes de OE3.

**Independent Test**: `PUBLICADOS_UI` no contiene slugs de OE3; el HTML no tiene mapa ni «ETA» como cifra.

- [X] T022 [P] [US5] En `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.spec.ts`: `PUBLICADOS_UI` tiene 12 slugs y **no** slugs de OE3 ni `eta`
- [X] T023 [US5] En `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts` y `frontend/src/app/modules/estrategico/oe6/oe6.routes.ts`: no hay ruta ni bloque de mapa/lat/lon/nombre; no se lee ETA como título de cifra
- [X] T024 [US5] Verificar que `frontend/src/app/modules/estrategico/oe6/services/informes-oe6-api.service.ts` no llama slugs de OE3 y que no hay import de Leaflet en `frontend/src/app/modules/estrategico/oe6/`

**Checkpoint**: US5 cumplida aunque Diagnóstico, Ejecución y Personas aún no existan.

---

## Phase 5: User Story 2 — Diagnóstico (Priority: P2)

**Goal**: tramos que suman; automático vs manual; desviación vs histórico, no ETA.

**Independent Test**: la lectura no titula ETA; referencia ausente si n bajo; Partner denegado.

- [X] T025 [P] [US2] Definición `diagnostico` cita `tramos-del-ciclo`, `origen-de-asignacion`, `desviacion-de-llegada` en `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.spec.ts`
- [X] T026 [US2] En `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts`: tramos visibles; origen automático/manual; alcance de histórico; MUST NOT «ETA»
- [X] T027 [US2] Rellenar definición `diagnostico` en `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.ts` y pintar zonas en `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.ts` / `.html`
- [X] T028 [US2] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Diagnóstico de tiempos» → `/estrategico/oe6/diagnostico`, roles `DirectorOperaciones` · `Gerente`
- [X] T029 [US2] En `frontend/src/app/modules/estrategico/oe6/oe6-cableado.spec.ts` / nav: Financiero **no** tiene Diagnóstico; Operaciones sí
- [X] T030 [US2] Quickstart §4 como pruebas en `frontend/src/app/modules/estrategico/oe6/`

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Ejecución (Priority: P3)

**Goal**: envejecimiento de abiertos; tasas con denominador; abortos vacíos ≠ 0 %; definición de cierres forzados.

**Independent Test**: denominador a la vista; vacío de abortos no es 0 %; abiertos no pintados como cerrados.

- [X] T031 [P] [US3] Definición `ejecucion` cita `envejecimiento-de-casos-abiertos`, `rechazo-y-timeout-por-unidad`, `abortos-y-misiones-fallidas`, `cierres-forzados` en `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.spec.ts`
- [X] T032 [US3] En `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts`: tasas con denominador; `data: []` de abortos no pinta 0 %; `meta.alcance` de cierres forzados visible
- [X] T033 [US3] Rellenar definición `ejecucion` y pintar zonas en `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.ts` / `.html` y `frontend/src/app/modules/estrategico/oe6/pages/apoyo-plegable.component.ts`
- [X] T034 [US3] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Ejecución del despacho» → `/estrategico/oe6/ejecucion`, roles `DirectorOperaciones` · `Gerente`
- [X] T035 [US3] Quickstart §5 como pruebas en `frontend/src/app/modules/estrategico/oe6/`

**Checkpoint**: US3 independiente.

---

## Phase 7: User Story 4 — Personas (Priority: P4)

**Goal**: impacto sin ceros fingidos; escaladas/evidencia con dato escaso declarado; sin identidad.

**Independent Test**: no-dato ≠ 0; evidencia solo cerrados; Partner denegado.

- [X] T036 [P] [US4] Definición `personas` cita `impacto-humano`, `escaladas-de-severidad`, `cobertura-de-evidencia` en `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.spec.ts`
- [X] T037 [US4] En `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts`: impacto no cuenta null como 0; dato escaso declarado; sin nombre/foto; Partner denegado vía HTML de menú
- [X] T038 [US4] Rellenar definición `personas` y pintar zonas en `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.ts` / `.html`
- [X] T039 [US4] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Personas atendidas» → `/estrategico/oe6/personas`, roles `DirectorOperaciones` · `Gerente`
- [X] T040 [US4] En `frontend/src/app/modules/estrategico/oe6/oe6-cableado.spec.ts`: las cuatro rutas OE6 tienen los mismos roles; Partner no aparece
- [X] T041 [US4] Quickstart §6 como pruebas en `frontend/src/app/modules/estrategico/oe6/`

**Checkpoint**: las cinco historias independientes.

---

## Phase 8: Polish

- [X] T042 [P] En `frontend/src/app/modules/estrategico/oe6/definiciones/pantallas-oe6.definiciones.spec.ts`: las cuatro pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 12; ningún slug táctico ni de OE3
- [X] T043 [P] En `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.spec.ts`: no hay mapa, lat, lon, ETA como título, nombre de implicado, `acotado_a`, botón de despacho
- [X] T044 Verificar diff vacío en `frontend/src/app/modules/estrategico/oe5/` y en módulos tácticos de Emergencias salvo lo ajeno
- [X] T045 Ejecutar la suite del módulo `estrategico/oe6` y `ng build` de producción; cobertura ≥80 % de `frontend/src/app/modules/estrategico/oe6/services/informes-oe6-api.service.ts`, `frontend/src/app/modules/estrategico/oe6/guards/oe6.guard.ts` y `frontend/src/app/modules/estrategico/oe6/pages/pantalla-z.page.ts`
- [X] T046 Reconstruir contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend` y `docker ps --filter name=accidentes-django --filter name=accidentes-frontend` ambos **Up**
- [X] T047 Actualizar `specs/001-estrategico/OE6-respuesta-y-vidas/OE6-respuesta-y-vidas.md` (frontend implementado al cerrar) y [`quickstart.md`](quickstart.md) si las cifras medidas difieren

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: inmediata
- **Foundational (2)**: depende de Setup. **Bloquea US1–US5**
- **US1 (3)**: Foundational. MVP
- **US5 (4)**: Foundational. Barata; adelantarla tras T014 evita pintar mapa/ETA
- **US2 (5)**: Foundational
- **US3 (6)**: Foundational
- **US4 (7)**: Foundational
- **Polish (8)**: historias entregadas

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US5 (P1)**: ninguna. Documental + aserción de ausencia
- **US2 (P2)**: ninguna respecto de US1; sí el guard de la fase 2
- **US3 (P3)**: ninguna
- **US4 (P4)**: ninguna

### Parallel Opportunities

- Fase 1: T002 y T003
- Fase 2: T005 y T009 tras T004/T008; T014 tras T012–T013
- Fase 3: T015 y T017 en paralelo
- Fase 4: T022 y T024
- Fase 5: T025 en paralelo
- Fase 6: T031 en paralelo
- Fase 7: T036 en paralelo
- Fase 8: T042 y T043

---

## Parallel Example: Phase 3

```text
Task: "definiciones.spec — llegada cita exactamente 2 slugs"
Task: "apoyo-plegable — nace plegado"
```

---

## Implementation Strategy

### MVP primero (US1 + US5)

1. Setup + Foundational
2. US5 (3 tareas, deja mapa/ETA/OE3 muertos)
3. US1
4. **PARAR Y VALIDAR**: quickstart §1–3 y §7
5. Entregar

### Incremental

1. Cáscara + guard → Partner y Finanzas fuera
2. US5 → sin mapa/ETA
3. US1 → **MVP**
4. US2 → diagnóstico (histórico ≠ ETA)
5. US3 → ejecución (denominadores)
6. US4 → personas (dato escaso)
7. Polish + rebuild Docker

### Varias personas

Tras la fase 2: A = US1, B = US2, C = US3, D = US4. US5 la cierra quien termine Foundational.

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea crea tabla ni altera OpenAPI**
- La cáscara Z se **copia** de `frontend/src/app/modules/estrategico/oe5/pages/`, no se importa
- Un solo guard es correcto: las cuatro historias tienen la misma autoridad (§4.6)
- Confirmar que las pruebas fallan antes de implementar
- No commit salvo que lo pidan
