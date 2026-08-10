# Trazabilidad — Evidencia en Sitio y Disponibilidad de Unidad

**Feature**: `specs/003-operational/Emergencias/evidencia-unidad/backend/`  
**Fecha validación**: 2026-07-09 (US1–US4) · **Extensión CU-O75/CU-O76**: 2026-07-28 · **RF-EVI-010 Implicados**: 2026-07-29

| CU | Descripción | Tasks | Estado |
|----|-------------|-------|--------|
| CU-O74 | Adjuntar evidencias | T022–T068 | ✓ |
| CU-O78 | Disponibilidad | (US1) | ✓ |
| CU-O77 | Sync diferida | (US3) | ✓ |
| CU-O75/CU-O76 | Enriquecer datos estructurados en sitio | T079–T125 + T128–T136 | ✓ |

## Matriz CU / RF / CA → Tasks

| ID | Descripción | Tasks | Estado |
|----|-------------|-------|--------|
| CU-O74 | Adjuntar evidencias en sitio | T040–T057 | ✓ |
| CU-O78 | Gestionar disponibilidad de unidad | T025–T039 | ✓ |
| CU-O77 | Sincronización diferida offline | T059–T069 (+ T107 enriquecimiento) | ✓ |
| CU-O75/CU-O76 | Enriquecer datos estructurados en sitio | T079–T136 | ✓ |
| RF-EVI-001 | Declarar estado disponibilidad | T031, T033, T034–T038 | ✓ |
| RF-EVI-002 | Subir evidencia fotográfica | T046, T049, T050, T057 | ✓ |
| RF-EVI-003 | Registrar nota de campo | T047, T049, T050, T057 | ✓ |
| RF-EVI-004 | Consultar disponibilidad/flota | T032, T033, T034, T038 | ✓ |
| RF-EVI-005 | Galería evidencias sincronizadas | T048, T049, T056 | ✓ |
| RF-EVI-006 | Sync diferida batch parcial | T062–T068, T107 | ✓ |
| RF-EVI-007 | Clima/período en sitio | T084, T094, T099, T103, T108 | ✓ |
| RF-EVI-008 | Elementos físicos en sitio | T085, T095, T100, T104, T108 | ✓ |
| RF-EVI-009 | Conductores/vehículos + Security PII | T086–T091, T096, T101, T105, T108, T110, T113, T121, T123, T125 | ✓ |
| RF-EVI-010 | Implicados no conductores (ontología diagrama) | T128–T136 + **T137–T150** remediación | ✓ |
| CA-EVI-015 | Implicados ontología | T137–T150 | ✓ |
| RNF-EVI-007/008 | Latencias catálogos / alta conductor | T124 | ✓ |
| RNF-EVI-009 | Cifrado PII tránsito/reposo/offline | T113, T114, T121, T123 | ✓ |
| RNF-EVI-010 | UX design-system enriquecimiento | T122 | ✓ |
| CA-EVI-001 | Unidad declara Ocupada | T025, T029, T031, T039 | ✓ |
| CA-EVI-002 | Default Fuera de servicio sin historial | T029, T031, T039 | ✓ |
| CA-EVI-003 | Subida foto en línea | T041, T043, T046, T058 | ✓ |
| CA-EVI-004 | Sync parcial con reintento | T059–T060, T062–T066, T069 | ✓ |
| CA-EVI-005 | Nota de campo registrada | T042, T044, T047, T058 | ✓ |
| CA-EVI-006 | Evidencia offline solo en capturador | T061, T064–T065, T069 | ✓ |
| CA-EVI-007 | Galería RBAC | T040, T045, T048, T052, T058 | ✓ |
| CA-EVI-008 | Caso inactivo rechaza captura | T043–T046, T058 | ✓ |
| CA-EVI-009 | Historial estado trazable | T028, T031, T039 | ✓ |
| CA-EVI-010 | Clima y período en sitio | T094, T099, T103, T118 | ✓ |
| CA-EVI-011 | Elementos físicos en sitio | T095, T100, T104, T118 | ✓ |
| CA-EVI-012 | Conductores y vehículos | T096, T101, T105, T118 | ✓ |
| CA-EVI-013 | PII conductor reposo/offline | T113, T121, T123, T118 | ✓ |
| CA-EVI-014 | UX enriquecimiento bajo presión | T122, T118 | ✓ |
| RN-EVI-012 | Roles galería | T020, T052, T071 | ✓ |
| RN-EVI-015 | RBAC consulta disponibilidad | T022, T036, T054, T071 | ✓ |
| RN-EVI-016–021 | RBAC/reglas enriquecimiento + PII offline | T092–T093, T101, T105, T113–T114 | ✓ |

## Validación quickstart (escenarios A–I + J–M)

| Escenario | Descripción | Validación | Resultado |
|-----------|-------------|------------|-----------|
| A–I | Evidencia / disponibilidad / sync | tests existentes | ✓ |
| J | Clima/período CU-O75/CU-O76 | `test_enriquecimiento_clima_*` | ✓ |
| K | Elementos físicos CU-O75/CU-O76 | `test_enriquecimiento_elementos_fisicos_*` | ✓ |
| L | Conductores/vehículos CU-O75/CU-O76 | `test_enriquecimiento_conductores_*` | ✓ |
| N | Implicados no conductores RF-EVI-010 | `test_enriquecimiento_implicados_*` / T128–T136 | ✓ |
| M | PII conductor cifrado offline + checklist at-rest | T121, T123 / CA-EVI-013 | ✓ |

## Cobertura backend (T077 / T119)

| Capa | Umbral | Resultado |
|------|--------|-----------|
| Servicios enriquecimiento CU-O75/CU-O76 | ≥80% | **86%** (T119) |

## Frontend

| Artefacto | Ruta | Estado |
|-----------|------|--------|
| Types OpenAPI | `evidencia-unidad.types.ts` | ✓ T081 |
| Enriquecimiento API | `enriquecimiento-api.service.ts` | ✓ T111 |
| Offline store + PII AES-GCM | `evidencia-offline-store.service.ts` | ✓ T113/T121 |
| Sync scheduler / multipart `enriquecimiento` | `evidencia-api` + scheduler | ✓ T114 |
| Ruta + `EvidenciaGalleryGuard` | `evidencia-unidad.routes.ts` | ✓ T116 |
| Página enriquecimiento | `enriquecimiento-accidente.page.ts` | ✓ T115/T122 |

## Extensión 2026-07-28

- CU-O75/CU-O76 implementado (T079–T125): repos, servicios, vistas, catálogos, sync, frontend offline cifrado, gates CA-EVI-010…014.
