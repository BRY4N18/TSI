# Implementation Plan: Onboarding y Validación de Región Operativa

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../incorporacion-regional.md`](../incorporacion-regional.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — stub Fase A; no duplicar OpenAPI/data-model en FE.


**Branch**: `003-operational-red-operativa-incorporacion-regional` | **Date**: 2026-07-21 | **Spec**: `specs/003-operational/Red-Operativa/incorporacion-regional/backend/spec.md`

**Input**: Feature specification from `specs/003-operational/Red-Operativa/incorporacion-regional/backend/spec.md`

## Summary

**Autoridad UI:** Interaction Capability en [`../frontend/plan.md`](../frontend/plan.md) / [`../frontend/tasks.md`](../frontend/tasks.md). Este plan BE no es superficie de trabajo UI.


Implementar el protocolo de validación de operatividad de una región (CU-O55/O60/O61/O62) con enfoque **contract-first**: primero contrato OpenAPI REST bajo `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** dentro de la app existente `red_operativa` (compartida con `alta-unidades`), con escritura exclusiva vía Kafka; finalmente frontend Angular 17+ con servicios tipados y guards de rol (Administrador / Director Tecnológico). Según lo clarificado en el spec: la validación es una revisión manual (sin checklist automatizado), una región puede reingresar a `CU-O55` desde `En_Alerta` o `Despublicada` para reactivarse, y la concurrencia en `Dim_RegionOperativa.estadoregion` se resuelve con último-INSERT-gana. `CU-O62` (despublicación automática) se documenta funcionalmente pero su disparador queda fuera de alcance de implementación (RN-REGON-005 — sin FK `Dim_UnidadEmergencia ↔ Dim_RegionOperativa`).

## Traceability

- **Objetivo Operacional (OP)**: OP-TSI-RED-01 (extensión: habilitar operación segura en nuevas regiones antes de recibir accidentes reales).
- **UC cubiertos**: CU-O55, CU-O60, CU-O61, CU-O62 (CU-O62 documentado, disparo no implementado — ver Complexity Tracking).
- **Mapeo de cumplimiento**:
  - Contract-first REST versionado (`/api/v1/red-operativa/regiones/...`).
  - Patrón Vista→Servicio→Repositorio; Kafka como único canal de escritura (`Dim_RegionOperativa_topic`, `Dim_ValidacionRegion_topic`).
  - JWT + RBAC: Administrador (ejecuta protocolo, CU-O55/O60), Director Tecnológico (aprobación final CU-O55, degradación/despublicación CU-O61) — dependencia `autenticacion-y-rbac`.
  - Regla de continuidad de casos activos (RF-REGON-003) valida en tiempo real contra `Fact_Accidente` (solo lectura, módulo Emergencias).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend Angular 17+)

**Primary Dependencies**: Django 5 + DRF + JWT RS256 (reutiliza `core/auth`), Kafka producer (`core/repositories/red_operativa/kafka_writer.py`, ya existente), Apache Pinot (lectura), Angular standalone + RxJS

**Storage**: Apache Pinot (lectura) + Kafka (escritura de `Dim_RegionOperativa`, `Dim_ValidacionRegion`)

**Testing**: pytest/APITestCase (backend contract + service + unit de permisos), Jasmine (Angular services/guards)

**Target Platform**: Linux containerizado (backend) + SPA web (frontend)

**Project Type**: Aplicación web (backend + frontend)

**Performance Goals**: Validación de continuidad de casos activos (RF-REGON-003) en tiempo real, sin demora perceptible (RNF-REGON-002) — umbral operativo: ≤100ms p95, consistente con `testing.md` (consulta Pinot simple).

**Constraints**: `/api/v1/`, envelope estándar `{data, meta}` / `{error, detail, code}`, `Idempotency-Key` en escrituras (validación, despublicación), sin INSERT/UPDATE directo a Pinot, trazabilidad completa de intentos de validación (RNF-REGON-001, append-only en `Dim_ValidacionRegion`)

