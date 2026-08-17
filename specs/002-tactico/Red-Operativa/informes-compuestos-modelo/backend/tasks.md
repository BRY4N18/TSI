# Tasks: Informes Compuestos de Red Operativa sobre el Modelo Analítico

**Input**: Design documents from `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** Este departamento tiene dos formas de equivocarse que **no
fallan**: unir con un catálogo de estados incompleto pierde el 13 % de los datos, y medir la
disponibilidad por transiciones da 0 % justo a las unidades que nunca fallaron. Solo una prueba
distingue esas cifras de las correctas.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**No crea ninguna pieza de infraestructura.** Reutiliza el cargador de consultas, el repositorio de
lectura, la resolución de período, los permisos y el versionado de dimensiones — todo construido para
Emergencias. Lo propio son sus consultas, dos dimensiones, dos hechos y sus endpoints.

**Es la comprobación de que el patrón escala.** Si el segundo departamento necesitara plomería
propia, los seis restantes también, y los 108 informes del catálogo volverían a ser 108 soluciones
particulares.

**⚠️ Depende de las fases 1 y 2 de Emergencias**, no de sus informes. Es la única dependencia entre
departamentos, y por eso está dicha aquí arriba.

---

## Phase 1: Setup

**Purpose**: comprobar los dos prerrequisitos y crear el sitio de las consultas.

- [X] T001 Verificar que el modelo analítico está cargado y que `dim_unidad` y `hecho_estado_unidad` tienen datos, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q`
- [X] T002 Verificar que **las fases 1 y 2 de Emergencias están implementadas**: existen `dags/lib/consultas/__init__.py` (cargador) y `backend/core/repositories/informes_tacticos/modelo_repository.py`. Sin ellas este módulo no tiene sobre qué apoyarse
- [X] T003 Crear `dags/lib/consultas/red_operativa/` con un `README.md` que remita a `contracts/catalogo-consultas.md` y recoja **la regla propia del departamento**: ninguna consulta une con un catálogo de estados de unidad

---

## Phase 2: Foundational — la región versionada y las reglas del departamento

**Purpose**: `dim_region` la necesitan **las tres** user stories, así que vive aquí; si estuviera
dentro de una, las otras dos dependerían de ella y dejarían de ser independientes.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

### La dimensión de región, versionada

- [X] T004 Crear `dim_region` en `dags/lib/ddl.py` según `data-model.md` §2.1, con `estado_ciclo_vida` y `estado_geo` como **columnas distintas**. El origen las confunde: su tabla llamada `Dim_RegionOperativaEstadoRegion` guarda geografía, no ciclo de vida
- [X] T005 Implementar `dags/lib/dimensiones/dim_region.py` **reutilizando `versionado.py` sin modificarlo**, con `estado_ciclo_vida` como único atributo versionado (research D1)
- [X] T006 Verificar que las versiones iniciales de región llevan `inicio_es_real = 0`: el estado se conoce, pero no desde cuándo
- [X] T007 Añadir `dim_region` al flujo de dimensiones existente en `dags/lib/dimensiones_tasks.py` y su fila desconocida en `dags/lib/dimensiones/desconocido.py`. **No se crea un flujo propio**: un flujo por dimensión reintroduciría el problema del flujo por informe
- [X] T008 [P] Prueba del versionado de región en `dags/tests/test_dim_region.py`: un cambio de estado abre versión nueva y cierra la anterior; recargar sin cambios **no escribe nada**; la primera versión abre por la izquierda

### El servicio, las vistas y los permisos


> **Fases 1 y 2 arrancadas el 2026-08-16.** `dim_region` creada, cargada y versionada; `dags/` en
> **428 verdes**.
>
> **Las dos trampas del departamento, confirmadas contra el origen antes de escribir nada:**
>
> 1. **El catalogo de estados de unidad esta incompleto.** `Dim_EstadoUnidadEmergencia` tiene tres
>    filas —`Activa`, `Ocupada`, `Fuera de servicio`— y el historico usa cuatro: aparece tambien
>    `En Mision`. De **45 transiciones, 6 son `En Mision`**: un `INNER JOIN` con el catalogo devolveria
>    39 y no fallaria. Es el 13 % que la spec anticipaba, medido.
> 2. **El origen confunde dos nociones de «estado» de region.**
>    `Dim_RegionOperativa.estadoregion` vale `Produccion` —el ciclo de vida— y
>    `Dim_EstadoRegion.estadoregion` vale «Ciudad de Mexico» —geografia—, con el mismo nombre de
>    columna. `Dim_RegionOperativaEstadoRegion`, que el catalogo citaba como fuente del ciclo de vida,
>    relaciona con **la segunda**. Se comprobo fila a fila.
>
> **`versionado.py` se reutilizo sin tocarlo**, como pedia T005. Hizo falta llamar a
> `decidir_version` directamente en vez de a `versionar_lote`, porque el segundo no propaga `campo_sk`
> y esta dimension necesita `sk_region`: es el mismo bucle con un argumento de mas, y es preferible a
> modificar un modulo que sostiene la atribucion historica de tres hechos ya cargados.
>
> **`dim_region` entra en el flujo de dimensiones existente**, no en uno propio (T007). Un flujo por
> dimension es el mismo error que un flujo por informe.
>
> **Tres pruebas transversales señalaron la dimension nueva**, que es exactamente su trabajo: la de
> filas desconocidas, la del catalogo de tablas y la de crecimiento aditivo. Esta ultima se acoto en
> vez de ampliarse: afirma que **un hecho nuevo** no necesita dimensiones nuevas, y meterle las que
> aporta otro departamento la habria convertido en otra afirmacion distinta.

