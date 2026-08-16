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

- [X] T001 Verificar que el modelo analítico está cargado y sus cuatro hechos tienen datos, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q` y comprobando que las tablas de `tsi_tactico` cuadran con el origen
- [X] T002 Crear el directorio del catálogo `dags/lib/consultas/emergencias/` con un `README.md` que fije las convenciones de `contracts/catalogo-consultas.md` §1
- [X] T003 [P] Implementar el cargador de consultas en `dags/lib/consultas/__init__.py`: dado un nombre, devuelve el SQL del fichero. **Sin construir SQL en Python** — el fichero es la definición canónica (research D1)
- [X] T004 [P] Prueba del cargador en `dags/tests/test_catalogo_consultas.py`: un nombre inexistente falla con un error que nombra el fichero buscado, no con un `KeyError` pelado

---

## Phase 2: Foundational — las piezas que comparten los 26 informes

**Purpose**: lo transversal, incluidas las dos reglas que se olvidan y no avisan.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T005 Implementar `backend/core/repositories/informes_tacticos/modelo_repository.py`: ejecuta una consulta del catálogo contra el almacén con parámetros con tipo. **Solo lectura**; reutiliza `core/clickhouse/client.py` sin añadir dependencias
- [X] T006 Implementar en el mismo repositorio la traducción de ausencia: un valor ausente del almacén llega a la respuesta como **nulo**, nunca como `0` ni como cadena vacía (FR-017)
- [X] T007 Implementar la resolución de período en `backend/apps/informes_tacticos/periodo.py` para estos informes, reutilizando lo existente: por defecto **los últimos 30 días**, ambos extremos inclusive
- [X] T008 Implementar el servicio base en `backend/apps/informes_tacticos/services/emergencias_compuestos_service.py`, que enlaza nombre de informe → consulta del catálogo → respuesta
- [X] T009 Implementar la vista base en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py`, reutilizando `views/base.py`, `envelope.py` y `permissions.py` ya existentes
- [X] T010 Aplicar los permisos en `backend/apps/informes_tacticos/permissions.py`, usando las constantes de `backend/core/auth/roles_tacticos.py`: el **Director de Operaciones** accede sin acotamiento por titularidad; el responsable operativo con él; quien no es ninguno de los dos no accede (FR-021, FR-023)
- [X] T011 ⚠️ **Prueba de la regla de versión final** en `dags/tests/test_regla_final_catalogo.py`, **sobre el texto de las consultas**: toda consulta que toca `hecho_accidente`, `hecho_despacho` o una dimensión **fuerza la versión final**; ninguna que toca `hecho_estado_unidad`, `hecho_ping_unidad` o `hecho_evidencia` lo hace. Omitirla devuelve cifras infladas **solo a veces**, y pedirla de más falla con `ILLEGAL_FINAL`
- [X] T012 ⚠️ **Prueba de exclusión de dato sensible** en `dags/tests/test_catalogo_sin_datos_sensibles.py`: ninguna consulta del catálogo nombra una columna de coordenadas, identidad de persona o texto libre (FR-015, FR-016)
- [X] T013 [P] Prueba de que **toda consulta lleva `ORDER BY` explícito** en `dags/tests/test_catalogo_forma.py`: sin él el orden es arbitrario y comparar dos corridas deja de ser posible
- [X] T014 [P] Prueba de que **ninguna consulta usa `SELECT *`** en el mismo fichero: una columna nueva del hecho aparecería sola en un informe sin que nadie lo decidiera

> **Desviación (2026-08-16).** T004 y T011–T014 pedían cuatro ficheros de prueba distintos
> (`test_catalogo_consultas.py`, `test_regla_final_catalogo.py`, `test_catalogo_sin_datos_sensibles.py`,
> `test_catalogo_forma.py`). Se escribieron en **uno solo**, `dags/tests/test_catalogo_consultas.py`:
> las cuatro reglas recorren el mismo catálogo y comparten los mismos ayudantes de análisis del texto
> (`sin_comentarios`, `fuerza_version_final`), y repartirlos habría duplicado esos ayudantes en cuatro
> sitios — con lo que una corrección en uno no llegaría a los otros.
>
> Las **seis reglas se verificaron falsables por mutación**: quitar `FINAL` del hecho, quitarlo de la
> dimensión, pedirlo sobre un hecho de transacción, borrar el `ORDER BY` de salida, nombrar una
> columna sensible y usar `SELECT *`. Cada mutación hace fallar exactamente su prueba.

