# Tasks: Informes Compuestos de Suscripciones y Facturación — Frontend

**Input**: Design documents from `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: un guard de unión deja a cada director en la materia del otro **sin síntoma**; un MRR con la cancelada, un 0 % donde no hay datos, o una columna vacía de llamadas, se leen como dato. Las pruebas existen para eso.

**Organization**: agrupadas por user story de [`spec.md`](spec.md). Las tres son P1; el MVP es US1 (Cobro e ingreso).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US3 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**No hay un solo jefe.** Ventas copió un Director y un Gerente sobre las **mismas** tres historias. Aquí **dos guards** (finanzas / catálogo) y tres enlaces con roles distintos. Un `canActivate` con la unión `DirectorFinanciero | DirectorEstrategia` haría pasar US1–US3 para la persona equivocada.

**Tres pantallas nuevas, no el índice de listados ni el catálogo de planes.** `/suscripciones/informes` se ignora. Añadir tarjetas Z ahí, o reutilizar los guards de listados (admiten Cliente/Proveedor), viola FR-UI-001 y FR-UI-022.

**Agrupar por materia, no por OT.** OT06 entero es Cobro; OT07 entero es Movimientos; OT05 entero es Catálogo. Las dos primeras comparten audiencia, **no** pantalla (D5).

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Un guard de unión de departamento** | Cada director vería la materia del otro sin que nada falle (D2, FR-UI-025) |
| **Reusar `informesFinanzasGuard` / `informesCatalogoGuard` de listados** | Esos listados admiten Cliente y Proveedor |
| **Pintar `data: []` como 0 % o mensualizar en cliente** | Convierte vacío o vigencia invertida en cifra de la empresa (D12, FR-UI-006) |
| **Añadir una columna de llamadas, ni vacía** | Un hueco se lee como «no consume la API» (D13, FR-UI-016) |

**Depends-on**: los 13 publicados del backend. Esta capa no calcula cifras ni toca OpenAPI. No extrae la cáscara Z a `shared/` (D1).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con listados, billing ni `emergencias/gestion`.

- [X] T001 Crear el árbol `frontend/src/app/modules/suscripciones/gestion/{guards,definiciones,services,models,pages}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en `frontend/src/app/modules/suscripciones/informes/` ni en `pages/catalogo-planes/`
- [X] T002 [P] Crear `frontend/src/app/modules/suscripciones/gestion/models/informes-compuestos.types.ts` con `PeriodoVista`, `EstadoZona` (`carga | dato | vacio | error | sin_dato`), `Materia` (`finanzas` \| `catalogo`), `DefinicionPantalla` (`id`: `cobro` \| `movimientos` \| `catalogo`, campo `materia`) y `MetaInforme` con `mes`, `nota_periodo` y `filtros` según [`data-model.md`](data-model.md)
- [X] T003 [P] Crear `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.ts` con `PUBLICADOS_UI` (los **13** slugs de `CATALOGO` en `backend/apps/informes_tacticos/services/suscripciones_compuestos_service.py`) y el esqueleto `PANTALLAS` con los tres `id` y su `materia`. Las zonas se rellenan en US1–US3

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: cáscara Z, HTTP, **dos** guards y rutas. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: si el guard es una unión de las dos autoridades, US1 «pasa» para el de Estrategia. La prueba de esta fase es la exclusión, no la entrada.

