# Tasks: Informes Tácticos Simples de Partners y API — Frontend

**Input**: Design documents from `specs/002-tactico/Partners-API/informes-tacticos-simples/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** El fallo de esta capa es silencioso: un guard de unión le da al Partner las versiones del contrato; pintar motivo en la credencial reúne una revocación con un impago; esconder al Director para coincidir con el `403` deja mintiendo FR-014a.

**Organization**: agrupadas por user story de [`spec.md`](spec.md) (US-FE-1…5 → US1…US5). MVP = US1 (los cinco listados para gestores y Director).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US5 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a esta capa

**Dos guards, no uno.** Acceso (cuatro roles) vs contrato (tres). Un `canActivate` con la unión le da al Partner versiones y alcance **sin síntoma**.

**FR-014a se cierra en backend en Phase 2**, con `es_gestor_informes()` — **no** ensanchando `es_gestor()` de la consola.

**Listados, no Z.** Se consume `frontend/src/app/shared/informes/` y **no se modifica**. Si hiciera falta tocarla, la corrección va allí.

### Cuatro cosas que esta capa tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Un guard de unión de los cuatro roles en contrato** | El Partner vería versiones y alcance (FR-UI-022, D1) |
| **Meter al Director en `es_gestor()`** | Le abriría operación sobre cualquier partner (D0) |
| **Columna de motivo o secreto en credenciales** | FR-UI-027, FR-UI-030 |
| **Añadir informes bajo `partners.routes.ts` sin ir antes en `app.routes.ts`** | El `redirectTo: 'consola'` traga al Partner (D2) |

**Depends-on**: los cinco GET de `../backend/`. Esta capa no calcula filas ni inventa campos.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: el sitio de la capa, sin mezclarlo con consola ni portal.

- [X] T001 Crear el árbol `frontend/src/app/modules/partners/informes/{guards,definiciones,pages/indice,pages/informe}` según [`plan.md`](plan.md). **No** meter ficheros nuevos en las páginas de `frontend/src/app/modules/partners/pages/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: FR-014a, dos guards y la ruta hermana. **Ninguna user story puede empezar hasta que esta fase esté completa.**

**⚠️ CRITICAL**: si el Director sigue en `403`, US1 «pasa» en Karma y miente en el navegador. Si el guard es una unión, US2 «pasa» para el Partner en contrato.

