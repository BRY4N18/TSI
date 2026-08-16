# Tasks: Modelo Analítico Táctico (esquema en estrella)

**Input**: Design documents from `specs/002-tactico/modelo-analitico/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D1, D2, D3 y D5 exigen pruebas concretas sin las cuales el modelo reproduciría en silencio los
defectos que existe para corregir.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**No depende de `core/informes/`** ni de ninguno de los ocho módulos de listados: vive en el stack
táctico, del que solo se ha verificado que existe. **Es el primer módulo de la serie que levanta el
stack táctico de verdad.**

**Y sustituye un diseño en producción.** Las tres tablas por informe y sus tres flujos se retiran
**solo cuando el modelo cubra sus informes con cifras coincidentes** (research D7), no antes.

---

## Phase 1: Setup — levantar y verificar el stack táctico

**Purpose**: comprobar que el sustrato existe y funciona. **Hasta ahora nunca se ha verificado**, y
los tres informes compuestos devuelven `500` por eso.

- [X] T001 Levantar el stack táctico con `docker compose -f docker/docker-compose.tactico.yml up -d` y comprobar que el almacén responde a `curl -s http://localhost:8123/ping`
- [X] T002 Verificar que el planificador, la interfaz web y el metastore del orquestador quedan en estado saludable, con `docker compose -f docker/docker-compose.tactico.yml ps`
- [X] T003 Verificar la conectividad **hacia el origen** desde el orquestador, consultando un recuento de accidentes con `lib/pinot_http_client.py` — debe devolver un número, no un error de resolución de nombre
- [X] T004 [P] Verificar la conectividad **hacia el almacén** desde el orquestador con `lib/clickhouse_http_client.py`
- [X] T005 [P] Ejecutar los tres flujos existentes y **anotar las cifras que devuelven sus tablas**, en `specs/002-tactico/modelo-analitico/quickstart.md` — son la referencia contra la que se validará el modelo antes de retirarlas (research D7)

> ⚠️ **Si T001 falla, todo lo demás es inútil.** Resolverlo antes de seguir.

**Resultado (2026-08-14): fase 1 verde.** ClickHouse 24.8.14.39 responde `Ok.`; los cuatro
contenedores quedan `healthy`; Pinot devuelve 4 252 accidentes desde el contenedor del orquestador; y
los tres flujos corren en verde. Cifras de referencia y cuatro observaciones del estado inicial en
[`quickstart.md` §3.8](quickstart.md).

**Causa confirmada de los `500`:** antes de T001 la base `tsi_tactico` **estaba vacía** —
`SHOW TABLES` devolvía cero filas—. Las tres tablas no existían porque sus flujos nunca se habían
ejecutado, no por un defecto del código de lectura.

---

## Phase 2: Foundational — el esqueleto del modelo

**Purpose**: las piezas compartidas por los tres hechos y todas las dimensiones.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T006 Reemplazar `dags/lib/ddl.py`: pasa de definir las tres tablas de informe a definir el modelo —5 dimensiones y 2 hechos— según `contracts/esquema-analitico.md`. **Las tres definiciones antiguas se conservan hasta la fase 6**, cuando sus tablas se retiren
- [X] T007 Implementar el versionado de dimensiones en `dags/lib/dimensiones/versionado.py`: dada la fila actual del origen y la versión vigente en el modelo, decidir si abrir versión nueva —cerrando la anterior— o no tocar nada (research D2)
- [X] T008 Implementar en el mismo módulo la marca `inicio_es_real`: **`0` cuando la fecha de inicio de una versión es la primera carga y no un cambio observado** (research D2, FR-021)
- [X] T009 Implementar la carga idempotente por partición en `dags/lib/carga_particion.py`: descartar la partición del período y repoblarla. **Prohibido usar borrado por condición**, que es una mutación y se acumula con 13 hechos (research D3)
- [X] T010 Implementar la fila «desconocida» de cada dimensión en `dags/lib/dimensiones/desconocido.py`, a la que apuntan los hechos cuya entidad aún no existe (FR-015)
- [X] T011 [P] Pruebas del versionado en `dags/tests/test_versionado.py`: atributo sin cambios no abre versión; atributo cambiado cierra la vigente y abre una nueva; la primera versión de una entidad lleva `inicio_es_real = 0`
- [X] T012 [P] Pruebas de la carga por partición en `dags/tests/test_carga_particion.py`: **recargar el mismo período deja el mismo número exacto de filas**, y no se emite ningún borrado por condición
- [X] T013 [P] Pruebas de la fila desconocida en `dags/tests/test_desconocido.py`: un hecho cuya dimensión no existe **se carga igualmente**, apuntando a la fila desconocida

**Checkpoint**: esqueleto listo — las tres user stories pueden abordarse.

