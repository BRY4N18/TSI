# Tasks: OE5 — Retención y Ciclo de Vida — Backend

**Input**: Design documents from `specs/001-estrategico/OE5-retencion-ciclo-vida/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/informes-estrategicos-oe5.openapi.yaml`](contracts/informes-estrategicos-oe5.openapi.yaml), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Constitución ≥80 % en servicios. Un SLA con tickets sin plazo, un NRR sin descomponer o un NPS de accidente no se ven en un 200.

**Organization**: US1–US4 de [`spec.md`](spec.md). MVP = US1. US4 (404) es barata: adelantarla tras Foundational.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: ficheros distintos, sin dependencias pendientes
- **[US1]–[US4]**: solo fases de historia
- Cada tarea lleva ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Publica 9 de 15. Cero tablas nuevas.** E5-01 y E5-11 no tienen SQL ni path. E5-09/10/13/14 **no existen en OE5**: 404 hacia OE1.

**E5-12 solo Gerente.** Una señal no marca riesgo. OT07 deja expansión/contracción en 0: E5-02 las calcula.

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Tickets sin compromiso en el denominador SLA** | Infla o hunde el 95 % |
| **Copiar OT07 con expansión = 0** | NRR sin descomponer |
| **Usar `dim_plan.precio` en E5-03** | La tarifa nueva reescribe historia |
| **Marcar riesgo con una señal** | Cuatro alarmas ruidosas |
| **SQL de E1-06/09/10/11 aquí** | Dos tasas de renovación |
| **`calificacion` de cierre como NPS** | Mide un accidente, no al cliente |
| **Texto de ticket o medio de cobro** | FR-OE5-003/004 |
| **Permiso de módulo único** | Finanzas vería tickets o Soporte vería NRR |

Slugs HTTP: `cumplimiento-sla`, `evolucion-incumplimiento`, `sla-por-plan`, `retencion-neta-ingresos`, `movimientos-de-plan`, `rendimiento-por-agente`, `reincidencia-soporte`, `cuentas-en-riesgo`, `antiguedad-de-cuenta`. **No** `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding`.

JWT: `GerenteExitoCliente` (no el alias de la spec).

---

## Phase 1: Setup

**Purpose**: armazón y carpeta SQL.

**Independent Test**: el cargador resuelve `estrategicos/oe5`; la ruta Django existe (stub).

- [x] T001 Verificar el armazón `informes_estrategicos`: `backend/apps/informes_estrategicos/periodo_estrategico.py`, `objetivo.py`, `envelope.py`, `permissions.py`, `backend/apps/informes_estrategicos/services/oe1_service.py`. Si falta OE1, no hay a dónde apuntar los 404 de E5-09/10/13/14
- [x] T002 Anotar en [`quickstart.md`](quickstart.md) §1: `EXISTS TABLE hecho_ticket`, `count()` de `hecho_ticket FINAL`, `hecho_suscripcion FINAL`, `hecho_sesion`, `hecho_llamada_api` (origen 2026-08-16: 14 / 4 / 747 / 18)
- [x] T003 Crear `dags/lib/consultas/estrategicos/oe5/README.md` con convención `e5_NN_<informe>.sql`, `FINAL` en dims y `hecho_ticket` / `hecho_suscripcion`, **nunca** `FINAL` en `hecho_factura` / `hecho_solicitud_cambio_plan` / `hecho_accion_ticket` / `hecho_sesion` / `hecho_llamada_api`, y **ningún** `e5_01_*.sql` / `e5_09_*.sql` / `e5_10_*.sql` / `e5_11_*.sql` / `e5_13_*.sql` / `e5_14_*.sql`
- [x] T004 [P] Añadir en `dags/tests/test_catalogo_estrategicos_oe5.py` que el cargador resuelve `departamento="estrategicos/oe5"`
- [x] T005 [P] Registrar `informes-estrategicos/oe5/<str:informe>` en `backend/apps/informes_estrategicos/urls.py` apuntando a `Oe5View` (import en stub hasta T010)

---

## Phase 2: Foundational

**Purpose**: autoridad partida, servicio vacío y 404. **Bloquea US1–US4.**

**Independent Test**: Gerente no 403 en un slug publicado; GET `nps-satisfaccion` → 404; GET `tasa-renovacion` bajo `/oe5/` → 404; Financiero 403 en `cumplimiento-sla`.