- [X] T002 Añadir `ROL_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"` en `backend/apps/partners/domain_constants.py`
- [X] T003 En `backend/apps/partners/permissions.py`: crear `ROLES_GESTORES_INFORMES` = `ROLES_GESTORES` ∪ `{ROL_DIRECTOR_TECNOLOGICO}` y `es_gestor_informes()`. `InformesAccesoPermission` / `InformesContratoPermission` usan ese conjunto. **`es_gestor()` y `ROLES_GESTORES` no cambian** (D0)
- [X] T004 En `backend/apps/partners/views/informes_views.py`, `acotar()` llama a `es_gestor_informes()`, no a `es_gestor()`
- [X] T005 Extender `backend/apps/partners/tests/api/test_informes_permisos.py`: `DirectorTecnologico` obtiene **200** en los cinco; Partner sigue en **403** en versiones y alcance. Usar el fixture `director_tecnologico_informes_headers` de `backend/apps/partners/tests/conftest.py`
- [X] T006 [P] Extender `backend/apps/partners/tests/unit/test_propiedad_partner.py`: `es_gestor(["DirectorTecnologico"])` es **False**; `es_gestor_informes` es **True**
- [X] T007 En `specs/002-tactico/Partners-API/informes-tacticos-simples/backend/contracts/informes-tacticos-simples.openapi.yaml`, el enum de `entorno` pasa de `Produccion` a `Producción` (D6). Sin campos nuevos
- [X] T008 Crear `frontend/src/app/modules/partners/informes/guards/informes-partners.guard.ts` con **dos** funciones: `informesAccesoGuard` (PartnerIntegracion, DesarrolladorAPIs, Administrador, DirectorTecnologico) e `informesContratoGuard` (los tres de gestión, **sin** Partner). No autenticado → login; otro rol → `access-denied`. **Prohibido** un tercer guard que una las dos audiencias (D1)
- [X] T009 ⚠️ Prueba en `frontend/src/app/modules/partners/informes/guards/informes-partners.guard.spec.ts`: Partner **denegado** en contrato; Operador denegado en ambos; Director y DesarrolladorAPIs pasan ambos; Partner pasa acceso. Un guard de unión fallaría esta prueba en silencio
- [X] T010 Crear `frontend/src/app/modules/partners/informes/partners-informes.routes.ts`: índice + `:informe` con `informesAccesoGuard`; `versiones-contrato` y `alcance-datos` **antes** de `:informe`, path literal, `informesContratoGuard`, `data.informe` (mismo truco que Soporte)
- [X] T011 Registrar `loadChildren` en `frontend/src/app/app.routes.ts` con `path: 'partners/informes'` **antes** de `path: 'partners'` (D2). **No** añadir la ruta dentro de `frontend/src/app/modules/partners/partners.routes.ts`
- [X] T012 Crear el esqueleto `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.ts` con los cinco `id` (`partners`, `credenciales`, `cambios-acceso`, `versiones-contrato`, `alcance-datos`), rutas `partners-api/...` y `INFORMES_CONTRATO` = los dos de contrato. Columnas y filtros se rellenan en US1
- [X] T013 Crear `frontend/src/app/modules/partners/informes/pages/informe/informe.page.ts` (una sola página): resuelve la definición y la pasa a `InformesListadoComponent` / `InformesFiltrosComponent` / `InformesListadoStore`. **No** implementa tabla, paginación ni manejo de error propios
- [X] T014 Crear `frontend/src/app/modules/partners/informes/pages/indice/indice-informes.page.ts` generado **del mismo catálogo**. El filtro por rol se completa en US1/US2; de momento puede mostrar todos los ids

**Checkpoint**: foundation ready — el Director obtiene 200 en la API; el Partner no pasa el guard de contrato; `/partners/informes` no redirige a consola.

---

## Phase 3: User Story 1 — Consultar los cinco listados (Priority: P1) 🎯 MVP

**Goal**: Desarrollador de APIs, Administrador y Director Tecnológico abren los cinco desde el índice, con columnas del contrato, rango de fechas **solo** en cambios de acceso, y `caduca_en_dias` en credenciales.

**Independent Test**: abrir cada uno de los cinco, filtrar, paginar y volver. El índice muestra **cinco** enlaces. No hay recuento total.

### Tests for User Story 1 ⚠️ escribir primero, deben FALLAR

- [X] T015 [P] [US1] Prueba en `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.spec.ts`: los cinco ids; columnas = OpenAPI transcrito (como Cuentas); `admiteRango === true` **solo** en `cambios-acceso`; `caduca_en_dias` solo en credenciales; enum `entorno` = `Sandbox` y `Producción`; enum `estado` de partners = los seis de `domain_constants`
- [X] T016 [US1] En `frontend/src/app/modules/partners/informes/pages/informe/informe.page.spec.ts`: los cuatro de estado actual **no** pintan selector de fechas; `cambios-acceso` sí; **no** hay recuento total ni «página N de M»

### Implementation for User Story 1

- [X] T017 [US1] Rellenar las cinco definiciones en `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.ts` según [`contracts/ui-contract.md`](contracts/ui-contract.md): columnas, filtros, `mensajeVacio` de dominio. `tipo_cambio` lista cada `CAMBIO_*` por separado (D5, D7)
- [X] T018 [US1] En `frontend/src/app/modules/partners/informes/pages/indice/indice-informes.page.ts`, un gestor o el Director ve **cinco** enlaces (`data-testid="indice-informes"` / `enlace-{id}`). Título de gestores, no «mi integración»
- [X] T019 [US1] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **Informes de partners** → `/partners/informes`, roles `Administrador`, `DesarrolladorAPIs`, `DirectorTecnologico`, grupo Partners y API. **No** incluir `PartnerIntegracion` en este ítem (D3)
- [X] T020 [US1] Recorrer [`quickstart.md`](quickstart.md) §1 con `director.tecnologico@demo.tsi.com` / `Tactico2026!` y `maria.suarez.dev@demo.tsi.com`: cinco enlaces, versiones y alcance 200, sin aviso de acotamiento

