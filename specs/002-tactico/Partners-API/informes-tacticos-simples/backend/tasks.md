# Tasks: Informes Tácticos Simples de Partners y API (Backend)

**Input**: Design documents from `specs/002-tactico/Partners-API/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D2, D3, D5 y D6 exigen pruebas concretas sin las cuales una fuga de secreto y tres defectos
silenciosos pasarían inadvertidos.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Dependencias externas bloqueantes

**Fases 1–2 del piloto**, **fase 2 de Ventas y CRM**, **fase 2 de Suscripciones** y **fase 2 de
Red Operativa** → `core/informes/` completo con el acotamiento parametrizado.

**Este módulo NO modifica nada compartido.** Es el segundo consecutivo que solo consume la capa
transversal, y además **reutiliza sin tocar** el mecanismo de propiedad y el servicio de consulta ya
existentes en `apps/partners`. Si en algún momento hace falta modificarlos, conviene entender por qué
antes de hacerlo.

---

## Phase 1: Setup

**Purpose**: comprobar dependencias y **sembrar los datos sin los cuales cinco pruebas centrales no
prueban nada**.

- [X] T001 Verificar que `core/informes/` está completo y que `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/red_operativa apps/soporte_cliente -q` está verde antes de tocar nada
- [X] T002 **Garantizar dos partners con credenciales simultáneas** en `backend/scripts/` — **con uno solo, filtrar y no filtrar dan el mismo resultado y el acotamiento pasa sin existir**. La revisión anterior dejó *Integradora Andina* además del partner de demo
- [X] T003 [P] Garantizar un partner con credencial de **pruebas y de producción a la vez** en `backend/scripts/`, requisito de la User Story 1 escenario 5
- [X] T004 [P] Garantizar sobre un mismo partner una credencial **revocada por el partner** y otra **desactivada en cascada** por suspensión, en `backend/scripts/` — requisito de la prueba de research D2. La revisión anterior dejó ese caso en *Integradora Andina*
- [X] T005 [P] Garantizar un partner **suspendido**, una **versión de contrato retirada** y un cliente **sin preferencias configuradas** en `backend/scripts/`, requisitos de FR-012, FR-004 y FR-023

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: los permisos del módulo. **No hay trabajo transversal.**

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T006 Añadir las clases de permiso de informes en `backend/apps/partners/permissions.py`, **reutilizando `verificar_propiedad` sin modificarla**: los listados de partners, credenciales y cambios de acceso admiten gestores y partner; los de versiones de contrato y alcance de datos, **solo gestores** (FR-009 a FR-013)
- [X] T007 [P] Pruebas de permisos en `backend/apps/partners/tests/unit/test_informes_permissions.py`: gestor sin acotar, partner acotado, partner pidiendo ajeno con negativa, partner sobre listados de gestor con negativa, y rol ajeno con negativa
- [X] T008 [P] Prueba de que un **partner suspendido conserva** el acceso a sus propios listados, en `backend/apps/partners/tests/unit/test_informes_partner_suspendido.py` (FR-012, SC-005)
- [X] T009 Ejecutar `cd backend && python -m pytest core/informes apps/soporte_cliente apps/red_operativa -q` y verificar que **nada se movió** — este módulo no debe haber tocado la capa compartida

**Checkpoint**: base lista — las tres user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Ver el estado de los partners y de sus credenciales (Priority: P1) 🎯 MVP

**Goal**: los dos listados de OT08 con acotamiento, la protección del secreto y **la distinción entre
estar inactiva y saber por qué**.

**Independent Test**: consultar ambos listados de forma aislada, con dos roles distintos, sin que
existan los otros tres.

**Criterio medible (ISO 25010 — Security / Confidentiality)**: en el 100 % de las respuestas de los
cinco listados, la respuesta serializada completa está libre del secreto de autenticación (T016).

### Implementación

- [X] T010 [US1] Implementar la consulta de partners en `backend/core/repositories/partners/informes_acceso_repository.py` con **columnas enumeradas**, filtros por estado, plan y cuenta, cursor escalar y acotamiento por `idcliente`
- [X] T011 [US1] Implementar la consulta de credenciales en el mismo repositorio con **lista blanca de columnas** —se enumera lo que sale, **no se leen todas y se descartan las prohibidas**: una lista negra falla abierta ante una columna sensible añadida mañana (research D3)— filtros por entorno, vigencia y caducidad, y cursor compuesto
- [X] T012 [US1] **No incluir ningún campo de motivo de inactividad** en la consulta de credenciales. El registro de la credencial **no contiene** ese dato: revocación, cascada y expiración son indistinguibles en él, y afirmar un motivo sería inventarlo (research D2, FR-006)
- [X] T013 [US1] Implementar `InformesAccesoService` en `backend/apps/partners/services/informes_acceso_service.py` con **reloj inyectable** para `dias_para_caducar`, traducción de `caduca_en_dias` a fecha de corte que viaja al filtro, y resolución de cuenta y partner contra sus catálogos
- [X] T014 [US1] Validar el filtro `estado` **importando las constantes del dominio**, no copiándolas: un estado nuevo no debe producir un `400` engañoso desde el módulo de informes (research D5, FR-020)
- [X] T015 [US1] Implementar las dos vistas en `backend/apps/partners/views/informes_views.py` como listados de **estado actual**, y registrar sus rutas en `backend/apps/partners/urls.py`

### Pruebas

- [X] T016 [P] [US1] ⛔ **Prueba de que el secreto de autenticación no sale** en `backend/apps/partners/tests/api/test_informes_sin_secreto.py`: inspecciona la **respuesta serializada completa** de los cinco listados y falla si aparece; verifica además **contra el código** que los repositorios **enumeran las columnas que devuelven** en lugar de descartar las prohibidas (SC-003, research D3)
- [X] T017 [P] [US1] ⚠️ **Prueba de que el listado de credenciales no afirma el motivo** en `backend/apps/partners/tests/api/test_informes_credencial_sin_motivo.py`: con una credencial revocada y otra desactivada en cascada, **ambas aparecen con la misma información** —inactivas, sin campo de motivo— y ningún campo de la respuesta sugiere una causa (research D2, FR-006)
- [X] T018 [P] [US1] Prueba de que **pruebas y producción coexisten** en `backend/apps/partners/tests/repositories/test_informes_credencial_entornos.py`: un partner en producción sigue aportando su credencial de pruebas
- [X] T019 [P] [US1] **Prueba de acotamiento con dos partners** en `backend/apps/partners/tests/api/test_informes_acceso_acotamiento.py`: el partner obtiene solo lo suyo, el gestor todo, y el conteo del partner es estrictamente menor (SC-001)
- [X] T020 [P] [US1] Prueba de que pedir los registros de otro partner responde **403 sin devolver filas** en `backend/apps/partners/tests/api/test_informes_acceso_partner_ajeno.py` (SC-002)
- [X] T021 [P] [US1] Prueba de que un **estado del dominio recién añadido es aceptado por el filtro** sin tocar este módulo, en `backend/apps/partners/tests/unit/test_informes_estados_importados.py` (research D5)
- [X] T022 [P] [US1] Prueba de contrato en `backend/apps/partners/tests/api/test_informes_acceso_contract.py`: envelope conforme al OpenAPI con `acotado_a`, `data: []` con 200 sin filas, `400` con estado inválido nombrando los seis reales, `400` con rango de fechas

**Checkpoint**: US1 entregable por sí sola. Es el MVP.

---

## Phase 4: User Story 2 — Auditar los cambios de acceso y sus motivos (Priority: P2)

**Goal**: la bitácora donde **sí** viven los motivos que el listado de credenciales no puede dar.

**Independent Test**: consultar el listado de forma aislada, con y sin rango, sin que existan los
otros.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de las revocaciones decididas por
el partner es distinguible de las desactivaciones por cascada (T026).

### Implementación

- [X] T023 [US2] Implementar la consulta de cambios de acceso en `backend/core/repositories/partners/informes_bitacora_repository.py` con columnas enumeradas, rango de fechas **opcional**, filtros por tipo de cambio y partner, cursor compuesto `fecha_cambio|idhistorial` y acotamiento por partner
- [X] T024 [US2] Implementar `InformesBitacoraService` en `backend/apps/partners/services/informes_bitacora_service.py`, resolviendo partner, credencial y ejecutor contra sus catálogos, y **conservando cada tipo de cambio con su valor propio** — en particular, sin agrupar revocación con desactivación por cascada (research D2, FR-007)
- [X] T025 [US2] Implementar la vista en `backend/apps/partners/views/informes_views.py` como listado de **hechos del período**, validando `tipo_cambio` contra las constantes importadas del dominio, y registrar su ruta en `backend/apps/partners/urls.py`

### Pruebas

- [X] T026 [P] [US2] ⚠️ **Prueba de que revocación y cascada no se confunden** en `backend/apps/partners/tests/repositories/test_informes_bitacora_tipos.py`: sobre el mismo partner, la credencial revocada por seguridad y la desactivada por suspensión aparecen con **tipos de cambio distintos**. Agruparlas pondría en la misma línea una decisión de seguridad y un impago administrativo (SC-004, research D2)
- [X] T027 [P] [US2] Prueba de que una **reactivación sin motivo es correcta** en `backend/apps/partners/tests/services/test_informes_bitacora_motivo.py`: el motivo llega **ausente** y no se marca como dato incompleto; una suspensión, en cambio, siempre lo trae (research D6)
- [X] T028 [P] [US2] Prueba de rango opcional en `backend/apps/partners/tests/api/test_informes_bitacora_rango.py`: sin rango devuelve el histórico completo; con rango lo acota
- [X] T029 [P] [US2] Prueba de acotamiento: un partner ve **solo su propia bitácora**, en `backend/apps/partners/tests/api/test_informes_bitacora_acotamiento.py`
- [X] T030 [P] [US2] Prueba de contrato en `backend/apps/partners/tests/api/test_informes_bitacora_contract.py`: envelope conforme al OpenAPI

**Checkpoint**: US2 entregable de forma independiente. Junto con US1 cierra el par
«estado sin motivo» / «motivos con su tipo».

---

## Phase 5: User Story 3 — Contrato vigente y alcance de datos contratado (Priority: P3)

**Goal**: qué versiones del contrato existen y qué alcance tiene habilitado cada cliente.

**Independent Test**: consultar los dos listados de forma aislada, sin que existan los de las otras
historias.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de los clientes sin alcance
configurado se presenta como alcance ausente, y ninguno como acceso ilimitado (T034).

### Implementación

- [X] T031 [US3] Implementar la consulta de versiones del contrato en `backend/core/repositories/partners/informes_contrato_repository.py`, **incluyendo las retiradas**, con filtros por estado y servicio y cursor compuesto
- [X] T032 [US3] Implementar en el mismo repositorio la consulta de alcance de datos por cliente, con columnas enumeradas y cursor escalar
- [X] T033 [US3] Implementar `InformesContratoService` en `backend/apps/partners/services/informes_contrato_service.py`, resolviendo servicio y cuenta contra sus catálogos y devolviendo el alcance **como ausente** cuando el cliente no tiene preferencias — **nunca como acceso ilimitado** (FR-023)
- [X] T034 [US3] Implementar las dos vistas en `backend/apps/partners/views/informes_views.py` como listados de **estado actual** restringidos a gestores, y registrar sus rutas en `backend/apps/partners/urls.py`

### Pruebas

- [X] T035 [P] [US3] ⚠️ **Prueba de que sin alcance configurado no es acceso ilimitado** en `backend/apps/partners/tests/services/test_informes_alcance_ausente.py`: un cliente sin preferencias devuelve las zonas **ausentes**, nunca una lista vacía presentada como «todas» ni texto que sugiera acceso total (SC-006, FR-023)
- [X] T036 [P] [US3] Prueba de que las **versiones retiradas se incluyen** en `backend/apps/partners/tests/repositories/test_informes_versiones_retiradas.py`, con su fecha de retiro (FR-004)
- [X] T037 [P] [US3] Prueba de que un partner recibe **403** en ambos listados, en `backend/apps/partners/tests/api/test_informes_contrato_permisos.py` (FR-013)
- [X] T038 [P] [US3] Prueba de contrato en `backend/apps/partners/tests/api/test_informes_contrato_contract.py`: envelope conforme al OpenAPI para ambos listados

**Checkpoint**: los cinco listados completos.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T039 [P] Prueba de **integridad de la paginación** en `backend/apps/partners/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez (SC-008)
- [X] T040 [P] Prueba de que `limit` sobre el máximo responde `400` y no se recorta en silencio, en `backend/apps/partners/tests/api/test_informes_limite.py` (FR-021)
- [X] T041 [P] Prueba de rendimiento en `backend/apps/partners/tests/performance/test_informes_latencia.py`: primera página de los cinco listados por debajo de 2 s (SC-007)
- [X] T042 Ejecutar `cd backend && python -m pytest -q` completo y verificar que **ninguna suite existente se movió**, en particular la de la consola de registros, que **no se toca**
- [X] T043 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint
- [X] T044 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.2 (secreto), §3.4 (motivo de inactividad) y §3.8 (alcance ausente)
- [X] T045 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los listados como 🟢, y **añadir al contrato común** `specs/002-tactico/contrato-informes-simples.md` la regla de que los repositorios de listados usan **lista blanca de columnas**, no lista negra de campos prohibidos