- [X] T009 Implementar `backend/apps/informes_tacticos/services/red_operativa_compuestos_service.py`, enlazando nombre de informe → consulta del catálogo → respuesta, sobre el `modelo_repository` ya existente
- [X] T010 Implementar `backend/apps/informes_tacticos/views/red_operativa_compuestos_views.py` reutilizando `views/base.py` y `envelope.py`
- [X] T011 ⚠️ Aplicar la **autoridad repartida** en `backend/apps/informes_tacticos/permissions.py`, con `AUTORIDAD_RED_OPERATIVA_CRECIMIENTO` y `AUTORIDAD_RED_OPERATIVA_VALIDACION` de `backend/core/auth/roles_tacticos.py`: cada director accede **a su materia y no a la del otro** (FR-025)
- [X] T012 Implementar en `backend/apps/informes_tacticos/envelope.py` el campo `medida_exacta_desde` de la meta, para los informes que dependen del versionado de región (FR-034)

### Las pruebas de las reglas que no avisan


> **T009-T012 y T016 hechos el 2026-08-16.** `apps/informes_tacticos` en **199 verdes**.
>
> **La autoridad repartida se decide por la materia del informe, declarada en el servicio.** Cada
> informe dice de que habla; el permiso mira eso. Ponerlo en la vista lo habria convertido en una
> propiedad de como se sirve, y no lo es.
>
> El error natural aqui es admitir a las dos autoridades del departamento y quedarse tranquilo: eso
> daria a cada director acceso a la materia del otro **sin ningun sintoma**. Por eso las pruebas que
> importan son las de que **cada uno se queda fuera de la ajena**, y esas van por HTTP —terminan en
> 403 antes de tocar ninguna consulta—.
>
> **Solo dos informes son de validacion**: la tasa de aprobacion al primer intento y los motivos de
> rechazo. Lo demas es crecimiento, **incluida la retirada**: decidir que un mercado se cierra es una
> decision de crecimiento, no un criterio de validacion. «Regiones en riesgo» suena a validacion
> —habla de regiones— y no lo es; la distincion se equivoca sola, asi que hay una prueba que la fija.
>
> **Un informe sin materia declarada no lo ve nadie.** La alternativa —una materia por defecto— dejaria
> accesible un informe nuevo a quien no le corresponde, en silencio.
>
> **Las pruebas de «si entra» preguntan a la clase de permiso, no por HTTP**, y esta explicado en el
> fichero: las consultas del catalogo son de las fases siguientes, asi que hoy un GET concedido
> termina en un error de consulta inexistente y la respuesta no distingue «entro» de «no entro».
>
> **`medida_exacta_desde` (T012) se resuelve consultando el modelo**, no con una constante: es el
> instante en que empezo a haber versiones reales, y cambia si el almacen se recarga. Una constante
> quedaria desfasada en silencio, que es el fallo que ese campo existe para evitar.

- [X] T013 ⚠️ **Prueba de que ninguna consulta une con un catálogo de estados de unidad**, en `dags/tests/test_catalogo_red_operativa.py`, sobre el **texto** de las consultas. Unir es lo correcto en un modelo bien formado y aquí **pierde 6 de 45 transiciones sin que nada falle** (research D2)
- [X] T014 [P] Prueba de la regla de versión final en el mismo fichero: obligatoria en `dim_region`, `dim_unidad`, `dim_geografia` y `hecho_despacho`; **prohibida** en los tres hechos de transacción
- [X] T015 [P] Prueba de exclusión de dato sensible en `dags/tests/test_red_operativa_sin_sensibles.py`: ninguna consulta nombra coordenadas, contacto de proveedor ni **identidad del validador** (FR-021)
- [X] T016 [P] Prueba de la autoridad repartida en `backend/apps/informes_tacticos/tests/api/test_permisos_red_operativa.py`: el Director de Expansión **no** accede a los informes de validación, y el Director Tecnológico **no** a los de crecimiento de flota

