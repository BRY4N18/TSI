# Tasks: OE1 — Posicionamiento y Captación Digital — Backend

**Input**: Design documents from `specs/001-estrategico/OE1-posicionamiento-captacion/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/informes-estrategicos-oe1.openapi.yaml`](contracts/informes-estrategicos-oe1.openapi.yaml), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Constitución ≥80 % en servicios. Un MRR sin mensualizar o un CAC de 0 € no se ven en un 200.

**Organization**: US1–US4 de [`spec.md`](spec.md). MVP = US1. US4 (bloqueados) es barata: adelantarla tras Foundational.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: ficheros distintos, sin dependencias pendientes
- **[US1]–[US4]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Publica 10 de 13. Cero tablas nuevas.** E1-05, E1-07 y E1-08 no tienen SQL ni path.

**No se recrea `dim_cliente`.** No hay eje de país. Onboarding/churn **solo Gerente**.

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Sumar `precio` sin `precio_mensualizado`** | Una anual infla el MRR ×12 |
| **CREATE/ALTER `dim_cliente`** | Dimensión conformada de Cuentas |
| **Agrupar por país/estado** | La columna no existe; el objetivo no mide mercados |
| **Publicar CAC = 0** | No hay costos de marketing |
| **Embudo solo con etapas completadas** | 100 % de onboarding falso |
| **Denominador de renovación = activas** | La tasa mejora sola si nadie vence |
| **% de churn con n=4 sin declarar** | Un abandono es un «25 %» anecdótico |
| **Segunda SQL en OE5** | Dueño único E1-06/09/10/11 |
| **Medios de cobro o ficha personal** | Exclusión más estricta del dominio comercial |
| **Permiso de módulo único** | Marketing vería MRR o Cuentas vería churn |

Slugs HTTP: `mrr-mensual`, `arr-proyeccion`, `mrr-por-segmento`, `cartera-por-plan`, `embudo-conversion`, `velocidad-ciclo-venta`, `tasa-renovacion`, `tiempo-onboarding`, `abandono-onboarding`, `churn-por-cohorte`. **No** `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado`.

---

## Phase 1: Setup

**Purpose**: armazón y carpeta SQL. Sin esto no hay HTTP.

**Independent Test**: el cargador resuelve `estrategicos/oe1`; la ruta Django existe (stub).

- [x] T001 Verificar el armazón `informes_estrategicos`: `backend/apps/informes_estrategicos/periodo_estrategico.py`, `objetivo.py`, `envelope.py`, `permissions.py`, `core/repositories/informes_estrategicos/`. Si falta, fases 1–2 de `specs/001-estrategico/OE6-respuesta-y-vidas/backend/tasks.md`
- [x] T002 Anotar en [`quickstart.md`](quickstart.md) §1: `EXISTS TABLE hecho_suscripcion`, `count()` de `hecho_suscripcion FINAL`, `dim_cliente FINAL`, `hecho_transicion_embudo`, `hecho_onboarding` (origen 2026-08-16: 4 / 4 / transiciones / 3)
- [x] T003 Crear `dags/lib/consultas/estrategicos/oe1/README.md` con convención `e1_NN_<informe>.sql`, `FINAL` en dimensiones y `hecho_suscripcion`, **nunca** `FINAL` en `hecho_factura` / `hecho_transicion_embudo` / `hecho_onboarding`, y **ningún** `e1_05_*.sql` / `e1_07_*.sql` / `e1_08_*.sql`
- [x] T004 [P] Añadir en `dags/tests/test_catalogo_estrategicos_oe1.py` que el cargador resuelve `departamento="estrategicos/oe1"`
- [x] T005 [P] Registrar `informes-estrategicos/oe1/<str:informe>` en `backend/apps/informes_estrategicos/urls.py` apuntando a `Oe1View` (import en stub hasta T010)

---

## Phase 2: Foundational

**Purpose**: autoridad partida, servicio vacío y 404 de los tres bloqueados. **Bloquea US1–US4.**

