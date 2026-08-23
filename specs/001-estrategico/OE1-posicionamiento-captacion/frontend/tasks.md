# Tasks: OE1 — Posicionamiento y Captación — Frontend

**Input**: Design documents from `specs/001-estrategico/OE1-posicionamiento-captacion/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Un MRR sin recuento, un CAC fingido o un 25 % de churn con n=4 no se ven en un 200. Constitución: cobertura ≥80 % en el módulo. Plan: Jasmine/Karma, `*.spec.ts` junto al fichero.

**Organization**: US1 P1 Ingreso (MVP) · US5 P1 sin CAC/mercados · US2 P2 Cartera · US3 P3 Captación · US4 P3 Ciclo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: otro fichero, sin dependencia pendiente
- **[US1]–[US5]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Segunda carpeta estratégica** en el SPA (`estrategico/oe1/`). Cuelga junto a OE2, no de táctico.

**Autoridad partida.** Cuatro guards, nunca una unión (D2).

**Envelope `{ data, meta }`**, no `data.resultados` táctico (D4).

**Cáscara Z copiada de OE2**, no extraída a `shared/` ni importada (D1, D17).

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Un guard unión** | El Financiero vería churn; Marketing vería MRR |
| **MRR sin recuento** | Con n=4 el importe se lee como KPI de empresa |
| **Pintar E1-05/07/08** | El 404 se leería como CAC = 0 o «un mercado» |
| **Importar `PantallaZPage` de OE2 o Partners** | Acopla módulos |
| **Ítem gris para quien no entra** | Descubre la superficie (Ciclo, cartera) |
| **Agrupar por país** | `dim_cliente` no tiene geografía comercial |

**Depends-on**: 10 GET publicados. Docker al cerrar (regla de contenedores).

---

## Phase 1: Setup

**Purpose**: árbol del módulo. Sin esto no hay rutas.

**Independent Test**: existe `frontend/src/app/modules/estrategico/oe1/` y no hay import desde `estrategico/oe2` ni `partners/gestion`.

- [x] T001 Crear el árbol `frontend/src/app/modules/estrategico/oe1/{guards,definiciones,services,models,pages}`. **No** meter ficheros en `estrategico/oe2/` ni en módulos tácticos
- [x] T002 [P] Crear `frontend/src/app/modules/estrategico/oe1/models/informes-oe1.types.ts` con `IdPantalla` (`ingreso` \| `cartera` \| `captacion` \| `ciclo`), envelope `{ data, meta }` (`cobertura`, `falta`, `alcance`, `objetivo`, `comparacion`). **`data` es array, no `resultados`**
- [x] T003 [P] Crear `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.ts` con `PUBLICADOS_UI` (los **10** slugs del OpenAPI, **sin** `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado`) y el esqueleto `PANTALLAS`. Zonas se rellenan en US1–US4

---

## Phase 2: Foundational

**Purpose**: HTTP, cuatro guards, cáscara Z, período+comparación. **Bloquea US1–US5.**

**Independent Test**: un Financiero entra a una cáscara de Ingreso; un Partner no; el GET usa el prefijo `informes-estrategicos/oe1`.

- [x] T004 Implementar `frontend/src/app/modules/estrategico/oe1/services/informes-oe1-api.service.ts`: un `GET` a `/api/v1/informes-estrategicos/oe1/{informe}` con `desde`, `hasta`, `granularidad`, `comparacion`. **Un método, no diez.** No envía umbral de muestra
- [x] T005 [P] Prueba en `frontend/src/app/modules/estrategico/oe1/services/informes-oe1-api.service.spec.ts`: prefijo `informes-estrategicos/oe1`, no `informes-tacticos/` ni `oe2`; un solo método; query con los cuatro params
- [x] T006 Crear `frontend/src/app/modules/estrategico/oe1/guards/oe1.guard.ts` con **cuatro** guards: `oe1IngresoGuard` = `DirectorFinanciero` \| `Gerente`; `oe1CarteraGuard` = `DirectorEstrategia` \| `Gerente`; `oe1CaptacionGuard` = `DirectorMarketing` \| `Gerente`; `oe1CicloGuard` = **solo** `Gerente`. **Prohibido** un array unión en las cuatro rutas. **Prohibido** `Administrador`, `PartnerIntegracion`, `DirectorExpansion`
- [x] T007 Prueba en `frontend/src/app/modules/estrategico/oe1/guards/oe1.guard.spec.ts`: Gerente pasa las cuatro; Financiero **pasa** ingreso y **falla** cartera/captacion/ciclo; Estrategia **pasa** cartera y **falla** el resto; Marketing **pasa** captacion y **falla** el resto; Partner/Operador denegados; sin auth → login
- [x] T008 Crear `frontend/src/app/modules/estrategico/oe1/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`; etapa con `transiciones = 0` es **dato**; `pct_churn` null es **sin_dato** en el %
- [x] T009 [P] Prueba en `frontend/src/app/modules/estrategico/oe1/models/estado-zona.spec.ts`: vacío ≠ 0 €; % nulo → `sin_dato`; envelope extrae `data` no `resultados`
- [x] T010 Copiar cáscara (no importar) a `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.ts` + `.html` desde `frontend/src/app/modules/estrategico/oe2/pages/`. Una página; `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`, `zona-parcial`, `zona-comparacion`. Controles `desde`/`hasta`/`granularidad`/`comparacion`. GET en paralelo. Pintar `meta.cobertura` / `meta.alcance` / comparación ausente. **Prohibido** `InformeCardComponent`. **Prohibido** importar `PantallaZPage`
- [x] T011 Prueba en `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts`: error en una zona deja las otras; cambiar período o comparación vuelve a pedir
- [x] T012 Crear `frontend/src/app/modules/estrategico/oe1/oe1.routes.ts`: `ingreso` → `oe1IngresoGuard`; `cartera` → `oe1CarteraGuard`; `captacion` → `oe1CaptacionGuard`; `ciclo` → `oe1CicloGuard`; las cuatro cargan `PantallaZPage`
- [x] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'estrategico/oe1'`. **No** colgarlo de `suscripciones`, `ventas-crm` ni `cuentas-clientes`
- [x] T014 [P] Prueba de cableado en `frontend/src/app/modules/estrategico/oe1/oe1-cableado.spec.ts`: las cuatro rutas usan el guard correcto; OE2 y táctico no ganan pantallas OE1

