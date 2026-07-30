# Implementation Plan: Suscripciones y Facturación

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../subscriptions-and-billing.md`](../subscriptions-and-billing.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — stub Fase A; no duplicar OpenAPI/data-model en FE.


**Branch**: `subscriptions-and-billing` | **Date**: 2026-07-26 (enmienda actor 2026-07-30) | **Spec**: `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/spec.md`

**Input**: Feature specification from `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/spec.md` (clarificaciones Session 2026-07-26 + **Session 2026-07-30** actor RF-SUSF-001).

## Summary

**Autoridad UI:** Interaction Capability en [`../frontend/plan.md`](../frontend/plan.md) / [`../frontend/tasks.md`](../frontend/tasks.md). Este plan BE no es superficie de trabajo UI.


Implementar el módulo SaaS de suscripciones/facturación con enfoque **contract-first**: primero el contrato OpenAPI REST (`contracts/subscriptions-and-billing.openapi.yaml`) según `api-standards.md`; luego backend Django/DRF (**Vista → Servicio → Repositorio**, skills `django-expert` + `api-authentication`) con **Kafka como único canal de escritura**; finalmente Angular 17+ (skills `angular-architect` + `typescript-expert`) con servicios tipados y guards. Cubre RF-SUSF-001…010 / CU-O101–O111, jobs de facturación/dunning/renovación/mantenimiento, y pasarela simulada detrás de adaptador.

**Enmienda 2026-07-30 (en curso — Phase 12 T091–T095):** RF-SUSF-001 (CRUD `Dim_Plan`) pasa de **Administrador** a **Director de Estrategia** (JWT `DirectorEstrategia`). Administrador conserva RF-SUSF-003 (downgrades) y RF-SUSF-006 (facturas). Sin cambio de modelo de datos ni topics Kafka.

## Traceability

- **Objetivo operacional:** sostener el acceso del Proveedor según plan contratado y estado de cobro (RN-SUSF-017).
- **UC cubiertos:** CU-O106, O101, O104, O107, O102, O108, O105, O109, O110, O111.
- **Dependencias:** `incorporacion-clientes` / `autenticacion-y-rbac` (`Dim_Cliente`, JWT/RBAC), `core/notificaciones/`, Kafka+Pinot.
- **Consumidores downstream:** Soporte (`Fact_Suscripcion`/`idplan`), Partners-API (patrón mora), despacho (límites de plan — futuro filtro `Dim_Plan`).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, JWT Bearer RS256 (`api-authentication`), Kafka producer, Celery/APScheduler (jobs batch), RxJS

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal escritura dominio)

**Testing**: pytest + contract tests OpenAPI; Jasmine/Karma servicios y guards

**Target Platform**: Linux containerizado (API + jobs) + SPA Proveedor / Administrador / Director de Estrategia

**Project Type**: Web application (backend + frontend)

**Performance Goals**: Historial facturas ≤ 3 s (CA-SUSF-006); job facturación ≤ 30 min / 10 000 activas (RNF-SUSF-005); ventana jobs 02:00–05:00 America/Guayaquil

**Constraints**: `/api/v1/`, envelope `{data, meta}` / `{error, detail, code}`, `Idempotency-Key` en escrituras, Vista→Servicio→Repositorio, Kafka-only-write, sin PAN/CVV, impuestos=0 v1, Title Case de estados (`Activa`|`Suspendida`|`Cancelada`, etc.)

**Scale/Scope**: Hasta 10 000 suscripciones activas; camino no crítico de despacho (Safety N/A)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | RF-SUSF-001…010 + CA-SUSF-001…015 trazables a contrato y data-model |
| Reliability | PASS | Idempotencia cobro (RNF-003), consistencia eventual (RNF-004), dunning 0/3/7, seq factura con reintento (RN-026) |
| Performance Efficiency | PASS | RNF-005, CA-006 medibles |
| Interaction Capability | PASS | RNF-006 + estados UX vacío/carga/error en RF-006 |
| Security | PASS | JWT+RBAC; aislamiento por `idcliente`; sin PAN/CVV; **RF-001 solo `DirectorEstrategia`** (RNF-001/002, Session 2026-07-30) |
| Compatibility | PASS | Contract-first OpenAPI; adaptador pasarela (RNF-008) |
| Maintainability | PASS | Capas + servicios por CU; observabilidad RNF-009 |
| Flexibility | PASS | Adaptador de pasarela sustituible |
| Safety | Not applicable | No participa en despacho ni decisión física de víctimas (spec §5) |

**Post-Design Gate (2026-07-26):** PASS — sin violaciones ni excepciones abiertas.

**Post-Design Gate (enmienda 2026-07-30):** PASS condicionado a T091–T095 (Phase 12) — spec/plan/contrato ya separan actores; código/UI aún asumen Admin en CRUD planes (gap conocido, no excepción constitucional permanente).

**Tie-Breaker:** Maintainability + Functional Suitability priorizan adaptador de pasarela y contract-first sobre optimización prematura del simulador (Safety no aplica). Ver `research.md` cierre.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/backend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── subscriptions-and-billing.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── suscripciones/
│       ├── views/                    # DRF APIViews delgadas
│       ├── urls.py
│       ├── permissions.py            # IsProveedorCuenta, IsAdministradorBilling, IsDirectorEstrategiaBilling
│       ├── authentication.py         # reutiliza JWT de cuentas_clientes / core.auth
│       ├── services/
│       │   ├── alta_suscripcion_service.py              # RF-010 / O111
│       │   ├── catalogo_plan_service.py                 # RF-001 / O106
│       │   ├── metodo_pago_service.py                   # RF-002 / O101
│       │   ├── cambio_plan_service.py                   # RF-003 / O104
│       │   ├── generacion_factura_service.py            # RF-004 / O107
│       │   ├── cobro_service.py                         # RF-005 / O102
│       │   ├── consulta_factura_service.py              # RF-006 / O108
│       │   ├── mora_suscripcion_service.py              # RF-007 / O105
│       │   ├── renovacion_service.py                    # RF-008 / O109
│       │   ├── cancelacion_service.py                   # RF-009 / O110
│       │   ├── evaluacion_acceso_service.py             # RN-017 (gate reutilizable)
│       │   └── pasarela/
│       │       ├── base.py                              # Puerto/adaptador
│       │       └── simulador_pasarela.py                # RN-024
│       ├── jobs/
│       │   ├── facturacion_mensual_job.py
│       │   ├── dunning_job.py
│       │   ├── renovacion_job.py
│       │   └── mantenimiento_activo_job.py              # RN-020
│       └── tests/
│           ├── api/
│           ├── services/
│           ├── jobs/
│           └── unit/
└── core/
    └── repositories/
        └── suscripciones/
            ├── plan_repository.py
            ├── metodo_pago_repository.py
            ├── suscripcion_repository.py                # extender lectura existente en soporte/
            ├── factura_repository.py
            └── solicitud_cambio_plan_repository.py

frontend/
└── src/app/
    └── modules/suscripciones/
        ├── pages/
        │   ├── mi-suscripcion/
        │   ├── metodos-pago/
        │   ├── historial-facturas/
        │   ├── cambio-plan/
        │   ├── catalogo-planes/          # consulta + CRUD si DirectorEstrategia
        │   └── aprobaciones-downgrade/   # Administrador
        ├── services/
        │   ├── suscripcion-api.service.ts
        │   ├── plan-api.service.ts
        │   ├── metodo-pago-api.service.ts
        │   ├── factura-api.service.ts
        │   └── models/suscripciones.types.ts
        ├── guards/
        │   ├── proveedor-billing.guard.ts
        │   ├── admin-billing.guard.ts
        │   └── director-estrategia-billing.guard.ts   # T093
        └── suscripciones.routes.ts
```