### Resultado (2026-08-14): fase 2 verde

**Suite de `dags/`: 61 pasan** (26 de línea base + 35 nuevas), corrida dentro del contenedor —el
host no tiene `airflow` ni `pyarrow`, así que `python -m pytest dags/tests` desde el host **no es la
línea base válida**.

Las 7 tablas del modelo existen en `tsi_tactico`, con los dos hechos en `ReplacingMergeTree`
particionados por `toYYYYMM(fecha)`, los 4 hitos de `hecho_accidente` en `Nullable` y **cero columnas
de coordenadas** en todo el modelo. Las tres tablas del diseño anterior siguen intactas.

**Comprobado también contra ClickHouse real, no solo contra dobles**: recargar el mismo período deja
8 filas y no 16; recargar un mes no toca el otro; y `particiones_vacias` sí vacía un período que dejó
de traer filas.

#### Tres decisiones que el diseño no fijaba y hubo que tomar

1. **`inicio_es_real = 1` exige que quien llama aporte el instante.** Detectar un cambio al cargar
   **no** lo convierte en observado: el cambio pudo ocurrir en cualquier momento desde la carga
   anterior, y lo único que se sabe es que ya había ocurrido al mirar. Solo una tabla de historial
   del origen da una fecha real. Esto hace que T033 (unidad siempre `0`) se cumpla por construcción.
2. **La clave sustituta es un hash determinista** de (clave de negocio, inicio de vigencia). Un
   contador incremental daría claves distintas en cada corrida y el hecho quedaría apuntando a una
   versión huérfana tras la primera recarga.
3. **`particiones_vacias` cubre un caso que corrompe en silencio**: si un período que tenía filas
   pasa a no tener ninguna, nadie descartaría su partición y **las filas viejas sobrevivirían** a una
   recarga que debía dejarlo vacío. Hay una prueba que ejecuta el fallo y otra el arreglo.

#### El coste de las mutaciones, medido

`system.mutations` tiene **5 mutaciones, todas de las tres tablas viejas y ninguna del modelo**. Y
son peores de lo que describía research D3: cada corrida emite un `DELETE WHERE periodo IN (…)` con
**unas 180 fechas literales**. Con 13 hechos ese patrón es justo lo que el descarte de partición
evita.

---

## Phase 3: User Story 1 — Un informe responde sin recalcular nada (Priority: P1) 🎯 MVP

**Goal**: las cinco dimensiones y los dos hechos cargados, de modo que un informe del catálogo se
resuelva con una consulta.

**Independent Test**: tomar un informe del catálogo, escribir su consulta contra el modelo y
comprobar que devuelve la cifra correcta sin tocar el origen ni crear tabla alguna.

**Criterio medible (ISO 25010 — Functional Suitability)**: dos formas distintas de medir «casos por
severidad y mes» —por la columna desnormalizada y uniendo con la dimensión— devuelven **cifras
idénticas** (T026).

### Dimensiones

- [X] T014 [P] [US1] Implementar la generación de `dim_tiempo` en `dags/lib/dimensiones/dim_tiempo.py`: una fila por día, con año, trimestre, mes, semana, día de semana y marca de fin de semana. **Se genera, no se extrae**
- [X] T015 [P] [US1] Implementar `dim_geografia` en `dags/lib/dimensiones/dim_geografia.py`: **una fila por calle con todos sus ascendientes aplanados** —ciudad, condado, estado, país— para que agrupar por condado sea una columna y no tres saltos. **Sin coordenadas**
- [X] T016 [P] [US1] Implementar `dim_severidad` en `dags/lib/dimensiones/dim_severidad.py`, con el orden de gravedad para poder ordenar por severidad y no alfabéticamente
- [X] T017 [P] [US1] Implementar `dim_origen_despacho` en `dags/lib/dimensiones/dim_origen_despacho.py`
- [X] T018 [US1] Implementar `dim_unidad` **versionada** en `dags/lib/dimensiones/dim_unidad.py`, usando el versionado de T007: una fila por versión, con el proveedor de esa versión, su vigencia y la marca de inicio real
- [X] T019 [US1] Implementar el flujo de dimensiones en `dags/etl/dag_dimensiones.py`, siguiendo el patrón de ficheros intermedios ya fijado. **Debe correr antes que cualquier flujo de hechos**

### Hechos

