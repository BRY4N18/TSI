# Trazabilidad: Registro de Accidentes

## Criterios de aceptación

| CA | Descripción | Tareas | Tests | Estado |
|----|-------------|--------|-------|--------|
| CA-REG-001 | Registro sin advertencias → REPORTADO | T028, T038 | `test_registrar_when_valid_returns_201_reportado` | ✓ |
| CA-REG-002 | Advertencias forzadas → BORRADOR | T028, T038 | `test_confirmar_when_borrador_returns_200` | ✓ |
| CA-REG-003 | Confirmación BORRADOR→REPORTADO | T029, T039 | `test_confirmar_when_borrador_returns_200` | ✓ |
| CA-REG-004 | Fusión duplicados | T065-T069 | `test_fusionar_when_valid_returns_200` | ✓ |
| CA-REG-005 | Lista accidentes activos | T047, T052 | `test_listar_when_activos_returns_200` | ✓ |
| CA-REG-006 | Geocodificación inversa | T027, T035 | `test_geocodificacion_when_valid_coords_returns_200` | ✓ |
| CA-REG-007 | Edición complementaria con auditoría | T049, T052 | `test_patch_when_increment_numvehiculos_returns_200` | ✓ |
| CA-REG-008 | 403 roles no autorizados | T016, T080 | `test_escalar_when_operador_returns_403` | ✓ |
| CA-REG-009 | Descarte solo BORRADOR | T058-T061 | `test_descartar_when_borrador_returns_200` | ✓ |
| CA-REG-010 | Escalamiento O40 | T072-T080 | `test_escalar_when_valid_returns_200` | ✓ |
| CA-REG-011 | Padre sugerido más antiguo | T066, T067 | `test_suggest_parent_returns_oldest_candidate` | ✓ |
| CA-REG-012 | Escalamiento requiere despacho | T075 | `test_escalar_when_no_despacho_raises` | ✓ |
| CA-REG-013 | Retrospectivo >24h | T025 | `test_validate_registro_when_retrospective_without_justification_blocks` | ✓ |
| CA-REG-014 | Cobertura Producción | T026, T034 | `test_en_cobertura_por_calle_when_in_production_returns_true` | ✓ |

## Requisitos funcionales

| RF | Descripción | Tareas |
|----|-------------|--------|
| RF-REG-003 | Validación registro | T025, T033, T067 |
| RF-REG-005 | Consulta/edición (filtros severidad/estado/activo/fecha/ciudad/estado-región + tabla rediseñada) | T047-T055, T098-T103 |
| RF-REG-006 | Geocodificación | T023, T035, T043 |
| RF-REG-010 | Confirmar reporte | T024, T029, T039 |

## Casos de uso

| CU | Descripción | Tareas |
|----|-------------|--------|
| CU-O21 | Registro accidente | T022-T045 |
| CU-O32 | Descartar caso | T058-T062 |
| CU-O40 | Escalar severidad | T072-T082 |
| CU-O41 | Fusionar duplicados | T064-T070 |

## RNF

| RNF | Evidencia | Tarea |
|-----|-----------|-------|
| RNF-REG-004 | Auditoría en servicios | T018, T019 |
| RNF-REG-005 | p95 registro ≤500ms (mock) | T085, T086 |
| RNF-REG-006 | Autosave en localStorage + restauración + indicador `syncStatus` (live/reconnecting/offline) en `registro-accidente.page.ts` | T045b, T045c, T046b |

## Escenarios quickstart A–G

| Escenario | Validación |
|-----------|------------|
| A | pytest API registro REPORTADO |
| B | pytest confirmar borrador |
| C | pytest confirmar-reporte |
| D | pytest duplicado + fusionar |
| E | pytest descartar |
| F | pytest escalar-severidad |
| G | pytest retrospectivo |

Cobertura servicios `apps/accidentes/services`: **93%** (pytest-cov, T089).
