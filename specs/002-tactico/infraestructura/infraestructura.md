# Índice — Stack `tactico` (infraestructura)

**Feature directory activa:** `specs/002-tactico/infraestructura` (ver `.specify/feature.json`)

Todo el alcance y el diseño de esta feature viven aquí. El compose real está en `docker/`.

| Artefacto | Rol |
| --- | --- |
| [spec.md](./spec.md) | Alcance (qué / por qué) + ISO 25010 |
| [plan.md](./plan.md) | Plan de implementación + Constitution Check |
| [research.md](./research.md) | Decisiones de investigación (imágenes, puertos, executor) |
| [data-model.md](./data-model.md) | Modelo conceptual de servicios/recursos (no Dim_/Fact_ de negocio) |
| [contracts/docker-compose-contract.md](./contracts/docker-compose-contract.md) | Contrato de puertos, hosts, volúmenes y conectividad |
| [quickstart.md](./quickstart.md) | Verificación operativa (arranque, persistencia, conectividad) |
| [tasks.md](./tasks.md) | Lista de tareas (estado de implementación) |

**Documento global de referencia:** `.specify/docs/infra/infrastructure.md` (§2.1 stack activo, §5.1 decisión).

**Código de despliegue:**

- `docker/docker-compose.tactico.yml`
- `docker/.env.tactico.example`
- `docker/tactico/airflow/` (Dockerfile custom + requirements.txt: pandas/pyarrow/pytest)
- `dags/` (raíz del repo) — DAGs, reemplaza a `docker/tactico/airflow-dags/`
- `ETL/` (raíz del repo) — staging Parquet, no versionado
