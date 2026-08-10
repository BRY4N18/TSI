# Quickstart: Validar los 3 informes tácticos compuestos

## Prerrequisitos

- Stack `tactico` levantado y verificado (`specs/002-tactico/infraestructura/quickstart.md`).
- Stack operativo levantado con datos de prueba (Pinot poblado, incluyendo `Dim_HistorialUbicacionUnidadEmergencia` con al menos un hueco de señal conocido).
- Los 3 DAGs (`perdida_senal_dag.py`, `indice_calidad_dag.py`, `rendimiento_proveedor_dag.py`) implementados en `dags/etl/` (raíz del repo — desde 2026-08-06 reemplaza a `docker/tactico/airflow-dags/`, ver Addendum en `tasks.md`).
- Backend Django corriendo con los 3 endpoints de esta spec implementados.
- Un token JWT de un usuario con rol `Administrador`.

## 1. Disparar manualmente los 3 DAGs (sin esperar al horario)

```bash
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler airflow dags trigger perdida_senal_gps
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler airflow dags trigger indice_calidad_historico
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler airflow dags trigger rendimiento_por_proveedor
```

**Resultado esperado**: en la UI de Airflow (`http://localhost:8090`) las 3 corridas terminan en estado `success`.

## 2. Verificar la materialización directa en ClickHouse

```bash
curl -s -u tactico:tactico "http://localhost:8123/?query=SELECT+count()+FROM+tsi_tactico.perdida_senal_gps+FORMAT+JSON"
curl -s -u tactico:tactico "http://localhost:8123/?query=SELECT+*+FROM+tsi_tactico.indice_calidad_historico+ORDER+BY+periodo+FORMAT+JSON"
curl -s -u tactico:tactico "http://localhost:8123/?query=SELECT+*+FROM+tsi_tactico.rendimiento_por_proveedor+FORMAT+JSON"
```

**Resultado esperado**: filas presentes, coherentes con los datos de prueba sembrados en Pinot.

## 3. Verificar idempotencia (SC-003)

```bash
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler airflow dags trigger perdida_senal_gps
```

Repetir la consulta de conteo del paso 2 sobre `perdida_senal_gps` para el mismo período.

**Resultado esperado**: el conteo de filas para ese período no cambia tras la segunda corrida.

## 4. Verificar los 3 endpoints de lectura

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/compuestos/perdida-senal?desde=2026-07-01&hasta=2026-07-31"

curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/compuestos/indice-calidad?desde=2026-07-01&hasta=2026-07-31"

curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/compuestos/rendimiento-proveedor?desde=2026-07-01&hasta=2026-07-31"
```

**Resultado esperado**: `200`, `meta.materializado: true`, `data` con las filas correspondientes.

## 5. Verificar el caso "no materializado todavía" (FR-008)

```bash
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/compuestos/perdida-senal?desde=2099-01-01&hasta=2099-01-31"
```

**Resultado esperado**: `200`, `data: null`, `meta.materializado: false` — distinguible del caso "sin datos en el período" de los informes simples.

## 6. Verificar control de acceso (FR-009)

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $OPERADOR_TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/compuestos/perdida-senal?desde=2026-07-01&hasta=2026-07-31"
```

**Resultado esperado**: `403` — un token de rol Operador (no Administrador) no puede consultar informes compuestos, a diferencia de los 16 informes simples.