- [X] T020 [US1] Implementar `hecho_accidente` en `dags/lib/hechos/hecho_accidente.py` como **instantánea acumulada**: una fila por caso, con una columna por hito y las métricas de impacto humano. **Los hitos no alcanzados van ausentes, nunca cero ni fecha de carga** (research D5)
- [X] T021 [US1] Implementar en el mismo módulo la desnormalización selectiva: copiar en el hecho severidad, condado, ciudad y franja horaria — los atributos por los que casi siempre se agrupa (research D4)
- [X] T022 [US1] Implementar `hecho_despacho` en `dags/lib/hechos/hecho_despacho.py` como **instantánea acumulada con grano de intento**: una fila por notificación de despacho, con sus hitos, su número de intento y su resultado (research D1)
- [X] T023 [US1] Implementar en el mismo módulo la resolución de `sk_unidad`: **la versión de unidad vigente en el momento del despacho**, no la actual. Copiar el proveedor de esa versión (research D2, D4)
- [X] T024 [US1] Implementar los flujos `dags/etl/dag_hecho_accidente.py` y `dags/etl/dag_hecho_despacho.py`, con carga idempotente por partición y dependencia declarada del flujo de dimensiones

### Pruebas

- [X] T025 [P] [US1] Prueba de que un **hito no alcanzado se guarda ausente** en `dags/tests/test_hecho_accidente_hitos.py`: cero filas con hito de cierre igual a la fecha cero. Un caso abierto guardado como cerrado en 1970 destruiría cualquier promedio de duración (SC-007)
- [X] T026 [P] [US1] ⚠️ **Prueba de cifras coincidentes** en `dags/tests/test_coherencia_desnormalizacion.py`: «casos por severidad y mes» calculado por la columna desnormalizada del hecho y uniendo con la dimensión devuelve **lo mismo**. Si difieren, la desnormalización se desincronizó de su dimensión — el fallo clásico de este diseño (SC-004)
- [X] T027 [P] [US1] Prueba de que **recargar un período no duplica** en `dags/tests/test_idempotencia_hechos.py`: mismo recuento exacto tras la segunda corrida (SC-005)
- [X] T028 [P] [US1] Prueba de que un **accidente cuya calle no existe se conserva** en `dags/tests/test_hecho_sin_dimension.py`, apuntando a la fila desconocida. **Perder un accidente porque falta una calle sería inaceptable** (SC-008)
- [X] T029 [P] [US1] Prueba de que **el modelo no contiene dato sensible** en `dags/tests/test_sin_datos_sensibles.py`: ninguna columna de latitud, longitud, nombre de persona ni identificación en los dos hechos ni en las cinco dimensiones
- [X] T030 [P] [US1] Prueba de que un informe del catálogo **se resuelve con una sola consulta** en `dags/tests/test_informe_sin_flujo_propio.py`, sin crear tabla alguna (SC-001)

**Checkpoint**: US1 entregable. Es el MVP: el modelo existe y sirve informes.

### Resultado (2026-08-14): fase 3 verde

**Suite de `dags/`: 93 pasan, ninguna omitida.** El modelo está cargado:

| Tabla | Filas | Comprobación |
|---|---|---|
| `dim_tiempo` | 592 | generada, sin días ausentes |
| `dim_geografia` | 3 | el origen solo tiene 2 calles; ambas resueltas + la desconocida |
| `dim_severidad` | 5 | 4 del catálogo + la desconocida |
| `dim_origen_despacho` | 4 | 3 del catálogo + la desconocida |
| `dim_unidad` | 19 | 18 unidades + la desconocida, todas `inicio_es_real = 0` |
| `hecho_accidente` | 4 252 | **exactamente los del origen**: ninguno perdido |
| `hecho_despacho` | 4 314 | **exactamente los del origen** |

Cero hitos en la época cero; 616 casos sin cierre y 615 sin llegada, correctamente ausentes. «Casos
por severidad y mes» da **cifras idénticas** por la columna desnormalizada y uniendo con la dimensión
(SC-004). Ocho informes del catálogo responden con **una sola consulta cada uno** y sin crear tabla
alguna (SC-001).

#### ⚠️ Un defecto de diseño encontrado al ejecutar, no al escribir

La primera versión de cada unidad empezaba **en el instante de la primera carga**. Como todo el
histórico es anterior, `version_vigente_en` no encontraba versión que lo cubriera y **los 4 314
despachos quedaron con proveedor «Desconocido»**.

Era coherente con la letra de research D2 y contrario a su propósito: el research promete que antes
del versionado se vería «el estado conocido al arrancar», **que sigue siendo útil**. Un modelo que
pierde la atribución de todo el histórico es peor que el defecto que vino a corregir.

**Corrección:** la primera versión de una entidad **abre por la izquierda** (`INICIO_DESCONOCIDO`),
no en el instante de la carga. `inicio_es_real = 0` sigue diciendo la verdad —no es un inicio
observado—, y un cambio posterior sí abre una versión fechada a partir de la cual la atribución es
exacta. Tras la corrección los 4 314 despachos quedan atribuidos. Hay tres pruebas nuevas que fijan
la regla, incluida la del **instante exacto del cambio**, que debe caer en una sola versión: con
ambos extremos cerrados, un despacho ocurrido justo entonces se contaría dos veces.

