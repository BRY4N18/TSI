# Tasks: Informes Compuestos de Emergencias sobre el Modelo Analítico

**Input**: Design documents from `specs/002-tactico/Emergencias/informes-compuestos-modelo/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80 % en servicios, y este
módulo produce **cifras para decidir**: una consulta que devuelve un número plausible y equivocado no
falla, no avisa, y solo se detecta comparándola con algo.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**No construye 26 informes: construye 10, migra 3 y vigila 13.** Dieciséis ya tienen endpoint
funcionando contra el sistema operativo; solo se migran los tres que dan cifras equivocadas.

**Y no crea ninguna tabla por informe.** Si a un informe le falta un dato, se amplía el modelo. Es la
regla que este módulo existe para demostrar a escala: si funciona con 26, funciona con los 108 del
catálogo.

---

## Phase 1: Setup — el sustrato y el sitio donde viven las consultas

**Purpose**: comprobar que el modelo está cargado y crear la estructura del catálogo de consultas.

- [ ] T001 Verificar que el modelo analítico está cargado y sus cuatro hechos tienen datos, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q` y comprobando que las tablas de `tsi_tactico` cuadran con el origen
- [ ] T002 Crear el directorio del catálogo `dags/lib/consultas/emergencias/` con un `README.md` que fije las convenciones de `contracts/catalogo-consultas.md` §1
- [ ] T003 [P] Implementar el cargador de consultas en `dags/lib/consultas/__init__.py`: dado un nombre, devuelve el SQL del fichero. **Sin construir SQL en Python** — el fichero es la definición canónica (research D1)
- [ ] T004 [P] Prueba del cargador en `dags/tests/test_catalogo_consultas.py`: un nombre inexistente falla con un error que nombra el fichero buscado, no con un `KeyError` pelado

---

## Phase 2: Foundational — las piezas que comparten los 26 informes