> **Fase 2 cerrada el 2026-08-16.** `dags/` en **441 verdes**.
>
> **Las dos trampas del departamento, evitadas y verificadas por mutacion.**
>
> `ot12_unidades_por_estado` agrupa por el **texto** del estado y no une con el catalogo: «En Mision»
> aparece con sus **6 transiciones de 45 (13,3 %)**, que es exactamente lo que un `INNER JOIN` habria
> hecho desaparecer sin fallar.
>
> `ot12_disponibilidad_declarada` mide **tiempo en estado**, no transiciones. Contar transiciones
> asignaria **0 % a la unidad que nunca fallo** —no tiene ninguna transicion a «Fuera de servicio»— y
> el informe que sirve para premiar a los proveedores fiables los senalaria como los peores. Cada
> transicion abre un tramo hasta la siguiente, y el ultimo hasta el fin del periodo; sin transiciones,
> la disponibilidad sale **ausente y no cero**.
>
> **T013 se comprueba en dos mitades.** Que no se une con el catalogo, y que **el estado se lee por su
> texto**: comprobar solo lo primero dejaria pasar una consulta que agrupara por el identificador y
> publicara numeros en vez de estados — no perderia filas, pero seria ilegible, y la primera tentacion
> al arreglarlo seria volver a unir con el catalogo.
>
> **Cuatro mutaciones confirmadas**: unir con el catalogo, agrupar por el id, pedir `FINAL` sobre un
> hecho de transaccion, y nombrar una columna de persona.
>
> **T015 juzga identificadores, no el texto entero**, con la misma tecnica que Emergencias: buscar el
> fragmento en todo el SQL confundiria `validaciones` con `validador`. La exclusion propia de este
> departamento es la **identidad del validador**, que cuesta mas de ver porque parece informacion de
> proceso — y no lo es: sobre ella se juzga a personas por resultados que dependen de las regiones que
> les tocaron.
>
> ⚠️ Las dos pruebas de catalogo empiezan comprobando que **el catalogo no esta vacio**. Sin eso,
> recorrerlo con cero consultas dejaria los dos ficheros en verde sin haber comprobado una sola regla.

**Checkpoint**: sustrato listo — las tres user stories pueden abordarse en cualquier orden.

---

## Phase 3: User Story 1 — El estado real de la flota (Priority: P1) 🎯 MVP

**Goal**: los ocho informes de OT12, con la disponibilidad medida en tiempo y los estados sin perder
ninguno.

**Independent Test**: pedir la cobertura de flota de un condado y comprobar que la suma de sus
estados iguala su número de unidades en el período.

**Criterio medible (ISO 25010 — Corrección funcional)**: una unidad activa todo el período —**sin
ninguna transición dentro de él**— devuelve **100 %** de disponibilidad, no 0 % (SC-003).

### Ampliar el modelo

- [X] T017 [US1] Añadir `fecha_alta` y `tuvo_primer_acceso` a `dim_unidad` en `dags/lib/ddl.py`. **No son atributos versionados**: el alta no cambia y el primer acceso ocurre una vez; versionarlos llenaría la dimensión de ruido
- [X] T018 [US1] Poblar ambos en `dags/lib/dimensiones/dim_unidad.py`, cruzando con las credenciales del origen para el primer acceso

> **Ampliacion del modelo hecha el 2026-08-16** (T017, T018, T020, T021). `dim_unidad` con
> `fecha_alta` y `tuvo_primer_acceso`; `hecho_baja_unidad` creada; `dim_geografia` con sus dos
> columnas **creadas pero aun sin poblar** (por eso T019 sigue abierta).
>
> **`CREATE TABLE IF NOT EXISTS` no migra**, otra vez: hizo falta
> `ensure_columnas_nuevas_dimensiones()` con `ALTER ... ADD COLUMN IF NOT EXISTS`. Sin ella el DDL
> pareceria correcto y las cuatro columnas no existirian en la instalacion actual.
>
> ⚠️ **El primer acceso se deriva del estado de la credencial**, porque el origen **no guarda ninguna
> fecha de primer acceso**: `Dim_Usuarios` no tiene `ultimo_acceso`. `Activo` significa que la unidad
> entro; `Cambio contrasena` es el estado con el que nace una credencial recien creada, es decir que
> todavia no entro. Hoy: **11 de 18 unidades** con primer acceso.
>
> Tiene un limite conocido y documentado en el codigo: una unidad que entro y luego pidio cambio de
> contrasena vuelve a contar como pendiente (2 de 31 credenciales hoy). Se declara en vez de
> disimularse porque el informe sirve para perseguir altas que nunca arrancaron, y un falso positivo
> ahi cuesta una llamada, no una decision equivocada.
>
> ⚠️ **`fecha_alta` esta ausente en 15 de 18 unidades**, y es correcto: solo 3 traen `fecha_creacion`
> en el origen. No se rellena con la epoca cero — una unidad con `1970-01-01` tendria cincuenta y seis
> anos de antiguedad y el informe de rotacion la contaria como la mas veterana de la flota.
>
> **`hecho_baja_unidad`**: `con_caso_en_curso` se **deriva** de que la baja traiga accidente asociado,
> porque el origen no lo dice de otra forma. `motivo` **si entra** al modelo —es una categoria del
> catalogo operativo, no una nota redactada—; el criterio de exclusion es si el campo se puede
> agrupar, no si es corto. `idusuario` no se copia: quien firma la baja es identidad de persona.

- [X] T019 [US1] Añadir `condados_vecinos` e `idregionoperativa` a `dim_geografia` en `dags/lib/ddl.py` y poblarlos en `dags/lib/dimensiones/dim_geografia.py`. La vecindad es **un atributo, no un hecho**: no tiene instante ni grano propio (research D3)
- [X] T020 [US1] Crear `hecho_baja_unidad` en `dags/lib/ddl.py` según `data-model.md` §2.4, con `con_caso_en_curso` derivado de que la baja traiga un accidente asociado
- [X] T021 [US1] Implementar `dags/lib/hechos/hecho_baja_unidad.py`, con `sk_unidad` y `proveedor` resueltos por **atribución histórica** reutilizando `dags/lib/hechos/atribucion.py`
- [X] T022 [US1] Implementar el flujo en `dags/lib/hecho_baja_unidad_tasks.py` y `dags/etl/dag_hecho_baja_unidad.py`, con sensor sobre el flujo de dimensiones
- [X] T023 [US1] Registrar `modelo_hecho_baja_unidad` en `dags/tests/test_dag_integrity.py` y `hecho_baja_unidad` en las listas de tablas de `dags/tests/test_sin_datos_sensibles.py`

