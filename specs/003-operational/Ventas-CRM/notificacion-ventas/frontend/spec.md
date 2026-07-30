# Feature Specification: Notificación de Ventas — Frontend

**Feature Branch / capa**: `notificacion-ventas/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-NV-*, RNF-NV-*, CA-NV-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Depends-on módulo**: `commercial-pipeline-prospects` (grant demo en registro prospecto).

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Autenticación demo? → A: Sin JWT usuario; `DemoSessionInterceptor` envía token de sesión demo en interacciones (RF-NV-001, RN-NV-005).
- Q: ¿Estados vacíos listado notificaciones? → A: Cumple RNF-NV-005 — skeleton, vacío accionable, error+retry.

## User Scenarios & Testing

### US-FE-1 — Sesión demo interactiva (P1)

Prospecto canjea grant → navega demo → eventos registrados hasta expiración (RF-NV-001).

### US-FE-2 — Consultar notificaciones (P1)

Gerente ve historial propio; Admin ve cualquier gerente (RF-NV-004).

### US-FE-3 — Resume sesión demo (P2)

Mismo grant reemite token si demo aún activa — sin nuevo inicio_sesion en UI (RF-NV-001 resume).

## Functional Requirements (UI)

- **FR-UI-001**: Página `demo-interactiva` — form grant + idprospecto; estados error grant inválido/expirado (RF-NV-001).
- **FR-UI-002**: Tras canje exitoso, UI demo emite eventos click/tiempo_seccion vía API (RF-NV-001).
- **FR-UI-003**: `DemoSessionInterceptor` adjunta token demo en requests de interacción (RN-NV-005).
- **FR-UI-004**: `DemoApiService` — start/resume/interact según contrato backend.
- **FR-UI-005**: Página `notificaciones-ventas` — listado paginado cursor (RF-NV-004).
- **FR-UI-006**: Estados async RNF-NV-005: skeleton, vacío accionable, error con reintento.
- **FR-UI-007**: Ruta protegida `admin-o-gerente-crm.guard` en `/ventas-crm/notificaciones`.
- **FR-UI-008**: `NotificacionApiService` — consulta historial filtrado por RBAC.
- **FR-UI-009**: Demo pública en `/ventas-crm/demo` — sin JWT usuario (RF-NV-001).

## Out of Scope

- Configuración de reglas MVP o canales (backend/Sistema).
- Envío real Slack (fuera MVP backend).
- Pipeline comercial (`commercial-pipeline-prospects`).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — demo + bandeja notificaciones |
| Functional Suitability | FR-UI citan RF-NV-* |
| Security | Token demo acotado; listado con JWT |
| Maintainability | Comparte módulo `ventas-crm` |
| Performance Efficiency | RNF-NV-002 heredado (job backend) |

**Traceability**: [`../notificacion-ventas.md`](../notificacion-ventas.md).
