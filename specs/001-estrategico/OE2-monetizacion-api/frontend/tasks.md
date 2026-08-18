# Tasks: OE2 — Monetización de APIs — Frontend

**Input**: Design documents from `specs/001-estrategico/OE2-monetizacion-api/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Un p95 sin muestras, un mix pintado como completo o un 100 % de uptime fingido no se ven en un 200. Constitución: cobertura ≥80 % en el módulo.

**Organization**: US1 P1 Uso (MVP) · US4 P1 sin disponibilidad · US2 P2 Dinero · US3 P3 Ecosistema.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: otro fichero, sin dependencia pendiente
- **[US1]–[US4]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Primera carpeta estratégica** en el SPA. No cuelga de `/partners/gestion/`.

**Autoridad partida.** Dos guards, nunca una unión (D2).

**Envelope `{ data, meta }`**, no `data.resultados` táctico (D4).

**Cáscara Z copiada**, no extraída a `shared/` ni importada de Partners (D1).

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Un guard unión** | El Financiero vería latencia de todos |
| **p95 sin muestras** | Con 18 llamadas el percentil es el máximo |
| **Pintar E2-06** | El 404 se leería como 100 % de uptime |
| **Importar `PantallaZPage` de Partners** | Acopla táctico y estratégico |
| **Ítem gris para Partner** | Descubre la comparativa de competidores |

**Depends-on**: 10 GET publicados. Docker al cerrar (regla de contenedores).

---

## Phase 1: Setup

**Purpose**: árbol del módulo. Sin esto no hay rutas.

**Independent Test**: existe `frontend/src/app/modules/estrategico/oe2/` y no hay import desde `partners/gestion`.

- [x] T001 Crear el árbol `frontend/src/app/modules/estrategico/oe2/{guards,definiciones,services,models,pages}`. **No** meter ficheros en `partners/gestion/`
- [x] T002 [P] Crear `frontend/src/app/modules/estrategico/oe2/models/informes-oe2.types.ts` con `IdPantalla` (`uso` \| `dinero` \| `ecosistema`), envelope `{ data, meta }` (`cobertura`, `falta`, `alcance`, `objetivo`, `comparacion`). **`data` es array, no `resultados`**
- [x] T003 [P] Crear `frontend/src/app/modules/estrategico/oe2/definiciones/pantallas-oe2.definiciones.ts` con `PUBLICADOS_UI` (los **10** slugs del OpenAPI, **sin** `disponibilidad-api`) y el esqueleto `PANTALLAS`. Zonas se rellenan en US1–US3

---

## Phase 2: Foundational

**Purpose**: HTTP, guards, cáscara Z, período+comparación. **Bloquea US1–US4.**

**Independent Test**: un Tecnológico entra a una cáscara vacía; un Partner no; el GET usa el prefijo `informes-estrategicos/oe2`.

- [x] T004 Implementar `frontend/src/app/modules/estrategico/oe2/services/informes-oe2-api.service.ts`: un `GET` a `/api/v1/informes-estrategicos/oe2/{informe}` con `desde`, `hasta`, `granularidad`, `comparacion`. **Un método, no diez.** No envía `muestra_minima`
- [x] T005 [P] Prueba en `frontend/src/app/modules/estrategico/oe2/services/informes-oe2-api.service.spec.ts`: prefijo `informes-estrategicos/oe2`, no `informes-tacticos/partners`; un solo método; query con los cuatro params
- [x] T006 Crear `frontend/src/app/modules/estrategico/oe2/guards/oe2.guard.ts` con **dos** guards: `oe2UsoEcosistemaGuard` = `DirectorTecnologico` \| `Gerente`; `oe2DineroGuard` = esos **más** `DirectorFinanciero`. **Prohibido** un array unión en las tres rutas. **Prohibido** `Administrador` y `PartnerIntegracion`
- [x] T007 Prueba en `frontend/src/app/modules/estrategico/oe2/guards/oe2.guard.spec.ts`: Tecnológico y Gerente pasan uso/ecosistema **y** dinero; Financiero **pasa** dinero y **falla** uso/ecosistema; Partner/Operador denegados; sin auth → login
- [x] T008 Crear `frontend/src/app/modules/estrategico/oe2/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`; `percentil_fiable = 0` es **dato** + marca; `llamadas = 0` en fila presente es **dato**
- [x] T009 [P] Prueba en `frontend/src/app/modules/estrategico/oe2/models/estado-zona.spec.ts`: vacío ≠ 0 ms; p95 nulo → `sin_dato`; envelope extrae `data` no `resultados`
- [x] T010 Implementar cáscara `frontend/src/app/modules/estrategico/oe2/pages/pantalla-z.page.ts` + `.html`: una página; `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`, `zona-parcial`, `zona-comparacion`. Controles `desde`/`hasta`/`granularidad`/`comparacion`. GET en paralelo. Pintar `meta.cobertura` / `meta.alcance` / comparación ausente. **Prohibido** `InformeCardComponent`. **Prohibido** importar `PantallaZPage` de Partners
- [x] T011 Prueba en `frontend/src/app/modules/estrategico/oe2/pages/pantalla-z.page.spec.ts`: error en una zona deja las otras; cambiar período o comparación vuelve a pedir
- [x] T012 Crear `frontend/src/app/modules/estrategico/oe2/oe2.routes.ts`: `uso` y `ecosistema` → `oe2UsoEcosistemaGuard`; `dinero` → `oe2DineroGuard`; las tres cargan `PantallaZPage`
- [x] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'estrategico/oe2'`. **No** colgarlo de `partners/gestion`
- [x] T014 [P] Prueba de cableado en `frontend/src/app/modules/estrategico/oe2/oe2-cableado.spec.ts`: las tres rutas usan el guard correcto; `partners/gestion` no gana pantallas OE2

