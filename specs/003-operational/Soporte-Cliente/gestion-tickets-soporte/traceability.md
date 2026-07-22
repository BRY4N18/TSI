# Traceability — Gestión de Tickets de Soporte

Matriz CU/RF/CA → tasks y validación quickstart (2026-07-21).

## Criterios de aceptación

| CA | Descripción | Tasks | Validación |
|----|-------------|-------|------------|
| CA-TIC-001 | Registro con clasificación automática y SLA asignado | T026-T030 | `test_clasificacion_automatica_service`, `test_asignacion_sla_service`, `test_registrar_ticket_contract`, `test_flujo_completo_ticket_integration` |
| CA-TIC-002 | Ticket no clasificable sin SLA | T026, T028-T030 | `test_clasificacion_automatica_service::test_clasificar_when_no_match_returns_none`, `test_registrar_ticket_contract::test_registrar_when_no_clasificable_returns_pendiente` |
| CA-TIC-003 | Agente toma, comenta, responde | T041-T042, T046-T047 | `test_tomar_ticket_service`, `test_comentar_ticket_service`, `test_tomar_ticket_contract`, `test_comentar_ticket_contract` |
| CA-TIC-004 | Escalado manual | T043, T046-T047 | `test_escalar_ticket_service`, `test_escalar_ticket_contract` |
| CA-TIC-005 | Resuelto notifica y espera confirmación | T044-T047 | `test_resolver_ticket_service`, `test_resolver_ticket_contract` |
| CA-TIC-006 | Cliente confirma cierre | T045-T047 | `test_confirmar_cierre_service::test_confirmar_when_resuelto_pasa_a_cerrado`, `test_confirmar_cierre_contract` |
| CA-TIC-007 | Auto-cierre a los 5 días | T045, T051 | `test_confirmar_cierre_service::test_cerrar_automaticamente_vencidos_cuando_pasaron_5_dias` |
| CA-TIC-008 | Admin crea regla SLA | T056-T058 | `test_configurar_sla_service::test_crear_when_valido_publica_regla_activa`, `test_sla_config_contract` |
| CA-TIC-009 | Admin modifica regla SLA sin afectar tickets existentes | T056-T058 | `test_configurar_sla_service::test_modificar_when_valido_desactiva_y_crea_nueva`, `test_modificar_sla_config_contract` |
| CA-TIC-010 | Job marca sla_status='en riesgo' al 80% | T050-T052 | `test_monitoreo_sla_service::test_ejecutar_ciclo_when_sobre_80_marca_en_riesgo` |
| CA-TIC-011 | Job escala automáticamente al exceder SLA | T050-T052 | `test_monitoreo_sla_service::test_ejecutar_ciclo_when_excede_100_escala_a_supervisor` |
| CA-TIC-012 | Reapertura con historial conservado | T061-T063 | `test_reabrir_ticket_service::test_reabrir_when_cerrado_renueva_sla_y_conserva_historial`, `test_reabrir_ticket_contract` |
| CA-TIC-013 | Reapertura permite adjuntar nueva evidencia | T061-T063 | `test_reabrir_ticket_service::test_reabrir_when_adjunto_publica_archivo` |

## Casos de uso

| CU/RF | Implementación | Tests |
|-------|----------------|-------|
| CU-O91 | `clasificacion_automatica_service`, `asignacion_sla_service`, `registrar_ticket_service`, `TicketsView.post`, `ClasificarTicketManualView` | T022-T024 |
| CU-O92 | `tomar_ticket_service`, `comentar_ticket_service`, `escalar_ticket_service`, `resolver_ticket_service`, `confirmar_cierre_service` | T036-T040 |
| CU-O95 | `configurar_sla_service`, `SLAConfigView`, `SLAConfigDetalleView` | T055 |
| CU-O96 | `monitoreo_sla_service`, `monitoreo_sla_job` + `management/commands/run_monitoreo_sla_job.py` | T048-T049 |
| CU-O97 | `reabrir_ticket_service`, `ReabrirTicketView` | T060 |
| RF-TIC-007 | `dashboard_soporte_service`, `DashboardSoporteView` | T065 |

## Quickstart escenarios A–G

| Escenario | Estado | Evidencia |
|-----------|--------|-----------|
| A — Clasificación automática | ✅ | `test_clasificacion_automatica_service`, `test_registrar_ticket_contract::test_registrar_when_valid_returns_201` |
| B — No clasificable | ✅ | `test_registrar_ticket_contract::test_registrar_when_no_clasificable_returns_pendiente`, `test_registro_ticket_integration` |
| C — Ciclo completo + cierre confirmado | ✅ | `test_flujo_completo_ticket_integration` |
| D — Auto-cierre | ✅ | `test_confirmar_cierre_service::test_cerrar_automaticamente_vencidos_cuando_pasaron_5_dias` |
| E — Modificación SLA | ✅ | `test_configurar_sla_service::test_modificar_when_valido_desactiva_y_crea_nueva` |
| F — Escalado automático SLA | ✅ | `test_monitoreo_sla_service::test_ejecutar_ciclo_when_excede_100_escala_a_supervisor` |
| G — Reapertura + renovación SLA | ✅ | `test_flujo_completo_ticket_integration`, `test_reabrir_ticket_service` |

## Frontend

| Artefacto | Ruta / archivo |
|-----------|----------------|
| TicketApiService | `frontend/src/app/modules/soporte-cliente/services/ticket-api.service.ts` |
| SlaConfigApiService | `frontend/src/app/modules/soporte-cliente/services/sla-config-api.service.ts` |
| Guards | `frontend/src/app/modules/soporte-cliente/guards/{cliente-soporte,agente-soporte,administrador-sla}.guard.ts` |
| Páginas | `frontend/src/app/modules/soporte-cliente/pages/{mis-tickets,cola-agente,detalle-ticket,configuracion-sla,dashboard-soporte}/*.page.ts` |
| Entradas sidebar | `frontend/src/app/shared/layout/nav-links.ts` (grupo "Soporte") — `core/sidebar/despacho-menu.config.ts` no se replicó por ser código muerto no consumido |

## Cobertura de tests (backend)

- 86 tests en `apps/soporte_cliente/` (repositorios, servicios, jobs, contratos API), todos verdes.
- Cobertura: `apps/soporte_cliente` + `core/repositories/soporte` = 94% líneas; `views.py` = 87% (umbral constitucional 75%); repositorios 94–100% (umbral 85%); servicios 83–100% (umbral 80%).
- Suite completa del backend (398 tests, excluyendo `apps/accidentes` y un archivo pre-existente rotos por WIP ajeno a este ciclo) pasa sin regresiones tras esta implementación.
- Frontend: `ng build` y `tsc --noEmit` sin errores; `ng test` no pudo levantar Chrome real en este entorno (mismo límite ya documentado en `despacho-inteligente`).

## Hallazgos y decisiones fuera del alcance original de tasks.md

- `AsignacionSLAService` requirió un repositorio de solo lectura nuevo, `core/repositories/soporte/suscripcion_repository.py` (lee `Fact_Suscripcion`), no listado explícitamente en tasks.md pero necesario para research.md Decision 5.
- `ResolverTicketService` y `TomarTicketService` incorporan validación de estado previo (RF-TIC-002 transiciones) no detallada originalmente en las tasks — se añadió para respetar la tabla de transiciones válidas de `spec.md` §9.
- El job CU-O96 corre vía `management/commands/run_monitoreo_sla_job.py` (loop `--interval`/`--once`), no vía consumer Kafka registrado en `apps.py` — mismo patrón que `despacho-inteligente`'s `run_timeout_despacho_job`.
