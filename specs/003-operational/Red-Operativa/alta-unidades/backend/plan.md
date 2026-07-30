# Implementation Plan: Alta y Configuración de Unidades de Emergencia

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../alta-unidades.md`](../alta-unidades.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — stub Fase A; no duplicar OpenAPI/data-model en FE.


**Branch**: `003-operational-red-operativa-alta-unidades` | **Date**: 2026-07-21 | **Spec**: `specs/003-operational/Red-Operativa/alta-unidades/backend/spec.md`

**Input**: Feature specification from `specs/003-operational/Red-Operativa/alta-unidades/backend/spec.md`

## Summary

**Autoridad UI:** Interaction Capability en [`../frontend/plan.md`](../frontend/plan.md) / [`../frontend/tasks.md`](../frontend/tasks.md). Este plan BE no es superficie de trabajo UI.


**Actualización 2026-07-24 / mapa 2026-07-29:** actor **Proveedor** (no Admin) en CU-O54/56/57/58; `idcliente` auto del token; O56 crea credenciales con todo-o-nada total; **CU-O59 eliminado** → **CU-O30**. Canónico: `flujoscorreguidos/flujo-red-operativa-canonico.md`.

Plan original (2026-07-21): ciclo de vida administrativo contract-first; Vista→Servicio→Repositorio; Kafka; Angular. Migración `zonacobertura`→`idcondado` acordada.

## Traceability

- **Objetivo Operacional (OP)**: OP-TSI-RED-01.
- **UC cubiertos**: CU-O54, CU-O56, CU-O57, CU-O58. **CU-O59: eliminado.**
- **Mapeo de cumplimiento** (delta 2026-07-24):
  - JWT + RBAC: rol **Proveedor** + ownership por `idcliente`; sin override Administrador.
  - O56: columnas + `gmail`; creación usuarios/credenciales; transacción atómica con unidades.
  - Retirar OpenAPI/FE/tests de disponibilidad externa (O59).
  - Dependencia fuerte de `incorporacion-clientes` (Proveedor `Activo` vía O14/O16).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend Angular 17+)

**Primary Dependencies**: Django 5 + DRF + JWT RS256 (reutiliza `core/auth`), Kafka producer (`core/repositories/*/kafka_writer.py`), Apache Pinot (lectura), Angular standalone + RxJS

**Storage**: Apache Pinot (lectura) + Kafka (escritura de `Dim_UnidadEmergencia`, `Fact_BajaUnidad`; credenciales O56; **no** escribe `Fact_HistorialEstadoUnidad` — eso es CU-O30)

**Testing**: pytest/APITestCase (backend contract + service + unit de permisos), Jasmine (Angular services/guards)

**Target Platform**: Linux containerizado (backend) + SPA web (frontend)

**Project Type**: Aplicación web (backend + frontend)

**Performance Goals**: Validación de duplicado de placa < 1s (RNF-CAM-001); importación en lote de 500 unidades < 30s con reporte fila por fila (RNF-CAM-002)

**Constraints**: `/api/v1/`, envelope estándar `{data, meta}` / `{error, detail, code}`, `Idempotency-Key` en escrituras (alta, baja, reactivación, lote), sin INSERT/UPDATE directo a Pinot, trazabilidad completa (RNF-CAM-003)

**Scale/Scope**: Catálogo administrativo de unidades externas; actor **Proveedor** (Session 2026-07-24; CU-O59 retirado → O30); app backend `red_operativa` (compartida con `incorporacion-regional`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Functional Suitability**: PASS — cubre CU-O54/56/57/58 y CA-CAM-001..010 (O59 retirado documentado en CA-CAM-009), trazables a OP-TSI-RED-01.
- **Reliability**: PASS — importación en lote todo-o-nada incl. credenciales (RF-CAM-002 / RN-CAM-007); reactivación valida unicidad de placa.
- **Performance Efficiency**: PASS — umbrales RNF-CAM-001/002.
- **Interaction Capability**: PASS — reporte fila-por-fila al Proveedor en importación bajo presión operativa.
- **Security**: PASS — JWT + `IsProveedorFlota` / ownership `idcliente`; sin override Admin; geolocalización solo autenticada.
- **Compatibility**: PASS — OpenAPI versionado; migración `zonacobertura`→`idcondado` coordinada con `despacho-inteligente` y `evidencia-unidad` (T018–T023e).
- **Maintainability**: PASS — Vista→Servicio→Repositorio; repos de escritura en `core/repositories/red_operativa/`.
- **Flexibility**: PASS — importación en lote vía CSV genérico, reutilizable para nuevas regiones sin cambio de código.
- **Safety**: PASS — bloqueo/confirmación con despacho activo (RF-CAM-003/004). (La alerta “Activa con despacho” de disponibilidad corresponde a CU-O30, no a este plan.)

**Tie-Breaker**: migración `zonacobertura`→`idcondado` prioriza Maintainability sin degradar Safety del despacho.

Post-Design Gate: PASS (sin violaciones abiertas para este spec).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Red-Operativa/alta-unidades/backend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── alta-unidades.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── apps/red_operativa/
│   ├── views/
│   │   └── unidad_views.py                  # alta, lote, detalle, edición, baja, reactivar
│   ├── permissions.py                        # IsProveedorFlota (+ permisos región en mismo app)
│   ├── services/
│   │   ├── registro_unidad_service.py         # CU-O54
│   │   ├── importacion_lote_unidad_service.py # CU-O56 (+ credenciales)
│   │   ├── edicion_unidad_service.py          # CU-O57
│   │   └── baja_unidad_service.py             # CU-O58 (baja + reactivación)
│   └── tests/
│       ├── api/
│       ├── services/
│       └── unit/
└── core/
    ├── repositories/red_operativa/
    │   ├── unidad_emergencia_repository.py
    │   ├── baja_unidad_repository.py
    │   ├── despacho_activo_read_repository.py
    │   └── kafka_writer.py
    └── auth/

# Migración cruzada (research Decision 8)
backend/apps/despacho/services/disponibilidad_unidad_service.py
backend/core/repositories/despacho/unidad_emergencia_repository.py

frontend/src/app/
├── modules/red-operativa/alta-unidades/
│   ├── models/unidad-emergencia.contract.ts
│   ├── services/
│   │   ├── unidad-emergencia-api.service.ts
│   │   └── unidad-emergencia-facade.service.ts
│   ├── guards/
│   │   └── proveedor-flota.guard.ts
│   └── pages/
│       ├── catalogo/
│       ├── edicion/
│       └── baja/
```

**Structure Decision**: App Django `red_operativa` compartida con `incorporacion-regional`. Módulo Angular `red-operativa/alta-unidades/`. Escrituras: `Dim_UnidadEmergencia_topic`, `Fact_BajaUnidad_topic` (+ cuenta en O56). Disponibilidad: **CU-O30**, no este módulo. Migración `idcondado` en el mismo ciclo.

## Implementation Order (contract-first)

1. **Contrato OpenAPI** — fuente de verdad (sin endpoint O59).
2. **Backend**: repos → servicios → vistas + `IsProveedorFlota` + tests.
3. **Migración cruzada**: consumidores `idcondado` en despacho/evidencia.
4. **Frontend**: modelos → API → `ProveedorFlotaGuard` → páginas.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Migración cruzada de `despacho-inteligente` / `evidencia-unidad` | `idcondado` sustituye el fallback textual que ya consumía despacho | Aislar solo `alta-unidades` dejaría candidatas sin match en producción |