**Checkpoint**: US1 usable sola. El Partner aún no tiene entrada de menú (US2).

---

## Phase 4: User Story 2 — Ver lo mío y saber que es solo lo mío (Priority: P1)

**Goal**: el Partner ve **tres** listados, con aviso `acotado_a: propios` también en el vacío, sin selector de partner ajeno. Suspendido sigue entrando.

**Independent Test**: entrar como Partner, con y sin filas. No existen para él las pantallas de contrato.

### Tests for User Story 2 ⚠️ escribir primero, deben FALLAR

- [X] T021 [P] [US2] Prueba en `frontend/src/app/modules/partners/informes/pages/indice/indice-informes.page.spec.ts`: Partner ve exactamente `partners`, `credenciales`, `cambios-acceso`; **cero** enlaces de contrato, ni en gris
- [X] T022 [US2] En `frontend/src/app/modules/partners/informes/pages/informe/informe.page.spec.ts`: `acotado_a: propios` muestra aviso; `todos` **no**; vacío con `propios` menciona el acotamiento; con rol Partner el filtro `partner` **no** se pinta (FR-UI-009, D4)

### Implementation for User Story 2

- [X] T023 [US2] Filtrar el índice en `frontend/src/app/modules/partners/informes/pages/indice/indice-informes.page.ts` por audiencia (D1). Título/copy distintos para Partner («Estado de mi acceso»)
- [X] T024 [US2] En `frontend/src/app/modules/partners/informes/pages/informe/informe.page.ts`, omitir el filtro `partner` de la barra cuando el actor es Partner. Gestores lo siguen viendo en los tres de acceso
- [X] T025 [US2] Añadir en `frontend/src/app/shared/layout/nav-links.ts` **Estado de mi acceso** → `/partners/informes`, rol **solo** `PartnerIntegracion`, mismo grupo. **No** fusionar con el ítem de T019
- [X] T026 [US2] Recorrer [`quickstart.md`](quickstart.md) §1 (mitad Partner) y §2: tres enlaces, aviso en vacío, `/partners/informes/versiones-contrato` → access-denied. Partner suspendido sigue entrando a los tres de acceso

**Checkpoint**: US1 y US2 independientes. Consola y portal no se fusionaron.

---

## Phase 5: User Story 3 — Inactiva no dice por qué (Priority: P1)

**Goal**: credenciales indican **si** están activas, nunca **por qué**. La bitácora conserva `revocacion_credencial` y `desactivacion_por_cascada` como tipos propios. Cero secreto en pantalla.

**Independent Test**: abrir credenciales y cambios de acceso; no hay columna de motivo en la primera; los dos tipos no se agrupan en la segunda.

### Tests for User Story 3 ⚠️ escribir primero, deben FALLAR

- [X] T027 [P] [US3] En `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.spec.ts`: credenciales **no** declara `motivo`, `client_secret`, `secret_hash`, `telefono_sms` ni campo equivalente; `tipo_cambio` ofrece `revocacion_credencial` y `desactivacion_por_cascada` como **dos** opciones, no una «inactiva»
- [X] T028 [US3] En `frontend/src/app/modules/partners/informes/pages/informe/informe.page.spec.ts`: una fila `activa: false` no muestra texto de motivo; no aparece secreto en el DOM; Sandbox y Producción pueden coexistir en `data`

### Implementation for User Story 3

- [X] T029 [US3] Verificar (y corregir si US1 se despistó) `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.ts`: credenciales según ui-contract; cambios de acceso no relabelan ni agrupan tipos (D7)
- [X] T030 [US3] Recorrer [`quickstart.md`](quickstart.md) §3: entorno con tilde no produce `400`; bitácora distingue los dos tipos