**Checkpoint**: cáscara sin cifras de negocio, solo con el rol correcto y los cuatro query params.

---

## Phase 3: User Story 1 — Uso de la API (Priority: P1) 🎯 MVP

**Goal**: adopción, taxonomía 4xx≠5xx, consumo con ceros, latencia en trío.

**Independent Test**: p95, media y muestras en el mismo bloque; no fiable visible; partner en cero aparece; Partner no ve el enlace; `/partners/gestion/consumo` sigue distinto.

- [x] T015 [P] [US1] Prueba en `frontend/src/app/modules/estrategico/oe2/definiciones/pantallas-oe2.definiciones.spec.ts`: `uso` cita exactamente `integraciones-activas`, `taxonomia-errores`, `consumo-por-partner`, `latencia-por-endpoint`
- [x] T016 [US1] En `frontend/src/app/modules/estrategico/oe2/pages/pantalla-z.page.spec.ts`: adopción con denominador de acceso y meta a la vista; 4xx y 5xx sin total; ceros de partner visibles; p95+media+muestras en el mismo bloque; no fiable no oculta fila; `data: []` no pinta 0 ms; bloques ≤ 8; sin IP/secreto
- [x] T017 [P] [US1] Crear `frontend/src/app/modules/estrategico/oe2/pages/apoyo-plegable.component.ts` (+ spec): nace plegado; latencia no sustituye el visual
- [x] T018 [US1] Rellenar definición `uso` en `frontend/src/app/modules/estrategico/oe2/definiciones/pantallas-oe2.definiciones.ts`
- [x] T019 [US1] Pintar zonas de uso en `frontend/src/app/modules/estrategico/oe2/pages/pantalla-z.page.ts` / `.html`
- [x] T020 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Uso de la API» → `/estrategico/oe2/uso`, roles `DirectorTecnologico` y `Gerente`, grupo `Estratégico`. **No** tocar enlaces de `/partners/gestion/consumo`
- [x] T021 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–3 como pruebas unitarias equivalentes

**Checkpoint**: US1 usable sola.

---

## Phase 4: User Story 4 — Sin disponibilidad fingida (Priority: P1)

**Goal**: ninguna pantalla pinta uptime. E2-06 no tiene ruta UI.

**Independent Test**: `PUBLICADOS_UI` no contiene `disponibilidad-api`; el HTML no tiene uptime.

- [x] T022 [P] [US4] En `frontend/src/app/modules/estrategico/oe2/definiciones/pantallas-oe2.definiciones.spec.ts`: `PUBLICADOS_UI` tiene 10 slugs y **no** `disponibilidad-api`
- [x] T023 [US4] En `frontend/src/app/modules/estrategico/oe2/pages/pantalla-z.page.spec.ts` y `oe2.routes.ts`: no hay ruta ni bloque de disponibilidad; período vacío ≠ 0 % uptime
- [x] T024 [US4] Verificar que `informes-oe2-api.service.ts` no llama `disponibilidad-api`

**Checkpoint**: US4 cumplida aunque Dinero y Ecosistema aún no existan.

---

## Phase 5: User Story 2 — Dinero de la API (Priority: P2)

**Goal**: excedente con cuatro componentes; no tarificables; parcial; Tecnológico entra; Financiero no ve Uso.

**Independent Test**: importe con llamadas/cupo/precio; alcance no cobrado; `zona-parcial`; Financiero 403 en `/uso`.

