# Implementation Plan: Registro de Accidentes en Tiempo Real

**Branch**: `registro-accidente` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Emergencias/registro-accidente/spec.md`

**Input**: Feature specification from `specs/003-operational/Emergencias/registro-accidente/spec.md` (clarificaciones Session 2026-07-09 integradas).

## Summary

Implementar el módulo de registro de accidentes con enfoque **contract-first**: primero el contrato OpenAPI REST (`/api/v1/accidentes/*`) alineado a `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka**; finalmente frontend Angular 17+ con servicios tipados y guards por rol (`Operador de emergencias`, `Unidad de emergencia`). Cubre CU-O21, CU-O32, CU-O40, CU-O41 y RF-REG-010 con promoción condicional BORRADOR→REPORTADO.

## Traceability

- **Objetivo operacional:** entrada al ciclo de emergencias (cadena registro → despacho → cierre).
- **UC cubiertos:** CU-O21, CU-O32, CU-O40, CU-O41.
- **Dependencias:** `autenticacion-y-rbac`, `incorporacion-regional`.
- **Consumidores downstream:** `despacho-inteligente` (requiere estado REPORTADO).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend)

**Primary Dependencies**: Django 5 + DRF, JWT RS256 (auth existente), RxJS, adaptador Nominatim (geocodificación); frontend: Tailwind CSS v4, @tabler/icons, Leaflet + OpenStreetMap (decisión y justificación en `.specify/docs/infra/infrastructure.md`)

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal de escritura de dominio)

**Testing**: pytest + contract tests OpenAPI (backend); Jasmine/Karma servicios y guards (frontend)

**Target Platform**: Linux containerizado (API) + SPA web operadores/unidades

**Project Type**: Web application (backend + frontend)

**Performance Goals**: Validaciones RF-REG-003 < 2s (RNF-REG-005); disponibilidad registro 99.9% (RNF-REG-003); formulario < 5 min meta operativa (RNF-REG-001); resiliencia de captura ante interrupción de red sin pérdida de datos (RNF-REG-006)

**Constraints**: API `/api/v1/`, envelope estándar, idempotencia en escrituras, sin INSERT directo a Pinot, comunicación inter-módulo vía Kafka

**Scale/Scope**: Camino crítico TSI; multi-región vía cobertura `Dim_RegionOperativa` en Producción

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | CU-O21/O32/O40/O41 + CA-REG-001–014 trazables |
| Reliability | PASS | Idempotencia, eventos Kafka, fail-safe en validaciones |
| Performance Efficiency | PASS | Validación síncrona <2s declarada; métricas en quickstart |
| Interaction Capability | PASS | UX advertencias/duplicados/confirmación reporte en contrato; frontend debe cumplir `.specify/docs/design/design-system.md` (Ley de Hick: máx. 3-4 acciones primarias visibles en el formulario de registro; Ley de Fitts: botón de confirmar/reportar ≥44x44px) |
| Security | PASS | JWT + RBAC + audit log RNF-REG-004 |
| Compatibility | PASS | Contract-first OpenAPI versionado |
| Maintainability | PASS | Vista→Servicio→Repositorio, servicios por caso de uso |
| Flexibility | PASS | Cobertura por región Producción, geocoder intercambiable |
| Safety | PASS | Bloqueo solo GPS global inválido; BORRADOR ante incertidumbre |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** documentado en `research.md` (Maintainability vs Performance en descomposición de servicios).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Emergencias/registro-accidente/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── registro-accidente.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── accidentes/
│       ├── views/
│       │   ├── accidente_views.py      # Vista DRF (thin)
│       │   ├── accion_views.py         # confirmar, descartar, escalar, fusionar
│       │   └── urls.py
│       ├── services/
│       │   ├── registro_accidente_service.py
│       │   ├── validacion_accidente_service.py
│       │   ├── confirmar_reporte_service.py
│       │   ├── descartar_caso_service.py
│       │   ├── escalar_severidad_service.py
│       │   ├── fusionar_reportes_service.py
│       │   ├── consulta_accidente_service.py
│       │   ├── geocodificacion_inversa_service.py
│       │   └── cobertura_operativa_service.py
│       ├── permissions.py              # OperadorEmergencias, UnidadEmergencia
│       └── tests/
│           ├── api/                    # Contract tests OpenAPI
│           ├── services/
│           └── repositories/
└── core/
    └── repositories/
        └── accidentes/
            ├── accidente_repository.py
            ├── estado_accidente_repository.py
            ├── nota_accidente_repository.py
            ├── elemento_climatico_repository.py
            ├── elemento_fisico_repository.py
            ├── despacho_read_repository.py   # lectura precondición O40
            └── region_operativa_repository.py

frontend/
└── src/app/
    ├── modules/accidentes/
    │   ├── pages/
    │   │   ├── registro-accidente/
    │   │   ├── lista-accidentes/
    │   │   └── detalle-accidente/
    │   ├── services/
    │   │   ├── accidente-api.service.ts
    │   │   ├── geocodificacion-api.service.ts
    │   │   └── models/accidente.types.ts
    │   ├── guards/
    │   │   ├── operador-emergencias.guard.ts
    │   │   └── unidad-emergencia.guard.ts
    │   └── accidentes.routes.ts
    └── core/
        └── interceptors/                 # JWT (reutilizar de auth)
```

**Structure Decision:** App Django `accidentes/` y módulo Angular `accidentes/` 1:1 según `project-structure.md`. Repositorios en `core/repositories/accidentes/` compartidos.

## Phase 0: Research (completado)

Ver `research.md` — resueltos: contract-first, capas Django, Kafka-only-write, JWT/RBAC, Nominatim, validaciones estructuradas, cobertura regional, Angular guards.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/registro-accidente.openapi.yaml`

Endpoints definidos antes de implementación backend/frontend. Roles:

| Rol | Endpoints |
|-----|-----------|
| Operador de emergencias | CRUD accidentes, confirmar-reporte, descartar, fusionar, geocodificación |
| Unidad de emergencia | escalar-severidad, detalle (lectura) |

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|-------------|----------|------------------------|
| `RegistrarAccidenteView` | `RegistroAccidenteService` + `ValidacionAccidenteService` | `AccidenteRepository`, `EstadoAccidenteRepository`, Kafka producer |
| `ListarAccidentesView` | `ConsultaAccidenteService` | `AccidenteRepository` (Pinot read) |
| `DetalleAccidenteView` | `ConsultaAccidenteService` | `AccidenteRepository`, `EstadoAccidenteRepository` |
| `ActualizarAccidenteView` | `ConsultaAccidenteService` | `AccidenteRepository`, audit |
| `GeocodificacionInversaView` | `GeocodificacionInversaService` + `CoberturaOperativaService` | Nominatim HTTP + `RegionOperativaRepository` |
| `ConfirmarReporteView` | `ConfirmarReporteService` | `EstadoAccidenteRepository` |
| `DescartarCasoView` | `DescartarCasoService` | `AccidenteRepository`, `EstadoAccidenteRepository` |
| `EscalarSeveridadView` | `EscalarSeveridadService` | `AccidenteRepository`, `NotaAccidenteRepository`, `DespachoReadRepository` |
| `FusionarReportesView` | `FusionarReportesService` | `AccidenteRepository`, `EstadoAccidenteRepository` |

**Flujo escritura Kafka (ejemplo registro):**

```text
POST /accidentes
  → ValidacionAccidenteService.validate()
  → RegistroAccidenteService.create()
      → AccidenteRepository.publish_create()      → Fact_Accidente_topic
      → EstadoAccidenteRepository.publish()         → Fact_AccidenteTipoEstadoAccidente_topic (BORRADOR [+ REPORTADO])
  → Response 201 con estado condicional
```

### Frontend — servicios y guards (prioridad 2, post-contrato)

| Artefacto | Contrato consumido |
|-----------|-------------------|
| `AccidenteApiService` | Todos los paths `/accidentes/*` |
| `GeocodificacionApiService` | `GET geocodificacion-inversa` |
| `OperadorEmergenciasGuard` | Rutas registro, lista, detalle, fusión, descarte |
| `UnidadEmergenciaGuard` | Escalamiento O40 |
| `accidente.types.ts` | Espejo de schemas OpenAPI (typescript-expert: tipos estrictos, sin `any`) |

### Data model

Ver `data-model.md` para entidades, transiciones, topics Kafka y reglas RN/RF.

### Validación E2E

Ver `quickstart.md` para escenarios A–G y criterios de salida.

## Phase 2: Task Decomposition (siguiente comando)

No generado por este plan. Ejecutar `/speckit-tasks` para producir `tasks.md` ordenado:

1. Contract tests esqueleto desde OpenAPI
2. Repositorios + Kafka producer
3. Servicios dominio (validación → registro → acciones)
4. Vistas DRF + permissions
5. Angular services/types
6. Angular guards + rutas
7. Páginas UI registro/lista/detalle
8. Tests integración quickstart

## Complexity Tracking

Sin violaciones de constitution que requieran excepción.

## ISO 25010 — Impacto Safety (camino crítico)

Este módulo es la **puerta de entrada** al camino crítico. Decisiones de diseño con impacto Safety:

- Promoción a REPORTADO solo sin advertencias → reduce despacho sobre datos dudosos.
- GPS global inválido bloquea registro (fail-closed).
- Duplicados no bloquean pero sugieren fusión con padre más antiguo.
- Escalamiento O40 requiere despacho confirmado (no especulación remota sin asignación).

## Artifacts Generated

| Artefacto | Ruta |
|-----------|------|
| Plan | `specs/003-operational/Emergencias/registro-accidente/plan.md` |
| Research | `specs/003-operational/Emergencias/registro-accidente/research.md` |
| Data model | `specs/003-operational/Emergencias/registro-accidente/data-model.md` |
| Quickstart | `specs/003-operational/Emergencias/registro-accidente/quickstart.md` |
| OpenAPI contract | `specs/003-operational/Emergencias/registro-accidente/contracts/registro-accidente.openapi.yaml` |