- [X] T015 [P] Prueba del repositorio en `backend/apps/informes_tacticos/tests/repositories/test_modelo_repository.py`: ejecuta, parametriza y **no escribe nunca**

**Checkpoint**: el sustrato está listo — las tres user stories pueden abordarse.

---

## Phase 3: User Story 1 — Qué se registró y con qué calidad (Priority: P1) 🎯 MVP

**Goal**: los seis informes de OT21 disponibles sobre el modelo, con la completitud **midiendo de
verdad**.

**Independent Test**: pedir los seis informes de un período y comprobar que la suma de cada
distribución es igual al total de casos, sin que exista ninguna tabla por informe.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: al cargar un caso sin severidad, la
completitud **baja del 100 %** (SC-002). Hoy es matemáticamente incapaz de hacerlo.


> **Modelo ampliado y poblado el 2026-08-16** (T048-T054). 35 pruebas nuevas; `dags/` en **234
> verdes** y el backend en **137**, con SC-010 verificado: ninguna cifra de US1 ni de US2 se movio.
>
> Cargado hoy: 51 notas, 3 implicados, 3 elementos de clima, 1 escalada, 1 resultado de atencion y
> **0 calificaciones** — la unica fila de cierre trae `calificacion = 0` en un cierre automatico tras
> retiro forzado, y `0` no esta en la escala. `hecho_evidencia`: 54 filas (3 fotos, 51 notas).
>
> **Un fallo que ocurrio de verdad y no fallo nada.** Anadi las seis fuentes nuevas a `extraer()` y
> olvide anadirlas a `FUENTES` en el modulo de tareas, que es lo que `transform` vuelve a cargar. El
> `datos.get(nombre, [])` de `construir` las sustituyo por listas vacias y **todos los recuentos
> salieron a cero**. Como cero es legitimo en esas columnas, el resultado era indistinguible de un
> origen sin datos: el modelo publico `0` notas donde el origen tenia 51, sin un solo error. Se vio
> comparando con el origen a mano. Anadida `TestLasFuentesDelFlujoYLasDeLaLogica`, que compara la
> tupla con las claves de `extraer()`.
>
> **La unidad de la evidencia se deriva, porque el origen no la trae.** Ni `Dim_EvidenciaFoto` ni
> `Dim_NotaAccidente` tienen unidad: traen `idusuario`, excluido por D6. Se atribuye al **primer
> despacho que llego** —no al confirmado: `Fact_Despacho` no guarda la hora de confirmacion, y ademas
> haber confirmado no es haber ido—. Hoy resuelve 23 de 54; las otras 31 caen en la unidad
> desconocida porque sus casos no tuvieron ninguna llegada, y quedan en el informe en vez de
> descartarse.
>
> **Las notas no tienen instante de sincronizacion**: la columna no existe en la fuente. Su latencia
> es ausente y no se fabrica. Ninguna de las 54 evidencias tiene latencia medible hoy.
>
> **`CREATE TABLE IF NOT EXISTS` no migra**: hizo falta `ensure_columnas_nuevas_hecho_accidente()` con
> `ALTER ... ADD COLUMN IF NOT EXISTS`. Sin ella el DDL habria parecido correcto y las ocho columnas
> no existirian en la instalacion actual.
>
> **`num_notas` disparo el patron `%nota%`** de la prueba de dato sensible. Se declaro la excepcion
> con su razon —contar no es leer— mas una prueba que comprueba el **tipo** de cada excepcion, en vez
> de estrechar el patron, que debe seguir cazando cualquier columna de texto futura.

### Las consultas

