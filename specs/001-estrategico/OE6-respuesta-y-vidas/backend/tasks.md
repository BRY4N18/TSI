# Tasks: OE6 — Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Input**: Design documents from `specs/001-estrategico/OE6-respuesta-y-vidas/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80 % en servicios, y este
módulo produce **cifras para decidir sobre tiempos de emergencia**: una consulta que devuelve un
número plausible y equivocado no falla, no avisa, y solo se detecta comparándola con algo.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1–US4 según [`spec.md`](spec.md)
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Es el piloto de la capa estratégica.** La mitad del trabajo de las fases 1 y 2 **no es de OE6**: son
las piezas que van a usar los otros cinco objetivos —ventanas comparadas, granularidad, metas del
BSC—. Por eso viven en la raíz de la app y no bajo `oe6`.

**No construye doce informes desde cero.** Diez tienen una consulta táctica de la que partir
(research D8); dos son nuevas (E6-01 y E6-03). El trabajo está en la forma estratégica, no en la
aritmética.

**Y no amplía el modelo.** Primer módulo del proyecto que no lo necesita. Si una tarea acaba
proponiendo una tabla, algo se entendió mal.

### Tres cosas que este módulo tiene prohibido hacer

| Prohibido | Por qué |
|---|---|
| **Unir `hecho_accidente` con `dim_region` por estado** | Duplica cada caso sin fallar: 4 252 salen como 8 504. El eje de región no existe (research D1) |
| **Publicar un `cumple` booleano** | Todas las metas de OE6 son `[CALIBRAR]`. Un semáforo aquí inventa un umbral y luego se mide contra él |
| **Ampliar la tolerancia de una prueba de contraste** | Si dos capas divergen, la salida es promover la medida a fichero compartido |

---

## Phase 1: Setup — la app y el catálogo de consultas

**Purpose**: crear el sitio donde vive todo y comprobar que el sustrato está cargado.

- [X] T001 Verificar la línea base del almacén siguiendo [`quickstart.md`](quickstart.md) §1: 13 tablas en `tsi_tactico`, 4 252 casos, 3 637 con llegada, 4 314 intentos y rango 2026-02-03 → 2026-08-13. **Anotar las cifras medidas en el propio `quickstart.md`** si difieren, en vez de asumir las de la spec
- [X] T002 Crear la app Django `backend/apps/informes_estrategicos/` con `apps.py` e `__init__.py`, y registrarla en `INSTALLED_APPS` de `backend/config/settings.py`
- [X] T003 Crear `dags/lib/consultas/estrategicos/oe6/` con un `README.md` que fije las convenciones del catálogo: un fichero por informe, nombre `e6_NN_<informe>.sql`, encabezado con el porqué de cada decisión no obvia
- [X] T004 [P] Prueba en `dags/tests/test_catalogo_estrategicos.py` de que el cargador existente resuelve el catálogo **anidado** (`departamento="estrategicos/oe6"`) y falla nombrando la ruta buscada cuando el nombre no existe
- [X] T005 [P] Registrar las rutas de la app en `backend/config/urls.py` bajo `/api/v1/informes-estrategicos/`

---

## Phase 2: Foundational — las piezas de **toda** la capa estratégica

**Purpose**: lo transversal a los seis OE. Se escribe una vez y aquí.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

### El período, que aquí es obligatorio

