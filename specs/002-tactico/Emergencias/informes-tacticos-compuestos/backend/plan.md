# Implementation Plan: Informes Tácticos Compuestos de Emergencias (Backend)

**Branch**: `informes-tacticos-compuestos` | **Date**: 2026-08-01 | **Spec**: `specs/002-tactico/Emergencias/informes-tacticos-compuestos/backend/spec.md`

**Input**: Feature specification from `specs/002-tactico/Emergencias/informes-tacticos-compuestos/backend/spec.md`
**Capa hermana (UI):** `../frontend/` — ver [`../informes-tacticos-compuestos.md`](../informes-tacticos-compuestos.md).
**Prerrequisito duro:** `../../infraestructura/` (ClickHouse + Airflow) ya implementada y verificada (`specs/002-tactico/infraestructura/`).

## Summary

Implementar 3 DAGs de Airflow (uno por informe: pérdida de señal GPS, índice de calidad consolidado, rendimiento por proveedor) que leen de Pinot (solo lectura) y materializan su resultado en tablas propias de ClickHouse, más 3 endpoints Django de solo lectura que sirven esos resultados ya calculados — sin recomputar nada en el momento de la consulta. Los DAGs viven en `docker/tactico/airflow-dags/` (bind mount del stack `tactico`, fuera del contenedor de Django) y son código Python **autocontenido**: no importan del paquete `backend/` porque corren en el contenedor `tactico-airflow-scheduler`, que no tiene ese código montado.

## Traceability

- **Objetivo estratégico:** E3 (escalar sin degradar — el caso de uso testigo de Airflow), E4 (histórico como ventaja competitiva).
- **Base:** `informestacticos/auditoria-esquemas-informes-v2.md` — los 3 informes compuestos priorizados para Emergencias.
- **Dependencias:** `../../infraestructura/` (stack `tactico`), `../informes-tacticos-simples/` (los 4 indicadores base que el índice de calidad consolida ya están implementados ahí).
- **Consumidores downstream:** `../frontend/` (tarjetas dentro de los 3 workpanels ya definidos en `informes-tacticos-simples/frontend/`).

## Technical Context

**Language/Version**: Python 3.11, tanto para los DAGs (imagen `apache/airflow:2.9.3` ya definida en `docker-compose.tactico.yml`) como para los endpoints Django (consistente con `informes-tacticos-simples`).

**Primary Dependencies**:
- DAGs: solo `requests` (ya viene en la imagen base de Airflow) contra las APIs HTTP de Pinot (broker `/query/sql`) y ClickHouse (`/` con `FORMAT JSONEachRow`) — **sin** driver de ClickHouse de terceros (`clickhouse-connect`/`clickhouse-driver`), para no depender de instalar paquetes nuevos en la imagen de Airflow (ver `research.md` §1).
- Endpoints Django: nuevo `core/clickhouse/client.py` (mismo patrón que `core/pinot/client.py`: HTTP + `requests`, solo lectura), reutiliza `apps/informes_tacticos/{permissions,periodo,envelope}.py` ya existentes.

**Storage**: ClickHouse (3 tablas nuevas, una por informe, ver `data-model.md`) como destino; Pinot como fuente de solo lectura (mismas tablas que `informes-tacticos-simples` + `Dim_HistorialUbicacionUnidadEmergencia`, `Dim_ParametrosSeguimiento`, `Dim_EvidenciaFoto`).

**Testing**: pytest para los endpoints Django (mock del cliente ClickHouse, mismo patrón `mock_pinot` pero para ClickHouse) y para la lógica pura de cada DAG (funciones de agregación/detección de huecos extraídas a módulos testeables, sin necesitar un scheduler de Airflow real corriendo — ver `research.md` §4). Verificación de idempotencia (SC-003) y de la detección de huecos (SC-002) vía esos tests unitarios, no vía Airflow.

**Target Platform**: Contenedor `tactico-airflow-scheduler` (DAGs) + backend Django ya desplegado (`docker/accidentes.yml`, endpoints de lectura).

**Project Type**: Web application (backend Django existente, ampliado) + componente de orquestación batch (Airflow, infraestructura ya provista).

**Performance Goals**: SC-001 — cualquier informe compuesto responde en menos de 2s (lectura directa de ClickHouse, sin cómputo en el momento).

**Constraints**: Los DAGs son idempotentes por período (FR-003); nunca escriben en Pinot (FR-002); el endpoint de lectura distingue "no materializado todavía" de "sin datos" (FR-008); acceso restringido a rol de supervisión (FR-009, ver desviación de roles más abajo).

