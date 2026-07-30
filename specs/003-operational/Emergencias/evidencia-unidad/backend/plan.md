# Implementation Plan: Evidencia en Sitio y Gestión de Disponibilidad de Unidad

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../evidencia-unidad.md`](../evidencia-unidad.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — stub Fase A; no duplicar OpenAPI/data-model en FE.


**Branch**: `evidencia-unidad` | **Date**: 2026-07-09 (remediación Dim_Implicado: **2026-07-29**) | **Spec**: `specs/003-operational/Emergencias/evidencia-unidad/backend/spec.md`

**Input**: Feature specification from `specs/003-operational/Emergencias/evidencia-unidad/backend/spec.md` (clarificaciones Session 2026-07-09 / 07-28 / **07-29 ontología Dim_Implicado**).

## Summary

Implementar evidencia fotográfica/notas de campo, **enriquecimiento estructurado en sitio (CU-O46: clima/período, elementos físicos, conductores/vehículos, implicados no conductores RF-EVI-010 alineado a ontología `Dim_Implicado`: `tipoimplicado`, `genero`, `estadoimplicado`, `edad`, `activo` — sin PII de identidad; Pinot `database/` sin cambio)**, gestión de disponibilidad de unidades y sincronización offline con enfoque **contract-first**: primero el contrato OpenAPI REST (`contracts/evidencia-unidad.openapi.yaml`) alineado a `api-standards.md` y a `flujoscorreguidos/flujo-emergencias-canonico.md` (escritura de enriquecimiento **exclusiva** del Técnico/Unidad; sin precarga CU-O21); luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura de dominio exclusiva vía **Kafka** y binarios en **Azure Blob**; finalmente frontend Angular 17+ con servicios tipados, store offline y guards por rol. Cubre CU-O27, CU-O46, CU-O30 y CU-O43.

### Remediación activa 2026-07-29 (app → ontología)

El contrato/spec/data-model ya describen la ontología. El **código y tests** aún publican PII (`identificacion`/`nombres`/`apellidos`/`lesionado`/…). Esta pasada de plan define el trabajo de alineación **sin tocar** `database/esquemas.json` ni `tablas.json`.

## Traceability

- **Objetivo operacional:** enriquecer expediente de accidente (evidencia + datos estructurados) y mantener flota despachable en tiempo real.
- **UC cubiertos:** CU-O27, CU-O46, CU-O30, CU-O43.
- **Dependencias:** `autenticacion-y-rbac`, `registro-accidente`, `despacho-inteligente`, `seguimiento-cierre-de-casos`.
- **Consumidores downstream:** `despacho-inteligente` (estado unidad), aseguradoras/auditoría/analítica (evidencia + enriquecimiento).

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
| Functional Suitability | PASS | CU-O27/O46/O30/O43 + CA-EVI-001–**015** (implicados ontología) |
| Reliability | PASS | Sync parcial con reintento; idempotencia; fail-safe estado default; enriquecimiento no bloquea despacho |
| Performance Efficiency | PASS | RNF-EVI-003/004/006 (despacho/sync/consulta estado) + **RNF-EVI-007/008** (catálogos ≤2s, alta conductor ≤3s p95) |
| Interaction Capability | PASS | Galería offline+online; indicador sync; **RNF-EVI-010 / CA-EVI-014** UI enriquecimiento; CA-EVI-015 sin campos PII en implicado |
| Security | PASS | JWT + RBAC; **PII solo en `Dim_Conductor`** (RNF-EVI-009); `Dim_Implicado` **sin** PII de identidad (Decision 13) |
| Compatibility | PASS | Contract-first OpenAPI; schemas `RegistrarImplicadoRequest` / `ImplicadoItem` = ontología |
| Maintainability | PASS | Vista→Servicio→Repositorio; un solo modelo Dim_Implicado (app = Pinot = diagrama) |
| Flexibility | PASS | Offline-first; Blob desacoplado de Pinot; catálogos Pinot multi-región |
| Safety | PASS | Default Fuera de servicio; Ocupada excluye despacho; enriquecimiento no altera asignación |

**Post-Design Gate (re-check 2026-07-28 tras CU-O46):** PASS — gaps Principle V (at-rest/offline PII) y Performance/Interaction del enriquecimiento cerrados en spec/plan/research/tasks.

**Post-Design Gate (re-check 2026-07-29 remediación Dim_Implicado):** PASS condicionado a implementar remediación en `/speckit-tasks` + `/speckit-implement` — spec/contrato/data-model ya alineados; código pendiente (gap canónico #12).

**Tie-Breaker:**
1. Maintainability vs Performance (histórico) — documentado en `research.md` Decision tie-breaker original.
2. **Security vs Maintainability (CU-O46 PII conductores):** dominio de identidad → **Information Security** prioriza sobre Maintainability (nunca sobre Safety). Ver Decision 11.
3. **Maintainability vs Functional Suitability ampliada (implicados):** ontología dimensional gana sobre modelo PII inventado en app — Decision 13.
## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Emergencias/evidencia-unidad/backend/
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
│   │   │   ├── evidencia_views.py
│   │   │   ├── enriquecimiento_views.py       # clima/físico/conductores/implicados
│   │   │   └── urls.py
│   │   ├── services/
│   │   │   ├── evidencia_foto_service.py
│   │   │   ├── nota_campo_service.py
│   │   │   ├── sincronizar_evidencia_service.py
│   │   │   ├── consulta_evidencia_service.py
│   │   │   ├── enriquecimiento_*_service.py   # clima, físico, conductor, implicado
│   │   │   └── consulta_enriquecimiento_service.py
│   │   ├── permissions.py
│   │   └── tests/…/test_enriquecimiento_implicados_*.py
│   └── despacho/
│       ├── views/disponibilidad_views.py
│       ├── services/disponibilidad_unidad_service.py
│       └── tests/api/test_disponibilidad_contract.py
└── core/
    ├── repositories/
    │   ├── evidencia/
    │   │   ├── evidencia_foto_repository.py
    │   │   ├── nota_accidente_repository.py
    │   │   ├── accidente_read_repository.py
    │   │   ├── conductor_repository.py / vehiculo_repository.py / …
    │   │   └── implicado_repository.py        # payload = ontología Pinot
    │   └── despacho/
    │       ├── historial_estado_unidad_repository.py
    │       └── unidad_emergencia_repository.py
    └── storage/
        └── blob_storage_service.py

frontend/
└── src/app/modules/evidencia-unidad/
    ├── pages/
    │   ├── galeria-evidencias/
    │   ├── captura-evidencia/
    │   ├── enriquecimiento-accidente/          # form implicado = ontología
    │   └── panel-disponibilidad/
    ├── services/
    │   ├── evidencia-api.service.ts
    │   ├── enriquecimiento-api.service.ts
    │   ├── disponibilidad-unidad-api.service.ts
    │   ├── evidencia-offline-store.service.ts # LocalImplicado sin crypto PII
    │   └── models/evidencia-unidad.types.ts
    ├── guards/…
    └── evidencia-unidad.routes.ts
```

