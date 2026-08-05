# Implementation Plan: Informes Tácticos Simples de Emergencias (Backend)

**Branch**: `informes-tacticos-simples` | **Date**: 2026-08-01 | **Spec**: `specs/002-tactico/Emergencias/informes-tacticos-simples/backend/spec.md`

**Input**: Feature specification from `specs/002-tactico/Emergencias/informes-tacticos-simples/backend/spec.md`
**Capa hermana (UI):** `../frontend/` — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).
**Autoridad UI:** Interaction Capability en `../frontend/plan.md` / `../frontend/tasks.md` (a crear después). Este plan BE no es superficie de trabajo UI.

## Summary

Implementar 16 endpoints de agregación de solo lectura sobre Apache Pinot (7 de Registro de Accidente, 6 de Despacho Inteligente, 3 de Seguimiento y Cierre de Casos), como una app Django nueva (`backend/apps/informes_tacticos`) en capas **Vista → Servicio → Repositorio**, reutilizando `PinotClient` (`backend/core/pinot/client.py`) ya existente. Ningún endpoint escribe en Pinot ni publica en Kafka — es una capa de lectura pura sobre datos que ya producen `accidentes`, `despacho` y `seguimiento`.

## Traceability

- **Objetivo estratégico:** E1 (impacto en tráfico, captación), E3 (escalar sin degradar — ratio demanda/capacidad), E4 (histórico como ventaja competitiva).
- **Base:** `informestacticos/auditoria-esquemas-informes-v2.md` — los 16 informes ya marcados ✅ Cubierto para Registro/Despacho/Seguimiento.
- **Dependencias:** `accidentes`, `despacho`, `seguimiento` (mismas tablas Pinot, sin tocar su código ni su esquema).
- **Consumidores downstream:** `../frontend/` (3 workpanels), y en el futuro `informes-tacticos-compuestos` (los DAG de Airflow leerán de las mismas tablas Pinot, no de estos endpoints).

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF), consistente con el resto de `backend/apps/*`.

**Primary Dependencies**: Django 5 + DRF, `PinotClient` (`backend/core/pinot/client.py`, ya existente — sin cliente nuevo), JWT RS256 + RBAC ya existente (`backend/core/auth/permissions.py`), envelope de respuesta estándar (`backend/core/api/response_envelope.py`).

**Storage**: Apache Pinot, exclusivamente de solo lectura (`Fact_Accidente`, `Fact_AccidenteTipoEstadoAccidente`, `Fact_Despacho`, `Fact_HistorialDespachoUnidad`, `Dim_UnidadEmergencia`, dimensiones geográficas). Ninguna tabla nueva, ningún cambio de esquema.

**Testing**: pytest, siguiendo el mismo layout que `backend/apps/accidentes/tests/` (`tests/repositories/`, `tests/services/`, `tests/api/`), con el fixture `mock_pinot` ya usado por otras apps para simular `PinotClient.query`.

**Target Platform**: Linux containerizado (mismo backend Django ya desplegado vía `docker/accidentes.yml`), sin infraestructura nueva.

**Project Type**: Web application (backend nuevo + frontend a definir en `../frontend/`)

**Performance Goals**: SC-001 de la spec — cualquiera de los 16 informes responde en menos de 3s para un rango de hasta 90 días.

**Constraints**: API `/api/v1/informes-tacticos/*`, envelope estándar, cada consulta Pinot declara `LIMIT` explícito (regla vinculante de `infrastructure.md` §4), filtros/orden/paginación en SQL — nunca en Python, sin INSERT/UPDATE a Pinot desde esta app.

**Scale/Scope**: 16 endpoints de agregación, 1 app Django nueva, sin tablas propias (repositorios de solo lectura sobre datos ya existentes).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| Functional Suitability | PASS | 16 RF trazables 1:1 a los informes ✅ Cubierto de `auditoria-esquemas-informes-v2.md` (FR-009) |
| Reliability | PASS | Solo lectura — un fallo de esta app no afecta el camino crítico de despacho (`accidentes`/`despacho`/`seguimiento` no dependen de ella) |
| Performance Efficiency | PASS | SC-001 (<3s) declarado; `LIMIT` explícito obligatorio (FR-003) evita degradar el broker de Pinot |
| Interaction Capability | N/A en esta capa — se evalúa en `../frontend/plan.md` (workpanels) |
| Security | PASS | RBAC existente (FR-007), sin credenciales nuevas, log de auditoría de uso (FR-008) sin registrar resultados |
| Compatibility | PASS | Mismo Pinot, mismo Django, mismo envelope — ninguna dependencia nueva de infraestructura |
| Maintainability | PASS | Vista→Servicio→Repositorio igual que `accidentes`/`despacho`/`seguimiento`; app nueva aislada, no modifica las 3 apps existentes |
| Flexibility | PASS | Cada informe es un endpoint independiente; añadir o quitar uno no afecta a los demás |
| Safety | N/A | Informes históricos/agregados, fuera del camino crítico de seguridad física (despacho en tiempo real) |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Emergencias/informes-tacticos-simples/
├── informes-tacticos-simples.md   # índice del módulo
├── backend/                       # esta capa (dominio + OpenAPI)
│   ├── spec.md
│   ├── plan.md                    # este archivo
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── contracts/
│   │   └── informes-tacticos-simples.openapi.yaml
│   ├── checklists/requirements.md
│   └── tasks.md
└── frontend/                      # Interaction Capability (Angular) — stub, se completa después
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── informes_tacticos/                     # NUEVO
│       ├── __init__.py
│       ├── apps.py
│       ├── urls.py                            # /api/v1/informes-tacticos/*
│       ├── repositories/
│       │   ├── registro_repository.py         # 7 métodos, 1 por informe de Registro
│       │   ├── despacho_repository.py         # 6 métodos, 1 por informe de Despacho
│       │   └── seguimiento_repository.py      # 3 métodos, 1 por informe de Seguimiento
│       ├── services/
│       │   ├── registro_informes_service.py
│       │   ├── despacho_informes_service.py
│       │   └── seguimiento_informes_service.py
│       ├── views/
│       │   ├── registro_views.py
│       │   ├── despacho_views.py
│       │   └── seguimiento_views.py
│       └── tests/
│           ├── repositories/
│           ├── services/
│           └── api/
└── core/
    └── pinot/client.py                        # existente, reutilizado sin cambios

frontend/
└── src/app/modules/emergencias/
    └── informes-tacticos/                     # definido en ../frontend/plan.md (a crear después)
```

**Structure Decision**: App Django nueva y aislada (`informes_tacticos`), en vez de añadir endpoints a `accidentes`/`despacho`/`seguimiento` — cada informe es una consulta de agregación propia, sin relación con los casos de uso de escritura de esas apps (registrar, despachar, cerrar). Mezclarlos ahí acoplaría lectura analítica con los flujos operativos críticos, violando Maintainability. Reutiliza `PinotClient` existente sin crear un cliente nuevo (Compatibility).

## Complexity Tracking

*Sin violaciones — no aplica.*
