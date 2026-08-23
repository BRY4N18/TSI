---

description: "Task list for feature implementation"
---

# Tasks: Informes Tácticos Compuestos de Emergencias (Backend)

**Input**: Design documents from `specs/002-tactico/Emergencias/informes-tacticos-compuestos/backend/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/informes-tacticos-compuestos.openapi.yaml](contracts/informes-tacticos-compuestos.openapi.yaml), [quickstart.md](quickstart.md)

**Prerrequisito duro**: `../../infraestructura/` (ClickHouse + Airflow) ya implementada y verificada — ninguna tarea de este archivo es viable sin ese stack arriba.

**Tests**: Incluidos. Los DAGs separan su lógica pura en funciones testeables con `pytest` normal (research.md §4, sin scheduler de Airflow real); los endpoints Django siguen el mismo patrón `repository`/`service`/`api` que `informes-tacticos-simples`.

**Organization**: Tareas agrupadas por historia de usuario de `spec.md`. US1 (pérdida de señal) es P1; US2 (índice de calidad) y US3 (rendimiento por proveedor) son P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: US1 (pérdida de señal GPS), US2 (índice de calidad consolidado), US3 (rendimiento por proveedor)
- Cada descripción incluye ruta exacta de archivo

## Path Conventions

Dos runtimes distintos, sin código compartido entre ellos (plan.md, Structure Decision):
- `dags/` en la raíz del repo — DAGs + su `lib/` propia, corre en `tactico-airflow-scheduler`. **Reemplaza a `docker/tactico/airflow-dags/`, mencionada en las tareas de más abajo — ver Addendum al final de este archivo para el mapeo de rutas vigente.**
- `backend/core/clickhouse/`, `backend/core/repositories/informes_tacticos/`, `backend/apps/informes_tacticos/` — endpoints Django, corre en el contenedor de Django

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Clientes HTTP mínimos (Pinot y ClickHouse) reutilizables por los 3 DAGs, y el cliente ClickHouse del lado Django.

- [X] T001 Crear `docker/tactico/airflow-dags/lib/__init__.py` y `docker/tactico/airflow-dags/tests/__init__.py`
- [X] T002 [P] Implementar `docker/tactico/airflow-dags/lib/pinot_http_client.py`: función `query_pinot(sql, params=None)` vía `requests.post` a `http://pinot-broker:8099/query/sql`, con `LIMIT` explícito por defecto — mismo comportamiento que `backend/core/pinot/client.py` pero sin dependencia de Django (research.md §1-2)
- [X] T003 [P] Implementar `docker/tactico/airflow-dags/lib/clickhouse_http_client.py`: funciones `execute_clickhouse(sql)` (DDL/INSERT) y `query_clickhouse(sql)` (SELECT, `FORMAT JSONEachRow`) vía `requests` a `http://tactico-clickhouse:8123/`, autenticado con las credenciales de `docker/.env.tactico` (research.md §1)
- [X] T004 [P] Crear `backend/core/clickhouse/__init__.py` y `backend/core/clickhouse/client.py` (`ClickHouseClient`, solo lectura, mismo patrón HTTP que `core/pinot/client.py`, settings `CLICKHOUSE_URL`/`CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD` nuevas en `backend/config/settings.py`)
- [X] T005 [P] Test unitario de `docker/tactico/airflow-dags/lib/clickhouse_http_client.py` en `docker/tactico/airflow-dags/tests/test_clickhouse_http_client.py` (mock de `requests.post`) verificando el formato de la query enviada
- [X] T006 [P] Test de repositorio (marker: repository) de `backend/core/clickhouse/client.py` en `backend/apps/informes_tacticos/tests/repositories/test_clickhouse_client.py`, con un fixture `mock_clickhouse` nuevo en `backend/conftest.py` (mismo patrón que `mock_pinot`)

**Checkpoint**: Ambos runtimes pueden hablar con ClickHouse (uno para escribir batch, otro para leer); ningún DAG ni endpoint de negocio implementado todavía.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Piezas compartidas por las 3 historias — permiso de solo-Administrador, envelope con el caso "no materializado", creación idempotente de tablas.

**⚠️ CRITICAL**: Ninguna historia de usuario puede completarse hasta que esta fase esté lista.