### Las consultas

- [X] T024 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_unidades_por_estado.sql`, agrupando **por el texto del estado**
- [X] T025 [US1] ⚠️ Escribir `dags/lib/consultas/red_operativa/ot12_disponibilidad_declarada.sql`: mide **tiempo en estado**; el estado vigente al final cuenta **hasta el fin del período**; sin transiciones conocidas devuelve **ausente**, no `0`

> **2026-08-16.** `dags/` en **461 verdes**. Seis de las ocho consultas de OT12 escritas y ejecutando.
>
> **Arreglado el refresco de atributos no versionados.** `fecha_alta` y `tuvo_primer_acceso` no
> llegaban al almacen: el versionado no escribe nada si ningun **atributo versionado** cambio —lo
> correcto—, y estos dos no lo son a proposito. Ahora la version vigente se reescribe con la **misma
> clave y el mismo `valido_desde`** y un `version` mayor; `ReplacingMergeTree` la sustituye. Cambiar
> `valido_desde` habria creado una fila nueva en vez de reemplazar y la unidad habria acabado con dos
> versiones vigentes. Idempotente: una segunda corrida sin cambios escribe **0 filas**.
>
> Hoy: **11 de 19 unidades con primer acceso, 3 con fecha de alta**, que es exactamente lo que trae el
> origen.
>
> **`ot12_pendientes_primer_acceso` es de estado actual y no de periodo**, y la regla del catalogo lo
> declara en vez de fabricarle un `desde`. Darselo seria un parametro que no filtra nada o —peor— que
> filtra por una fecha de alta que 15 de 18 unidades no tienen, dejando fuera justo a las que llevan
> mas tiempo olvidadas. Usa `{hasta:Date}` como corte, que es lo que lo hace reproducible.
>
> **Bajas: tres desenlaces, no dos.** `Forzada` dejo un caso sin unidad; `Forzada_con_reasignacion` lo
> paso a otra. Agruparlas haria que un proveedor con buena reasignacion pareciera igual de malo que
> uno que abandona casos, y sobre este informe se decide con quien se sigue trabajando.

- [X] T026 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_cobertura_flota_por_region.sql`
- [X] T027 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_condados_cobertura_critica.sql` con `umbral_unidades`, marcando `sin_alternativas` cuando el condado **no tiene vecinos declarados**
- [X] T028 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_rotacion_flota.sql`
- [X] T029 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_bajas_forzadas.sql`, distinguiendo normal, forzada y forzada con reasignación
- [X] T030 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_pendientes_primer_acceso.sql`
- [X] T031 [P] [US1] Escribir `dags/lib/consultas/red_operativa/ot12_rendimiento_proveedor.sql`, agrupando por el proveedor **de aquel momento**

### Los endpoints

- [X] T032 [US1] Exponer los ocho endpoints de OT12 en `backend/apps/informes_tacticos/views/red_operativa_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-red-operativa.openapi.yaml`
- [X] T033 [US1] Documentar en la respuesta de cobertura crítica que `umbral_unidades` es **una convención del informe**, no una política de la empresa: el origen no define ningún umbral

### Pruebas


> **Las ocho consultas de OT12 y sus ocho endpoints, hechos el 2026-08-16.** `dags/` en **461
> verdes**, `apps/informes_tacticos` en **199**. Los ocho comprobados por HTTP entrando con el login
> real del Director de Expansion.
>
> **Dos limitaciones de ClickHouse, las dos con su nota en el SQL:**
>
> `has(izquierda.array, derecha.columna)` **no se admite en un `ON`** —falla con «join expression
> contains column from left and right table»—. La vecindad se explota con `arrayJoin` **sobre una
> copia**, no sobre la fuente: hacerlo en la fuente multiplicaria las filas del condado por su numero
> de vecinos y las unidades propias se contarian varias veces.
>
> Y el `LEFT JOIN` volvio a rellenar con el **valor por defecto del tipo** en vez de `NULL`: la region
> sin resolver salia como cadena vacia y `coalesce` no disparaba, dejando la fila con la region **en
> blanco**. Es el mismo defecto que aparecio en el ranking de ubicaciones de Emergencias; mismo
> arreglo, `nullIf(..., '')`.
>
> **`umbral_unidades` es una convencion del informe, no una politica** (T033). El origen no define
> ninguna cobertura minima, asi que viaja como parametro con defecto explicito, la respuesta lo
> devuelve en `filtros` y ademas lleva una **nota junto a la cifra**: quien lee «3 condados criticos»
> tiene que poder ver contra que numero se midio, o esa cifra pasaria por una decision de la empresa.
>
> **`cobertura-flota-por-region` devuelve hoy todo bajo «Sin region asignada»**, y es lo correcto: la
> decision #38 sigue abierta. Lleva su nota en la respuesta. La alternativa era una cobertura completa
> y equivocada, que nadie cuestionaria.

