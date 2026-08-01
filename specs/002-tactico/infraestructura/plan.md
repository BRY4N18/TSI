# Implementation Plan: Infraestructura Táctica (ClickHouse + Airflow)

**Branch**: `002-tactico` | **Date**: 2026-08-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/infraestructura/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Levantar un segundo stack de infraestructura, `docker-compose.tactico.yml`, con ClickHouse (almacén analítico batch) y Apache Airflow (orquestador), prefijados `tactico-*`, que conviven en la misma red Docker (`pipeline-net`) que el stack operativo existente (Kafka + Pinot) sin modificarlo. Esto materializa el roadmap ya documentado en `.specify/docs/infra/infrastructure.md` §5.1 ("ClickHouse + Airflow para capa analítica batch (futuro)"): Pinot sigue siendo el serving en tiempo real; ClickHouse es la capa batch/histórica para los informes tácticos compuestos que se especificarán después. Esta spec solo entrega la infraestructura verificable (servicios arriba, persistencia, conectividad de red) — ningún DAG de negocio ni tabla de dominio.

## Technical Context

**Language/Version**: N/A a nivel de aplicación — esta feature es infraestructura declarativa (Docker Compose YAML), no código de aplicación.

**Primary Dependencies**: ClickHouse (imagen oficial `clickhouse/clickhouse-server`), Apache Airflow (imagen oficial `apache/airflow`, ejecutor `LocalExecutor`), PostgreSQL (metastore de Airflow, imagen oficial `postgres`).

**Storage**: ClickHouse (analítica batch, volumen propio `tactico-clickhouse-data`) + PostgreSQL (metadatos de Airflow: DAGs, runs, conexiones, variables — volumen propio `tactico-airflow-metadata`). Ninguno reemplaza a Pinot; Pinot sigue siendo la única fuente operativa.

**Testing**: Verificación manual vía `docker compose` (`ps`, healthchecks) + consultas de humo documentadas en `quickstart.md` (crear tabla de prueba en ClickHouse, listar DAGs en Airflow, tarea de conectividad Airflow→Pinot y Airflow→ClickHouse). No aplica framework de test de código porque no hay código de aplicación en esta feature.

**Target Platform**: Docker Compose en el entorno de desarrollo local del responsable único del proyecto (Windows con Docker Desktop), igual que el resto de `docker/*.yml` ya existentes.

**Project Type**: Infraestructura (nuevo archivo `docker/docker-compose.tactico.yml`, sin proyecto de código nuevo en `backend/` ni `frontend/`).

**Performance Goals**: No aplica umbral de latencia de negocio — es infraestructura de soporte para analítica batch (no está en el camino crítico de despacho). Meta operativa: stack completo arriba y healthy en < 5 min (SC-001 de la spec).

**Constraints**: No exponer puertos a internet (uso interno/desarrollo). No colisionar con los puertos ya reservados por `docker-compose.infraestructura.yml` (2181, 9092, 9000, 8099, 8098) ni por `accidentes.yml` (8000, 4200). No modificar ni reiniciar el stack operativo existente para levantar este.

**Scale/Scope**: 1 nodo ClickHouse (single-node, no cluster — no hay volumen que lo justifique todavía) + Airflow con `LocalExecutor` (single-node, sin Celery/Kubernetes executor — no hay concurrencia de DAGs que lo justifique todavía) + 1 Postgres de metastore. Alcance explícitamente limitado a lo que las specs futuras de informes compuestos van a necesitar; no se sobre-dimensiona.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Esta feature es infraestructura pura (sin lógica de negocio ni UI), así que varias características ISO/IEC 25010 aplican a nivel de la capa que otras specs construirán encima, no aquí. Se declara explícitamente cuáles aplican ahora y cuáles quedan diferidas:

