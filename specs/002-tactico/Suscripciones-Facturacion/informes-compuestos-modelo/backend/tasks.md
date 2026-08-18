# Tasks: Informes Compuestos de Suscripciones y Facturación sobre el Modelo Analítico

**Input**: Design documents from `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** Este módulo produce **cinco indicadores financieros del
BSC**, y sus cinco formas de equivocarse **no fallan**: un MRR inflado, un ingreso sin descontar
notas de crédito, una duración negativa, una solicitud olvidada que mejora la media y un plan
inexistente. Todos devuelven números que parecen razonables.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Cinco indicadores BSC pasan de no medibles a medibles** —MRR, ingresos, renovación, movimientos y
NRR—, y se calcularán sobre **4 suscripciones y 6 facturas**. Correctos, y no representativos.

**Su fase 2 es la más pesada de la serie, y es deliberado.** `hecho_suscripcion` lo necesitan **las
tres** historias y `hecho_factura` **dos**. Si estuvieran dentro de una historia, las demás
dependerían de ella y dejarían de ser entregables por separado.

**⚠️ Depende de las fases 1 y 2 de Emergencias**, no de sus informes.

---

## Phase 1: Setup

- [X] T001 Verificar que el modelo analítico está cargado, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q`
- [X] T002 Verificar que **las fases 1 y 2 de Emergencias están implementadas**: existen `dags/lib/consultas/__init__.py` y `backend/core/repositories/informes_tacticos/modelo_repository.py`
- [X] T003 Crear `dags/lib/consultas/suscripciones/` con un `README.md` que remita a `contracts/catalogo-consultas.md` y recoja **las cuatro reglas propias**: nada de `activo`, ingresos con signo, disputa ≠ impago, y sin medios de cobro ni desglose por persona

---

## Phase 2: Foundational — el dominio financiero, con los cinco defectos neutralizados

**Purpose**: dos dimensiones y **dos hechos** que las tres historias comparten, y las cinco columnas
que resuelven de una vez lo que si no tendrían que esquivar trece consultas.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

### Las dos dimensiones

- [X] T004 Crear `dim_plan` y `dim_cliente` en `dags/lib/ddl.py` según `data-model.md` §2.1 y §2.2. ⚠️ **`dim_cliente` sin identificador fiscal, sin contacto, sin token de pasarela y sin últimos dígitos**: solo `tiene_metodo_pago` y `metodo_pago_caduca`
- [X] T005 Implementar `dags/lib/dimensiones/dim_plan.py` **desplegando los límites en columnas** —unidades, usuarios, llamadas mes y minuto— y las severidades en un array. El origen los guarda como texto estructurado; interpretarlo en cada consulta repartiría esa lógica por todo el catálogo (research D5)
- [X] T006 Implementar `dags/lib/dimensiones/dim_cliente.py`. ⚠️ **Es una dimensión conformada**: la necesitan también Red Operativa y Ventas. Cuentas y Clientes **la ampliará, no la recreará**
- [X] T007 Añadir ambas al flujo existente en `dags/lib/dimensiones_tasks.py` y sus filas desconocidas en `dags/lib/dimensiones/desconocido.py`
- [X] T008 [P] Prueba de que `dim_cliente` **no contiene medios de cobro ni dato fiscal** en `dags/tests/test_dim_cliente_sin_sensibles.py`: no filtrados, **inexistentes** (SC-009)
- [X] T009 [P] Prueba de que los límites del plan **quedaron desplegados y son comparables** en `dags/tests/test_dim_plan_limites.py`

### El hecho de suscripción — instantánea acumulada

- [X] T010 Crear `hecho_suscripcion` en `dags/lib/ddl.py` según `data-model.md` §2.3, como **`ReplacingMergeTree` particionado por mes**: es el tercer hecho de instantánea acumulada del modelo
- [X] T011 ⚠️ Implementar `dags/lib/hechos/hecho_suscripcion.py` con **`estado_derivado`**, que **nunca sale de `activo`**: el origen tiene suscripciones canceladas con esa columna en verdadero (research D1)
- [X] T012 ⚠️ Implementar en el mismo módulo **`precio_mensualizado`**: normaliza toda periodicidad a mensual, usa el **precio de la suscripción** y no el de lista del plan, y queda **ausente —nunca cero—** cuando la periodicidad no consta (research D3)
- [X] T013 ⚠️ Implementar **`vigencia_inconsistente`**: marca las suscripciones con fin anterior al inicio. **No se corrigen ni se descartan**: corregirlas inventaría un dato y borraría la evidencia del defecto; descartarlas perdería un ingreso real (research D4)
- [X] T014 Implementar `motivo_cancelacion` **solo cuando el estado dice que canceló** —el origen lo puebla en suscripciones activas— y `idplan_programado` **nulo en vez del centinela `0`**
- [X] T015 Implementar el flujo en `dags/lib/hecho_suscripcion_tasks.py` y `dags/etl/dag_hecho_suscripcion.py`, con sensor sobre el flujo de dimensiones