**Independent Test**: Gerente no 403 en un slug publicado desconocido para SQL; GET a `cac-por-canal` → 404; Marketing 403 en `mrr-mensual`.

- [x] T006 Añadir en `backend/core/auth/roles_tacticos.py`: `AUTORIDAD_OE1`, `AUTORIDAD_OE1_FINANZAS` (`DirectorFinanciero`, `Gerente`), `AUTORIDAD_OE1_ESTRATEGIA` (`DirectorEstrategia`, `Gerente`; Finanzas extra en segmento), `AUTORIDAD_OE1_MARKETING` (`DirectorMarketing`, `Gerente`), `AUTORIDAD_OE1_CICLO` (`Gerente` solo)
- [x] T007 Ampliar `backend/apps/informes_estrategicos/permissions.py` con `Oe1Permission` y mapa por slug: `mrr-mensual`/`arr-proyeccion`/`tasa-renovacion` → FINANZAS; `mrr-por-segmento` → FINANZAS ∪ ESTRATEGIA; `cartera-por-plan` → ESTRATEGIA; `embudo-conversion`/`velocidad-ciclo-venta` → MARKETING; `tiempo-onboarding`/`abandono-onboarding`/`churn-por-cohorte` → CICLO; desconocido/bloqueado → 404 de vista, no 403
- [x] T008 Implementar `backend/apps/informes_estrategicos/services/oe1_service.py` con `CATALOGO` (10 slugs), `PUBLICADOS`, `BLOQUEADOS={"cac-por-canal","mercados-activos","cartera-mrr-por-mercado"}`, `DEPARTAMENTO="estrategicos/oe1"`. Forzar `cobertura: parcial` + `falta` de muestra mientras n < umbral (defecto 20). `cumple` de objetivo siempre `null`
- [x] T009 Implementar `backend/apps/informes_estrategicos/views/oe1_views.py` al patrón de `oe2_views.py` (`IsAuthenticated401`, `Oe1Permission`, envelope, 400 de período)
- [x] T010 Completar el import de `Oe1View` en `backend/apps/informes_estrategicos/urls.py`
- [x] T011 [P] Prueba de **exclusión** en `backend/apps/informes_estrategicos/tests/api/test_permisos_oe1.py`: Marketing 403 en `mrr-mensual`; Financiero 403 en `embudo-conversion`; Estrategia 403 en `tiempo-onboarding`; Gerente no 403 en las diez; partner 403 en todas
- [x] T012 [P] Prueba en `backend/apps/informes_estrategicos/tests/api/test_oe1_bloqueados.py`: GET `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado` → **404** (también con Gerente)
- [x] T013 [P] En `dags/tests/test_catalogo_estrategicos_oe1.py`: ninguna consulta nombra `idpais`/`idestado`/`tiene_metodo_pago`/`metodo_pago_caduca`; `SELECT *` prohibido; `ORDER BY` obligatorio; `{desde:Date}` `{hasta:Date}` `{granularidad:String}`; `FINAL` en dims y `hecho_suscripcion`; **cero** ficheros `e1_05_*` / `e1_07_*` / `e1_08_*`; ninguna SQL crea tabla

**Checkpoint**: ruta viva, permisos partidos, tres 404. SQL de informes puede empezar.

---

## Phase 3: User Story 1 — Ingreso recurrente (Priority: P1) 🎯 MVP

**Goal**: E1-01, E1-02, E1-03, E1-12.

**Independent Test**: MRR usa `precio_mensualizado` y trae recuento; ARR declara extrapolación; segmento por `tipo`; cobertura parcial.

