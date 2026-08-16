# Tasks: Informes Compuestos de Ventas y CRM sobre el Modelo Analítico

**Input**: Design documents from `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** Este departamento tiene tres formas de equivocarse que **no
fallan**: leer el desenlace de una columna que mezcla éxito con fracaso, medir el embudo dejando
fuera a los prospectos estancados, y contar un aviso ignorado como reacción instantánea. Las tres
devuelven números plausibles.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Es el primero cuyo dominio no toca ninguna tabla del modelo**: hacen falta **dos dimensiones y
cuatro hechos**. No es un defecto del modelo, es lo que cuesta incorporar un dominio entero por
primera vez.

**Y sigue sin crear plomería.** Cargador de consultas, repositorio, período y permisos se reutilizan
tal cual. **⚠️ Depende de las fases 1 y 2 de Emergencias**, no de sus informes.

**Es el departamento con más dato personal del sistema** —prospectos con nombre, correo, teléfono y
cargo— y **nada de eso entra al modelo**.

---

## Phase 1: Setup

- [ ] T001 Verificar que el modelo analítico está cargado, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q`
- [ ] T002 Verificar que **las fases 1 y 2 de Emergencias están implementadas**: existen `dags/lib/consultas/__init__.py` y `backend/core/repositories/informes_tacticos/modelo_repository.py`
- [ ] T003 Crear `dags/lib/consultas/ventas_crm/` con un `README.md` que remita a `contracts/catalogo-consultas.md` y recoja **las dos reglas propias**: ninguna consulta lee `activo`, y ninguna devuelve dato personal

---

## Phase 2: Foundational — el prospecto sin identidad y su desenlace real

**Purpose**: `dim_prospecto` y `dim_canal` las necesitan **las tres** user stories, así que viven
aquí. Y es donde se resuelve, de una vez, el defecto que si no tendrían que esquivar trece consultas.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

### Las dos dimensiones

- [ ] T004 Crear `dim_prospecto` y `dim_canal` en `dags/lib/ddl.py` según `data-model.md` §2.1 y §2.2. ⚠️ **Sin nombres, apellidos, correo, teléfono ni cargo**: es la tabla con más dato personal del sistema y ningún informe del catálogo necesita saber quién es el prospecto
- [ ] T005 ⚠️ Implementar `dags/lib/dimensiones/dim_prospecto.py` con la columna **`desenlace` de tres valores** —convertido, perdido, en_curso— derivada de `motivo_inactividad` y `etapa_actual`. **Nunca de `activo`**, que cubre a la vez convertido y perdido (research D1)
- [ ] T006 Implementar `dags/lib/dimensiones/dim_canal.py`, normalizando el texto libre de `como_nos_conocio`, con su **fila desconocida** para los prospectos sin canal — que **cuentan en los totales**
- [ ] T007 Añadir ambas al flujo existente en `dags/lib/dimensiones_tasks.py` y sus filas desconocidas en `dags/lib/dimensiones/desconocido.py`. **No se crean flujos propios**
- [ ] T008 ⚠️ **Prueba del desenlace** en `dags/tests/test_dim_prospecto.py`: un prospecto convertido y otro perdido —que en el origen comparten `activo = false`— quedan en **grupos distintos**. Si el modelo solo distingue dos grupos, el desenlace salió de la columna equivocada (SC-002)
- [ ] T009 [P] Prueba de que **la dimensión no contiene dato personal** en `dags/tests/test_dim_prospecto_sin_identidad.py`: ninguna columna de nombre, correo, teléfono ni cargo. **No filtradas: inexistentes** (SC-007)

### El servicio, las vistas y los permisos

- [ ] T010 Implementar `backend/apps/informes_tacticos/services/ventas_crm_compuestos_service.py` sobre el `modelo_repository` existente
- [ ] T011 Implementar `backend/apps/informes_tacticos/views/ventas_crm_compuestos_views.py` reutilizando `views/base.py` y `envelope.py`
- [ ] T012 Aplicar los permisos en `backend/apps/informes_tacticos/permissions.py` con `AUTORIDAD_VENTAS_CRM` de `backend/core/auth/roles_tacticos.py`: el **Director de Marketing** sin acotamiento; el **ejecutivo comercial** acotado a sus propios prospectos (FR-033, FR-034)
- [ ] T013 Implementar el campo `acotado_a` de la meta en `backend/apps/informes_tacticos/envelope.py`, para que la respuesta declare cuándo viene acotada