#### Cuatro decisiones que el contrato no fijaba

1. **`abortado` es un quinto resultado de despacho.** El contrato enumeraba cuatro
   (confirmado/rechazado/vencido/en_curso), pero el catálogo del origen tiene `Abortado` y el informe
   de rendimiento por proveedor **ya publica un porcentaje de abortos**. Plegarlo a `en_curso` habría
   vaciado en silencio una cifra que hoy se publica. Reparto real: 3 310 confirmados, 334 rechazados,
   331 abortados, 327 vencidos, 12 en curso.
2. **Los hitos de despacho salen de `Fact_HistorialDespachoUnidad`, no de `Fact_NotificacionDespacho`.**
   Esta última **no tiene hora propia de confirmación ni de rechazo** —solo su última escritura— y
   además está casi vacía: **31 filas para 4 314 despachos**. Construir sobre ella habría producido
   cifras plausibles y falsas.
3. **Las columnas desnormalizadas se copian desde las dimensiones ya cargadas, no desde el origen.**
   Es lo que hace que la copia y su dimensión no puedan divergir, y lo que da sentido real a T026.
4. **Los DAGs de hechos esperan al de dimensiones con un sensor**, no con el horario. Dos flujos
   `@daily` no garantizan orden entre sí, y un hecho cargado antes que sus dimensiones se queda con
   severidad, ciudad y condado en blanco — sin error y sin aviso.

#### Dos defectos propios corregidos sobre la marcha

- **`resolver_o_desconocido` devolvía la fila de la dimensión en vez de su clave**, así que el hecho
  intentaba meter un diccionario entero en una columna. Se corrigió en el ayudante —que era donde
  estaba la ambigüedad— y se añadió la prueba que lo habría atrapado: la anterior usaba un mapa donde
  clave y valor coincidían, y por eso no lo veía.
- **El paso por parquet cambia los tipos**: una sola fila con `capacidad` ausente convierte la
  columna entera a decimal y `4` pasa a `4.0`, que el almacén rechaza con un error de análisis
  sintáctico que no menciona la causa. Se resolvió leyendo el **tipo declarado por la tabla**
  (`dags/lib/tipos_almacen.py`) en vez de adivinar por la parte fraccionaria — la heurística fácil
  funcionaría hoy y rompería la primera métrica decimal que se añadiera.

#### Un cambio en pieza compartida

`parquet_io.stage_path` acepta ahora un `prefijo` opcional. Sin él los tres flujos nuevos se
pisarían: corren el mismo día, comparten `ts`, y el de hechos depende de que el de dimensiones haya
dejado su fichero intacto. **La convención de carpetas no cambia** —sigue sin segmento de `dag_id`,
como se decidió—; solo se distingue el nombre del fichero.

---

## Phase 4: User Story 2 — El pasado no se reescribe (Priority: P1)

**Goal**: que un informe histórico atribuya los hechos a la versión de la entidad vigente en su
momento.

**Independent Test**: cambiar el proveedor de una unidad, recargar, y comprobar que sus despachos
anteriores siguen atribuidos al proveedor anterior.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de los despachos anteriores a un
cambio de proveedor conserva su atribución original (T032).

> **Misma prioridad que US1, y no es un descuido.** Un modelo que no resuelva esto **produce cifras
> equivocadas sin avisar**, que es peor que no tenerlas. US1 sin US2 sería reproducir el defecto
> actual con más pasos.

### Implementación

> **T031 se adelantó a la fase 3**: `hecho_despacho` (T023) no puede resolver `sk_unidad` sin ella,
> así que implementarla después habría exigido cargar el hecho dos veces. Está probada en
> `dags/tests/test_versionado.py`. **La prueba ancla T034 sigue pendiente**, y no es un trámite: con
> los datos actuales pasaría en vacío, porque el origen tiene un solo proveedor.

- [X] T031 [US2] Implementar la resolución histórica en `dags/lib/dimensiones/versionado.py`: dada una entidad y un instante, devolver la versión vigente entonces. Es lo que T023 consume al cargar el hecho de despacho
- [X] T032 [US2] Implementar la reconstrucción del histórico reconstruible en `dags/lib/dimensiones/reconstruccion.py`, para las dimensiones cuyo origen sí lo guarda —partner y región—, marcando esas versiones con `inicio_es_real = 1` (research D2)
- [X] T033 [US2] Garantizar que **las versiones de unidad llevan `inicio_es_real = 0`**: nada en el origen historiza el cambio de proveedor, así que su historia empieza en la primera carga y el modelo debe declararlo (research D2)

### Pruebas

