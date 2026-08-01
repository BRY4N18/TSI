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
| Base de datos por defecto | `default` (las tablas de informes compuestos crearán su propia base de datos en la spec correspondiente — no en esta) |
| Autenticación | Usuario/contraseña de desarrollo definidos por variables de entorno del compose; sin TLS (uso interno de desarrollo, ver Assumptions de [`spec.md`](spec.md)) |

## Acceso a Airflow

| Propiedad | Valor |
|---|---|
| UI web (host) | `http://localhost:8090` |
| Usuario admin | Definido por `_AIRFLOW_WWW_USER_USERNAME` / `_AIRFLOW_WWW_USER_PASSWORD` en el `.env` del compose `tactico` (no versionado con valores reales) |
| Carpeta de DAGs | `tactico-airflow-dags` (bind mount) — las specs de informes compuestos añadirán aquí sus archivos `.py` de DAG |
| Conexión a Pinot (a configurar en Airflow UI/CLI por la spec de informes compuestos) | Host `pinot-broker`, puerto `8099`, dentro de `pipeline-net` |
| Conexión a ClickHouse (a configurar en Airflow UI/CLI por la spec de informes compuestos) | Host `tactico-clickhouse`, puerto `8123` (HTTP) o `9000` (nativo, interno) |

**Conectividad verificada (T014-T016, `specs/002-tactico/infraestructura/tasks.md`)**: desde `tactico-airflow-scheduler`, `curl http://pinot-broker:8099/health` responde `OK` y `curl http://tactico-clickhouse:8123/ping` responde `Ok.` — ambos alcanzables por nombre de host dentro de `pipeline-net`, sin necesidad de IP ni puerto publicado al host. La configuración de la `Connection` de Airflow (UI/CLI) con estos hosts queda para la spec de informes compuestos, que es quien primero necesitará usarla desde un DAG real.

## Garantías que esta feature entrega

1. Ambos servicios (ClickHouse, Airflow) están arriba y healthy antes de que cualquier spec futura intente usarlos.
2. Los nombres de host anteriores son estables dentro de `pipeline-net` — no cambian según qué otros stacks estén levantados.
3. Los datos persisten entre reinicios del stack `tactico` (no entre un `docker compose down -v`, que borra volúmenes explícitamente).
4. Ningún puerto de este contrato colisiona con los ya documentados en `.specify/docs/infra/infrastructure.md` §2 (stack operativo) ni con `accidentes.yml`.

## Fuera de este contrato (pendiente de specs futuras)

- Esquema de tablas de ClickHouse por informe compuesto.
- Definición de DAGs concretos (qué leen de Pinot, qué escriben en ClickHouse, con qué frecuencia).
- Workpanels de frontend que consuman estos informes.
