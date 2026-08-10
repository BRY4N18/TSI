---

description: "Task list for feature implementation"
---

# Tasks: Infraestructura Táctica (ClickHouse + Airflow)

**Input**: Design documents from `specs/002-tactico/infraestructura/`

**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/docker-compose-contract.md](contracts/docker-compose-contract.md), [quickstart.md](quickstart.md)

**Tests**: No se solicitaron tests automatizados de código (no hay código de aplicación en esta feature — es infraestructura declarativa). La validación es la ejecución de `quickstart.md`, que se materializa como tareas de verificación dentro de cada historia.

**Organization**: Tareas agrupadas por historia de usuario de `spec.md`. US1 y US3 son P1; US2 es P2 — se ejecutan en ese orden.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias)
- **[Story]**: US1 (levantar stack aislado), US2 (persistencia entre reinicios), US3 (conectividad Airflow↔Pinot/ClickHouse)
- Rutas de archivo exactas en cada descripción

## Path Conventions

Infraestructura pura — no hay `src/`/`tests/` de aplicación. Todo vive en:
- `docker/docker-compose.tactico.yml` (nuevo, sibling de `docker/docker-compose.infraestructura.yml` y `docker/accidentes.yml`)
- `docker/.env.tactico.example` (nuevo, plantilla de variables — sin valores reales versionados)
- `docker/tactico/airflow-dags/` (nuevo, bind mount vacío — carpeta de DAGs, sin DAGs de negocio en esta feature)
- `.specify/docs/infra/infrastructure.md` (existente, se actualiza)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar el archivo compose base y los recursos que todos los servicios comparten, sin arrancar todavía ningún contenedor.

- [X] T001 Crear `docker/docker-compose.tactico.yml` con `name: tactico`, la red externa `pipeline-net` (`external: true`, mismo nombre que crea `docker/docker-compose.infraestructura.yml`) y el bloque `volumes:` declarando `tactico-clickhouse-data` y `tactico-airflow-metadata` (con nombre, no anónimos), según `research.md` §2 y §6
- [X] T002 [P] Crear `docker/.env.tactico.example` con las variables de entorno de ejemplo (sin valores reales): `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `AIRFLOW_POSTGRES_USER`, `AIRFLOW_POSTGRES_PASSWORD`, `AIRFLOW__CORE__FERNET_KEY`, `_AIRFLOW_WWW_USER_USERNAME`, `_AIRFLOW_WWW_USER_PASSWORD`, según `research.md` §7
- [X] T003 [P] Crear la carpeta `docker/tactico/airflow-dags/` (vacía, con un `.gitkeep`) para el bind mount de DAGs, según `data-model.md` ("Fuera de alcance de esta fase")

**Checkpoint**: El archivo compose existe con red/volúmenes declarados pero sin servicios todavía — nada se ha levantado.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Definir en el compose los servicios base de los que dependen las 3 historias (ClickHouse y el metastore de Airflow), sin los cuales ninguna historia es verificable.

**⚠️ CRITICAL**: Ninguna historia de usuario puede validarse hasta que esta fase esté completa.

- [X] T004 Añadir el servicio `tactico-clickhouse` a `docker/docker-compose.tactico.yml` (imagen `clickhouse/clickhouse-server`, puertos `8123:8123` y `9100:9000`, volumen `tactico-clickhouse-data`, red `pipeline-net`, healthcheck HTTP `GET /ping`), según `research.md` §1 y §4 y el contrato en `specs/002-tactico/infraestructura/contracts/docker-compose-contract.md`
- [X] T005 [P] Añadir el servicio `tactico-airflow-postgres` a `docker/docker-compose.tactico.yml` (imagen `postgres`, sin puerto publicado al host, volumen `tactico-airflow-metadata`, red `pipeline-net`, healthcheck `pg_isready`), según `research.md` §6
- [X] T006 Añadir el servicio `tactico-airflow-init` a `docker/docker-compose.tactico.yml` (imagen `apache/airflow`, comando de migración de base de datos + `airflow users create` usando `_AIRFLOW_WWW_USER_USERNAME`/`_AIRFLOW_WWW_USER_PASSWORD`, `depends_on: tactico-airflow-postgres` con `condition: service_healthy`, sin reinicio automático — corre una vez), según `research.md` §3 y §7
- [X] T007 Verificar manualmente que `docker compose -f docker/docker-compose.tactico.yml config` no reporta errores de sintaxis tras T001-T006

**Checkpoint**: Fundación lista — ClickHouse y el metastore de Airflow pueden arrancar; las historias de usuario ya pueden implementarse.

---

## Phase 3: User Story 1 - Levantar el stack táctico junto al stack operativo existente (Priority: P1) 🎯 MVP

**Goal**: Poder levantar el stack `tactico` completo con un solo comando, sin afectar el stack operativo (Kafka + Pinot), y verificar que ambos coexisten sin colisión.

**Independent Test**: Levantar `docker/docker-compose.tactico.yml` de forma aislada; ClickHouse responde y la UI de Airflow carga; el stack operativo sigue sin cambios de estado (pasos 1-3 de `quickstart.md`).

### Implementation for User Story 1

- [X] T008 [US1] Añadir el servicio `tactico-airflow-webserver` a `docker/docker-compose.tactico.yml` (imagen `apache/airflow`, comando `webserver`, puerto `8090:8080`, `depends_on: tactico-airflow-init` completado y `tactico-airflow-postgres` healthy, red `pipeline-net`, healthcheck HTTP `GET /health`), según `research.md` §1, §3, §7
- [X] T009 [US1] Añadir el servicio `tactico-airflow-scheduler` a `docker/docker-compose.tactico.yml` (imagen `apache/airflow`, comando `scheduler`, bind mount `docker/tactico/airflow-dags/:/opt/airflow/dags`, `depends_on: tactico-airflow-init` completado y `tactico-airflow-postgres` healthy, red `pipeline-net`), según `research.md` §3 y `data-model.md`
- [X] T010 [US1] Ejecutar el paso 1 de `specs/002-tactico/infraestructura/quickstart.md` (`docker compose -f docker/docker-compose.tactico.yml up -d` + `ps`) y confirmar que los 5 servicios llegan a `healthy`/`exited (0)` en menos de 5 minutos (SC-001)
- [X] T011 [US1] Ejecutar la verificación de no-interferencia del paso 1 de `quickstart.md` (`docker compose -f docker/docker-compose.infraestructura.yml ps`) y confirmar que ningún contenedor del stack operativo cambió de estado (FR-002, FR-003)
- [X] T012 [P] [US1] Ejecutar el paso 2 de `quickstart.md` (verificación HTTP de ClickHouse: `SELECT 1`) y confirmar respuesta correcta
- [X] T013 [P] [US1] Ejecutar el paso 3 de `quickstart.md` (abrir `http://localhost:8090`, autenticarse, confirmar listado de DAGs vacío) — FR-008

