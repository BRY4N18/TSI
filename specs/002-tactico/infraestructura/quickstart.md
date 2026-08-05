# Quickstart: Validar el stack `tactico`

## Prerrequisitos

- Docker Desktop corriendo.
- El stack operativo debe estar levantado al menos una vez para que la red `pipeline-net` exista (`docker compose -f docker/docker-compose.infraestructura.yml up -d`) — el stack `tactico` la referencia como red externa.
- Archivo `docker/docker-compose.tactico.yml` implementado (tarea de la fase `/speckit-tasks` / `/speckit-implement`, no de este documento).

## 1. Levantar el stack `tactico` de forma aislada (User Story 1)

```bash
docker compose -f docker/docker-compose.tactico.yml up -d
docker compose -f docker/docker-compose.tactico.yml ps
```

**Resultado esperado**: los 5 servicios (`tactico-clickhouse`, `tactico-airflow-postgres`, `tactico-airflow-init`, `tactico-airflow-webserver`, `tactico-airflow-scheduler`) llegan a estado `healthy` (o `exited (0)` para `tactico-airflow-init`, que corre una vez) en menos de 5 minutos (SC-001).

Verificar que el stack operativo sigue intacto:

```bash
docker compose -f docker/docker-compose.infraestructura.yml ps
```

**Resultado esperado**: ningún contenedor del stack operativo se reinició ni cambió de estado.

## 2. Verificar ClickHouse

```bash
curl "http://localhost:8123/?user=tactico&password=tactico&query=SELECT%201"
```

**Resultado esperado**: respuesta `1`.

Base analítica del stack (variable `CLICKHOUSE_DB`, default `tsi_tactico`). Si el volumen ya existía antes de añadir el init script, créala una vez:

```bash
curl "http://localhost:8123/?user=tactico&password=tactico" --data-binary "CREATE DATABASE IF NOT EXISTS tsi_tactico"
```

En DBeaver: **Database/Schema** = `tsi_tactico` (mismo valor que `CLICKHOUSE_DB`).

Crear una tabla de prueba (para la validación de persistencia del paso 4):

```bash
curl "http://localhost:8123/?user=tactico&password=tactico" --data-binary "CREATE TABLE IF NOT EXISTS tsi_tactico.ping (id UInt32) ENGINE = MergeTree() ORDER BY id"
curl "http://localhost:8123/?user=tactico&password=tactico" --data-binary "INSERT INTO tsi_tactico.ping VALUES (1)"
```

## 3. Verificar Airflow

Abrir `http://localhost:8090` en el navegador, autenticarse con las credenciales de desarrollo definidas en el `.env` del compose `tactico`.

**Resultado esperado**: la UI carga, el listado de DAGs aparece vacío (ningún DAG de negocio en esta fase — ver `data-model.md`).

## 4. Verificar persistencia entre reinicios (User Story 2 / SC-003)

```bash
docker compose -f docker/docker-compose.tactico.yml restart
```

Repetir la consulta del paso 2:

```bash
curl "http://localhost:8123/?user=tactico&password=tactico&query=SELECT%20*%20FROM%20tsi_tactico.ping"
```

**Resultado esperado**: sigue devolviendo `1` — los datos sobrevivieron al reinicio.

## 5. Verificar conectividad Airflow → Pinot y Airflow → ClickHouse (User Story 3 / SC-004)

Con ambos stacks levantados:

```bash
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler bash -c "curl -sf http://pinot-broker:8099/health && echo PINOT_OK"
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler bash -c "curl -sf http://tactico-clickhouse:8123/ping && echo CLICKHOUSE_OK"
```

**Resultado esperado**: ambos comandos imprimen su marca `_OK` correspondiente.

## 6. Limpieza (opcional, destruye datos)

```bash
docker compose -f docker/docker-compose.tactico.yml down -v
```

Usar solo si se quiere empezar de cero — borra los volúmenes `tactico-clickhouse-data` y `tactico-airflow-metadata`.
