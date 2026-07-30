# Feature Specification: Suscripciones y Facturación — Frontend

**Feature Branch / capa**: `subscriptions-and-billing/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-SUSF-*, RNF-SUSF-*, CA-SUSF-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Quién edita catálogo planes en UI? → A: Solo rol `DirectorEstrategia` — Admin ya no CRUD planes (RF-SUSF-001 enmienda 2026-07-30).
- Q: ¿Home billing por rol? → A: Redirect en `suscripcionesHomeRedirect` — Proveedor → mi-suscripcion; Admin → aprobaciones; Director → catálogo.

## User Scenarios & Testing

### US-FE-1 — Portal Proveedor (P1)

Proveedor gestiona suscripción, método de pago, historial y cambio de plan sobre su `idcliente` (RF-SUSF-010, RF-SUSF-002, RF-SUSF-006, RF-SUSF-003).

### US-FE-2 — Catálogo planes Director (P1)

Director Estrategia crea/edita/desactiva planes en UI admin (RF-SUSF-001).

### US-FE-3 — Aprobaciones downgrade Admin (P1)

Administrador resuelve solicitudes pendientes de downgrade (RF-SUSF-003).

### US-FE-4 — Acceso suspendido (P1)

UI refleja RN-SUSF-017 — mensaje cuando suscripción Suspendida bloquea acciones operativas.

## Functional Requirements (UI)

- **FR-UI-001**: Shell `billing-shell.page` con tabs/nav por rol.
- **FR-UI-002**: `mi-suscripcion` — alta inicial RF-SUSF-010, estado Activa/Suspendida/Cancelada.
- **FR-UI-003**: `metodos-pago` — alta/reemplazo tokenizado; postcondición reactivación automática visible (RF-SUSF-002, RN-SUSF-021).
- **FR-UI-004**: `historial-facturas` — orden `fecha_emision` desc (RF-SUSF-006).
- **FR-UI-005**: `cambio-plan` — upgrade inmediato / downgrade solicitud Pendiente (RF-SUSF-003).
- **FR-UI-006**: `catalogo-planes` — listado; CRUD solo Director en rutas `planes/nuevo` y `planes/:id/editar` (RF-SUSF-001).
- **FR-UI-007**: `aprobaciones-downgrade` — bandeja Admin (RF-SUSF-003).
- **FR-UI-008**: Guards `proveedor-billing`, `admin-billing`, `director-estrategia-billing`.
- **FR-UI-009**: `suscripcionesHomeRedirect` — landing por rol al entrar a `/suscripciones`.
- **FR-UI-010**: Servicios API: suscripcion, plan, metodo-pago, factura — tipos desde OpenAPI.
- **FR-UI-011**: CTA «Reintentar cobro» en factura Fallida cuando RN-SUSF-017 lo permite (RF-SUSF-007 UX).
- **FR-UI-012**: Estados async estándar design-system en todas las pages billing.
- **FR-UI-013**: Proveedor nunca selecciona otro `idcliente` — scope implícito del token (RNF-SUSF-002).

## Out of Scope

- Pasarela real (simulador backend v1).
- Pricing dinámico por región.
- Jobs batch (Sistema).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — portal billing |
| Functional Suitability | FR-UI citan RF-SUSF-* |
| Security | Guards por rol + scope cliente |
| Maintainability | Capa FE separada |
| Reliability | RN-SUSF-017 reflejada en UX de bloqueo |

**Traceability**: [`../subscriptions-and-billing.md`](../subscriptions-and-billing.md).