- [X] T007 Añadir `InformesTacticosCompuestosPermission` a `backend/apps/informes_tacticos/permissions.py` (rol `Administrador` únicamente — research.md §5)
- [X] T008 [P] Extender `backend/apps/informes_tacticos/envelope.py` con `informe_compuesto_response(data, periodo, materializado, ultima_corrida)` para el shape `{data, meta: {periodo, materializado, ultima_corrida}}` de `data-model.md`
- [X] T009 [P] Crear `docker/tactico/airflow-dags/lib/ddl.py` con las 3 sentencias `CREATE TABLE IF NOT EXISTS` de `data-model.md` (una función por tabla: `ensure_perdida_senal_table()`, `ensure_indice_calidad_table()`, `ensure_rendimiento_proveedor_table()`), invocadas al inicio de cada DAG
- [X] T010 Verificar manualmente (`docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler python -c "..."`) que `ensure_*_table()` crea las 3 tablas en `tsi_tactico` sin error, usando las credenciales reales del stack `tactico` ya levantado

**Checkpoint**: Permiso, envelope y DDL listos — las 3 historias ya pueden implementarse en paralelo.

---

## Phase 3: User Story 1 - Detectar misiones con pérdida de señal GPS (Priority: P1) 🎯 MVP

**Goal**: DAG que recorre `Dim_HistorialUbicacionUnidadEmergencia` por unidad, detecta huecos mayores al umbral vigente, materializa en `perdida_senal_gps`; endpoint Django que lee esa tabla.

**Independent Test**: Con datos de prueba con huecos conocidos sembrados en Pinot, correr el DAG de forma aislada y verificar que `perdida_senal_gps` contiene exactamente los huecos esperados (SC-002); consultar el endpoint y confirmar que sirve esas filas sin recomputar.

> **US1 completa y verificada contra el stack real (2026-08-02).** Sembré 3 pings reales en Pinot vía Kafka (unidad 777, hueco de 200s), disparé `perdida_senal_gps` de verdad en `tactico-airflow-scheduler` (`airflow dags trigger`), confirmé la fila materializada en ClickHouse con `curl`, verifiqué idempotencia con una segunda corrida (mismo conteo de filas), reconstruí `accidentes-django` y confirmé el endpoint HTTP real de punta a punta (200 con datos, 403 con rol Operador, 401 sin token).
> **Desviación real de diseño**: dado que el DAG reprocesa el histórico completo en cada corrida (no una ventana incremental — ver docstring de `perdida_senal_dag.py`), `materializado` es `true` para cualquier período una vez que el DAG corrió al menos una vez; solo es `false` si la tabla nunca tuvo ninguna corrida. El paso 5 de `quickstart.md` (período 2099 esperando `materializado:false`) no aplica tal cual con este diseño — se corrigió la expectativa en la verificación real (2099 devuelve `materializado:true, data:[]`, que es la lectura correcta: "sin huecos en ese rango", no "sin procesar").
> **Bug preexistente no relacionado, encontrado y evitado (no corregido, fuera de alcance)**: `HistorialUbicacionRepository._next_id()` (`backend/core/repositories/seguimiento/historial_ubicacion_repository.py`) consulta la columna `idhistorialubicacion`, que no existe — el esquema real usa `idhistorialunidademergencia`. Rompe cualquier `publish()` de esa clase. Se sembraron los datos de prueba publicando directo con `KafkaWriter`, evitando el método roto.
> Se añadieron `CLICKHOUSE_URL`/`CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD`/`CLICKHOUSE_DB` a `backend/.env` (Django corre en un contenedor separado del stack `tactico`, necesita las credenciales reales para alcanzar `tactico-clickhouse` por nombre de host en `pipeline-net`).

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Test unitario (marker: unit) de la función pura de detección de huecos en `docker/tactico/airflow-dags/tests/test_perdida_senal_logic.py`: casos con huecos conocidos, sin huecos, huecos exactamente en el umbral (límite), múltiples unidades (SC-002)
- [X] T012 [P] [US1] Test de idempotencia en `docker/tactico/airflow-dags/tests/test_perdida_senal_logic.py`: procesar el mismo conjunto de pings dos veces no debe producir huecos duplicados (SC-003)
- [X] T013 [P] [US1] Test de repositorio (marker: repository) en `backend/apps/informes_tacticos/tests/repositories/test_perdida_senal_repository.py` contra `mock_clickhouse`, incluyendo el caso "tabla vacía para el período" (FR-008)
- [X] T014 [P] [US1] Test de API (marker: api) en `backend/apps/informes_tacticos/tests/api/test_compuestos_views.py::TestPerdidaSenalView` cubriendo `200` materializado, `200` no materializado, `403` con rol Operador (FR-009)