### Las pruebas de las reglas que no avisan

- [ ] T014 ⚠️ **Prueba de que ninguna consulta lee `activo`**, en `dags/tests/test_catalogo_ventas_crm.py`, sobre el **texto** de las consultas. Es el defecto que mezcla éxito con fracaso sin fallar
- [ ] T015 [P] Prueba de que **ninguna consulta nombra un campo personal ni una columna de coste**, en `dags/tests/test_catalogo_ventas_crm.py` (FR-022, FR-027)
- [ ] T016 [P] Prueba de la regla de versión final en `dags/tests/test_catalogo_ventas_crm.py`: obligatoria en las dos dimensiones, **prohibida** en los cuatro hechos, todos de transacción
- [ ] T017 [P] Prueba del acotamiento en `backend/apps/informes_tacticos/tests/api/test_permisos_ventas_crm.py`: un ejecutivo obtiene solo sus prospectos y la meta lo declara (SC-008)

**Checkpoint**: sustrato listo — las tres user stories pueden abordarse en cualquier orden.

---

## Phase 3: User Story 1 — El embudo comercial (Priority: P1) 🎯 MVP

**Goal**: los cinco informes de OT02, que satisfacen **CU-T03**, uno de los dos casos de uso tácticos
que hoy no cubre ningún informe del proyecto.

**Independent Test**: pedir el embudo de un período y comprobar que los prospectos que entran en una
etapa son iguales a los que salen más los que permanecen.

**Criterio medible (ISO 25010 — Corrección funcional)**: un prospecto estancado en una etapa muestra
**la permanencia mayor**, no la menor (SC-004).

### Ampliar el modelo

- [ ] T018 [US1] Crear `hecho_transicion_embudo` y `hecho_asignacion_prospecto` en `dags/lib/ddl.py` según `data-model.md` §2.3 y §2.4. ⚠️ **Sin `notas`**: es texto libre escrito por el ejecutivo
- [ ] T019 [US1] Implementar `dags/lib/hechos/hecho_transicion_embudo.py`, con `es_avance` para distinguir el retroceso de etapa y `segundos_en_etapa_anterior` **ausente en la primera transición** — cero significaría «pasó al instante»
- [ ] T020 [US1] Implementar `dags/lib/hechos/hecho_asignacion_prospecto.py`. ⚠️ **Es el primer historial del proyecto que el origen sí guarda bien**: la atribución es exacta desde el primer día, sin marca de «inicio no real» (research D4)
- [ ] T021 [US1] Implementar el flujo conjunto en `dags/lib/hecho_ciclo_prospecto_tasks.py` y `dags/etl/dag_hecho_ciclo_prospecto.py`: **los dos hechos comparten fuente y se cargan juntos**, no en dos DAGs
- [ ] T022 [US1] Registrar el DAG en `dags/tests/test_dag_integrity.py` y las dos tablas en `dags/tests/test_sin_datos_sensibles.py`

### Las consultas

- [ ] T023 [US1] ⚠️ Escribir `dags/lib/consultas/ventas_crm/ot02_embudo_conversion.sql`: el porcentaje se calcula **sobre transiciones, no sobre prospectos únicos** —un prospecto puede retroceder—, con `denominador` visible
- [ ] T024 [US1] ⚠️ Escribir `dags/lib/consultas/ventas_crm/ot02_permanencia_por_etapa.sql` **incluyendo el tramo abierto**: la etapa vigente al final cuenta hasta el fin del período, y esos prospectos se informan en `abiertos`
- [ ] T025 [P] [US1] Escribir `dags/lib/consultas/ventas_crm/ot02_carga_por_ejecutivo.sql`, atribuyendo al ejecutivo **vigente en el momento medido**
- [ ] T026 [P] [US1] Escribir `dags/lib/consultas/ventas_crm/ot02_pipeline_ponderado.sql` con `pesos_etapa`, devolviendo el peso aplicado para que la cifra sea auditable
- [ ] T027 [P] [US1] Escribir `dags/lib/consultas/ventas_crm/ot02_motivos_perdida.sql`, agrupando **motivo y etapa juntos**