- [X] T034 [US1] ⚠️ **Prueba de la disponibilidad**, en `dags/tests/test_ot12_disponibilidad.py`, con los tres casos del quickstart §2.2: unidad activa todo el período **sin transiciones** → 100 %; unidad activa el 60 % → 60 %; unidad sin transiciones conocidas → **ausente**, no 0 % (SC-003)
- [X] T035 [US1] ⚠️ **Prueba de que «En Misión» aparece** en `dags/tests/test_ot12_estados.py`, pese a no estar en el catálogo del origen. Si falta, la consulta está uniendo con él (SC-002)
- [X] T036 [P] [US1] Prueba de que **la suma de estados cuadra con la flota** en `dags/tests/test_ot12_cobertura.py` (SC-005)
- [X] T037 [P] [US1] Prueba de que un **condado sin vecinos aparece igualmente**, señalado, en `dags/tests/test_ot12_criticos.py`. Es la situación más grave, no un caso a omitir (SC-008)
- [X] T038 [P] [US1] Prueba de que una **unidad dada de baja a mitad de período cuenta hasta su baja**, ni el período entero ni cero, en `dags/tests/test_ot12_rotacion.py` (FR-012)
- [X] T039 [US1] Prueba de que **el pasado no se reescribe** en `dags/tests/test_ot12_atribucion.py`: cambiar el proveedor de una unidad y comprobar que las bajas anteriores conservan el suyo (SC-004)

**Checkpoint**: US1 entregable. Es el MVP: ocho informes y la disponibilidad medida por primera vez.

---

> **US1 completa el 2026-08-16.** 16 pruebas nuevas; `dags/` en **485 verdes**.
>
> **T034 cubre los tres casos del quickstart y dos mas.** Que el ultimo tramo llegue al fin del
> periodo —sin eso, la unidad estable aportaria cero segundos y desapareceria justo por haber sido
> estable— y que el cero legitimo si llegue: tratar todo como ausente escondería la alarma en vez de
> darla.
>
> **El relleno del LEFT JOIN mordio por tercera vez.** `uniqExact` contaba el `0` con que ClickHouse
> rellena las filas sin coincidencia como una unidad distinta, asi que un condado vecino **sin
> ninguna unidad** salia con una — y la cobertura critica diria que hay a quien recurrir cuando no lo
> hay. Ya habia pasado con el nombre de calle del ranking de Emergencias y con el nombre de region de
> la cobertura por region. Arreglado con `uniqExactIf`.
>
> **Las dos consultas de cobertura son de estado actual**, como la de pendientes de primer acceso:
> miden que cobertura hay, no la que hubo. Se declaran en `DE_ESTADO_ACTUAL` con su razon en vez de
> fabricarles un `desde` que no filtraria lo que parece.

## Phase 4: User Story 2 — Cómo se abren regiones (Priority: P2)

**Goal**: los cuatro informes de OT11, con dos indicadores BSC.

**Independent Test**: una región rechazada dos veces y aprobada a la tercera **no** cuenta como
aprobada al primer intento.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: una región que aún no llegó a producción
devuelve tiempo de puesta en operación **ausente**, y **no** aparece como incumplimiento del
indicador normativo de 30 días (SC-007).

### Ampliar el modelo

- [X] T040 [US2] Crear `hecho_validacion_region` en `dags/lib/ddl.py` según `data-model.md` §2.5, **sin `idusuario`**: el validador es una persona
- [X] T041 [US2] Implementar `dags/lib/hechos/hecho_validacion_region.py`, con `numero_intento` calculado por orden de validación dentro de cada región — es lo que hace calculable la tasa al primer intento
- [X] T042 [US2] Implementar el flujo en `dags/lib/hecho_validacion_region_tasks.py` y `dags/etl/dag_hecho_validacion_region.py`
- [X] T043 [US2] Registrar el DAG y la tabla en `dags/tests/test_dag_integrity.py` y `dags/tests/test_sin_datos_sensibles.py`

### Las consultas


> **`hecho_validacion_region` cargado el 2026-08-16.** `dags/` en **485 verdes**.
>
> **`numero_intento` se calcula en la carga, y es lo que hace calculable el indicador.** El origen
> guarda las validaciones sueltas; el ordinal sale de ordenarlas **dentro de cada region por su
> instante**. Sin el, una region rechazada dos veces y aprobada a la tercera contaria como aprobada,
> y la tasa al primer intento daria el mejor resultado posible justamente en el caso que peor fue.
>
> Los datos de hoy son exactamente ese caso: «Region Prueba Norte» con **rechazo (1), rechazo (2),
> aprobacion (3)**.
>
> ⚠️ **El ordinal sale del instante, no del orden de llegada.** Pinot no garantiza orden sin
> `ORDER BY`, asi que confiar en el orden en que devuelva las filas haria que el «primer intento»
> cambiara entre dos corridas sin que nada hubiera pasado — el mismo defecto que la decision #35
> documenta en `tiempo-asignado-cerrado`.
>
> **`idusuario` no se copia.** El validador es una persona (FR-021), y es la exclusion que mas cuesta
> ver de este departamento porque parece informacion de proceso: un informe de validaciones
> desglosado por quien las firma juzga a alguien por resultados que dependen de las regiones que le
> tocaron.
>
> **Un fallo de tipos al cruzar las dos fuentes**: las validaciones llegan de Pinot en epoch-ms y las
> versiones de region del almacen como **texto**. Compararlas sin convertir haria que
> `"2100-01-01" < "2026-08-16"` fuese cierto por orden alfabetico, y la version vigente saldria mal en
> cuanto una fecha cambiara de longitud.