- [X] T034 [US2] ⚠️ **Prueba del caso ancla** en `dags/tests/test_atribucion_historica.py`: cargar despachos de una unidad, **cambiar su proveedor en el origen**, recargar, y comprobar que los despachos anteriores **siguen atribuidos al proveedor anterior**. Si aparecen bajo el nuevo, el modelo no ha resuelto nada y reproduce el defecto documentado (SC-003)
- [X] T035 [P] [US2] Prueba de que la dimensión tiene **dos versiones** de esa unidad —la primera cerrada, la segunda vigente— en `dags/tests/test_versiones_unidad.py`
- [X] T036 [P] [US2] Prueba de que **una entidad que nunca cambió se comporta como si no hubiera versionado** en `dags/tests/test_versionado_caso_simple.py`: el mecanismo no penaliza el caso común
- [X] T037 [P] [US2] Prueba de que **ambas lecturas son posibles** en `dags/tests/test_lectura_historica_y_actual.py`: agrupar por el proveedor histórico y por el actual devuelven resultados **distintos y ambos correctos** (FR-009)
- [X] T038 [P] [US2] Prueba de que `inicio_es_real` distingue una fecha observada de «desde la primera carga», en `dags/tests/test_inicio_real.py` (FR-021)

**Checkpoint**: US2 entregable. **Con US1 y US2 el modelo cumple su propósito.**

### Resultado (2026-08-14): fase 4 verde — **el MVP está completo**

**Suite de `dags/`: 128 pasan, ninguna omitida.** Se añadieron `reconstruccion.py` y seis ficheros de
prueba (`test_atribucion_historica`, `test_versiones_unidad`, `test_versionado_caso_simple`,
`test_lectura_historica_y_actual`, `test_inicio_real`, `test_reconstruccion`).

#### La prueba ancla (T034) usa una unidad sintética, y es deliberado

El origen tiene **un solo proveedor**: las 18 unidades son de `idcliente = 1`. Una prueba escrita
contra los datos reales **pasaría en vacío** —no habría dos proveedores que distinguir— y daría
confianza falsa sobre justo la propiedad que más importa.

La prueba fabrica el escenario y lo hace pasar por **la tubería real**: el mismo versionado, la misma
resolución histórica y el mismo constructor del hecho que usa la carga de producción. **Lo sintético
son los datos, no el camino.** Corre en dos niveles: sobre la lógica, y contra el almacén con carga,
cambio de proveedor y recarga completa.

Incluye una prueba que **reproduce el defecto**: con una sola versión —el estado actual— los dos
despachos se atribuyen al proveedor nuevo, incluido el de marzo. Sin ella, la prueba ancla podría
pasar por casualidad y nadie lo sabría.

#### Tres trampas de las bitácoras reales, encontradas en `Fact_HistorialAccesoPartner`

Las tres producen versiones falsas si se toma la bitácora al pie de la letra, y las tres están en los
datos de verdad:

1. **Eventos que no cambian nada.** Un `revocacion_credencial` aparece con `Activo → Activo`: hubo un
   suceso, pero el atributo versionado no se movió. Tomar cada evento como un cambio inflaría
   «cuántas veces cambió de plan».
2. **Eventos duplicados a milisegundos.** Dos `desactivacion_por_cascada` del mismo partner con 46 ms
   de diferencia y los mismos valores.
3. **Lo anterior al primer evento no tiene fecha.** El valor de partida se conoce —lo dice el
   `estado_anterior` del primer evento— pero desde cuándo, no. Esa versión abre por la izquierda con
   `inicio_es_real = 0`.

La reconstrucción también expone `divergencias()`, que compara la última versión reconstruida con el
valor actual: **una bitácora incompleta produce una historia que parece correcta y termina en un
valor equivocado**, y entonces el error no está en la última versión sino en todas. Devuelve la lista
en vez de lanzar, porque una historia reconstruida imperfecta sigue siendo mejor que ninguna — pero
debe verse.

#### Un defecto de la propia prueba, encontrado al comprobar los totales

La prueba ancla escribe en el hecho de producción, y sus fechas sintéticas estaban en 2026 — es
decir, en particiones **reales**. La limpieza descarta la partición de prueba, así que no las
alcanzaba: **`hecho_despacho` pasó de 4 314 a 4 316 filas**, con dos despachos de una unidad que no
existe, de forma permanente y sin que ninguna prueba fallara.

Corregido llevando todas las fechas del escenario a la partición de prueba, y añadida la
comprobación que lo detecta sola. Tras la suite completa los totales vuelven a ser **4 252 y 4 314**,
exactamente los del origen.

Es el mismo patrón que este módulo persigue en el dominio: **un fallo que no rompe nada y solo
altera una cifra**. Solo apareció porque se comprobaron los totales después de correr las pruebas,
no porque las pruebas lo dijeran.

#### T033 se cumple por construcción, no por disciplina