**Scale/Scope**: Catálogo de regiones operativas administradas por Administrador/Director Tecnológico; app backend existente `red_operativa` (compartida con `alta-unidades`); módulo Angular existente `red-operativa`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Functional Suitability**: PASS — cubre CU-O55/O60/O61/O62 y criterios CA-REGON-001..008, trazables a OP-TSI-RED-01.
- **Reliability**: PASS — cada intento de validación es una fila nueva e inmutable en `Dim_ValidacionRegion` (RNF-REGON-001); ninguna transición pierde historial de intentos aunque `estadoregion` sea un campo directo sin historial propio.
- **Performance Efficiency**: PASS — umbral explícito en RNF-REGON-002 para la validación de continuidad de casos activos.
- **Interaction Capability**: PASS — el 409 Conflict en `CU-O60`/`CU-O61`/`CU-O62` ante una transición de `estadoregion` no permitida da un error accionable; el flujo de reingreso a `CU-O55` desde `En_Alerta`/`Despublicada` reutiliza la misma pantalla sin un estado "especial" adicional que confunda al operador. (RN-REGON-003 se garantiza por construcción en `CU-O55`, sin un 409 asociado — ver spec.md §8 y hallazgo F1 de `/speckit-analyze` 2026-07-21.)
- **Security**: PASS — JWT + RBAC por rol (Administrador vs Director Tecnológico); `idusuario` queda registrado en cada aprobación final (excepto `CU-O62`, sin actor humano por diseño, documentado en RF-REGON-004).
- **Compatibility**: PASS — contrato OpenAPI versionado, aditivo sobre la app `red_operativa` ya expuesta por `alta-unidades`; no rompe contratos existentes.
- **Maintainability**: PASS — capas Vista→Servicio→Repositorio; repositorios nuevos por tabla (`RegionOperativaRepository`, `ValidacionRegionRepository`) dentro de `core/repositories/red_operativa/`, junto a los ya existentes de `alta-unidades`.
- **Flexibility**: PASS — el protocolo de validación es agnóstico de la región (mismo flujo para cualquier zona geográfica nueva), habilitando el objetivo de escalar a nuevas ciudades sin cambio de código (Principio VIII).
- **Safety**: PASS — la despublicación (`CU-O61`/`CU-O62`) nunca cancela casos activos, solo bloquea casos nuevos (RN-REGON-004); la validación de continuidad corre en tiempo real contra `Fact_Accidente` antes de bloquear una región.

**Tie-Breaker**: no se identifica conflicto directo entre características para las funcionalidades implementables (`CU-O55`, `CU-O60`, `CU-O61`, `CU-O62` con regla de cobertura). Cobertura O62 = puente geo → condados → unidades activas; Safety garantiza no despublicar si `count > 0`.

Post-Design Gate: PASS (excepción única y documentada: disparador de `CU-O62`, ver Complexity Tracking).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Red-Operativa/incorporacion-regional/backend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── incorporacion-regional.openapi.yaml
└── tasks.md                    # generado por /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── apps/red_operativa/                         # app existente (compartida con alta-unidades)
│   ├── views/
│   │   └── region_views.py                     # Vista DRF: validar, listar historial, reevaluar/despublicar
│   ├── permissions.py                           # extiende: IsAdministradorRedOperativa, IsDirectorTecnologico
│   ├── services/
│   │   ├── validacion_region_service.py         # CU-O55 (alta si no existe + insert validación + transición)
│   │   ├── remediacion_region_service.py        # CU-O60 (historial + rechazo definitivo)
│   │   ├── reevaluacion_region_service.py       # CU-O61 (degradar/despublicar + validación continuidad)
│   │   └── despublicacion_automatica_service.py # CU-O62 (lógica de negocio, sin disparador conectado)
│   └── tests/
│       ├── api/                                 # Contract tests por endpoint
│       └── services/
└── core/
    ├── repositories/red_operativa/
    │   ├── region_operativa_repository.py       # CRUD Dim_RegionOperativa (existente app, tabla nueva)
    │   ├── validacion_region_repository.py       # INSERT + historial ordenado por fechahora
    │   └── accidente_activo_read_repository.py   # SELECT solo lectura contra Fact_Accidente (módulo Emergencias)
    └── auth/                                     # JWT/roles, reutilizado sin cambios

frontend/src/app/
├── modules/red-operativa/incorporacion-regional/   # nueva subcarpeta del módulo existente red-operativa
│   ├── models/
│   │   └── region-operativa.contract.ts            # Tipos TS alineados al contrato OpenAPI
│   ├── services/
│   │   ├── region-operativa-api.service.ts          # HTTP tipado 1:1 con el contrato
│   │   └── region-operativa-facade.service.ts
│   ├── guards/
│   │   ├── administrador-red-operativa.guard.ts      # reutilizar el de alta-unidades si aplica
│   │   └── director-tecnologico.guard.ts             # nuevo, exclusivo de CU-O61
│   └── pages/
│       ├── validacion/                               # CU-O55/O60: ejecutar protocolo + historial + remediación
│       └── reevaluacion/                              # CU-O61: degradar/despublicar región en producción
└── core/guards/
    └── administrador.guard.ts                          # reutilizar si existe (mismo patrón que alta-unidades)
```

**Structure Decision**: Se reutiliza la app Django `red_operativa` y el módulo Angular `red-operativa` ya creados por `alta-unidades` (mismo módulo de negocio Red-Operativa, ver `module-map.md`). Escrituras publican a `Dim_RegionOperativa_topic` y `Dim_ValidacionRegion_topic`. No se crea app ni módulo nuevo — esta feature añade vistas/servicios/repositorios dentro de la estructura existente.

## Implementation Order (contract-first)

1. **Contrato OpenAPI** (`contracts/incorporacion-regional.openapi.yaml`) — fuente de verdad.
2. **Backend**: repositorios (`core/repositories/red_operativa/region_operativa_repository.py`, `validacion_region_repository.py`, `accidente_activo_read_repository.py`) → servicios → vistas DRF + permisos + tests de contrato.
3. **Frontend**: modelos TS → `RegionOperativaApiService` → guards → páginas (sin lógica de negocio en componentes).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `CU-O62` cron/job externo (no embebido en este repo) | El endpoint valida cobertura=0; el orquestador (cron) es ops | Embebido frágil con match textual (rechazado: Safety) |
