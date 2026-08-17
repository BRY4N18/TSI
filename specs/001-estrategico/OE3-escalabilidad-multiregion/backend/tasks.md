# Tasks: OE3 — Escalabilidad Multi-Región sin Degradación

**Input**: Design documents from `specs/001-estrategico/OE3-escalabilidad-multiregion/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80 % en servicios, y este
módulo publica **las dos primeras metas semaforizables de la capa estratégica**: una cifra equivocada
aquí no da un error, da un verde o un rojo que alguien se cree.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US4 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Publica 7 de los 14 del catálogo, y declara los otros 7.** Los bloqueados también tienen tareas
—verificar que devuelven `404`, nombrar su prerrequisito, corregir el catálogo—, porque **declarar
bien un hueco es entregable**: es lo que evita que alguien lo rellene con ceros más adelante.

**Es el primer módulo que semaforiza.** `latencia-asignacion` y `tasa-error-registro` devuelven un
`cumple` booleano. Los dos cumplen hoy.

**No crea app nueva.** Se añade a `informes_estrategicos`, que creó OE6. Este módulo es la primera
prueba de que poner las piezas transversales en la raíz de esa app fue correcto.

### Cuatro cosas que este módulo tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Copiar de OE6 la prueba «ningún `cumple` booleano»** | Haría fallar exactamente los dos informes que este módulo aporta de nuevo |
| **Publicar E3-02 con la meta de ≤100 ms** | El p95 real es 106 s. Daría un rojo 1 060× falso en el único informe que cumple |
| **Unir con `dim_region` o agrupar por región** | Duplica cada caso sin fallar (#38) |
| **Publicar cualquiera de los 7 bloqueados, ni siquiera vacío** | E3-04 compararía contra 1970 y daría veinte mil días en rojo `[NORMATIVO]` |

---

## Phase 1: Setup — el sitio y el prerrequisito

**Purpose**: comprobar que el armazón existe y crear el catálogo de OE3.

- [X] T001 ⚠️ Verificar que el **armazón de OE6 está implementado**: `periodo_estrategico.py`, `objetivo.py`, `envelope.py`, `permissions.py` y `core/repositories/informes_estrategicos/`. **Si no lo está, las fases 1 y 2 de `specs/001-estrategico/OE6-respuesta-y-vidas/backend/tasks.md` son prerrequisito bloqueante de este módulo** y hay que hacerlas antes de T002
- [X] T002 Verificar la línea base del almacén siguiendo [`quickstart.md`](quickstart.md) §1: **13 tablas** antes de este módulo, 4 252 casos, 3 638 con primera asignación, p95 de 106 s, 4 314 intentos. Anotar las cifras medidas en el propio `quickstart.md` si difieren
- [X] T003 Crear `dags/lib/consultas/estrategicos/oe3/` con un `README.md` que fije las convenciones: un fichero por informe, nombre `e3_NN_<informe>.sql`, encabezado con el porqué de cada decisión no obvia
- [X] T004 [P] Prueba en `dags/tests/test_catalogo_estrategicos.py` de que el cargador resuelve `departamento="estrategicos/oe3"`
- [X] T005 [P] Registrar las rutas de OE3 en `backend/apps/informes_estrategicos/urls.py` bajo `/api/v1/informes-estrategicos/oe3/`

---

## Phase 2: Foundational — la dimensión nueva y el acceso repartido

**Purpose**: la única ampliación del modelo, y el primer permiso no uniforme de la capa.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa. **US2 depende
además de la dimensión** (T006–T012).

### La dimensión `dim_condado_vecino` — única ampliación del modelo

- [X] T006 Declarar la tabla `dim_condado_vecino` según [`data-model.md`](data-model.md) §2: `ReplacingMergeTree(version)`, `ORDER BY (idcondado, idcondadovecino)`, **sin versionar por atributo** — la adyacencia física no cambia; si cambiara, sería otro mapa
- [X] T007 Implementar `dags/lib/dimensiones/dim_condado_vecino.py`: extrae `Dim_CondadoVecino` del origen filtrando `activo = true`, y **resuelve los nombres contra `Dim_Condado`** para no publicar identificadores internos
- [X] T008 Añadir su **fila desconocida** en `dags/lib/dimensiones/desconocido.py`. Sin ella, los condados que no resuelvan vecino **desaparecen en la primera unión** en vez de aparecer sin respaldo — que es la respuesta que E3-08 existe para dar
- [X] T009 Añadir la tarea de carga al DAG de dimensiones, **declarando la dependencia con un sensor y no con el horario**, según el §4.bis del contrato de esquema
- [X] T010 [P] ⚠️ Prueba de **crecimiento aditivo** en `dags/tests/test_dim_condado_vecino.py`: las cifras de `hecho_accidente` y `hecho_despacho` **no se mueven** tras cargar la dimensión. Es la garantía que el §4.bis exige a toda ampliación
- [X] T011 [P] Prueba en el mismo fichero de que la dimensión cargada es **simétrica** (2 filas en la línea base: 1↔2) y de que un condado sin vecino resuelve a la fila desconocida
- [X] T012 Documentar la dimensión en `specs/002-tactico/modelo-analitico/contracts/esquema-analitico.md` §2. **El §4.bis lo obliga**: una dimensión que no está en el contrato de esquema es una tabla que alguien creó

### El acceso repartido — primer permiso no uniforme de la capa

- [X] T013 ⚠️ Ampliar `backend/apps/informes_estrategicos/permissions.py` con conjuntos **por informe**, no por módulo: `DirectorOperaciones` en los cuatro de despacho y registro; `DirectorExpansion` **y** `DirectorOperaciones` en los tres de capacidad; `Gerente` en los siete. Usar las constantes de `backend/core/auth/roles_tacticos.py`
- [X] T014 ⚠️ Prueba de **exclusión** en `.../tests/api/test_permisos_oe3.py`: `DirectorExpansion` recibe **`403` en `latencia-asignacion`** y `200` en `ratio-demanda-capacidad`. Comprobar solo quién entra dejaría pasar un permiso de módulo, que concede de más justo donde el SRS advierte que la autoridad «no debe leerse como una cadena de mando única»

### El armazón de OE3

- [X] T015 ⚠️ Verificar que `objetivo.py` de OE6 resuelve correctamente un objetivo **`NORMATIVO` con `cumple` booleano**. OE6 nunca ejerció ese camino —todas sus metas son `[CALIBRAR]`—, así que es código escrito y no probado en producción
- [X] T016 Implementar `backend/apps/informes_estrategicos/services/oe3_service.py` con el patrón `CATALOGO` (informe → fichero) y `PUBLICADOS`. **Los siete bloqueados no entran en `PUBLICADOS`**, y el registro explícito es lo que impide que un fichero suelto en el disco publique un endpoint
- [X] T017 Implementar `backend/apps/informes_estrategicos/views/oe3_views.py`, reutilizando la vista base de OE6

### Pruebas transversales del catálogo

- [X] T018 [P] ⚠️ Prueba de la **regla de versión final** en `dags/tests/test_catalogo_estrategicos.py`: toda consulta de `oe3` que toca `hecho_accidente`, `hecho_despacho`, `dim_unidad`, `dim_geografia` o `dim_condado_vecino` la fuerza; ninguna que toca `hecho_estado_unidad` o `hecho_ping_unidad` lo hace — pedirlo ahí falla con `ILLEGAL_FINAL`
- [X] T019 [P] ⚠️ Prueba en el mismo fichero de que **ninguna consulta de `oe3` nombra `dim_region`** ni una columna de región
- [X] T020 [P] Prueba en el mismo fichero de que ninguna usa `SELECT *`, todas llevan `ORDER BY` explícito, todas filtran por `fecha`, y ninguna nombra columna sensible

**Checkpoint**: el modelo tiene 14 tablas, el acceso repartido funciona y las cuatro historias pueden abordarse.

---

## Phase 3: User Story 1 — El rendimiento del despacho no se degrada (Priority: P1) 🎯 MVP

**Goal**: los cuatro informes con metas medibles, y **las dos primeras semaforizaciones de la capa
estratégica**.

**Independent Test**: pedir `latencia-asignacion` de un trimestre con `comparacion=yoy` y comprobar
que devuelve p95, la meta de 2 minutos, un `cumple` **booleano** y las dos ventanas declaradas.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: el `objetivo.valor` de E3-02 es **2 minutos**
y no 100 ms (SC-002b). Con la meta del catálogo, el informe estaría 1 060 veces por encima.

- [X] T021 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe3/e3_02_latencia_asignacion.sql`: mediana y p95 de `hora_primera_asignacion − fechahora_accidente`, con `casos_asignados`, `excluidos_sin_asignacion` y `sobre_umbral`. ⚠️ **No usar `segundos_respuesta` del despacho**: ese mide oferta→confirmación (p95 28 s), no el proceso completo que RNF-DES-001 acota
- [X] T022 [US1] En la misma consulta, excluir descartados y fusionados, y **declarar aparte los casos sin asignación**. Contarlos como cero haría instantáneos precisamente los casos que nadie atendió
- [X] T023 [US1] En la misma consulta, devolver el p95 **ausente** bajo `muestra_minima`
- [X] T024 [P] [US1] Escribir `.../e3_03_evolucion_latencia.sql`: serie del p95 sobre ventanas amplias, para detectar **degradación gradual**. ⚠️ Es la consulta donde el filtrado por partición más pesa: sin él, una ventana anual recorre el histórico entero
- [X] T025 [P] [US1] Escribir `.../e3_10_tasa_error_registro.sql` como complemento de la completitud, midiendo la **ausencia real del modelo**, y devolviendo la lista `campos_comprobados` en cada fila
- [X] T026 [P] [US1] Escribir `.../e3_11_primer_intento.sql` con **grano de intento**: `numero_intento = 1 AND resultado = 'confirmado'`. Con grano de caso los intentos fallidos desaparecen y el indicador sube solo
- [X] T027 [US1] Registrar los cuatro en `CATALOGO` y `PUBLICADOS` de `oe3_service.py`, con sus parámetros (`muestra_minima`, `por_condado`)
- [X] T028 [US1] Exponer los cuatro endpoints según [`contracts/informes-estrategicos-oe3.openapi.yaml`](contracts/informes-estrategicos-oe3.openapi.yaml)
- [X] T029 [US1] ⚠️ Declarar el objetivo de **E3-02**: `valor: 2`, `unidad: "min"`, `tipo: "NORMATIVO"`, `cumple` booleano — **y emitir `meta.alcance`** diciendo que mide el proceso operativo y no la latencia técnica del algoritmo (FR-OE3-008b)
- [X] T030 [US1] Declarar el objetivo de **E3-10** (`1 %`, `NORMATIVO`, booleano) y el de **E3-11** (`90 %`, `CALIBRAR`, **`null`**)
- [X] T031 [P] [US1] Prueba de contrato de los cuatro en `.../tests/api/test_oe3_us1_contract.py`
- [X] T032 [P] [US1] ⚠️ Prueba en `.../tests/api/test_us1_meta_correcta.py`: el `objetivo.valor` de E3-02 es **2 minutos**, la unidad es `min`, y `meta.alcance` está presente. Falsable por mutación: poner 100 ms debe hacerla fallar
- [X] T033 [P] [US1] ⚠️ Prueba en `.../tests/api/test_us1_semaforo.py`: `cumple` es **booleano** en E3-02 y E3-10, y **`null`** en E3-11. **No copiar la prueba de OE6**, que exige lo contrario
- [X] T034 [P] [US1] Prueba en `.../tests/api/test_us1_sin_asignacion.py`: los casos sin asignación se declaran y **no entran en la mediana**. El síntoma del fallo sería una latencia que **mejora cuando empeora la atención**
- [X] T035 [P] [US1] Prueba en `.../tests/api/test_us1_campos_comprobados.py`: E3-10 **no responde `200` sin `campos_comprobados`**. Su tasa es 0 % y un indicador que nunca se mueve, sin la lista, se lee como «el registro es perfecto»
- [X] T036 [P] [US1] Prueba de comparación en `.../tests/api/test_us1_comparacion.py`: `mom` da dos ventanas de igual longitud; `yoy` devuelve `ventana_anterior: null` con `motivo_ausencia`, **no un `400`**
- [X] T037 [US1] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_oe3_us1.py`: `primer-intento` coincide con `/informes-tacticos/emergencias/primer-intento`, y `tasa-error-registro` es el complemento exacto de `completitud-campos-criticos`, con la misma agrupación y período
- [X] T038 [US1] Prueba de que los cuatro no devuelven coordenadas ni identidad, **con `DirectorOperaciones`** y no solo con un rol acotado

**Checkpoint**: US1 entregable. **La capa estratégica tiene sus dos primeras metas semaforizadas**, y
las dos se cumplen.

---

## Phase 4: User Story 2 — Detectar la tensión antes de que degrade (Priority: P2)

**Goal**: los tres informes de capacidad, incluido el que la dimensión nueva desbloquea.

**Independent Test**: pedir el ratio demanda/capacidad de un trimestre pasado y comprobar que la
capacidad es la **vigente entonces**, no la flota de hoy.

**Criterio medible (ISO 25010 — Safety)**: un condado con demanda y ninguna unidad vigente se declara
`sin_capacidad`, y sus vecinos sin unidad disponible **no cuentan como respaldo** (SC-005). Son las
zonas donde una emergencia no tiene quién la atienda.

- [X] T039 [P] [US2] Escribir `.../e3_07_ratio_demanda_capacidad.sql`, partiendo de `ot22_ratio_demanda_capacidad.sql`: casos frente a **versiones de unidad vigentes en el período**, por condado
- [X] T040 [US2] ⚠️ En la misma consulta, usar la lectura **histórica** de `dim_unidad` (Regla 5). Filtrar por `es_vigente = 1` calcularía un ratio de hace tres meses contra la flota de hoy — el defecto que la dimensión versionada existe para corregir
- [X] T041 [US2] En la misma consulta, declarar `sin_capacidad: true` y `ratio: null` para un condado con demanda y cero unidades vigentes. **No un infinito, ni un cero, ni un `500`**
- [X] T042 [US2] Emitir `meta.alcance` en E3-07 declarando **desde cuándo la atribución es fiable** (Regla 6): las versiones de unidad arrancan en la primera carga del modelo, porque el origen no historiza el cambio de proveedor
- [X] T043 [P] [US2] Escribir `.../e3_08_cobertura_de_respaldo.sql`: por condado, cuántos vecinos tienen al menos una unidad **disponible** — último estado de `hecho_estado_unidad`, **no** la mera existencia de la unidad. ⚠️ `hecho_estado_unidad` es de transacción: **prohibido forzar la versión final**
- [X] T044 [P] [US2] Escribir `.../e3_13_perdida_de_senal.sql`, partiendo de `ot23_perdida_senal.sql`, con granularidad. ⚠️ Debe analizar **todas** las posiciones: el flujo legado veía 10 000 de 59 045
- [X] T045 [US2] Registrar los tres en `CATALOGO` y `PUBLICADOS`, con el parámetro `umbral_seg` de E3-13, y exponer sus endpoints
- [X] T046 [P] [US2] Prueba de contrato de los tres en `.../tests/api/test_oe3_us2_contract.py`
- [X] T047 [P] [US2] ⚠️ Prueba en `.../tests/api/test_us2_capacidad_del_periodo.py`: dos períodos con distinta flota devuelven **distinta capacidad**. Si todos devuelven el mismo número, se está usando la flota actual
- [X] T048 [P] [US2] Prueba en `.../tests/api/test_us2_sin_capacidad.py`: un condado con casos y cero unidades vigentes devuelve `sin_capacidad: true` y `ratio: null`
- [X] T049 [P] [US2] ⚠️ Prueba en `.../tests/api/test_us2_respaldo_disponibilidad.py`: un vecino con unidades dadas de alta pero **todas ocupadas o fuera de servicio** devuelve `vecinos_con_unidad_disponible: 0`. Es el error que Red Operativa documentó como el más caro de su departamento
- [X] T050 [P] [US2] Prueba en `.../tests/api/test_us2_senal_completa.py`: E3-13 analiza todas las posiciones — del orden de 3 942 huecos, no los 714 del flujo legado
- [X] T051 [US2] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_oe3_us2.py`: `ratio-demanda-capacidad` y `perdida-de-senal` coinciden con sus equivalentes tácticos con la misma agrupación y período
- [X] T052 [US2] Prueba de permisos específica: `DirectorExpansion` accede a los tres de esta historia