**Purpose**: lo transversal, incluidas las dos reglas que se olvidan y no avisan.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [ ] T005 Implementar `backend/core/repositories/informes_tacticos/modelo_repository.py`: ejecuta una consulta del catálogo contra el almacén con parámetros con tipo. **Solo lectura**; reutiliza `core/clickhouse/client.py` sin añadir dependencias
- [ ] T006 Implementar en el mismo repositorio la traducción de ausencia: un valor ausente del almacén llega a la respuesta como **nulo**, nunca como `0` ni como cadena vacía (FR-017)
- [ ] T007 Implementar la resolución de período en `backend/apps/informes_tacticos/periodo.py` para estos informes, reutilizando lo existente: por defecto **los últimos 30 días**, ambos extremos inclusive
- [ ] T008 Implementar el servicio base en `backend/apps/informes_tacticos/services/emergencias_compuestos_service.py`, que enlaza nombre de informe → consulta del catálogo → respuesta
- [ ] T009 Implementar la vista base en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py`, reutilizando `views/base.py`, `envelope.py` y `permissions.py` ya existentes
- [ ] T010 Aplicar los permisos en `backend/apps/informes_tacticos/permissions.py`, usando las constantes de `backend/core/auth/roles_tacticos.py`: el **Director de Operaciones** accede sin acotamiento por titularidad; el responsable operativo con él; quien no es ninguno de los dos no accede (FR-021, FR-023)
- [ ] T011 ⚠️ **Prueba de la regla de versión final** en `dags/tests/test_regla_final_catalogo.py`, **sobre el texto de las consultas**: toda consulta que toca `hecho_accidente`, `hecho_despacho` o una dimensión **fuerza la versión final**; ninguna que toca `hecho_estado_unidad`, `hecho_ping_unidad` o `hecho_evidencia` lo hace. Omitirla devuelve cifras infladas **solo a veces**, y pedirla de más falla con `ILLEGAL_FINAL`
- [ ] T012 ⚠️ **Prueba de exclusión de dato sensible** en `dags/tests/test_catalogo_sin_datos_sensibles.py`: ninguna consulta del catálogo nombra una columna de coordenadas, identidad de persona o texto libre (FR-015, FR-016)
- [ ] T013 [P] Prueba de que **toda consulta lleva `ORDER BY` explícito** en `dags/tests/test_catalogo_forma.py`: sin él el orden es arbitrario y comparar dos corridas deja de ser posible
- [ ] T014 [P] Prueba de que **ninguna consulta usa `SELECT *`** en el mismo fichero: una columna nueva del hecho aparecería sola en un informe sin que nadie lo decidiera
- [ ] T015 [P] Prueba del repositorio en `backend/apps/informes_tacticos/tests/repositories/test_modelo_repository.py`: ejecuta, parametriza y **no escribe nunca**

**Checkpoint**: el sustrato está listo — las tres user stories pueden abordarse.

---

## Phase 3: User Story 1 — Qué se registró y con qué calidad (Priority: P1) 🎯 MVP

**Goal**: los seis informes de OT21 disponibles sobre el modelo, con la completitud **midiendo de
verdad**.

**Independent Test**: pedir los seis informes de un período y comprobar que la suma de cada
distribución es igual al total de casos, sin que exista ninguna tabla por informe.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: al cargar un caso sin severidad, la
completitud **baja del 100 %** (SC-002). Hoy es matemáticamente incapaz de hacerlo.

### Las consultas

- [ ] T016 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_distribucion_severidad.sql` — devuelve `periodo, severidad, casos, pct`
- [ ] T017 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_distribucion_zona.sql` — devuelve `periodo, condado, casos, pct`
- [ ] T018 [US1] ⚠️ Escribir `dags/lib/consultas/emergencias/ot21_completitud_campos_criticos.sql` — **es el que corrige el defecto**: la condición de completitud se evalúa sobre el modelo, donde la ausencia es ausencia, no sobre centinelas
- [ ] T019 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_descarte_fusion.sql` usando `fue_descartado` y `es_duplicado`, que **sí distinguen** descartado de fusionado y de cerrado
- [ ] T020 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_ranking_ubicaciones.sql` con parámetro `top`, expresando la ubicación **por nombre**
- [ ] T021 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_impacto_humano.sql` — devuelve heridos, víctimas y fallecidos por condado

### El endpoint que se migra

