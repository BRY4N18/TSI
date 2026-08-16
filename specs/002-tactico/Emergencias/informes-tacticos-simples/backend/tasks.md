# Tasks: Informes Tácticos Simples de Emergencias (Backend)

**Input**: Design documents from `specs/002-tactico/Emergencias/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D1, D2, D3, D4 y D6 exigen pruebas concretas sin las cuales cinco defectos silenciosos pasarían
inadvertidos.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3, US4 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Dependencias externas bloqueantes

**Fases 1–2 del piloto**, **fase 2 de Ventas y CRM**, **fase 2 de Suscripciones** y **fase 2 de
Red Operativa** → `core/informes/` con el acotamiento parametrizado.

**Este módulo amplía la capa transversal con un eje nuevo**, el cuarto: cobertura geográfica
contratada. Es la segunda vez desde Red Operativa que se toca `acotamiento.py`, y por una razón
legítima: ninguno de los tres ejes anteriores acota por zona.

**Y no toca el módulo vecino.** Los 19 informes agregados viven en el mismo departamento
(`apps/informes_tacticos`) y **no se modifican**.

---

## Phase 1: Setup

**Purpose**: comprobar dependencias y **sembrar los datos sin los cuales seis pruebas centrales no
prueban nada**.

- [X] T001 Verificar que `core/informes/` está completo y que `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/red_operativa apps/soporte_cliente apps/partners -q` está verde antes de tocar nada
- [X] T002 **Garantizar casos en al menos dos condados distintos** en `backend/scripts/`, uno dentro y otro fuera de la zona contratada del cliente de demo — **sin eso, el acotamiento por zona pasa sin demostrar nada**
- [X] T003 [P] Garantizar en `backend/scripts/` un caso **cerrado**, uno **descartado por falsa alarma**, uno **fusionado** como duplicado y uno **abierto en la zona del cliente**, requisitos de research D2 y de FR-010
- [X] T004 [P] Garantizar en `backend/scripts/` un despacho **en tránsito** —sin llegada ni retiro— y otro con **retiro forzado**, requisitos de research D5
- [X] T005 [P] Garantizar en `backend/scripts/` **evidencia capturada sin conexión y sincronizada** más **evidencia registrada en línea**, tanto fotografía como nota, y además **evidencia sin sincronizar** — requisitos de research D3 y de la User Story 3
- [X] T006 [P] Garantizar en `backend/scripts/` un cierre **sin calificación** y otro **sin observaciones**, requisitos de research D6
- [X] T007 [P] Garantizar un **cliente sin zonas contratadas** en `backend/scripts/`, requisito de FR-011 y SC-002

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: el cuarto eje de acotamiento.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T008 Ampliar `backend/core/informes/acotamiento.py` con el eje **«cobertura contratada»**: resuelve las zonas de un cliente a un **conjunto de ubicaciones** consultable, deja ver todo al rol interno, y **devuelve conjunto vacío —no acceso total— cuando el cliente no tiene zonas** (research D1, FR-011). **El valor por defecto de los tres ejes anteriores no cambia**
- [X] T009 Implementar la resolución de zonas a conjunto de calles en el mismo módulo, **reutilizando el repositorio de catálogo geográfico** que ya resuelve un nivel a un conjunto — **prohibido resolver la ubicación fila a fila** (research D1)
- [X] T010 [P] ⚠️ **Prueba de que un cliente sin zonas obtiene conjunto vacío** en `backend/apps/accidentes/tests/unit/test_acotamiento_zonas.py`, **no acceso total**. De las dos lecturas posibles de «sin zonas», la contraria daría todo a quien no contrató nada (FR-011, SC-002)
- [X] T011 [P] Prueba de que la resolución de zonas produce **un conjunto por petición**, no una consulta por fila, en `backend/apps/accidentes/tests/services/test_acotamiento_resolucion_lotes.py` (research D1)
- [X] T012 Añadir las clases de permiso en `backend/apps/accidentes/permissions.py` y `backend/apps/seguimiento/permissions.py`: casos para roles internos y Cliente; despachos, evidencia y cierres **solo roles internos**; Partner de integración con negativa en los cinco (FR-009 a FR-013)
- [X] T013 [P] Pruebas de permisos en `backend/apps/accidentes/tests/unit/test_informes_permissions.py` y `backend/apps/seguimiento/tests/unit/test_informes_permissions.py`
- [X] T014 Ejecutar `cd backend && python -m pytest core/informes apps/red_operativa apps/suscripciones apps/soporte_cliente apps/partners apps/informes_tacticos -q` y verificar que la ampliación **fue aditiva** — en particular que **los 19 informes agregados no se movieron**

**Checkpoint**: base lista — las cuatro user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Consultar los casos con el alcance que corresponde (Priority: P1) 🎯 MVP

**Goal**: el listado de casos con acotamiento por zona contratada, los tres hechos en vez de un
estado inferido, y sin coordenadas.

**Independent Test**: consultar el listado con cada filtro, con un rol interno y con un cliente, sin
que existan los otros cuatro listados.

**Criterio medible (ISO 25010 — Security / Confidentiality)**: un cliente obtiene el 100 % de los
casos cerrados de sus zonas y **cero** de zonas ajenas, y **cero** casos aún abiertos (T019, T020).

### Implementación

- [X] T015 [US1] Implementar la consulta de casos en `backend/core/repositories/accidentes/informes_casos_repository.py` con **columnas enumeradas** —**sin latitud ni longitud** (research D4)— filtros por severidad, ubicación, tipo de reporte y rango de fecha, y cursor compuesto `fechahoraaccidente|idaccidente`
- [X] T016 [US1] Implementar el filtro `situacion` en el mismo repositorio combinando **los tres hechos del caso**: activo, hora de fin y caso origen. **Prohibido leer el histórico de estados** (research D2)
- [X] T017 [US1] Implementar `InformesCasosService` en `backend/apps/accidentes/services/informes_casos_service.py`, aplicando el acotamiento por zona, resolviendo la ubicación y la severidad contra sus catálogos, y **devolviendo los tres hechos por separado — sin un campo «estado» calculado** (research D2, FR-008)
- [X] T018 [US1] Implementar la vista en `backend/apps/accidentes/views/informes_views.py` como listado de **hechos del período**, forzando para el rol Cliente el filtro de **solo casos cerrados** (FR-010), y registrar `/informes/emergencias/casos` en `backend/apps/accidentes/urls.py`

### Pruebas

- [X] T019 [US1] ⚠️ **Prueba de acotamiento por zona con casos en dos condados** en `backend/apps/accidentes/tests/api/test_informes_casos_zonas.py`: el cliente obtiene solo los de su condado contratado, el rol interno todos, y el conteo del cliente es estrictamente menor (SC-001)
- [X] T020 [P] [US1] **Prueba de que el cliente no ve casos abiertos** en `backend/apps/accidentes/tests/api/test_informes_casos_solo_cerrados.py`: con un caso abierto en su propia zona, no aparece (SC-003, FR-010)
- [X] T021 [P] [US1] ⚠️ **Prueba de que cerrado, descartado y fusionado se distinguen** en `backend/apps/accidentes/tests/repositories/test_informes_casos_situacion.py`: los tres filtros devuelven conjuntos **disjuntos**, el fusionado indica de qué caso es duplicado, y **la respuesta no contiene ningún campo «estado»** (SC-004, research D2)
- [X] T022 [P] [US1] ⛔ **Prueba de que no salen coordenadas ni identidad** en `backend/apps/accidentes/tests/api/test_informes_casos_sin_datos_sensibles.py`: inspecciona la respuesta serializada completa y verifica contra el código que el repositorio enumera columnas (SC-005, research D4)
- [X] T023 [P] [US1] Prueba de que un caso **sin ubicación resoluble aparece** con la ubicación ausente y **no se omite**, en `backend/apps/accidentes/tests/services/test_informes_casos_sin_ubicacion.py` (FR-026)
- [X] T024 [P] [US1] Prueba de contrato en `backend/apps/accidentes/tests/api/test_informes_casos_contract.py`: envelope conforme al OpenAPI con `acotado_a`, `data: []` con 200 sin filas, `400` con situación inválida
- [X] T025 [P] [US1] Prueba de rendimiento del acotamiento en `backend/apps/accidentes/tests/performance/test_informes_casos_zonas_latencia.py`: primera página **con varias zonas contratadas** por debajo de 2 s (SC-007)

**Checkpoint**: US1 entregable por sí sola. Es el MVP y valida el cuarto eje de acotamiento.

---

## Phase 4: User Story 2 — Seguir los despachos y las misiones en curso (Priority: P2)

**Goal**: el listado de despachos con su origen, sus horas y la distinción entre retiro forzado y
normal.

**Independent Test**: consultar el listado de forma aislada, con y sin rango, sin que existan los
otros cuatro.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de las misiones en tránsito se
identifica a partir de las horas del propio despacho, sin consultar ningún histórico (T028).

### Implementación

- [X] T026 [US2] Implementar la consulta de despachos en `backend/core/repositories/seguimiento/informes_despachos_repository.py` con columnas enumeradas, rango de fechas **opcional**, filtros por origen, unidad y caso, y cursor compuesto `fechahoradespacho|iddespacho`
- [X] T027 [US2] Implementar el filtro `en_transito` en el mismo repositorio **derivándolo de las horas del despacho** —despachado, sin llegada, sin retiro—. **Prohibido consultar el histórico de estados del despacho** (research D5)
- [X] T028 [US2] Implementar `InformesDespachosService` en `backend/apps/seguimiento/services/informes_despachos_service.py`, resolviendo unidad y origen contra sus catálogos y **distinguiendo el retiro forzado del normal**
- [X] T029 [US2] Implementar la vista en `backend/apps/seguimiento/views/informes_views.py` como listado de **hechos del período** restringido a roles internos, y registrar `/informes/emergencias/despachos` en `backend/apps/seguimiento/urls.py`

### Pruebas

- [X] T030 [P] [US2] Prueba de que **`en_transito` se deriva de las horas** en `backend/apps/seguimiento/tests/repositories/test_informes_despachos_transito.py`: el despacho sin llegada ni retiro aparece; el que ya llegó, no. Verificar contra el código que no se consulta ningún histórico (research D5)
- [X] T031 [P] [US2] Prueba de que el **retiro forzado se distingue** del normal en `backend/apps/seguimiento/tests/services/test_informes_despachos_retiro.py`
- [X] T032 [P] [US2] Prueba de que **varios despachos sobre un mismo caso aparecen todos**, cada uno con sus horas, en `backend/apps/seguimiento/tests/repositories/test_informes_despachos_multiples.py`
- [X] T033 [P] [US2] Prueba de rango opcional y de contrato en `backend/apps/seguimiento/tests/api/test_informes_despachos_contract.py`: sin rango devuelve el histórico completo; envelope conforme al OpenAPI; `403` para Cliente y Partner

**Checkpoint**: US2 entregable de forma independiente.

---

## Phase 5: User Story 3 — Revisar la evidencia levantada en campo (Priority: P3)

**Goal**: los dos listados de evidencia, con la hora de captura correcta y la evidencia que nunca
llegó.

**Independent Test**: consultar los dos listados de forma aislada, sin que existan los otros tres.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de la evidencia capturada sin
conexión conserva su hora de captura distinta de su hora de registro, **en fotografías y en notas**
(T037).

### Implementación

- [X] T034 [US3] Implementar la consulta de **fotografías** en `backend/core/repositories/accidentes/informes_evidencia_repository.py` con columnas enumeradas, rango opcional, filtros por sincronización, caso y autor, y cursor compuesto — tomando la hora de registro de **la columna de sincronización propia** de esa tabla
- [X] T035 [US3] Implementar la consulta de **notas de campo** en el mismo repositorio, tomando la hora de registro de **la marca genérica de última modificación**, porque la nota **no tiene columna de sincronización propia** (research D3)
- [X] T036 [US3] Implementar `InformesEvidenciaService` en `backend/apps/accidentes/services/informes_evidencia_service.py`, devolviendo **hora de captura y hora de registro por separado** en ambos listados, y resolviendo el autor contra su catálogo
- [X] T037 [US3] Implementar las dos vistas en `backend/apps/accidentes/views/informes_views.py` como listados de **hechos del período** restringidos a roles internos, y registrar sus rutas en `backend/apps/accidentes/urls.py`

### Pruebas

- [X] T038 [P] [US3] ⚠️ **Prueba de la hora de captura en las notas** en `backend/apps/accidentes/tests/repositories/test_informes_notas_hora_captura.py`: la nota capturada sin conexión devuelve **dos horas distintas**; la registrada en línea, dos iguales. **Es la prueba más importante de esta historia**: tomar la columna equivocada sería invisible en las notas en línea y solo fallaría en las offline (research D3)
- [X] T039 [P] [US3] Prueba equivalente para las **fotografías** en `backend/apps/accidentes/tests/repositories/test_informes_fotos_hora_captura.py`
- [X] T040 [P] [US3] Prueba de que **la evidencia sin sincronizar es listable** en `backend/apps/accidentes/tests/api/test_informes_evidencia_sin_sincronizar.py`, en ambos listados — es el hueco que la revisión del sistema dejó anotado
- [X] T041 [P] [US3] Prueba de que la evidencia de **dos unidades sobre el mismo caso** se atribuye a cada autor sin mezclarse, en `backend/apps/accidentes/tests/services/test_informes_evidencia_autoria.py`
- [X] T042 [P] [US3] Pruebas de contrato en `backend/apps/accidentes/tests/api/test_informes_evidencia_contract.py`: envelope conforme al OpenAPI para ambos listados; `403` para Cliente y Partner

**Checkpoint**: US3 entregable de forma independiente.

---

## Phase 6: User Story 4 — Consultar cómo se cerraron los casos (Priority: P4)

**Goal**: el listado de cierres con resultado, calificación y observaciones.

**Independent Test**: consultar el listado de forma aislada, sin que existan los otros cuatro.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de los cierres sin calificar
devuelve la calificación **ausente**, y **ninguno** la devuelve como cero (T044).

### Implementación

- [X] T043 [US4] Implementar la consulta de cierres en `backend/core/repositories/seguimiento/informes_cierres_repository.py` con columnas enumeradas, filtros por resultado, ausencia de observaciones y presencia de calificación, y cursor escalar
- [X] T044 [US4] Implementar `InformesCierresService` en `backend/apps/seguimiento/services/informes_cierres_service.py`, devolviendo la **calificación ausente como ausente, nunca como cero** (research D6, FR-025)
- [X] T045 [US4] Implementar la vista en `backend/apps/seguimiento/views/informes_views.py` como listado de **estado actual** —el registro de cierre no tiene fecha propia— restringido a roles internos, y registrar su ruta en `backend/apps/seguimiento/urls.py`

### Pruebas

- [X] T046 [P] [US4] ⚠️ **Prueba de que una calificación ausente no es un cero** en `backend/apps/seguimiento/tests/services/test_informes_cierres_calificacion.py`: el cierre sin calificar devuelve el campo **ausente**. Un cero aquí hundiría cualquier promedio posterior sin que nadie lo note (research D6)
- [X] T047 [P] [US4] Prueba de que un cierre **sin observaciones** las devuelve ausentes, no como cadena vacía, en `backend/apps/seguimiento/tests/services/test_informes_cierres_observaciones.py`
- [X] T048 [P] [US4] Prueba de que el listado **rechaza un rango de fechas** con `400`, en `backend/apps/seguimiento/tests/api/test_informes_cierres_sin_rango.py` — el registro de cierre no tiene fecha propia (FR-020)
- [X] T049 [P] [US4] Prueba de contrato en `backend/apps/seguimiento/tests/api/test_informes_cierres_contract.py`: envelope conforme al OpenAPI; `403` para Cliente y Partner

**Checkpoint**: los cinco listados completos.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T050 [P] Prueba de **integridad de la paginación** en `backend/apps/accidentes/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez, incluido el cursor de casos que desempata por texto (SC-008)
- [X] T051 [P] Prueba de que `limit` sobre el máximo responde `400` y no se recorta en silencio, en `backend/apps/accidentes/tests/api/test_informes_limite.py` (FR-023)
- [X] T052 [P] Prueba de rendimiento de los cinco listados en `backend/apps/seguimiento/tests/performance/test_informes_latencia.py`: primera página por debajo de 2 s (SC-007)
- [X] T053 Ejecutar `cd backend && python -m pytest -q` completo y verificar que **ninguna suite existente se movió**, en particular la de `apps/informes_tacticos`, que vive en el mismo departamento y **no se toca**
- [X] T054 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint
- [X] T055 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.2 (zonas), §3.3 (tres hechos), §3.6 (hora de captura en notas) y §3.9 (sin coordenadas)
- [X] T056 Anotar en `decisiones-pendientes.md` dos asimetrías del modelo: que **la nota de campo carece de marca de sincronización propia** —y depende de una columna genérica que cualquier actualización pisaría— y que **el registro de cierre no tiene fecha propia**, lo que impide filtrarlo por período sin cruzar con el caso
- [X] T057 Anotar en `decisiones-pendientes.md` que `historial_emergencias_service.py` contiene **las dos formas de acotar** —conjunto resuelto y comprobación fila a fila— a diez líneas de distancia, y conviene unificarlas
- [X] T058 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los listados como 🟢, y **añadir al contrato común** `specs/002-tactico/contrato-informes-simples.md` la regla de que **un listado devuelve hechos, no estados inferidos** cuando la garantía de exclusividad vive en otro módulo

