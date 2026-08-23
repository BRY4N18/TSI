# Tasks: OE5 — Retención y Ciclo de Vida — Frontend

**Input**: Design documents from `specs/001-estrategico/OE5-retencion-ciclo-vida/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Un SLA sin recuento, un 0 % fingido, un NPS inventado o una cuenta con una señal no se ven en un 200. Constitución: cobertura ≥80 % en el módulo. Plan: Jasmine/Karma, `*.spec.ts` junto al fichero.

**Organization**: US1 P1 Servicio (MVP) · US5 P1 sin NPS/ciclo OE1 · US2 P2 Ingresos · US3 P3 Planes · US4 P3 Riesgo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: otro fichero, sin dependencia pendiente
- **[US1]–[US5]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Tercera carpeta estratégica** en el SPA (`estrategico/oe5/`). Cuelga junto a OE1/OE2, no de táctico.

**Autoridad partida.** Cuatro guards, nunca una unión (D2).

**Envelope `{ data, meta }`**, no `data.resultados` táctico (D4).

**Cáscara Z copiada de OE1**, no extraída a `shared/` ni importada (D1, D17).

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Un guard unión** | El Financiero vería riesgo; Éxito de Cliente vería NRR |
| **SLA sin recuento** | Con n=14 el % se lee como KPI de empresa |
| **Vacío = 0 %** | No hubo compromisos que cumplir |
| **Pintar E5-01/11** | El 404 se leería como NPS = 0 o reportes impecables |
| **Recuadros de ciclo OE1** | Dueño: OE1; aquí 404 |
| **Importar `PantallaZPage` de OE1/OE2/Partners** | Acopla módulos |
| **Ítem gris para quien no entra** | Descubre Riesgo y NRR |
| **Una señal = riesgo** | El informe existe porque una sola no predice |

**Depends-on**: 9 GET publicados. Docker al cerrar (regla de contenedores).

---

## Phase 1: Setup

**Purpose**: árbol del módulo. Sin esto no hay rutas.

**Independent Test**: existe `frontend/src/app/modules/estrategico/oe5/` y no hay import desde `estrategico/oe1`, `estrategico/oe2` ni módulos tácticos de Soporte.

- [x] T001 Crear el árbol `frontend/src/app/modules/estrategico/oe5/{guards,definiciones,services,models,pages}`. **No** meter ficheros en `estrategico/oe1/` ni en `soporte-cliente/`
- [x] T002 [P] Crear `frontend/src/app/modules/estrategico/oe5/models/informes-oe5.types.ts` con `IdPantalla` (`servicio` \| `ingresos` \| `planes` \| `riesgo`), envelope `{ data, meta }` (`cobertura`, `falta`, `alcance`, `objetivo`, `comparacion`). **`data` es array, no `resultados`**
- [x] T003 [P] Crear `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.ts` con `PUBLICADOS_UI` (los **9** slugs del OpenAPI, **sin** `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding`) y el esqueleto `PANTALLAS`. Zonas se rellenan en US1–US4

---

## Phase 2: Foundational

**Purpose**: HTTP, cuatro guards, cáscara Z, período+comparación. **Bloquea US1–US5.**

**Independent Test**: un Éxito de Cliente entra a una cáscara de Servicio; un Partner no; el GET usa el prefijo `informes-estrategicos/oe5`.

- [x] T004 Implementar `frontend/src/app/modules/estrategico/oe5/services/informes-oe5-api.service.ts`: un `GET` a `/api/v1/informes-estrategicos/oe5/{informe}` con `desde`, `hasta`, `granularidad`, `comparacion`. **Un método, no nueve.** No envía umbral de muestra
- [x] T005 [P] Prueba en `frontend/src/app/modules/estrategico/oe5/services/informes-oe5-api.service.spec.ts`: prefijo `informes-estrategicos/oe5`, no `informes-tacticos/` ni `oe1`; un solo método; query con los cuatro params
- [x] T006 Crear `frontend/src/app/modules/estrategico/oe5/guards/oe5.guard.ts` con **cuatro** guards: `oe5ServicioGuard` = `GerenteExitoCliente` \| `Gerente`; `oe5IngresosGuard` = `DirectorFinanciero` \| `Gerente`; `oe5PlanesGuard` = `DirectorEstrategia` \| `Gerente`; `oe5RiesgoGuard` = **solo** `Gerente`. **Prohibido** un array unión. **Prohibido** `Administrador`, `PartnerIntegracion`, `DirectorMarketing`
- [x] T007 Prueba en `frontend/src/app/modules/estrategico/oe5/guards/oe5.guard.spec.ts`: Gerente pasa las cuatro; Éxito de Cliente **pasa** servicio y **falla** ingresos/planes/riesgo; Financiero **pasa** ingresos y **falla** el resto; Estrategia **pasa** planes y **falla** el resto; Partner/Operador denegados; sin auth → login
- [x] T008 Crear `frontend/src/app/modules/estrategico/oe5/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`; 0 incumplimientos en una fila presente es **dato**; vacío de SLA **no** es 0 %
- [x] T009 [P] Prueba en `frontend/src/app/modules/estrategico/oe5/models/estado-zona.spec.ts`: vacío ≠ 0 %; envelope extrae `data` no `resultados`
- [x] T010 Copiar cáscara (no importar) a `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.ts` + `.html` desde `frontend/src/app/modules/estrategico/oe1/pages/`. Una página; `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`, `zona-parcial`, `zona-comparacion`. Controles `desde`/`hasta`/`granularidad`/`comparacion`. GET en paralelo. Pintar `meta.cobertura` / `meta.alcance` / comparación ausente. **Prohibido** `InformeCardComponent`. **Prohibido** importar `PantallaZPage`
- [x] T011 Prueba en `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts`: error en una zona deja las otras; cambiar período o comparación vuelve a pedir
- [x] T012 Crear `frontend/src/app/modules/estrategico/oe5/oe5.routes.ts`: `servicio` → `oe5ServicioGuard`; `ingresos` → `oe5IngresosGuard`; `planes` → `oe5PlanesGuard`; `riesgo` → `oe5RiesgoGuard`; las cuatro cargan `PantallaZPage`
- [x] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'estrategico/oe5'`. **No** colgarlo de `soporte-cliente`, `suscripciones` ni `estrategico/oe1`
- [x] T014 [P] Prueba de cableado en `frontend/src/app/modules/estrategico/oe5/oe5-cableado.spec.ts`: las cuatro rutas usan el guard correcto; OE1 y táctico no ganan pantallas OE5