---

## Dependencies

```text
Piloto + Ventas y CRM + Suscripciones + Red Operativa   ← BLOQUEANTES EXTERNOS
    ↓
Phase 1 (Setup + siembra de datos)
    ↓
Phase 2 (Foundational: permisos) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    ├─→ Phase 4 (US2, P2) ─┤ independientes entre sí
    └─→ Phase 5 (US3, P3) ─┘
                            ↓
                    Phase 6 (Polish)
```

**Dentro de la fase 1**: T003, T004 y T005 son paralelos; T002 conviene primero.

**Dentro de la fase 2**: T006 primero; T007 y T008 dependen de él. **T009 cierra la fase**: comprueba
que este módulo no tocó la capa compartida.

**Entre user stories**: ninguna depende de otra. Comparten `views/informes_views.py` y `urls.py`
(T015, T025, T034), tocados en tres puntos sin solapamiento. US1 y US3 usan un repositorio cada una
para sus dos listados, así que sus tareas de repositorio son secuenciales entre sí.

---

## Parallel Execution Examples

**Fase 1 — la siembra de datos:**

```text
T003 partner con credencial de pruebas y producción
T004 credencial revocada + credencial desactivada en cascada
T005 partner suspendido + versión retirada + cliente sin preferencias
```

**Fase 3 — todas las pruebas de US1 tras la implementación:**