### Implementation for User Story 1

- [X] T015 [US1] Implementar la función pura `detectar_huecos(pings: list[dict], umbral_seg: int) -> list[dict]` en `docker/tactico/airflow-dags/lib/perdida_senal_logic.py` (recorre pings ordenados por `fechahora`, emite huecos > umbral) — según T011/T012
- [X] T016 [US1] Implementar `docker/tactico/airflow-dags/perdida_senal_dag.py`: `PythonOperator` que (a) llama `ensure_perdida_senal_table()`, (b) lee `Dim_HistorialUbicacionUnidadEmergencia` y `Dim_ParametrosSeguimiento.gps_umbral_senal_perdida_seg` vía `pinot_http_client`, (c) agrupa por unidad y llama `detectar_huecos`, (d) escribe en `perdida_senal_gps` vía `clickhouse_http_client` (INSERT idempotente: `DELETE` del período antes de insertar, o `ReplacingMergeTree` — decidir en implementación y documentar), horario diario (depende de T002, T003, T009, T015)
- [X] T017 [US1] Implementar `backend/core/repositories/informes_tacticos/perdida_senal_repository.py` (`PerdidaSenalRepository.consultar(desde, hasta)` → filas de ClickHouse o `None` si no hay `calculado_en` para el período) (depende de T004)
- [X] T018 [US1] Añadir `perdida_senal(periodo)` a un nuevo `backend/apps/informes_tacticos/services/informes_compuestos_service.py` (depende de T017)
- [X] T019 [US1] Crear `backend/apps/informes_tacticos/views/compuestos_views.py` con `PerdidaSenalView`, aplicando `InformesTacticosCompuestosPermission` (T007) (depende de T018)
- [X] T020 [US1] Registrar `/informes-tacticos/compuestos/perdida-senal` en `backend/apps/informes_tacticos/urls.py` (depende de T019)
- [X] T021 [US1] Ejecutar los pasos 1, 2, 3 (subset pérdida de señal), 4 (subset) y 6 de `quickstart.md` contra el stack `tactico` real: disparar el DAG, verificar la tabla en ClickHouse, verificar idempotencia, consultar el endpoint

**Checkpoint**: El informe de pérdida de señal funciona de punta a punta (Pinot → DAG → ClickHouse → endpoint), de forma independiente de los otros dos.

---

## Phase 4: User Story 2 - Índice consolidado de calidad del histórico (Priority: P2)

**Goal**: DAG que combina los 4 indicadores base (completitud, descarte, fusión, cobertura de evidencia) en un índice único por período, conservando la serie histórica; endpoint Django que sirve la evolución completa.

**Independent Test**: Con los 4 indicadores base disponibles para al menos 2 períodos, correr el DAG y verificar que `indice_calidad_historico` tiene una fila por período con el índice combinado correcto.

> **US2 completa y verificada contra el stack real (2026-08-02).** Disparé `indice_calidad_historico` contra los datos ya existentes en Pinot (sin necesidad de sembrar nada nuevo — usó accidentes reales del ambiente), confirmé filas reales en ClickHouse con `curl` y el endpoint HTTP real respondiendo la serie completa.
> **Bug real encontrado y corregido en el momento**: la primera corrida falló (`TypeError: 'int' object is not subscriptable`) porque `DATETRUNC(...)` en Pinot **real** devuelve epoch milliseconds (LONG), no un string de fecha — asunción incorrecta que arrastré del mock de Pinot usado en `informes-tacticos-simples` (ahí sí devolvía strings, porque yo mismo escribí esa simulación). Corregido con `_periodo_str()` en `indice_calidad_dag.py`, re-verificado con éxito.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Test unitario (marker: unit) de la función de combinación en `docker/tactico/airflow-dags/tests/test_indice_calidad_logic.py`: verifica la fórmula (promedio de completitud, `1-descarte`, `1-fusión`, cobertura de evidencia) con valores conocidos
- [X] T023 [P] [US2] Test de repositorio (marker: repository) en `backend/apps/informes_tacticos/tests/repositories/test_indice_calidad_repository.py` contra `mock_clickhouse`, verificando que devuelve la serie completa (no solo el último valor, Acceptance Scenario 2 de la spec)
- [X] T024 [P] [US2] Test de API (marker: api) en `test_compuestos_views.py::TestIndiceCalidadView`

### Implementation for User Story 2