**Checkpoint**: cáscara sin cifras de negocio, solo con el rol correcto y los cuatro query params.

---

## Phase 3: User Story 1 — Ingreso recurrente (Priority: P1) 🎯 MVP

**Goal**: MRR con recuento y parcial; ARR como extrapolación; renovación con denominador de vencidas.

**Independent Test**: recuento y `parcial` en el mismo bloque que el importe; ARR no se lee como compromiso; Marketing no ve el enlace; el compuesto táctico de Suscripciones sigue distinto.

- [x] T015 [P] [US1] Prueba en `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.spec.ts`: `ingreso` cita exactamente `mrr-mensual`, `arr-proyeccion`, `tasa-renovacion`
- [x] T016 [US1] En `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts`: héroe con importe **y** recuento; `zona-parcial` si `cobertura === 'parcial'`; ARR con `meta.alcance` de extrapolación (MUST NOT «comprometido»); renovación declara vencidas; `data: []` de flujo no pinta 0 € de stock; bloques ≤ 8; sin cobro
- [x] T017 [P] [US1] Crear `frontend/src/app/modules/estrategico/oe1/pages/apoyo-plegable.component.ts` (+ spec): nace plegado; renovación no sustituye el visual
- [x] T018 [US1] Rellenar definición `ingreso` en `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.ts`
- [x] T019 [US1] Pintar zonas de ingreso en `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.ts` / `.html`
- [x] T020 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Ingreso recurrente» → `/estrategico/oe1/ingreso`, roles `DirectorFinanciero` y `Gerente`, grupo `Estratégico`. **No** tocar enlaces tácticos de Suscripciones ni los de OE2
- [x] T021 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–3 como pruebas unitarias equivalentes en `frontend/src/app/modules/estrategico/oe1/`

**Checkpoint**: US1 usable sola.

---

## Phase 4: User Story 5 — Sin CAC ni mercados fingidos (Priority: P1)

**Goal**: ninguna pantalla pinta CAC, mercados ni mapa. E1-05/07/08 no tienen ruta UI.

