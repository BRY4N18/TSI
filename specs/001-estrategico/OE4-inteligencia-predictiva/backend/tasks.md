# Tasks: OE4 — Registro Histórico e Inteligencia Predictiva

**Input**: Design documents from `specs/001-estrategico/OE4-inteligencia-predictiva/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80 % en servicios, y este
módulo produce **datos que se venden a terceros**: un comprador no puede distinguir un cero real de
un cero por falta de registro, así que la prueba tiene que hacerlo por él.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US4 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Publica 9 de los 15 del catálogo**, retira la última tabla legada del dominio y **añade dos columnas
a `hecho_accidente`** que completan los dos informes que se venden.

**Es el único módulo cuyo producto sale de la empresa.** E4-05, E4-06, E4-12 y E4-13 los compra una
aseguradora o un municipio. Eso sube el listón de la exclusión de dato sensible: una coordenada aquí
no es una fuga interna, es **una fuga con destinatario comercial**.

**Y no semaforiza.** Todas las metas de OE4 son `[CALIBRAR]`.

### Cuatro cosas que este módulo tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Rellenar con `0` las métricas nuevas en filas antiguas** | Hunde el promedio y presenta «no lo medíamos» como «no hubo afectación», en un informe que se vende |
| **Publicar E4-14** | `cargado_en` daría ~1 971 horas: la antigüedad del accidente disfrazada de latencia de ingesta |
| **Cambiar la fórmula del índice al migrarlo** | Hay 182 días calculados con ella; un salto en la serie sería inatribuible |
| **Devolver un `cumple` booleano** | Todas las metas son `[CALIBRAR]`. **Aquí sí aplica la prueba de OE6**, al contrario que en OE3 |

---

## Phase 1: Setup — el sitio y el prerrequisito

- [ ] T001 ⚠️ Verificar que el **armazón de `informes_estrategicos` está implementado** (`periodo_estrategico.py`, `objetivo.py`, `envelope.py`, `permissions.py`, `core/repositories/informes_estrategicos/`). **Si no lo está, las fases 1 y 2 de `specs/001-estrategico/OE6-respuesta-y-vidas/backend/tasks.md` son prerrequisito bloqueante**
- [ ] T002 Verificar la línea base siguiendo [`quickstart.md`](quickstart.md) §1: 4 252 casos, **2 con foto y 3 fotografías**, 51 con nota, **3 con clima**, 1 `resultado_atencion`, **0 `calificacion`**, 182 filas en `indice_calidad_historico`. Anotar las cifras medidas si difieren
- [ ] T003 Crear `dags/lib/consultas/estrategicos/oe4/` con un `README.md` que fije las convenciones: `e4_NN_<informe>.sql`, encabezado con el porqué de cada decisión no obvia
- [ ] T004 [P] Prueba en `dags/tests/test_catalogo_estrategicos.py` de que el cargador resuelve `departamento="estrategicos/oe4"`
- [ ] T005 [P] Registrar las rutas de OE4 en `backend/apps/informes_estrategicos/urls.py` bajo `/api/v1/informes-estrategicos/oe4/`

---

## Phase 2: Foundational — las dos columnas nuevas y el acceso

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa. **US2 depende en
particular de las dos columnas** (T006–T014).

### Las dos ampliaciones de `hecho_accidente`

- [ ] T006 Añadir las dos columnas al esquema según [`data-model.md`](data-model.md) §2: `ALTER TABLE hecho_accidente ADD COLUMN distancia_millas Nullable(Float64)` y `ADD COLUMN condicion_clima Nullable(String)`. ⚠️ **`Nullable` y sin valor por defecto**, según el §4.bis
- [ ] T007 Extender `dags/lib/hechos/hecho_accidente.py` para extraer `Fact_Accidente.distanciamillas`
- [ ] T008 Extender el mismo módulo para resolver la condición climática: `Dim_ElementoClimaticosAccidente` → `Dim_EstadosClimas.condicionclima`
- [ ] T009 ⚠️ **Añadir las dos fuentes nuevas también a `FUENTES`**, no solo a `extraer()`. Es la trampa documentada del changelog de este mismo flujo: `datos.get(nombre, [])` sustituye la fuente olvidada por una lista vacía y **todos los recuentos salen a cero sin un solo error**. Ocurrió de verdad con las seis fuentes de OT24
- [ ] T010 [P] ⚠️ Prueba en `dags/tests/test_metricas_oe4.py` de que **`distancia_millas` tiene ≈4 200 valores no nulos** y `condicion_clima` **exactamente 3**. Comprobar que la columna existe no basta: es justo lo que pasaría con el fallo de T009
- [ ] T011 [P] ⚠️ Prueba en el mismo fichero de que **ningún caso tiene más de un elemento climático** (`max(num_elementos_clima) = 1`). Si cambia, la columna desnormalizada **elegiría uno en silencio** y hay que rediseñar con un puente
- [ ] T012 [P] Prueba de **crecimiento aditivo**: casos, descartados, duplicados y los cuatro hitos de `hecho_accidente` **no se mueven** tras la ampliación
- [ ] T013 [P] Prueba de que las filas cargadas antes de la ampliación tienen las métricas **ausentes, no cero**, y de que los promedios las excluyen
- [ ] T014 Documentar las dos columnas en `specs/002-tactico/modelo-analitico/contracts/esquema-analitico.md`. **El §4.bis lo obliga**

### El acceso y el armazón de OE4

- [ ] T015 Ampliar `backend/apps/informes_estrategicos/permissions.py` con los conjuntos de OE4: `DirectorDatos` y `Gerente` en los nueve; **`DirectorOperaciones` solo en los del expediente** —E4-01 a E4-04, E4-12, E4-13— según `acceso-estrategico.md` §4.4
- [ ] T016 ⚠️ Prueba de **exclusión** en `.../tests/api/test_permisos_oe4.py`: `DirectorOperaciones` recibe **`403` en `concentracion-siniestralidad`** y `200` en `completitud-campos-criticos`
- [ ] T017 Implementar `backend/apps/informes_estrategicos/services/oe4_service.py` con `CATALOGO` y `PUBLICADOS`. **Los seis bloqueados no entran en `PUBLICADOS`**
- [ ] T018 Implementar `backend/apps/informes_estrategicos/views/oe4_views.py`, reutilizando la vista base

### Pruebas transversales del catálogo

- [ ] T019 [P] ⚠️ Prueba de la **regla de versión final** en `dags/tests/test_catalogo_estrategicos.py`: toda consulta de `oe4` que toca `hecho_accidente`, `dim_geografia` o `dim_severidad` la fuerza; **ninguna que toca `hecho_evidencia` lo hace** — pedirlo ahí falla con `ILLEGAL_FINAL`
- [ ] T020 [P] ⚠️ Prueba de que **ninguna consulta de `oe4` nombra una columna de coordenadas ni de identidad de persona**. Es la prueba más importante del módulo: sus informes se venden
- [ ] T021 [P] Prueba de que ninguna usa `SELECT *`, todas llevan `ORDER BY` explícito y todas filtran por `fecha`
- [ ] T022 [P] Prueba de que **ninguna consulta nombra `dim_region`** (#38)

**Checkpoint**: las dos columnas están cargadas con sus volúmenes reales y el acceso repartido funciona.

---

## Phase 3: User Story 1 — Saber si el histórico es fiable (Priority: P1) 🎯 MVP

**Goal**: los cuatro informes de calidad, y **la retirada de la última tabla legada del dominio**.

**Independent Test**: pedir el índice de calidad de un trimestre y comprobar que sus cuatro
componentes son consultables por separado, que reproducen la fórmula del legado, y que
`indice_calidad_historico` no ha hecho falta.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: el índice se puede descomponer en sus cuatro
partes desde la propia respuesta (SC-002), cosa que la tabla legada no permite.

- [ ] T023 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe4/e4_01_indice_calidad_historico.sql` con la fórmula descifrada: `(completitud + (1−descarte) + (1−fusión) + cobertura_evidencia) / 4`, **devolviendo las cuatro componentes además del índice**
- [ ] T024 [US1] En la misma consulta, definir la cobertura de evidencia **explícitamente**: `con_foto`, `con_nota` y `con_ambas` por separado. Es lo que el legado no permite saber, y la causa de que sus cifras no se puedan reproducir
- [ ] T025 [US1] Emitir `meta.alcance` en E4-01 declarando **la fórmula y la definición de evidencia**. Un índice consolidado cuya composición no se publica no es verificable por quien lo lee
- [ ] T026 [P] [US1] Escribir `.../e4_02_completitud_campos_criticos.sql`, midiendo la **ausencia real del modelo** y devolviendo `campos_comprobados` en cada fila
- [ ] T027 [P] [US1] Escribir `.../e4_03_campos_mas_ausentes.sql`. ⚠️ **Incluir todos los campos críticos, también los que no fallan nunca, con cero**: un campo que sale de la lista se confunde con un campo que nadie revisó
- [ ] T028 [P] [US1] Escribir `.../e4_04_calidad_por_origen.sql` usando `categoria_nota` de `hecho_evidencia` para distinguir captura central de enriquecimiento en campo. ⚠️ **Sin desglose por persona**: compara orígenes de captura, no rendimiento individual
- [ ] T029 [US1] Registrar los cuatro en `CATALOGO` y `PUBLICADOS`, y exponer sus endpoints según [`contracts/informes-estrategicos-oe4.openapi.yaml`](contracts/informes-estrategicos-oe4.openapi.yaml)
- [ ] T030 [US1] Declarar el objetivo de **E4-02**: `97 %`, `CALIBRAR`, **`cumple: null`**
- [ ] T031 [P] [US1] Prueba de contrato de los cuatro en `.../tests/api/test_oe4_us1_contract.py`
- [ ] T032 [P] [US1] ⚠️ Prueba en `.../tests/api/test_us1_formula_indice.py`: la fórmula **reproduce exactamente** `indice_consolidado` del legado en sus 182 filas. Falsable por mutación: cambiar un peso debe hacerla fallar
- [ ] T033 [P] [US1] Prueba en `.../tests/api/test_us1_componentes.py`: E4-01 **no responde `200` sin las cuatro componentes**. Un número único dice que la calidad bajó y no dice por qué
- [ ] T034 [P] [US1] Prueba en `.../tests/api/test_us1_campos_comprobados.py`: E4-02 publica `campos_comprobados`. Su cifra es 100 %, y sin la lista se lee como «el expediente es perfecto»
- [ ] T035 [P] [US1] Prueba en `.../tests/api/test_us1_ranking_completo.py`: E4-03 incluye los campos con **cero ausencias**
- [ ] T036 [US1] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_oe4_us1.py`: E4-02 coincide con `ot21_completitud_campos_criticos`; y para E4-01, la prueba **declara la divergencia de `pct_cobertura_evidencia` con su causa** —tres definiciones probadas, ninguna reproduce el legado— en vez de tolerarla o de fallar
- [ ] T037 [US1] Prueba de que los cuatro no exponen identidad de operadores ni de técnicos, **con `DirectorDatos`**
- [ ] T038 [US1] Marcar `indice_calidad_historico` como **fuente retirada** en la documentación del modelo: se conserva solo para contraste

**Checkpoint**: US1 entregable. **La última tabla legada del dominio deja de ser fuente**, y la
calidad del histórico pasa a medirse con una consulta legible.

---

## Phase 4: User Story 2 — Convertir el histórico en inteligencia vendible (Priority: P2)

**Goal**: los cuatro informes que se venden, **los cuatro completos** gracias a las columnas de la
fase 2.

**Independent Test**: pedir el mapa de concentración de un trimestre y comprobar que la suma por
ubicación es igual al total, que ninguna respuesta lleva coordenadas, y que E4-13 entrega duración y
distancia con denominadores distintos.

**Criterio medible (ISO 25010 — Seguridad)**: ninguna respuesta contiene coordenadas ni identidad,
consultada con la máxima autoridad del módulo (SC-006). Es el criterio más estricto del proyecto
porque estos datos **salen de la empresa**.

- [ ] T039 [P] [US2] Escribir `.../e4_05_concentracion_siniestralidad.sql`: densidad por condado, ciudad o calle según `nivel`, con top N y porcentaje acumulado. ⚠️ **Ubicación por nombre, nunca por coordenadas**
- [ ] T040 [US2] En la misma consulta, agrupar como **«Desconocido»** los casos sin ubicación resoluble, de modo que la suma por ubicación **sea igual** al total del período
- [ ] T041 [P] [US2] Escribir `.../e4_06_patron_horario_climatico.sql`: reparto por franja horaria y día de semana sobre los 4 252 casos, **y por `condicion_clima`**
- [ ] T042 [US2] ⚠️ En la misma consulta, devolver `cobertura: "parcial"` con `falta` nombrando la escasez climática mientras los casos con clima estén bajo `muestra_minima`. **3 de 4 252 tiene la forma de un patrón y el significado de una anécdota**, y este informe alimenta un modelo predictivo
- [ ] T043 [P] [US2] Escribir `.../e4_12_impacto_humano_por_zona.sql` con víctimas, heridos y fallecidos por severidad y condado, publicando `casos_con_dato` como denominador real
- [ ] T044 [P] [US2] Escribir `.../e4_13_impacto_vial_por_zona.sql` con **duración y distancia**, y sus **dos denominadores por separado** (`casos_con_duracion`, `casos_con_distancia`)
- [ ] T045 [US2] Emitir `meta.alcance` en E4-13 declarando **desde cuándo existe la métrica de distancia** (Regla 6). Sin ello, una serie que arranca en la fecha de la ampliación parece una caída de la afectación vial
- [ ] T046 [US2] Registrar los cuatro en `CATALOGO` y `PUBLICADOS`, con los parámetros `nivel`, `top`, `muestra_minima` y `por_condado`, y exponer sus endpoints
- [ ] T047 [P] [US2] Prueba de contrato de los cuatro en `.../tests/api/test_oe4_us2_contract.py`
- [ ] T048 [P] [US2] ⚠️ Prueba en `.../tests/api/test_us2_sin_coordenadas.py`: **ninguno de los cuatro devuelve latitud, longitud ni identidad**, con `DirectorDatos`. Es la prueba que más importa del módulo — el fallo no tiene síntoma visible, y el destinatario del dato es externo
- [ ] T049 [P] [US2] Prueba en `.../tests/api/test_us2_suma_ubicaciones.py`: la suma de casos por ubicación **es igual** al total del período, «Desconocido» incluido
- [ ] T050 [P] [US2] ⚠️ Prueba en `.../tests/api/test_us2_clima_escaso.py`: E4-06 devuelve `cobertura: "parcial"` con la muestra climática actual, y `completa` si se baja `muestra_minima` a 1
- [ ] T051 [P] [US2] ⚠️ Prueba en `.../tests/api/test_us2_denominadores_vial.py`: `casos_con_duracion` y `casos_con_distancia` son **distintos** (4 252 frente a ≈4 200). Si coinciden, la distancia entra como cero en los casos sin dato
- [ ] T052 [P] [US2] Prueba en `.../tests/api/test_us2_cero_vs_no_registrado.py`: un caso con cero heridos y otro sin heridos registrados dan resultados distintos, y `casos_con_dato` < `casos`
- [ ] T053 [P] [US2] Prueba en `.../tests/api/test_us2_zona_unica.py`: una zona con un solo caso **no aparece como concentración**; se declara bajo el umbral
- [ ] T054 [US2] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_oe4_us2.py`: E4-05 coincide con `ot21_ranking_ubicaciones` y `ot21_distribucion_zona`; E4-12 con `ot21_impacto_humano`
- [ ] T055 [US2] Prueba de permisos: `DirectorOperaciones` accede a E4-12 y E4-13 —miden el expediente— y recibe **`403` en E4-05 y E4-06**
- [ ] T056 [US2] Verificar contra la app real que los cuatro responden y que sus payloads no contienen ningún campo que no esté en el contrato OpenAPI

