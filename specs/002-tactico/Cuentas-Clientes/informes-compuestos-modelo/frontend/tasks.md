# Tasks: Informes Compuestos de Cuentas y Clientes — Frontend

**Input**: Design documents from `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/frontend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/ui-contract.md`](contracts/ui-contract.md), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Reusar el guard de listados deja entrar al Tecnológico al churn. Pintar ocupación sin cobertura afirma una cartera falsa. Omitir etapas en cero afirma un embudo perfecto.

**Organization**: US1 P1 (ciclo), US2 P2 (incorporación), US3 P3 (acceso). El MVP es US1 más la exclusión de menú.

## Format: `[ID] [P?] [Story] Description`

---

## ⚠️ Lo que distingue a esta capa

**Autoridad partida.** Dos guards, nunca una unión (D2).

**Tres pantallas nuevas**, no los listados ni `gestion-cuenta`.

**El envelope es `{ resultados }`**, no un array (D4).

**Una cáscara Z copiada**, no extraída (D1).

### Cuatro cosas prohibidas

| Prohibido | Por qué |
|---|---|
| **Un guard unión** | El Tecnológico vería el churn (D2) |
| **Ocupación sin cobertura** | El 9,5 % se lee como cartera real (D5) |
| **Filtrar etapas con cero** | Embudo perfecto falso (D6) |
| **Pintar multi-rol como hallazgo** | Es el mecanismo previsto (D8) |

**Depends-on**: los 9 publicados. No extrae Z a `shared/`. Docker aplazado (D14).

---

## Phase 1: Setup

- [X] T001 Crear el árbol `frontend/src/app/modules/cuentas-clientes/gestion/{guards,definiciones,services,models,pages}`. **No** meter ficheros en `informes/` ni en `gestion-cuenta/`
- [X] T002 [P] Crear `models/informes-compuestos.types.ts` con `IdPantalla` (`ciclo` \| `incorporacion` \| `acceso`), `Materia`, envelope `{ resultados }` y `extraerResultados`. **`data` no es un array**. Notas: `nota_cobertura`, `nota_catalogo`, `nota_solape`
- [X] T003 [P] Crear `definiciones/pantallas-gestion.definiciones.ts` con `PUBLICADOS_UI` (los **9** slugs) y el esqueleto `PANTALLAS`. Las zonas se rellenan en US1–US3

---

## Phase 2: Foundational (bloquea US1–US3)

- [X] T004 Implementar `services/informes-compuestos-api.service.ts`: un `GET` a `/api/v1/informes-tacticos/cuentas/{informe}?desde=&hasta=`. **Un método, no nueve.** No envía `dias_inactividad`, `mes_cohorte` ni `pares_incompatibles` (D11)
- [X] T005 [P] Prueba del servicio: prefijo `cuentas`, no `partners` ni `suscripciones`; no hay un método por informe; el GET no manda filtros extra
- [X] T006 Crear `guards/cuentas-gestion.guard.ts` con **dos** guards: ciclo/incorporación = `Administrador`; acceso = `DirectorTecnologico` \| `Administrador`. **Prohibido** un array unión usado en las tres rutas
- [X] T007 ⚠️ Prueba de guards: Tecnológico **pasa** acceso y **falla** ciclo/incorporación; Administrador pasa las tres; Cliente/Operador denegados; sin autenticar → login
- [X] T008 Crear `models/estado-zona.ts`: `resultados: []` → `vacio`; métrica `null` → `sin_dato`; 4xx/5xx → `error`. Conservar notas en vacío. `sin_actividad_conocida = 1` es **dato**
- [X] T009 [P] Prueba de estado-zona: vacío ≠ ceros; `tope_plan` nulo → `sin_dato`; envelope extrae `resultados`
- [X] T010 Implementar cáscara `pages/pantalla-z.page.ts` + html: una página, `data-testid` de las cuatro zonas. Reutilizar `PeriodoSelectorComponent`. **Prohibido** `InformeCardComponent`. GET en paralelo salvo concurrencia compartida (D12). Pintar notas de `meta`
- [X] T011 Prueba de cáscara: error en una zona deja las otras; cambiar período vuelve a pedir
- [X] T012 Crear `cuentas-gestion.routes.ts`: `ciclo` e `incorporacion` → guard admin; `acceso` → guard acceso
- [X] T013 Registrar `loadChildren` en `app.routes.ts` bajo `path: 'cuentas-clientes/gestion'`, **sin** colgarlo de `gestion-cuenta` ni de `informes`
- [X] T014 [P] Prueba de cableado: las tres rutas usan el guard correcto; informes y gestion-cuenta no ganan pantallas Z