**Independent Test**: `PUBLICADOS_UI` no contiene `cac-por-canal`, `mercados-activos` ni `cartera-mrr-por-mercado`; el HTML no tiene mapa.

- [x] T022 [P] [US5] En `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.spec.ts`: `PUBLICADOS_UI` tiene 10 slugs y **no** `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado`
- [x] T023 [US5] En `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts` y `frontend/src/app/modules/estrategico/oe1/oe1.routes.ts`: no hay ruta ni bloque de CAC/mercados/mapa; no se lee «CAC = 0» ni «mercado único»
- [x] T024 [US5] Verificar que `frontend/src/app/modules/estrategico/oe1/services/informes-oe1-api.service.ts` no llama esos tres slugs

**Checkpoint**: US5 cumplida aunque Cartera, Captación y Ciclo aún no existan.

---

## Phase 5: User Story 2 — Cartera (Priority: P2)

**Goal**: mezcla por plan; segmento = tipo; desconocidos visibles; Financiero **sin** enlace.

**Independent Test**: no hay eje de país; tipo desconocido aparece; Marketing no entra; Financiero 403 en `/cartera`.

- [x] T025 [P] [US2] Definición `cartera` cita exactamente `cartera-por-plan`, `mrr-por-segmento` en `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.spec.ts`
- [x] T026 [US2] En `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts`: agrupación por `tipo` no por país; desconocidos visibles; evolución de mezcla, no foto única; sin mapa
- [x] T027 [US2] Rellenar definición `cartera` en `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.ts` y pintar zonas en `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.ts` / `.html` (un GET de plan para héroe y visual)
- [x] T028 [US2] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Cartera» → `/estrategico/oe1/cartera`, roles `DirectorEstrategia` · `Gerente` (**sin** Financiero)
- [x] T029 [US2] En `frontend/src/app/modules/estrategico/oe1/oe1-cableado.spec.ts` / nav: Financiero **no** tiene enlace de Cartera; Estrategia **no** tiene Ingreso; Marketing **no** tiene Cartera
- [x] T030 [US2] Quickstart §4 como pruebas en `frontend/src/app/modules/estrategico/oe1/`

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Captación (Priority: P3)

**Goal**: embudo con ceros; velocidad sin ficha; Financiero fuera.

**Independent Test**: etapa en cero visible; volumen no se «arregla»; sin nombre de prospecto; Financiero denegado.

- [x] T031 [P] [US3] Definición `captacion` cita `embudo-conversion`, `velocidad-ciclo-venta` en `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.spec.ts`
- [x] T032 [US3] En `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts`: etapas con `transiciones = 0` visibles; no se reordenan etapas; sin ficha/correo de prospecto; `meta.alcance` de cruce Ventas–Cuentas si viene
- [x] T033 [US3] Rellenar definición `captacion` y pintar zonas en `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.ts` / `.html` y `frontend/src/app/modules/estrategico/oe1/pages/apoyo-plegable.component.ts`
- [x] T034 [US3] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Captación» → `/estrategico/oe1/captacion`, roles `DirectorMarketing` · `Gerente` (sin Financiero ni Estrategia)
- [x] T035 [US3] Quickstart §5 como pruebas en `frontend/src/app/modules/estrategico/oe1/`

**Checkpoint**: US3 independiente.

---

## Phase 7: User Story 4 — Ciclo (Priority: P3)

**Goal**: churn sin % cerrado si n bajo; catálogo de onboarding con ceros; `en_proceso` aparte; solo Gerente.

**Independent Test**: n=4 no publica 25 %; etapa de catálogo en cero está; Finanzas/Marketing/Estrategia no ven el enlace.

- [x] T036 [P] [US4] Definición `ciclo` cita `churn-por-cohorte`, `abandono-onboarding`, `tiempo-onboarding` en `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.spec.ts`
- [x] T037 [US4] En `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts`: `pct_churn` null → sin % cerrado, `n` visible; ceros de catálogo; `en_proceso` ≠ 0 días; Financiero denegado
- [x] T038 [US4] Rellenar definición `ciclo` y pintar zonas en `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.ts` / `.html` y `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.ts`
- [x] T039 [US4] Nav en `frontend/src/app/shared/layout/nav-links.ts`: «Ciclo de vida» → `/estrategico/oe1/ciclo`, rol **solo** `Gerente`
- [x] T040 [US4] En `frontend/src/app/modules/estrategico/oe1/oe1-cableado.spec.ts`: Financiero, Estrategia y Marketing **no** tienen enlace de Ciclo; Gerente sí
- [x] T041 [US4] Quickstart §6 como pruebas en `frontend/src/app/modules/estrategico/oe1/`

