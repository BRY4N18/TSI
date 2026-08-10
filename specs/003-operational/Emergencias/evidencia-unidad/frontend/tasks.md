# Tasks: Evidencia en Sitio — Frontend

**Input**: `frontend/spec.md`, Depends-on `../backend/`
**Prerequisites**: Backend US1–US6 + Phase 10 implicados completados.

## Phase 0: Stub (Fase A)

- [X] T-FE-000 Crear capa `frontend/` stub (2026-07-30)

## Phase 1: Disponibilidad (FR-UI-001–003)

- [X] T-FE-001 `DisponibilidadUnidadApiService` + spec (backend T034–T035)
- [X] T-FE-002 `UnidadEmergenciaDisponibilidadGuard` + spec (backend T036–T037)
- [X] T-FE-003 `panel-disponibilidad.page.*` (backend T038)

## Phase 2: Galería y offline (FR-UI-004–008)

- [X] T-FE-004 `EvidenciaApiService` + spec (backend T050–T051)
- [X] T-FE-005 `EvidenciaGalleryGuard` + `AdministradorFlotaGuard` (backend T052–T055)
- [X] T-FE-006 `galeria-evidencias.page.*` + modals captura/visor (backend T056–T057, T068)
- [X] T-FE-007 `EvidenciaOfflineStoreService` + spec (backend T064, T061)
- [X] T-FE-008 `evidencia-sync-scheduler.service.*` + merge galería (backend T065–T067)

## Phase 3: Integración rutas (FR-UI-018–019)

- [X] T-FE-009 Rutas lazy + spec (backend T071, T070)
- [X] T-FE-010 Nav Técnico + `accidentesLecturaGuard` (backend T072b)

## Phase 4: Enriquecimiento CU-O75/CU-O76 (FR-UI-009–017)

- [X] T-FE-011 `EnriquecimientoApiService` + spec (backend T111–T112)
- [X] T-FE-012 Offline enriquecimiento + cifrado PII conductor (backend T113–T114, T121)
- [X] T-FE-013 `enriquecimiento-accidente.page.*` paneles clima/físico/conductor/vehículo (backend T115–T127)
- [X] T-FE-014 Ruta enriquecimiento + guard galería (backend T116–T117)
- [X] T-FE-015 Conformidad design-system RNF-EVI-010 (backend T122)

## Phase 5: Implicados ontología (FR-UI-013)

- [X] T-FE-016 Tipos/API/UI implicados ontología (backend T144–T147)

## Phase 6: mode=view (FR-UI-016)

- [X] T-FE-017 Soporte `?mode=view` solo lectura (integración registro-accidente frontend)

## Phase 7: Documentación Fase B

- [X] T-FE-018 Completar `frontend/spec.md` Interaction (2026-07-30)

**Checkpoint**: FR-UI-001…019 cubiertos en código (backend tasks US1–US6 + Phase 10).