`dim_unidad.construir` **rechaza** cualquier versión con `inicio_es_real = 1`. Es una afirmación
sobre el origen, no sobre el código: nada historiza el cambio de unidad a proveedor. Si algún día el
origen empezara a hacerlo, el error salta y obliga a decidir conscientemente —reconstruir el
histórico— en vez de que la marca cambie de significado sin que nadie lo advierta.

---

## Phase 5: User Story 3 — El modelo crece sin rehacer lo construido (Priority: P2)

**Goal**: demostrar que añadir hechos, dimensiones y métricas no altera lo existente.

**Independent Test**: añadir un hecho nuevo y comprobar que los informes existentes dan las mismas
cifras.

**Criterio medible (ISO 25010 — Flexibility)**: añadir un hecho deja inalterado el 100 % de los
resultados anteriores (T040).

### Implementación

- [X] T039 [US3] Documentar en `contracts/esquema-analitico.md` el procedimiento para añadir un hecho, una dimensión o una métrica, con las garantías que debe preservar
- [X] T040 [US3] Implementar un **tercer hecho de prueba** —el más simple del diseño, estado de unidad— en `dags/lib/hechos/hecho_estado_unidad.py`, para ejercitar el crecimiento de verdad y no solo documentarlo

### Pruebas

- [X] T041 [P] [US3] Prueba de que **añadir un hecho no altera los existentes** en `dags/tests/test_crecimiento_aditivo.py`: las cifras de accidente y despacho no cambian tras incorporar el tercero (SC-006)
- [X] T042 [P] [US3] Prueba de que una **métrica añadida se presenta ausente en las filas anteriores, nunca como cero**, en `dags/tests/test_metrica_nueva.py` (FR-018)
- [X] T043 [P] [US3] Prueba de que **añadir un atributo a una dimensión compartida no rompe los hechos que ya la usaban**, en `dags/tests/test_dimension_ampliada.py`

**Checkpoint**: el crecimiento está probado, no solo prometido.

### Resultado (2026-08-14): fase 5 verde

El tercer hecho (`hecho_estado_unidad`) se añadió **siguiendo el procedimiento recién documentado**,
y las cifras de los dos anteriores no se movieron. El procedimiento vive en
[`contracts/esquema-analitico.md` §4.bis](contracts/esquema-analitico.md).

**Ejercita el otro camino del diseño**: es de transacción, no instantánea acumulada, así que usa
`MergeTree` y **no admite `FINAL`** — pedirlo falla con `ILLEGAL_FINAL`. La distinción salió a la luz
al escribir su propia prueba, que aplicaba `FINAL` a los tres hechos por costumbre. Ahora hay una
prueba que fija los tres motores y comprueba que el error salta.

**Se extrajo `dags/lib/hechos/atribucion.py`.** El tercer hecho necesita la misma resolución
histórica que el de despacho, y hacer que importara una función privada del otro habría creado una
dependencia entre hechos que **no existe en el modelo**: son tablas independientes que comparten una
dimensión. Esa dependencia falsa se notaría el día que uno de los dos se retirara.

---

## Phase 6: Retirada del diseño anterior

**Purpose**: sustituir las tres tablas por informe, **solo cuando el modelo las cubra con cifras
coincidentes**.

- [X] T044 Escribir la consulta equivalente de **pérdida de señal** sobre el modelo, reutilizando la lógica pura de detección de huecos que ya existe y está probada, en `dags/lib/consultas/perdida_senal.sql`
- [X] T045 [P] Escribir la consulta equivalente de **índice de calidad** sobre el modelo en `dags/lib/consultas/indice_calidad.sql`. **Corregir de paso el defecto de completitud**: la condición debe comparar contra los centinelas del origen, no contra nulidad
- [X] T046 [P] Escribir la consulta equivalente de **rendimiento por proveedor** sobre el modelo en `dags/lib/consultas/rendimiento_proveedor.sql`, **usando la atribución histórica** — es el informe cuyo defecto justificó el modelo
- [X] T047 ⚠️ **Comparar las tres consultas con las cifras anotadas en T005** y documentar cualquier diferencia. **El rendimiento por proveedor diferirá a propósito**: la cifra vieja usa el proveedor actual y la nueva el histórico. Esa diferencia **es el arreglo**, no un error — hay que verificarla y explicarla, no eliminarla
- [ ] T048 ⛔ **BLOQUEADO** — Retirar `dags/etl/indice_calidad_dag.py`, `dags/etl/perdida_senal_dag.py` y `dags/etl/rendimiento_proveedor_dag.py`, y sus tres definiciones de tabla de `dags/lib/ddl.py`, **solo tras T047**
- [X] T049 Retirar la spec del módulo `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`, o marcarla como sustituida, según lo acordado

### Resultado (2026-08-14): fase 6 — verificada, **retirada bloqueada a propósito**

