# Phase 0 Research: Informes Tácticos Compuestos de Emergencias (Backend)

## 1. Cliente ClickHouse: HTTP + `requests` vs. driver de terceros

**Decision**: Implementar un cliente HTTP mínimo propio (`core/clickhouse/client.py` en Django, `docker/tactico/airflow-dags/lib/clickhouse_http_client.py` en los DAGs), usando `requests` contra la interfaz HTTP de ClickHouse (`POST http://tactico-clickhouse:8123/` con la consulta como body y `FORMAT JSONEachRow`/`FORMAT JSON`), en vez de instalar `clickhouse-connect` o `clickhouse-driver`.

**Rationale**: Ya verificamos manualmente en `specs/002-tactico/infraestructura/quickstart.md` que la interfaz HTTP responde (`curl http://localhost:8123/?query=SELECT+1`). `PinotClient` (`backend/core/pinot/client.py`) ya usa exactamente este patrón (HTTP + `requests`, sin driver dedicado) para Pinot — replicarlo mantiene consistencia arquitectónica (Maintainability) y evita añadir una dependencia nueva a `requirements.txt` / a la imagen de Airflow, que no se puede instalar sin reconstruir la imagen.

**Alternatives considered**: `clickhouse-connect` (driver oficial Python) — más ergonómico para queries complejas, pero introduce una dependencia nueva en dos runtimes distintos (Django y Airflow) por una ganancia marginal dado que las consultas de esta feature son simples `SELECT`/`INSERT` sin necesidad de tipos nativos de columna avanzados.

## 2. DAGs autocontenidos (sin importar de `backend/`)

**Decision**: Los 3 DAGs y su `lib/` compartida viven enteramente dentro de `docker/tactico/airflow-dags/`, sin ningún `import` desde el paquete `backend/`.

**Rationale**: `docker-compose.tactico.yml` monta `docker/tactico/airflow-dags/` como el único volumen de código dentro de `tactico-airflow-scheduler`/`tactico-airflow-webserver` (ver `specs/002-tactico/infraestructura/plan.md`, Project Structure) — el contenedor no tiene acceso al código de `backend/` ni a sus dependencias (Django, DRF). Intentar importar `core.pinot.client.PinotClient` desde un DAG fallaría en tiempo de ejecución.

**Alternatives considered**: Montar también `backend/` dentro del contenedor de Airflow para reutilizar `PinotClient` — descartado: acopla el ciclo de vida de dos contenedores con propósitos distintos (API request/response vs. batch scheduler) y obliga a instalar Django completo en la imagen de Airflow solo para reusar un cliente HTTP de 90 líneas. Duplicar ese cliente (research.md §1) es más barato y más aislado (Flexibility).

## 3. Esquema de las 3 tablas de ClickHouse

**Decision**: Una tabla `MergeTree` por informe, particionada por `periodo` (o por unidad+período según el informe), con una columna `calculado_en` (timestamp de cuándo corrió el DAG) y `parametros_usados` (JSON/String, para el caso de pérdida de señal donde el umbral puede cambiar entre corridas — Edge Case de la spec). Detalle completo en `data-model.md`.

**Rationale**: `MergeTree` es el motor por defecto de ClickHouse para series temporales/analítica batch, ya usado como ejemplo en el propio quickstart de infraestructura. Guardar `calculado_en`/`parametros_usados` resuelve directamente dos Edge Cases de la spec: distinguir "no materializado todavía" y detectar cambios de configuración entre corridas.

**Alternatives considered**: Una única tabla genérica `informes_compuestos(informe, clave, valor_json, periodo)` — descartada por perder tipado de columnas (obliga a parsear JSON en cada lectura) y por mezclar 3 dominios de datos distintos en una sola tabla sin necesidad real.

## 4. Testing de los DAGs sin un scheduler de Airflow real

**Decision**: Cada DAG separa su lógica pura (detección de huecos GPS, combinación del índice de calidad, agregación por proveedor) en funciones puro-Python testeables con `pytest` normal, y el archivo del DAG (`*_dag.py`) es solo un `PythonOperator` delgado que invoca esas funciones. Los tests de esas funciones viven junto a los DAGs (`docker/tactico/airflow-dags/tests/`), corridos con `pytest` apuntando a esa carpeta — **no** dentro de `backend/pytest.ini` (contextos de ejecución distintos, sin Django).

**Rationale**: Airflow no es trivial de testear con un scheduler real dentro de un ciclo de CI rápido; separar la lógica de negocio del `PythonOperator` (que solo hace I/O: leer de Pinot, llamar a la función pura, escribir en ClickHouse) permite verificar SC-002 (detección de huecos) y SC-003 (idempotencia) con tests unitarios normales, sin infraestructura de Airflow en el loop de test.

**Alternatives considered**: `pytest-airflow`/`DagBag` testing (cargar el DAG y verificar su estructura) — se añade como test estructural liviano (que el DAG parsea y tiene las tareas esperadas), pero no reemplaza los tests de la lógica pura, que son los que verifican comportamiento real.

## 5. Rol de acceso a los 3 endpoints de lectura

**Decision**: `InformesTacticosCompuestosPermission` (nueva, en `apps/informes_tacticos/permissions.py`), restringida solo a `Administrador` — a diferencia de `InformesTacticosLecturaPermission` (Operador + Administrador) que ya usan los 16 informes simples.

**Rationale**: FR-009 de la spec pide "Supervisor, no Operador raso" — como ya se resolvió en `informes-tacticos-simples`, el rol "Supervisor" no existe (`.specify/docs/actors.md`); `Administrador` es el único rol operativo real con función de gestión/supervisión. A diferencia de los informes simples (uso operativo diario, Operador+Administrador), estos 3 son indicadores de gestión — restringir a solo Administrador es la interpretación más fiel de "no Operador raso" con los roles reales disponibles.

**Alternatives considered**: Reutilizar `InformesTacticosLecturaPermission` tal cual — descartado porque diluiría la distinción explícita que pide FR-009 entre informes operativos (ambos roles) e indicadores de gestión (solo Administrador).