**Scale/Scope**: 3 DAGs, 3 tablas ClickHouse, 3 endpoints Django de lectura. Ejecución diaria por defecto (ver Assumptions de la spec).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| Functional Suitability | PASS | 3 RF trazables 1:1 a los informes priorizados de `auditoria-esquemas-informes-v2.md` (US1-US3 de la spec) |
| Reliability | PASS | Idempotencia por período (FR-003, SC-003); un fallo de DAG no afecta el camino crítico de despacho (batch, desacoplado) |
| Performance Efficiency | PASS | SC-001 (<2s) declarado — se cumple por diseño al leer ya-materializado, no recalculado |
| Interaction Capability | N/A en esta capa — se evalúa en `../frontend/plan.md` |
| Security | PASS | RBAC existente reutilizado (rol de supervisión, ver desviación abajo); DAGs no exponen credenciales nuevas (usa las ya definidas en `docker/.env.tactico`) |
| Compatibility | PASS | Mismo Pinot/ClickHouse/Django ya verificados; sin dependencias nuevas de terceros (research.md §1) |
| Maintainability | PASS | DAGs autocontenidos y simples (un archivo por informe + lib compartida mínima); endpoints Django siguen el mismo patrón Vista→Servicio→Repositorio que `informes-tacticos-simples` |
| Flexibility | PASS | Cada DAG y su tabla ClickHouse son independientes — añadir/quitar un informe compuesto no afecta a los otros dos |
| Safety | N/A | Informes históricos/batch, fuera del camino crítico de seguridad física |

**Desviación de `spec.md` corregida (consistente con `informes-tacticos-simples`):** el rol "Supervisor" no existe en el sistema (`.specify/docs/actors.md`); FR-009 se implementa restringiendo a `Administrador` (el rol operativo real más cercano a una función de supervisión), no a `Operador`.

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Re-check post Phase 1 (diseño completado)**: `research.md`, `data-model.md`, `contracts/informes-tacticos-compuestos.openapi.yaml` y `quickstart.md` no introducen ningún componente en el camino crítico de despacho ni datos sensibles nuevos (siguen siendo agregados/históricos). El diseño no cambia ninguna de las 9 evaluaciones anteriores. **Gate result: PASS.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Emergencias/informes-tacticos-compuestos/
├── informes-tacticos-compuestos.md   # índice del módulo
├── backend/                          # esta capa
│   ├── spec.md
│   ├── plan.md                       # este archivo
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── contracts/
│   │   └── informes-tacticos-compuestos.openapi.yaml
│   ├── checklists/requirements.md
│   └── tasks.md
└── frontend/                         # Interaction Capability — stub, se completa después
```

### Source Code (repository root)

```text
docker/tactico/airflow-dags/
├── lib/                                   # NUEVO — código compartido de los 3 DAGs (autocontenido, sin importar de backend/)
│   ├── __init__.py
│   ├── pinot_http_client.py               # cliente HTTP mínimo a Pinot (solo lectura), independiente de Django
│   └── clickhouse_http_client.py          # cliente HTTP mínimo a ClickHouse (lectura + escritura batch)
├── perdida_senal_dag.py                   # NUEVO — US1
├── indice_calidad_dag.py                  # NUEVO — US2
└── rendimiento_proveedor_dag.py           # NUEVO — US3

backend/
├── core/
│   └── clickhouse/                        # NUEVO — mismo patrón que core/pinot/
│       ├── __init__.py
│       └── client.py                      # ClickHouseClient, solo lectura desde Django
├── core/repositories/informes_tacticos/
│   ├── perdida_senal_repository.py        # NUEVO
│   ├── indice_calidad_repository.py       # NUEVO
│   └── rendimiento_proveedor_repository.py # NUEVO
└── apps/informes_tacticos/
    ├── services/
    │   └── informes_compuestos_service.py # NUEVO — 3 métodos, uno por informe
    ├── views/
    │   └── compuestos_views.py            # NUEVO — 3 vistas DRF
    ├── permissions.py                     # existente — se añade InformesTacticosCompuestosPermission (solo Administrador)
    └── urls.py                            # existente — se añaden 3 rutas bajo /informes-tacticos/compuestos/*

frontend/
└── src/app/modules/emergencias/informes-tacticos/   # definido en ../frontend/plan.md (a crear después) — 3 tarjetas nuevas dentro de los workpanels ya existentes
```

**Structure Decision**: Los DAGs viven en `docker/tactico/airflow-dags/` (ya provisto por `../../infraestructura/`) como código **autocontenido**, con su propia `lib/` mínima de clientes HTTP — no importan de `backend/` porque el contenedor `tactico-airflow-scheduler` no tiene ese paquete montado ni instalado (son dos runtimes/contenedores distintos). El backend Django gana un cliente ClickHouse nuevo (`core/clickhouse/client.py`, mismo patrón de solo-lectura que `core/pinot/client.py`) y 3 repositorios más dentro de la misma app `informes_tacticos` ya existente — no se crea una app Django nueva, porque estos 3 informes son una extensión natural del mismo módulo de informes tácticos, solo que leen de una fuente distinta (ClickHouse en vez de Pinot).

## Complexity Tracking

*Sin violaciones — no aplica.*