#### El modelo no cubría dos de los tres informes, y hubo que ampliarlo

Al escribir las consultas equivalentes aparecieron dos huecos que el diseño de fase 1 no preveía:

- **La cobertura de evidencia** no era calculable → se añadió `num_evidencias` a `hecho_accidente`,
  siguiendo el §4.bis (métrica `Nullable`, sin recargar nada más).
- **La pérdida de señal** necesita instantes de posición → se añadió un **cuarto hecho**,
  `hecho_ping_unidad` (59 045 filas), **sin latitud ni longitud**: la continuidad de la señal se mide
  con los instantes, no con las posiciones. Es el caso que mejor ilustra la exclusión del §5.

#### T047: la comparación, y lo que reveló ⚠️

| Informe | Su tabla | Desde el modelo | Veredicto |
|---|---|---|---|
| Pérdida de señal | 714 huecos | **3 942** | La tabla veía el **16,9 %** de los datos |
| Índice de calidad | 0.7296 | 0.7289 | Coincide salvo cobertura de evidencia |
| Rendimiento — llegada media | 669.44 s | **669.44 s** | **Idéntico** |
| Rendimiento — rechazos | 344 | **661** | La tabla veía el **51 %** de las transiciones |

**La diferencia esperada no era la que esperábamos.** Se anticipaba que el rendimiento por proveedor
divergiría por usar atribución histórica; con los datos actuales **no diverge por eso** —el origen
tiene un solo proveedor y ninguna unidad ha cambiado—. Lo que sí apareció es un defecto peor:

⚠️ **Dos consultas de los flujos viejos no llevan `LIMIT` explícito**, así que reciben el límite por
defecto del cliente —10 000 filas— y **truncan en silencio**: 10 000 de 59 045 posiciones y 10 000 de
19 528 transiciones. Los informes publicaban esos resultados como completos.

**Validado en las dos direcciones:** corriendo la **lógica del flujo viejo sobre datos completos**
salen 3 942 huecos, 661 rechazos y 331 abortos — exactamente lo que devuelve el modelo. No es que el
modelo calcule distinto; es que el viejo miraba menos datos.

Es la mejor justificación posible del `LIMITE` explícito en todas las consultas del modelo.

#### Por qué T048 queda bloqueado

Las tres tablas y sus flujos **siguen vivos**. Los leen tres repositorios del backend
(`backend/core/repositories/informes_tacticos/*_repository.py`), además de `dag_backfill`,
`dag_validacion_calidad` y `dag_mantenimiento_bd`.

Dejar de refrescarlas mientras los endpoints siguen consultándolas serviría **datos congelados sin
error visible**, que es peor que retirarlas del todo o que no tocar nada. Y retirar endpoints en
funcionamiento no es una decisión técnica: está registrada como **decisión pendiente #20**, con sus
dos opciones (repuntar los repositorios al modelo, o retirarlos con el módulo sustituido).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T050 [P] Prueba de rendimiento en `dags/tests/test_latencia_consultas.py`: las consultas de los informes del catálogo sobre el modelo responden en tiempo aceptable **con al menos tres meses de datos**, para que el particionado se ejercite de verdad
- [X] T051 [P] Prueba de que **omitir el forzado de versión final produce duplicados** en `dags/tests/test_regla_final.py` — documenta ejecutablemente por qué la Regla 2 del contrato de consumo existe
- [X] T052 Ejecutar `cd backend && python -m pytest -q` y verificar que **ninguna suite del sistema operativo se movió**: este módulo solo lee el origen
- [X] T053 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.4 (el pasado no se reescribe) y §3.8 (los tres informes coinciden)
- [X] T054 Anotar en `decisiones-pendientes.md` que **la atribución histórica unidad↔proveedor empieza en la primera carga del modelo**, porque el origen nunca guardó ese cambio — y preguntar si se quiere añadir esa historización al sistema operativo para el futuro
### Resultado (2026-08-14): fase 7 verde — **módulo cerrado**

**Suite de `dags/`: 151 pasan, ninguna omitida.** **Backend: 1 673 pasan, 2 omitidas**, sin
movimiento respecto de la línea base (T052) — este módulo solo lee el sistema operativo.

**El quickstart se recorrió entero contra el stack levantado (T053): todo verde**, incluidos los dos
apartados críticos:

- **§3.4, el pasado no se reescribe:** ninguna versión de unidad declara inicio real, **los 4 314
  despachos tienen proveedor atribuido**, y el proveedor del hecho coincide con el de su versión en
  el 100 % de los casos.
- **§3.8, los tres informes coinciden:** tiempo medio de llegada **669.44 s == 669.44 s** y el mismo
  total de despachos.