---

## Dependencies

```text
Piloto + Ventas y CRM + Suscripciones + Red Operativa   ← BLOQUEANTES EXTERNOS
    ↓
Phase 1 (Setup + siembra de datos)
    ↓
Phase 2 (Foundational: cuarto eje de acotamiento) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    ├─→ Phase 4 (US2, P2) ─┤ independientes
    ├─→ Phase 5 (US3, P3) ─┤ entre sí
    └─→ Phase 6 (US4, P4) ─┘
                            ↓
                    Phase 7 (Polish)
```

**Dentro de la fase 1**: T003–T007 son paralelos; T002 conviene primero por condicionar más pruebas.

**Dentro de la fase 2**: T008 y T009 son secuenciales; T010 y T011 dependen de ambos. T012 y T013 son
independientes. **T014 cierra la fase.**

**Entre user stories**: ninguna depende de otra. **Se reparten entre dos apps**: US1 y US3 en
`accidentes`, US2 y US4 en `seguimiento`. Dentro de cada app comparten el módulo de vistas y el de
rutas, tocados en puntos distintos sin solapamiento. US3 usa un solo repositorio para sus dos
listados, así que T034 y T035 son secuenciales entre sí.

---

## Parallel Execution Examples

**Fase 1 — la siembra de datos:**