**Checkpoint**: El stack `tactico` está arriba, aislado del stack operativo, y ambos servicios (ClickHouse, Airflow) son accesibles y verificables de forma independiente.

---

## Phase 4: User Story 3 - Conectividad Pinot → Airflow → ClickHouse (Priority: P1)

**Goal**: Confirmar que Airflow puede alcanzar por red tanto Pinot (fuente, stack operativo) como ClickHouse (destino, stack `tactico`), sin exponer datos ni credenciales reales todavía.

**Independent Test**: Con ambos stacks levantados, una tarea de conectividad ejecutada desde el contenedor de Airflow alcanza `pinot-broker:8099` y `tactico-clickhouse:8123` (paso 5 de `quickstart.md`).

### Implementation for User Story 3

- [X] T014 [US3] Levantar el stack operativo si no está arriba (`docker compose -f docker/docker-compose.infraestructura.yml up -d`) y confirmar que `pipeline-net` es visible desde `docker network inspect pipeline-net` incluyendo los contenedores `tactico-*`
- [X] T015 [US3] Ejecutar el paso 5 de `quickstart.md`: `docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler bash -c "curl -sf http://pinot-broker:8099/health && echo PINOT_OK"` y confirmar `PINOT_OK`
- [X] T016 [US3] Ejecutar el paso 5 de `quickstart.md`: `docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler bash -c "curl -sf http://tactico-clickhouse:8123/ping && echo CLICKHOUSE_OK"` y confirmar `CLICKHOUSE_OK`
- [X] T017 [US3] Documentar en `specs/002-tactico/infraestructura/contracts/docker-compose-contract.md` (sección "Acceso a Airflow") la conexión Pinot/ClickHouse verificada, dejando constancia de que la configuración de la `Connection` de Airflow (UI/CLI) queda para la spec de informes compuestos, no para esta