- [x] T006 Añadir en `backend/core/auth/roles_tacticos.py`: `AUTORIDAD_OE5`, `AUTORIDAD_OE5_SOPORTE` (`GerenteExitoCliente`, `Gerente`), `AUTORIDAD_OE5_FINANZAS` (`DirectorFinanciero`, `Gerente`), `AUTORIDAD_OE5_ESTRATEGIA` (`DirectorEstrategia`, `Gerente`), `AUTORIDAD_OE5_RIESGO` (`Gerente` solo)
- [x] T007 Ampliar `backend/apps/informes_estrategicos/permissions.py` con `Oe5Permission` y mapa: `cumplimiento-sla`/`evolucion-incumplimiento`/`rendimiento-por-agente`/`reincidencia-soporte` → SOPORTE; `sla-por-plan` → SOPORTE ∪ ESTRATEGIA; `retencion-neta-ingresos` → FINANZAS; `movimientos-de-plan` → ESTRATEGIA ∪ FINANZAS; `antiguedad-de-cuenta` → ESTRATEGIA; `cuentas-en-riesgo` → RIESGO; desconocido/bloqueado/referencia OE1 → 404 de vista, no 403
- [x] T008 Implementar `backend/apps/informes_estrategicos/services/oe5_service.py` con `CATALOGO` (9 slugs), `PUBLICADOS`, `BLOQUEADOS={"nps-satisfaccion","reportes-sin-correccion"}`, `REFERENCIAS_OE1={"tasa-renovacion","churn-por-cohorte","tiempo-onboarding","abandono-onboarding"}`, `DEPARTAMENTO="estrategicos/oe5"`. Forzar `cobertura: parcial` + `falta` de muestra mientras n < 20. `cumple` siempre `null`. Slug en `REFERENCIAS_OE1` o `BLOQUEADOS` → `InformeDesconocido` (404)
- [x] T009 Implementar `backend/apps/informes_estrategicos/views/oe5_views.py` al patrón de `oe1_views.py` (`IsAuthenticated401`, `Oe5Permission`, envelope, 400 de período). El 404 de referencias OE1 puede nombrar el path `/informes-estrategicos/oe1/<slug>`
- [x] T010 Completar el import de `Oe5View` en `backend/apps/informes_estrategicos/urls.py`
- [x] T011 [P] Prueba de **exclusión** en `backend/apps/informes_estrategicos/tests/api/test_permisos_oe5.py`: Financiero 403 en `cumplimiento-sla`; `GerenteExitoCliente` 403 en `retencion-neta-ingresos`; Estrategia 403 en `cuentas-en-riesgo`; Gerente no 403 en las nueve; partner 403 en todas
- [x] T012 [P] Prueba en `backend/apps/informes_estrategicos/tests/api/test_oe5_bloqueados.py`: GET `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding` → **404** (también con Gerente)
- [x] T013 [P] En `dags/tests/test_catalogo_estrategicos_oe5.py`: ninguna consulta nombra `asunto`/`descripcion`/`mensaje`/`idmetodopago`/`calificacion`; `SELECT *` prohibido; `ORDER BY` obligatorio; `{desde:Date}` `{hasta:Date}` `{granularidad:String}`; `FINAL` en dims, `hecho_ticket`, `hecho_suscripcion`; **cero** ficheros `e5_01_*` / `e5_09_*` / `e5_10_*` / `e5_11_*` / `e5_13_*` / `e5_14_*`; ninguna SQL crea tabla

**Checkpoint**: ruta viva, permisos partidos, seis 404. SQL de informes puede empezar.

---

## Phase 3: User Story 1 — Compromiso de servicio (Priority: P1) 🎯 MVP

**Goal**: E5-04, E5-05, E5-07.

**Independent Test**: denominador SLA = cerrados con compromiso; sin compromiso aparte; `data: []` si no hubo qué cumplir; cobertura parcial.