**Checkpoint**: cáscara sin cifras de negocio, solo con el rol correcto y los cuatro query params.

---

## Phase 3: User Story 1 — Servicio / SLA (Priority: P1) 🎯 MVP

**Goal**: SLA con recuento y parcial; vacío ≠ 0 %; sin compromiso aparte; carga por agente (no desempeño).

**Independent Test**: recuento y `parcial` en el mismo bloque que el %; período vacío no pinta 0 %; Financiero no ve el enlace; el compuesto táctico de Soporte sigue distinto.

- [x] T015 [P] [US1] Prueba en `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.spec.ts`: `servicio` cita exactamente `cumplimiento-sla`, `evolucion-incumplimiento`, `rendimiento-por-agente`, `reincidencia-soporte`
- [x] T016 [US1] En `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts`: héroe con % **y** recuento; `zona-parcial` si `cobertura === 'parcial'`; `data: []` no pinta 0 %; lectura declara sin compromiso; agente por id/cola no nombre; bloques ≤ 8; sin texto de ticket
- [x] T017 [P] [US1] Crear `frontend/src/app/modules/estrategico/oe5/pages/apoyo-plegable.component.ts` (+ spec): nace plegado; carga/reincidencia no sustituyen el visual
- [x] T018 [US1] Rellenar definición `servicio` en `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.ts`
- [x] T019 [US1] Pintar zonas de servicio en `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.ts` / `.html`
- [x] T020 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Servicio (SLA)» → `/estrategico/oe5/servicio`, roles `GerenteExitoCliente` y `Gerente`, grupo `Estratégico`. **No** tocar enlaces tácticos de Soporte ni los de OE1
- [x] T021 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–3 como pruebas unitarias equivalentes en `frontend/src/app/modules/estrategico/oe5/`

