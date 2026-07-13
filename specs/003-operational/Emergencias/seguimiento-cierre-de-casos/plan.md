# Implementation Plan: Seguimiento y Cierre de Casos

**Branch**: `seguimiento-cierre-de-casos` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/spec.md`

**Input**: Feature specification from `specs/003-operational/Emergencias/seguimiento-cierre-de-casos/spec.md` (clarificaciones Session 2026-07-09 integradas).

## Summary

Implementar el módulo de seguimiento GPS, cierre multi-despacho, historial y expedientes con enfoque **contract-first**: primero `contracts/seguimiento-cierre-de-casos.openapi.yaml` alineado a `api-standards.md`; luego backend Django/DRF en **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka**, jobs O37/depuración GPS y SSE para mapa operador; finalmente frontend Angular 17+ con servicios tipados y guards. Cubre CU-O25–O29, O37, O39, O42, O44 y RF-SEG-001–011.

## Traceability

- **Objetivo operacional:** trazabilidad completa despacho → cierre; SLA tiempos respuesta/transito/sitio.
- **UC cubiertos:** CU-O25, O26, O28, O29, O37, O39, O42, O44.
- **Dependencias:** `despacho-inteligente` (despacho Confirmado, O36), `registro-accidente`, `evidencia-unidad`, `incorporacion-clientes` (zonas condado), `autenticacion-y-rbac`.
- **Consumidores downstream:** reportes/aseguradoras vía expedientes cliente.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, JWT RS256, Kafka producer/consumer, Celery o APScheduler (jobs O37 + depuración), RxJS, EventSource (SSE), WeasyPrint/reportlab (PDF)

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal escritura dominio)

**Testing**: pytest + contract tests OpenAPI; Jasmine/Karma servicios, guards y SSE

**Target Platform**: Linux containerizado (API + workers) + SPA operador + app móvil unidad + portal cliente

**Project Type**: Web application (backend + frontend)

**Performance Goals**: GPS mapa cada 10s, latencia ≤5s (RNF-SEG-001); mapa 99.9% disponibilidad (RNF-SEG-003)

**Constraints**: API `/api/v1/`, envelope estándar, `Idempotency-Key`, Vista→Servicio→Repositorio, Kafka-only-write, SSE seguimiento, filtro cliente por `Dim_Condado`

**Scale/Scope**: Camino crítico post-despacho; N-N despachos; retención GPS 90d con 3 puntos clave por despacho

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | CU-O25–O44 + CA-SEG-001–014 trazables al contrato y data-model |
| Reliability | PASS | Jobs O37/depuración; historial append-only; idempotencia escrituras |
| Performance Efficiency | PASS | RNF-SEG-001 SSE push; ingestión GPS asíncrona Kafka |
| Interaction Capability | PASS | Mapa SSE RF-SEG-007; expediente PDF cliente |
| Security | PASS | JWT + RBAC; cliente sin activos/mapa (RN-SEG-005) |
| Compatibility | PASS | Contract-first; evento `DespachoAbortado` → despacho O36 |
| Maintainability | PASS | App `seguimiento/` dedicada; servicios por CU |
| Flexibility | PASS | Umbrales GPS/geofence configurables |
| Safety | PASS | Geofencing histéresis 30s; alerta GPS sin desasignar unidad |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** documentado en `research.md` (Maintainability vs Performance).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Emergencias/seguimiento-cierre-de-casos/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── seguimiento-cierre-de-casos.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── seguimiento/
│       ├── views/
│       │   ├── mapa_views.py              # RF-SEG-007 + SSE
│       │   ├── mi_seguimiento_views.py    # O25, O26, O39 (unidad)
│       │   ├── cierre_views.py            # O28, O42, O44
│       │   ├── historial_views.py         # O29 operador
│       │   ├── cliente_expediente_views.py # O29 cliente + PDF
│       │   └── urls.py
│       ├── services/
│       │   ├── registrar_posicion_gps_service.py    # O25 + geofencing O26
│       │   ├── registrar_llegada_service.py           # O26 manual
│       │   ├── cerrar_caso_service.py                 # O28
│       │   ├── cancelar_caso_service.py               # O42
│       │   ├── forzar_retiro_service.py               # O44
│       │   ├── abortar_mision_service.py              # O39
│       │   ├── mapa_seguimiento_service.py            # RF-SEG-007
│       │   ├── seguimiento_sse_service.py             # pub/sub SSE
│       │   ├── historial_emergencias_service.py       # RF-SEG-005
│       │   ├── expediente_service.py                  # RF-SEG-006
│       │   ├── expediente_pdf_service.py
│       │   └── eta_calculo_service.py                 # Haversine lineal
│       ├── jobs/
│       │   ├── gps_senal_perdida_job.py               # O37
│       │   └── gps_depuracion_job.py                  # RNF-SEG-004
│       ├── permissions.py
│       └── tests/
│           ├── api/
│           ├── services/
│           └── jobs/
└── core/
    └── repositories/
        └── seguimiento/
            ├── historial_ubicacion_repository.py
            ├── unidad_snapshot_repository.py
            ├── expediente_repository.py
            └── parametros_seguimiento_repository.py
        # Reutiliza: despacho/, geografia, estado_accidente, nota_accidente

frontend/
└── src/app/
    └── modules/seguimiento/
        ├── pages/
        │   ├── mapa-seguimiento/
        │   ├── historial-emergencias/
        │   ├── detalle-expediente/
        │   └── mi-seguimiento/           # app unidad
        ├── services/
        │   ├── seguimiento-api.service.ts
        │   ├── mi-seguimiento-api.service.ts
        │   ├── seguimiento-sse.service.ts
        │   ├── expediente-cliente-api.service.ts
        │   └── models/seguimiento.types.ts
        ├── guards/
        │   ├── operador-seguimiento.guard.ts
        │   ├── unidad-seguimiento.guard.ts
        │   └── cliente-expediente.guard.ts
        └── seguimiento.routes.ts
```

