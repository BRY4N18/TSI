# Trazabilidad — Incorporación de Clientes

Numeración de CU corregida 2026-08-08 al catálogo vigente (`TSI-Catalogo-CU-RF-RNF.md`); ver `spec.md` Clarifications para el mapeo desde la numeración previa. "Registro directo" y "config. plan+logo" quedan sin CU vigente (capacidades retiradas del catálogo viejo).

| CU | RF/RNF | CA | Task IDs | Estado |
|----|--------|-----|----------|--------|
| — (registro directo, retirado) | RF-ONB-002c | CA-ONB-010 | T097 | ⛔ Retirado (410) |
| — (config. plan+logo, retirado) | RF-ONB-002b | CA-ONB-010 | T098 | ⛔ Retirado (410) |
| O09 | RF-ONB-001 | CA-ONB-001 | T073–T084 | ✅ |
| O10 | RF-ONB-002, RN-ONB-013 | CA-ONB-002, CA-ONB-008, CA-ONB-009 | T085–T090, T099–T102 | ✅ + anular + email |
| O11 (incluye RF-O11.2, guardar progreso) | RF-ONB-003, RF-ONB-004 | CA-ONB-003–005 | T040–T055, T091–T095 | ✅ gate Activo |
| O12 | RF-ONB-005 | CA-ONB-006 | T056–T062, T103 | ✅ UI solicitudes + wizard |
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
| CA-ONB-009 | Soft-anular + nuevo O09 mismo NIT | `test_anular_rechazo_*` |
| CA-ONB-010 | Registro directo / config. plan+logo → 410 (sin CU vigente) | `test_registro_cuenta_contract`, `test_configuracion_cuenta_contract` |
| CA-ONB-011 | UI design-system + Toast/íconos/44px + modal rechazo + “en revisión” | `*.page.html` + `NotificationService` |

## Flujo canónico (corregido 2026-08-08)

`CU-O09` (autorregistro) → `Pendiente_Aprobación` → `CU-O10` (aprobar | rechazar → anular) → `Activo` + onboarding (`CU-O11`, logo lo carga el cliente).

## Mapeo RF/RNF → Tasks

| ID | Descripción | Tasks |
|----|-------------|-------|
| RF-ONB-001 | Autorregistro (CU-O09) | T073–T084 |
| RF-ONB-002 | Aprobación / anular / email (CU-O10) | T085–T090, T099–T102 |
| RF-ONB-002b/c | Retiro registro directo / config. plan+logo (sin CU vigente) | T097–T098 |
| RF-ONB-003 | Onboarding (CU-O11) | T040–T055, T091–T094 |
| RF-ONB-005 | Reenvío invitación (CU-O12) | T056–T062, T103 |
| RN-ONB-011 | Gate Activo | T091–T092 |
| RN-ONB-013 | Soft-anular | T099–T100 |