**Checkpoint**: US1 usable sola.

---

## Phase 4: User Story 5 — Sin NPS, reportes ni ciclo OE1 (Priority: P1)

**Goal**: ninguna pantalla pinta NPS, reportes sin corrección ni renovación/churn/onboarding. E5-01/11 y refs OE1 no tienen ruta UI.

**Independent Test**: `PUBLICADOS_UI` no contiene esos slugs; el HTML no tiene NPS ni recuadro de ciclo OE1.

- [x] T022 [P] [US5] En `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.spec.ts`: `PUBLICADOS_UI` tiene 9 slugs y **no** `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding`
- [x] T023 [US5] En `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts` y `frontend/src/app/modules/estrategico/oe5/oe5.routes.ts`: no hay ruta ni bloque de NPS/reportes/ciclo OE1; no se lee «NPS = 0» ni «todos los reportes corregidos»
- [x] T024 [US5] Verificar que `frontend/src/app/modules/estrategico/oe5/services/informes-oe5-api.service.ts` no llama esos slugs

**Checkpoint**: US5 cumplida aunque Ingresos, Planes y Riesgo aún no existan.

---

## Phase 5: User Story 2 — Ingresos retenidos (Priority: P2)

**Goal**: NRR con expansión/contracción/churn; precio congelado; Éxito de Cliente **sin** enlace.

**Independent Test**: el neto no aparece solo; no se hereda expansión=0 de OT07; CSM 403 en `/ingresos`.

- [x] T025 [P] [US2] Definición `ingresos` cita exactamente `retencion-neta-ingresos` en `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.spec.ts`
- [x] T026 [US2] En `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts`: visual con expansión, contracción y churn; `meta.alcance` de precio congelado; MUST NOT «expansión = 0» de stub táctico
- [x] T027 [US2] Rellenar definición `ingresos` en `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.ts` y pintar zonas en `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.ts` / `.html` (un GET para héroe y visual)
- [x] T028 [US2] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Ingresos retenidos» → `/estrategico/oe5/ingresos`, roles `DirectorFinanciero` · `Gerente` (**sin** Éxito de Cliente)
- [x] T029 [US2] En `frontend/src/app/modules/estrategico/oe5/oe5-cableado.spec.ts` / nav: Éxito de Cliente **no** tiene enlace de Ingresos; Financiero **no** tiene Servicio; Estrategia **no** tiene Ingresos
- [x] T030 [US2] Quickstart §4 como pruebas en `frontend/src/app/modules/estrategico/oe5/`

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Planes (Priority: P3)

**Goal**: SLA por plan; movimientos solo aprobados; antigüedad de activas; Financiero fuera.

**Independent Test**: pendientes no cuentan; cerradas no inflan antigüedad; CSM y Financiero denegados.

- [x] T031 [P] [US3] Definición `planes` cita `sla-por-plan`, `movimientos-de-plan`, `antiguedad-de-cuenta` en `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.spec.ts`
- [x] T032 [US3] En `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts`: solo movimientos aprobados; antigüedad de activas; cerradas declaradas aparte
- [x] T033 [US3] Rellenar definición `planes` y pintar zonas en `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.ts` / `.html`
- [x] T034 [US3] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Planes y antigüedad» → `/estrategico/oe5/planes`, roles `DirectorEstrategia` · `Gerente` (sin Financiero ni Éxito de Cliente)
- [x] T035 [US3] Quickstart §5 como pruebas en `frontend/src/app/modules/estrategico/oe5/`

**Checkpoint**: US3 independiente.

---

## Phase 7: User Story 4 — Riesgo (Priority: P3)

**Goal**: ≥2 señales; fuentes faltantes nombradas; solo Gerente.

**Independent Test**: una señal no marca; `meta.falta` visible; Finanzas/CSM/Estrategia no ven el enlace.

