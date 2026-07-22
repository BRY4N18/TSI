# Implementation Plan: Alta y Configuración de Unidades de Emergencia

**Branch**: `003-operational-red-operativa-alta-unidades` | **Date**: 2026-07-21 | **Spec**: `specs/003-operational/Red-Operativa/alta-unidades/spec.md`

**Input**: Feature specification from `specs/003-operational/Red-Operativa/alta-unidades/spec.md`

## Summary

Implementar el ciclo de vida administrativo del catálogo de unidades de emergencia (CU-O54, O56, O57, O58, O59) con enfoque **contract-first**: primero contrato OpenAPI REST bajo `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía Kafka; finalmente frontend Angular 17+ con servicios tipados y guards de rol (Administrador / Operador de emergencias). Incluye la migración de `despacho-inteligente` de `zonacobertura` (texto libre) a `idcondado` (FK real), acordada en clarificación.

## Traceability

- **Objetivo Operacional (OP)**: OP-TSI-RED-01 (catálogo confiable de unidades externas para el algoritmo de despacho — TSI no posee flotas, su valor es el de orquestador digital).
- **UC cubiertos**: CU-O54, CU-O56, CU-O57, CU-O58, CU-O59.
- **Mapeo de cumplimiento**:
  - Contract-first REST versionado (`/api/v1/red-operativa/unidades/...`).
  - Patrón Vista→Servicio→Repositorio; Kafka como único canal de escritura (`Dim_UnidadEmergencia_topic`, `Fact_BajaUnidad_topic`, `Fact_HistorialEstadoUnidad_topic`).
  - JWT + RBAC: Administrador (CU-O54/56/57/58), Operador de emergencias (CU-O59) — dependencia `autenticacion-y-rbac`.
  - Migración cruzada documentada: `despacho-inteligente` debe adoptar `idcondado` (ver Sección 12 del spec y Decision 8 de `research.md`).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend Angular 17+)

**Primary Dependencies**: Django 5 + DRF + JWT RS256 (reutiliza `core/auth`), Kafka producer (`core/repositories/*/kafka_writer.py`), Apache Pinot (lectura), Angular standalone + RxJS

**Storage**: Apache Pinot (lectura) + Kafka (escritura de `Dim_UnidadEmergencia`, `Fact_BajaUnidad`, `Fact_HistorialEstadoUnidad`)

**Testing**: pytest/APITestCase (backend contract + service + unit de permisos), Jasmine (Angular services/guards)

**Target Platform**: Linux containerizado (backend) + SPA web (frontend)

**Project Type**: Aplicación web (backend + frontend)

**Performance Goals**: Validación de duplicado de placa < 1s (RNF-CAM-001); importación en lote de 500 unidades < 30s con reporte fila por fila (RNF-CAM-002)

**Constraints**: `/api/v1/`, envelope estándar `{data, meta}` / `{error, detail, code}`, `Idempotency-Key` en escrituras (alta, baja, reactivación), sin INSERT/UPDATE directo a Pinot, trazabilidad completa (RNF-CAM-003)

**Scale/Scope**: Catálogo administrativo de unidades externas/propias; actores Administrador y Operador de emergencias; app backend nueva `red_operativa` (compartida con `incorporacion-regional`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Functional Suitability**: PASS — cubre CU-O54/56/57/58/59 y criterios CA-CAM-001..009, trazables a OP-TSI-RED-01.
- **Reliability**: PASS — importación en lote es todo-o-nada (RF-CAM-002); reactivación valida unicidad de placa antes de escribir (evita estado inconsistente).
- **Performance Efficiency**: PASS — umbrales explícitos en RNF-CAM-001/002.
- **Interaction Capability**: PASS — reporte fila-por-fila en importación en lote da error accionable al Administrador bajo presión operativa.
- **Security**: PASS — JWT + RBAC por rol (Administrador vs Operador); ningún dato de geolocalización de unidad se expone sin autenticación (dependencia `autenticacion-y-rbac`).
- **Compatibility**: PASS — contrato OpenAPI versionado; el cambio `zonacobertura`→`idcondado` no rompe ninguna integración externa (insurers/Smart City), pero sí rompe dos contratos internos ya implementados: `despacho-inteligente` (`unidad_emergencia_repository.py`, `disponibilidad_unidad_service.py`) **y** `evidencia-unidad` (contrato OpenAPI, tipo TS y template Angular `panel-disponibilidad.page.html`, que hoy renderiza `zonacobertura` literalmente). Ambas migraciones quedan explícitas en `tasks.md` Fase 2 (T018-T023e) antes de avanzar a las historias de usuario.
- **Maintainability**: PASS — capas Vista→Servicio→Repositorio; un repositorio por tabla (`UnidadEmergenciaRepository`, `BajaUnidadRepository`, `HistorialEstadoUnidadRepository`).
- **Flexibility**: PASS — importación en lote vía CSV/Excel genérico, reutilizable para nuevas regiones sin cambio de código.
- **Safety**: PASS — bloqueo/confirmación explícita al editar o dar de baja unidad con despacho activo (RF-CAM-003, RF-CAM-004); alerta al marcar "Activa" con despacho sin retirar (RF-CAM-005) — protege contra que el algoritmo de despacho pierda de vista una unidad realmente ocupada.

**Tie-Breaker**: no se identifica conflicto directo entre características para este spec. La migración `zonacobertura`→`idcondado` prioriza Maintainability (eliminar un cast de texto frágil) sin afectar Safety del despacho activo — cambio aditivo, no requiere invocar el mecanismo de desempate.

Post-Design Gate: PASS (sin violaciones ni excepciones abiertas). Única excepción documentada: T108 de `registro-accidente` (snackbar de deshacer pendiente) no aplica a este spec.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Red-Operativa/alta-unidades/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── alta-unidades.openapi.yaml
└── tasks.md                    # generado por /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── apps/red_operativa/
│   ├── views/
│   │   └── unidad_views.py                  # Vista DRF: alta, lote, edición, baja, disponibilidad
│   ├── permissions.py                        # IsAdministradorRedOperativa, IsOperadorOUnidadPropia
│   ├── services/
│   │   ├── registro_unidad_service.py         # CU-O54
│   │   ├── importacion_lote_unidad_service.py # CU-O56
│   │   ├── edicion_unidad_service.py          # CU-O57 (bloqueo por despacho activo)
│   │   ├── baja_unidad_service.py             # CU-O58 (baja + reactivación)
│   │   └── disponibilidad_externa_service.py  # CU-O59
│   └── tests/
│       ├── api/                               # Contract tests por endpoint
│       └── services/
└── core/
    ├── repositories/red_operativa/
    │   ├── unidad_emergencia_repository.py    # CRUD + duplicado de placa (escritura, distinto del ya existente de solo lectura en despacho/)
    │   ├── baja_unidad_repository.py
    │   ├── historial_estado_unidad_repository.py
    │   ├── despacho_activo_read_repository.py  # SELECT de solo lectura contra Fact_Despacho (módulo Emergencias)
    │   └── kafka_writer.py                     # reexporta core/repositories/cuentas_clientes/kafka_writer.py
    └── auth/                                   # JWT/roles, reutilizado sin cambios

# Migración cruzada (dependencia obligatoria, ver spec §12 y research.md Decision 8)
backend/apps/despacho/services/disponibilidad_unidad_service.py   # deja de exponer zonacobertura, expone idcondado
backend/core/repositories/despacho/unidad_emergencia_repository.py # list_candidatas_por_condado usa idcondado directo, sin fallback de texto

frontend/src/app/
├── modules/red-operativa/alta-unidades/
│   ├── models/
│   │   └── unidad-emergencia.contract.ts      # Tipos TS alineados al contrato OpenAPI
│   ├── services/
│   │   ├── unidad-emergencia-api.service.ts   # HTTP tipado 1:1 con el contrato
│   │   └── unidad-emergencia-facade.service.ts
│   ├── guards/
│   │   ├── administrador-red-operativa.guard.ts
│   │   └── operador-disponibilidad.guard.ts
│   └── pages/
│       ├── catalogo/                          # listado + alta individual/lote
│       ├── edicion/
│       ├── baja/
│       └── disponibilidad-externa/            # CU-O59, rol Operador
└── core/guards/
    └── administrador.guard.ts                 # reutilizar si existe (mismo patrón que gestion-cuentas)
```

**Structure Decision**: Nueva app Django `red_operativa` (compartida con `incorporacion-regional`, siguiendo el mismo patrón que `cuentas_clientes` sirve a sus 3 specs). Nuevo módulo Angular `red-operativa` con subcarpeta `alta-unidades/`. Escrituras publican a `Dim_UnidadEmergencia_topic`, `Fact_BajaUnidad_topic` y `Fact_HistorialEstadoUnidad_topic`. La migración de `despacho-inteligente` (`zonacobertura`→`idcondado`) se ejecuta como tarea cruzada dentro de este mismo ciclo de implementación, no como spec separado.

## Implementation Order (contract-first)

1. **Contrato OpenAPI** (`contracts/alta-unidades.openapi.yaml`) — fuente de verdad.
2. **Backend**: repositorios (`core/repositories/red_operativa/`) → servicios → vistas DRF + permisos + tests de contrato.
3. **Migración cruzada**: actualizar `despacho-inteligente` (`unidad_emergencia_repository.py`, `disponibilidad_unidad_service.py`, su `spec.md` y `data-model.md`) para consumir `idcondado`.
4. **Frontend**: modelos TS → `UnidadEmergenciaApiService` → guards → páginas (sin lógica de negocio en componentes).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Migración cruzada de un módulo ya implementado (`despacho-inteligente`) como parte de este plan | `zonacobertura` es un fallback geográfico real y documentado que `alta-unidades` reemplaza por diseño (`idcondado`); dejarlo desincronizado rompería el filtro de candidatas por condado en producción | Aislar el cambio solo en `alta-unidades` sin tocar `despacho-inteligente` (rechazado: `unidad_emergencia_repository.py::list_candidatas_por_condado` dejaría de encontrar candidatas para toda unidad sin `idcondado`, que sería el 100% de las existentes) |
