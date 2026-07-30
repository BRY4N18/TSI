# Feature Specification: Registro de Accidentes — Frontend (UI Operador)

**Feature Branch / capa**: `registro-accidente/frontend`  
**Created**: 2026-07-30  
**Status**: Active (piloto split BE/FE)  
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-REG-*, RNF-REG-*, CA-REG-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Clarificaciones Session 2026-07-30 (Interaction Capability): lista/workpanel Detalles vs Editar; ID sin link; paneles adyacentes en `mode=view`; descartar borrador local con confirmación de usuario.

## Clarifications

### Session 2026-07-30

- Q: ¿Patrón de Acciones en tabla? → A: Ojo = Detalles; lápiz = Editar. Íconos ≥44×44 px, `aria-label` y tooltip. Navegación a workpanel (no master-detail).
- Q: ¿Títulos y permisos de modo? → A: Detalles = solo lectura, sin Guardar; Editar = campos complementarios + Guardar arriba.
- Q: ¿ID en lista es enlace? → A: No — texto plano; apertura solo vía Acciones.
- Q: ¿En Detalles siguen Descartar/Escalar? → A: Sí (según estado/rol).
- Q: ¿Galería y datos del siniestro en Detalles? → A: Solo consulta + páginas destino `?mode=view`.
- Q: ¿Descartar borrador local (RNF-REG-006 UI)? → A: CTA «Descartar borrador» + confirmación «¿Descartar el borrador y empezar de nuevo?» (sin términos técnicos).

## User Scenarios & Testing

### US-FE-1 — Abrir caso (P1)

Lista con ID texto; ojo → Detalles; lápiz → Editar (`?focus=edit`).

### US-FE-2 — Guardar solo en Editar (P1)

CTA Guardar arriba solo en modo Editar; confirmación/error según design-system.

### US-FE-3 — Paneles adyacentes (P1)

Desde Detalles: «Ver galería» / «Ver datos del siniestro» con `mode=view`. Desde Editar: CTAs de completar/captura según rol.

### US-FE-4 — Borrador local (P1)

Banner de restauración + Descartar borrador con confirmación de usuario; limpia storage y resetea form.

### US-FE-5 — Selección en lista (P2)

Fila/card del último caso con acento de marca; severidad/estado solo en badge.

## Functional Requirements (UI)

- **FR-UI-001**: ID en lista = texto plano (sin link).
- **FR-UI-002**: Ojo → modo Detalles; lápiz → modo Editar (`focus=edit`).
- **FR-UI-003**: Detalles: sin Guardar; campos Impacto no editables; títulos intuitivos.
- **FR-UI-004**: Editar: Guardar cambios arriba; feedback éxito/error.
- **FR-UI-005**: Detalles: enlaces galería/siniestro en consulta + `mode=view` en destino.
- **FR-UI-006**: Editar: CTAs completar/captura según rol (dueño evidencia = `evidencia-unidad`).
- **FR-UI-007**: CTA Nuevo registro arriba → flujo CU-O21 existente.
- **FR-UI-008**: Selección de fila/card último caso (acento de marca).
- **FR-UI-009**: Banner borrador + Descartar borrador con confirmación de usuario (RNF-REG-006 UI).
- **FR-UI-010**: Guards/roles según backend; sin ampliar datos editables más allá de RF-REG-005 backend.

## Out of Scope

- Cambiar OpenAPI, validaciones de servidor, Kafka/Pinot.
- Rediseñar captura en sitio (clima/físicos/conductores) — dueño `evidencia-unidad`.

## ISO/IEC 25010 — Justificación

| Characteristic | Treatment |
|---|---|
| Functional Suitability | FR-UI citan RF-REG-005 / RNF-REG-006 del backend |
| Interaction Capability | Núcleo de esta capa (Principio IV) |
| Security | Reutiliza guards/RBAC del módulo padre |
| Maintainability | Separada de `backend/` para cambios UX sin tocar dominio |
| Safety / Reliability / Performance / Compatibility / Flexibility | N/A o heredadas del backend |

**Traceability**: Índice módulo [`../registro-accidente.md`](../registro-accidente.md).
