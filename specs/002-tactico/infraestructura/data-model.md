# Phase 1 Data Model: Infraestructura Táctica (ClickHouse + Airflow)

Esta feature es infraestructura, no dominio de negocio — no hay `Dim_*`/`Fact_*` nuevos en Pinot ni tablas de negocio en ClickHouse todavía (eso corresponde a la spec de informes compuestos). Las "entidades" de esta fase son recursos de infraestructura y su estado operativo, no datos de negocio.

## Entidad: Servicio del stack `tactico`

Representa cada contenedor que compone el stack. No es una tabla de base de datos; es el modelo conceptual que documenta `docker-compose.tactico.yml`.

| Campo | Descripción |
|---|---|
| `nombre` | Nombre del servicio/contenedor, siempre prefijado `tactico-` (ej. `tactico-clickhouse`). |
| `rol` | Almacén analítico \| metastore \| inicialización \| interfaz web \| planificador. |
| `puerto_externo` | Puerto publicado al host, si aplica (ver `research.md` §1). Los servicios internos (ej. `tactico-airflow-postgres`) no publican puerto. |
| `red` | Siempre `pipeline-net` (externa, compartida con el stack operativo). |
| `volumen` | Volumen con nombre o bind mount asociado, si el servicio persiste estado. |
| `depende_de` | Otro(s) servicio(s) que deben estar `healthy` antes de arrancar este. |
| `healthcheck` | Comando de verificación de salud, siguiendo el mismo patrón que `docker-compose.infraestructura.yml`. |

**Instancias (definidas en Project Structure de `plan.md`)**: `tactico-clickhouse`, `tactico-airflow-postgres`, `tactico-airflow-init`, `tactico-airflow-webserver`, `tactico-airflow-scheduler`.

**Relaciones**:
- `tactico-airflow-init` depende de `tactico-airflow-postgres` (healthy) — corre migraciones y crea el usuario admin, luego termina (no es un proceso de larga duración).
- `tactico-airflow-webserver` y `tactico-airflow-scheduler` dependen de `tactico-airflow-init` (completado) y de `tactico-airflow-postgres` (healthy).
- Ninguno de los servicios `tactico-*` depende de servicios del stack operativo (`zookeeper`, `kafka`, `pinot-*`) para arrancar — solo la *tarea de conectividad de prueba* (User Story 3) requiere que Pinot esté arriba, no el arranque del stack en sí (ver Edge Cases en [`spec.md`](spec.md)).

## Entidad: Conexión de red verificada

Representa el resultado de la prueba de conectividad de la User Story 3 — no se persiste como tabla, es el criterio de aceptación de una tarea de humo documentada en `quickstart.md`.

| Campo | Descripción |
|---|---|
| `origen` | Siempre `tactico-airflow-scheduler` (o webserver, para la prueba manual). |
| `destino` | `pinot-broker:8099` (stack operativo) o `tactico-clickhouse:8123` (stack `tactico`). |
| `resultado` | Alcanzable / no alcanzable. |

No requiere modelo de datos persistente — es una verificación operativa puntual, no un dato de negocio.

## Fuera de alcance de esta fase

- Ningún `Dim_*`/`Fact_*` de Pinot se modifica ni se lee con datos reales todavía.
- Ninguna tabla de ClickHouse con modelo de informe compuesto (ej. "misiones abortadas / pérdida de señal") se crea aquí — la única tabla que existe en esta fase es una tabla de prueba desechable para validar SC-003, documentada en `quickstart.md`.

## Addendum (2026-08-06): artefacto de staging Parquet

No es un `Dim_*`/`Fact_*` ni una tabla — es un archivo de staging intermedio entre Pinot y ClickHouse, regenerable en cada corrida (no versionado, no es el almacén de registro).

| Campo | Descripción |
|---|---|
| `ruta` | `ETL/<fecha:YYYY-MM-DD>/<hora:HH-MM>/<stage>_data.parquet`, raíz del repo (bind mount a `/opt/airflow/ETL`, variable `ETL_ROOT`). `<stage>` es `extract`, `transform` o `loading`. |
| `ciclo_de_vida` | Escrito por la tarea `extract`/`transform`/`load` correspondiente de un DAG; leído por la siguiente tarea del mismo DAG; eventualmente borrado por `dags/operations/dag_limpieza_staging.py` pasado el umbral de retención (`Variable` `etl_retention_days`, default 7 días). |
| `riesgo aceptado` | La ruta no incluye `dag_id` — dos DAGs que corran en el mismo `ts` se pisan los archivos entre sí (decisión explícita del responsable del proyecto, ver `contracts/docker-compose-contract.md`). |

La carpeta de DAGs de esta fase (antes `docker/tactico/airflow-dags/`, ahora `dags/` en la raíz) ya no está vacía: contiene los DAGs de negocio migrados por `Emergencias/informes-tacticos-compuestos/backend/` más los DAGs de referencia/operación propios de esta capa de infraestructura (`dag_etl_principal`, `dag_backfill`, `dag_validacion_calidad`, `dag_limpieza_staging`, `dag_mantenimiento_bd`, `dag_system_health`).
