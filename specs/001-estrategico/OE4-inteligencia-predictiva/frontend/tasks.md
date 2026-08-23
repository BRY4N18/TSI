# Tasks: OE4 — Histórico e Inteligencia — Frontend

**Input**: `specs/001-estrategico/OE4-inteligencia-predictiva/frontend/`

**Tests**: **obligatorios.** Un mapa, un 0 % de precisión, víctimas=0 por no-dato o un ítem gris no se ven en un 200.

**Organization**: US1 P1 Calidad (MVP) · US5 P1 sin mapa/bloqueados · US2 P2 Concentración · US3 P3 Impacto · US4 P4 Cobertura.

---

## Phase 1: Setup

- [X] T001 Crear `frontend/src/app/modules/estrategico/oe4/{guards,definiciones,services,models,pages}`. **No** tocar `oe3/`
- [X] T002 [P] Crear `frontend/src/app/modules/estrategico/oe4/models/informes-oe4.types.ts` con `IdPantalla` (`calidad` \| `concentracion` \| `impacto` \| `cobertura`), envelope `{ data, meta }`. `data` es array. `objetivo.cumple` es `boolean \| null` (aquí siempre null útil)
- [X] T003 [P] Crear `frontend/src/app/modules/estrategico/oe4/definiciones/pantallas-oe4.definiciones.ts` con `PUBLICADOS_UI` (9 slugs) y `BLOQUEADOS_UI` (6 slugs). Esqueleto `PANTALLAS`

---

## Phase 2: Foundational

- [X] T004 Implementar `frontend/src/app/modules/estrategico/oe4/services/informes-oe4-api.service.ts`: un GET `/api/v1/informes-estrategicos/oe4/{informe}` con cuatro query params. Un método
- [X] T005 [P] Prueba en `informes-oe4-api.service.spec.ts`: prefijo `oe4`; no `oe3` ni bloqueados
- [X] T006 Crear `frontend/src/app/modules/estrategico/oe4/guards/oe4.guard.ts` con **cuatro** guards: Calidad = Datos·Operaciones·Gerente; Concentración = Datos·Gerente; Impacto = Datos·Operaciones·Gerente; Cobertura = Datos·Gerente. Prohibido unión y Partner
- [X] T007 Prueba en `oe4.guard.spec.ts`: Gerente pasa 4; Operaciones pasa calidad/impacto y falla concentración/cobertura; Datos pasa 4; Partner/Tecnológico fallan
- [X] T008 Crear `frontend/src/app/modules/estrategico/oe4/models/estado-zona.ts`: `data: []` → `vacio`; métrica null → `sin_dato`
- [X] T009 [P] Prueba `estado-zona.spec.ts`: vacío ≠ 0 %
- [X] T010 Copiar cáscara a `pages/pantalla-z.page.ts` + `.html` desde `oe3/pages/`. **Prohibido** importar `PantallaZPage`. **Prohibido** Leaflet
- [X] T011 Prueba: error de zona aislado; cambio de período reconsulta
- [X] T012 Crear `oe4.routes.ts` con los cuatro guards
- [X] T013 `loadChildren` en `app.routes.ts` path `estrategico/oe4`
- [X] T014 [P] `oe4-cableado.spec.ts`: guards correctos; OE3 no gana rutas OE4

---

## Phase 3: US1 Calidad 🎯 MVP

- [X] T015 [P] [US1] `definiciones.spec.ts`: calidad cita los 4 slugs de expediente
- [X] T016 [US1] `pantalla-z.page.spec.ts`: índice + 4 componentes; ranking con 0 ausencias; vacío ≠ 0 %; sin semáforo
- [X] T017 [P] [US1] `apoyo-plegable.component.ts` (+ spec): nace plegado
- [X] T018 [US1] Rellenar definición `calidad`
- [X] T019 [US1] Pintar zonas de calidad
- [X] T020 [US1] Nav «Calidad del histórico» → `/estrategico/oe4/calidad`, roles Datos·Operaciones·Gerente
- [X] T021 [US1] Quickstart §1–3 como tests

---

## Phase 4: US5 sin mapa/bloqueados

- [X] T022 [P] [US5] `PUBLICADOS_UI` = 9; no contiene los 6 bloqueados
- [X] T023 [US5] HTML sin mapa/lat/lon/región/`precision-del-modelo`
- [X] T024 [US5] El servicio no llama slugs bloqueados; sin Leaflet en `oe4/`

---

## Phase 5: US2 Concentración

- [X] T025 [P] [US2] Definición `concentracion` cita concentración + patrón
- [X] T026 [US2] Ranking por nombre; clima parcial; Operaciones sin menú
- [X] T027 [US2] Pintar zonas
- [X] T028 [US2] Nav Concentración: Datos · Gerente
- [X] T029 [US2] Cableado: Operaciones **no** tiene Concentración
- [X] T030 [US2] Quickstart §4

---

## Phase 6: US3 Impacto

- [X] T031 [P] [US3] Definición `impacto` cita humano + vial
- [X] T032 [US3] no-dato ≠ 0 víctimas; denominadores de duración/distancia separados
- [X] T033 [US3] Pintar zonas
- [X] T034 [US3] Nav Impacto: Datos · Operaciones · Gerente
- [X] T035 [US3] Quickstart §5

---

## Phase 7: US4 Cobertura

- [X] T036 [P] [US4] Definición `cobertura` cita solo `cobertura-del-historico`
- [X] T037 [US4] umbral visible; `sin_masa_critica`; Operaciones sin menú
- [X] T038 [US4] Pintar zonas
- [X] T039 [US4] Nav Cobertura: Datos · Gerente
- [X] T040 [US4] Cableado: cuatro rutas con roles D2
- [X] T041 [US4] Quickstart §6

---

## Phase 8: Polish

- [X] T042 [P] Unión de slugs = 9; ninguno bloqueado ni táctico
- [X] T043 [P] Sin mapa, semáforo, identidad, región
- [X] T044 Diff vacío en `oe3/`
- [X] T045 Suite `estrategico/oe4` + `ng build`; cobertura ≥80 % en service, guard y page
- [X] T046 `docker compose -f docker/accidentes.yml up -d --build django frontend`
- [X] T047 Actualizar índice OE4 a frontend implementado

---

## Notes

- Cáscara Z copiada de `oe3/pages/`, no importada
- `cumple` no se pinta como semáforo
- No commit salvo pedido