- [X] T016 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_distribucion_severidad.sql` — devuelve `periodo, severidad, casos, pct`
- [X] T017 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_distribucion_zona.sql` — devuelve `periodo, condado, casos, pct`
- [X] T018 [US1] ⚠️ Escribir `dags/lib/consultas/emergencias/ot21_completitud_campos_criticos.sql` — **es el que corrige el defecto**: la condición de completitud se evalúa sobre el modelo, donde la ausencia es ausencia, no sobre centinelas
- [X] T019 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_descarte_fusion.sql` usando `fue_descartado` y `es_duplicado`, que **sí distinguen** descartado de fusionado y de cerrado
- [X] T020 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_ranking_ubicaciones.sql` con parámetro `top`, expresando la ubicación **por nombre**
- [X] T021 [P] [US1] Escribir `dags/lib/consultas/emergencias/ot21_impacto_humano.sql` — devuelve heridos, víctimas y fallecidos por condado

### El endpoint que se migra

- [X] T022 [US1] Exponer `GET /api/v1/informes-tacticos/emergencias/completitud-campos-criticos` según `contracts/informes-compuestos-emergencias.openapi.yaml`, en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py` y `urls.py`
- [X] T023 [US1] **Dejar intacto** `CompletitudCamposCriticosView` en `backend/apps/informes_tacticos/views/registro_views.py` y su ruta en `urls.py`. Se retirará cuando se decida qué pasa con los endpoints del módulo sustituido; apagarlo aquí dejaría al tablero sin el informe

### Pruebas

- [X] T024 [US1] ⚠️ **Prueba de que la completitud puede bajar del 100 %** en `dags/tests/test_ot21_completitud.py`: cargar en la partición de prueba un caso **sin severidad** y comprobar que el porcentaje baja. Si sigue en `1.0000`, la consulta heredó el defecto (SC-002)

> **T024 hecha (2026-08-16).** `dags/tests/test_ot21_completitud.py`, 6 pruebas. Escribe casos
> incompletos en la partición `209912` y la descarta al terminar; se verificó que las 4252 filas
> reales quedan intactas.
>
> Cubre los dos campos críticos por separado, el caso al que le faltan los dos (cuenta una vez, no
> dos), el 100 % legítimo —una consulta que devolviera siempre menos de 1 estaría igual de rota, solo
> que dando una alarma permanente— y el período vacío (nulo, **no** cero).
>
> Incluye una prueba que no estaba prevista y resultó necesaria: **una calle no resoluble cuenta como
> incompleto**. La consulta juzga la ubicación por `condado` y no por `idcalle`, pero en todos los
> demás casos del fichero los dos campos van juntos, así que una consulta que mirara `idcalle` pasaba
> igual. Sin ella la distinción que el encabezado del SQL declara no estaba probada.
>
> **Cuatro mutaciones confirmadas**: contar todo como completo (el defecto heredado), mirar `idcalle`
> en vez de `condado`, ignorar la severidad, y devolver `0` en vez de nulo con denominador cero.

- [X] T025 [P] [US1] Prueba de que **ningún caso se pierde al clasificar** en `dags/tests/test_ot21_distribuciones.py`: la suma de todas las categorías es igual al total del período, con lo no resoluble bajo `Desconocido` (SC-007)
- [X] T026 [P] [US1] Prueba de que **descartado, fusionado y cerrado no se confunden** en `dags/tests/test_ot21_descarte_fusion.py`: tres casos, uno de cada, cuentan cada uno en lo suyo
- [X] T027 [P] [US1] Prueba de que el ranking **no devuelve coordenadas** en `dags/tests/test_ot21_ranking.py` (FR-015)
- [X] T028 [US1] ⚠️ **Prueba de contraste** en `backend/apps/informes_tacticos/tests/api/test_contraste_ot21.py`: los **cinco** informes correctos de OT21 dan la misma cifra por el endpoint actual y por la consulta del catálogo. **La completitud queda excluida a propósito**: debe diferir, porque el endpoint actual está mal

**Checkpoint**: US1 entregable. Es el MVP: seis informes sobre el modelo y un defecto de tablero corregido.

---

## Phase 4: User Story 2 — El desempeño del despacho (Priority: P1)

**Goal**: los diez informes de OT22 y OT23, con la capacidad histórica y las posiciones completas.

**Independent Test**: cambiar el proveedor de una unidad, recargar, y comprobar que los informes de
un período anterior devuelven **exactamente las mismas cifras**.

**Criterio medible (ISO 25010 — Corrección funcional)**: la pérdida de señal pasa de considerar el
**16,9 %** de las posiciones a considerar el **100 %** (SC-004).

### Las consultas nuevas y migradas


> **Fase 3 (US1) cerrada el 2026-08-16.** 27 pruebas nuevas: 16 en `dags/` (T024–T027) y 11 en el
> backend (T022, T023, T028). `dags/` queda en **171 verdes** y `apps/informes_tacticos` en **120**.
>
> **Corrección de alcance en T022.** El registro publicaba los **seis** informes OT21. El contrato
> publica **uno**: solo la completitud se migra, porque su endpoint actual está mal. Los otros cinco
> ya los sirve `informes-tacticos-agregados` correctamente y sus consultas existen aquí para
> **contrastarlos**, no para sustituirlos — publicarlos habría creado dos endpoints respondiendo lo
> mismo desde almacenes distintos, que es la situación que T028 vigila. Se separó `CATALOGO` (lo que
> se puede calcular) de `PUBLICADOS` (lo que se sirve), y la ruta perdió el segmento `compuestos/` y
> el `meta` propio que se habían desviado del contrato.
>
> **Defecto encontrado por T027**: en ClickHouse un `LEFT JOIN` sin coincidencia rellena con el
> **valor por defecto del tipo**, no con `NULL`. Una calle fuera del catálogo geográfico volvía como
> cadena vacía y `coalesce` no disparaba: el ranking mostraba una fila con la calle en blanco, que
> parece un fallo de maquetación y significa ubicación sin resolver. Corregido con `nullIf(calle, '')`.
>
> **Sobre T028**: se comparan **totales e invariantes**, no filas. Los dos caminos agrupan por claves
> distintas a propósito —el endpoint actual por calle, el catálogo por condado, porque una calle no es
> una zona—, así que una comparación fila a fila mediría la diferencia de forma y no la de cálculo.
> Verificado falsable alterando una consulta del catálogo.
>
> ⚠️ **Limitación registrada en T028**: `descarte-fusion` solo se puede contrastar **día a día**. El
> endpoint actual publica las tasas **sin denominador**, y sin él las tasas diarias no se recomponen
> en una del período. Es justo lo que el contrato nuevo prohíbe («todo porcentaje viene con su
> denominador»), y este informe es la demostración de por qué esa regla existe.

- [X] T029 [US2] ⚠️ Escribir `dags/lib/consultas/emergencias/ot22_ratio_demanda_capacidad.sql` — `unidades_vigentes` cuenta **versiones de unidad cuya vigencia cubre el período consultado**, no la flota de hoy. Es el defecto de CU-T08
- [X] T030 [US2] Escribir `dags/lib/consultas/emergencias/ot22_primer_intento.sql` — indicador BSC con meta ≥90 %, calculable **solo con grano de intento**: `numero_intento = 1 AND resultado = 'confirmado'`
- [X] T031 [US2] ⚠️ Escribir `dags/lib/consultas/emergencias/ot23_perdida_senal.sql` con parámetro `umbral_seg` — filtra por `segundos_desde_anterior`, ya medido en la carga. **Sin truncar**
- [X] T032 [US2] ⚠️ Escribir `dags/lib/consultas/emergencias/ot23_desviacion_llegada.sql` — la referencia es la **mediana** de despachos comparables en una ventana **anterior** al despacho medido; sin `muestra_minima` llegadas, la referencia sale **ausente** (research D5)

### Las consultas de los que ya funcionan *(para el contraste, sin migrar endpoint)*

- [X] T033 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_asignacion_automatica_vs_manual.sql`
- [X] T034 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_tiempo_reportado_a_confirmado.sql`
- [X] T035 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_tiempo_respuesta_por_severidad.sql`
- [X] T036 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_rechazo_timeout_por_unidad.sql`, separando **rechazado de vencido**: el informe anterior los sumaba
- [X] T037 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot22_carga_por_unidad.sql`
- [X] T038 [P] [US2] Escribir `dags/lib/consultas/emergencias/ot23_abortos_perdidas.sql`, con `abortado` como desenlace propio