- [X] T006 Implementar `backend/apps/informes_estrategicos/periodo_estrategico.py`: `desde`, `hasta` y `granularidad` **obligatorios**; omitir cualquiera responde `400` **nombrando cuál falta** (FR-OE6-003). Es la regla inversa a la de los listados tácticos, así que **no se reutiliza `informes_tacticos/periodo.py`**
- [X] T007 En el mismo fichero, traducir `granularidad` desde una **lista cerrada** de tres valores (`mes` · `trimestre` · `anio`) a la función de truncado. ⚠️ **Nunca interpolar el valor de la petición en el SQL**: el nombre de la función va dentro de la consulta, así que un valor libre sería inyección
- [X] T008 Implementar el cálculo de las **ventanas de comparación** en el mismo fichero: `mom` y `yoy` desplazan la ventana **conservando su longitud**, y la respuesta declara las dos (FR-OE6-004)
- [X] T009 Implementar la marca `parcial` para un período en curso (FR-OE6-005)
- [X] T010 Implementar el caso **ventana anterior sin datos**: devuelve la comparación ausente con `motivo_ausencia`, **no un `400` ni una variación de 0 %** (research D5). Con el histórico actual esto es lo que hará **todo** `yoy`

### Las metas del BSC

- [X] T011 [P] Implementar `backend/apps/informes_estrategicos/objetivo.py`: `valor`, `unidad`, `tipo` (`NORMATIVO` / `CALIBRAR`) y `cumple`, con la regla dura de que **`cumple` es `null` siempre que `tipo` sea `CALIBRAR`** (FR-OE6-006)

### La respuesta y el acceso

- [X] T012 [P] Implementar `backend/apps/informes_estrategicos/envelope.py`: `{data, meta}` con `periodo`, `comparacion`, `objetivo`, `cobertura`, `falta` y `alcance`. ⚠️ **No emite `acotado_a`**: esta capa no acota por titularidad, y un `todos` fijo no significaría nada (FR-OE6-015)
- [X] T013 Añadir `ROL_GERENTE = "Gerente"` y el conjunto `AUTORIDAD_ESTRATEGICA_OE6` a `backend/core/auth/roles_tacticos.py`, con el docstring explicando que el `Gerente` **no es un grupo que acumule directores**: cada director entra por su departamento
- [X] T014 Implementar `backend/apps/informes_estrategicos/permissions.py`: acceden `DirectorOperaciones` y `Gerente`; **cualquier otro rol recibe `403`**, incluidos `Operador`, `Despacho` y `Unidad` (FR-OE6-013, FR-OE6-014)

### El acceso al almacén y el armazón de OE6

- [X] T015 Implementar `backend/core/repositories/informes_estrategicos/modelo_estrategico_repository.py`: envuelve el `ModeloRepository` existente y resuelve la **doble ejecución** de la comparación (research D4). **Solo lectura**
- [X] T016 Implementar `backend/apps/informes_estrategicos/services/oe6_service.py` con el patrón `CATALOGO` (informe → fichero) y `PUBLICADOS` (los que tienen endpoint), copiando la separación de `emergencias_compuestos_service.py`: un informe existe **porque está en el registro**, no porque haya un fichero en el disco
- [X] T017 Implementar `backend/apps/informes_estrategicos/views/oe6_views.py` y `urls.py`, con la vista base que resuelve período, permisos y envelope

### Las pruebas transversales, que son las que atrapan lo silencioso

- [X] T018 [P] ⚠️ Prueba de la **regla de versión final** en `dags/tests/test_catalogo_estrategicos.py`, sobre el texto de las consultas: toda consulta que toca `hecho_accidente`, `hecho_despacho`, `dim_severidad` o `dim_geografia` **fuerza la versión final**; ninguna que toca `hecho_evidencia` lo hace. Omitirla infla cifras **solo a veces**; pedirla de más falla con `ILLEGAL_FINAL`
- [X] T019 [P] ⚠️ Prueba en el mismo fichero de que **ninguna consulta nombra `dim_region` ni una columna de región**. Es la prohibición de research D1, y su fallo es el más silencioso del módulo: los totales se doblan y cada región muestra el total completo
- [X] T020 [P] Prueba en el mismo fichero de que **ninguna consulta usa `SELECT *`** y de que **todas llevan `ORDER BY` explícito** y **filtran por `fecha`** (Regla 7)
- [X] T021 [P] Prueba en el mismo fichero de que ninguna consulta nombra una columna de coordenadas, identidad de persona o texto libre (FR-OE6-009)
- [X] T022 [P] Prueba unitaria de `periodo_estrategico` en `backend/apps/informes_estrategicos/tests/unit/test_periodo_estrategico.py`: las dos ventanas tienen igual longitud; falta un parámetro → `400` que lo nombra; granularidad desconocida → `400` que lista las válidas; período en curso → `parcial: true`
- [X] T023 [P] Prueba unitaria de `objetivo` en `.../tests/unit/test_objetivo.py`: **ningún objetivo `CALIBRAR` devuelve un `cumple` booleano**, ni siquiera pasándole un valor medido
- [X] T024 Prueba de permisos en `.../tests/api/test_permisos_oe6.py`: `DirectorOperaciones` y `Gerente` entran; `Operador`, `Despacho`, `Unidad`, `Administrador` y `DirectorFinanciero` reciben **`403`, no `200` con `data: []`**