**Structure Decision:** App nueva `apps/suscripciones/` y módulo Angular `modules/suscripciones/` (reservados en la spec). Repositorios en `core/repositories/suscripciones/`. La lectura existente `core/repositories/soporte/suscripcion_repository.py` se alinea a Title Case / RN-017 o se depreca a favor del repo canónico de este módulo (sin imports cruzados de apps).

## Phase 0: Research (completado + enmienda actor)

Ver `research.md` — contract-first, capas, Kafka-only-write, JWT/RBAC (**Decision 4 + Decision 12**), jobs Guayaquil, simulador pasarela, seq factura, Angular guards, alineación casing con fixtures legacy.

## Phase 1: Design & Contracts (completado + enmienda OpenAPI 2026-07-30)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/subscriptions-and-billing.openapi.yaml`

| Actor | Endpoints |
|-------|-----------|
| Proveedor | Alta suscripción, ver mia, cancelar, reintentar cobro, métodos de pago, solicitar cambio plan, historial facturas |
| Director de Estrategia | CRUD lógico planes (`Dim_Plan`) — RF-SUSF-001; rol JWT `DirectorEstrategia` |
| Administrador | Listar/aprobar/rechazar downgrades, historial facturas de cualquier cliente (**no** CRUD de planes) |
| Sistema | Sin HTTP público — jobs batch |

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|-------------|----------|------------------------|
| `AltaSuscripcionView` | `AltaSuscripcionService` | `SuscripcionRepository`, `PlanRepository`, `ClienteRepository` (`backend/core/repositories/cuentas_clientes/cliente_repository.py` — patch `plan_suscripcion`), `FacturaRepository`+`CobroService` si hay método |
| `MiSuscripcionView` | `EvaluacionAccesoService` + lectura | `SuscripcionRepository`, `PlanRepository` |
| `CancelarSuscripcionView` | `CancelacionService` | `SuscripcionRepository` |
| `ReintentarCobroView` | `MoraSuscripcionService` | `FacturaRepository`, `SuscripcionRepository`, adaptador pasarela |
| `MetodoPagoListCreateView` | `MetodoPagoService` | `MetodoPagoRepository` (+ mora si Suspendida) |
| `SolicitudCambioPlanView` | `CambioPlanService` | `SolicitudCambioPlanRepository`, `SuscripcionRepository`, `PlanRepository`, `ClienteRepository` |
| `Aprobar/RechazarCambioPlanView` | `CambioPlanService` | idem |
| `PlanListCreateView` / `PlanDetailView` | `CatalogoPlanService` | `PlanRepository` — **POST/PATCH:** `IsDirectorEstrategiaBilling`; **GET:** Proveedor o Admin o Director |
| `FacturaListView` / `FacturaDetailView` | `ConsultaFacturaService` | `FacturaRepository`, `MetodoPagoRepository` |
| Jobs | `GeneracionFacturaService`, `CobroService`, `RenovacionService`, `MoraSuscripcionService` | repos + pasarela + `core/notificaciones` |