**Checkpoint**: cáscara vacía de cifras, solo con el rol correcto.

---

## Phase 3: User Story 1 — Ciclo de vida (P1) 🎯 MVP

- [X] T015 [P] [US1] Prueba de definiciones: `ciclo` cita exactamente `churn-por-cohorte`, `usuarios-vs-tope`, `cuentas-en-riesgo`, `antiguedad-media`
- [X] T016 [US1] En `pantalla-z.page.spec.ts`: churn por `cohorte_alta`; ocupación con cobertura en el mismo bloque; sin plan → sin dato; sin actividad conocida ≠ 0 días; `resultados: []` no pinta 0 %; bloques ≤ 8; sin token/nombre
- [X] T017 [P] [US1] Prueba de apoyo plegado: nace plegado; antigüedad no sustituye el visual
- [X] T018 [US1] Crear `pages/apoyo-plegable.component.ts`
- [X] T019 [US1] Rellenar definición `ciclo`
- [X] T020 [US1] Pintar zonas de ciclo en la página
- [X] T021 [US1] Añadir en `nav-links.ts` **solo** «Ciclo de vida» → `/cuentas-clientes/gestion/ciclo`, rol `Administrador`. **No** tocar «Informes de cuentas» ni «Gestión de cuenta»
- [X] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §1–2 (pruebas unitarias equivalentes)

**Checkpoint**: US1 usable sola.

---

## Phase 4: Exclusión de menú (P1)

- [X] T023 [P] [US1] En cableado: `/cuentas-clientes/gestion/ciclo` e `incorporacion` **no** incluyen `DirectorTecnologico`; `acceso` sí. `/cuentas-clientes/informes` **sigue** admitiendo al Tecnológico
- [X] T024 Verificar que no hay ítems grises de gestión para Cliente/Operador

---

## Phase 5: User Story 2 — Incorporación (P2)

- [X] T025 [P] [US2] Definición `incorporacion` cita exactamente `tiempo-onboarding`, `embudo-abandono`, `tasa-aprobacion`
- [X] T026 [US2] Página: etapa con cero **visible**; `en_proceso` no es 0 días; `nota_catalogo` visible; sin identidad
- [X] T027 [US2] Rellenar definición y pintar zonas
- [X] T028 [US2] Nav: «Incorporación de cuentas» → `/cuentas-clientes/gestion/incorporacion`, solo Administrador
- [X] T029 [US2] Quickstart §3 (pruebas)

---

## Phase 6: User Story 3 — Acceso (P3)

- [X] T030 [P] [US3] Definición `acceso` cita `concurrencia-sesiones` y `roles-incompatibles`
- [X] T031 [US3] Página: un GET de concurrencia alimenta héroe/visual/apoyo; `concurrencia_maxima` e inicios juntos; `sesiones_sin_cierre` a la vista; roles vacíos ≠ multi-rol; `idusuario` sin nombre; sin mapa
- [X] T032 [US3] Pintar zonas; GET compartido
- [X] T033 [US3] Nav: «Acceso de cuentas» → `/cuentas-clientes/gestion/acceso`, Tecnológico + Administrador
- [X] T034 [US3] Quickstart §4–5 (pruebas)

---

## Phase 7: Polish

- [X] T035 [P] Las tres pantallas solo citan slugs de `PUBLICADOS_UI`; unión = 9; ningún slug de listados
- [X] T036 [P] Página: no hay mapa, exportar, baja, token, nombre, correo
- [X] T037 Verificar diff vacío en `informes/` y `gestion-cuenta/` salvo lo ajeno
- [X] T038 Ejecutar la suite del módulo y `ng build` de producción
- [X] T039 Docker **aplazado** (D14 / petición del usuario)
- [X] T040 Documentar en `.specify/docs/changelog.md` y marcar la capa en el índice del módulo

---

## Dependencies

- Setup → Foundational → US1 → exclusión → US2 → US3 → Polish
- US1, US2, US3 tocan `pantalla-z.page.ts`: secuencial en un solo implementador

## Implementation Strategy

1. Phase 1 + 2
2. US1 + exclusión (MVP)
3. US2
4. US3
5. Polish sin Docker