```text
T003 casos cerrado + descartado + fusionado + abierto en zona
T004 despacho en tránsito + retiro forzado
T005 evidencia offline y en línea, foto y nota, más sin sincronizar
T006 cierre sin calificación + cierre sin observaciones
T007 cliente sin zonas contratadas
```

**Fase 3 — pruebas de US1 tras la implementación** (T019 primero, por ser la más costosa de sembrar):

```text
T020 test_informes_casos_solo_cerrados.py
T021 test_informes_casos_situacion.py
T022 test_informes_casos_sin_datos_sensibles.py
T023 test_informes_casos_sin_ubicacion.py
T024 test_informes_casos_contract.py
T025 test_informes_casos_zonas_latencia.py
```

**Fase 7 — la batería de cierre:**

```text
T050 test_informes_paginacion_integridad.py
T051 test_informes_limite.py
T052 test_informes_latencia.py
```

---

## Implementation Strategy

### MVP — solo User Story 1

Las fases 1, 2 y 3 entregan **el listado de casos con el cuarto eje de acotamiento funcionando**, y
con él la pieza que cualquier futuro listado por zona reutilizará. Es el corte natural: valida el eje
nuevo antes de que nada se construya encima.

### Entrega incremental

1. **Fases 1–2** — eje «cobertura contratada» listo y verificado como aditivo (T014).
2. **Fase 3 (US1)** — MVP. Casos con zona, tres hechos y sin coordenadas.
3. **Fase 4 (US2)** — despachos.
4. **Fase 5 (US3)** — evidencia. **Contiene la prueba más sutil del módulo** (T038).
5. **Fase 6 (US4)** — cierres.
6. **Fase 7** — cierre, dos asimetrías anotadas y una regla nueva al contrato común.