**Structure Decision:** Tercera app Emergencias `apps/seguimiento/` (excepción documentada como accidentes/despacho). Repositorios compartidos de despacho para lectura/escritura de `Fact_Despacho` e historial.

## Phase 0: Research (completado)

Ver `research.md` — resueltos: contract-first, app seguimiento, Kafka-only-write, SSE, geofencing en pipeline GPS, O39 vía `DespachoAbortado_topic`, auditoría O28, O42 mínimo, filtro condado cliente, jobs O37/depuración, Angular guards.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/seguimiento-cierre-de-casos.openapi.yaml`

| Rol | Endpoints |
|-----|-----------|
| Operador de emergencias | Mapa, SSE, historial, cerrar, cancelar, forzar retiro |
| Unidad de emergencia | GPS, llegada, abortar (+ cerrar/cancelar vía mismos endpoints con RBAC) |
| Cliente | Expedientes cerrados (condado), PDF |

**Flujos sin endpoint HTTP (orquestación interna):**

| CU/RF | Mecanismo |
|-------|-----------|
| O26 geofencing | `RegistrarPosicionGpsService` al ingestar GPS |
| O37 | Job `gps_senal_perdida_job` cada 30s |
| O39 → O36 | Kafka `DespachoAbortado_topic` → consumer despacho |
| RNF-SEG-004 | Job `gps_depuracion_job` diario |

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|-------------|----------|------------------------|
| `MapaSeguimientoView` | `MapaSeguimientoService` | `DespachoRepository`, `UbicacionUnidadRepository`, `EstadoAccidenteRepository` |
| `SeguimientoSseView` | `SeguimientoSseService` | pub/sub interno + Pinot read |
| `SeguimientoAccidenteView` | `MapaSeguimientoService` | repos seguimiento + despacho |
| `RegistrarPosicionView` | `RegistrarPosicionGpsService` | `HistorialUbicacionRepository`, `UnidadSnapshotRepository`, geofencing |
| `RegistrarLlegadaView` | `RegistrarLlegadaService` | `HistorialDespachoRepository`, `DespachoRepository` |
| `CerrarCasoView` | `CerrarCasoService` | repos despacho + `AccidenteRepository`, `EstadoAccidenteRepository` |
| `CancelarCasoView` | `CancelarCasoService` | repos + `NotaAccidenteRepository` |
| `ForzarRetiroView` | `ForzarRetiroService` | `HistorialDespachoRepository`; reevalúa `CerrarCasoService` |
| `AbortarMisionView` | `AbortarMisionService` | Kafka `DespachoAbortado_topic` |
| `HistorialEmergenciasView` | `HistorialEmergenciasService` | `ExpedienteRepository` |
| `ExpedienteOperadorView` | `ExpedienteService` | join completo Pinot |
| `ExpedienteClienteView` | `ExpedienteService` + filtro condado | `PreferenciasClienteRepository`, `GeografiaRepository` |
| `ExpedientePdfView` | `ExpedientePdfService` | `ExpedienteService` |
| `GpsSenalPerdidaJob` | servicio O37 | `HistorialUbicacionRepository`, `NotaAccidenteRepository` |
| `GpsDepuracionJob` | servicio depuración | `HistorialUbicacionRepository` |

**Flujo escritura GPS (O25):**

```text
POST /mi-seguimiento/posicion
  → RegistrarPosicionGpsService.registrar()
      → HistorialUbicacionRepository.publish()     → Dim_HistorialUbicacionUnidadEmergencia_topic
      → UnidadSnapshotRepository.publish()         → Dim_UnidadEmergencia_topic
      → GeofencingEvaluator.evaluar()              → (si aplica) RegistrarLlegadaService
      → EtaCalculoService.recalcular()
      → SeguimientoSseService.emit("seguimiento.posicion")
```

### Frontend — servicios y guards (prioridad 2, post-contrato)

| Artefacto | Contrato consumido |
|-----------|-------------------|
| `SeguimientoApiService` | `/seguimiento/mapa`, `/accidentes/{id}/seguimiento`, cierre, historial |
| `MiSeguimientoApiService` | `/mi-seguimiento/*` |
| `SeguimientoSseService` | `GET /seguimiento/stream` |
| `ExpedienteClienteApiService` | `/cliente/expedientes/*` |
| `OperadorSeguimientoGuard` | Mapa, historial, cierre |
| `UnidadSeguimientoGuard` | mi-seguimiento |
| `ClienteExpedienteGuard` | portal expedientes |

## Phase 2: Tasks (siguiente comando)

Ejecutar `/speckit-tasks` para generar `tasks.md` ordenado: contrato → repos → servicios → jobs → views → contract tests → consumer despacho abortado → Angular.

## Complexity Tracking

Sin violaciones de constitution que requieran excepción documentada. Tercera app Emergencias justificada por ciclo de vida y volumen de eventos GPS post-confirmación.
