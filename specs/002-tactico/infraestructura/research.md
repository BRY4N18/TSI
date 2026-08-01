# Phase 0 Research: Infraestructura Táctica (ClickHouse + Airflow)

## 1. Puertos: evitar colisión con el stack existente

**Decision**: Usar los siguientes puertos externos para el stack `tactico`:

| Servicio | Puerto interno | Puerto externo propuesto |
|---|---|---|
| `tactico-clickhouse` (HTTP) | 8123 | `8123` |
| `tactico-clickhouse` (nativo TCP) | 9000 | `9100` (remapeado — el `9000` externo ya lo usa `pinot-controller`) |
| `tactico-airflow-webserver` | 8080 | `8090` (remapeado por consistencia/legibilidad, aunque `8080` estaba libre) |
| `tactico-airflow-postgres` | 5432 | *sin publicar* (solo accesible dentro de `pipeline-net`; no lo necesita nadie fuera del propio Airflow) |

**Rationale**: Puertos ya ocupados por `docker-compose.infraestructura.yml`: `2181` (zookeeper), `9092` (kafka), `9000` (pinot-controller), `8099` (pinot-broker), `8098` (pinot-server). Y por `accidentes.yml`: `8000` (django), `4200` (frontend). El puerto nativo por defecto de ClickHouse (`9000`) colisiona directamente con `pinot-controller`, de ahí el remapeo a `9100`. El resto de puertos default de ClickHouse/Airflow no colisionan, pero se documentan explícitamente para que cualquier cambio futuro los revise contra esta tabla.

**Alternatives considered**: Publicar el puerto nativo de ClickHouse en `9001` — descartado por preferir un salto de rango más claro (`91xx` para servicios `tactico`) que no se confunda por proximidad visual con los puertos `90xx` de Pinot.

## 2. Red Docker: unir vs. duplicar

**Decision**: `docker-compose.tactico.yml` declara `pipeline-net` como red **externa** (`external: true`), la misma que crea `docker-compose.infraestructura.yml`. No crea una red propia adicional para el stack `tactico`.

**Rationale**: Es el requisito de conectividad de la User Story 3 (Airflow debe alcanzar el broker de Pinot). Si se creara una red aislada nueva, habría que publicar puertos del stack operativo hacia el host y volver a consumirlos desde ahí — más frágil y contrario a cómo Docker Compose modela la comunicación inter-stack. Reutilizar la red por nombre es el patrón estándar de Compose para "stacks separados que conviven".

**Alternatives considered**: Puentear ambos stacks en un único archivo compose — descartado explícitamente porque el spec (FR-002) exige que el stack `tactico` se levante/detenga de forma independiente del operativo, sin tocarlo.

## 3. Motor de ejecución de Airflow

**Decision**: `LocalExecutor` (ejecuta tareas como subprocesos del propio scheduler), con Postgres como backend de metadatos.

**Rationale**: `SequentialExecutor` (el default de una instalación mínima) no soporta paralelismo real y solo se recomienda con SQLite — insuficiente incluso para pruebas de conectividad concurrentes. `CeleryExecutor`/`KubernetesExecutor` añaden un broker de colas (Redis/RabbitMQ) o un clúster K8s — sobre-ingeniería para un proyecto individual sin DAGs de negocio todavía (ver Scale/Scope en `plan.md`). `LocalExecutor` es el mínimo que da paralelismo real de tareas usando solo un contenedor de scheduler + un Postgres, alineado con el principio de Mantenibilidad de la constitución (lo que el responsable único puede operar sin infraestructura adicional).

**Alternatives considered**: `CeleryExecutor` con Redis — se revisará si una spec futura de informes compuestos necesita paralelismo entre DAGs que `LocalExecutor` no pueda dar; no hay evidencia de esa necesidad hoy.

## 4. Imagen y versión de ClickHouse

**Decision**: Imagen oficial `clickhouse/clickhouse-server`, tag `24.x` (última estable LTS disponible al momento de implementar), single-node.

**Rationale**: Es la imagen oficial mantenida por ClickHouse Inc., mismo criterio ya usado en el proyecto para Pinot/Kafka (imágenes oficiales de la comunidad/vendor, no forks). Single-node porque no hay volumen de datos ni requerimiento de alta disponibilidad que justifique un clúster (ver Scale/Scope).

**Alternatives considered**: Ninguna — no hay otro almacén analítico columnar evaluado en este proyecto; ClickHouse ya estaba decidido explícitamente por el usuario y coincide con el roadmap ya documentado en `infrastructure.md` §5.1.

## 5. Imagen y versión de Airflow

**Decision**: Imagen oficial `apache/airflow`, tag `2.9.x` (o la última estable 2.x disponible al momento de implementar).

**Rationale**: Imagen oficial mantenida por Apache Airflow. Se evita la serie 3.x hasta confirmar que las specs de DAGs de negocio (informes compuestos) no dependan de comportamiento específico de 2.x que rompa en 3.x — decisión conservadora apropiada para un roadmap que hasta ahora solo estaba documentado como futuro, nunca probado en este proyecto.

**Alternatives considered**: Ninguna — Airflow ya estaba decidido explícitamente por el usuario.

## 6. Persistencia y nombres de volumen

**Decision**: Volúmenes con nombre (no anónimos), prefijados `tactico-`: `tactico-clickhouse-data`, `tactico-airflow-metadata`. Carpeta de DAGs (`tactico-airflow-dags`) como bind mount local en lugar de volumen con nombre, para poder editar DAGs desde el host en specs futuras sin reconstruir imagen.

**Rationale**: Mismo patrón que `docker-compose.infraestructura.yml` (`zookeeper-data`, `kafka-data`, etc. — todos con nombre, ninguno anónimo). Satisface FR-006 (persistencia entre reinicios) y SC-003.

**Alternatives considered**: Bind mount también para los datos de ClickHouse — descartado por preferir volúmenes gestionados por Docker para datos binarios de motor de base de datos (más portable entre Windows/Linux, evita problemas de permisos de bind mount en Docker Desktop for Windows).

## 7. Autenticación de Airflow

**Decision**: Usuario/contraseña de desarrollo creado por el job `tactico-airflow-init` en el primer arranque (`airflow users create`), vía variables de entorno del compose (`_AIRFLOW_WWW_USER_USERNAME`, `_AIRFLOW_WWW_USER_PASSWORD`).

**Rationale**: Satisface FR-008 (acceso administrativo requiere autenticación) con el mecanismo estándar que ya trae la imagen oficial de Airflow para entornos de desarrollo, sin introducir un proveedor de identidad externo (fuera de alcance según Assumptions de la spec).

**Alternatives considered**: Integración con el sistema de autenticación propio de TSI (`Dim_Credencial`) — descartado explícitamente: Airflow es una herramienta de administración de infraestructura, no una pantalla de negocio para operadores/clientes; mezclar ambos sistemas de auth sería alcance fuera de esta spec y del roadmap documentado.