**Checkpoint**: la corrección de fondo del módulo es visible en pantalla.

---

## Phase 6: User Story 4 — Distinguir vacío, 400 y 403 (Priority: P1)

**Goal**: un filtro malo muestra el `detail` del backend sin Reintentar; un 403 no es tabla vacía; un 500 sí ofrece Reintentar; el vacío de `todos` habla del dominio.

**Independent Test**: forzar cada caso en un listado, sin las otras historias.

### Tests for User Story 4 ⚠️ escribir primero, deben FALLAR

- [X] T031 [P] [US4] En `frontend/src/app/modules/partners/informes/pages/informe/informe.page.spec.ts`: `400` muestra `detail` y **no** Reintentar ni tabla vacía; `403` se distingue del vacío; `500` ofrece Reintentar (FR-UI-013…015)
- [X] T032 [US4] En el mismo spec: `data: []` con `acotado_a: todos` usa `mensajeVacio` de dominio y **no** dice «sin datos»; Operador no llega a la tabla (lo cubre T009 — aquí no se pinta vacío)

### Implementation for User Story 4

- [X] T033 [US4] Confirmar que `informe.page.ts` no intercepta el error de la capa compartida ni lo traduce a `data: []`. Si el `mensajeVacio` de alguna definición dice «sin datos», corregirlo en `informes-partners.definiciones.ts`
- [X] T034 [US4] Recorrer [`quickstart.md`](quickstart.md) §5: Operador en `/partners/informes` → negativa

**Checkpoint**: rechazar en backend ya no se puede pintar como «no hay filas».

---

## Phase 7: User Story 5 — Ausente no es ilimitado ni cero (Priority: P2)

**Goal**: alcance sin configurar ≠ todas las zonas; reactivación sin motivo y partner no suspendido se ven ausentes; `0` de cupo se ve `0`; versiones retiradas no se omiten.

**Independent Test**: las cinco lecturas de [`spec.md`](spec.md) US-FE-5, sobre la misma página.

### Tests for User Story 5 ⚠️ escribir primero, deben FALLAR

- [X] T035 [P] [US5] En `frontend/src/app/modules/partners/informes/pages/informe/informe.page.spec.ts`: `zonas_geograficas: null` → ausente, **sin** texto «ilimitado» / «todas las zonas»; `motivo: null` en reactivación → ausente; `fecha_suspension: null` → ausente; `limite_llamadas_mes: 0` → se ve `0`; una versión con `fecha_retiro` nulo no se omite y una retirada con fecha **aparece**

### Implementation for User Story 5

- [X] T036 [US5] Asegurar formato `lista` en zonas/canales/destinatarios en `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.ts` (arreglo vacío = ausencia, como Cuentas). Sin copy que lea el nulo como permiso total
- [X] T037 [US5] Recorrer [`quickstart.md`](quickstart.md) §4

**Checkpoint**: las cinco historias independientes en comportamiento; comparten página y catálogo.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: lo que un olvido dejaría mentir al Partner, al Director o a quien lea una credencial inactiva.

