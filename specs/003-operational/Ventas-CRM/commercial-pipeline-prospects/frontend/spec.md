# Feature Specification: Pipeline Comercial y Prospectos — Frontend

**Feature Branch / capa**: `commercial-pipeline-prospects/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-CPP-*, RNF-CPP-*, CA-CPP-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Catálogo planes público duplicado con Suscripciones? → A: RF-CPP-000 lee mismo catálogo; ruta pública `/ventas-crm/planes` es entrada comercial del embudo, sin JWT.
- Q: ¿Conflictos 409 en pipeline? → A: UI muestra mensaje de conflicto optimista y CTA «Refrescar» (RF-CPP-004 clarificación 2026-07-25).
- Q: ¿Retroceso de etapa en board? → A: No permitido en UI — solo avance adyacente + Perdido.

## User Scenarios & Testing

### US-FE-1 — Consultar catálogo público (P1)

Visitante ve planes activos en solo lectura antes de registrarse (RF-CPP-000).

### US-FE-2 — Registro de prospecto (P1)

Formulario público inbound crea prospecto y muestra grant demo si aplica (RF-CPP-001).

### US-FE-3 — Operar pipeline asignado (P1)

Gerente ve listado/detalle/board solo de prospectos propios; Admin ve todos (RF-CPP-008, matriz RBAC).

### US-FE-4 — Transiciones y pérdida (P1)

Board permite avanzar etapa adyacente o marcar Perdido con motivo; maneja 409 (RF-CPP-004, RF-CPP-005).

### US-FE-5 — Entrada directa (P2)

Administrador crea cliente sin prospecto previo (RF-CPP-007).

### US-FE-6 — Conversión a cliente (P1)

Desde detalle, acción convertir con validación NIT (RF-CPP-006).

## Functional Requirements (UI)

- **FR-UI-001**: Página pública `catalogo-planes` — skeleton/vacío/error+retry; CTA a registro (RF-CPP-000).
- **FR-UI-002**: Página `registro-publico` — formulario O116; estados loading/error (RF-CPP-001).
- **FR-UI-003**: Rutas públicas `/ventas-crm/planes` y `/ventas-crm/registro` sin JWT en `app.routes.ts`.
- **FR-UI-004**: `listado-prospectos` — skeleton/vacío/error; filtro implícito por rol gerente (RF-CPP-008).
- **FR-UI-005**: `detalle-prospecto` — acciones asignación, conversión, transición según dueño (RF-CPP-003, RF-CPP-006).
- **FR-UI-006**: `pipeline-board` — columnas etapas; drag o acciones adyacentes; sin retroceso (RF-CPP-004).
- **FR-UI-007**: Modal/motivo obligatorio al marcar `Perdido` (RF-CPP-005).
- **FR-UI-008**: Manejo HTTP 409 — toast + refrescar estado prospecto (optimistic check backend).
- **FR-UI-009**: `entrada-directa` — solo Admin; formulario RF-CPP-007.
- **FR-UI-010**: Guards `gerente-ventas`, `gerente-cuentas-publicas`, `admin-o-gerente-crm`, `admin-crm`.
- **FR-UI-011**: `ProspectoApiService`, `PipelineApiService`, `ConversionApiService`, `PlanesApiService`.
- **FR-UI-012**: Primera asignación huérfano: acción visible solo Admin (RF-CPP-003 clarificación).
- **FR-UI-013**: Listado Admin sin filtro por `idusuario`; gerente solo asignados.
- **FR-UI-014**: Navegación lazy `ventas-crm.routes.ts` — redirect default a prospectos autenticados.

## Out of Scope

- Demo interactiva y notificaciones (`notificacion-ventas`).
- Escritura en catálogo `Dim_Plan` (Suscripciones-Facturación).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — embudo comercial |
| Functional Suitability | FR-UI citan RF-CPP-* |
| Security | Guards CRM + rutas públicas acotadas |
| Maintainability | Capa FE separada |
| Performance / Reliability / Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: [`../commercial-pipeline-prospects.md`](../commercial-pipeline-prospects.md).