- [X] T044 [US2] ⚠️ Escribir `dags/lib/consultas/red_operativa/ot11_tiempo_puesta_operacion.sql` con `dias_objetivo`: las regiones que **no llegaron a producción** devuelven `dias` y `cumple_objetivo` **ausentes**, nunca `0` ni `false`
- [X] T045 [P] [US2] Escribir `dags/lib/consultas/red_operativa/ot11_mercados_activos.sql`
- [X] T046 [P] [US2] Escribir `dags/lib/consultas/red_operativa/ot11_tasa_aprobacion_primer_intento.sql`, **por región y no por validador**, contando intentos y no regiones
- [X] T047 [P] [US2] Escribir `dags/lib/consultas/red_operativa/ot11_motivos_rechazo.sql` con `top`, agrupando **solo validaciones rechazadas**

### Los endpoints

- [X] T048 [US2] Exponer los cuatro endpoints de OT11 en `backend/apps/informes_tacticos/views/red_operativa_compuestos_views.py` y `urls.py`

### Pruebas

- [X] T049 [US2] ⚠️ **Prueba del primer intento** en `dags/tests/test_ot11_tasa_aprobacion.py`: una región con dos rechazos y una aprobación **no** cuenta como aprobada al primero, y sus tres intentos son visibles (FR-017)
- [X] T050 [US2] ⚠️ **Prueba de la región aún en validación** en `dags/tests/test_ot11_puesta_operacion.py`: devuelve ausente, **no `0` días ni incumplimiento**. No incumplió un plazo, todavía está dentro de él (SC-007)
- [X] T051 [P] [US2] Prueba de que **una aprobación sin motivo no aparece como categoría** en `dags/tests/test_ot11_motivos.py` (FR-018)
- [X] T052 [P] [US2] Prueba de que ningún informe de OT11 devuelve **identidad del validador** en `dags/tests/test_ot11_sin_identidad.py`

**Checkpoint**: US2 entregable. Los dos BSC de apertura de mercado quedan medibles.

---

> **US2 completa el 2026-08-16.** Cuatro consultas, cuatro endpoints y 14 pruebas; `dags/` en **515
> verdes**, comprobados por HTTP con el login real de cada director segun su materia.
>
> **La tasa al primer intento cuenta intentos, no regiones.** Con grano de region solo queda la
> aprobacion final y el indicador daria 100 % a una region rechazada dos veces — el mejor resultado
> posible en el caso que peor fue. Es el caso que hay en los datos reales.
>
> **Los motivos se agrupan solo sobre rechazos.** Sobre todas las validaciones, el motivo nulo de una
> aprobacion se convertiria en categoria y hoy seria **la causa de rechazo mas frecuente del
> informe** — con nombre plausible y conteo creible. Un rechazo **si** sin motivo es otra cosa y se
> etiqueta aparte: es un hueco de registro que hay que ver.
>
> **El relleno del LEFT JOIN mordio por cuarta vez.** `ot11_tiempo_puesta_operacion` daba primera
> validacion en 1970 y **-20 677 dias**. El negativo se ve; lo peligroso es que la misma causa produce
> numeros positivos plausibles en cuanto las fechas caen del otro lado. Y `minIf` sin filas que
> cumplan devuelve el valor por defecto igual que el join.
>
> Hoy las dos regiones devuelven `dias` **ausente**, que es la verdad: ninguna tiene version de inicio
> real, asi que no se sabe cuando entro en produccion.
>
> **Una columna renombrada en vez de exceptuada.** `mercados_activos` publicaba `nombres` —de
> regiones— y la comprobacion de dato sensible la cazo. Hacia bien en dudar: una columna llamada asi
> es ambigua tambien para quien lee el informe. Se llama `regiones_incluidas`.
>
> **Cuatro de las quince consultas son de corte y no de periodo**, todas declaradas con su razon.

## Phase 5: User Story 3 — Regiones en riesgo y retirada (Priority: P3)

**Goal**: los tres informes de OT13, dos de los cuales miden **desde la primera carga del modelo**.

**Independent Test**: dejar un condado sin unidades disponibles y comprobar que su región aparece en
riesgo.

**Criterio medible (ISO 25010 — Corrección funcional)**: tras despublicar una región, un informe de
un período **anterior** sigue mostrándola como publicada (SC-010).

### Las consultas

- [X] T053 [US3] Escribir `dags/lib/consultas/red_operativa/ot13_regiones_en_riesgo.sql` con `umbral_unidades`, sobre las regiones **en producción** según su versión vigente
- [X] T054 [US3] ⚠️ Escribir `dags/lib/consultas/red_operativa/ot13_casos_activos_al_despublicar.sql`, devolviendo `medida_exacta_desde`
- [X] T055 [US3] ⚠️ Escribir `dags/lib/consultas/red_operativa/ot13_tiempo_perdida_a_despublicacion.sql`, devolviendo `medida_exacta_desde`