- [x] T014 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe5/e5_04_cumplimiento_sla.sql`: `hecho_ticket FINAL`; numerador `desenlace_sla`; denominador `tiene_compromiso = 1`; contar `sin_compromiso`
- [x] T015 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe5/e5_05_evolucion_incumplimiento.sql`: serie por período; mismos filtros de compromiso
- [x] T016 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe5/e5_07_sla_por_plan.sql`: cruzar `idplan` copiado en el hecho, **no** el precio vigente de `dim_plan`
- [x] T017 [US1] Registrar los tres slugs en `CATALOGO` de `backend/apps/informes_estrategicos/services/oe5_service.py`
- [x] T018 [P] [US1] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe5_us1_contract.py` (período obligatorio, envelope, slugs OpenAPI)
- [x] T019 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_sla_sin_compromiso.py`: tickets `tiene_compromiso = 0` no entran en el denominador (falsable)
- [x] T020 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_sla_periodo_vacio.py`: sin cerrados-con-compromiso → `data: []`, no 0 %
- [x] T021 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_sin_prosa.py`: ninguna clave es asunto, mensaje o nota
- [x] T022 [US1] Recorrer [`quickstart.md`](quickstart.md) §2.1 (pruebas equivalentes)

**Checkpoint**: MVP. El tablero de Cliente ve el SLA sin mentir el denominador.

---

## Phase 4: User Story 4 — Bloqueados y referencias OE1 (Priority: P4)

**Goal**: E5-01/11 no existen; E5-09/10/13/14 viven en OE1. Barata; adelantar tras T013.

**Independent Test**: OpenAPI no declara las seis rutas; GET → 404.

- [x] T023 [P] [US4] En `backend/apps/informes_estrategicos/tests/api/test_openapi_conforme_oe5.py`: los nueve `PUBLICADOS` están en `specs/001-estrategico/OE5-retencion-ciclo-vida/backend/contracts/informes-estrategicos-oe5.openapi.yaml`; `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding` **no**
- [x] T024 [US4] Confirmar `test_oe5_bloqueados.py` cubre los dos bloqueados y los cuatro alias OE1
- [x] T025 [P] [US4] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us4_sin_nps_emergencia.py`: ninguna consulta ni clave de respuesta nombra `calificacion` de cierre de accidente
- [x] T026 [US4] Documentar en el índice y en [`quickstart.md`](quickstart.md) §2.8 que el KPI principal del BSC (NPS) queda sin fuente

**Checkpoint**: nadie publica NPS = 0 ni una segunda tasa de renovación.

---

## Phase 5: User Story 2 — Cartera (Priority: P2)

**Goal**: E5-02, E5-03.

**Independent Test**: NRR muestra expansión, contracción y churn; pendientes no cuentan; precio congelado.

