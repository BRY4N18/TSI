# Feature Specification: Gestión de Cuentas — Frontend

**Feature Branch / capa**: `gestion-cuentas/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-CTA-*, RNF-CTA-*, CA-CTA-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Campos solo lectura en perfil? → A: `tipo` y `nit_identificacion` deshabilitados en formulario (RN-CTA-001).
- Q: ¿Confirmación transferencia? → A: Diálogo de confirmación antes de PATCH inmediato — sin flujo de aceptación del nuevo admin (RN-CTA-002).
- Q: ¿Baja de cuenta? → A: Solo Administrador; motivo opcional en UI, persistido solo en logs backend (RF-CTA-004).

## User Scenarios & Testing

### US-FE-1 — Perfil corporativo (P1)

Cliente o Admin editan `razon_social`, `nombre`, `logo_url`; tipo/NIT solo lectura (RF-CTA-001).

### US-FE-2 — Preferencias operativas (P1)

Formulario de umbrales, canales, SMS, zonas, destinatarios, frecuencia y formato (RF-CTA-002).

### US-FE-3 — Transferir propiedad (P1)

Admin local selecciona nuevo responsable de la misma cuenta y confirma transferencia inmediata (RF-CTA-003).

### US-FE-4 — Dar de baja cuenta (P2)

Administrador ejecuta baja lógica con confirmación destructiva y motivo opcional (RF-CTA-004).

## Functional Requirements (UI)

- **FR-UI-001**: Hub Admin `/gestion-cuenta` lista cuentas accesibles (scope Administrador).
- **FR-UI-002**: Página `perfil` — edición campos RF-CTA-001; `tipo`/`nit` disabled (RN-CTA-001).
- **FR-UI-003**: `CuentaClienteFacadeService` — flujo upload logo + patch perfil (RF-CTA-001).
- **FR-UI-004**: Página `preferencias` — todos los campos editables excepto `activo` (RF-CTA-002).
- **FR-UI-005**: Página `transferencia` — selector usuarios misma cuenta + confirmación (RF-CTA-003, RN-CTA-002).
- **FR-UI-006**: Página `baja` — solo rol Administrador; motivo opcional; confirmación fuerte (RF-CTA-004).
- **FR-UI-007**: `CuentaScopeGuard` — usuario solo accede a `:idcliente` autorizado (RNF-CTA-002).
- **FR-UI-008**: `CuentaActivaGuard` — bloquea gestión en cuentas `Dado de baja` (RN-CTA-003).
- **FR-UI-009**: `AdminLocalGuard` en ruta transferencia — solo admin local actual (RF-CTA-003).
- **FR-UI-010**: Toast/feedback éxito-error tras guardar; sin notificación email en cambios O03 (RF-CTA-005).

## Out of Scope

- Plan de suscripción, facturación, métricas de uso (Suscripciones-Facturación).
- Reactivación de cuenta dada de baja (RN-CTA-004).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — portal autogestión cuenta |
| Functional Suitability | FR-UI citan RF-CTA-* |
| Security | Guards scope + rol |
| Maintainability | Capa FE separada |
| Reliability / Performance / Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: [`../gestion-cuentas.md`](../gestion-cuentas.md).