**Checkpoint**: la capa estratégica tiene su armazón. Las cuatro user stories pueden abordarse.

---

## Phase 3: User Story 1 — Cuánto tarda en llegar la ayuda (Priority: P1) 🎯 MVP

**Goal**: los dos informes del KPI del objetivo, con mediana y p95, comparables entre períodos.

**Independent Test**: pedir `tiempo-respuesta-global` de un trimestre con `comparacion=yoy` y obtener
mediana, p95, las dos ventanas declaradas y el recuento de casos — sin que exista ninguna tabla nueva.

**Criterio medible (ISO 25010 — Seguridad física)**: un caso **sin llegada registrada nunca aparece
como tiempo cero** (SC-004). Contarlo así haría instantáneos precisamente los casos que nadie atendió.

- [X] T025 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe6/e6_01_tiempo_respuesta_global.sql`: mediana y p95 de `hora_primera_llegada − fechahora_accidente`, con `casos_con_llegada` y `excluidos_sin_llegada`. ⚠️ **Sin unir con `hecho_despacho`** — el hito ya está desnormalizado en el caso, y unir reintroduciría el riesgo de contar intentos como casos
- [X] T026 [US1] En la misma consulta, aplicar el filtro de los tres términos —con llegada, no descartado, no duplicado— **y documentar en el encabezado por qué ninguno es redundante**
- [X] T027 [US1] En la misma consulta, devolver el p95 **ausente** cuando la muestra no alcance `muestra_minima` (FR-OE6-017). Con cinco observaciones el p95 es el máximo, no un percentil
- [X] T028 [P] [US1] Escribir `.../e6_02_tiempo_respuesta_por_severidad.sql`, partiendo de `ot22_tiempo_respuesta_por_severidad.sql`: añadir p95 y granularidad, ordenar por `dim_severidad.orden` **y no alfabéticamente**, y agrupar como «Desconocido» los casos sin severidad resuelta
- [X] T029 [US1] Registrar los dos informes en `CATALOGO` y `PUBLICADOS` de `oe6_service.py`, con sus parámetros (`muestra_minima`, `por_condado` en E6-01)
- [X] T030 [US1] Exponer los dos endpoints en `views/oe6_views.py` y `urls.py` según [`contracts/informes-estrategicos-oe6.openapi.yaml`](contracts/informes-estrategicos-oe6.openapi.yaml)
- [X] T031 [P] [US1] Prueba de contrato de los dos endpoints en `.../tests/api/test_oe6_us1_contract.py`: forma de `data` y de `meta`, y `400` cuando falta `granularidad`
- [X] T032 [P] [US1] ⚠️ Prueba en `.../tests/api/test_us1_sin_llegada.py`: los casos sin llegada **se declaran en `excluidos_sin_llegada` y no entran en la mediana**. Falsable por mutación: incluirlos como cero debe hacer fallar la prueba, y el síntoma en producción sería **un tiempo de respuesta que mejora cuando empeora la atención**
- [X] T033 [P] [US1] Prueba en `.../tests/api/test_us1_percentil.py`: con `muestra_minima` alta el p95 sale `null`, no un número
- [X] T034 [P] [US1] Prueba en `.../tests/api/test_us1_suma_severidad.py`: la suma de los recuentos por severidad **es igual** al total de casos con llegada del período, «Desconocido» incluido
- [X] T035 [P] [US1] Prueba de la comparación en `.../tests/api/test_us1_comparacion.py`: `mom` declara dos ventanas de igual longitud; `yoy` devuelve `ventana_anterior: null` con `motivo_ausencia`, **no un `400`**
- [X] T036 [US1] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_us1.py`: con granularidad `mes` y sin comparación, las cifras de `tiempo-respuesta-por-severidad` **coinciden** con las de `ot22_tiempo_respuesta_por_severidad` (SC-007)
- [X] T037 [US1] Prueba de que ninguna de las dos respuestas contiene coordenadas ni identidad, **ejecutada con el rol `DirectorOperaciones`** y no solo con uno acotado