### Los endpoints

- [X] T039 [US2] Exponer los cuatro endpoints de esta historia —ratio demanda/capacidad, primer intento, pérdida de señal y desviación de llegada— en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-emergencias.openapi.yaml`
- [X] T040 [US2] Documentar en la respuesta de la desviación que `segundos_referencia` es un **valor derivado del histórico**, y **no** un objetivo ni un SLA (FR-032)

### Pruebas

- [X] T041 [US2] ⚠️ **Prueba de la capacidad histórica** en `dags/tests/test_ot22_ratio.py`: dar de baja una unidad, recargar dimensiones, y comprobar que `unidades_vigentes` de un período **anterior no cambia** (FR-006)
- [X] T042 [US2] ⚠️ **Prueba de que la pérdida de señal no trunca** en `dags/tests/test_ot23_perdida_senal.py`: el número de posiciones consideradas es igual al del origen, y el resultado supera al de la tabla anterior
- [X] T043 [US2] ⚠️ **Prueba de la referencia de llegada** en `dags/tests/test_ot23_desviacion.py`, con cuatro comprobaciones: usa mediana y no promedio; su ventana es anterior al despacho medido; sin muestra suficiente devuelve **ausente y no cero**; y los despachos sin llegada quedan fuera del cálculo (SC-011)
- [X] T044 [P] [US2] Prueba de que **el primer intento se cuenta bien** en `dags/tests/test_ot22_primer_intento.py`: un caso con dos rechazos y una confirmación **no** cuenta como resuelto al primer intento
- [X] T045 [P] [US2] Prueba de que **los cinco desenlaces se distinguen** en `dags/tests/test_ot23_abortos.py`: abortado no es rechazado, ni vencido, ni en curso

> **Fase 4 (US2) cerrada el 2026-08-16.** 10 consultas nuevas (4 publicadas, 6 solo para contraste) y
> 27 pruebas. `dags/` queda en **198 verdes** y `apps/informes_tacticos` en **127**.
>
> **T041 reproduce el defecto de CU-T08.** Da de baja una unidad con efecto **posterior** al mes
> medido y comprueba que ese mes no se mueve. Con `es_vigente = 1` la prueba falla — verificado por
> mutación. El síntoma del defecto es el peor posible: el histórico se reescribe solo, y el mismo
> informe de marzo da cifras distintas en marzo y en agosto sin que en marzo haya pasado nada.
>
> **T043 verifica sus cuatro comprobaciones por mutación**, y una de ellas resultó no comprobar lo que
> decía. «Los despachos sin llegada quedan fuera de la referencia» no era falsable: `median()` ignora
> los nulos de todos modos, así que colarlos no desplaza la referencia. El daño real está en
> `llegadas_comparables` — veinte rechazos y dos llegadas darían una muestra de veintidós, se
> superaría el mínimo, y se publicaría como norma la mediana de **dos** llegadas. La prueba se
> reescribió sobre ese punto y ahora sí falla al mutar la consulta.
>
> **Un fallo de ClickHouse que costó encontrar**: en `ot23_desviacion_llegada`, la columna interna no
> puede llamarse igual que el alias de salida (`segundos_referencia`). Si coincide, el nombre dentro
> de `medianIf(...)` se resuelve al propio alias —que ya es una agregación— y falla con
> `ILLEGAL_AGGREGATION`, un mensaje que no menciona el alias. Antes de dar con ello se probaron
> subconsultas en vez de `WITH`, un nivel extra de `SELECT` y el analizador nuevo; ninguno era la
> causa, y el nivel extra llegó a quedarse en el fichero pareciendo la solución. Se retiró al
> comprobar que sin él la consulta funciona igual.
>
> **Rechazado y vencido se publican por separado** (T036), como pedía la tarea. Sumados, las dos
> desaparecen tras un porcentaje que no dice qué arreglar: un rechazo tiene una persona y un motivo
> detrás, y un vencimiento significa que nadie contestó. Y una unidad con muchos rechazos y ningún
> vencimiento está respondiendo siempre, que es lo contrario de una unidad ausente.

- [X] T046 [US2] Prueba de que **el pasado no se reescribe** en `dags/tests/test_ot22_atribucion.py`: cambiar el proveedor de una unidad y comprobar que las cifras de un período anterior son idénticas (SC-003)
- [X] T047 [US2] ⚠️ **Prueba de contraste** en `backend/apps/informes_tacticos/tests/api/test_contraste_ot22_ot23.py`: los **seis** informes correctos coinciden por ambos caminos. **Ratio y pérdida de señal quedan excluidos**: deben diferir

> **T046 y T047 hechos el 2026-08-16**, después de haber dado la fase por cerrada de más.
>
> **T047 encontró tres cosas que no estaban previstas**, y es exactamente para lo que existe:
>
> 1. **Un error mío**: `ot22_tiempo_respuesta_por_severidad` medía `segundos_transito`, que es
>    *confirmación → llegada*, mientras el endpoint mide *despacho → llegada*. Los ~18 s que la unidad
>    tarda en aceptar quedaban fuera. Corregido.
> 2. **Un sesgo sistemático de +1 s** al intentar el arreglo sumando `segundos_respuesta +
>    segundos_transito`: las dos vienen truncadas a segundos y cada una pierde medio segundo de media.
>    El sesgo es constante y del mismo signo, así que sobrevive a cualquier promedio y no se delata
>    como ruido. Se calcula con **una sola resta**.
> 3. **`rechazo-timeout-por-unidad` está mal, y estaba clasificado como correcto** → decisión
>    pendiente **#34**. Su denominador son transiciones de estado y no intentos de despacho, así que
>    cuanto mejor trabaja una unidad más baja parece su tasa de rechazo; y su tabla se trunca (19 528
>    filas, tope de 10 000). Medido en `LOTE-A2`: 0,0769 frente a 0,2 real.
>
> **`tiempo-reportado-a-confirmado` queda excluido del contraste numérico y declarado.** Los dos
> caminos miden los mismos 3638 casos y arrancan el cronómetro en instantes distintos —el estado
> `REPORTADO` del historial frente al momento del accidente—, y el modelo no guarda hoy el primero.
> Taparlo con una tolerancia del 10 % habría tapado también cualquier error real.

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

- [X] T048 [US3] Añadir a `hecho_accidente` en `dags/lib/ddl.py` las ocho columnas de `data-model.md` §2.1, **todas `Nullable`**: `num_notas`, `num_conductores`, `num_implicados`, `num_elementos_clima`, `num_escaladas_severidad`, `severidad_inicial`, `resultado_atencion` y `calificacion`
- [X] T049 [US3] Poblar los recuentos en `dags/lib/hechos/hecho_accidente.py`: **`0` cuando el caso existe y no tiene ninguno** —cero notas es una medición— y **ausente** en las filas anteriores a la métrica
- [X] T050 [US3] Poblar `severidad_inicial`, `resultado_atencion` y `calificacion` en el mismo módulo: **ausentes cuando no se registraron**. Una calificación `0` sería la peor nota, no «sin calificar»
- [X] T051 [US3] Crear `hecho_evidencia` en `dags/lib/ddl.py` según `data-model.md` §2.2: hecho de transacción, particionado por mes, **sin `idusuario`**
- [X] T052 [US3] Implementar `dags/lib/hechos/hecho_evidencia.py`: fotos y notas en el mismo grano, con `sk_unidad` resuelto por **atribución histórica** y `segundos_hasta_sincronia` calculado al cargar
- [X] T053 [US3] Implementar el flujo en `dags/lib/hecho_evidencia_tasks.py` y `dags/etl/dag_hecho_evidencia.py`, con sensor sobre el flujo de dimensiones, siguiendo el patrón de los cuatro hechos existentes
- [X] T054 [US3] Añadir `modelo_hecho_evidencia` a `dags/tests/test_dag_integrity.py` y `hecho_evidencia` a las listas de tablas de `test_sin_datos_sensibles.py` e `test_informe_sin_flujo_propio.py`

### Las consultas

- [X] T055 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_cobertura_evidencia.sql` — distingue con foto, con nota y con ambas
- [X] T056 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_latencia_sincronizacion.sql` — las evidencias **aún sin sincronizar** cuentan en `pendientes` y su latencia es **ausente**, no infinita
- [X] T057 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_completitud_enriquecimiento.sql`
- [X] T058 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_volumen_evidencia_por_unidad.sql` — **por unidad, sin desglose por persona** (FR-034)
- [X] T059 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot24_escaladas_severidad.sql`
- [X] T060 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_distribucion_resultados.sql` — los casos sin calificar quedan **fuera del promedio** y se cuentan aparte
- [X] T061 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_envejecimiento_cartera.sql` con parámetro `tramos_dias`, sobre casos **sin hora de cierre**
- [X] T062 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_retiros_forzados_por_proveedor.sql`, agrupando por el proveedor **de aquel momento**
- [X] T063 [P] [US3] Escribir `dags/lib/consultas/emergencias/ot25_tiempo_asignado_a_cierre.sql` y `ot25_cierres_forzados.sql` para el contraste

### Los endpoints

- [X] T064 [US3] Exponer los ocho endpoints nuevos de OT24 y OT25 en `backend/apps/informes_tacticos/views/emergencias_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-emergencias.openapi.yaml`

### Pruebas

- [X] T065 [US3] ⚠️ **Prueba de que la cartera de casos abiertos no sale vacía** en `dags/tests/test_ot25_envejecimiento.py`: un caso abierto **no tiene fecha de cierre**; si la tuviera, todos los abiertos aparecerían cerrados y este informe devolvería cero para siempre
- [X] T066 [P] [US3] Prueba de la cobertura de evidencia con **datos sintéticos** en `dags/tests/test_ot24_cobertura.py`: un caso con foto, otro con nota, otro con ambas y otro sin nada se reparten como corresponde
- [X] T067 [P] [US3] Prueba de que una evidencia **sin sincronizar** no cuenta como latencia cero en `dags/tests/test_ot24_latencia.py`
- [X] T068 [P] [US3] Prueba de que una **calificación ausente no es un cero** en `dags/tests/test_ot25_resultados.py`: el promedio la excluye en vez de hundirse
- [X] T069 [P] [US3] Prueba de que **ningún informe de este bloque devuelve identidad de persona** en `dags/tests/test_ot24_sin_identidad.py`, incluido el volumen por unidad (FR-034)
- [X] T070 [US3] ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_ot24.py`: tras añadir `hecho_evidencia` y las ocho columnas, **las cifras de US1 y US2 no cambian** (SC-010)
- [X] T071 [US3] Prueba de contraste de los **dos** informes correctos de OT25 en `backend/apps/informes_tacticos/tests/api/test_contraste_ot25.py`