- [X] T038 [P] Completar `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.spec.ts`: unión de columnas no incluye secreto; `INFORMES_CONTRATO` = exactamente dos ids; filtro `partner` declarado solo en los tres de acceso
- [X] T039 [P] Prueba de cableado en `frontend/src/app/modules/partners/informes/partners-informes-cableado.spec.ts`: contrato usa `informesContratoGuard`; acceso e índice usan `informesAccesoGuard`; `partners.routes.ts` **no** gana hijos de informes ni cambia su `redirectTo`
- [X] T040 Verificar en `frontend/src/app/shared/layout/nav-links.ts` la matriz D3 (dos ítems, misma path, roles disjuntos) y que consola/portal/logs **no** cambiaron
- [X] T041 Ejecutar la suite del frontend afectada (`informes-partners` + guards) y `ng build` de producción sin errores nuevos. Suite de `apps/partners/tests/api/test_informes_permisos.py` verde
- [X] T042 Reconstruir con `docker compose -f docker/accidentes.yml up -d --build django frontend` (el frontend se sirve desde nginx; no hay hot-reload) y comprobar `docker ps --filter name=accidentes-` ambos `Up`
- [X] T043 Recorrer [`quickstart.md`](quickstart.md) §6–7: consola/portal/logs intactos; paginación opaca
- [X] T044 Documentar en `.specify/docs/changelog.md` (FR-014a + enum `entorno`) y marcar la capa frontend en `specs/002-tactico/Partners-API/informes-tacticos-simples/informes-tacticos-simples.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — **bloquea** US1–US5. El parche de backend es parte de esta fase, no un extra
- **US1 (Phase 3)**: depende de Phase 2 — MVP
- **US2 (Phase 4)**: depende de Phase 2; comparte índice, página y `nav-links.ts` con US1
- **US3–US5**: dependen de Phase 2 y del catálogo de US1 (columnas). Son sobre todo pruebas + recorridos
- **Polish (Phase 8)**: las historias deseadas hechas

### User Story Dependencies

- **US1 (P1)**: tras Phase 2. Entregable solo. Demuestra los cinco listados **y** que el Director entra
- **US2 (P1)**: tras Phase 2. Idealmente después de T018 (índice). Añade la segunda entrada de menú
- **US3 (P1)**: tras T017 (definiciones). Independiente para testear; mismo fichero de definiciones
- **US4 (P1)**: tras T013 (página). Independiente
- **US5 (P2)**: tras T017. Independiente

US1–US2 tocan `indice-informes.page.ts`, `informe.page.ts` y `nav-links.ts`: en un solo implementador, **secuencial US1 → US2**. US3–US5 pueden intercalarse como pruebas sobre esos ficheros.

### Within Each User Story

- Pruebas primero y en rojo
- Definición antes de pintar
- Enlace de sidebar después de que la ruta responda (no anunciar un índice vacío)
- Recorrido en navegador al cerrar la historia

### Parallel Opportunities

- T006 y T007 (tras T003)
- T009 en paralelo con T010–T011 cuando el guard ya existe
- T015 en paralelo con T016
- T021 en paralelo con T022
- T027 en paralelo con T028
- T031 en paralelo con T032
- T038 y T039 en Polish

---

## Parallel Example: User Story 1

```text
Task: "Prueba columnas y enums en definiciones/informes-partners.definiciones.spec.ts"
Task: "Prueba rango de fechas y paginación opaca en pages/informe/informe.page.spec.ts"
```

Luego, en serie: rellenar definiciones → índice de cinco → nav gestores → quickstart §1 (Director / Dev APIs).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (FR-014a incluido)
2. Phase 3 (cinco listados para gestores y Director)
3. **STOP**: Director ve cinco; Partner aún sin menú
4. Demo / validar SC-UI-001 (gestores), SC-UI-004

### Incremental Delivery

1. Setup + Foundational (Director 200; exclusión de Partner en contrato ya testeada)
2. US1 → demo MVP
3. US2 → el Partner tiene índice propio y aviso de alcance
4. US3 → inactiva ≠ motivo
5. US4 → 400/403 no son vacío
6. US5 → ausente ≠ ilimitado
7. Polish (Docker, changelog)

### Parallel Team Strategy

Un solo implementador: US1 → US2 → US3 → US4 → US5 por los ficheros compartidos.

Si hay dos: A hace Phase 2 backend + US1; B escribe las pruebas de US2–US5 en los `*.spec.ts` y las implementa cuando la página exista.

---

## Notes

- [P] = ficheros distintos, sin esperar a una tarea incompleta del mismo fichero
- `shared/informes/` no se toca (D4: el filtro `partner` se omite en la página)
- El recorrido en navegador (T020, T026, T030, T034, T037, T043) no lo sustituye Karma: el proxy, el JWT real y nginx solo se ven ahí
- Tras código del aplicativo: rebuild Docker (T042)
- Contraseñas de demo: `password123` (admin, dev, partner, operador) y `Tactico2026!` (Director Tecnológico)
