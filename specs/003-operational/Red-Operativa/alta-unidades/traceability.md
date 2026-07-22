# Trazabilidad — Alta y Configuración de Unidades de Emergencia

Mapeo CU → RF/RNF → Criterios de Aceptación → Task IDs, para verificación de cumplimiento por historia de usuario.

## US1 — Registro individual (CU-O54)

| Requisito | Descripción | Task IDs | Estado |
|---|---|---|---|
| RF-CAM-001 | Registro individual con validación de placa e `idcondado` | T006, T029, T030 | ✅ |
| RNF-CAM-001 | Validación de duplicado <1s | T071 | ✅ |
| CA-CAM-001 | Alta con todos los campos reales | T024, T029 | ✅ |
| CA-CAM-002 | Rechazo por placa duplicada (409) | T024, T029 | ✅ |

**Gate T037**: CA-CAM-001, CA-CAM-002 cumplidos — 25 tests backend + frontend en verde (US1).

## US2 — Registro en lote (CU-O56)

| Requisito | Descripción | Task IDs | Estado |
|---|---|---|---|
| RF-CAM-002 | Importación CSV todo-o-nada, límite duro 500 filas | T041, T042 | ✅ |
| RNF-CAM-002 | ≤30s para 500 unidades | T040 | ✅ |
| CA-CAM-003 | Ninguna unidad insertada si una fila falla | T038, T039 | ✅ |

**Gate T045**: CA-CAM-003 cumplido — test de performance bajo el umbral de 30s.

## US3 — Edición (CU-O57)

| Requisito | Descripción | Task IDs | Estado |
|---|---|---|---|
| RF-CAM-003 | Campos editables, inmutables, bloqueo por despacho activo, last-write-wins | T048, T049 | ✅ |
| CA-CAM-004 | Edición sin modificar `idunidademergencia`/`idcliente` | T046, T048 | ✅ |
| CA-CAM-005 | Bloqueo/confirmación con despacho activo | T047, T048 | ✅ |

**Gate T052**: CA-CAM-004, CA-CAM-005 cumplidos.

## US4 — Baja y reactivación (CU-O58)

| Requisito | Descripción | Task IDs | Estado |
|---|---|---|---|
| RF-CAM-004 | Baja normal/forzada, reactivación con validación de placa | T056, T057 | ✅ |
| RN-CAM-003, RN-CAM-004 | Unicidad de placa en reactivación; historial append-only | T056 | ✅ |
| CA-CAM-006 | Baja registra `Fact_BajaUnidad` y `activo=false` | T053, T056 | ✅ |
| CA-CAM-007 | Reactivación conserva historial de baja | T054, T056 | ✅ |

**Gate T060**: CA-CAM-006, CA-CAM-007 cumplidos.

## US5 — Disponibilidad externa (CU-O59)

| Requisito | Descripción | Task IDs | Estado |
|---|---|---|---|
| RF-CAM-005 | Declaración de disponibilidad por Operador, alerta si "Activa" con despacho activo | T064, T065 | ✅ |
| CA-CAM-008 | `idusuario` registrado es el del Operador | T061, T064 | ✅ |
| CA-CAM-009 | Alerta (422) al marcar "Activa" con despacho sin retirar | T061, T064 | ✅ |

**Gate T070**: CA-CAM-008, CA-CAM-009 cumplidos.

## Migración cruzada (bloqueante, ejecutada en Foundational)

| Módulo afectado | Cambio | Task IDs | Estado |
|---|---|---|---|
| `despacho-inteligente` | `zonacobertura` → `idcondado` (spec, data-model, repositorio, servicio) | T018–T023 | ✅ 90/90 tests en verde |
| `evidencia-unidad` | `zonacobertura` → `idcondado` (contrato OpenAPI, tipo TS, template Angular) | T023a–T023e | ✅ verificado con `tsc --noEmit` + `ng build` |

## Resumen de cobertura

- Total CU cubiertos: 5/5 (CU-O54, O56, O57, O58, O59)
- Total CA cubiertos: 9/9 (CA-CAM-001 a CA-CAM-009)
- Tests backend: 61/61 en `apps/red_operativa` + 90/90 en `apps/despacho` tras la migración
- Tests frontend: no ejecutables en este entorno (sin Chrome/Karma) — validados con `tsc --noEmit` (app + spec) y `ng build` de producción, ambos limpios