**Checkpoint**: US2 entregable. **Los cuatro productos vendibles están completos**, y los dos que
entregaban la mitad ya no lo hacen.

---

## Phase 5: User Story 3 — Saber si el histórico sirve para entrenar (Priority: P3)

**Goal**: E4-15 publicado con su umbral, y **E4-14 correctamente declarado como no medible**.

**Independent Test**: pedir la cobertura del histórico y comprobar que ninguna zona se marca con el
umbral por defecto y ambas se marcan con uno alto; y que E4-14 devuelve `404`.

- [ ] T057 [P] [US3] Escribir `.../e4_15_cobertura_del_historico.sql`: casos por condado contra `umbral_casos`, marcando `sin_masa_critica`
- [ ] T058 [US3] En la misma consulta, **publicar el umbral en cada fila**. Un «esta zona no tiene masa crítica» sin decir contra qué umbral no es accionable
- [ ] T059 [US3] Registrar E4-15 y exponer su endpoint con el parámetro `umbral_casos` (defecto 500)
- [ ] T060 [P] [US3] Prueba en `.../tests/api/test_us3_umbral.py`: con el defecto, **ninguna zona se marca** (2 158 y 2 094 casos); con `umbral_casos=3000`, **ambas se marcan**
- [ ] T061 [P] [US3] Prueba de contrato de E4-15 en `.../tests/api/test_oe4_us3_contract.py`
- [ ] T062 [US3] ⚠️ Verificar que **`latencia-de-ingesta` no existe como ruta** y devuelve `404`, en `.../tests/api/test_oe4_bloqueados.py`. Es el bloqueado que más fácil se cuela: `cargado_en` existe y la resta no falla
- [ ] T063 [US3] Registrar en `decisiones-pendientes.md` que **E4-14 no es medible por la regla de idempotencia**: cada recarga hace `DROP PARTITION` y reescribe `cargado_en`. Incluir la medición —4 252 filas con el mismo valor, mediana de 1 971 horas— y la salida: una marca de primera aparición por fila, que sería **una excepción deliberada a esa regla**