- [x] T014 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe1/e1_01_mrr_mensual.sql`: suma `precio_mensualizado` de vigentes **al cierre**; recuento; `alcance` en servicio (criterio de cierre)
- [x] T015 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe1/e1_02_arr_proyeccion.sql`: MRR×12; no es compromiso
- [x] T016 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe1/e1_03_mrr_por_segmento.sql`: `dim_cliente.tipo`; desconocidos agrupados; **sin país**
- [x] T017 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe1/e1_12_cartera_por_plan.sql`: mezcla y evolución, no solo foto
- [x] T018 [US1] Registrar los cuatro slugs en `CATALOGO` de `backend/apps/informes_estrategicos/services/oe1_service.py`; `alcance` de E1-01 y E1-02
- [x] T019 [P] [US1] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe1_us1_contract.py` (período obligatorio, envelope, slugs OpenAPI)
- [x] T020 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_mrr_mensualizado.py`: una anual no vale 12× un mensual del mismo precio anualizado (falsable)
- [x] T021 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_arr_extrapolacion.py`: `alcance` nombra extrapolación
- [x] T022 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_cobertura_parcial.py`: con n demo, `cobertura: parcial` y `falta` nombra muestra
- [x] T023 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_sin_cobro.py`: ninguna clave es medio de pago, hash o contacto
- [x] T024 [US1] Recorrer [`quickstart.md`](quickstart.md) §2.1–2.3 (pruebas equivalentes)

**Checkpoint**: MVP. El tablero financiero ve MRR sin mentir periodicidad.

---

## Phase 4: User Story 4 — Bloqueados (Priority: P4)

**Goal**: E1-05/07/08 no existen. Barata; adelantar tras T013.

**Independent Test**: OpenAPI no declara las tres rutas; GET → 404.

- [x] T025 [P] [US4] En `backend/apps/informes_estrategicos/tests/api/test_openapi_conforme_oe1.py`: los diez `PUBLICADOS` están en `specs/001-estrategico/OE1-posicionamiento-captacion/backend/contracts/informes-estrategicos-oe1.openapi.yaml`; `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado` **no**
- [x] T026 [US4] Confirmar `test_oe1_bloqueados.py` cubre alias `cac-por-canal` / `mercados-activos` / `cartera-mrr-por-mercado`
- [x] T027 [US4] Documentar en el índice del módulo y en [`quickstart.md`](quickstart.md) §2.8 que dos KPI BSC (CAC, mercados) quedan sin fuente

**Checkpoint**: nadie puede «arreglar» el hueco publicando 0.

---

## Phase 5: User Story 2 — Captación (Priority: P2)

**Goal**: E1-04, E1-13.

**Independent Test**: etapa en cero visible; volumen no creciente; sin ficha de prospecto.

- [x] T028 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe1/e1_04_embudo_conversion.sql`: grano transiciones; etapas en cero; `alcance` de cruce con Cuentas en el servicio
- [x] T029 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe1/e1_13_velocidad_ciclo_venta.sql`: tiempo por etapa; `idejecutivo` de cartera, **sin** identidad de prospecto
- [x] T030 [US2] Registrar slugs en `backend/apps/informes_estrategicos/services/oe1_service.py`
- [x] T031 [P] [US2] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe1_us2_contract.py`
- [x] T032 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_embudo_ceros.py`: etapa vacía presente; volumen no crece
- [x] T033 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_sin_prospecto.py`: respuesta sin nombre/contacto de prospecto
- [x] T034 [US2] Quickstart §2.4 (pruebas)

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Ciclo de vida (Priority: P3)

**Goal**: E1-06, E1-09, E1-10, E1-11. Dueño de E5-09/13/14/10.

**Independent Test**: denominador de renovación = vencidas; onboarding contra catálogo; churn sin % si n bajo; solo Gerente.