### El hecho de factura

- [X] T016 Crear `hecho_factura` en `dags/lib/ddl.py` según `data-model.md` §2.4. ⚠️ **Sin `idmetodopago`, sin `desglose_cargos` y sin `motivo_anulacion`**
- [X] T017 ⚠️ Implementar `dags/lib/hechos/hecho_factura.py` con **`monto_con_signo`**, para que sumar ingresos sea sumar: las notas de crédito **restan solas**. Sin esa columna, la primera consulta que olvide el signo inflará los ingresos
- [X] T018 Implementar `pagada_primer_intento` y `dias_mora`, y conservar **`En disputa` como estado propio**: no es impago (FR-019)
- [X] T019 Implementar el flujo conjunto en `dags/lib/hecho_facturacion_tasks.py` y `dags/etl/dag_hecho_facturacion.py`
- [X] T020 Registrar ambos DAG en `dags/tests/test_dag_integrity.py` y las tablas en `dags/tests/test_sin_datos_sensibles.py`

### El servicio, las vistas y la autoridad repartida

- [X] T021 Implementar `backend/apps/informes_tacticos/services/suscripciones_compuestos_service.py` sobre el `modelo_repository` existente
- [X] T022 Implementar `backend/apps/informes_tacticos/views/suscripciones_compuestos_views.py` reutilizando `views/base.py` y `envelope.py`
- [X] T023 ⚠️ Aplicar la **autoridad repartida** en `backend/apps/informes_tacticos/permissions.py` con `AUTORIDAD_SUSCRIPCIONES_FINANZAS` y `AUTORIDAD_SUSCRIPCIONES_CATALOGO` de `backend/core/auth/roles_tacticos.py`: el Financiero cubre facturación y cobro; el de Estrategia, catálogo y precios. **Ninguno cubre la materia del otro** (FR-038, FR-039)
- [X] T024 Implementar en `backend/apps/informes_tacticos/envelope.py` los campos `mes` y `nota_periodo` de la meta, para los informes que se resuelven a mes natural (research D8)

### Las pruebas de las reglas que no avisan

- [X] T025 ⚠️ **Prueba del estado derivado** en `dags/tests/test_hecho_suscripcion_estado.py`: una suscripción `Cancelada` con `activo = true` en el origen **no aporta MRR**. Si lo aporta, el estado salió de la columna equivocada (SC-002)
- [X] T026 ⚠️ **Prueba de la versión final** en `dags/tests/test_catalogo_suscripciones.py`, sobre el **texto** de las consultas: obligatoria en las dos dimensiones **y en `hecho_suscripcion`**; prohibida en factura y solicitud. Es la trampa del módulo — los otros dos hechos son de transacción, y la costumbre lleva a no forzarla justo donde infla el MRR
- [X] T027 [P] Prueba de que **ninguna consulta lee `activo` ni suma `monto_total` sin signo**, en `dags/tests/test_catalogo_suscripciones.py`
- [X] T028 [P] Prueba de que **ninguna consulta nombra medio de cobro, dato fiscal ni administrador**, en `dags/tests/test_catalogo_suscripciones.py` (FR-032, FR-033)
- [X] T029 [P] Prueba de la autoridad repartida en `backend/apps/informes_tacticos/tests/api/test_permisos_suscripciones.py`: el Financiero **no** accede a los informes de catálogo, y el de Estrategia **no** a los de cobro

**Checkpoint**: sustrato listo — las tres user stories pueden abordarse en cualquier orden.

---

## Phase 3: User Story 1 — Cuánto entra y si se cobra (Priority: P1) 🎯 MVP

**Goal**: los seis informes de OT06, con **tres indicadores BSC** que hoy no tienen ninguna fuente.

**Independent Test**: pedir el MRR de un mes y comprobar que es la suma de los precios
**mensualizados** de las suscripciones vigentes.

**Criterio medible (ISO 25010 — Corrección funcional)**: una suscripción cancelada **no aporta MRR**,
pese a tener la columna de actividad en verdadero (SC-002).

### Las consultas