**Checkpoint**: US1 entregable. **El KPI del objetivo estratégico pasa de no medible a medible**, con
la línea base que hoy falta para poder fijar su meta.

---

## Phase 4: User Story 2 — Dónde se va ese tiempo (Priority: P2)

**Goal**: los tres informes que explican el número de US1 — en qué tramo, con qué origen y frente a
qué referencia.

**Independent Test**: tomar un período con la mediana degradada respecto al anterior y comprobar que
el desglose por tramos localiza en cuál se produjo la diferencia.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: cada tramo publica **su propia población**, y
son distintas entre sí (SC-003 en su variante de denominador).

- [X] T038 [P] [US2] Escribir `.../e6_03_tramos_del_ciclo.sql` con los cuatro tramos, cada uno como resta dentro de `hecho_accidente`: registro→confirmación, confirmación→asignación, asignación→llegada, llegada→cierre
- [X] T039 [US2] En la misma consulta, dar a **cada tramo su propio denominador** y publicarlo. ⚠️ Un denominador común descartaría los ~404 casos que se confirmaron y nunca se asignaron, que es justo donde vive la información sobre los que se atascaron al principio
- [X] T040 [US2] En la misma consulta, agrupar **por período y nunca por unidad** (FR-OE6-021), documentando en el encabezado que es lo que disuelve la decisión #35: la duración de un caso es propiedad del caso
- [X] T041 [P] [US2] Escribir `.../e6_04_origen_de_asignacion.sql`, partiendo de `ot22_asignacion_automatica_vs_manual.sql`: añadir granularidad y condado, e **incluir «escalado a zona» como origen propio** — sumarlo a «manual» ocultaría cuándo el sistema se queda sin cobertura local
- [X] T042 [P] [US2] Escribir `.../e6_07_desviacion_de_llegada.sql`, partiendo de `ot23_desviacion_llegada.sql`: añadir granularidad, **conservando intactas** la ventana anterior al período, la muestra mínima y el renombrado `ref_seg` que evita el `ILLEGAL_AGGREGATION`
- [X] T043 [US2] Registrar los tres informes en `CATALOGO` y `PUBLICADOS`, con los parámetros `ventana_dias` y `muestra_minima` de E6-07
- [X] T044 [US2] Exponer los tres endpoints según el contrato
- [X] T045 [US2] Emitir `meta.alcance` en E6-07 declarando que la referencia es **el histórico comparable y no un ETA estimado** (FR-OE6-025)
- [X] T046 [P] [US2] Prueba de contrato de los tres endpoints en `.../tests/api/test_oe6_us2_contract.py`
- [X] T047 [P] [US2] ⚠️ Prueba en `.../tests/api/test_us2_tramos_poblacion.py`: los cuatro tramos devuelven **recuentos distintos entre sí** (4 040 / 3 638 / 3 637 / 3 636 en la línea base). Si los cuatro coinciden, se está usando un denominador común
- [X] T048 [P] [US2] Prueba en `.../tests/api/test_us2_tramos_suman.py`: para los casos completos, la suma de los tiempos por tramo **es igual** al tiempo total, sin residuo
- [X] T049 [P] [US2] Prueba en `.../tests/api/test_us2_origen.py`: los porcentajes de los tres orígenes **suman 100 %**
- [X] T050 [P] [US2] Prueba en `.../tests/api/test_us2_referencia_ausente.py`: sin muestra suficiente, referencia y desviación salen **`null`**. Un `0` diría «llegó exactamente a tiempo», que convertiría una unidad sin histórico en una unidad ejemplar
- [X] T051 [US2] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_us2.py`: `origen-de-asignacion` y `desviacion-de-llegada` coinciden con sus equivalentes tácticos con la misma agrupación y período (SC-007)
- [X] T052 [US2] Prueba de que E6-07 **no expone identidad del operador ni del técnico**, con el rol de autoridad

**Checkpoint**: US2 entregable. El número de US1 deja de ser un termómetro sin diagnóstico.

---

## Phase 5: User Story 3 — Qué falla en la ejecución (Priority: P3)

**Goal**: los cuatro modos de fallo, con los denominadores correctos y las limitaciones declaradas.

**Independent Test**: pedir los cuatro informes y comprobar que cada tasa publica su denominador y que
los dos informes afectados por una decisión abierta **declaran qué miden**.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: la tasa de rechazo de una unidad **no baja al
añadirle despachos bien atendidos** (SC-003). Hoy el endpoint táctico hace exactamente eso, con un
factor medido de 2,6.

> ⚠️ **Es la historia con las tres decisiones abiertas.** Está aislada aquí para que un bloqueo de
> esquema no pare el MVP. Si #36 se resolviera durante esta fase, T063 cambia de alcance.

- [X] T053 [P] [US3] Escribir `.../e6_05_rechazo_y_timeout_por_unidad.sql`, **adoptando `ot22_rechazo_timeout_por_unidad.sql`**, cuya consulta ya calcula bien: denominador en **intentos ofrecidos**, no en transiciones de estado (decisión #34)
- [X] T054 [US3] En la misma consulta, publicar **`tasa_rechazo` y `tasa_vencimiento` por separado**, cada una con su denominador. Sumarlas en «no atendidos» daría 661 y ocultaría que la mitad de las veces **nadie contestó**, que es otro problema y se arregla de otra manera
- [X] T055 [US3] Emitir `meta.alcance` en E6-05 declarando que el denominador son intentos ofrecidos
- [X] T056 [P] [US3] Escribir `.../e6_06_abortos_y_misiones_fallidas.sql`, partiendo de `ot23_abortos_perdidas.sql`: granularidad y condado, contando **misiones y no transiciones**
- [X] T057 [P] [US3] Escribir `.../e6_09_cierres_forzados.sql`, partiendo de `ot25_cierres_forzados.sql`
- [X] T058 [US3] ⚠️ Emitir en E6-09 `meta.alcance` y `cobertura: "parcial"` con `falta: ["retiro manual desde central"]`, declarando que mide el indicador del despacho —**1 de 4 314**— y no la definición del catálogo —**451 de 3 310**— (FR-OE6-029, decisión #36)
- [X] T059 [P] [US3] Escribir `.../e6_10_envejecimiento_casos_abiertos.sql`, partiendo de `ot25_envejecimiento_cartera.sql`, con los tramos calculados **contra el instante de la consulta** y considerando abierto solo al caso sin hora de cierre
- [X] T060 [US3] Registrar los cuatro informes en `CATALOGO` y `PUBLICADOS`, con los parámetros `top` y `tramos_dias`
- [X] T061 [US3] Reutilizar `ParametroTramos` de `emergencias_compuestos_service.py` para `tramos_dias`, **ordenando la lista antes de pasarla**: una lista desordenada asigna casos al tramo equivocado sin fallar
- [X] T062 [US3] Exponer los cuatro endpoints según el contrato
- [X] T063 [P] [US3] Prueba de contrato de los cuatro en `.../tests/api/test_oe6_us3_contract.py`
- [X] T064 [P] [US3] ⚠️ Prueba en `.../tests/api/test_us3_denominador_intentos.py`: añadir despachos **confirmados y completados** a una unidad **no baja** su tasa de rechazo. Es el defecto #34 y su síntoma es contraintuitivo — cuanto mejor trabaja una unidad, mejor parece
- [X] T065 [P] [US3] Prueba en `.../tests/api/test_us3_rechazo_vs_vencido.py`: las dos tasas se publican por separado y sus recuentos cuadran con 334 y 327 en la línea base
- [X] T066 [P] [US3] ⚠️ Prueba en `.../tests/api/test_us3_alcance_declarado.py`: E6-09 **no responde `200` sin `meta.alcance`**. Sin esa declaración, un `1 de 3310` se lee como «esto casi no pasa» cuando la definición pedida da 451
- [X] T067 [P] [US3] Prueba en `.../tests/api/test_us3_envejecimiento.py`: ningún caso abierto aparece como cerrado, y los tramos cubren toda la cartera sin solaparse
- [X] T068 [US3] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_us3.py`: `abortos` y `envejecimiento` **coinciden** con sus equivalentes tácticos; `rechazo-y-timeout` **debe divergir** —el estratégico corrige #34 y da una tasa mayor—, y la prueba **declara la divergencia con su causa** en vez de tolerarla