- [x] T025 [P] [US2] Definición `dinero` cita exactamente `excedente-facturable`, `participacion-ingresos-api`, `mrr-por-linea` en `pantallas-oe2.definiciones.spec.ts`
- [x] T026 [US2] Página: cuatro componentes del excedente juntos; `meta.alcance` visible; no tarificables declarados; participación/MRR con `zona-parcial` y `falta`; sin «cobrado» como afirmación
- [x] T027 [US2] Rellenar definición `dinero` y pintar zonas (un GET de excedente para héroe y visual)
- [x] T028 [US2] Nav: «Dinero de la API» → `/estrategico/oe2/dinero`, roles Tecnológico · Gerente · Financiero
- [x] T029 [US2] En `oe2-cableado.spec.ts` / nav: Financiero **no** tiene enlaces de Uso ni Ecosistema; Tecnológico **sí** tiene Dinero
- [x] T030 [US2] Quickstart §4 (pruebas)

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Ecosistema (Priority: P3)

**Goal**: primera 2xx; (servicio, versión); ceros; Financiero fuera.

**Independent Test**: dos `'v1'` = dos grupos; credencial sin 2xx no incrementa; Financiero denegado.

- [x] T031 [P] [US3] Definición `ecosistema` cita `crecimiento-ecosistema`, `adopcion-versiones`, `comparativa-partners`
- [x] T032 [US3] Página: agrupación `(servicio, version)`; `version_es_derivada` visible; crecimiento ≠ alta de credencial; ceros en comparativa; sin contacto
- [x] T033 [US3] Pintar zonas en la página
- [x] T034 [US3] Nav: «Ecosistema» → `/estrategico/oe2/ecosistema`, Tecnológico · Gerente (sin Financiero)
- [x] T035 [US3] Quickstart §5 (pruebas)

**Checkpoint**: las tres historias independientes.

---

## Phase 7: Polish

- [x] T036 [P] Las tres pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 10; ningún slug táctico de Partners
- [x] T037 [P] Página: no hay mapa, exportar, facturar, IP, secreto, hash, contacto, `acotado_a`, total «errores»
- [x] T038 Verificar diff vacío en `frontend/src/app/modules/partners/gestion/` salvo lo ajeno
- [x] T039 Ejecutar la suite del módulo `estrategico/oe2` y `ng build` de producción; cobertura ≥80 % de `informes-oe2-api.service.ts`, `oe2.guard.ts` y `pantalla-z.page.ts`
- [x] T040 Reconstruir contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend` y `docker ps --filter name=accidentes-django --filter name=accidentes-frontend` ambos **Up**
- [x] T041 Actualizar `specs/001-estrategico/OE2-monetizacion-api/OE2-monetizacion-api.md` (frontend implementado al cerrar) y [`quickstart.md`](quickstart.md) si las cifras medidas difieren

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: inmediata
- **Foundational (2)**: depende de Setup. **Bloquea US1–US4**
- **US1 (3)**: Foundational. MVP
- **US4 (4)**: Foundational. Barata; adelantarla tras T014 evita pintar uptime
- **US2 (5)**: Foundational. Independiente de US1 salvo la cáscara
- **US3 (6)**: Foundational
- **Polish (7)**: historias entregadas

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US4 (P1)**: ninguna. Documental + aserción de ausencia
- **US2 (P2)**: ninguna respecto de US1; sí el guard de dinero de la fase 2
- **US3 (P3)**: ninguna

### Parallel Opportunities

- Fase 1: T002 y T003
- Fase 2: T005 y T009 tras T004/T008; T014 tras T012–T013
- Fase 3: T015 y T017 en paralelo
- Fase 4: T022 y T024
- Fase 5: T025 en paralelo con preparación de tests
- Fase 7: T036 y T037

---

## Parallel Example: Phase 3

```text
Task: "definiciones.spec — uso cita exactamente 4 slugs"
Task: "apoyo-plegable — nace plegado"
```

---

## Implementation Strategy

### MVP primero (US1 + US4)

1. Setup + Foundational
2. US4 (3 tareas, deja E2-06 muerto)
3. US1
4. **PARAR Y VALIDAR**: quickstart §1–3 y §6
5. Entregar

### Incremental

1. Cáscara + guards → Partner fuera
2. US4 → sin uptime
3. US1 → **MVP**
4. US2 → dinero (parcial + facturable)
5. US3 → ecosistema
6. Polish + rebuild Docker

### Varias personas

Tras la fase 2: A = US1, B = US2, C = US3. US4 la cierra quien termine Foundational.

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea crea tabla ni altera OpenAPI**
- La cáscara Z se **copia** de `partners/gestion/pages/pantalla-z.page.ts`, no se importa
- Si el HTTP negara Dinero al Tecnológico, se corrige el HTTP (FR-OE2-006), no se oculta el enlace
- Confirmar que las pruebas fallan antes de implementar
- No commit salvo que lo pidan