- [X] T030 [US1] ⚠️ Escribir `dags/lib/consultas/suscripciones/ot06_mrr.sql`: normaliza a mensual, excluye las de periodicidad ausente contándolas en `sin_periodicidad`, y **descompone la variación en nuevo, expansión, contracción y baja**, que deben sumar el neto
- [X] T031 [US1] ⚠️ Escribir `dags/lib/consultas/suscripciones/ot06_ingresos.sql` sumando **`monto_con_signo`**, y devolviendo `notas_credito` aparte para que se vea cuánto se restó
- [X] T032 [P] [US1] Escribir `dags/lib/consultas/suscripciones/ot06_tasa_renovacion.sql`
- [X] T033 [P] [US1] Escribir `dags/lib/consultas/suscripciones/ot06_cobro_primer_intento.sql`, distinguiendo pagada sin reintentos de pagada tras reintentos
- [X] T034 [P] [US1] Escribir `dags/lib/consultas/suscripciones/ot06_efectividad_dunning.sql` con `escalones_dunning`
- [X] T035 [US1] ⚠️ Escribir `dags/lib/consultas/suscripciones/ot06_clientes_sin_metodo_pago.sql` como **diferencia de conjuntos**: el cliente que interesa es el que **no tiene ninguna fila** de método. Una unión interna lo perdería, al revés del propósito

### Los endpoints

- [X] T036 [US1] Exponer los seis endpoints de OT06 en `backend/apps/informes_tacticos/views/suscripciones_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-suscripciones.openapi.yaml`
- [X] T037 [US1] Resolver el MRR a **mes natural** aunque se pidan fechas arbitrarias, declarándolo en `meta.mes` y `meta.nota_periodo` (research D8)

### Pruebas

- [X] T038 [US1] ⚠️ **Prueba del MRR** en `dags/tests/test_ot06_mrr.py`, con cuatro comprobaciones: normaliza periodicidades distintas; excluye la que no tiene periodicidad **sin contarla como cero**; usa el precio de la suscripción y no el del plan; y los cuatro componentes **suman la variación neta** (SC-003, SC-008)
- [X] T039 [US1] ⚠️ **Prueba de las notas de crédito** en `dags/tests/test_ot06_ingresos.py`: el ingreso neto de un período con nota de crédito es **menor** que sumando importes sin signo. Si coinciden, los ingresos están inflados (SC-006)
- [X] T040 [P] [US1] Prueba de que **una factura en disputa no aparece entre las impagas** ni suma mora, en `dags/tests/test_ot06_disputa.py` (SC-005)
- [X] T041 [P] [US1] Prueba de que **el cliente sin ninguna fila de método de pago sí aparece** en `dags/tests/test_ot06_sin_metodo.py`: es la diferencia de conjuntos, y una unión ordinaria lo perdería
- [X] T042 [P] [US1] Prueba de que **ningún informe de OT06 devuelve medio de cobro** en `dags/tests/test_ot06_sin_medios_cobro.py`, ni con la autoridad departamental

**Checkpoint**: US1 entregable. Es el MVP: **tres indicadores BSC pasan a ser medibles**.

---

## Phase 4: User Story 2 — Los movimientos de la cartera (Priority: P2)

**Goal**: los cuatro informes de OT07, con **dos indicadores BSC más**.

**Independent Test**: aprobar una subida de plan y comprobar que aparece como upgrade con delta
positivo, y una bajada con delta negativo.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: una solicitud pendiente **no aparece** con
tiempo de resolución cero (SC-007).

### Ampliar el modelo

- [X] T043 [US2] Crear `hecho_solicitud_cambio_plan` en `dags/lib/ddl.py` según `data-model.md` §2.5. ⚠️ **Sin `idadminaprobador`** —identidad— y **sin `motivo_rechazo`** —texto libre—
- [X] T044 [US2] ⚠️ Implementar `dags/lib/hechos/hecho_solicitud_cambio_plan.py` derivando `tipo_movimiento` **del delta de precio, no del nivel del plan**: el catálogo tiene un Empresarial más barato que un Profesional, así que subir de nivel no siempre es subir de precio
- [X] T045 [US2] Implementar `segundos_resolucion` **ausente mientras la solicitud esté pendiente**: una solicitud abierta no se resolvió en cero segundos
- [X] T046 [US2] Añadir el hecho al flujo de `dags/lib/hecho_facturacion_tasks.py` —comparte fuente y ciclo— y registrarlo en `dags/tests/test_sin_datos_sensibles.py`

### Las consultas