**Checkpoint**: US3 entregable. Los cuatro modos de fallo son medibles, y los dos limitados lo dicen.

---

## Phase 6: User Story 4 — El resultado sobre la persona (Priority: P4)

**Goal**: los tres informes que distinguen OE6 de OE3 — OE3 mide el proceso; esto mide el resultado
sobre quien esperaba una ambulancia.

**Independent Test**: pedir el impacto humano de un período y comprobar que las sumas cuadran con el
total de casos, y que los dos informes de dato escaso **declaran su escasez** en vez de devolver ceros.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: el impacto humano **distingue «cero» de «no
registrado»** (SC-009).

- [X] T069 [P] [US4] Escribir `.../e6_08_impacto_humano.sql`, partiendo de `ot21_impacto_humano.sql`: añadir granularidad y severidad, sumando víctimas, heridos y fallecidos
- [X] T070 [US4] En la misma consulta, publicar `casos_con_dato` junto a `casos`. ⚠️ Sumar los no registrados como ceros haría **bajar** el impacto humano total cada vez que empeora la calidad del registro — el indicador se movería en la dirección contraria a la realidad
- [X] T071 [P] [US4] Escribir `.../e6_11_escaladas_de_severidad.sql`, partiendo de `ot24_escaladas_severidad.sql`, con granularidad
- [X] T072 [US4] ⚠️ Emitir en E6-11 `cobertura: "parcial"` cuando la muestra no alcance el mínimo. Un porcentaje cercano a cero **no significa que la severidad inicial acierte casi siempre**: significa que casi nadie usa la función
- [X] T073 [P] [US4] Escribir `.../e6_12_cobertura_de_evidencia.sql`, partiendo de `ot24_cobertura_evidencia.sql`: solo casos **cerrados**, separando `con_foto`, `con_nota` y `con_ambas` antes de combinarlas. ⚠️ `hecho_evidencia` es de transacción: **prohibido forzar la versión final**, pedirlo falla
- [X] T074 [US4] Registrar los tres informes en `CATALOGO` y `PUBLICADOS` y exponer sus endpoints según el contrato
- [X] T075 [P] [US4] Prueba de contrato de los tres en `.../tests/api/test_oe6_us4_contract.py`
- [X] T076 [P] [US4] Prueba en `.../tests/api/test_us4_cero_vs_no_registrado.py`: un caso con cero heridos y un caso sin heridos registrados **producen resultados distintos**
- [X] T077 [P] [US4] Prueba en `.../tests/api/test_us4_escasez.py`: con muestra insuficiente, E6-11 devuelve `cobertura: "parcial"`
- [X] T078 [P] [US4] Prueba en `.../tests/api/test_us4_evidencia.py`: solo entran casos cerrados, y foto y nota se publican por separado además de combinadas
- [X] T079 [US4] ⚠️ Prueba de contraste en `.../tests/contraste/test_contraste_us4.py`: los tres coinciden con sus equivalentes tácticos (SC-007)
- [X] T080 [US4] Prueba de que los tres **no exponen identidad de implicados, conductores ni del técnico que capturó la evidencia**, con el rol de autoridad