### Los endpoints

- [ ] T028 [US1] Exponer los cinco endpoints de OT02 en `backend/apps/informes_tacticos/views/ventas_crm_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-ventas-crm.openapi.yaml`
- [ ] T029 [US1] Documentar en la respuesta del pipeline ponderado que `pesos_etapa` es **una convención del informe**, no una política: el sistema operativo no define ninguna (FR-020)

### Pruebas

- [ ] T030 [US1] ⚠️ **Prueba del prospecto estancado** en `dags/tests/test_ot02_permanencia.py`: un prospecto semanas en la misma etapa **sin transiciones** muestra la permanencia **mayor** y se cuenta en `abiertos`. Si no aparece, la consulta solo mide etapas abandonadas y **deja fuera a quienes el informe existe para encontrar** (SC-004)
- [ ] T031 [US1] ⚠️ **Prueba de que el embudo cuadra** en `dags/tests/test_ot02_embudo.py`: entran = salen + permanecen, con los retrocesos contados como transición (SC-003)
- [ ] T032 [P] [US1] Prueba de que **la primera transición no tiene duración cero** en `dags/tests/test_ot02_primera_transicion.py`: va ausente, porque no había etapa anterior
- [ ] T033 [P] [US1] Prueba de que **la carga histórica no se reescribe** en `dags/tests/test_ot02_carga.py`: reasignar un prospecto y comprobar que un período anterior devuelve lo mismo (SC-005)
- [ ] T034 [P] [US1] Prueba de que **un motivo de pérdida ausente aparece como «sin motivo registrado»** en `dags/tests/test_ot02_motivos.py`, no como fila descartada (FR-014)

**Checkpoint**: US1 entregable. Es el MVP y satisface CU-T03.

---

## Phase 4: User Story 2 — La captación por canal (Priority: P2)

**Goal**: los tres informes de OT01, que satisfacen **CU-T04**.

**Independent Test**: la suma de prospectos de todos los canales, incluido «Desconocido», es igual al
total del período.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: ningún prospecto se pierde al clasificar por
canal (SC-006).

> **Es la historia más barata del módulo**: no necesita ninguna tabla nueva. Todo lo que usa
> —`dim_prospecto` con su desenlace y `dim_canal` con su fila desconocida— ya está en la fase 2.

### Las consultas

- [ ] T035 [P] [US2] Escribir `dags/lib/consultas/ventas_crm/ot01_captacion_por_canal.sql`, con los prospectos sin canal bajo `Desconocido` **sumando en los totales**
- [ ] T036 [P] [US2] Escribir `dags/lib/consultas/ventas_crm/ot01_conversion_por_canal.sql`, leyendo `desenlace` y **nunca `activo`**; un canal sin prospectos devuelve **sin dato**, no 0 %
- [ ] T037 [US2] ⚠️ Escribir `dags/lib/consultas/ventas_crm/ot01_convertidos_por_canal.sql` **sin ninguna columna de coste, ni vacía**, y con `nota_indicador` declarando que es la parte medible del CAC (FR-021 a FR-023)

### Los endpoints

- [ ] T038 [US2] Exponer los tres endpoints de OT01 en `backend/apps/informes_tacticos/views/ventas_crm_compuestos_views.py` y `urls.py`

### Pruebas

- [ ] T039 [US2] ⚠️ **Prueba de que el informe de convertidos no trae coste** en `dags/tests/test_ot01_sin_coste.py`: ninguna clave `coste`, `importe` ni `inversion`, **ni siquiera nula**. Una columna vacía invita a rellenarla desde fuera, y el tablero mostraría un CAC que el sistema no sostiene (FR-022)
- [ ] T040 [P] [US2] Prueba de que **los canales suman el total** en `dags/tests/test_ot01_canales.py`, con `Desconocido` incluido (SC-006)
- [ ] T041 [P] [US2] Prueba de que un **canal sin prospectos devuelve sin dato** y no 0 % en `dags/tests/test_ot01_conversion.py` (FR-020)
- [ ] T042 [P] [US2] Prueba de que la conversión por canal **usa `desenlace`** en `dags/tests/test_ot01_desenlace.py`: un prospecto perdido no cuenta como convertido pese a compartir estado de actividad con uno que sí lo hizo