**Checkpoint**: Conectividad de red verificada extremo a extremo — la spec de informes compuestos puede empezar a definir DAGs reales sobre esta base sin volver a validar infraestructura.

---

## Phase 5: User Story 2 - Persistencia de datos entre reinicios (Priority: P2)

**Goal**: Confirmar que los datos de ClickHouse y los metadatos de Airflow sobreviven a un reinicio de los contenedores.

**Independent Test**: Crear una tabla de prueba en ClickHouse, reiniciar el stack `tactico`, confirmar que los datos siguen presentes (pasos 2 y 4 de `quickstart.md`).

### Implementation for User Story 2

- [X] T018 [US2] Ejecutar el paso 2 de `quickstart.md` (crear `tactico_smoke_test.ping` en ClickHouse e insertar una fila) — prerrequisito de esta historia
- [X] T019 [US2] Ejecutar el paso 4 de `quickstart.md` (`docker compose -f docker/docker-compose.tactico.yml restart`) y confirmar que `SELECT * FROM tactico_smoke_test.ping` sigue devolviendo la fila insertada (SC-003)
- [X] T020 [US2] Configurar en Airflow (vía UI o CLI, vinculado a T013) una `Variable` o `Connection` de prueba, reiniciar el stack, y confirmar que la configuración persiste (SC-003, segunda mitad)

**Checkpoint**: Persistencia confirmada — el stack `tactico` puede detenerse/levantarse en el día a día del desarrollo sin perder trabajo previo.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Dejar el stack documentado y descubrible para las specs siguientes (informes simples y compuestos de Emergencias).

