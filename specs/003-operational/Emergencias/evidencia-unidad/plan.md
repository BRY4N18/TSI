# Implementation Plan: Evidencia en Sitio y Gestión de Disponibilidad de Unidad

**Branch**: `evidencia-unidad` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Emergencias/evidencia-unidad/spec.md`

**Input**: Feature specification from `specs/003-operational/Emergencias/evidencia-unidad/spec.md` (clarificaciones Session 2026-07-09 integradas).

## Summary

Implementar evidencia fotográfica/notas de campo, gestión de disponibilidad de unidades y sincronización offline con enfoque **contract-first**: primero el contrato OpenAPI REST (`contracts/evidencia-unidad.openapi.yaml`) alineado a `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura de dominio exclusiva vía **Kafka** y binarios en **Azure Blob**; finalmente frontend Angular 17+ con servicios tipados, store offline y guards por rol. Cubre CU-O27, CU-O30 y CU-O43.

## Traceability

- **Objetivo operacional:** enriquecer expediente de accidente y mantener flota despachable en tiempo real.
- **UC cubiertos:** CU-O27, CU-O30, CU-O43.
- **Dependencias:** `autenticacion-y-rbac`, `registro-accidente`, `despacho-inteligente`, `seguimiento-cierre-de-casos`.
- **Consumidores downstream:** `despacho-inteligente` (estado unidad), aseguradoras/auditoría (evidencia).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x / Angular 17+ (frontend/móvil)

**Primary Dependencies**: Django 5 + DRF, SimpleJWT (RS256), Azure SDK Blob, RxJS, IndexedDB (offline store)

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal escritura dominio), Azure Blob (binarios foto)

**Testing**: pytest + contract tests OpenAPI; Jasmine/Karma servicios, guards y offline store

**Target Platform**: Linux containerizado (API) + SPA/móvil campo (Técnico, Unidad)

**Project Type**: Web application (backend + frontend)

**Performance Goals**: Cambio estado reflejado ≤5s despacho (RNF-EVI-003); sync batch ≤30s (RNF-EVI-004); consulta estado ≤2s (RNF-EVI-006)

**Constraints**: API `/api/v1/`, envelope estándar, idempotencia escrituras, Vista→Servicio→Repositorio, Kafka-only-write, evidencia offline solo en dispositivo capturador

**Scale/Scope**: Módulo Emergencias; multi-unidad por caso; fotos ≤10 MB con compresión

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|--------------------------|--------|---------------|
| Functional Suitability | PASS | CU-O27/O30/O43 + CA-EVI-001–009 trazables |
| Reliability | PASS | Sync parcial con reintento; idempotencia; fail-safe estado default |
| Performance Efficiency | PASS | RNF-EVI-003/004/006 declarados; query última fila historial |
| Interaction Capability | PASS | Galería offline+online; indicador sync pendiente |
| Security | PASS | JWT + RBAC RN-EVI-012/015; evidencia sensible con control rol |
| Compatibility | PASS | Contract-first OpenAPI versionado |
| Maintainability | PASS | Vista→Servicio→Repositorio; servicios por CU |
| Flexibility | PASS | Offline-first; Blob desacoplado de Pinot |
| Safety | PASS | Default Fuera de servicio; Ocupada excluye despacho |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker:** documentado en `research.md` (Maintainability vs Performance en descomposición de servicios).