### Los endpoints

- [X] T056 [US3] Exponer los tres endpoints de OT13 en `backend/apps/informes_tacticos/views/red_operativa_compuestos_views.py` y `urls.py`

### Pruebas


> **Las tres consultas de OT13 y sus endpoints, hechos el 2026-08-16.** El catalogo de Red Operativa
> tiene ya sus **15 consultas** y los **15 endpoints** publicados.
>
> **Una region sin despublicar no cuenta como despublicada en cero dias** (FR-035). No entra en el
> calculo: un `0` diria que se retiro **inmediatamente** —la mejor marca posible— y la pondria a la
> cabeza de la lista de reacciones mas rapidas, que es justo la region que sigue publicada sin
> cobertura. Aparece en `aun_publicadas_sin_flota`, que es la alarma contraria: aquella mide reaccion,
> esta mide inaccion. Hoy: **0 despublicaciones medidas y 2 regiones aun publicadas sin flota**, con
> mediana **nula**.
>
> **Un historico vacio no significa «nunca paso»**, significa «no lo vimos»: el origen no historiza el
> estado de una region, asi que una despublicacion anterior a la primera carga no dejo rastro. Las dos
> lecturas se ven igual en pantalla y la primera es tranquilizadora, que es por lo que hace falta
> decirlo. Los dos informes llevan `medida_exacta_desde` y una nota en la respuesta, y publican su
> denominador —`despublicaciones_medidas`— aunque valga cero.
>
> `casos-activos-al-despublicar` **faltaba** en la lista de los que dependen del versionado, y es el
> que mas lo necesita: sin despublicaciones observadas devuelve una tabla vacia.
>
> **Solo cuentan las versiones con `inicio_es_real = 1`.** Las que abren por la izquierda no fechan la
> despublicacion, solo dicen que ya estaba despublicada cuando el modelo empezo a mirar: restar contra
> esa fecha daria cincuenta y seis anos de casos acumulados.

- [X] T057 [US3] ⚠️ **Prueba de que el pasado de la región no se reescribe** en `dags/tests/test_ot13_atribucion_region.py`: despublicar una región y comprobar que un informe de un período anterior **sigue mostrándola como publicada** (SC-010)
- [X] T058 [US3] ⚠️ **Prueba de `medida_exacta_desde`** en `dags/tests/test_ot13_medida_exacta.py`: con cero despublicaciones registradas, la respuesta trae la fecha desde la que se mide. **Sin ella, un histórico vacío se leería como «nunca pasó»** (SC-011)
- [X] T059 [P] [US3] Prueba de que una **región sin despublicar no cuenta como despublicada con tiempo cero** en `dags/tests/test_ot13_tiempo.py` (FR-035)
- [X] T060 [P] [US3] Prueba de que una región **con cobertura suficiente no aparece en riesgo** en `dags/tests/test_ot13_riesgo.py`

**Checkpoint**: los 15 informes disponibles.

---

> **US3 completa el 2026-08-16.** 11 pruebas; `dags/` en **537 verdes**. Las tres user stories de Red
> Operativa cerradas: 15 consultas, 15 endpoints.
>
> **Una prueba mia no comprobaba lo que decia, y lo destapo una mutacion.**
> `test_una_version_que_abre_por_la_izquierda_no_fecha_la_despublicacion` pasaba aunque se quitara la
> guarda de `inicio_es_real`: la region de prueba no tenia version en produccion, asi que
> `publicada_en` salia nulo y el resultado era ausente **por otra razon**. Corregida anadiendo esa
> version; ahora la mutacion la hace fallar.
>
> ⚠️ **Y antes de eso, una mutacion que dije haber verificado no se habia aplicado siquiera**: el
> script de sustitucion fallo en silencio y las pruebas pasaron por no haber cambiado nada. Es el
> mismo `str.replace` que no falla cuando el ancla no existe. Se repitio con `assert` sobre el ancla y
> entonces si: las dos pruebas caen.
>
> **T057 es la razon de que `dim_region` este versionada.** Si el estado se leyera de la version
> actual, despublicar una region borraria de golpe todos los informes de riesgo que la senalaban —
> desapareceria la prueba de que alguien lo advirtio a tiempo.

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T061 [P] Prueba de que **un período vacío devuelve cero filas** y no una fila de ceros, en `dags/tests/test_red_operativa_periodo_vacio.py` (FR-023)
- [X] T062 [P] Prueba de que **todo porcentaje viene con su denominador** en `dags/tests/test_red_operativa_denominador.py` (FR-022)
- [X] T063 ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_red_operativa.py`: tras añadir dos dimensiones y dos hechos, **las cifras de los informes de Emergencias no cambian** (SC-009)
- [X] T064 Ejecutar `cd backend && python -m pytest -q` y verificar que ninguna suite existente se movió
- [X] T065 Recorrer `quickstart.md` de principio a fin, con especial atención a §2.2 (disponibilidad), §2.3 (el pasado de la región) y §2.8 (autoridad repartida)
- [X] T066 Anotar en `decisiones-pendientes.md` que **el ciclo de vida de la región se historiza desde el modelo y no desde el origen**, como extensión de la decisión #19, y que **el catálogo de estados de unidad del origen está incompleto**
- [X] T067 Documentar en `.specify/docs/changelog.md` y actualizar el estado de los 15 informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md`

