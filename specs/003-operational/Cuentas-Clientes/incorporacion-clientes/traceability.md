# Trazabilidad — Incorporación de Clientes

| CU | RF/RNF | CA | Task IDs | Estado |
|----|--------|-----|----------|--------|
| O01 | RF-ONB-001 | CA-ONB-001 | T018–T029 | ✅ Cumplido |
| O12 | RF-ONB-002 | CA-ONB-002 | T030–T039 | ✅ Cumplido |
| O02/O09 | RF-ONB-003, RF-ONB-004 | CA-ONB-003–005 | T040–T055 | ✅ Cumplido |
| O08 | RF-ONB-005 | CA-ONB-006 | T056–T062 | ✅ Cumplido |
| Recordatorios | RNF-ONB-004, RN-ONB-004 | CA-ONB-007 | T063–T067 | ✅ Cumplido |

## Criterios de aceptación

| CA | Descripción | Validación |
|----|-------------|------------|
| CA-ONB-001 | Registro de cuenta con admin local, estado Activo, NIT único | `test_registro_cuenta_contract.py`, `test_registro_cuenta_service.py`, frontend `registro.page.ts` |
| CA-ONB-002 | Configuración plan/logo, estado_onboarding Pendiente | `test_configuracion_cuenta_contract.py`, `configuracion.page.ts` |
| CA-ONB-003 | Wizard con etapas canónicas y reanudación | `test_onboarding_service.py`, `onboarding-wizard.page.ts` |
| CA-ONB-004 | Creación Dim_Preferencias_Cliente en etapa preferencias | `test_onboarding_service.py` |
| CA-ONB-005 | estado_onboarding Completado al finalizar | `test_onboarding_etapas_contract.py` |
| CA-ONB-006 | Reenvío invitación con credencial temporal | `test_invitacion_service.py`, `configuracion.page.ts` |
| CA-ONB-007 | Recordatorios semanales desde día 30 | `test_onboarding_reminder_service.py`, `send_onboarding_reminders` command |

## Mapeo RF/RNF → Tasks

| ID | Descripción | Tasks |
|----|-------------|-------|
| RF-ONB-001 | Alta de cuenta B2B | T018–T029 |
| RF-ONB-002 | Configuración inicial | T030–T039 |
| RF-ONB-003 | Onboarding digital por etapas | T040–T055 |
| RF-ONB-004 | Consulta de progreso | T040, T047–T048 |
| RF-ONB-005 | Reenvío de invitación | T056–T062 |
| RN-ONB-004 | Recordatorios automáticos | T063–T067 |
| RN-ONB-007 | Membresía vía admin_local_id | T015–T016 |