### Cinco riesgos a vigilar

**T010 protege contra la peor lectura posible de un dato vacío.** Un cliente sin zonas contratadas
debe obtener **nada**. La interpretación contraria —«sin zonas» como «todas las zonas»— daría acceso
completo al histórico de siniestralidad a quien no contrató ninguna cobertura.

**T038 es la prueba más sutil de toda la serie.** La nota de campo no tiene marca de sincronización
propia, así que su hora de registro sale de otra columna. Tomar la equivocada **sería invisible en
las notas registradas en línea** —donde ambas horas coinciden— y solo fallaría en las capturadas sin
conexión, que son justamente el caso que la regla protege.

**T021 verifica una ausencia.** La respuesta **no debe contener** un campo «estado». Devolverlo
calculado funcionaría hoy, pero ataría este listado a una garantía que vive en el módulo de fusión.

**T002 hace real la prueba del acotamiento.** Sin casos en dos condados, T019 pasa sin demostrar
nada.

**T014 y T053 vigilan al módulo vecino.** Los 19 informes agregados están en el mismo departamento y
**no deben moverse**. Es la primera vez que un módulo de listados convive tan cerca de uno agregado.


---

## Desviaciones respecto a lo planificado *(2026-08-15)*

Las 58 tareas están hechas, pero cuatro se hicieron de otra forma y una queda a medias. Se declara
aquí para que nadie lea el `[X]` como algo que no es.