```text
T016 test_informes_sin_secreto.py
T017 test_informes_credencial_sin_motivo.py
T018 test_informes_credencial_entornos.py
T019 test_informes_acceso_acotamiento.py
T020 test_informes_acceso_partner_ajeno.py
T021 test_informes_estados_importados.py
T022 test_informes_acceso_contract.py
```

**Fase 6 — la batería de cierre:**

```text
T039 test_informes_paginacion_integridad.py
T040 test_informes_limite.py
T041 test_informes_latencia.py
```

---

## Implementation Strategy

### MVP — solo User Story 1

Las fases 1, 2 y 3 entregan **los dos listados de OT08 con el secreto protegido por lista blanca y la
distinción entre estar inactiva y saber por qué**. Es el corte natural.

### Entrega incremental

1. **Fases 1–2** — permisos listos y verificado que la capa compartida no se tocó (T009).
2. **Fase 3 (US1)** — MVP. Partners y credenciales.
3. **Fase 4 (US2)** — bitácora. **Cierra el par con US1**: el estado sin motivo, y los motivos con su
   tipo.
4. **Fase 5 (US3)** — contrato y alcance.
5. **Fase 6** — cierre y una regla nueva al contrato común.

### Cuatro riesgos a vigilar

**T016 no es una prueba de contrato más.** El secreto de autenticación es del mismo orden que el
medio de cobro de Suscripciones. Y lo que verifica va más allá de la respuesta: **que el repositorio
enumere las columnas que devuelve**. Una lista negra pasaría esta prueba hoy y fallaría el día que
alguien añada una columna sensible a la tabla — **falla abierta y en silencio**.

