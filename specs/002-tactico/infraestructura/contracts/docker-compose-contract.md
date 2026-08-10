# Contrato: Stack `tactico` (interfaz para specs futuras)

> Este documento es el "contrato" que las specs de informes simples e informes compuestos (departamento de Gestión de Emergencias) pueden asumir como estable una vez implementada esta feature. No es una API HTTP — es la interfaz de infraestructura (nombres de host, puertos, credenciales) que un DAG de Airflow o un cliente ClickHouse usarán.

## Acceso a ClickHouse

| Propiedad | Valor |
|---|---|
| Host (dentro de `pipeline-net`) | `tactico-clickhouse` |
| Puerto HTTP (interno) | `8123` |
| Puerto HTTP (host, para verificación manual) | `8123` |
| Puerto nativo TCP (interno) | `9000` |
| Puerto nativo TCP (host, para verificación manual) | `9100` |
| Base de datos analítica | Variable `CLICKHOUSE_DB` (default `tsi_tactico`) — creada al primer arranque vía `docker/tactico/clickhouse-init/` |
| Autenticación | Usuario/contraseña de desarrollo definidos por `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` del compose; sin TLS (uso interno de desarrollo, ver Assumptions de [`spec.md`](spec.md)) |

## Acceso a Airflow

| Propiedad | Valor |
|---|---|
| UI web (host) | `http://localhost:8090` |
| Usuario admin | Definido por `_AIRFLOW_WWW_USER_USERNAME` / `_AIRFLOW_WWW_USER_PASSWORD` en el `.env` del compose `tactico` (no versionado con valores reales) |
| Imagen de Airflow | Custom, build local (`docker/tactico/airflow/Dockerfile`, `FROM apache/airflow:2.9.3` + `pandas`/`pyarrow`/`pytest` vía `requirements.txt`) — ya no es la imagen oficial stock, porque el patrón de staging en Parquet (ver abajo) requiere esas dependencias |
| Carpeta de DAGs | `dags/` en la **raíz del repositorio** (bind mount a `/opt/airflow/dags`) — **reemplaza** a `docker/tactico/airflow-dags/`, que fue eliminada. Estructura: `dags/etl/` (DAGs de negocio + `dag_etl_principal.py`/`dag_backfill.py`), `dags/quality/`, `dags/operations/`, `dags/lib/` (clientes HTTP + lógica pura + tareas reutilizables), `dags/tests/` |
| Carpeta de staging Parquet | `ETL/` en la raíz del repositorio (bind mount a `/opt/airflow/ETL`, variable de entorno `ETL_ROOT` dentro del contenedor). Ruta por archivo: `ETL/<fecha:YYYY-MM-DD>/<hora:HH-MM>/<extract\|transform\|loading>_data.parquet`. No versionado en git (`.gitignore`: `ETL/**/*.parquet`) — son artefactos regenerables, no el almacén de registro |
| Conexión a Pinot | Host `pinot-broker`, puerto `8099`, dentro de `pipeline-net` — usada directamente por `dags/lib/pinot_http_client.py` (no vía Airflow Connection configurada en UI) |
| Conexión a ClickHouse | Host `tactico-clickhouse`, puerto `8123` (HTTP) — usada directamente por `dags/lib/clickhouse_http_client.py` |

**Conectividad verificada (T014-T016, `specs/002-tactico/infraestructura/tasks.md`)**: desde `tactico-airflow-scheduler`, `curl http://pinot-broker:8099/health` responde `OK` y `curl http://tactico-clickhouse:8123/ping` responde `Ok.` — ambos alcanzables por nombre de host dentro de `pipeline-net`, sin necesidad de IP ni puerto publicado al host. La configuración de la `Connection` de Airflow (UI/CLI) con estos hosts queda para la spec de informes compuestos, que es quien primero necesitará usarla desde un DAG real.

## Garantías que esta feature entrega

1. Ambos servicios (ClickHouse, Airflow) están arriba y healthy antes de que cualquier spec futura intente usarlos.
2. Los nombres de host anteriores son estables dentro de `pipeline-net` — no cambian según qué otros stacks estén levantados.
3. Los datos persisten entre reinicios del stack `tactico` (no entre un `docker compose down -v`, que borra volúmenes explícitamente).
4. Ningún puerto de este contrato colisiona con los ya documentados en `.specify/docs/infra/infrastructure.md` §2 (stack operativo) ni con `accidentes.yml`.

## Fuera de este contrato (pendiente de specs futuras)

- Esquema de tablas de ClickHouse por informe compuesto (ver `Emergencias/informes-tacticos-compuestos/backend/data-model.md`).
- Contenido de negocio de cada DAG (qué leen de Pinot, qué escriben en ClickHouse, con qué frecuencia) — el patrón de ejecución (extract/transform/load-parquet) sí es parte de este contrato, el contenido de cada tarea no.
- Workpanels de frontend que consuman estos informes.

## Patrón de ejecución vinculante para DAGs `tactico` (2026-08-06)

Todo DAG bajo `dags/` sigue el patrón **BD Operacional (Pinot) → extract.parquet → transform.parquet → loading.parquet → BD Analítica (ClickHouse)**: Airflow solo orquesta el orden de las tareas (`extract >> transform >> load`) y les pasa el contexto de ejecución (`ts`); cada tarea reconstruye su propia ruta en `ETL/` a partir de ese `ts` y lee/escribe únicamente archivos Parquet — no se usa XCom para pasar datos entre tareas del pipeline. Esto hace que cada tarea sea re-ejecutable independientemente desde la UI de Airflow.

Riesgo aceptado y documentado (decisión explícita del responsable del proyecto): la ruta `ETL/<fecha>/<hora>/` no incluye el `dag_id`, así que dos DAGs que corran en el mismo `ts` (p. ej. varios `@daily` a medianoche) escriben en la misma carpeta y sus archivos se pisan entre sí. No es un defecto de implementación.

Justificación (Mantenibilidad, ISO/IEC 25010): separar extract/transform/load en tareas independientes con staging en disco hace que un fallo en `transform` no obligue a repetir la consulta a Pinot, y que el contenido intermedio de cada corrida quede inspeccionable para depuración — relevante para un proyecto con un único responsable.