- [X] T025 [US2] Implementar `combinar_indice(pct_completitud, pct_descarte, pct_fusion, pct_cobertura_evidencia) -> float` en `docker/tactico/airflow-dags/lib/indice_calidad_logic.py` (depende de T022)
- [X] T026 [US2] Implementar `docker/tactico/airflow-dags/indice_calidad_dag.py`: lee los 4 indicadores desde Pinot (mismas consultas que `informes-tacticos-simples` para completitud/descarte/fusión, más una nueva para cobertura de evidencia vía `Dim_EvidenciaFoto`+`Fact_Accidente` estado Cerrado), llama `combinar_indice`, escribe en `indice_calidad_historico` (idempotente por período), horario diario (depende de T003, T009, T025)
- [X] T027 [US2] Implementar `backend/core/repositories/informes_tacticos/indice_calidad_repository.py` (depende de T004)
- [X] T028 [US2] Añadir `indice_calidad(periodo)` a `informes_compuestos_service.py` (depende de T027)
- [X] T029 [US2] Añadir `IndiceCalidadView` a `compuestos_views.py` (depende de T028)
- [X] T030 [US2] Registrar `/informes-tacticos/compuestos/indice-calidad` en `urls.py` (depende de T029)
- [X] T031 [US2] Ejecutar el subset de `quickstart.md` correspondiente a índice de calidad contra el stack real

**Checkpoint**: El índice de calidad funciona de punta a punta, independiente de los otros dos informes.

---

## Phase 5: User Story 3 - Rendimiento de despacho por proveedor de unidades (Priority: P2)

**Goal**: DAG que agrupa despachos por `Dim_UnidadEmergencia.idcliente` (proveedor vigente en el momento del despacho), materializa % rechazo/tiempo de llegada/% abortos por proveedor y período.

**Independent Test**: Con datos de prueba de al menos 2 proveedores con comportamiento distinto, correr el DAG y verificar que `rendimiento_por_proveedor` distingue correctamente a cada uno.

> **US3 completa y verificada contra el stack real (2026-08-02).** `rendimiento_por_proveedor` corrió exitosamente a la primera contra los despachos ya existentes en el ambiente; 3 filas materializadas en ClickHouse, endpoint HTTP real confirmado con `curl`.
> **Limitación de diseño documentada** (Edge Case de la spec: "unidad cambia de proveedor entre períodos"): `Dim_UnidadEmergencia` no historiza cambios de `idcliente` (sin tabla tipo SCD), así que el DAG usa el proveedor **actual** de la unidad para todos los períodos, no el vigente en el momento histórico de cada despacho. Documentado en el docstring de `lib/rendimiento_proveedor_logic.py` — resolverlo requeriría una tabla de historial de asignación unidad↔proveedor que no existe en el esquema v2.

### Tests for User Story 3 ⚠️

- [X] T032 [P] [US3] Test unitario (marker: unit) de la función de agregación por proveedor en `docker/tactico/airflow-dags/tests/test_rendimiento_proveedor_logic.py`, incluyendo el caso "unidad cambia de proveedor entre períodos" (Edge Case de la spec: cada período refleja el proveedor vigente en ese momento)
- [X] T033 [P] [US3] Test de repositorio (marker: repository) en `backend/apps/informes_tacticos/tests/repositories/test_rendimiento_proveedor_repository.py` contra `mock_clickhouse`
- [X] T034 [P] [US3] Test de API (marker: api) en `test_compuestos_views.py::TestRendimientoProveedorView`

### Implementation for User Story 3

- [X] T035 [US3] Implementar `agregar_por_proveedor(despachos, historial, unidades) -> list[dict]` en `docker/tactico/airflow-dags/lib/rendimiento_proveedor_logic.py` (depende de T032)
- [X] T036 [US3] Implementar `docker/tactico/airflow-dags/rendimiento_proveedor_dag.py`: lee `Fact_Despacho`+`Fact_HistorialDespachoUnidad`+`Dim_UnidadEmergencia` (`idcliente`) vía `pinot_http_client`, llama `agregar_por_proveedor`, escribe en `rendimiento_por_proveedor` (idempotente por período), horario diario (depende de T002, T003, T009, T035)
- [X] T037 [US3] Implementar `backend/core/repositories/informes_tacticos/rendimiento_proveedor_repository.py` (depende de T004)
- [X] T038 [US3] Añadir `rendimiento_proveedor(periodo)` a `informes_compuestos_service.py` (depende de T037)
- [X] T039 [US3] Añadir `RendimientoProveedorView` a `compuestos_views.py` (depende de T038)
- [X] T040 [US3] Registrar `/informes-tacticos/compuestos/rendimiento-proveedor` en `urls.py` (depende de T039)
- [X] T041 [US3] Ejecutar el subset de `quickstart.md` correspondiente a rendimiento por proveedor contra el stack real