**Checkpoint**: las cinco historias independientes.

---

## Phase 8: Polish

- [x] T042 [P] En `frontend/src/app/modules/estrategico/oe1/definiciones/pantallas-oe1.definiciones.spec.ts`: las cuatro pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 10; ningún slug táctico ni de OE2
- [x] T043 [P] En `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.spec.ts`: no hay mapa, exportar, cobrar, cambiar plan, ficha, país, `acotado_a`, CAC
- [x] T044 Verificar diff vacío en `frontend/src/app/modules/estrategico/oe2/` y en módulos tácticos de Suscripciones/Ventas/Cuentas salvo lo ajeno
- [x] T045 Ejecutar la suite del módulo `estrategico/oe1` y `ng build` de producción; cobertura ≥80 % de `frontend/src/app/modules/estrategico/oe1/services/informes-oe1-api.service.ts`, `frontend/src/app/modules/estrategico/oe1/guards/oe1.guard.ts` y `frontend/src/app/modules/estrategico/oe1/pages/pantalla-z.page.ts`
- [x] T046 Reconstruir contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend` y `docker ps --filter name=accidentes-django --filter name=accidentes-frontend` ambos **Up**
- [x] T047 Actualizar `specs/001-estrategico/OE1-posicionamiento-captacion/OE1-posicionamiento-captacion.md` (frontend implementado al cerrar) y [`quickstart.md`](quickstart.md) si las cifras medidas difieren

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: inmediata
- **Foundational (2)**: depende de Setup. **Bloquea US1–US5**
- **US1 (3)**: Foundational. MVP
- **US5 (4)**: Foundational. Barata; adelantarla tras T014 evita pintar CAC
- **US2 (5)**: Foundational. Independiente de US1 salvo la cáscara
- **US3 (6)**: Foundational
- **US4 (7)**: Foundational
- **Polish (8)**: historias entregadas

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US5 (P1)**: ninguna. Documental + aserción de ausencia
- **US2 (P2)**: ninguna respecto de US1; sí el guard de cartera de la fase 2
- **US3 (P3)**: ninguna
- **US4 (P3)**: ninguna

### Parallel Opportunities

- Fase 1: T002 y T003
- Fase 2: T005 y T009 tras T004/T008; T014 tras T012–T013
- Fase 3: T015 y T017 en paralelo
- Fase 4: T022 y T024
- Fase 5: T025 en paralelo con preparación de tests
- Fase 6: T031 en paralelo
- Fase 7: T036 en paralelo
- Fase 8: T042 y T043

---

## Parallel Example: Phase 3

```text
Task: "definiciones.spec — ingreso cita exactamente 3 slugs"
Task: "apoyo-plegable — nace plegado"
```

---

## Implementation Strategy

### MVP primero (US1 + US5)

1. Setup + Foundational
2. US5 (3 tareas, deja E1-05/07/08 muertos)
3. US1
4. **PARAR Y VALIDAR**: quickstart §1–3 y §7
5. Entregar

### Incremental

1. Cáscara + guards → Partner fuera; autoridad partida
2. US5 → sin CAC/mapa
3. US1 → **MVP**
4. US2 → cartera (tipo, no país)
5. US3 → captación (ceros de embudo)
6. US4 → ciclo (solo Gerente)
7. Polish + rebuild Docker

### Varias personas

Tras la fase 2: A = US1, B = US2, C = US3, D = US4. US5 la cierra quien termine Foundational.

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea crea tabla ni altera OpenAPI**
- La cáscara Z se **copia** de `frontend/src/app/modules/estrategico/oe2/pages/`, no se importa
- El HTTP permite segmento al Financiero; el **menú** de Cartera no se lo da (FR-UI-019)
- Confirmar que las pruebas fallan antes de implementar
- No commit salvo que lo pidan
