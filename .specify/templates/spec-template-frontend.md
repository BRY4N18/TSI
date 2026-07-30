# Feature Specification: [FEATURE NAME] — Frontend

**Feature Branch / capa**: `[###-feature-name]/frontend`

**Created**: [DATE]

**Status**: Draft

**Depends-on**: `../backend/spec.md` (dominio, RF/RN/CA, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: User description: "$ARGUMENTS"

## Clarifications

<!-- Session notes for Interaction Capability only -->

## User Scenarios & Testing *(mandatory)*

### User Story 1 - [Brief UI journey] (Priority: P1)

[Describe the interaction in plain language]

**Why this priority**: [Value under operator pressure / Principle IV]

**Independent Test**: [How to test this UI slice alone]

**Acceptance Scenarios**:

1. **Given** [state], **When** [action], **Then** [UI outcome]

## Functional Requirements (UI)

- **FR-UI-001**: [Measurable interaction requirement]
- **FR-UI-002**: [… ]

## Out of Scope

- Cambiar OpenAPI, validaciones de servidor, Kafka/Pinot o RF/RN del backend.
- [Other UI out of scope]

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo de esta capa |
| Functional Suitability | Cita RF/CA del backend (Depends-on) |
| Security | Reutiliza guards/RBAC existentes |
| Maintainability | Capa FE separada de `backend/` |
| Reliability / Performance / Compatibility / Flexibility / Safety | N/A o heredadas — justificar |

**Traceability**: Índice del módulo `{module-name}.md` en la carpeta padre.