- [x] T036 [P] [US4] Definición `riesgo` cita `cuentas-en-riesgo` en `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.spec.ts`
- [x] T037 [US4] En `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts`: una señal no aparece como riesgo; fuentes faltantes nombradas; sin identidad ni coordenadas; Financiero denegado
- [x] T038 [US4] Rellenar definición `riesgo` y pintar zonas en `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.ts` / `.html`
- [x] T039 [US4] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Cuentas en riesgo» → `/estrategico/oe5/riesgo`, rol **solo** `Gerente`
- [x] T040 [US4] En `frontend/src/app/modules/estrategico/oe5/oe5-cableado.spec.ts`: Financiero, Estrategia y Éxito de Cliente **no** tienen enlace de Riesgo; Gerente sí
- [x] T041 [US4] Quickstart §6 como pruebas en `frontend/src/app/modules/estrategico/oe5/`

**Checkpoint**: las cinco historias independientes.

---

## Phase 8: Polish

- [x] T042 [P] En `frontend/src/app/modules/estrategico/oe5/definiciones/pantallas-oe5.definiciones.spec.ts`: las cuatro pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 9; ningún slug táctico ni de OE1
- [x] T043 [P] En `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.spec.ts`: no hay NPS, reportes, texto de ticket, nombre de agente, cobro, `acotado_a`, recuadro de ciclo OE1
- [x] T044 Verificar diff vacío en `frontend/src/app/modules/estrategico/oe1/` y en módulos tácticos de Soporte/Suscripciones/Cuentas salvo lo ajeno
- [x] T045 Ejecutar la suite del módulo `estrategico/oe5` y `ng build` de producción; cobertura ≥80 % de `frontend/src/app/modules/estrategico/oe5/services/informes-oe5-api.service.ts`, `frontend/src/app/modules/estrategico/oe5/guards/oe5.guard.ts` y `frontend/src/app/modules/estrategico/oe5/pages/pantalla-z.page.ts`
- [x] T046 Reconstruir contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend` y `docker ps --filter name=accidentes-django --filter name=accidentes-frontend` ambos **Up**
- [x] T047 Actualizar `specs/001-estrategico/OE5-retencion-ciclo-vida/OE5-retencion-ciclo-vida.md` (frontend implementado al cerrar) y [`quickstart.md`](quickstart.md) si las cifras medidas difieren

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: inmediata
- **Foundational (2)**: depende de Setup. **Bloquea US1–US5**
- **US1 (3)**: Foundational. MVP
- **US5 (4)**: Foundational. Barata; adelantarla tras T014 evita pintar NPS
- **US2 (5)**: Foundational. Independiente de US1 salvo la cáscara
- **US3 (6)**: Foundational
- **US4 (7)**: Foundational
- **Polish (8)**: historias entregadas

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US5 (P1)**: ninguna. Documental + aserción de ausencia
- **US2 (P2)**: ninguna respecto de US1; sí el guard de ingresos de la fase 2
- **US3 (P3)**: ninguna
- **US4 (P3)**: ninguna

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
Task: "definiciones.spec — servicio cita exactamente 4 slugs"
Task: "apoyo-plegable — nace plegado"
```

---

## Implementation Strategy

### MVP primero (US1 + US5)

1. Setup + Foundational
2. US5 (3 tareas, deja E5-01/11 y refs OE1 muertos)
3. US1
4. **PARAR Y VALIDAR**: quickstart §1–3 y §7
5. Entregar

### Incremental

1. Cáscara + guards → Partner fuera; autoridad partida
2. US5 → sin NPS/ciclo OE1
3. US1 → **MVP**
4. US2 → NRR descompuesto
5. US3 → planes (aprobados, activas)
6. US4 → riesgo (solo Gerente, ≥2 señales)
7. Polish + rebuild Docker

### Varias personas

Tras la fase 2: A = US1, B = US2, C = US3, D = US4. US5 la cierra quien termine Foundational.

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea crea tabla ni altera OpenAPI**
- La cáscara Z se **copia** de `frontend/src/app/modules/estrategico/oe1/pages/`, no se importa
- El HTTP permite SLA por plan al Éxito de Cliente; el **menú** de Planes no se lo da (FR-UI-017)
- Confirmar que las pruebas fallan antes de implementar
- No commit salvo que lo pidan
