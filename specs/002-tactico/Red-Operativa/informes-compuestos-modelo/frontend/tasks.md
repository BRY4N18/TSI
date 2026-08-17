# Tasks: Informes Compuestos de Red Operativa — Frontend

**Input**: Design documents from `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: un guard de unión deja a cada director en la materia del otro **sin síntoma**; un 0 % donde no hay transiciones, o un vacío de despublicación sin fecha, se leen como dato. Las pruebas existen para eso.

**Organization**: agrupadas por user story de [`spec.md`](spec.md). Las tres son P1; el MVP es US1 (Flota y cobertura).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US3 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**No hay un solo jefe.** Emergencias copió un Director. Aquí **dos guards** (crecimiento / validación) y tres enlaces con roles distintos. Un `canActivate` con la unión `DirectorExpansion | DirectorTecnologico` haría pasar US1–US3 para la persona equivocada.

**Tres pantallas nuevas, no el índice de listados.** `/red-operativa/informes` se ignora. Añadir tarjetas Z ahí, o reutilizar los guards de listados (flota admite Cliente/Proveedor), viola FR-UI-001 y FR-UI-017.

**Agrupar por materia, no por OT.** Solo `tasa-aprobacion-primer-intento` y `motivos-rechazo` son validación. El resto —incluida la retirada— es crecimiento (D5).

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Un guard de unión de departamento** | Cada director vería la materia del otro sin que nada falle (D2, FR-UI-020) |
| **Reusar `informesFlotaGuard` / `informesValidacionesGuard`** | Flota de listados admite Cliente y Proveedor |
| **Pintar `pct_disponibilidad: 0` cuando es `null`** | Convierte «no se sabe» en «estuvo caída» (FR-UI-007) |
| **Ocultar `medida_exacta_desde` cuando `data: []`** | El vacío se lee como «nunca se despublicó» (FR-UI-011) |

**Depends-on**: los 15 publicados del backend. Esta capa no calcula cifras ni toca OpenAPI. No extrae la cáscara Z a `shared/` (D1).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con listados ni con `emergencias/gestion`.

- [X] T001 Crear el árbol `frontend/src/app/modules/red-operativa/gestion/{guards,definiciones,services,models,pages}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en `frontend/src/app/modules/red-operativa/informes/`
- [X] T002 [P] Crear `frontend/src/app/modules/red-operativa/gestion/models/informes-compuestos.types.ts` con `PeriodoVista`, `EstadoZona` (`carga | dato | vacio | error | sin_dato`), `Materia` (`crecimiento` \| `validacion`), `DefinicionPantalla` (`id`: `flota` \| `mercados` \| `validacion`, campo `materia`) y `MetaInforme` con `medida_exacta_desde` y `filtros` según [`data-model.md`](data-model.md)
- [X] T003 [P] Crear `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.ts` con `PUBLICADOS_UI` (los **15** slugs de `CATALOGO` en `backend/apps/informes_tacticos/services/red_operativa_compuestos_service.py`) y el esqueleto `PANTALLAS` con los tres `id` y su `materia`. Las zonas se rellenan en US1–US3

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: cáscara Z, HTTP, **dos** guards y rutas. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: si el guard es una unión de las dos autoridades, US1 «pasa» para el Tecnológico. La prueba de esta fase es la exclusión, no la entrada.