**T017 comprueba una ausencia deliberada.** Es contraintuitivo: la prueba exige que dos credenciales
inactivas por razones opuestas **se vean igual** en este listado. Quien la lea sin contexto podría
pensar que documenta un defecto; documenta que el listado **no inventa** un dato que su fuente no
tiene.

**T026 es su contrapartida**, y las dos se leen juntas: lo que US1 no puede decir, US2 lo dice con su
tipo propio.

**T002 hace reales las pruebas de acotamiento.** Con un solo partner con credenciales, T019 y T020
pasan aunque el acotamiento no exista.

---

## Desviaciones respecto a lo planificado *(2026-08-15)*

Las 45 tareas están hechas, pero tres se hicieron de otra forma y una queda a medias. Se declara aquí
para que nadie lea el `[X]` como algo que no es.

**T002–T005 — la siembra vive en las pruebas, no en `backend/scripts/`.** Los casos (dos partners con
credenciales, pruebas y producción coexistiendo, revocada frente a cascada, partner suspendido,
versión retirada, cliente sin preferencias) están en `apps/partners/tests/conftest.py`, no en el
guion de demo. Es donde las necesitaban las pruebas, y ahí quedan bajo control de versiones y
verificadas en cada ejecución. **El guion de demo sigue sin esos casos**: quien levante el stack para
recorrer el `quickstart.md` tendrá que sembrarlos a mano.

**Los ficheros de prueba están agrupados, no uno por tarea.** `tasks.md` nombraba un fichero por
comprobación; están en seis, por listado y no por aserción: `test_informes_acceso.py` (US1),
`test_informes_bitacora.py` (US2), `test_informes_contrato.py` (US3), más permisos, paginación,
conformidad OpenAPI, latencia y la derivación de estado. El contenido exigido está completo.

**T041 mide contra el Pinot falso.** El umbral de 2 s se cumple con holgura, pero ahí no hay red: lo
que la prueba vigila de verdad es que **el número de consultas no crezca con el tamaño de la
página**, que sí se traslada al stack real. Es la comprobación con valor; el cronómetro sobre el
falso no lo tiene.

**T044 no se recorrió contra el stack levantado.** El `quickstart.md` está escrito y su contenido
está cubierto por las pruebas automáticas, pero **nadie lo ha ejecutado con Docker arriba**. Queda
pendiente de hacer en una sesión con el stack en marcha.