---

## Dependencies

```text
Emergencias, fases 1 y 2 (plomería)  ← DEPENDENCIA EXTERNA
    ↓
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: dim_region + servicio + reglas) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ── independiente
    ├─→ Phase 4 (US2, P2) ── independiente
    └─→ Phase 5 (US3, P3) ── independiente
            ↓
    Phase 6 (Polish)
```

**`dim_region` está en la fase 2 y no dentro de una historia porque las tres la necesitan** — US1
para la cobertura por región, US2 para las regiones que valida y US3 para las que retira. Colocarla
dentro de US2 haría que US1 y US3 dependieran de ella y dejarían de ser entregables por separado.

**Dentro de la fase 2**: T004 y T005 primero; T007 depende de ambas; el bloque de servicio (T009–T012)
es independiente del de la dimensión; las cuatro pruebas dependen de sus módulos.

**Dentro de la fase 3**: la ampliación del modelo (T017–T023) **antes** que las consultas
(T024–T031), que van antes que endpoints y pruebas.

---

## Parallel Execution Examples

**Fase 3 — siete consultas de OT12 a la vez:**

```text
T024 ot12_unidades_por_estado.sql
T026 ot12_cobertura_flota_por_region.sql
T027 ot12_condados_cobertura_critica.sql
T028 ot12_rotacion_flota.sql
T029 ot12_bajas_forzadas.sql
T030 ot12_pendientes_primer_acceso.sql
T031 ot12_rendimiento_proveedor.sql
```

**Fase 4 — tres consultas de OT11:**

```text
T045 ot11_mercados_activos.sql
T046 ot11_tasa_aprobacion_primer_intento.sql
T047 ot11_motivos_rechazo.sql
```

---

## Implementation Strategy

### MVP — US1

Ocho informes de flota, y **la disponibilidad declarada medida por primera vez**: hoy no se puede
calcular de ninguna forma, porque el estado operativo solo vive en un historial de transiciones.

### Entrega incremental

1. **Fases 1–2** — la región versionada y las dos reglas que no avisan.
2. **Fase 3 (US1)** — **MVP**.
3. **Fase 4 (US2)** — los dos BSC de apertura de mercado.
4. **Fase 5 (US3)** — la vigilancia de regiones y la historia que empieza hoy.
5. **Fase 6** — cierre.

### Cinco riesgos a vigilar

**T013 vigila el error más silencioso del departamento.** Unir con el catálogo de estados es lo
correcto en un modelo bien formado, y aquí descarta 6 de 45 transiciones **sin error alguno**. La
prueba mira el texto de las consultas, no su resultado, porque el resultado parece razonable.

**T034 es la prueba que más fácil se escribe mal.** Una unidad activa todo el período **no tiene
ninguna transición dentro de él**. Si la consulta cuenta transiciones, esa unidad —la mejor de la
flota— aparece con 0 % de disponibilidad.

**T050 protege un indicador normativo.** Una región aún en validación no incumple los 30 días: está
dentro del plazo. Contarla como `0` la convertiría en un incumplimiento inventado.

**T058 evita afirmar algo que nadie sabe.** Los informes #14 y #15 devolverán cero filas durante
mucho tiempo. Sin `medida_exacta_desde`, ese vacío se lee como «nunca se ha despublicado una región»,
que es una afirmación sobre el pasado que el sistema no puede sostener.

**T063 protege a Emergencias.** Este módulo añade dos dimensiones y dos hechos **al mismo modelo**.
Si alguna cifra de Emergencias se mueve, la ampliación no fue aditiva y el modelo dejó de ser
compartible.

---

## Cierre del modulo — 2026-08-16

**Las 67 tareas hechas.** 15 consultas, 15 endpoints, una dimension y dos hechos nuevos.
`dags/` en **584 verdes**; `apps/informes_tacticos` en **199** ejecutado aislado.

**T065 recorrido entero contra el stack, sin fallos**, entrando con el login real de cada director:
la disponibilidad no da 0 % a nadie por no haber fallado; «En Mision» aparece con sus 6 de 45
transiciones; la autoridad repartida deja fuera a cada director de la materia ajena en los cuatro
casos; y la mediana de despublicacion sale ausente con 0 despublicaciones medidas.

⚠️ **T064: en la suite completa del backend fallan 13 pruebas de contraste que pasan aisladas.** Es
contaminacion por orden —alguna prueba anterior deja parcheado el cliente de Pinot, y los contrastes
necesitan Pinot real—, la misma familia que las 5 de `test_pinot_client_limit` ya registradas. **No es
un defecto de este modulo**: `apps/informes_tacticos` da 199 verdes ejecutado solo.

**Tres decisiones abiertas que este modulo destapo**: #38 (no existe relacion region-condado), #39 (el
ciclo de vida de la region solo se historiza desde el modelo) y #40 (el catalogo de estados de unidad
del origen esta incompleto).