**Conflictos identificados:** ninguno adicional fuera del tie-breaker documentado.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Emergencias/evidencia-unidad/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evidencia-unidad.openapi.yaml
└── tasks.md                    # (/speckit-tasks — siguiente paso)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   ├── accidentes/
│   │   ├── views/
│   │   │   ├── evidencia_views.py          # Vista DRF (thin)
│   │   │   └── urls.py                     # + rutas /evidencias/*
│   │   ├── services/
│   │   │   ├── evidencia_foto_service.py
│   │   │   ├── nota_campo_service.py
│   │   │   ├── sincronizar_evidencia_service.py
│   │   │   └── consulta_evidencia_service.py
│   │   ├── permissions.py                  # + TecnicoCampo, EvidenciaGallery
│   │   └── tests/api/test_evidencia_contract.py
│   └── despacho/
│       ├── views/
│       │   ├── disponibilidad_views.py
│       │   └── urls.py                     # + rutas /unidades-emergencia/*
│       ├── services/
│       │   ├── disponibilidad_unidad_service.py
│       │   └── consulta_flota_service.py
│       ├── permissions.py                  # + UnidadPropia, FlotaDespacho, AdministradorFlota
│       └── tests/api/test_disponibilidad_contract.py
└── core/
    ├── repositories/
    │   ├── evidencia/
    │   │   ├── evidencia_foto_repository.py
    │   │   ├── nota_accidente_repository.py   # compartido tipos campo/escalamiento
    │   │   └── accidente_read_repository.py   # precondición caso activo
    │   └── despacho/
    │       ├── historial_estado_unidad_repository.py
    │       └── unidad_emergencia_repository.py
    └── storage/
        └── blob_storage_service.py            # Azure Blob evidencia-accidentes

frontend/
└── src/app/
    ├── modules/evidencia-unidad/
    │   ├── pages/
    │   │   ├── galeria-evidencias/
    │   │   ├── captura-evidencia/
    │   │   └── panel-disponibilidad/
    │   ├── services/
    │   │   ├── evidencia-api.service.ts
    │   │   ├── disponibilidad-unidad-api.service.ts
    │   │   ├── evidencia-offline-store.service.ts
    │   │   └── models/evidencia-unidad.types.ts
    │   ├── guards/
    │   │   ├── evidencia-gallery.guard.ts
    │   │   ├── unidad-emergencia-disponibilidad.guard.ts
    │   │   └── administrador-flota.guard.ts
    │   └── evidencia-unidad.routes.ts
    └── core/interceptors/                     # JWT (reutilizar auth)
```

**Structure Decision:** Evidencia en `apps/accidentes/` (vinculada a `idaccidente`); disponibilidad en `apps/despacho/` (flota y despacho). Módulo Angular `evidencia-unidad/` consume ambos grupos de paths del contrato único. Repositorios en `core/repositories/`. Actualizar `project-structure.md` con nota de extensión Emergencias (evidencia + disponibilidad declarada).

## Phase 0: Research (completado)

Ver `research.md` — resueltos: contract-first, capas Django, Kafka-only-write, Blob, JWT/RBAC, offline-first, sync parcial, estado default, Angular guards.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/evidencia-unidad.openapi.yaml`

| Rol | Endpoints |
|-----|-----------|
| Técnico de campo | Galería, captura foto/nota, sync |
| Unidad de emergencia | Idem evidencia + propia disponibilidad (`/mi-unidad-emergencia/*`) |
| Administrador | Galería lectura + flota completa |
| Servicio despacho | `GET /unidades-emergencia` (flota para algoritmo) |

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|-------------|----------|------------------------|
| `ListarEvidenciasView` | `ConsultaEvidenciaService` | `EvidenciaFotoRepository`, `NotaAccidenteRepository` (Pinot read) |
| `SubirEvidenciaFotoView` | `EvidenciaFotoService` | `BlobStorageService` → `EvidenciaFotoRepository.publish()` |
| `RegistrarNotaCampoView` | `NotaCampoService` | `NotaAccidenteRepository`, `AccidenteReadRepository` |
| `SincronizarEvidenciaView` | `SincronizarEvidenciaService` | Blob + repos evidencia (batch parcial) |
| `ListarUnidadesEmergenciaView` | `ConsultaFlotaService` | `UnidadEmergenciaRepository`, `HistorialEstadoUnidadRepository` |
| `ConsultarDisponibilidadView` | `DisponibilidadUnidadService` | `HistorialEstadoUnidadRepository` |
| `DeclararEstadoDisponibilidadView` | `DisponibilidadUnidadService` | `HistorialEstadoUnidadRepository.publish()` |