**T002–T007 — la siembra vive en las pruebas, no en `backend/scripts/`.** Los casos en dos condados,
las tres formas de quedar inactivo, el caso sin ubicación, el despacho en tránsito y el de retiro
forzado, la evidencia sin conexión frente a la de en línea, los cierres sin calificación y sin
observaciones, y el cliente sin zonas están en `apps/accidentes/tests/informes_fixtures.py`. **El
guion de demo sigue sin esos casos**: quien levante el stack para recorrer el `quickstart.md` tendrá
que sembrarlos a mano.

**Los ficheros de prueba están agrupados, no uno por tarea.** `tasks.md` nombraba un fichero por
comprobación; están en nueve, por listado y no por aserción.

**T025 y T034 miden contra el Pinot falso.** El umbral de 2 s se cumple con holgura, pero ahí no hay
red: lo que las pruebas vigilan de verdad es que el **número de consultas** no crezca ni con el
tamaño de la página ni con el número de zonas contratadas, que sí se traslada al stack real.

**T012 concentró los permisos en `apps/accidentes/permissions.py`.** La tarea pedía tocar también
`apps/seguimiento/permissions.py`; la vista de despachos **importa** las clases de accidentes en vez
de duplicarlas. Los cinco listados comparten un mismo mapa de roles, y duplicarlo crearía dos fuentes
de verdad que divergirían al primer rol nuevo.