- [X] T021 [P] Actualizar `.specify/docs/infra/infrastructure.md` §5.1: mover "ClickHouse + Airflow para capa analítica batch (futuro)" de roadmap a stack activo, con la tabla de puertos real de `research.md` §1 (FR-009)
- [X] T022 [P] Añadir `tactico-clickhouse` y los servicios `tactico-airflow-*` a la tabla de "Servicios de datos: puertos y orden de dependencia" (§2) de `.specify/docs/infra/infrastructure.md`, siguiendo el mismo formato que las filas existentes de Kafka/Pinot
- [X] T023 Ejecutar `docker compose -f docker/docker-compose.tactico.yml down` (sin `-v`) seguido de `up -d` una vez más como prueba final de idempotencia (Edge Cases de `spec.md`: "¿qué pasa si se levantan dos veces los stacks?")
- [X] T024 Recorrer `specs/002-tactico/infraestructura/quickstart.md` de punta a punta una vez más, sin pasos previos ya ejecutados en memoria, para confirmar que un responsable de infraestructura nuevo podría seguirlo solo con la documentación (SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — puede iniciar de inmediato
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEA las 3 historias de usuario
- **User Story 1 (Phase 3, P1)**: Depende de Foundational
- **User Story 3 (Phase 4, P1)**: Depende de Foundational y de que User Story 1 haya dejado Airflow arriba (T008-T009) — no es independiente de la infraestructura de Airflow, pero sí es una historia separada porque valida una capacidad distinta (red, no arranque)
- **User Story 2 (Phase 5, P2)**: Depende de Foundational y de que ClickHouse/Airflow estén arriba (Phase 3) para tener algo que reiniciar
- **Polish (Phase 6)**: Depende de que las 3 historias estén completas

### User Story Dependencies

- **US1 (P1)**: Ninguna dependencia de otra historia — es el MVP
- **US3 (P1)**: Requiere que los contenedores de Airflow existan (creados en US1); prueba una capacidad ortogonal (conectividad de red) que US1 no verifica
- **US2 (P2)**: Requiere que exista algo persistible (ClickHouse/Airflow arriba, de US1); prueba una capacidad ortogonal (supervivencia a reinicio)

### Parallel Opportunities

- T002 y T003 (Setup) en paralelo — archivos distintos
- T005 (Foundational) en paralelo con T004 — servicios distintos en el mismo archivo compose, pero sin dependencia mutua en su definición (el compose se edita de forma incremental; en la práctica conviene aplicar T004-T006 en secuencia sobre el mismo archivo para evitar conflictos de edición, aunque conceptualmente T004 y T005 son independientes)
- T012 y T013 (US1) en paralelo — verifican servicios distintos (ClickHouse vs. Airflow UI)
- T021 y T022 (Polish) en paralelo — mismo archivo pero secciones distintas; ejecutar con cuidado de no pisar la edición del otro si se paralelizan literalmente

---

## Parallel Example: User Story 1

```bash
# Verificaciones de la Historia 1 que pueden lanzarse juntas una vez el stack está arriba (T010-T011 completados):
Task: "Ejecutar paso 2 de quickstart.md (ClickHouse SELECT 1)"
Task: "Ejecutar paso 3 de quickstart.md (Airflow UI carga y autentica)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (CRÍTICO — bloquea todas las historias)
3. Completar Phase 3: User Story 1
4. **DETENER Y VALIDAR**: el stack `tactico` arriba, aislado, con ClickHouse y Airflow accesibles
5. Con esto ya se puede empezar a diseñar la spec de informes compuestos en paralelo, aunque US2/US3 no estén terminadas

### Incremental Delivery

1. Setup + Foundational → Fundación lista
2. User Story 1 → Validar de forma independiente → MVP: stack visible y accesible
3. User Story 3 → Validar de forma independiente → Conectividad de red confirmada, listo para DAGs reales
4. User Story 2 → Validar de forma independiente → Persistencia confirmada, seguro para uso diario
5. Polish → Documentación actualizada, stack descubrible para las specs siguientes

---

## Notes

- [P] = archivos distintos, sin dependencias directas
- Esta feature no tiene tests de código porque no hay código de aplicación — la "prueba" de cada historia es su tramo correspondiente de `quickstart.md`, convertido en tareas ejecutables (T010-T013, T014-T017, T018-T020)
- Confirmar cada checkpoint antes de pasar a la siguiente fase
- No se toca `docker/docker-compose.infraestructura.yml` ni `docker/accidentes.yml` en ninguna tarea (restricción dura de FR-002/FR-003)

---

## Addendum (2026-08-06): migración a staging en Parquet

- [X] T025 Crear `docker/tactico/airflow/Dockerfile` + `requirements.txt` (`pandas==2.1.4`, `pyarrow==16.1.0`, `pytest==8.2.2`) y cambiar `x-airflow-common` en `docker-compose.tactico.yml` de `image:` a `build:`
- [X] T026 Cambiar los bind mounts de `x-airflow-common` de `../docker/tactico/airflow-dags` a `../dags` (raíz del repo) y añadir `../ETL:/opt/airflow/ETL` + variable `ETL_ROOT`
- [X] T027 Crear `dags/` en la raíz del repo (`etl/`, `quality/`, `operations/`, `lib/`, `tests/`), mover `lib/*` y `tests/*` desde `docker/tactico/airflow-dags/` sin cambios, y eliminar `docker/tactico/airflow-dags/` por completo
- [X] T028 Crear `dags/lib/parquet_io.py` (`stage_path`/`write_parquet`/`read_parquet`, ruta `ETL/<fecha>/<hora>/<stage>_data.parquet`, formato de hora `HH-MM` — no `HH:MM`, inválido en rutas de Windows, verificado con Docker Desktop)
- [X] T029 Migrar los 3 DAGs de negocio a 3 tareas (`extract`/`transform`/`load`) vía staging Parquet, moviendo las funciones a `dags/lib/*_tasks.py` (no en el archivo del DAG) para que `dag_backfill.py` las reutilice sin re-importar un archivo de DAG (anti-patrón de Airflow: causa `AirflowDagDuplicatedIdException`)
- [X] T030 Crear `dags/etl/dag_etl_principal.py` (referencia del patrón) y `dags/etl/dag_backfill.py` (reproceso manual parametrizado, Dynamic Task Mapping sobre las mismas funciones extract/transform/load)
- [X] T031 Crear DAGs operativos: `dags/quality/dag_validacion_calidad.py`, `dags/operations/dag_limpieza_staging.py`, `dags/operations/dag_mantenimiento_bd.py`, `dags/operations/dag_system_health.py`
- [X] T032 Crear `dags/tests/test_parquet_io.py` y `dags/tests/test_dag_integrity.py` (pytest plano, no un DAG); confirmar que la suite completa (26 tests) pasa dentro del contenedor
- [X] T033 Actualizar `contracts/docker-compose-contract.md`, `spec.md` y `data-model.md` de esta carpeta con el nuevo patrón y las nuevas rutas
- [X] T034 Verificación end-to-end: `airflow dags test` de cada uno de los 9 DAGs, confirmando parquet generados en `ETL/` y filas correctas en ClickHouse