**Structure Decision:** Evidencia en `apps/accidentes/` (vinculada a `idaccidente`); disponibilidad en `apps/despacho/` (flota y despacho). Módulo Angular `evidencia-unidad/` consume ambos grupos de paths del contrato único. Repositorios en `core/repositories/`. Actualizar `project-structure.md` con nota de extensión Emergencias (evidencia + disponibilidad declarada).

## Phase 0: Research (completado)

Ver `research.md` — resueltos: contract-first, capas Django, Kafka-only-write, Blob, JWT/RBAC, offline-first, sync parcial, estado default, Angular guards, **Decision 13 ontología Dim_Implicado**.

## Phase 1: Design & Contracts (completado + remediación contrato 2026-07-29)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/evidencia-unidad.openapi.yaml`

| Rol | Endpoints |
|-----|-----------|
| Técnico de campo | Galería, captura foto/nota, sync, **enriquecimiento CU-O46** (clima/físico/conductores/**implicados**) |
| Unidad de emergencia | Idem evidencia + enriquecimiento + propia disponibilidad (`/mi-unidad-emergencia/*`) |
| Administrador | Galería/enriquecimiento lectura + flota completa |
| Servicio despacho | `GET /unidades-emergencia` (flota para algoritmo) |

**Schemas implicado (ontología — ya en OpenAPI):** `RegistrarImplicadoRequest` / `ImplicadoItem` = `tipoimplicado`, `estadoimplicado`, `genero?`, `edad?`, `activo`; **prohibido** PII de identidad.

### Phase 1b — Remediación código (siguiente: `/speckit-tasks`)

| Capa | Archivos a alinear | Cambio |
|------|--------------------|--------|
| Repo | `backend/core/repositories/evidencia/implicado_repository.py` | Payload Kafka/Pinot: `tipoimplicado`, `genero`, `estadoimplicado`, `edad`, `activo`, `fecha_actualizacion` (+ `idimplicado`, `idaccidente`). Quitar PII / `idusuario` del documento de negocio. |
| Service | `enriquecimiento_implicado_service.py` | Validar enums; requeridos `tipoimplicado`+`estadoimplicado`; opcionales `genero`/`edad`. |
| Sync | `sincronizar_evidencia_service.py` | Mapear batch offline sin `identificacion`/`nombres`/… |
| Views | `enriquecimiento_views.py` | Passthrough body OpenAPI. |
| Tests BE | `test_enriquecimiento_implicados_*`, `test_implicado_repository.py`, sync/consulta | Fixtures ontología; assert ausencia de PII. |
| Types/FE | `evidencia-unidad.types.ts`, `enriquecimiento-api.service.ts` | Tipos = OpenAPI. |
| Offline | `evidencia-offline-store.service.ts` | `LocalImplicado` campos planos; **sin** AES-GCM (no PII). |
| UI | `enriquecimiento-accidente.page.ts` / `.html` | Form: tipo + estado (+ género/edad); quitar cédula/nombres/`lesionado`. |
| Docs runtime | `quickstart.md` Escenario N, `traceability.md` | Ya parcialmente; cerrar CA-EVI-015 en tasks. |

**No modificar:** `database/esquemas.json`, `database/tablas.json`, topic `Dim_Implicado_topic`.

**Flujo escritura implicado (post-remediación):**

```text
POST /accidentes/{id}/enriquecimiento/implicados
  → EnriquecimientoImplicadoService.registrar(tipoimplicado, estadoimplicado, genero?, edad?)
  → ImplicadoRepository.create() → Dim_Implicado_topic
  → 201 ImplicadoItem (ontología)
```

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
| `Implicados*View` / enriquecimiento | `EnriquecimientoImplicadoService` | `ImplicadoRepository` → `Dim_Implicado_topic` |
| `ConsultaEnriquecimientoView` | `ConsultaEnriquecimientoService` | repos clima/físico/conductor/**implicado** |

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
| `EnriquecimientoApiService` | `/accidentes/{id}/enriquecimiento/*` (incl. implicados) |
| `DisponibilidadUnidadApiService` | `/unidades-emergencia/*`, `/mi-unidad-emergencia/*` |
| `EvidenciaOfflineStoreService` | Store local + merge galería; LocalImplicado sin PII |
| `EvidenciaGalleryGuard` | Roles galería (RN-EVI-012) |
| `UnidadEmergenciaDisponibilidadGuard` | Panel unidad |
| `AdministradorFlotaGuard` | Vista admin flota |
| `evidencia-unidad.types.ts` | Espejo schemas OpenAPI (sin `any`; implicado = ontología) |

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
11. **Remediación Dim_Implicado (2026-07-29):** tests → repo/service/sync → FE types/offline/UI (Phase 1b); **no** tocar `database/`

## Complexity Tracking

Sin violaciones abiertas de constitution. Trade-offs:
- Security↔Maintainability (PII conductor offline) — Decision 11.
- Ontología↔modelo PII implicados — Decision 13 (gana ontología; remediación app pendiente en tasks/implement).

## ISO 25010 — Impacto Safety

- Estado default **Fuera de servicio** evita despacho accidental a unidades sin historial.
- **Ocupada** / **Fuera de servicio** excluyen del algoritmo (RN-EVI-002).
- Evidencia y **enriquecimiento CU-O46 no alteran despacho** directamente; enriquecen expediente post-asignación.
- Transiciones automáticas Ocupada/Activa por `despacho-inteligente` y `seguimiento-cierre-de-casos` permanecen en esos módulos (mismo topic Kafka).

## Artifacts Generated

| Artefacto | Ruta | Estado remediación 2026-07-29 |
|-----------|------|-------------------------------|
| Plan | `plan.md` | Phase 1b + estructura actualizados |
| Research | `research.md` | Decision 13 |
| Data model | `data-model.md` | Ontología Dim_Implicado |
| Quickstart | `quickstart.md` | Escenario N + criterios CA-EVI-015 |
| OpenAPI | `contracts/evidencia-unidad.openapi.yaml` | Schemas implicado = ontología |
| Tasks | `tasks.md` | Phase 10 T137–T150 generadas |
