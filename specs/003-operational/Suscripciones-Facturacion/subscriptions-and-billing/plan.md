# Implementation Plan: Suscripciones y Facturación

**Branch**: `subscriptions-and-billing` | **Date**: 2026-07-26 | **Spec**: `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/spec.md`

**Input**: Feature specification from `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/spec.md` (clarificaciones Session 2026-07-26 integradas).

## Summary

Implementar el módulo SaaS de suscripciones/facturación con enfoque **contract-first**: primero el contrato OpenAPI REST (`contracts/subscriptions-and-billing.openapi.yaml`) según `api-standards.md`; luego backend Django/DRF (**Vista → Servicio → Repositorio**, skills `django-expert` + `api-authentication`) con **Kafka como único canal de escritura**; finalmente Angular 17+ (skills `angular-architect` + `typescript-expert`) con servicios tipados y guards. Cubre RF-SUSF-001…010 / CU-O101–O111, jobs de facturación/dunning/renovación/mantenimiento, y pasarela simulada detrás de adaptador.

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

**Target Platform**: Linux containerizado (API + jobs) + SPA Proveedor/Administrador

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
| Security | PASS | JWT+RBAC; aislamiento por `idcliente`; sin PAN/CVV (RNF-001/002) |
| Compatibility | PASS | Contract-first OpenAPI; adaptador pasarela (RNF-008) |
| Maintainability | PASS | Capas + servicios por CU; observabilidad RNF-009 |
| Flexibility | PASS | Adaptador de pasarela sustituible |
| Safety | Not applicable | No participa en despacho ni decisión física de víctimas (spec §5) |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** Maintainability + Functional Suitability priorizan adaptador de pasarela y contract-first sobre optimización prematura del simulador (Safety no aplica). Ver `research.md` cierre.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/
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
│       ├── permissions.py            # IsProveedorCuenta, IsAdministradorBilling
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
        │   ├── catalogo-planes/          # Admin
        │   └── aprobaciones-downgrade/   # Admin
        ├── services/
        │   ├── suscripcion-api.service.ts
        │   ├── plan-api.service.ts
        │   ├── metodo-pago-api.service.ts
        │   ├── factura-api.service.ts
        │   └── models/suscripciones.types.ts
        ├── guards/
        │   ├── proveedor-billing.guard.ts
        │   └── admin-billing.guard.ts
        └── suscripciones.routes.ts
```

**Structure Decision:** App nueva `apps/suscripciones/` y módulo Angular `modules/suscripciones/` (reservados en la spec). Repositorios en `core/repositories/suscripciones/`. La lectura existente `core/repositories/soporte/suscripcion_repository.py` se alinea a Title Case / RN-017 o se depreca a favor del repo canónico de este módulo (sin imports cruzados de apps).

## Phase 0: Research (completado)

Ver `research.md` — contract-first, capas, Kafka-only-write, JWT/RBAC, jobs Guayaquil, simulador pasarela, seq factura, Angular guards, alineación casing con fixtures legacy.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/subscriptions-and-billing.openapi.yaml`

| Actor | Endpoints |
|-------|-----------|
| Proveedor | Alta suscripción, ver mia, cancelar, reintentar cobro, métodos de pago, solicitar cambio plan, historial facturas |
| Administrador | CRUD lógico planes, listar/aprobar/rechazar downgrades, historial facturas de cualquier cliente |
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
| `PlanListCreateView` / `PlanDetailView` | `CatalogoPlanService` | `PlanRepository` |
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
| `AdminBillingGuard` | catálogo + aprobaciones |

## Phase 2: Tasks (siguiente comando)

Ejecutar `/speckit-tasks` para generar `tasks.md`: contrato → repos → adaptador pasarela → servicios → jobs → views/permissions → contract tests → Angular types/services/guards/pages.