- [X] T004 Implementar `frontend/src/app/modules/suscripciones/gestion/services/informes-compuestos-api.service.ts`: un `GET` parametrizado a `/api/v1/informes-tacticos/suscripciones/{informe}?desde=&hasta=`. **Un método, no trece.** No envía `escalones_dunning`, `dias_aviso_caducidad` ni `mes` (D7, D8)
- [X] T005 [P] Prueba en `frontend/src/app/modules/suscripciones/gestion/services/informes-compuestos-api.service.spec.ts` de que la URL incluye el slug y el período, el prefijo es `suscripciones` (no `ventas-crm` ni `emergencias`), y de que **no** hay un método por informe ni query de escalones
- [X] T006 Crear `frontend/src/app/modules/suscripciones/gestion/guards/suscripciones-gestion.guard.ts` con **dos** funciones: `gestionFinanzasGuard` (`DirectorFinanciero` \| `Administrador`) y `gestionCatalogoGuard` (`DirectorEstrategia` \| `Administrador`) (D2). No autenticado → login; otro rol → `access-denied`. **Prohibido** un tercer guard que una las dos materias
- [X] T007 ⚠️ Prueba en `frontend/src/app/modules/suscripciones/gestion/guards/suscripciones-gestion.guard.spec.ts`: **Financiero denegado en catálogo**; **Estrategia denegado en finanzas**; Administrador pasa las dos; Cliente, Proveedor y Operador denegados en ambas. Un guard de unión fallaría esta prueba en silencio
- [X] T008 Crear `frontend/src/app/modules/suscripciones/gestion/models/estado-zona.ts`: `data: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. **Nunca** mapear vacío a 0. Conservar `meta` (incluido `mes` y `nota_periodo`) también en `vacio`
- [X] T009 [P] Prueba en `frontend/src/app/modules/suscripciones/gestion/models/estado-zona.spec.ts` de que `[]` no es `dato` con ceros, de que `pct_renovacion: null` es `sin_dato` y no `0`, y de que un envelope vacío **sigue exponiendo** `mes` / `nota_periodo`
- [X] T010 Implementar la cáscara `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`: una sola página, resuelve `PANTALLAS` por el segmento de ruta, pinta las zonas con `data-testid` `zona-heroe`, `zona-periodo`, `zona-mes`, `zona-visual`, `zona-lectura`. Reutilizar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.ts`. **Prohibido** importar `InformeCardComponent`. Cada zona dispara su GET en paralelo (D9). `zona-mes` pinta `meta.mes` y `meta.nota_periodo` del envelope, **no** un mes calculado en cliente (D8)
- [X] T011 Prueba en `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.spec.ts`: un error en una zona deja las otras visibles; cambiar el período vuelve a pedir **todas** las zonas de la definición; `meta.mes: '2026-07'` se lee en `zona-mes` aunque el período pedido sea otro rango
- [X] T012 Crear `frontend/src/app/modules/suscripciones/gestion/suscripciones-gestion.routes.ts` con `cobro` y `movimientos` → `PantallaZPage` + `gestionFinanzasGuard`; `catalogo` → la misma página + `gestionCatalogoGuard` (D3). **No** un `canActivate` común a las tres
- [X] T013 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` bajo `path: 'suscripciones/gestion'`. **No** colgar estas rutas de `frontend/src/app/modules/suscripciones/suscripciones.routes.ts` ni de `informes/suscripciones-informes.routes.ts`
- [X] T014 [P] Prueba de cableado en `frontend/src/app/modules/suscripciones/gestion/suscripciones-gestion-cableado.spec.ts`: `cobro`/`movimientos` usan `gestionFinanzasGuard`; `catalogo` usa `gestionCatalogoGuard`; `suscripciones-informes.routes.ts` **no** cambia de guard ni gana pantallas Z

**Checkpoint**: foundation ready — se puede abrir la cáscara (vacía de cifras) solo con el rol de esa materia.

---

## Phase 3: User Story 1 — Cobro e ingreso (Priority: P1) 🎯 MVP

**Goal**: el Director Financiero ve cuánto entra y si se cobra. MRR (con variación y `sin_periodicidad` aparte) como héroe; ingresos con notas de crédito a la vista; tasa de renovación abajo; cobro al primer intento, dunning y clientes sin método **plegados**.

**Independent Test**: suscripción cancelada **no** aporta al héroe (el backend ya la excluye; la UI no la «recupera»). Estrategia **no** ve el enlace ni entra. Período sin datos → vacío, no 0 %. Vista principal ≤ 8 bloques. `zona-mes` declara el mes natural.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `cobro.materia === 'finanzas'` y de que sus slugs son exactamente los seis de OT06 (`mrr`, `ingresos`, `tasa-renovacion`, `cobro-primer-intento`, `efectividad-dunning`, `clientes-sin-metodo-pago`)
- [X] T016 [P] [US1] Prueba en `frontend/src/app/modules/suscripciones/gestion/pages/apoyo-plegable.component.spec.ts`: el bloque nace **plegado**; al abrirse muestra los tres de apoyo y no sustituye el visual grande
- [X] T017 [US1] En `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.spec.ts`: `data: []` no pinta 0 %; `sin_periodicidad` se ve aparte; `notas_credito` visible junto a `facturado` / `ingreso_neto`; `zona-mes` presente; las cuatro `data-testid` del Z están; recuento de bloques de la vista principal ≤ 8; el apoyo de «sin método» **no** enlaza a `/suscripciones/metodos-pago`

### Implementation for User Story 1

- [X] T018 [US1] Crear `frontend/src/app/modules/suscripciones/gestion/pages/apoyo-plegable.component.ts` (y template) para el segundo plano de Cobro (tres informes) — se reutiliza en US2
- [X] T019 [US1] Rellenar la definición `cobro` en `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `mrr`, visual `ingresos`, lectura `tasa-renovacion`, apoyo los tres restantes, `apoyoPlegado: true`. Contrato: [`contracts/ui-contract.md`](contracts/ui-contract.md)
- [X] T020 [US1] Pintar héroe (MRR + nuevo/expansión/contracción/baja + `sin_periodicidad` + moneda), barras de ingresos por plan (Tailwind, D6) con `notas_credito` restando, lectura de renovación y apoyo plegado en `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.html` (y la lógica en `pantalla-z.page.ts`). `meta.filtros` de dunning se **lee**, no se edita (D7). Nombre comercial sí; instrumento de cobro no (D14)
- [X] T021 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **solo** «Cobro e ingreso» → `/suscripciones/gestion/cobro`, roles `DirectorFinanciero` y `Administrador`, grupo Suscripciones. **No** incluir `DirectorEstrategia`. **No** tocar el enlace «Informes de suscripciones»
- [X] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §1 y §3 en el navegador (Financiero entra, Estrategia no ve el enlace; cancelada fuera, notas restan, `sin_periodicidad` aparte, apoyo plegado, 1999 vacío)