1. **Functional Suitability** — Aplica. La necesidad de negocio trazada es habilitar los informes tácticos compuestos del departamento de Gestión de Emergencias (ver `informestacticos/auditoria-esquemas-informes-v2.md`), que hoy no se pueden construir sin una capa batch separada de Pinot. Esta spec entrega exactamente el prerrequisito de infraestructura, nada más.
2. **Reliability** — Aplica parcialmente. Healthchecks por servicio (siguiendo el mismo patrón que `docker-compose.infraestructura.yml`) y persistencia con volúmenes con nombre (FR-006). Recuperación ante fallo de un DAG concreto es "Not applicable" en esta spec — no hay DAGs de negocio todavía.
3. **Performance Efficiency** — Not applicable como umbral de negocio: este stack no participa del camino crítico de despacho (`registro → asignación → despacho → confirmación`), que es donde la constitución exige latencia medible. Se declara solo la meta operativa de arranque (SC-001).
4. **Interaction Capability** — Not applicable: no hay interfaz de usuario final en esta spec. La interfaz web de Airflow es una herramienta de administración interna, no una pantalla de operador/técnico/soporte.
5. **Security** — Aplica. Airflow requiere autenticación (FR-008); ningún puerto se expone fuera de la red local de desarrollo (Assumptions); no se maneja aquí ningún dato sensible real (víctimas, ubicación) — estas tablas y DAGs de negocio son objeto de las specs siguientes, que sí deberán abordar control de acceso a datos sensibles cuando lean de Pinot y escriban en ClickHouse.
6. **Compatibility** — Aplica. FR-003 exige convivencia sin colisión con el stack operativo existente (mismos red `pipeline-net`, puertos distintos, nombres prefijados `tactico`).
7. **Maintainability** — Aplica con prioridad, según el principio de proyecto individual de la constitución: nombrado consistente (`tactico-*`), documentación actualizada en `infrastructure.md` (FR-009), reutilización del mismo patrón de healthcheck/depends_on ya usado en el compose operativo, para que el único responsable del proyecto no tenga que aprender un patrón nuevo.
8. **Flexibility** — Aplica. El stack se levanta/detiene independientemente del operativo (FR-002), permitiendo evolución o reemplazo futuro de la capa analítica sin tocar Pinot/Kafka.
9. **Safety** — Not applicable directo: esta infraestructura no participa del camino crítico de seguridad física (despacho de emergencias). Se documenta explícitamente como no aplicable en este nivel; sí volverá a evaluarse en la spec de informes compuestos si algún informe táctico llegara a alimentar decisiones operativas en tiempo real (hoy no es el caso — son informes históricos/batch).

**Gate result: PASS.** No hay violaciones que requieran entrada en Complexity Tracking.

**Re-check post Phase 1 (diseño completado)**: `research.md`, `data-model.md`, `contracts/docker-compose-contract.md` y `quickstart.md` no introducen ningún dato sensible, endpoint público ni componente en el camino crítico de despacho. El diseño no cambia ninguna de las 9 evaluaciones anteriores. **Gate result: PASS.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/infraestructura/   # feature_directory activa
├── infraestructura.md               # Índice de esta carpeta
├── spec.md                          # Alcance (qué / por qué) + ISO 25010
├── plan.md                          # This file (/speckit-plan)
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── contracts/
    └── docker-compose-contract.md
```

### Source Code (repository root)

```text
docker/
├── docker-compose.infraestructura.yml   # Existente — Kafka + Pinot, NO se modifica
├── accidentes.yml                       # Existente — django + frontend, NO se modifica
└── docker-compose.tactico.yml           # NUEVO — este feature

  services (todas prefijadas tactico-):
    tactico-clickhouse            # almacén analítico batch
    tactico-airflow-postgres      # metastore de Airflow (interno, no expuesto)
    tactico-airflow-init          # job de inicialización (migraciones + usuario admin), corre una vez
    tactico-airflow-webserver     # UI de administración
    tactico-airflow-scheduler     # planificador de DAGs

  networks:
    pipeline-net (external: true)  # red ya creada por docker-compose.infraestructura.yml — se une a ella para tener visibilidad de Pinot/Kafka

  volumes:
    tactico-clickhouse-data
    tactico-airflow-metadata
    tactico-airflow-dags           # carpeta de DAGs, vacía en esta fase (bind mount, sin DAGs de negocio)

.specify/docs/infra/infrastructure.md   # actualizar §5.1 de "roadmap futuro" a stack activo, con puertos reales (FR-009)
```

**Structure Decision**: Un único archivo compose nuevo (`docker/docker-compose.tactico.yml`), sibling de los dos ya existentes en `docker/`, sin tocarlos. Se une a la red externa `pipeline-net` (ya definida por `docker-compose.infraestructura.yml`) para que Airflow tenga visibilidad de red hacia Pinot/Kafka sin necesidad de exponer puertos adicionales del stack operativo. No se crea ningún directorio de aplicación (`backend/`, `frontend/`) porque no hay código de negocio en esta feature.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