- [X] T004 Implementar `frontend/src/app/modules/red-operativa/gestion/services/informes-compuestos-api.service.ts`: un `GET` parametrizado a `/api/v1/informes-tacticos/red-operativa/{informe}?desde=&hasta=`. **Un método, no quince.** No envía `umbral_unidades` ni `dias_objetivo` (D7)
- [X] T005 [P] Prueba en `frontend/src/app/modules/red-operativa/gestion/services/informes-compuestos-api.service.spec.ts` de que la URL incluye el slug y el período, el prefijo es `red-operativa` (no `emergencias`), y de que **no** hay un método por informe
- [X] T006 Crear `frontend/src/app/modules/red-operativa/gestion/guards/red-operativa-gestion.guard.ts` con **dos** funciones: `gestionCrecimientoGuard` (`DirectorExpansion` \| `Administrador`) y `gestionValidacionGuard` (`DirectorTecnologico` \| `Administrador`) (D2). No autenticado → login; otro rol → `access-denied`. **Prohibido** un tercer guard que una las dos materias
- [X] T007 ⚠️ Prueba en `frontend/src/app/modules/red-operativa/gestion/guards/red-operativa-gestion.guard.spec.ts`: **Expansión denegado en validación**; **Tecnológico denegado en crecimiento**; Administrador pasa las dos; Cliente, Proveedor y Operador denegados en ambas. Un guard de unión fallaría esta prueba en silencio
- [X] T008 Crear `frontend/src/app/modules/red-operativa/gestion/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. **Nunca** mapear vacío a 0. Conservar `meta` (incluido `medida_exacta_desde`) también en `vacio`
- [X] T009 [P] Prueba en `frontend/src/app/modules/red-operativa/gestion/models/estado-zona.spec.ts` de que `[]` no es `dato` con ceros, de que `pct_disponibilidad: null` es `sin_dato` y no `0`, y de que un envelope vacío **sigue exponiendo** `medida_exacta_desde`
- [X] T010 Implementar la cáscara `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`: una sola página, resuelve `PANTALLAS` por el segmento de ruta, pinta las cuatro zonas con `data-testid` `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`. Reutilizar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.ts`. **Prohibido** importar `InformeCardComponent`. Cada zona dispara su GET en paralelo (D9)
- [X] T011 Prueba en `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.spec.ts`: un error en una zona deja las otras visibles; cambiar el período vuelve a pedir **todas** las zonas de la definición
- [X] T012 Crear `frontend/src/app/modules/red-operativa/gestion/red-operativa-gestion.routes.ts` con `flota` y `mercados` → `PantallaZPage` + `gestionCrecimientoGuard`; `validacion` → la misma página + `gestionValidacionGuard` (D3). **No** un `canActivate` común a las tres
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'red-operativa/gestion'`. **No** colgar estas rutas de `frontend/src/app/modules/red-operativa/informes/red-operativa-informes.routes.ts`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/red-operativa/gestion/red-operativa-gestion-cableado.spec.ts`: `flota`/`mercados` usan `gestionCrecimientoGuard`; `validacion` usa `gestionValidacionGuard`; `red-operativa-informes.routes.ts` **no** cambia de guard ni gana pantallas Z

**Checkpoint**: foundation ready — se puede abrir la cáscara (vacía de cifras) solo con el rol de esa materia.

---

## Phase 3: User Story 1 — Flota y cobertura (Priority: P1) 🎯 MVP

**Goal**: el Director de Expansión ve dónde falta cobertura. Estados tal como los registró la operación (incluido En Misión); disponibilidad **ausente** si no hay transiciones; condado crítico **sin alternativas** si no hay vecinos. Cinco informes de apoyo plegados.

**Independent Test**: condado sin unidades y sin vecinos se nombra y se señala. Tecnológico **no** ve el enlace ni entra. Período sin datos → vacío, no 0 %. Vista principal ≤ 8 bloques.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `flota.materia === 'crecimiento'` y de que sus slugs son exactamente los ocho de OT12 (`unidades-por-estado`, `disponibilidad-declarada`, `cobertura-flota-por-region`, `condados-cobertura-critica`, `rotacion-flota`, `bajas-forzadas`, `pendientes-primer-acceso`, `rendimiento-proveedor`)
- [X] T016 [P] [US1] Prueba en `frontend/src/app/modules/red-operativa/gestion/pages/apoyo-plegable.component.spec.ts`: el bloque nace **plegado**; al abrirse muestra los informes de apoyo y no sustituye el visual grande
- [X] T017 [US1] En `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.spec.ts`: `data: []` no pinta 0 %; `pct_disponibilidad: null` se lee ausente y un `0` real no se relabela; `sin_alternativas: true` se lee **sin alternativas**; el visual de estados pinta el texto `En Misión` si llega en `data`; las cuatro `data-testid` del Z están presentes; recuento de bloques de la vista principal ≤ 8

### Implementation for User Story 1