**Checkpoint**: US2 entregable. El modelo tiene 14 tablas y **E3-08 se entrega gracias a la única
ampliación del módulo**.

---

## Phase 5: User Story 3 — Medir la maduración regional (Priority: P3) ⛔ BLOQUEADA

**Goal**: dejar los tres informes **correctamente declarados como no construibles**, con su
prerrequisito común nombrado, para que nadie los rellene con ceros más adelante.

**Independent Test**: pedir las tres rutas y obtener `404`; y comprobar que el catálogo y la
trazabilidad nombran el prerrequisito.

> **No hay consultas que escribir.** Los entregables de esta historia son documentales y de
> verificación — y no son menores: **es lo que impide que E3-04 se publique comparando contra 1970**.

- [X] T053 [US3] Verificar que `tiempo-puesta-operacion`, `curva-maduracion` y `cohorte-region` **no existen como ruta** y devuelven `404`, en `.../tests/api/test_oe3_bloqueados.py`
- [X] T054 [US3] Documentar en `traceability.md` que los tres comparten **un único prerrequisito**: historizar el estado de región en el sistema operativo. Se desbloquean a la vez, no uno a uno
- [X] T055 [US3] Actualizar `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §3: E3-04, E3-05 y E3-06 pasan a **⛔** con su prerrequisito, igual que el catálogo ya hace con el CAC y el NPS
- [X] T056 [US3] Ampliar `decisiones-pendientes.md` #38 con la **historización del estado de región**: hoy solo recoge la relación región↔condado, y la misma tabla puente resolvería las dos cosas. Anotar que E3-04 daría **más de veinte mil días** si se publicara

---

## Phase 6: User Story 4 — Lo que el sistema no registra ni produce (Priority: P4) ⛔

**Goal**: declarar los cuatro, y **registrar el hallazgo de E3-12**, que es nuevo y no estaba en
ninguna parte.

**Independent Test**: las cuatro rutas devuelven `404`, y `decisiones-pendientes.md` recoge el
hallazgo de E3-12 con su medición.

- [X] T057 [US4] Verificar que `reasignacion-manual`, `uptime-por-region`, `margen-operativo` y `cobertura-pruebas` devuelven `404`, en `.../tests/api/test_oe3_bloqueados.py`
- [X] T058 [US4] ⚠️ Registrar en `decisiones-pendientes.md` una decisión nueva: **E3-12 no es medible porque el sistema no instrumenta la falla del algoritmo**. Incluir la medición —**1 082 de 1 083 despachos manuales sin intento automático previo**, 918 de ellos primer intento— y la salida: registrar el evento «asignación automática sin candidatas» con su instante
- [X] T059 [US4] Actualizar el catálogo §3: **E3-12 pasa de ⚪ a ⛔**, y se corrige **la meta de E3-02** separando la latencia técnica del tiempo operativo
- [X] T060 [US4] Anotar en el catálogo que **E3-14 es candidata a salir del tablero de negocio**: mide el proceso de desarrollo, no la operación del servicio, y ninguna decisión de dirección se toma con ella

**Checkpoint**: los siete bloqueados están declarados, con prerrequisito, y el catálogo dice la verdad.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T061 [P] Prueba de conformidad con el contrato en `.../tests/api/test_openapi_conforme_oe3.py`: los siete publicados están en el YAML, **los siete bloqueados no**, y el YAML no declara ningún campo sensible
- [X] T062 [P] ⚠️ Prueba transversal en `.../tests/api/test_oe3_semaforo_correcto.py`: exactamente **dos** informes devuelven `cumple` booleano. Ni uno más —sería una meta inventada— ni uno menos —se perdió la semaforización que este módulo aporta
- [X] T063 [P] Prueba transversal de denominadores: ningún endpoint devuelve un porcentaje sin el total sobre el que se calculó
- [X] T064 [P] Prueba transversal de período vacío: los siete devuelven `data: []` con `cobertura: "completa"`, **nunca una fila de ceros**
- [X] T065 [P] Prueba transversal de que **ninguna respuesta acepta ni emite `por_region`**
- [X] T066 Medir la cobertura de la parte OE3 de `backend/apps/informes_estrategicos/` y dejarla **≥80 %** en servicios
- [X] T067 Recorrer entero [`quickstart.md`](quickstart.md) §2 —las 14 comprobaciones— contra el stack levantado, **anotando en el fichero las cifras medidas** y no las previstas
- [X] T068 Escribir `traceability.md`: FR-OE3-nnn → tarea → prueba, y los criterios de aceptación de las cuatro historias, incluidos los de las dos bloqueadas
- [X] T069 [P] Anotar en `.specify/docs/changelog.md` las **dos correcciones fuera de ciclo** que este plan produjo: la meta de E3-02 (el catálogo mezclaba latencia técnica con tiempo operativo, factor 1 060) y la reclasificación de E3-12, con su medición
- [X] T070 [P] Actualizar `specs/001-estrategico/contrato-informes-estrategicos.md` §10 con el estado de OE3 tras la implementación
- [X] T071 ⚠️ Reconstruir y recrear los contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend`, y verificar con `docker ps --filter name=accidentes-` que ambos están `Up`. **El frontend se sirve desde imagen nginx: no hay recarga en caliente**
- [X] T072 Verificar contra la app real, con usuarios de rol `DirectorOperaciones` y `DirectorExpansion`, que los siete responden según la matriz del quickstart §2.10 — **incluido el `403` de Expansión en los de despacho**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: depende de que **el armazón de OE6 exista** (T001). Es la única dependencia
  entre módulos de la capa