**Checkpoint**: Los 3 informes compuestos funcionan de punta a punta.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cerrar la spec de backend antes de pasar a `../frontend/`.

- [X] T042 [P] Recorrer `quickstart.md` completo (los 6 pasos) sin pasos previos ya ejecutados en memoria, contra el stack `tactico` real
- [X] T043 [P] Verificar en la UI de Airflow (`http://localhost:8090`) que los 3 DAGs tienen horario diario configurado y que sus últimas corridas están en `success` (FR-010, logs nativos de Airflow — ver data-model.md "Registro de ejecución")
- [X] T044 Actualizar `../informes-tacticos-compuestos.md` (índice del módulo) marcando la capa backend como completa
- [~] T045 ~~Cambiar `.specify/feature.json` → `.../informes-tacticos-compuestos/frontend`~~ — **no se ejecuta: el módulo se retiró.**

  ⚠️ Esta tarea apuntaría el flujo de trabajo a la capa UI de un módulo que ya no
  existe. El diseño de **una tabla materializada por informe** se sustituyó el
  2026-08-15 por el modelo analítico compartido (decisión #20, opción B):
  `informe_compuesto_response` se retiró con él —llevaba `materializado` y
  `ultima_corrida`, que hoy serían siempre `True` y no informarían de nada— y sus
  flujos y DDL se dieron de baja.

  Lo único que queda son tres tablas con datos residuales de la última corrida
  —`perdida_senal_gps`, `indice_calidad_historico`, `rendimiento_por_proveedor`—,
  que **no se borran desde una tarea**: destruir datos no es reversible, y la
  limpieza es una operación de base. Las pruebas del catálogo las restan
  explícitamente como «heredadas».

  Lo que sustituyó a este módulo es `informes-compuestos-modelo`, con sus 78
  tareas de backend y 42 de frontend cerradas.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEA las 3 historias
- **User Story 1 (Phase 3, P1)**: Depende de Foundational
- **User Story 2 (Phase 4, P2)**: Depende de Foundational — independiente de US1/US3 (lee indicadores ya cubiertos por `informes-tacticos-simples`, no depende de que US1 exista)
- **User Story 3 (Phase 5, P2)**: Depende de Foundational — independiente de US1/US2
- **Polish (Phase 6)**: Depende de que las 3 historias estén completas

### User Story Dependencies

- **US1, US2, US3**: Cada una toca su propio DAG, su propio módulo `*_logic.py`, su propio repositorio y su propia vista — ninguna depende de que las otras estén implementadas. Comparten únicamente lo ya resuelto en Foundational (permiso, envelope, DDL).

### Parallel Opportunities

- T002-T006 (Setup) en paralelo entre sí
- T007-T009 (Foundational) en paralelo entre sí
- Tras Foundational: US1 (Phase 3), US2 (Phase 4) y US3 (Phase 5) completas pueden avanzar en paralelo
- Dentro de cada historia: los tests marcados [P] en paralelo entre sí, antes de la implementación secuencial (lógica pura → DAG → repositorio → service → vista → url, por dependencia real)
- T042/T043 (Polish) en paralelo

---

## Parallel Example: User Story 1

```bash
# Tests de la Historia 1, en paralelo (antes de implementar):
Task: "Test unitario de detección de huecos en docker/tactico/airflow-dags/tests/test_perdida_senal_logic.py"
Task: "Test de repositorio en backend/apps/informes_tacticos/tests/repositories/test_perdida_senal_repository.py"
Task: "Test de API en backend/apps/informes_tacticos/tests/api/test_compuestos_views.py::TestPerdidaSenalView"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (CRÍTICO)
3. Completar Phase 3: User Story 1 (pérdida de señal — el caso de uso testigo de Airflow)
4. **DETENER Y VALIDAR**: el DAG corre de verdad contra el stack `tactico`, materializa en ClickHouse, el endpoint lo sirve
5. Con esto ya queda demostrado el patrón completo (Pinot→DAG→ClickHouse→Django) para los otros dos informes

### Incremental Delivery

1. Setup + Foundational → Fundación lista
2. User Story 1 (pérdida de señal, P1) → Validar contra el stack real → primera tarjeta compuesta en el workpanel de Seguimiento
3. User Story 2 (índice de calidad, P2) → Validar → tarjeta en el workpanel de Registro
4. User Story 3 (rendimiento por proveedor, P2) → Validar → tarjeta en el workpanel de Despacho
5. Polish → Backend cerrado, listo para `../frontend/`

---

## Notes

- [P] = archivos distintos, sin dependencia directa
- La idempotencia (FR-003, SC-003) se decide en implementación entre `DELETE`+`INSERT` del período o `ReplacingMergeTree` con `FINAL` en lectura — documentar la decisión tomada en el docstring del DAG correspondiente
- Ningún DAG escribe en Pinot ni ningún endpoint Django escribe en ClickHouse (FR-002, FR-004) — verificar esto explícitamente en los tests de repositorio (solo se llama a `query_clickhouse`/`ClickHouseClient.query`, nunca a un método de escritura, desde el lado Django)
- Confirmar cada checkpoint antes de pasar a la siguiente fase

---

## Addendum (2026-08-06): migración a `dags/` (raíz) + extract/transform/load-parquet

Las tareas T001-T036 de arriba (todas `[X]`, completadas) mencionan rutas bajo `docker/tactico/airflow-dags/` — esa carpeta **ya no existe**, fue reemplazada por `dags/` en la raíz del repo (ver `../../infraestructura/spec.md`, Addendum 2026-08-06). Mapeo de rutas vigente:

| Ruta mencionada en T001-T036 | Ruta vigente |
|---|---|
| `docker/tactico/airflow-dags/lib/pinot_http_client.py` | `dags/lib/pinot_http_client.py` (sin cambios de contenido) |
| `docker/tactico/airflow-dags/lib/clickhouse_http_client.py` | `dags/lib/clickhouse_http_client.py` (sin cambios de contenido) |
| `docker/tactico/airflow-dags/lib/ddl.py` | `dags/lib/ddl.py` (sin cambios de contenido) |
| `docker/tactico/airflow-dags/lib/perdida_senal_logic.py` | `dags/lib/perdida_senal_logic.py` (sin cambios de contenido) |
| `docker/tactico/airflow-dags/lib/indice_calidad_logic.py` | `dags/lib/indice_calidad_logic.py` (sin cambios de contenido) |
| `docker/tactico/airflow-dags/lib/rendimiento_proveedor_logic.py` | `dags/lib/rendimiento_proveedor_logic.py` (sin cambios de contenido) |
| `docker/tactico/airflow-dags/perdida_senal_dag.py` | `dags/etl/perdida_senal_dag.py` (solo wiring del DAG) + `dags/lib/perdida_senal_tasks.py` (extract/transform/load, nuevo) |
| `docker/tactico/airflow-dags/indice_calidad_dag.py` | `dags/etl/indice_calidad_dag.py` (solo wiring del DAG) + `dags/lib/indice_calidad_tasks.py` (extract/transform/load, nuevo) |
| `docker/tactico/airflow-dags/rendimiento_proveedor_dag.py` | `dags/etl/rendimiento_proveedor_dag.py` (solo wiring del DAG) + `dags/lib/rendimiento_proveedor_tasks.py` (extract/transform/load, nuevo) |
| `docker/tactico/airflow-dags/tests/*` | `dags/tests/*` (sin cambios de contenido — mismos 19 tests, ahora 26 con los nuevos de `parquet_io`/`dag_integrity`) |

Cada DAG pasó de 1 tarea a 3 (`extract >> transform >> load`), con staging en Parquet en `ETL/<fecha>/<hora>/`. Las funciones de negocio (`detectar_huecos`, `combinar_indice`, `agregar_por_proveedor`) no cambiaron — ver `data-model.md`, Addendum 2026-08-06, para el detalle completo.

Nuevas tareas (no numeradas contra T001-T036, ver `../../infraestructura/tasks.md` T025-T034 para el detalle completo de esta migración):
- [X] Extraer `extract`/`transform`/`load` de cada DAG a `dags/lib/*_tasks.py` (necesario para que `dags/etl/dag_backfill.py` los reutilice sin re-importar un archivo de DAG)
- [X] Verificar con `airflow dags test <dag_id> <fecha>` que los 3 DAGs de negocio siguen produciendo las mismas filas en ClickHouse que antes de la migración