- [ ] T022 [US1] Exponer `GET /api/v1/informes-tacticos/emergencias/completitud-campos-criticos` según `contracts/informes-compuestos-emergencias.openapi.yaml`, en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py` y `urls.py`
- [ ] T023 [US1] **Dejar intacto** `CompletitudCamposCriticosView` en `backend/apps/informes_tacticos/views/registro_views.py` y su ruta en `urls.py`. Se retirará cuando se decida qué pasa con los endpoints del módulo sustituido; apagarlo aquí dejaría al tablero sin el informe

### Pruebas

- [ ] T024 [US1] ⚠️ **Prueba de que la completitud puede bajar del 100 %** en `dags/tests/test_ot21_completitud.py`: cargar en la partición de prueba un caso **sin severidad** y comprobar que el porcentaje baja. Si sigue en `1.0000`, la consulta heredó el defecto (SC-002)
- [ ] T025 [P] [US1] Prueba de que **ningún caso se pierde al clasificar** en `dags/tests/test_ot21_distribuciones.py`: la suma de todas las categorías es igual al total del período, con lo no resoluble bajo `Desconocido` (SC-007)
- [ ] T026 [P] [US1] Prueba de que **descartado, fusionado y cerrado no se confunden** en `dags/tests/test_ot21_descarte_fusion.py`: tres casos, uno de cada, cuentan cada uno en lo suyo
- [ ] T027 [P] [US1] Prueba de que el ranking **no devuelve coordenadas** en `dags/tests/test_ot21_ranking.py` (FR-015)
- [ ] T028 [US1] ⚠️ **Prueba de contraste** en `backend/apps/informes_tacticos/tests/api/test_contraste_ot21.py`: los **cinco** informes correctos de OT21 dan la misma cifra por el endpoint actual y por la consulta del catálogo. **La completitud queda excluida a propósito**: debe diferir, porque el endpoint actual está mal

**Checkpoint**: US1 entregable. Es el MVP: seis informes sobre el modelo y un defecto de tablero corregido.

---

## Phase 4: User Story 2 — El desempeño del despacho (Priority: P1)

**Goal**: los diez informes de OT22 y OT23, con la capacidad histórica y las posiciones completas.

**Independent Test**: cambiar el proveedor de una unidad, recargar, y comprobar que los informes de
un período anterior devuelven **exactamente las mismas cifras**.

**Criterio medible (ISO 25010 — Corrección funcional)**: la pérdida de señal pasa de considerar el
**16,9 %** de las posiciones a considerar el **100 %** (SC-004).

### Las consultas nuevas y migradas

- [ ] T029 [US2] ⚠️ Escribir `dags/lib/consultas/emergencias/ot22_ratio_demanda_capacidad.sql` — `unidades_vigentes` cuenta **versiones de unidad cuya vigencia cubre el período consultado**, no la flota de hoy. Es el defecto de CU-T08
- [ ] T030 [US2] Escribir `dags/lib/consultas/emergencias/ot22_primer_intento.sql` — indicador BSC con meta ≥90 %, calculable **solo con grano de intento**: `numero_intento = 1 AND resultado = 'confirmado'`
- [ ] T031 [US2] ⚠️ Escribir `dags/lib/consultas/emergencias/ot23_perdida_senal.sql` con parámetro `umbral_seg` — filtra por `segundos_desde_anterior`, ya medido en la carga. **Sin truncar**
- [ ] T032 [US2] ⚠️ Escribir `dags/lib/consultas/emergencias/ot23_desviacion_llegada.sql` — la referencia es la **mediana** de despachos comparables en una ventana **anterior** al despacho medido; sin `muestra_minima` llegadas, la referencia sale **ausente** (research D5)

### Las consultas de los que ya funcionan *(para el contraste, sin migrar endpoint)*

- [ ] T033 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_asignacion_automatica_vs_manual.sql`
- [ ] T034 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_tiempo_reportado_a_confirmado.sql`
- [ ] T035 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_tiempo_respuesta_por_severidad.sql`
- [ ] T036 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_rechazo_timeout_por_unidad.sql`, separando **rechazado de vencido**: el informe anterior los sumaba
- [ ] T037 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_carga_por_unidad.sql`
- [ ] T038 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot23_abortos_perdidas.sql`, con `abortado` como desenlace propio

### Los endpoints

- [ ] T039 [US2] Exponer los cuatro endpoints de esta historia —ratio demanda/capacidad, primer intento, pérdida de señal y desviación de llegada— en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-emergencias.openapi.yaml`
- [ ] T040 [US2] Documentar en la respuesta de la desviación que `segundos_referencia` es un **valor derivado del histórico**, y **no** un objetivo ni un SLA (FR-032)

### Pruebas

