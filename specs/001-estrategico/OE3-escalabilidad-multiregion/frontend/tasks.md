# Tasks: OE3 — Escalabilidad Multi-Región — Frontend

**Input**: Design documents from `specs/001-estrategico/OE3-escalabilidad-multiregion/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Un 0 min fingido, un p95 de 3 despachos, un ratio infinito, un mapa o un bloqueado pintado no se ven en un 200. Constitución: cobertura ≥80 % en el módulo. Plan: Jasmine/Karma, `*.spec.ts` junto al fichero.

**Organization**: US1 P1 Latencia (MVP) · US5 P1 sin mapa/región/bloqueados · US2 P2 Calidad · US3 P3 Capacidad · US4 P4 Respaldo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: otro fichero, sin dependencia pendiente
- **[US1]–[US5]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Quinta carpeta estratégica** en el SPA (`estrategico/oe3/`). Cuelga junto a OE1/OE2/OE5/OE6, no de táctico.

**Autoridad partida.** Cuatro guards, nunca una unión (D2). No es el guard único de OE6.

**Envelope `{ data, meta }`**, no `data.resultados` táctico (D4).

**Cáscara Z copiada de OE6**, no extraída a `shared/` ni importada (D1, D20).

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Un guard unión** | Expansión vería latencia de despacho |
| **Tecnológico en el menú** | El GET de E3-02 no lo admite; un 403 descubre la superficie |
| **Vacío = 0 min / meta cumplida** | No hubo despachos que medir |
| **p95 con n mínimo como percentil** | Es el despacho más lento disfrazado |
| **Sin capacidad = infinito o 0** | Condado con demanda y sin flota |
| **Semáforo en E3-11** | `[CALIBRAR]`, `cumple` nulo |
| **Mapa / lat-lon / nombres / eje región** | Constitución; región no es construible |
| **Pintar los siete bloqueados** | 20 000 días, uptime, margen, pruebas |
| **Importar `PantallaZPage` de OE6/OE5** | Acopla módulos |
| **Ítem gris** | Descubre Respaldo y Latencia |

**Depends-on**: 7 GET publicados. Docker al cerrar (regla de contenedores).

---

## Phase 1: Setup

**Purpose**: árbol del módulo. Sin esto no hay rutas.

**Independent Test**: existe `frontend/src/app/modules/estrategico/oe3/` y no hay import desde `estrategico/oe6`, `estrategico/oe5`, `emergencias/` táctico ni Leaflet.

- [X] T001 Crear el árbol `frontend/src/app/modules/estrategico/oe3/{guards,definiciones,services,models,pages}`. **No** meter ficheros en `estrategico/oe6/` ni en `emergencias/`
- [X] T002 [P] Crear `frontend/src/app/modules/estrategico/oe3/models/informes-oe3.types.ts` con `IdPantalla` (`latencia` \| `calidad` \| `capacidad` \| `respaldo`), envelope `{ data, meta }` (`cobertura`, `falta`, `alcance`, `objetivo`, `comparacion`). **`data` es array, no `resultados`**. `objetivo.cumple` es `boolean \| null`
- [X] T003 [P] Crear `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.ts` con `PUBLICADOS_UI` (los **7** slugs de `oe3_service.PUBLICADOS`: `latencia-asignacion`, `evolucion-latencia`, `tasa-error-registro`, `primer-intento`, `ratio-demanda-capacidad`, `cobertura-de-respaldo`, `perdida-de-senal`) y `BLOQUEADOS_UI` (los 7 que no se llaman). Esqueleto `PANTALLAS`. Zonas se rellenan en US1–US4

---

## Phase 2: Foundational

**Purpose**: HTTP, cuatro guards, cáscara Z, período+comparación. **Bloquea US1–US5.**

**Independent Test**: Operaciones entra a una cáscara de Latencia; Expansión no; Tecnológico no; el GET usa el prefijo `informes-estrategicos/oe3`.

- [X] T004 Implementar `frontend/src/app/modules/estrategico/oe3/services/informes-oe3-api.service.ts`: un `GET` a `/api/v1/informes-estrategicos/oe3/{informe}` con `desde`, `hasta`, `granularidad`, `comparacion`. **Un método, no siete.** No envía `umbral_seg` ni umbral de muestra
- [X] T005 [P] Prueba en `frontend/src/app/modules/estrategico/oe3/services/informes-oe3-api.service.spec.ts`: prefijo `informes-estrategicos/oe3`, no `informes-tacticos/` ni `oe6`; un solo método; query con los cuatro params; **no** llama slugs de `BLOQUEADOS_UI`
- [X] T006 Crear `frontend/src/app/modules/estrategico/oe3/guards/oe3.guard.ts` con **cuatro** guards: `oe3LatenciaGuard` = `DirectorOperaciones` \| `Gerente`; `oe3CalidadGuard` = `DirectorOperaciones` \| `Gerente`; `oe3CapacidadGuard` = `DirectorExpansion` \| `DirectorOperaciones` \| `Gerente`; `oe3RespaldoGuard` = `DirectorExpansion` \| `Gerente`. **Prohibido** un array unión de las cuatro. **Prohibido** `Administrador`, `PartnerIntegracion`, `DirectorFinanciero`, `DirectorTecnologico`
- [X] T007 Prueba en `frontend/src/app/modules/estrategico/oe3/guards/oe3.guard.spec.ts`: Gerente pasa las cuatro; Operaciones **pasa** latencia/calidad/capacidad y **falla** respaldo; Expansión **pasa** capacidad/respaldo y **falla** latencia/calidad; Tecnológico, Financiero, Partner, Operador **fallan** las cuatro; sin auth → login
- [X] T008 Crear `frontend/src/app/modules/estrategico/oe3/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; demanda sin flota → `sin_capacidad`; 4xx/5xx → `error`; vacío de latencia **no** es 0 min
- [X] T009 [P] Prueba en `frontend/src/app/modules/estrategico/oe3/models/estado-zona.spec.ts`: vacío ≠ 0 min; `sin_capacidad` ≠ infinito; envelope extrae `data` no `resultados`
- [X] T010 Copiar cáscara (no importar) a `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.ts` + `.html` desde `frontend/src/app/modules/estrategico/oe6/pages/`. Una página; `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`, `zona-parcial`, `zona-comparacion`. Controles `desde`/`hasta`/`granularidad`/`comparacion`. GET en paralelo. Pintar `meta.cobertura` / `meta.alcance` / comparación ausente. **Prohibido** `InformeCardComponent`. **Prohibido** importar `PantallaZPage`. **Prohibido** Leaflet
- [X] T011 Prueba en `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts`: error en una zona deja las otras; cambiar período o comparación vuelve a pedir
- [X] T012 Crear `frontend/src/app/modules/estrategico/oe3/oe3.routes.ts`: `latencia` → `oe3LatenciaGuard`; `calidad` → `oe3CalidadGuard`; `capacidad` → `oe3CapacidadGuard`; `respaldo` → `oe3RespaldoGuard`; las cuatro cargan `PantallaZPage`
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'estrategico/oe3'`. **No** colgarlo de `emergencias` ni de `estrategico/oe6`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/estrategico/oe3/oe3-cableado.spec.ts`: las cuatro rutas usan el guard correcto; OE6 y táctico no ganan pantallas OE3