- [X] T047 [P] [US2] Escribir `dags/lib/consultas/suscripciones/ot07_movimientos_plan.sql`, distinguiendo aprobada de aplicada
- [X] T048 [US2] ⚠️ Escribir `dags/lib/consultas/suscripciones/ot07_nrr.sql` sobre la **cohorte de clientes existentes al inicio del mes**, **excluyendo a los nuevos**: incluirlos convertiría el NRR en crecimiento bruto, que es otro indicador
- [X] T049 [P] [US2] Escribir `dags/lib/consultas/suscripciones/ot07_suspension_reactivacion.sql`
- [X] T050 [US2] ⚠️ Escribir `dags/lib/consultas/suscripciones/ot07_tiempo_resolucion.sql` **sin desglose por administrador**, contando las resueltas —incluidas las rechazadas— y dejando las **pendientes aparte**

### Los endpoints

- [X] T051 [US2] Exponer los cuatro endpoints de OT07 en `backend/apps/informes_tacticos/views/suscripciones_compuestos_views.py` y `urls.py`

### Pruebas

- [X] T052 [US2] ⚠️ **Prueba de la solicitud pendiente** en `dags/tests/test_ot07_tiempo_resolucion.py`: queda **fuera de la mediana** y se cuenta en `pendientes`. Contarla como cero haría que las solicitudes olvidadas **mejoraran** el indicador (SC-007)
- [X] T053 [P] [US2] Prueba de que **una rechazada cuenta como resuelta** en `dags/tests/test_ot07_tiempo_resolucion.py`: se resolvió, aunque fuera en contra (FR-026)
- [X] T054 [P] [US2] Prueba de que **el tipo de movimiento sale del delta de precio** en `dags/tests/test_ot07_movimientos.py`: un cambio a un plan de nivel superior **más barato** es un downgrade
- [X] T055 [P] [US2] Prueba de que **el NRR excluye a los clientes nuevos** en `dags/tests/test_ot07_nrr.py`, y que sus componentes explican la cifra
- [X] T056 [P] [US2] Prueba de que ningún informe de OT07 devuelve **identidad del administrador** en `dags/tests/test_ot07_sin_identidad.py`

**Checkpoint**: US2 entregable. **Con US1, los cinco indicadores BSC del departamento son medibles.**

---

## Phase 5: User Story 3 — El catálogo y su uso (Priority: P3)

**Goal**: los tres informes de OT05, bajo la autoridad del **Director de Estrategia**.

**Independent Test**: un cliente con plan de 25 unidades y 5 dadas de alta muestra 5 de 25, **con
ambos números**.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: un plan de precio cero cuenta en el reparto
de clientes y aporta **cero ingreso**, con ambas cifras visibles (SC-010).

### Las consultas

- [X] T057 [P] [US3] Escribir `dags/lib/consultas/suscripciones/ot05_distribucion_cartera.sql`, con los planes de precio cero contando en `clientes` y aportando **cero** en `mrr_aportado`
- [X] T058 [US3] ⚠️ Escribir `dags/lib/consultas/suscripciones/ot05_utilizacion_limites.sql` **sin ninguna columna de llamadas API, ni vacía**, cruzando con `dim_unidad` para las unidades, y devolviendo `nota_dimension_pendiente` (FR-030, FR-031)
- [X] T059 [P] [US3] Escribir `dags/lib/consultas/suscripciones/ot05_severidades_habilitadas_vs_usadas.sql`, cruzando `dim_plan` con `hecho_accidente` — **es el primer informe del proyecto que une el dominio financiero con el operativo**

### Los endpoints

- [X] T060 [US3] Exponer los tres endpoints de OT05 en `backend/apps/informes_tacticos/views/suscripciones_compuestos_views.py` y `urls.py`, **bajo la autoridad del Director de Estrategia**

### Pruebas

- [X] T061 [US3] ⚠️ **Prueba de que la utilización no inventa la dimensión que falta** en `dags/tests/test_ot05_utilizacion.py`: ninguna clave de llamadas API, **ni siquiera nula**. Un `llamadas: null` diría «no consume la API», que es otra afirmación (FR-030)
- [X] T062 [P] [US3] Prueba de que devuelve **lo usado y lo contratado**, no solo el porcentaje, en `dags/tests/test_ot05_utilizacion.py`: 5 de 25 y 500 de 2 500 son situaciones distintas (FR-027)
- [X] T063 [P] [US3] Prueba de que **un plan de precio cero no desaparece** en `dags/tests/test_ot05_distribucion.py`: cuenta en clientes y aporta cero ingreso (SC-010)
- [X] T064 [P] [US3] Prueba de que **una severidad habilitada y no usada aparece** en `dags/tests/test_ot05_severidades.py`: es la señal de que un cliente paga por algo que no necesita

