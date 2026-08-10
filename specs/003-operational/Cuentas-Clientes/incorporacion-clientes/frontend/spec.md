# Feature Specification: Incorporación de Clientes — Frontend

**Feature Branch / capa**: `incorporacion-clientes/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-ONB-*, RNF-ONB-*, CA-ONB-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Sesión Fase B — autorregistro público, aprobación Admin, wizard onboarding y guards de cuenta no activa.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Rutas de registro directo / config. plan+logo retiradas (numeración vieja "CU-O01/O12")? → A: Sin ruta FE; pantallas legacy responden 410 — no enlazar desde UI. Sin CU vigente en el catálogo (corregido 2026-08-08).
- Q: ¿Login bloqueado en Pendiente_Aprobación? → A: **No** (RN-ONB-011); la UI bloquea onboarding y módulos que exijan cliente activo vía guards, no el login.
- Q: ¿Logo en aprobación Admin? → A: Nunca en O16; logo solo en etapa `perfil_corporativo` del wizard (RN-ONB-012).

## User Scenarios & Testing

### US-FE-1 — Autorregistro público (P1)

Solicitante completa formulario CU-O09 sin JWT; recibe confirmación de solicitud en estado `Pendiente_Aprobación` (RF-ONB-001, RNF-ONB-001).

### US-FE-2 — Aprobar, rechazar o anular (P1)

Administrador lista solicitudes pendientes/rechazadas, decide aprobar/rechazar/anular rechazo con motivo cuando aplique (RF-ONB-002).

### US-FE-3 — Wizard onboarding digital (P1)

Admin local de cuenta `Activo` avanza etapas `cambio_password` → `perfil_corporativo` (con logo) → `preferencias`; progreso reanudable (RF-ONB-003, RF-ONB-004).

### US-FE-4 — Reenviar invitación (P2)

Admin o cliente reenvía credenciales temporales desde UI de solicitudes u onboarding (RF-ONB-005).

### US-FE-5 — Guards de elegibilidad (P1)

Guards impiden wizard si cuenta no está `Activo` o onboarding ya completado (RN-ONB-011, RN-ONB-008).

## Functional Requirements (UI)

- **FR-UI-001**: Página pública `/cuentas-clientes/incorporacion-clientes/autorregistro` — formulario O14, validación NIT/gmail, feedback 409 (RF-ONB-001).
- **FR-UI-002**: Listado Admin `/incorporacion-clientes/solicitudes` — filas `Pendiente_Aprobación` y `Rechazado` con acciones aprobar/rechazar/anular (RF-ONB-002).
- **FR-UI-003**: Aprobación **no** incluye campos plan ni logo — solo decisión y motivo de rechazo (RN-ONB-012, RF-ONB-002).
- **FR-UI-004**: Wizard `/incorporacion-clientes/:idcliente/onboarding` — stepper etapas canónicas con indicador de progreso (RF-ONB-003, RN-ONB-009).
- **FR-UI-005**: Etapa `perfil_corporativo` — upload/URL de logo gestionado por el cliente (RF-ONB-003, RN-ONB-012).
- **FR-UI-006**: Etapa `preferencias` — formulario umbrales/canales/zonas; al guardar refleja creación backend de preferencias (RF-ONB-003, RN-ONB-010).
- **FR-UI-007**: Reanudación: al entrar al wizard, posicionar en primera etapa pendiente según API progreso (RF-ONB-004, RN-ONB-005).
- **FR-UI-008**: CTA reenviar invitación en solicitudes Admin (RF-ONB-005, CU-O12).
- **FR-UI-009**: `AdminLocalOnboardingGuard`, `OnboardingPendienteGuard`, `OnboardingCompletadoGuard` en rutas wizard.
- **FR-UI-010**: `OnboardingFacadeService` centraliza estado UI del wizard sin lógica de dominio duplicada.
- **FR-UI-011**: Sin rutas ni enlaces a pantallas O01/O12 retiradas (RF-ONB-002b/c).
- **FR-UI-012**: Feedback de error 403 cuando cuenta no `Activo` intenta onboarding — mensaje orientado al usuario (RN-ONB-011).

## Out of Scope

- Cambiar OpenAPI, validaciones de servidor, Kafka/Pinot o RF/RN del backend.
- Asignación de plan de suscripción (Suscripciones-Facturación).
- Recordatorios SMTP automáticos (RNF-ONB-004) — solo backend/job.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — autorregistro, aprobación, wizard |
| Functional Suitability | FR-UI citan RF-ONB-* del backend |
| Security | Guards + roles Administrador/Cliente |
| Maintainability | Capa FE separada |
| Performance Efficiency | Autorregistro < 3 min interacción (RNF-ONB-001 UX) |
| Reliability / Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: Índice [`../incorporacion-clientes.md`](../incorporacion-clientes.md).