**T037 no se recorrió contra el stack levantado.** El `quickstart.md` está escrito y su contenido
está cubierto por las pruebas automáticas, pero **nadie lo ha ejecutado con Docker arriba**.

## Cambios que la implementación obligó a hacer en los documentos

**`borrador` se retiró del filtro `situacion`.** No es derivable de lo que el caso registra:
`BORRADOR` es un estado formal que vive en el histórico, y un caso en borrador es indistinguible de
cualquier otro caso activo. FR-002 lo pedía y FR-008 prohíbe leer el histórico; se resolvió a favor
de FR-008. Corregidos `spec.md`, `data-model.md`, el contrato OpenAPI y el catálogo, donde la fila
queda marcada ⛔ con el motivo.

**`cerrado` exige además que el caso no apunte a otro.** Sin esa condición, un duplicado con hora de
fin salía en los dos filtros y `cerrado` y `duplicado` dejaban de ser disjuntos.

**El cursor de casos y cierres lleva componente de texto.** `idaccidente` es el número de caso, no un
entero; con el convertidor por defecto la segunda página daba `400`.

## Lo que este módulo dejó en el contrato común

**§5.6 — el acotamiento por cobertura no es acotamiento por titularidad.** El cuarto eje resuelve un
conjunto en vez de un identificador, filtra con `IN` en vez de `=`, y **no tener nada significa cero
resultados**. Con sus dos reglas: conjunto vacío no es «no filtrar», y el conjunto se resuelve una
vez antes de consultar.

**§5.7 — una exención de autoridad no levanta una exclusión constitucional.** La autoridad
departamental está exenta del acotamiento, no de las exclusiones de dato sensible. Cada listado con
dato excluido lleva una prueba **con la autoridad**, no solo con el rol acotado.