**Checkpoint**: cáscara sin cifras de negocio, solo con el rol correcto y los cuatro query params.

---

## Phase 3: User Story 1 — Latencia (Priority: P1) 🎯 MVP

**Goal**: p95 + recuento + `cumple` juntos; alcance operativo (minutos, no 100 ms); vacío ≠ 0 min; p95 nulo si n bajo.

**Independent Test**: las tres cifras en el mismo bloque; período vacío no pinta 0 min; Expansión y Tecnológico no ven el enlace; OE6 Llegada sigue distinta.

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.spec.ts`: `latencia` cita exactamente `latencia-asignacion`, `evolucion-latencia`
- [X] T016 [US1] En `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts`: héroe con p95 **y** recuento **y** `cumple`; p95 `null` → sin dato; `data: []` no pinta 0 min ni meta cumplida; alcance declara proceso no algoritmo; `zona-parcial` si parcial; bloques ≤ 8; sin mapa ni promedio como héroe
- [X] T017 [P] [US1] Crear `frontend/src/app/modules/estrategico/oe3/pages/apoyo-plegable.component.ts` (+ spec): nace plegado (Capacidad lo usará)
- [X] T018 [US1] Rellenar definición `latencia` en `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.ts`
- [X] T019 [US1] Pintar zonas de latencia en `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.ts` / `.html`
- [X] T020 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Latencia de despacho» → `/estrategico/oe3/latencia`, roles `DirectorOperaciones` y `Gerente`, grupo `Estratégico`. **No** tocar enlaces tácticos ni OE6
- [X] T021 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–3 como pruebas unitarias equivalentes en `frontend/src/app/modules/estrategico/oe3/`

**Checkpoint**: US1 usable sola.

---

## Phase 4: User Story 5 — Sin mapa, región ni bloqueados (Priority: P1)

**Goal**: ninguna pantalla pinta mapa, coordenadas, nombres, eje de región ni los siete informes bloqueados.

**Independent Test**: `PUBLICADOS_UI` tiene 7 slugs y no contiene bloqueados; el HTML no tiene mapa ni «región» como eje.

- [X] T022 [P] [US5] En `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.spec.ts`: `PUBLICADOS_UI` tiene 7 slugs y **no** `uptime-por-region`, `tiempo-puesta-operacion`, `curva-maduracion`, `cohorte-region`, `margen-operativo`, `reasignacion-manual`, `cobertura-pruebas`
- [X] T023 [US5] En `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts` y `frontend/src/app/modules/estrategico/oe3/oe3.routes.ts`: no hay ruta ni bloque de mapa/lat/lon/nombre; no hay eje de región; no hay recuadro de 20 000 días
- [X] T024 [US5] Verificar que `frontend/src/app/modules/estrategico/oe3/services/informes-oe3-api.service.ts` no llama slugs bloqueados ni de OE6 y que no hay import de Leaflet en `frontend/src/app/modules/estrategico/oe3/`

**Checkpoint**: US5 cumplida aunque Calidad, Capacidad y Respaldo aún no existan.

---

## Phase 5: User Story 2 — Calidad (Priority: P2)

**Goal**: error de registro con lista de campos; primer intento con denominador y grano de intento; sin semáforo cerrado en E3-11.

**Independent Test**: campos comprobados junto a la tasa; E3-11 no es verde/rojo; Expansión denegada.

- [X] T025 [P] [US2] Definición `calidad` cita `tasa-error-registro`, `primer-intento` en `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.spec.ts`
- [X] T026 [US2] En `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts`: campos comprobados visibles; primer intento con denominador; `cumple` nulo de E3-11 **no** pinta semáforo; MUST NOT «registro perfecto» sin lista
- [X] T027 [US2] Rellenar definición `calidad` en `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.ts` y pintar zonas en `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.ts` / `.html`
- [X] T028 [US2] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Calidad del despacho» → `/estrategico/oe3/calidad`, roles `DirectorOperaciones` · `Gerente`
- [X] T029 [US2] En `frontend/src/app/modules/estrategico/oe3/oe3-cableado.spec.ts` / nav: Expansión **no** tiene Calidad; Operaciones sí; Tecnológico no
- [X] T030 [US2] Quickstart §4 como pruebas en `frontend/src/app/modules/estrategico/oe3/`

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Capacidad (Priority: P3)

**Goal**: ratio por condado; sin capacidad ≠ infinito; flota del período; GPS en apoyo plegado con recuento.

**Independent Test**: condado sin flota se lee «sin capacidad»; no hay mapa; Tecnológico denegado; Operaciones y Expansión entran.

- [X] T031 [P] [US3] Definición `capacidad` cita `ratio-demanda-capacidad`, `perdida-de-senal` en `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.spec.ts`
- [X] T032 [US3] En `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts`: grano condado; demanda sin flota → sin capacidad no infinito; lectura declara flota del período; apoyo plegado con recuento de posiciones; sin mapa ni eje región
- [X] T033 [US3] Rellenar definición `capacidad` y pintar zonas en `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.ts` / `.html` y `frontend/src/app/modules/estrategico/oe3/pages/apoyo-plegable.component.ts`
- [X] T034 [US3] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Capacidad por condado» → `/estrategico/oe3/capacidad`, roles `DirectorExpansion`, `DirectorOperaciones`, `Gerente`
- [X] T035 [US3] Quickstart §5 como pruebas en `frontend/src/app/modules/estrategico/oe3/`

**Checkpoint**: US3 independiente.

---

## Phase 7: User Story 4 — Respaldo (Priority: P4)

**Goal**: cobertura con denominador; alta ≠ disponible; vacío ≠ 0 %; Operaciones sin enlace.

**Independent Test**: denominador a la vista; Operaciones no ve el ítem; Partner denegado.

- [X] T036 [P] [US4] Definición `respaldo` cita exactamente `cobertura-de-respaldo` en `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.spec.ts`
- [X] T037 [US4] En `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts`: tasa con denominador; vecino solo alta no cuenta; `data: []` no pinta 0 %; sin mapa
- [X] T038 [US4] Rellenar definición `respaldo` y pintar zonas en `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.ts` / `.html`
- [X] T039 [US4] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Respaldo vecinal» → `/estrategico/oe3/respaldo`, roles `DirectorExpansion` · `Gerente`. **No** incluir `DirectorOperaciones`
- [X] T040 [US4] En `frontend/src/app/modules/estrategico/oe3/oe3-cableado.spec.ts`: las cuatro rutas tienen roles distintos según D2; Partner y Tecnológico no aparecen; Operaciones no tiene Respaldo
- [X] T041 [US4] Quickstart §6 como pruebas en `frontend/src/app/modules/estrategico/oe3/`

**Checkpoint**: las cinco historias independientes.

---

## Phase 8: Polish

- [X] T042 [P] En `frontend/src/app/modules/estrategico/oe3/definiciones/pantallas-oe3.definiciones.spec.ts`: las cuatro pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 7; ningún slug táctico, de OE6 ni bloqueado
- [X] T043 [P] En `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.spec.ts`: no hay mapa, lat, lon, eje región, nombre de implicado, `acotado_a`, botón de despacho, semáforo en E3-11
- [X] T044 Verificar diff vacío en `frontend/src/app/modules/estrategico/oe6/` y en módulos tácticos de Emergencias salvo lo ajeno
- [X] T045 Ejecutar la suite del módulo `estrategico/oe3` y `ng build` de producción; cobertura ≥80 % de `frontend/src/app/modules/estrategico/oe3/services/informes-oe3-api.service.ts`, `frontend/src/app/modules/estrategico/oe3/guards/oe3.guard.ts` y `frontend/src/app/modules/estrategico/oe3/pages/pantalla-z.page.ts`
- [X] T046 Reconstruir contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend` y `docker ps --filter name=accidentes-django --filter name=accidentes-frontend` ambos **Up**
- [X] T047 Actualizar `specs/001-estrategico/OE3-escalabilidad-multiregion/OE3-escalabilidad-multiregion.md` (frontend implementado al cerrar) y [`quickstart.md`](quickstart.md) si las cifras medidas difieren

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: inmediata
- **Foundational (2)**: depende de Setup. **Bloquea US1–US5**
- **US1 (3)**: Foundational. MVP
- **US5 (4)**: Foundational. Barata; adelantarla tras T014 evita pintar mapa/región/bloqueados
- **US2 (5)**: Foundational
- **US3 (6)**: Foundational (usa apoyo plegado de T017)
- **US4 (7)**: Foundational
- **Polish (8)**: historias entregadas

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US5 (P1)**: ninguna. Documental + aserción de ausencia
- **US2 (P2)**: ninguna respecto de US1; sí el guard de la fase 2
- **US3 (P3)**: T017 (apoyo plegado) si Capacidad lo usa
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
Task: "definiciones.spec — latencia cita exactamente 2 slugs"
Task: "apoyo-plegable — nace plegado"
```

---

## Implementation Strategy

### MVP primero (US1 + US5)

1. Setup + Foundational
2. US5 (3 tareas, deja mapa/región/bloqueados muertos)
3. US1
4. **PARAR Y VALIDAR**: quickstart §1–3 y §7
5. Entregar

### Incremental

1. Cáscara + cuatro guards → Expansión fuera de Latencia; Tecnológico fuera
2. US5 → sin mapa/región/bloqueados
3. US1 → **MVP**
4. US2 → calidad (campos + sin semáforo E3-11)
5. US3 → capacidad (sin capacidad ≠ infinito)
6. US4 → respaldo (Operaciones sin menú)
7. Polish + rebuild Docker

### Varias personas

Tras la fase 2: A = US1, B = US2, C = US3, D = US4. US5 la cierra quien termine Foundational.

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea crea tabla ni altera OpenAPI**
- La cáscara Z se **copia** de `frontend/src/app/modules/estrategico/oe6/pages/`, no se importa
- Cuatro guards son correctos: §4.3 parte la autoridad; el GET de E3-02 no incluye Tecnológico
- Confirmar que las pruebas fallan antes de implementar
- No commit salvo que lo pidan