- [X] T018 [US1] Crear `frontend/src/app/modules/red-operativa/gestion/pages/apoyo-plegable.component.ts` (y template) para el segundo plano de Flota (cinco informes) — se reutiliza en US2
- [X] T019 [US1] Rellenar la definición `flota` en `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `condados-cobertura-critica`, visual `unidades-por-estado`, lectura `disponibilidad-declarada`, apoyo los cinco restantes, `apoyoPlegado: true`. Contrato: [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T020 [US1] Pintar héroe (recuento crítico + umbral/`nota_umbral`), barras por `estado` (Tailwind, D6), lectura de disponibilidad y apoyo plegado en `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.html` (y la lógica en `pantalla-z.page.ts`). `nota_region` junto a cobertura por región
- [X] T021 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Flota y cobertura» → `/red-operativa/gestion/flota`, roles `DirectorExpansion` y `Administrador`, grupo Red operativa. **No** incluir `DirectorTecnologico`. **No** tocar el enlace «Informes de red»
- [X] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §1 y §3 en el navegador (Expansión entra, Tecnológico no ve el enlace; En Misión, ausente, sin alternativas, apoyo plegado)

**Checkpoint**: US1 usable sola. Mercados y validación aún no tienen enlace.

---

## Phase 4: User Story 2 — Mercados y retirada (Priority: P1)

**Goal**: mercados activos (ciclo de vida, no geografía); tiempo de puesta en operación con convención de días, no SLA; regiones en riesgo con umbral visible; despublicación con **`medida_exacta_desde` aunque `data` esté vacío**.

**Independent Test**: región aún no en producción → días ausentes, no 0 ni incumplimiento. Histórico vacío de despublicación no se lee como «nunca pasó». Tecnológico no entra.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T023 [P] [US2] Prueba en `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `mercados.materia === 'crecimiento'` y de que incluye `tiempo-puesta-operacion`, `mercados-activos`, `regiones-en-riesgo`, `casos-activos-al-despublicar`, `tiempo-perdida-a-despublicacion` — y **no** `tasa-aprobacion-primer-intento` ni `motivos-rechazo`
- [X] T024 [US2] En `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.spec.ts`: `dias: null` / `cumple_objetivo: null` → ausente, no 0 ni «incumple»; texto de convención de objetivo visible (`meta` o nota); `data: []` en despublicación **sigue mostrando** `medida_exacta_desde`; error de `bajas-forzadas` no aplica aquí — un 500 de `casos-activos-al-despublicar` no vacía `zona-heroe`

### Implementation for User Story 2