**Checkpoint**: los 13 informes disponibles.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T065 [P] Prueba de que **todo importe declara moneda y periodicidad** en `dags/tests/test_suscripciones_importes.py` (FR-037)
- [X] T066 [P] Prueba de que **un período sin facturas devuelve cero filas** y no una fila de ceros, en `dags/tests/test_suscripciones_periodo_vacio.py`
- [X] T067 ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_suscripciones.py`: tras añadir dos dimensiones y tres hechos, **las cifras de los tres departamentos anteriores no cambian** (SC-011)
- [X] T068 Ejecutar `cd backend && python -m pytest -q` y verificar que ninguna suite existente se movió
- [X] T069 Recorrer `quickstart.md` de principio a fin, con especial atención a §2.1 (cancelada sin MRR), §2.3 (vigencia invertida) y §2.5 (notas de crédito)
- [X] T070 Anotar en `decisiones-pendientes.md` los **cinco defectos del sistema operativo** de este departamento, señalando que **dos de cada cuatro filas ya traen uno** y que en una cartera grande sería un problema serio de calidad de dato
- [X] T071 Documentar en `.specify/docs/changelog.md`, actualizar el estado de los 13 informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` y **dejar constancia de que `dim_cliente` es conformada**, para que Cuentas y Clientes la amplíe en vez de recrearla

---

## Dependencies

```text
Emergencias, fases 1 y 2 (plomería)  ← DEPENDENCIA EXTERNA
    ↓
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: 2 dimensiones + 2 hechos + servicio + reglas) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ── independiente
    ├─→ Phase 4 (US2, P2) ── independiente
    └─→ Phase 5 (US3, P3) ── independiente
            ↓
    Phase 6 (Polish)
```

**Por qué la fase 2 es tan grande aquí.** `hecho_suscripcion` lo necesitan **las tres** historias
—MRR y renovación en US1, NRR y suspensiones en US2, distribución de cartera en US3— y
`hecho_factura` **dos** —ingresos y cobro en US1, NRR en US2—. Dejarlos dentro de una historia haría
que las otras dependieran de ella.

**Solo `hecho_solicitud_cambio_plan` es propio de una historia** (US2).

**Dentro de la fase 2**: T004 primero; T005–T007 dependen de ella; T010–T015 y T016–T020 son dos
bloques independientes entre sí; el de servicio (T021–T024) no depende de ninguno.

---

## Parallel Execution Examples

**Fase 3 — tres consultas de OT06 a la vez:**

```text
T032 ot06_tasa_renovacion.sql
T033 ot06_cobro_primer_intento.sql
T034 ot06_efectividad_dunning.sql
```

**Fase 4 — las pruebas tras los endpoints:**

```text
T053 rechazada cuenta como resuelta
T054 tipo de movimiento por delta de precio
T055 NRR excluye clientes nuevos
T056 sin identidad del administrador
```

---

## Implementation Strategy

### MVP — US1

Seis informes y **tres indicadores BSC que pasan de no tener fuente a estar medidos**: MRR, ingresos
y tasa de renovación.

### Entrega incremental

1. **Fases 1–2** — el dominio financiero con los cinco defectos neutralizados.
2. **Fase 3 (US1)** — **MVP**, tres BSC.
3. **Fase 4 (US2)** — los otros dos BSC. **Con US1, el departamento queda completo en indicadores.**
4. **Fase 5 (US3)** — el catálogo, bajo otra autoridad.
5. **Fase 6** — cierre.

### Cinco riesgos a vigilar

**T026 vigila la trampa específica de este módulo.** `hecho_suscripcion` es el único hecho acumulado
aquí; los otros dos son de transacción, así que la costumbre lleva a no forzar versión final — y
justo en ese **infla el MRR de forma intermitente**.

**T011 y T025 son la tarea y la prueba que sostienen todo lo demás.** Si `estado_derivado` se calcula
mal, los trece informes heredan un MRR inflado y **ninguno falla**.

**T039 protege una resta silenciosa.** Sumar `monto_total` en vez de `monto_con_signo` funciona
perfectamente y **deja de descontar las notas de crédito**.

**T013 no debe «arreglar» la vigencia invertida.** Corregirla borraría la evidencia de un defecto que
el origen sigue produciendo; descartarla perdería un ingreso real. Se aísla y se cuenta.

**T061 defiende una abstención.** Basta con añadir `llamadas: null` «por coherencia» para que alguien
lo interprete como consumo cero, y para que Partners herede un diseño que no eligió.