- [x] T035 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe1/e1_06_tasa_renovacion.sql`: denominador = vencidas en el período
- [x] T036 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe1/e1_09_tiempo_onboarding.sql`: días; en proceso aparte, no cero días
- [x] T037 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe1/e1_10_abandono_onboarding.sql`: LEFT JOIN `dim_etapa_onboarding`; ceros del catálogo
- [x] T038 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe1/e1_11_churn_por_cohorte.sql`: `cohorte_alta`; n < umbral → sin porcentaje (null), no 25 %
- [x] T039 [US3] Registrar los cuatro slugs; documentar dueño OE5 en comentario de `backend/apps/informes_estrategicos/services/oe1_service.py`
- [x] T040 [P] [US3] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe1_us3_contract.py`
- [x] T041 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_renovacion_vencidas.py`: denominador no es stock de activas
- [x] T042 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_onboarding_catalogo.py`: etapa de catálogo con 0 completadas visible
- [x] T043 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_churn_sin_muestra.py`: n=4 no publica % como KPI cerrado
- [x] T044 [US3] Quickstart §2.5–2.7 (pruebas)

**Checkpoint**: US3 independiente. OE5 podrá referenciar.

---

## Phase 7: Polish

- [x] T045 [P] Completar `backend/apps/informes_estrategicos/tests/api/test_openapi_conforme_oe1.py`: YAML sin cobro, país, contacto; slugs = `CATALOGO`
- [x] T046 [P] Período vacío: informes de **flujo** `data: []`; MRR de stock no finge 0 si hay vigentes — `backend/apps/informes_estrategicos/tests/api/test_oe1_periodo_vacio.py`
- [x] T047 [P] Todo porcentaje con denominador en `backend/apps/informes_estrategicos/tests/api/test_oe1_denominadores.py`
- [x] T048 Cobertura ≥80 % de `backend/apps/informes_estrategicos/services/oe1_service.py` y `backend/apps/informes_estrategicos/views/oe1_views.py`
- [x] T049 Recorrer [`quickstart.md`](quickstart.md) §2 y anotar cifras ClickHouse
- [x] T050 Escribir `specs/001-estrategico/OE1-posicionamiento-captacion/backend/traceability.md`: FR-OE1-* → tarea → prueba
- [x] T051 Actualizar `specs/001-estrategico/contrato-informes-estrategicos.md` §10: OE1 tasks ✅, código al cerrar implement
- [x] T052 Actualizar `specs/001-estrategico/OE1-posicionamiento-captacion/OE1-posicionamiento-captacion.md` capa backend
- [x] T053 Reconstruir `docker compose -f docker/accidentes.yml up -d --build django` y `docker ps --filter name=accidentes-django` **Up** (frontend no cambia en este backend)

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (1) → Foundational (2) **bloquea historias**
- US4 (4) puede ir **justo después de T013** (barata)
- US1 (3) = MVP
- US2 (5) y US3 (6) independientes entre sí
- Polish (7) al cerrar

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US4 (P4)**: ninguna; 404 + YAML
- **US2 (P2)**: Foundational
- **US3 (P3)**: Foundational; dueño OE5

### Parallel Opportunities

- Fase 1: T004, T005
- Fase 2: T011–T013 tras T010
- Fase 3: T014–T017; T019–T023
- Fase 5: T028–T029; T031–T033
- Fase 6: T035–T038; T040–T043
- Fase 7: T045–T047

---

## Parallel Example: Phase 3

```text
Task: "e1_01_mrr_mensual.sql — precio_mensualizado al cierre"
Task: "e1_03_mrr_por_segmento.sql — tipo, no país"
Task: "e1_12_cartera_por_plan.sql — evolución"
```

---

## Implementation Strategy

### MVP (US1 + US4)

1. Setup + Foundational
2. US4 (tres 404)
3. US1
4. **PARAR**: quickstart 2.1–2.3 y 2.8–2.10

### Incremental

1. Cáscara + permisos + 404
2. US1 → **MVP financiero**
3. US2 → captación
4. US3 → ciclo (OE5 podrá colgarse)
5. Polish + rebuild Django

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea CREATE/ALTER**
- No copiar SQL táctica parametrizando endpoints publicados
- Si al implementar se descubre que `precio_mensualizado` falta en alguna fila, se declara en `falta`, no se divide `precio` a ciegas
- No commit salvo que lo pidan
