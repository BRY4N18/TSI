# Módulo: Informes Tácticos Compuestos

**Ubicación:** `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`
**Departamento:** Emergencias
**Feature paraguas:** `002-tactico` (hermano de `infraestructura/` y de `informes-tacticos-simples/`)
**Base:** `informestacticos/auditoria-esquemas-informes-v2.md`

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

**Estado (2026-08-02):** capa **backend completa y verificada contra el stack real** — 3 DAGs corriendo en `tactico-airflow-scheduler` (horario `@daily`, activos), 3 tablas materializadas en ClickHouse, 3 endpoints Django probados con `curl` de punta a punta (Pinot → DAG → ClickHouse → HTTP). Suite completa del backend: 1006 passed, 0 rotos. Pendiente: `frontend/` (integrar las 3 tarjetas en los workpanels de `informes-tacticos-simples/frontend`, que tampoco existe todavía).

**Actualización (2026-08-06):** los 3 DAGs migraron a `dags/` (raíz del repo, reemplaza `docker/tactico/airflow-dags/`) y al patrón extract/transform/load-parquet definido en `../../infraestructura/`. Ver `backend/data-model.md` y `backend/tasks.md` (Addendum 2026-08-06) para el detalle — esquemas ClickHouse y endpoints Django sin cambios.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | DAGs de Airflow, esquema de tablas ClickHouse, endpoints de lectura de resultados materializados | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*.openapi.yaml`, `quickstart.md` |
| **Frontend** | [`frontend/`](./frontend/) | Integración de las tarjetas compuestas dentro de los 3 workpanels ya definidos en `informes-tacticos-simples/frontend/` | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Requiere `../../infraestructura/` (ClickHouse + Airflow) ya implementada y verificada — es prerrequisito duro, no opcional.
2. Especificar e implementar **backend** primero: DAGs + esquema ClickHouse + endpoint de lectura por informe.
3. Luego **frontend**, con `Depends-on: ../backend` — cada informe compuesto se integra como una tarjeta adicional dentro del workpanel de su módulo (`informes-tacticos-simples/frontend`), no como pantalla nueva separada.
4. Cambiar `.specify/feature.json` → `…/informes-tacticos-compuestos/backend` o `…/frontend` según la capa en curso.

## Dependencias de módulo

- Requiere: `../../infraestructura/` (stack `tactico`: ClickHouse + Airflow), `../informes-tacticos-simples/` (los 3 workpanels donde se integran estas tarjetas)
- Requiere (solo lectura, sin cambios): `registro-accidente`, `despacho-inteligente`, `seguimiento-cierre-de-casos` (`specs/003-operational/Emergencias/`) y, para el informe de pérdida de señal, `Dim_HistorialUbicacionUnidadEmergencia` / `Dim_ParametrosSeguimiento`

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`informes-tacticos-compuestos.md`), no `README.md`.