- **Foundational (Phase 2)**: depende de Setup. **Bloquea las cuatro historias**
- **US1 (Phase 3)**: depende de Foundational
- **US2 (Phase 4)**: depende de Foundational **y en particular de la dimensión** (T006–T012). Es la
  única historia con una dependencia dura dentro de la fase 2
- **US3 y US4 (Phases 5–6)**: solo dependen de que exista el servicio, para comprobar los `404`.
  **Pueden hacerse en cualquier momento tras la fase 2**, incluso antes que US1
- **Polish (Phase 7)**: depende de las historias que se quieran entregar

### User Story Dependencies

- **US1 (P1)**: ninguna. Es el MVP
- **US2 (P2)**: ninguna respecto de US1. Depende de la dimensión, que es de la fase 2
- **US3 (P3)** y **US4 (P4)**: ninguna. Son documentales y **baratas**; adelantarlas tiene una ventaja
  real: dejan el catálogo corregido antes de que alguien lo lea y construya sobre él

### Parallel Opportunities

- **Fase 2**: T010, T011, T018, T019 y T020 en paralelo. T006–T009 son la misma cadena de carga
- **Fase 3**: T021, T024, T025 y T026 son ficheros distintos; T031–T036 en paralelo tras el endpoint
- **Fase 4**: T039, T043 y T044 en paralelo — tres consultas independientes
- **Fases 5 y 6**: casi todo en paralelo, y en paralelo con las fases 3 y 4
- **Fase 7**: T061–T065 y T069–T070 en paralelo