- [ ] T041 [US2] ⚠️ **Prueba de la capacidad histórica** en `dags/tests/test_ot22_ratio.py`: dar de baja una unidad, recargar dimensiones, y comprobar que `unidades_vigentes` de un período **anterior no cambia** (FR-006)
- [ ] T042 [US2] ⚠️ **Prueba de que la pérdida de señal no trunca** en `dags/tests/test_ot23_perdida_senal.py`: el número de posiciones consideradas es igual al del origen, y el resultado supera al de la tabla anterior
- [ ] T043 [US2] ⚠️ **Prueba de la referencia de llegada** en `dags/tests/test_ot23_desviacion.py`, con cuatro comprobaciones: usa mediana y no promedio; su ventana es anterior al despacho medido; sin muestra suficiente devuelve **ausente y no cero**; y los despachos sin llegada quedan fuera del cálculo (SC-011)
- [ ] T044 [P] [US2] Prueba de que **el primer intento se cuenta bien** en `dags/tests/test_ot22_primer_intento.py`: un caso con dos rechazos y una confirmación **no** cuenta como resuelto al primer intento
- [ ] T045 [P] [US2] Prueba de que **los cinco desenlaces se distinguen** en `dags/tests/test_ot23_abortos.py`: abortado no es rechazado, ni vencido, ni en curso
- [ ] T046 [US2] Prueba de que **el pasado no se reescribe** en `dags/tests/test_ot22_atribucion.py`: cambiar el proveedor de una unidad y comprobar que las cifras de un período anterior son idénticas (SC-003)
- [ ] T047 [US2] ⚠️ **Prueba de contraste** en `backend/apps/informes_tacticos/tests/api/test_contraste_ot22_ot23.py`: los **seis** informes correctos coinciden por ambos caminos. **Ratio y pérdida de señal quedan excluidos**: deben diferir

**Checkpoint**: US2 entregable. **Con US1 y US2 están cubiertos los cuatro indicadores BSC del departamento.**

---

## Phase 5: User Story 3 — Evidencia y cierre del caso (Priority: P2)

**Goal**: los diez informes de OT24 y OT25, con el modelo ampliado para sostenerlos.

**Independent Test**: tomar un caso cerrado con evidencia y otro sin ella y comprobar que la
cobertura los distingue.

**Criterio medible (ISO 25010 — Flexibilidad)**: ampliar el modelo con un hecho y ocho columnas
**no altera** ninguna cifra de US1 ni de US2 (SC-010).

> ⚠️ **Cinco de sus fuentes están casi vacías** (research D8): conductores y parámetros con **0
> filas**, historial de severidad y cierre con **1**, evidencia con **3**. Los informes son
> correctos y devolverán casi cero. **Las pruebas van con datos sintéticos**, porque con las fuentes
> vacías una consulta rota y un origen vacío se ven exactamente igual.

### Ampliar el modelo *(§4.bis del contrato de esquema)*

- [ ] T048 [US3] Añadir a `hecho_accidente` en `dags/lib/ddl.py` las ocho columnas de `data-model.md` §2.1, **todas `Nullable`**: `num_notas`, `num_conductores`, `num_implicados`, `num_elementos_clima`, `num_escaladas_severidad`, `severidad_inicial`, `resultado_atencion` y `calificacion`
- [ ] T049 [US3] Poblar los recuentos en `dags/lib/hechos/hecho_accidente.py`: **`0` cuando el caso existe y no tiene ninguno** —cero notas es una medición— y **ausente** en las filas anteriores a la métrica
- [ ] T050 [US3] Poblar `severidad_inicial`, `resultado_atencion` y `calificacion` en el mismo módulo: **ausentes cuando no se registraron**. Una calificación `0` sería la peor nota, no «sin calificar»
- [ ] T051 [US3] Crear `hecho_evidencia` en `dags/lib/ddl.py` según `data-model.md` §2.2: hecho de transacción, particionado por mes, **sin `idusuario`**
- [ ] T052 [US3] Implementar `dags/lib/hechos/hecho_evidencia.py`: fotos y notas en el mismo grano, con `sk_unidad` resuelto por **atribución histórica** y `segundos_hasta_sincronia` calculado al cargar
- [ ] T053 [US3] Implementar el flujo en `dags/lib/hecho_evidencia_tasks.py` y `dags/etl/dag_hecho_evidencia.py`, con sensor sobre el flujo de dimensiones, siguiendo el patrón de los cuatro hechos existentes
- [ ] T054 [US3] Añadir `modelo_hecho_evidencia` a `dags/tests/test_dag_integrity.py` y `hecho_evidencia` a las listas de tablas de `test_sin_datos_sensibles.py` e `test_informe_sin_flujo_propio.py`

### Las consultas