**Checkpoint**: los 26 informes disponibles sobre el modelo.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T072 [P] Prueba de latencia en `dags/tests/test_latencia_informes_emergencias.py`: los 26 informes responden en tiempo aceptable **con al menos tres meses** de datos, para que el particionado se ejercite (SC-009)
- [X] T073 [P] Prueba de que **un período vacío devuelve cero filas** y no una fila de ceros, en `dags/tests/test_periodo_vacio.py` (FR-019, SC-011)
- [X] T074 [P] Prueba de que **todo porcentaje viene con su denominador** en `dags/tests/test_denominador_visible.py`: un `12,5 %` sobre 8 casos y sobre 8 000 son afirmaciones muy distintas
- [X] T075 Ejecutar `cd backend && python -m pytest -q` y verificar que **los 13 endpoints no migrados siguen intactos** y ninguna suite existente se movió
- [X] T076 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §2.2 (la completitud baja), §2.3 (capacidad de entonces) y §2.7 (los trece coinciden)
- [X] T077 Anotar en `decisiones-pendientes.md` que **quedan dos fuentes para los 13 informes no migrados**, con la prueba de contraste como vigilancia, y que la unificación depende de la decisión #20
- [X] T078 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar el estado de los 26 informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` y **corregir allí el reparto simples/compuestos de Emergencias**, que hoy dice 14/25 cuando las filas dan 12/26 + 1

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
