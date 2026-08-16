# Módulo: Informes Tácticos Compuestos — ⚠️ SUSTITUIDO

> ## Estado: **sustituido por `specs/002-tactico/modelo-analitico/`** (2026-08-14)
>
> **No implementar nada nuevo desde aquí.** El diseño de este módulo —una tabla y un flujo por
> informe— es el que el modelo analítico existe para reemplazar. Con ~105 informes compuestos por
> delante, ese patrón son ~105 tablas y ~105 flujos, cada uno con su propia forma de calcular lo
> mismo y su propia oportunidad de discrepar.
>
> ### Qué se verificó antes de declararlo sustituido (T047)
>
> Las tres consultas equivalentes sobre el modelo están en `dags/lib/consultas/`. Comparadas con las
> cifras que estas tres tablas devuelven:
>
> | Informe | Tabla propia | Desde el modelo | Veredicto |
> |---|---|---|---|
> | Pérdida de señal | 714 huecos | **3 942** | La tabla analizaba el **16,9 %** de las posiciones |
> | Índice de calidad | índice 0.7296 | 0.7289 | Coincide salvo la cobertura de evidencia |
> | Rendimiento por proveedor | llegada 669.44 s | **669.44 s** | Idéntico; rechazos y abortos, corregidos |
>
> ⚠️ **Las diferencias son defectos de estos tres flujos, no de la migración.** Dos de sus consultas
> a Pinot **no llevan `LIMIT` explícito**, así que el cliente les aplica el suyo de 10 000 filas y
> truncan en silencio: 10 000 de 59 045 posiciones y 10 000 de 19 528 transiciones. Corriendo **su
> propia lógica sobre los datos completos** salen 3 942 huecos, 661 rechazos y 331 abortos — que es
> exactamente lo que devuelve el modelo.
>
> ### Lo que falta para retirarlo del todo
>
> Las tres tablas y sus tres flujos **siguen vivos**, porque tres repositorios del backend los leen:
> `backend/core/repositories/informes_tacticos/{perdida_senal,indice_calidad,rendimiento_proveedor}_repository.py`.
> Retirarlos sin repuntar esos repositorios dejaría los endpoints sirviendo datos congelados **sin
> error visible**, que es peor que cualquiera de los dos extremos.
>
> Secuencia pendiente, en este orden: repuntar los tres repositorios al modelo (o retirar sus
> endpoints), luego retirar los tres DAGs y sus definiciones de tabla. Registrado como T048 del
> módulo sustituto.

---

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