- [x] T027 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe5/e5_02_retencion_neta_ingresos.sql`: cohorte al inicio (`precio_mensualizado`); expansión/contracción desde `hecho_solicitud_cambio_plan` aprobada/aplicada; churn de bajas; **no** copiar los ceros de OT07
- [x] T028 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe5/e5_03_movimientos_de_plan.sql`: solo `estado` en `aprobada`/`aplicada`; `delta_precio` del hecho, nunca `dim_plan.precio`
- [x] T029 [US2] Registrar slugs en `backend/apps/informes_estrategicos/services/oe5_service.py`; `alcance` de E5-02 nombra descomposición
- [x] T030 [P] [US2] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe5_us2_contract.py`
- [x] T031 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_nrr_descompuesto.py`: la respuesta tiene expansión, contracción y churn (no solo neto)
- [x] T032 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_pendiente_no_cuenta.py`: catálogo SQL no trata `pendiente` como movimiento de ingreso
- [x] T033 [US2] Quickstart §2.2–2.3 (pruebas)

**Checkpoint**: US2 independiente.

---

## Phase 6: User Story 3 — Señales (Priority: P3)

**Goal**: E5-06, E5-08, E5-12, E5-15.

**Independent Test**: una señal no marca; `falta` nombra fuente ausente; agente sin nombre; reincidencia = cliente × servicio; antigüedad solo activas.

- [x] T034 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe5/e5_06_rendimiento_por_agente.sql`: `idagente` (clave); sin nombre; columnas de carga
- [x] T035 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe5/e5_08_reincidencia_soporte.sql`: agrupar `idcliente` × `servicio`
- [x] T036 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe5/e5_12_cuentas_en_riesgo.sql`: cuatro señales (API, tickets, cobro, sesiones); marcado solo si ≥2; `sin_actividad_conocida` no es 0 días
- [x] T037 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe5/e5_15_antiguedad_de_cuenta.sql`: `dim_cliente FINAL` con `fecha_baja IS NULL`; cerradas aparte
- [x] T038 [US3] Registrar los cuatro slugs; `alcance` de E5-06 = carga de trabajo; de E5-12 = umbral de dos señales; si una fuente no carga, `falta` la nombra en `backend/apps/informes_estrategicos/services/oe5_service.py`
- [x] T039 [P] [US3] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe5_us3_contract.py`
- [x] T040 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_una_senal_no_marca.py`: una sola señal activa → cuenta no listada
- [x] T041 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_agente_sin_nombre.py`: respuesta de E5-06 sin nombre/correo
- [x] T042 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_reincidencia_servicio.py`: grano cliente × servicio en el SQL
- [x] T043 [US3] Quickstart §2.4–2.7 (pruebas)

**Checkpoint**: US3 independiente. E5-12 es informe de dirección, no de departamento.

---

## Phase 7: Polish

- [x] T044 [P] Completar `backend/apps/informes_estrategicos/tests/api/test_openapi_conforme_oe5.py`: YAML sin prosa, cobro, `calificacion`; slugs = `CATALOGO`
- [x] T045 [P] Período vacío de **flujo** `data: []`; stock de antigüedad no finge 0 si hay activas — `backend/apps/informes_estrategicos/tests/api/test_oe5_periodo_vacio.py`
- [x] T046 [P] Todo porcentaje con denominador en `backend/apps/informes_estrategicos/tests/api/test_oe5_denominadores.py` (SLA, NRR, reincidencia)
- [x] T047 Cobertura ≥80 % de `backend/apps/informes_estrategicos/services/oe5_service.py` y `backend/apps/informes_estrategicos/views/oe5_views.py`
- [x] T048 Recorrer [`quickstart.md`](quickstart.md) §2 y anotar cifras ClickHouse
- [x] T049 Escribir `specs/001-estrategico/OE5-retencion-ciclo-vida/backend/traceability.md`: FR-OE5-* → tarea → prueba
- [x] T050 Actualizar `specs/001-estrategico/contrato-informes-estrategicos.md` §10: OE5 tasks ✅, código al cerrar implement
- [x] T051 Actualizar `specs/001-estrategico/OE5-retencion-ciclo-vida/OE5-retencion-ciclo-vida.md` capa backend
- [x] T052 Reconstruir `docker compose -f docker/accidentes.yml up -d --build django` y `docker ps --filter name=accidentes-django` **Up** (frontend no cambia en este backend)

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (1) → Foundational (2) **bloquea historias**
- US4 (4) puede ir **justo después de T013**
- US1 (3) = MVP
- US2 (5) y US3 (6) independientes entre sí (US3 no exige NRR para marcar riesgo)
- Polish (7) al cerrar

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia
- **US4 (P4)**: ninguna; 404 + YAML
- **US2 (P2)**: Foundational
- **US3 (P3)**: Foundational; E5-12 cruza cuatro hechos, no otras historias HTTP

### Parallel Opportunities

- Fase 1: T004, T005
- Fase 2: T011–T013 tras T010
- Fase 3: T014–T016; T018–T021
- Fase 5: T027–T028; T030–T032
- Fase 6: T034–T037; T039–T042
- Fase 7: T044–T046

---

## Parallel Example: Phase 3

```text
Task: "e5_04_cumplimiento_sla.sql — denominador con compromiso"
Task: "e5_05_evolucion_incumplimiento.sql — serie"
Task: "e5_07_sla_por_plan.sql — idplan del hecho"
```

---

## Implementation Strategy

### MVP (US1 + US4)

1. Setup + Foundational
2. US4 (seis 404)
3. US1
4. **PARAR**: quickstart 2.1 y 2.8–2.10

### Incremental

1. Cáscara + permisos + 404
2. US1 → **MVP de Cliente (SLA)**
3. US2 → cartera (NRR de verdad)
4. US3 → señales (E5-12 Gerente-only)
5. Polish + rebuild Django

---

## Notes

- `[P]` = ficheros distintos
- **Ninguna tarea CREATE/ALTER**
- No copiar SQL táctica parametrizando endpoints publicados; OT07 en concreto no se copia
- Si al implementar una señal de E5-12 no tiene filas, se declara en `falta`, no se omite
- No commit salvo que lo pidan