**Checkpoint**: US1 usable sola. Movimientos y catálogo aún no tienen enlace.

---

## Phase 4: User Story 2 — Movimientos de cartera (Priority: P1)

**Goal**: NRR de quienes **ya estaban** (componentes visibles, mes natural declarado); movimientos clasificados por **delta de precio**; tiempo de resolución con pendientes aparte; suspensión / reactivación plegada.

**Independent Test**: un cliente nuevo del mes **no** aparece como retención (el backend ya lo excluye; la UI no lo «completa»). Un cambio a nivel superior más barato se lee como downgrade (el tipo llega; no se retitula). Estrategia no entra. Pendiente no mejora la mediana.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T023 [P] [US2] Prueba en `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `movimientos.materia === 'finanzas'` y de que incluye `nrr`, `movimientos-plan`, `tiempo-resolucion-solicitudes`, `suspension-reactivacion` — y **no** `distribucion-cartera` ni `mrr`
- [X] T024 [US2] En `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.spec.ts`: `pendientes` visible; `segundos_mediana: null` → sin dato, no 0 s; `tipo_movimiento` se pinta tal cual (no se mapea «upgrade» por `nivel`); `zona-mes` presente; un 500 de `suspension-reactivacion` no vacía `zona-heroe`; **ninguna** columna de administrador/persona

### Implementation for User Story 2

- [X] T025 [US2] Rellenar la definición `movimientos` en `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `nrr`, visual `movimientos-plan`, lectura `tiempo-resolucion-solicitudes`, apoyo `suspension-reactivacion`, `apoyoPlegado: true`
- [X] T026 [US2] Pintar las zonas de movimientos en `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Componentes del NRR visibles. Reutilizar `apoyo-plegable.component.ts` (D10, D12)
- [X] T027 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Movimientos de cartera» → `/suscripciones/gestion/movimientos`, roles `DirectorFinanciero` y `Administrador`. Distinto del listado de solicitudes de cambio
- [X] T028 [US2] Recorrer [`quickstart.md`](quickstart.md) §4 (NRR, delta de precio, pendiente aparte)

**Checkpoint**: US1 y US2 independientes. Catálogo aún sin enlace. Estrategia sigue sin ver estas dos.

---

## Phase 5: User Story 3 — Catálogo y uso (Priority: P1)

**Goal**: el Director de Estrategia ve si el catálogo se usa: distribución (plan de precio cero cuenta y aporta 0); utilización usado **y** contratado, con `nota_dimension_pendiente`; severidades habilitadas y no usadas. Sin apoyo. Sin columna de llamadas. Financiero no ve el enlace.

**Independent Test**: plan de precio cero visible en ambas cifras. 5 de 25 se lee con ambos números. Ninguna zona se titula llamadas. Financiero no entra.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T029 [P] [US3] Prueba en `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.spec.ts` de que `catalogo.materia === 'catalogo'`, de que sus slugs son **exactamente** `distribucion-cartera`, `utilizacion-limites`, `severidades-habilitadas-vs-usadas`, y de que **no** cita `mrr` ni `nrr`
- [X] T030 [US3] En `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.spec.ts`: un plan con `mrr_aportado: 0` y `clientes > 0` **aparece**; `unidades_usadas` y `unidades_limite` se ven (no solo %); `nota_dimension_pendiente` visible; el template **no** contiene `llamadas`, `api` ni `CAC`; `data: []` no pinta 0 %; **no** hay `zona-mes` obligatoria en esta pantalla

### Implementation for User Story 3

- [X] T031 [US3] Rellenar la definición `catalogo` en `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.ts`: héroe `distribucion-cartera`, visual `utilizacion-limites`, lectura `severidades-habilitadas-vs-usadas` (sin zona de apoyo)
- [X] T032 [US3] Pintar las zonas de catálogo en `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.ts` y `pantalla-z.page.html`. Filas de utilización por `plan`; `idcliente` no se resuelve a persona ni fiscal (D15). Prohibido inventar campo de llamadas (D13)
- [X] T033 [US3] Añadir en `frontend/src/app/shared/layout/nav-links.ts` «Catálogo y uso» → `/suscripciones/gestion/catalogo`, roles `DirectorEstrategia` y `Administrador`. **No** incluir `DirectorFinanciero`. **No** tocar `/suscripciones/catalogo-planes`
- [X] T034 [US3] Recorrer [`quickstart.md`](quickstart.md) §2 (Estrategia entra; Financiero no ve el enlace ni entra; sin columna de llamadas)

**Checkpoint**: las tres historias independientes; cada director ve **solo** las suyas.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido en una sola pantalla dejaría mentir a un director, o descubriría al otro cargo.

- [X] T035 [P] Completar `frontend/src/app/modules/suscripciones/gestion/definiciones/pantallas-gestion.definiciones.spec.ts`: las tres pantallas solo citan slugs de `PUBLICADOS_UI`; cada slug aparece **una** vez; unión = 13; ningún slug de catálogo en `cobro`/`movimientos`
- [X] T036 [P] Prueba en `frontend/src/app/modules/suscripciones/gestion/pages/pantalla-z.page.spec.ts` de que **no** hay mapa, `leaflet`, exportar, botón de emitir/cobrar/cambiar plan, texto `llamadas`, ni enlace a `metodos-pago` (FR-UI-018, FR-UI-019, FR-UI-023)
- [X] T037 Verificar en `frontend/src/app/shared/layout/nav-links.ts` la matriz de roles (Cobro/Movimientos sin Estrategia; Catálogo sin Financiero) y en `frontend/src/app/modules/suscripciones/informes/` más `pages/catalogo-planes/` que **no** se añadieron tarjetas Z. Diff vacío en listados y billing
- [X] T038 Ejecutar la suite del frontend (`ng test` del módulo `gestion` de suscripciones / afectados) y `ng build` de producción sin errores nuevos
- [X] T039 Reconstruir con `docker compose -f docker/accidentes.yml up -d --build django frontend` (el frontend se sirve desde nginx; no hay hot-reload) y comprobar `docker ps --filter name=accidentes-` ambos `Up`
- [X] T040 Recorrer [`quickstart.md`](quickstart.md) §5–7: fallo aislado; índice de listados y catálogo de planes intactos; Cliente no gana gestión; ningún token, fiscal ni identidad de administrador
- [X] T041 Documentar hallazgos en `.specify/docs/changelog.md` y marcar la capa frontend en `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/informes-compuestos-modelo.md`

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

- **US1 (P1)**: tras Phase 2. Entregable solo. Demuestra Z **y** exclusión de Estrategia.
- **US2 (P1)**: tras Phase 2. Extiende la misma página; no rompe Cobro. Idealmente después de T018.
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
Task: "Prueba materia y slugs OT06 en definiciones/pantallas-gestion.definiciones.spec.ts"
Task: "Prueba apoyo plegado en pages/apoyo-plegable.component.spec.ts"
```