**Checkpoint**: US2 entregable. Con US1, quedan cubiertos **los dos casos de uso tácticos ausentes**.

---

## Phase 5: User Story 3 — La nutrición del prospecto (Priority: P3)

**Goal**: los cinco informes de OT03.

**Independent Test**: con interacciones sintéticas, la efectividad de la nutrición distingue
prospectos con demo de prospectos sin demo, cada grupo con su denominador.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: los informes distinguen «no hubo demos» de
«hubo demos y no se usaron» (SC-009).

> ⚠️ **Sus dos fuentes tienen 0 filas.** Pero el diagnóstico es de **entorno, no de diseño**: ambos
> repositorios publican a Kafka —comprobado en el código—, así que funcionarán en cuanto haya demos.
> **Las pruebas van con datos sintéticos**: con la fuente vacía, una consulta rota y un origen vacío
> devuelven lo mismo.

### Ampliar el modelo

- [ ] T043 [US3] Crear `hecho_interaccion_demo` y `hecho_notificacion_ventas` en `dags/lib/ddl.py` según `data-model.md` §2.5 y §2.6. ⚠️ **Sin `metadata`** —campo libre— y **sin `estado_envio`**, que ningún código escribe
- [ ] T044 [US3] Implementar `dags/lib/hechos/hecho_interaccion_demo.py`
- [ ] T045 [US3] ⚠️ Implementar `dags/lib/hechos/hecho_notificacion_ventas.py`, con `hubo_avance` y `segundos_a_reaccion` **ausente cuando no hubo reacción**. No es una reacción instantánea: es que no la hubo
- [ ] T046 [US3] Implementar el flujo conjunto en `dags/lib/hecho_nutricion_tasks.py` y `dags/etl/dag_hecho_nutricion.py`: los dos hechos se cargan juntos
- [ ] T047 [US3] Registrar el DAG y las dos tablas en `dags/tests/test_dag_integrity.py` y `dags/tests/test_sin_datos_sensibles.py`

### Las consultas

- [ ] T048 [P] [US3] Escribir `dags/lib/consultas/ventas_crm/ot03_intensidad_demo.sql`
- [ ] T049 [P] [US3] Escribir `dags/lib/consultas/ventas_crm/ot03_secciones_visitadas.sql` con `top`
- [ ] T050 [P] [US3] Escribir `dags/lib/consultas/ventas_crm/ot03_efectividad_nutricion.sql`, devolviendo **dos filas** —con demo y sin demo—, cada una con su denominador
- [ ] T051 [US3] ⚠️ Escribir `dags/lib/consultas/ventas_crm/ot03_latencia_reaccion.sql`: los avisos **sin reacción** se cuentan en `sin_reaccion` y **quedan fuera de la mediana**
- [ ] T052 [P] [US3] Escribir `dags/lib/consultas/ventas_crm/ot03_reglas_disparo.sql`

### Los endpoints

- [ ] T053 [US3] Exponer los cinco endpoints de OT03 en `backend/apps/informes_tacticos/views/ventas_crm_compuestos_views.py` y `urls.py`

### Pruebas

- [ ] T054 [US3] ⚠️ **Prueba de que un aviso ignorado no mejora la latencia** en `dags/tests/test_ot03_latencia.py`, con datos sintéticos: una notificación sin ningún avance posterior queda **fuera de la mediana**. Contada como cero, **los avisos ignorados mejorarían el indicador** — al revés de la realidad
- [ ] T055 [US3] ⚠️ **Prueba de «no hubo» frente a «hubo y no se usó»** en `dags/tests/test_ot03_vacio.py`: sin demos devuelve `data: []`; con demos sin interacciones devuelve filas en cero. Son conclusiones opuestas sobre el producto (SC-009)
- [ ] T056 [P] [US3] Prueba de la efectividad de la nutrición en `dags/tests/test_ot03_efectividad.py`: dos grupos, **cada uno con su denominador** (FR-024)
- [ ] T057 [P] [US3] Prueba de que ningún informe de OT03 devuelve **identidad del prospecto** en `dags/tests/test_ot03_sin_identidad.py`