---

## Parallel Example: Phase 3

```bash
# Las cuatro consultas de US1, ficheros distintos y sin dependencias entre sí:
Task: "e3_02_latencia_asignacion.sql — mediana y p95 registro→asignación"
Task: "e3_03_evolucion_latencia.sql — serie de p95 sobre ventanas amplias"
Task: "e3_10_tasa_error_registro.sql — con la lista de campos comprobados"
Task: "e3_11_primer_intento.sql — grano de intento, ordinal 1 confirmado"
```

---

## Implementation Strategy

### MVP primero (solo US1)

1. Fase 1: Setup — **con T001 como puerta**: sin el armazón de OE6 no se empieza
2. Fase 2: Foundational
3. Fase 3: US1
4. **PARAR Y VALIDAR**: comprobaciones 2.2, 2.3, 2.4, 2.11 y 2.12 del quickstart
5. Entregar

**El MVP tiene valor por sí solo**: la capa estratégica pasa de no poder semaforizar nada a tener dos
metas `[NORMATIVO]` verificadas, y las dos se cumplen.

### Atajo recomendado

**Hacer las fases 5 y 6 justo después de la 2**, antes que US1. Son 8 tareas, casi todas documentales,
y dejan el catálogo corregido y los `404` garantizados **antes** de que nadie construya encima de un
catálogo que hoy anuncia catorce informes de los que siete no pueden existir.

### Entrega incremental

1. Setup + Foundational → 14 tablas y acceso repartido
2. US3 + US4 → el catálogo dice la verdad *(barato, ver atajo)*
3. US1 → **MVP**, las dos primeras semaforizaciones
4. US2 → la tensión de capacidad, con el informe que la dimensión desbloquea

### Si hay varias personas

Tras la fase 2, US1 y US2 pueden repartirse. **La fase 2 conviene que la haga una sola persona**: la
dimensión y el permiso repartido son las dos piezas que el resto asume correctas.

---

## Notes

- `[P]` = ficheros distintos, sin dependencias pendientes
- Cada consulta lleva **en su encabezado el porqué de sus decisiones no obvias**, como las 26 tácticas
- **Solo una tarea crea una tabla** (T006), y es una **dimensión compartida**, no una tabla de informe.
  Cualquier otra que lo proponga es señal de que se entendió mal el alcance
- Confirmar que las pruebas fallan antes de implementar, y **verificarlas falsables por mutación** en
  las marcadas con ⚠️
- ⚠️ **La prueba de OE6 «ningún `cumple` booleano» no se copia aquí.** T062 es su equivalente y exige
  lo contrario: exactamente dos booleanos
- Parar en cualquier checkpoint para validar la historia por separado