- [ ] T055 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_cobertura_evidencia.sql` — distingue con foto, con nota y con ambas
- [ ] T056 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_latencia_sincronizacion.sql` — las evidencias **aún sin sincronizar** cuentan en `pendientes` y su latencia es **ausente**, no infinita
- [ ] T057 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_completitud_enriquecimiento.sql`
- [ ] T058 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_volumen_evidencia_por_unidad.sql` — **por unidad, sin desglose por persona** (FR-034)
- [ ] T059 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_escaladas_severidad.sql`
- [ ] T060 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_distribucion_resultados.sql` — los casos sin calificar quedan **fuera del promedio** y se cuentan aparte
- [ ] T061 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_envejecimiento_cartera.sql` con parámetro `tramos_dias`, sobre casos **sin hora de cierre**
- [ ] T062 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_retiros_forzados_por_proveedor.sql`, agrupando por el proveedor **de aquel momento**
- [ ] T063 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_tiempo_asignado_a_cierre.sql` y `ot25_cierres_forzados.sql` para el contraste

### Los endpoints

- [ ] T064 [US3] Exponer los ocho endpoints nuevos de OT24 y OT25 en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-emergencias.openapi.yaml`

### Pruebas

- [ ] T065 [US3] ⚠️ **Prueba de que la cartera de casos abiertos no sale vacía** en `dags/tests/test_ot25_envejecimiento.py`: un caso abierto **no tiene fecha de cierre**; si la tuviera, todos los abiertos aparecerían cerrados y este informe devolvería cero para siempre
- [ ] T066 [P] [US3] Prueba de la cobertura de evidencia con **datos sintéticos** en `dags/tests/test_ot24_cobertura.py`: un caso con foto, otro con nota, otro con ambas y otro sin nada se reparten como corresponde
- [ ] T067 [P] [US3] Prueba de que una evidencia **sin sincronizar** no cuenta como latencia cero en `dags/tests/test_ot24_latencia.py`
- [ ] T068 [P] [US3] Prueba de que una **calificación ausente no es un cero** en `dags/tests/test_ot25_resultados.py`: el promedio la excluye en vez de hundirse
- [ ] T069 [P] [US3] Prueba de que **ningún informe de este bloque devuelve identidad de persona** en `dags/tests/test_ot24_sin_identidad.py`, incluido el volumen por unidad (FR-034)
- [ ] T070 [US3] ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_ot24.py`: tras añadir `hecho_evidencia` y las ocho columnas, **las cifras de US1 y US2 no cambian** (SC-010)
- [ ] T071 [US3] Prueba de contraste de los **dos** informes correctos de OT25 en `backend/apps/informes_tacticos/tests/api/test_contraste_ot25.py`

**Checkpoint**: los 26 informes disponibles sobre el modelo.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T072 [P] Prueba de latencia en `dags/tests/test_latencia_informes_emergencias.py`: los 26 informes responden en tiempo aceptable **con al menos tres meses** de datos, para que el particionado se ejercite (SC-009)
- [ ] T073 [P] Prueba de que **un período vacío devuelve cero filas** y no una fila de ceros, en `dags/tests/test_periodo_vacio.py` (FR-019, SC-011)
- [ ] T074 [P] Prueba de que **todo porcentaje viene con su denominador** en `dags/tests/test_denominador_visible.py`: un `12,5 %` sobre 8 casos y sobre 8 000 son afirmaciones muy distintas
- [ ] T075 Ejecutar `cd backend && python -m pytest -q` y verificar que **los 13 endpoints no migrados siguen intactos** y ninguna suite existente se movió
- [ ] T076 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §2.2 (la completitud baja), §2.3 (capacidad de entonces) y §2.7 (los trece coinciden)
- [ ] T077 Anotar en `decisiones-pendientes.md` que **quedan dos fuentes para los 13 informes no migrados**, con la prueba de contraste como vigilancia, y que la unificación depende de la decisión #20
- [ ] T078 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar el estado de los 26 informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` y **corregir allí el reparto simples/compuestos de Emergencias**, que hoy dice 14/25 cuando las filas dan 12/26 + 1