**Flujo escritura Kafka (ejemplo alta + primera factura):**

```text
POST /suscripciones
  → AltaSuscripcionService.ejecutar()
      → SuscripcionRepository.publish()     → Fact_Suscripcion_topic
      → ClienteRepository.publish_patch()   → Dim_Cliente_topic (plan_suscripcion)
      → [si método activo]
           GeneracionFacturaService.para_suscripcion()
             → FacturaRepository.publish()  → Fact_Factura_topic
           CobroService.intentar()
             → pasarela (simulador) + FacturaRepository.publish()
```

### Frontend — servicios y guards (prioridad 2, post-contrato)

| Artefacto | Contrato consumido |
|-----------|-------------------|
| `SuscripcionApiService` | `/suscripciones*` |
| `PlanApiService` | `/suscripciones/planes*` |
| `MetodoPagoApiService` | `/suscripciones/metodos-pago*` |
| `FacturaApiService` | `/suscripciones/facturas*` |
| `ProveedorBillingGuard` | rutas Proveedor |
| `AdminBillingGuard` | aprobaciones downgrade |
| `DirectorEstrategiaBillingGuard` | catálogo planes (crear/editar/desactivar) |

## Phase 2: Tasks

`tasks.md` existe (T001–T090 done). **Siguiente implementación:** Phase 12 T091–T095 (actor RF-001). Opcional: `/speckit-tasks` solo si se reabre alcance más allá de esa phase.