**Flujo escritura foto en línea:**

```text
POST /accidentes/{id}/evidencias/fotos
  → EvidenciaFotoService.validate_caso_activo()
  → BlobStorageService.upload()
  → EvidenciaFotoRepository.publish_create()  → Dim_EvidenciaFoto_topic
  → Response 201 { sincronizado: true, urlevidenciafoto }
```

**Flujo cambio disponibilidad:**

```text
POST /mi-unidad-emergencia/disponibilidad
  → DisponibilidadUnidadService.declarar_estado()
  → HistorialEstadoUnidadRepository.publish()  → Fact_HistorialEstadoUnidad_topic
  → Response 201 { estadoanterior, estadonuevo }
```

### Frontend — servicios y guards (prioridad 2, post-contrato)

| Artefacto | Contrato consumido |
|-----------|-------------------|
| `EvidenciaApiService` | `/accidentes/{id}/evidencias/*` |
| `DisponibilidadUnidadApiService` | `/unidades-emergencia/*`, `/mi-unidad-emergencia/*` |
| `EvidenciaOfflineStoreService` | Store local + merge galería |
| `EvidenciaGalleryGuard` | Roles galería (RN-EVI-012) |
| `UnidadEmergenciaDisponibilidadGuard` | Panel unidad |
| `AdministradorFlotaGuard` | Vista admin flota |
| `evidencia-unidad.types.ts` | Espejo schemas OpenAPI (sin `any`) |

### Permisos DRF (api-authentication)

| Permission class | Regla |
|------------------|-------|
| `IsTecnicoCampoOrUnidadOrAdmin` | Endpoints evidencia lectura/escritura |
| `IsUnidadEmergenciaOwn` | `/mi-unidad-emergencia/*` |
| `IsAdministradorOrDespachoService` | Flota `/unidades-emergencia` |
| `IsUnidadEmergenciaSelfOrAdmin` | `GET/POST .../{id}/...` por id |

JWT: validar firma RS256 + sesión activa (`Fact_Session`) en cada request.

### Data model

Ver `data-model.md` para entidades, topics Kafka, Blob y reglas RN/RF.

### Validación E2E

Ver `quickstart.md` para escenarios A–I y criterios de salida.

## Phase 2: Task Decomposition (siguiente comando)

No generado por este plan. Ejecutar `/speckit-tasks` para producir `tasks.md` ordenado:

1. Contract tests esqueleto desde OpenAPI
2. Repositorios + Kafka producer (evidencia + historial estado)
3. `BlobStorageService`
4. Servicios dominio (evidencia → disponibilidad)
5. Vistas DRF + permissions JWT/RBAC
6. Angular types + API services
7. Offline store + sync service
8. Guards + rutas
9. Páginas galería/captura/disponibilidad
10. Tests integración quickstart

## Complexity Tracking

Sin violaciones de constitution que requieran excepción.

## ISO 25010 — Impacto Safety

- Estado default **Fuera de servicio** evita despacho accidental a unidades sin historial.
- **Ocupada** / **Fuera de servicio** excluyen del algoritmo (RN-EVI-002).
- Evidencia no altera despacho directamente; enriquece expediente post-asignación.
- Transiciones automáticas Ocupada/Activa por `despacho-inteligente` y `seguimiento-cierre-de-casos` permanecen en esos módulos (mismo topic Kafka).

## Artifacts Generated

| Artefacto | Ruta |
|-----------|------|
| Plan | `specs/003-operational/Emergencias/evidencia-unidad/plan.md` |
| Research | `specs/003-operational/Emergencias/evidencia-unidad/research.md` |
| Data model | `specs/003-operational/Emergencias/evidencia-unidad/data-model.md` |
| Quickstart | `specs/003-operational/Emergencias/evidencia-unidad/quickstart.md` |
| OpenAPI contract | `specs/003-operational/Emergencias/evidencia-unidad/contracts/evidencia-unidad.openapi.yaml` |