---

## Dependencies

```text
Phase 1 (Setup: sustrato y catálogo)
    ↓
Phase 2 (Foundational: repositorio, permisos, reglas) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ── independiente
    ├─→ Phase 4 (US2, P1) ── independiente
    └─→ Phase 5 (US3, P2) ── independiente, pero amplía el modelo
            ↓
    Phase 6 (Polish)
```

**Las tres user stories son independientes entre sí**: cada una toca informes distintos y consultas
distintas. US3 amplía el modelo, y por eso lleva T070 — la prueba de que esa ampliación **no mueve
las cifras** de las otras dos.

**Dentro de la fase 2**: T005 primero; T006 depende de él; T007–T010 son independientes; las cinco
pruebas dependen de sus módulos.

**Dentro de la fase 5**: T048–T054 (la ampliación) **antes** que T055–T063 (las consultas), que a su
vez van antes que los endpoints y las pruebas.

---

## Parallel Execution Examples

**Fase 3 — cinco consultas de OT21 a la vez:**

```text
T016 ot21_distribucion_severidad.sql
T017 ot21_distribucion_zona.sql
T019 ot21_descarte_fusion.sql
T020 ot21_ranking_ubicaciones.sql
T021 ot21_impacto_humano.sql
```

**Fase 4 — las seis consultas de contraste:**

```text
T033 ot22_asignacion_automatica_vs_manual.sql
T034 ot22_tiempo_reportado_a_confirmado.sql
T035 ot22_tiempo_respuesta_por_severidad.sql
T036 ot22_rechazo_timeout_por_unidad.sql
T037 ot22_carga_por_unidad.sql
T038 ot23_abortos_perdidas.sql
```

**Fase 5 — las nueve consultas de OT24 y OT25, tras la ampliación:**

```text
T055 … T063
```

---

## Implementation Strategy

### MVP — US1

Seis informes sobre el modelo y **un defecto de tablero corregido**: la completitud deja de decir
siempre «100 % completo». Es entregable por sí solo y demuestra la tesis del módulo con el informe
donde más se nota.

### Entrega incremental

1. **Fases 1–2** — el sustrato y las dos reglas que no avisan cuando se incumplen.
2. **Fase 3 (US1)** — **MVP**.
3. **Fase 4 (US2)** — con US1, los **cuatro indicadores BSC** del departamento quedan cubiertos.
4. **Fase 5 (US3)** — el modelo crece y cierra el ciclo del caso.
5. **Fase 6** — cierre, contraste y documentación.

### Cinco riesgos a vigilar

**T011 vigila el fallo más difícil del modelo.** Olvidar la versión final devuelve cifras infladas
**solo a veces**, según si la fusión ya ocurrió. Quien lo reporte verá cifras normales al
comprobarlo. Por eso la prueba mira el **texto** de las consultas y no su resultado.

**T024 es la prueba que justifica migrar la completitud.** Si tras escribir la consulta nueva el
porcentaje sigue clavado en `1.0000`, se copió el defecto en vez de corregirlo — y nada más lo
delataría.

**T041 y T042 encontrarán diferencias esperadas, y hay que no «arreglarlas».** El ratio y la pérdida
de señal **deben** diferir del endpoint actual: esas diferencias son el arreglo. Quien las vea sin
contexto las tomará por una regresión.

**Las pruebas de OT24 deben usar datos sintéticos.** Con conductores a 0 filas y evidencia a 3, una
consulta rota y un origen vacío devuelven lo mismo: cero.

**T028, T047 y T071 son la única defensa contra dos verdades.** Mientras 13 informes se sirvan por
dos caminos, solo esas pruebas garantizan que dan la misma cifra. Si se saltan, la divergencia se
descubrirá cuando alguien decida con el número equivocado.