**Checkpoint**: los 13 informes disponibles.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T058 [P] Prueba de que **todo porcentaje viene con su denominador** en `dags/tests/test_ventas_crm_denominador.py` (FR-030)
- [ ] T059 [P] Prueba de que **un período vacío devuelve cero filas** y no una fila de ceros, en `dags/tests/test_ventas_crm_periodo_vacio.py` (FR-031)
- [ ] T060 ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_ventas_crm.py`: tras añadir dos dimensiones y cuatro hechos, **las cifras de Emergencias y Red Operativa no cambian** (SC-010)
- [ ] T061 Ejecutar `cd backend && python -m pytest -q` y verificar que ninguna suite existente se movió
- [ ] T062 Recorrer `quickstart.md` de principio a fin, con especial atención a §2.1 (convertido ≠ perdido), §2.2 (el estancado) y §2.7 (sin coste)
- [ ] T063 Anotar en `decisiones-pendientes.md` que **el coste por canal no existe en el sistema**, que el informe entrega solo la parte medible del BSC de adquisición, y que **`Dim_Prospecto.activo` mezcla convertido con perdido** en la capa operativa
- [ ] T064 Documentar en `.specify/docs/changelog.md` y actualizar el estado de los 13 informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md`, **anotando allí el defecto de `activo`** para que otros departamentos no lo repitan

---

## Dependencies

```text
Emergencias, fases 1 y 2 (plomería)  ← DEPENDENCIA EXTERNA
    ↓
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: dim_prospecto + dim_canal + servicio + reglas) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ── independiente
    ├─→ Phase 4 (US2, P2) ── independiente, y sin tablas nuevas
    └─→ Phase 5 (US3, P3) ── independiente
            ↓
    Phase 6 (Polish)
```

**Las dos dimensiones están en la fase 2 porque las tres historias las necesitan** — US1 para el
valor del pipeline, US2 para todo, US3 para la efectividad de la nutrición. Colocarlas dentro de una
historia haría que las otras dos dependieran de ella.

**Dentro de la fase 2**: T004 primero; T005 y T006 dependen de ella; T007 de ambas; el bloque de
servicio (T010–T013) es independiente del de dimensiones.

**Dentro de las fases 3 y 5**: la ampliación del modelo **antes** que las consultas, y estas antes
que endpoints y pruebas.

---

## Parallel Execution Examples

**Fase 3 — tres consultas de OT02 a la vez:**

```text
T025 ot02_carga_por_ejecutivo.sql
T026 ot02_pipeline_ponderado.sql
T027 ot02_motivos_perdida.sql
```

**Fase 5 — cuatro consultas de OT03:**

```text
T048 ot03_intensidad_demo.sql
T049 ot03_secciones_visitadas.sql
T050 ot03_efectividad_nutricion.sql
T052 ot03_reglas_disparo.sql
```

---

## Implementation Strategy

### MVP — US1

Cinco informes de embudo, y **CU-T03 satisfecho**: uno de los dos casos de uso tácticos que hoy no
cubre ningún informe del proyecto.

### Entrega incremental

1. **Fases 1–2** — el prospecto sin identidad, con su desenlace ya desagregado.
2. **Fase 3 (US1)** — **MVP**, y CU-T03.
3. **Fase 4 (US2)** — CU-T04, y **sin ninguna tabla nueva**: la historia más barata del módulo.
4. **Fase 5 (US3)** — la nutrición, con datos sintéticos.
5. **Fase 6** — cierre.

### Cinco riesgos a vigilar

**T005 y T008 son la tarea y la prueba más importantes del módulo.** Si el desenlace se deriva mal,
las trece consultas heredan el defecto y **ninguna falla**: presentarán conversiones y pérdidas como
lo mismo, con números que parecen razonables.

**T030 protege a los prospectos estancados.** Son los que el informe existe para encontrar, y una
consulta que solo mida etapas cerradas los deja fuera **presentándolos como los más rápidos**.

**T039 defiende una decisión que es fácil deshacer sin querer.** Basta con añadir `coste: null` a la
respuesta «por si acaso» para que alguien lo rellene desde el frontend y el tablero muestre un CAC
inventado. La prueba lo impide.

**T054 vigila el sesgo más contraintuitivo.** Contar un aviso ignorado como latencia cero hace que
**los peores casos mejoren el indicador**.

**Las pruebas de OT03 deben usar datos sintéticos.** Con las dos fuentes a cero, una consulta rota y
un origen vacío devuelven exactamente lo mismo.