**T051 documenta ejecutablemente la Regla 2**: escribe dos versiones del mismo caso y comprueba que
sin `FINAL` cuenta **dos** y con `FINAL` cuenta **una**. Es el fallo más difícil de diagnosticar del
diseño, porque desaparece solo cuando el motor fusiona en segundo plano — quien lo reporte verá
cifras normales al comprobarlo.

**Decisiones registradas:** #19 (historizar unidad↔proveedor en el sistema operativo) y #20 (qué
hacer con los endpoints de los tres informes sustituidos).

- [X] T055 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` con el estado de los tres informes migrados, y **añadir al contrato común** `specs/002-tactico/contrato-informes-simples.md` una referencia al contrato de consumo del modelo, para que quien especifique un informe compuesto sepa dónde están sus reglas

---

## Dependencies

```text
Phase 1 (Setup: levantar y verificar el stack táctico)
    ↓
Phase 2 (Foundational: versionado, particiones, fila desconocida) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ──┐
    │                        │ US2 depende de US1: necesita el hecho
    └─→ Phase 4 (US2, P1) ◄─┘  de despacho cargado para probar la atribución
            ↓
    Phase 5 (US3, P2)
            ↓
    Phase 6 (Retirada del diseño anterior)
            ↓
    Phase 7 (Polish)
```

**⚠️ US2 sí depende de US1**, a diferencia de todos los módulos anteriores: la prueba del caso ancla
necesita despachos cargados. Se puede implementar el versionado en paralelo (T031–T033), pero **la
prueba T034 requiere US1 terminada**.

**Dentro de la fase 2**: T007 primero, T008 depende de él; T009 y T010 son independientes; las tres
pruebas dependen de sus módulos.

**Dentro de la fase 3**: las cuatro dimensiones simples (T014–T017) son paralelas; T018 depende del
versionado; T019 depende de las cinco; los hechos dependen de T019.

**Fase 6 es secuencial y no debe adelantarse**: retirar antes de T047 dejaría al sistema sin esos
tres informes.

---

## Parallel Execution Examples

**Fase 3 — las cuatro dimensiones simples a la vez:**

```text
T014 dim_tiempo.py
T015 dim_geografia.py
T016 dim_severidad.py
T017 dim_origen_despacho.py
```

**Fase 3 — las pruebas tras la implementación:**

```text
T025 test_hecho_accidente_hitos.py
T026 test_coherencia_desnormalizacion.py
T027 test_idempotencia_hechos.py
T028 test_hecho_sin_dimension.py
T029 test_sin_datos_sensibles.py
T030 test_informe_sin_flujo_propio.py
```

**Fase 6 — las tres consultas equivalentes:**

```text
T044 perdida_senal.sql
T045 indice_calidad.sql
T046 rendimiento_proveedor.sql
```

---

## Implementation Strategy

### MVP — US1 **y** US2

**Es el único módulo de la serie cuyo MVP son dos historias.** US1 entrega el modelo; US2 entrega
que no mienta. Parar entre ambas dejaría un modelo que reproduce el defecto actual con más pasos —
peor que no haber empezado, porque parecería resuelto.

### Entrega incremental

1. **Fase 1** — el stack táctico verificado. **Es la primera vez que se levanta.**
2. **Fase 2** — versionado, particiones y fila desconocida.
3. **Fases 3–4 (US1 + US2)** — **MVP**. El modelo existe y atribuye el pasado correctamente.
4. **Fase 5 (US3)** — el crecimiento probado con un tercer hecho real.
5. **Fase 6** — retirada del diseño anterior, **solo tras verificar cifras**.
6. **Fase 7** — cierre y documentación.

### Cinco riesgos a vigilar

**T001 es la condición de todo.** Si el almacén no arranca, ni este módulo ni los tres informes
existentes tienen sentido. Nunca se ha verificado en toda esta serie.

**T034 es la prueba que justifica el módulo entero.** Si los despachos anteriores aparecen bajo el
proveedor nuevo, el modelo no resolvió nada. Es la única prueba de la serie que valida una **tesis de
diseño**, no un requisito.

**T047 encontrará una diferencia esperada, y hay que no «arreglarla».** El rendimiento por proveedor
dará cifras distintas a las de la tabla vieja, porque la vieja usa el proveedor actual y la nueva el
histórico. **Esa diferencia es el arreglo.** Quien la vea sin contexto la tomará por un error de
migración.

**T026 vigila el precio de la desnormalización.** Copiar atributos en el hecho es lo que da
rendimiento, y también lo que permite que el hecho y su dimensión se desincronicen. Sin esa prueba,
dos informes empezarían a discrepar sin que nadie sepa cuál creer.

**La fase 6 no debe adelantarse.** Retirar los tres flujos antes de verificar las cifras dejaría al
sistema sin esos informes — y sin forma de comparar.
