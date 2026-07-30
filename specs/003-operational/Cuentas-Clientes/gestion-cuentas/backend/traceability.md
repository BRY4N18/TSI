# Traceability — Gestión de Cuenta de Cliente

| CU | RF/RNF/CA | Task IDs | Status |
|----|-----------|----------|--------|
| CU-O03 | RF-CTA-001, RF-CTA-002, CA-CTA-001 | T017–T036 | ✓ Validated |
| CU-O10 | RF-CTA-003, RF-CTA-005, CA-CTA-002, CA-CTA-006 | T037–T048 | ✓ Validated |
| CU-O11 | RF-CTA-004, RF-CTA-005, CA-CTA-003..006 | T049–T061 | ✓ Validated |
| Transversal | RNF-CTA-002, RNF-CTA-003 | T006–T016, T062–T066 | ✓ Validated |

## Acceptance criteria mapping

- **CA-CTA-001**: Perfil/preferencias editables + logs — `CuentaPerfilService`, `CuentaPreferenciasService`, `AuditService.log_cuenta_field_change`
- **CA-CTA-002**: Transferencia inmediata — `TransferenciaPropiedadService`
- **CA-CTA-003**: Baja lógica — `BajaCuentaService` + `ClienteRepository.update(estado)`
- **CA-CTA-004**: Sesiones expulsadas — `SessionRepository.expel_all_by_cliente`
- **CA-CTA-005**: Datos históricos preservados — solo Kafka update, sin DELETE
- **CA-CTA-006**: SMTP transferencia/baja — `CuentaNotificacionService` + `log_smtp_failure`