- [X] T025 [US2] Rellenar la definición `mercados` en `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `mercados-activos`, visual `tiempo-puesta-operacion`, lectura `regiones-en-riesgo`, apoyo los dos de despublicación, `apoyoPlegado: true`
- [X] T026 [US2] Pintar las zonas de mercados en `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Umbral y `dias_objetivo` se **leen** de `meta.filtros`, no se editan (D7). Hueco región↔condado (`nota` / #38) junto a la cifra de riesgo si el envelope lo trae
- [X] T027 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Mercados y retirada» → `/red-operativa/gestion/mercados`, roles `DirectorExpansion` y `Administrador`. Distinto del listado «Regiones operativas»
- [X] T028 [US2] Recorrer [`quickstart.md`](quickstart.md) §4 (convención de 30 días, medida exacta en vacío)

**Checkpoint**: US1 y US2 independientes. Validación aún sin enlace. Tecnológico sigue sin ver estas dos.

---

## Phase 5: User Story 3 — Criterios de validación (Priority: P1)

**Goal**: el Director Tecnológico ve cómo se valida: tasa al primer intento (grano = intentos) y motivos de rechazo. Sin apoyo. Sin desglose por validador. Expansión no ve el enlace.

**Independent Test**: región rechazada dos veces y aprobada a la tercera no sube la tasa como si hubiera aprobado al primero (el backend ya lo calcula; la UI no lo «corrige» agrupando por región). Expansión no entra. Un motivo ausente no aparece como categoría de aprobaciones.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T029 [P] [US3] Prueba en `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `validacion.materia === 'validacion'`, de que sus slugs son **exactamente** `tasa-aprobacion-primer-intento` y `motivos-rechazo`, y de que el texto de grano declara **intentos**, no regiones
- [X] T030 [US3] En `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.spec.ts`: `pct_aprobacion_primer_intento: null` → sin dato; la lectura nombra intentos; **ninguna** columna de validador/persona; `data: []` no pinta 0 %

### Implementation for User Story 3

- [X] T031 [US3] Rellenar la definición `validacion` en `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `tasa-aprobacion-primer-intento`, visual `motivos-rechazo`, lectura = texto de grano (sin zona de apoyo)
- [X] T032 [US3] Pintar las zonas de validación en `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Barras de motivos solo sobre lo que llegó (rechazos)
- [X] T033 [US3] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Criterios de validación» → `/red-operativa/gestion/validacion`, roles `DirectorTecnologico` y `Administrador`. **No** incluir `DirectorExpansion`
- [X] T034 [US3] Recorrer [`quickstart.md`](quickstart.md) §2 (Tecnológico entra; Expansión no ve el enlace ni entra)

**Checkpoint**: las tres historias independientes; cada director ve **solo** las suyas.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido en una sola pantalla dejaría mentir a un director, o descubriría al otro cargo.

- [X] T035 [P] Completar `frontend/src/app/modules/red-operativa/gestion/definiciones/pantallas-gestion.definiciones.spec.ts`: las tres pantallas solo citan slugs de `PUBLICADOS_UI`; cada slug aparece **una** vez; unión = 15; ningún slug de validación en `flota`/`mercados`
- [X] T036 [P] Prueba en `frontend/src/app/modules/red-operativa/gestion/pages/pantalla-z.page.spec.ts` de que **no** hay mapa, `leaflet`, exportar, ni botón de alta/baja/validar/despublicar (FR-UI-013, FR-UI-014, FR-UI-018)
- [X] T037 Verificar en `frontend/src/app/shared/layout/nav-links.ts` la matriz de roles (Flota/Mercados sin Tecnológico; Validación sin Expansión) y en `frontend/src/app/modules/red-operativa/informes/` que **no** se añadieron tarjetas Z. Diff vacío en listados
- [X] T038 Ejecutar la suite del frontend (`ng test` del módulo `gestion` de red-operativa / afectados) y `ng build` de producción sin errores nuevos
- [X] T039 Reconstruir con `docker compose -f docker/accidentes.yml up -d --build django frontend` (el frontend se sirve desde nginx; no hay hot-reload) y comprobar `docker ps --filter name=accidentes-` ambos `Up`
- [X] T040 Recorrer [`quickstart.md`](quickstart.md) §5–7: fallo aislado; índice de listados intacto; Proveedor no gana gestión; ninguna coordenada ni nombre de validador
- [X] T041 Documentar hallazgos en `.specify/docs/changelog.md` y marcar la capa frontend en `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/informes-compuestos-modelo.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — **bloquea** US1–US3
- **US1 (Phase 3)**: depende de Phase 2 — MVP
- **US2 (Phase 4)**: depende de Phase 2; reutiliza `apoyo-plegable` de US1 si US1 ya está; si se implementa sola, T018 debe existir
- **US3 (Phase 5)**: depende de Phase 2; no necesita apoyo plegado
- **Polish (Phase 6)**: las tres historias hechas

### User Story Dependencies

- **US1 (P1)**: tras Phase 2. Entregable solo. Demuestra Z **y** exclusión del Tecnológico.
- **US2 (P1)**: tras Phase 2. Extiende la misma página; no rompe Flota. Idealmente después de T018.
- **US3 (P1)**: tras Phase 2. No depende de US1/US2 para ser testeable; comparte `pantalla-z.page.*` y `nav-links.ts`.

US1–US3 tocan `pantalla-z.page.ts` y `nav-links.ts`: en un solo implementador, **secuencial US1 → US2 → US3**. En paralelo, coordinar esos dos ficheros.

### Within Each User Story

- Pruebas primero y en rojo
- Definición de pantalla antes de pintar
- Pintado antes del enlace de sidebar (no anunciar una ruta vacía)
- Recorrido en navegador al cerrar la historia

### Parallel Opportunities

- T002 y T003
- T005, T007, T009 (tras existir los ficheros que prueban)
- T014 con T011–T013 cuando las rutas ya están
- T015 y T016 en paralelo; T017 después (mismo `pantalla-z.page.spec.ts` que T011)
- T023 en paralelo con T024
- T029 en paralelo con T030
- T035 y T036 en Polish

---

## Parallel Example: User Story 1

```text
Task: "Prueba materia y slugs OT12 en definiciones/pantallas-gestion.definiciones.spec.ts"
Task: "Prueba apoyo plegado en pages/apoyo-plegable.component.spec.ts"
```

Luego, en serie: componente de apoyo → rellenar `flota` → pintar zonas → `nav-links` → quickstart §1 y §3.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (Flota y cobertura)
3. **STOP**: Expansión ve cobertura honesta; Tecnológico no ve el enlace
4. Demo / validar SC-F01, SC-F03 (mitad), SC-F04, SC-F05, SC-F08

### Incremental Delivery

1. Setup + Foundational (exclusión ya testeada)
2. US1 → demo MVP
3. US2 → mercados y retirada, con fecha de medida exacta
4. US3 → el Tecnológico tiene su pantalla, Expansión no la ve
5. Polish (15 slugs, listados intactos, Docker)

### Parallel Team Strategy

Un solo implementador: US1 → US2 → US3 por el fichero compartido `pantalla-z.page.ts`.

Si hay dos: A hace US1 completo; B prepara definición y pruebas de US3 (ficheros de spec distintos) y pinta validación después de US1, coordinando `pantalla-z.page.ts`.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- No hay librería de charts (D6)
- Umbral y `dias_objetivo` se **muestran**, no se editan (D7)
- El recorrido en navegador (T022, T028, T034, T040) no lo sustituye Karma: el proxy, el guard real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T039)