**Checkpoint**: los doce informes funcionan y son independientemente verificables.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: lo que afecta a los doce, y lo que deja el módulo cerrado para el siguiente OE.

- [X] T081 [P] Prueba de conformidad con el contrato en `.../tests/api/test_openapi_conforme_oe6.py`: los doce endpoints publicados están en el YAML, y el YAML **no declara ningún campo sensible** — si apareciera ahí, la implementación tendría permiso escrito para publicarlo
- [X] T082 [P] ⚠️ Prueba transversal en `.../tests/api/test_ningun_cumple_booleano.py`: recorrer los doce y comprobar que **ningún `meta.objetivo.cumple` es booleano**. Todas las metas de OE6 son `[CALIBRAR]`, así que la comprobación es absoluta
- [X] T083 [P] Prueba transversal de denominadores en `.../tests/api/test_todo_porcentaje_con_denominador.py`: ningún endpoint devuelve un porcentaje sin el total sobre el que se calculó
- [X] T084 [P] Prueba transversal de período vacío en `.../tests/api/test_periodo_sin_datos.py`: los doce devuelven `data: []` con `cobertura: "completa"`, **nunca una fila de ceros**
- [X] T085 Medir la cobertura de `backend/apps/informes_estrategicos/` y dejarla **≥80 %** en servicios, según la constitución y `.specify/docs/architecture/testing.md`
- [X] T086 Recorrer entero [`quickstart.md`](quickstart.md) §2 contra el stack levantado —las 15 comprobaciones— y **anotar en el propio fichero las cifras medidas**, no las previstas
- [X] T087 Escribir `traceability.md` en la raíz de esta capa: FR-OE6-nnn → tarea → prueba, y los criterios de aceptación de las cuatro historias
- [X] T088 [P] Actualizar `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §6: los doce de OE6 pasan de ⚪ a construido, **y se corrigen las cinco discrepancias de fuente** que la spec documentó (`hecho_accidente_tipo_estado`, `hecho_ubicacion_unidad`, `eta_estimado`, `hecho_historial_severidad_accidente`, el JOIN de E6-01)
- [X] T089 [P] Añadir el eje de región al §6 del mismo catálogo como **⛔ no construible**, con su prerrequisito, igual que el catálogo ya hace con el CAC y el NPS
- [X] T090 [P] Anotar en `.specify/docs/changelog.md` lo que se descubrió fuera del ciclo: la refutación del eje de región y la corrección de `FR-OE6-008`, con referencia a la decisión #38
- [X] T091 ⚠️ Reconstruir y recrear los contenedores del aplicativo: `docker compose -f docker/accidentes.yml up -d --build django frontend`, y verificar con `docker ps --filter name=accidentes-` que ambos están `Up`. **El frontend se sirve desde imagen nginx, así que no hay recarga en caliente**
- [X] T092 Verificar contra la app real, con un usuario de rol `DirectorOperaciones`, que los doce endpoints responden y que un rol operativo recibe `403`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup. **Bloquea las cuatro user stories**
- **User Stories (Phases 3–6)**: dependen de Foundational. Entre sí **son independientes**
- **Polish (Phase 7)**: depende de las historias que se quieran entregar

### User Story Dependencies

Las cuatro son independientes y pueden abordarse en cualquier orden tras la fase 2. El orden
propuesto es de **valor**, no de dependencia técnica:

- **US1 (P1)**: ninguna dependencia. Es el KPI del objetivo y la rebanada de menor riesgo
- **US2 (P2)**: ninguna técnica. **Depende de US1 para tener sentido** — explica su número
- **US3 (P3)**: ninguna. Aislada a propósito: concentra las tres decisiones abiertas
- **US4 (P4)**: ninguna. Última porque dos de sus tres informes operan sobre dato escaso, y su valor
  llega cuando el histórico crezca

### Dentro de cada historia

Consulta SQL → registro en el servicio → endpoint → pruebas. Las pruebas de contraste van al final de
su historia: necesitan el endpoint en pie para compararlo con el táctico.

### Parallel Opportunities

- **Fase 2**: T011, T012 y T018–T023 en paralelo. T006–T010 comparten fichero, así que van en serie
- **Fase 3**: T025 y T028 son ficheros distintos; T031–T035 en paralelo tras el endpoint
- **Fase 4**: T038, T041 y T042 en paralelo — tres consultas independientes
- **Fase 5**: T053, T056, T057 y T059 en paralelo — cuatro consultas independientes
- **Fase 6**: T069, T071 y T073 en paralelo
- **Fase 7**: T081–T084 y T088–T090 en paralelo

---

## Parallel Example: Phase 5

```bash
# Las cuatro consultas de US3, ficheros distintos y sin dependencias entre sí:
Task: "e6_05_rechazo_y_timeout_por_unidad.sql — adoptar la consulta táctica correcta"
Task: "e6_06_abortos_y_misiones_fallidas.sql — granularidad y condado"
Task: "e6_09_cierres_forzados.sql — partiendo de ot25_cierres_forzados"
Task: "e6_10_envejecimiento_casos_abiertos.sql — tramos contra el instante de consulta"
```

---

## Implementation Strategy

### MVP primero (solo US1)

1. Fase 1: Setup
2. Fase 2: Foundational — **crítica, bloquea todo, y la mitad no es de OE6** sino de la capa
3. Fase 3: US1
4. **PARAR Y VALIDAR**: las comprobaciones 2.2, 2.3, 2.4, 2.10 y 2.11 del quickstart
5. Entregar

**El MVP tiene valor por sí solo**: el KPI del objetivo estratégico pasa de no medible a medible, y su
primera lectura produce la línea base que hoy falta para poder fijar la meta.

### Entrega incremental

1. Setup + Foundational → el armazón de la capa estratégica, reutilizable por los cinco OE restantes
2. US1 → **MVP**, el KPI del BSC
3. US2 → el diagnóstico de ese KPI
4. US3 → los modos de fallo
5. US4 → el resultado sobre la persona

Cada historia añade valor sin romper las anteriores.

### Si hay varias personas

Tras la fase 2, las cuatro historias pueden repartirse. **La fase 2 conviene hacerla entre todos o por
una sola persona**: es la que fija la forma que copiarán los otros cinco objetivos, y una divergencia
ahí se paga seis veces.

---

## Notes

- `[P]` = ficheros distintos, sin dependencias pendientes
- Cada consulta lleva **en su encabezado el porqué de sus decisiones no obvias**, como las 26 tácticas.
  Es lo que evitó que se perdiera el motivo del renombrado `ref_seg`
- **Ninguna tarea crea una tabla.** Si una acaba proponiéndolo, es señal de que se entendió mal el
  alcance: este módulo no amplía el modelo
- Confirmar que las pruebas fallan antes de implementar, y **verificarlas falsables por mutación** en
  las marcadas con ⚠️ — son las que atrapan fallos silenciosos, y una prueba que no puede fallar da
  una confianza peor que no tenerla
- Parar en cualquier checkpoint para validar la historia por separado