Luego, en serie: componente de apoyo → rellenar `cobro` → pintar zonas → `nav-links` → quickstart §1 y §3.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (Cobro e ingreso)
3. **STOP**: Financiero ve cobro honesto; Estrategia no ve el enlace
4. Demo / validar SC-F01, SC-F03 (mitad), SC-F04, SC-F05, SC-F08, SC-F11

### Incremental Delivery

1. Setup + Foundational (exclusión ya testeada)
2. US1 → demo MVP
3. US2 → movimientos y NRR, con pendientes aparte
4. US3 → Estrategia tiene su pantalla, Financiero no la ve
5. Polish (13 slugs, listados intactos, Docker)

### Parallel Team Strategy

Un solo implementador: US1 → US2 → US3 por el fichero compartido `pantalla-z.page.ts`.

Si hay dos: A hace US1 completo; B prepara definición y pruebas de US3 (ficheros de spec distintos) y pinta catálogo después de US1, coordinando `pantalla-z.page.ts`.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- No hay librería de charts (D6)
- Escalones de dunning y días de aviso se **muestran**, no se editan (D7)
- `meta.mes` / `nota_periodo` se pintan; no se recalculan (D8)
- El recorrido en navegador (T022, T028, T034, T040) no lo sustituye Karma: el proxy, el guard real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T039)