---

## Phase 6: User Story 4 — Evaluar el modelo predictivo (Priority: P4) ⛔ BLOQUEADA

**Goal**: dejar los cinco declarados con su prerrequisito, y **contar lo que cuesta no tenerlos**.

**Independent Test**: las cinco rutas devuelven `404`, y la documentación nombra los tres
prerrequisitos y los tres indicadores BSC que quedan sin fuente.

- [ ] T064 [US4] Verificar que `precision-modelo`, `contraste-prediccion`, `unidades-preposicionadas`, `versiones-modelo` y `productos-inteligencia` devuelven `404`, en `.../tests/api/test_oe4_bloqueados.py`
- [ ] T065 [US4] Documentar en `traceability.md` los tres prerrequisitos —`registro_predicciones`, `registro_modelos`, `catalogo_productos_inteligencia`— y **a qué informe desbloquea cada uno**
- [ ] T066 [US4] ⚠️ Declarar en la documentación del módulo que **tres indicadores del BSC de OE4 quedan sin fuente**: precisión del modelo (≥80 %), unidades preposicionadas (≥60 %) y productos de inteligencia. Los tres son de la perspectiva de Aprendizaje y crecimiento, que es la de este objetivo — **OE4 solo cubre hoy la mitad de su propio tablero**
- [ ] T067 [US4] Actualizar `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §4: los cinco pasan a **⛔** con su prerrequisito, y **E4-14 también**
- [ ] T068 [US4] Anotar en el mismo catálogo que **E4-09 tiene consecuencia de Safety**: mide si las unidades se preposicionan según el modelo, y un modelo mal evaluado desplaza ambulancias a las zonas equivocadas. Que esté bloqueado no lo hace menos crítico

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T069 [P] Prueba de conformidad con el contrato en `.../tests/api/test_openapi_conforme_oe4.py`: los nueve publicados están en el YAML, **los seis bloqueados no**, y el YAML **no declara ningún campo de coordenadas ni de identidad** — si apareciera, la implementación tendría permiso escrito para publicarlo
- [ ] T070 [P] ⚠️ Prueba transversal en `.../tests/api/test_oe4_sin_semaforo.py`: **ningún `meta.objetivo.cumple` es booleano** en los nueve. Es la prueba de OE6, que **aquí sí aplica** — a diferencia de OE3
- [ ] T071 [P] Prueba transversal de denominadores: ningún endpoint devuelve un porcentaje sin su total
- [ ] T072 [P] Prueba transversal de período vacío: los nueve devuelven `data: []` con `cobertura: "completa"`, nunca una fila de ceros
- [ ] T073 [P] Prueba transversal de que ninguna respuesta acepta ni emite `por_region`
- [ ] T074 Medir la cobertura de la parte OE4 de `backend/apps/informes_estrategicos/` y dejarla **≥80 %** en servicios
- [ ] T075 Recorrer entero [`quickstart.md`](quickstart.md) §2 —las 15 comprobaciones— contra el stack levantado, **anotando en el fichero las cifras medidas**
- [ ] T076 Escribir `traceability.md`: FR-OE4-nnn → tarea → prueba, y los criterios de aceptación de las cuatro historias, incluidas las bloqueadas
- [ ] T077 [P] Anotar en `.specify/docs/changelog.md` los **tres hallazgos fuera de ciclo** de este módulo: la fórmula del índice descifrada, las dos métricas que existían en el origen y no se cargaban, y la imposibilidad estructural de E4-14
- [ ] T078 [P] Actualizar `specs/001-estrategico/contrato-informes-estrategicos.md` §10 con el estado de OE4
- [ ] T079 ⚠️ Reconstruir y recrear los contenedores: `docker compose -f docker/accidentes.yml up -d --build django frontend`, verificando con `docker ps --filter name=accidentes-` que ambos están `Up`. **El frontend se sirve desde imagen nginx: no hay recarga en caliente**
- [ ] T080 Verificar contra la app real, con `DirectorDatos` y `DirectorOperaciones`, que los nueve responden según la matriz del quickstart §2.14 — **incluido el `403` de Operaciones en los de analítica pura**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: depende de que exista el armazón de OE6 (T001)
- **Foundational (Phase 2)**: depende de Setup. **Bloquea las cuatro historias**
- **US1 (Phase 3)**: depende de Foundational, pero **no de las dos columnas nuevas**: sus cuatro
  informes se calculan con lo que ya había
- **US2 (Phase 4)**: depende de Foundational **y en particular de T006–T014**. Es la única historia
  con dependencia dura sobre la ampliación del modelo
- **US3 (Phase 5)** y **US4 (Phase 6)**: solo necesitan el servicio en pie. **Pueden hacerse en
  cualquier momento tras la fase 2**
- **Polish (Phase 7)**: depende de las historias entregadas

### User Story Dependencies

- **US1 (P1)**: ninguna. Es el MVP y **no necesita las columnas nuevas**
- **US2 (P2)**: ninguna respecto de US1, pero **sí sobre la fase 2**
- **US3 (P3)**: ninguna. Una consulta y dos tareas documentales
- **US4 (P4)**: ninguna. Enteramente documental

### Parallel Opportunities

- **Fase 2**: T010–T013 y T019–T022 en paralelo. T006–T009 son la misma cadena de carga y van en serie
- **Fase 3**: T023, T026, T027 y T028 son ficheros distintos; T031–T035 en paralelo tras el endpoint
- **Fase 4**: T039, T041, T043 y T044 en paralelo — cuatro consultas independientes
- **Fases 5 y 6**: casi todo en paralelo, y en paralelo con las fases 3 y 4
- **Fase 7**: T069–T073 y T077–T078 en paralelo

---

## Parallel Example: Phase 4

```bash
# Las cuatro consultas de US2, ficheros distintos y sin dependencias entre sí:
Task: "e4_05_concentracion_siniestralidad.sql — densidad por zona, ubicación por nombre"
Task: "e4_06_patron_horario_climatico.sql — franja y día sobre 4252, clima sobre 3"
Task: "e4_12_impacto_humano_por_zona.sql — con casos_con_dato como denominador"
Task: "e4_13_impacto_vial_por_zona.sql — duración y distancia, denominadores separados"
```

---

## Implementation Strategy

### MVP primero (solo US1)

1. Fase 1: Setup — con T001 como puerta
2. Fase 2: Foundational
3. Fase 3: US1
4. **PARAR Y VALIDAR**: comprobaciones 2.3, 2.4, 2.5, 2.6 y 2.11 del quickstart
5. Entregar

**El MVP tiene valor por sí solo**: la calidad del histórico —la condición previa de que este objetivo
signifique algo— pasa a medirse con una consulta legible, y **se retira la última tabla legada del
dominio**.

### Atajo recomendado

**Si el objetivo es entregar valor comercial cuanto antes, US2 es la historia que se vende.** Pero
depende de la fase 2 entera, mientras que US1 no depende de las columnas nuevas. Con una sola persona,
el orden P1 → P2 sigue siendo el correcto: US1 valida el armazón con menos piezas móviles.

**Las fases 5 y 6 son baratas** —12 tareas, casi todas documentales— y conviene adelantarlas: dejan
el catálogo corregido y los `404` garantizados antes de que nadie construya encima.

### Entrega incremental

1. Setup + Foundational → dos columnas nuevas con sus volúmenes reales
2. US1 → **MVP**, la calidad medible y la tabla legada retirada
3. US2 → **los cuatro productos vendibles, completos**
4. US3 + US4 → el catálogo dice la verdad sobre lo que falta

---

## Notes

- `[P]` = ficheros distintos, sin dependencias pendientes
- **Ninguna tarea crea una tabla.** Las dos ampliaciones son columnas de un hecho existente
- ⚠️ **T009 es la tarea con más probabilidad de fallar en silencio** de todo el módulo. El fallo ya
  ocurrió en este mismo flujo con seis fuentes de OT24: el modelo publicó 0 notas donde el origen
  tenía 51, sin un solo error. T010 existe para atraparlo
- ⚠️ **T070 es la prueba de OE6 y aquí SÍ aplica.** En OE3 hay que hacer lo contrario. Los tres
  módulos conviven en la misma app
- Confirmar que las pruebas fallan antes de implementar, y **verificarlas falsables por mutación** en
  las marcadas con ⚠️
- Parar en cualquier checkpoint para validar la historia por separado
