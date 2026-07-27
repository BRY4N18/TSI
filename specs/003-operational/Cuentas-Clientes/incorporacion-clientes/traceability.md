# Trazabilidad — Incorporación de Clientes

| CU | RF/RNF | CA | Task IDs | Estado |
|----|--------|-----|----------|--------|
| O01 | RF-ONB-002c | CA-ONB-010 | T097 | ⛔ Retirado (410) |
| O12 | RF-ONB-002b | CA-ONB-010 | T098 | ⛔ Retirado (410) |
| O14 | RF-ONB-001 | CA-ONB-001 | T073–T084 | ✅ |
| O16 | RF-ONB-002, RN-ONB-013 | CA-ONB-002, CA-ONB-008, CA-ONB-009 | T085–T090, T099–T102 | ✅ + anular + email |
| O02/O09 | RF-ONB-003, RF-ONB-004 | CA-ONB-003–005 | T040–T055, T091–T095 | ✅ gate Activo |
| O08 | RF-ONB-005 | CA-ONB-006 | T056–T062, T103 | ✅ UI solicitudes + wizard |
| Recordatorios | RNF-ONB-004 | CA-ONB-007 | T063–T067 | ✅ |

## Criterios de aceptación

| CA | Descripción | Validación |
|----|-------------|------------|
| CA-ONB-001 | Autorregistro → `Pendiente_Aprobación` | `test_autorregistro_proveedor_*` |
| CA-ONB-002 | Aprobar/rechazar + email; sin logo/plan | `test_aprobacion_*`, `test_onboarding_notificacion_*` |
| CA-ONB-003 | Wizard solo Activo; logo en perfil | `test_onboarding_*`, wizard FE |
| CA-ONB-004 | Preferencias → `Dim_Preferencias_Cliente` | `test_onboarding_service.py` |
| CA-ONB-005 | Completado al finalizar | `test_onboarding_etapas_contract.py` |
| CA-ONB-006 | Reenvío invitación | `test_invitacion_*`; UI solicitudes/wizard |
| CA-ONB-007 | Recordatorios post-aprobación | `test_onboarding_reminder_*` |
| CA-ONB-008 | Pendiente/Rechazado sin onboarding/alta | `test_onboarding_requiere_activo_*` |
| CA-ONB-009 | Soft-anular + nuevo O14 mismo NIT | `test_anular_rechazo_*` |
| CA-ONB-010 | O01/O12 → 410 | `test_registro_cuenta_contract`, `test_configuracion_cuenta_contract` |
| CA-ONB-011 | UI design-system + Toast/íconos/44px + modal rechazo + “en revisión” | `*.page.html` + `NotificationService` |

## Flujo canónico (2026-07-25)

`CU-O14` → `Pendiente_Aprobación` → `CU-O16` (aprobar | rechazar → anular) → `Activo` + onboarding → `CU-O02` (logo cliente).

## Mapeo RF/RNF → Tasks

| ID | Descripción | Tasks |
|----|-------------|-------|
| RF-ONB-001 | Autorregistro (O14) | T073–T084 |
| RF-ONB-002 | Aprobación / anular / email (O16) | T085–T090, T099–T102 |
| RF-ONB-002b/c | Retiro O12/O01 | T097–T098 |
| RF-ONB-003 | Onboarding | T040–T055, T091–T094 |
| RF-ONB-005 | Reenvío invitación | T056–T062, T103 |
| RN-ONB-011 | Gate Activo | T091–T092 |
| RN-ONB-013 | Soft-anular | T099–T100 |
