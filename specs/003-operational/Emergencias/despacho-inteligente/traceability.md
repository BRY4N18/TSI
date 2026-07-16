# Traceability — Despacho Inteligente

Matriz CU/RF/CA → tasks y validación quickstart (2026-07-09).

## Criterios de aceptación

| CA | Descripción | Tasks | Validación |
|----|-------------|-------|------------|
| CA-DES-001 | Asignación <5s tras REPORTADO | T033, T038, T098 | `test_asignacion_automatica_integration`, `test_cadena_critica_despacho_integration` |
| CA-DES-002 | Filtro condado + scoring | T029, T035 | `test_consulta_candidatas_service` |
| CA-DES-003 | Notificación push/SMS | T031, T037 | `test_notificacion_despacho_service` |
| CA-DES-004 | Confirmar → ASIGNADO + Ocupada | T042, T046, T098 | `test_confirmar_despacho_contract` |
| CA-DES-005 | Rechazo → activo=false + O36 | T043, T047 | `test_rechazar_despacho_contract` |
| CA-DES-006 | Timeout job O35 | T050, T056, T057 | `test_timeout_despacho_service` |
| CA-DES-007 | Consumer O36 async | T052, T058, T053 | `test_timeout_reasignacion_integration` |
| CA-DES-008 | Parámetros RF-DES-010 | T076-T079 | `test_parametros_despacho_contract` |
| CA-DES-010 | Asignación manual O33 | T062, T069 | `test_asignar_manual_contract` |
| CA-DES-011 | Monitoreo REST + SSE | T060, T072, T074 | `test_monitoreo_despacho_contract` |
| CA-DES-012 | Escalamiento O34 | T063, T070 | `test_escalar_zona_contract` |
| CA-DES-013 | Fail entrega O23→O36 | T054 | `test_fallo_notificacion_integration` |

## Casos de uso

| CU/RF | Implementación | Tests |
|-------|----------------|-------|
| CU-O22 | `asignacion_inteligente_service`, `accidente_reportado_consumer` | T030, T032, T033 |
| CU-O23 | `notificacion_despacho_service` | T031 |
| CU-O24 | `confirmar_despacho_service`, `mi_despacho_views` | T042, T044 |
| CU-O33 | `asignacion_manual_service`, `asignacion_views` | T062, T065 |
| CU-O34 | `escalamiento_zona_service` | T063, T066 |
| CU-O35 | `timeout_despacho_service`, `timeout_despacho_job` | T050, T053 |
| CU-O36 | `reasignacion_despacho_service`, `despacho_timeout_consumer` | T051, T052 |
| CU-O38 | `coordinacion_multiple_service` | T064, T067 |
| CU-O45 | `rechazar_despacho_service` | T043, T045 |
| RF-DES-010 | `parametros_despacho_service`, `parametros_views` | T077, T076 |
| RF-DES-011 | `monitoreo_despacho_service`, `monitoreo_views` | T068, T060 |

## Quickstart escenarios A–H

| Escenario | Estado | Evidencia |
|-----------|--------|-----------|
| A — O22 automático | ✅ | `test_accidente_reportado_consumer`, integración |
| B — O24 confirmar | ✅ | API + servicio confirmar |
| C — O45 rechazo + O36 | ✅ | API rechazar + reasignación |
| D — O35 + O36 async | ✅ | `test_timeout_reasignacion_integration` |
| E — Fallo O23 | ✅ | `test_fallo_notificacion_integration` |
| F — O34 escalar | ✅ | `test_escalar_zona_contract` |
| G — O38 coordinar | ✅ | `test_coordinar_despacho_contract` |
| H — RF-DES-010 parámetros | ✅ | `test_parametros_despacho_contract` |

## Frontend (US6)

| Artefacto | Ruta / archivo |
|-----------|----------------|
| DespachoApiService | `frontend/src/app/modules/despacho/services/despacho-api.service.ts` |
| MiDespachoApiService | `.../mi-despacho-api.service.ts` |
| DespachoSseService | `.../despacho-sse.service.ts` |
| Guards | `.../guards/*.guard.ts` |
| Páginas | `.../pages/*` |
| Menú sidebar | `frontend/src/app/core/sidebar/despacho-menu.config.ts` |

## Cambios fuera de ciclo

Ver `.specify/docs/changelog.md` § 2026-07-15 — fixes G1 (jobs periódicos sin agendar:
`run_timeout_despacho_job`, RN-SEG relacionadas) y G5 (scoring "disponibilidad reciente"
hardcodeado en `consulta_candidatas_service.py`, RN-DES-008) aplicados fuera del ciclo
plan→tasks. G7 (stubs push/SMS) y G8 (payload alerta crítica RF-DES-008) quedan
pendientes/fuera de alcance — ver changelog.
