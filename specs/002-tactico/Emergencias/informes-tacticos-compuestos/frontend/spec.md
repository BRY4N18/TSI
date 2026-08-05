# Feature Specification: Informes Tácticos Compuestos de Emergencias — Frontend

**Feature Branch / capa**: `informes-tacticos-compuestos/frontend`

**Created**: 2026-08-01

**Status**: Draft (stub — se completa después de cerrar `../backend/spec.md`)

**Depends-on**: `../backend/spec.md` (3 endpoints de lectura materializada, RF-001..RF-010) y `../../informes-tacticos-simples/frontend/spec.md` (los 3 workpanels donde se integran estas tarjetas). Esta capa **MUST NOT** redefinir DAGs, esquema de ClickHouse ni contratos REST del backend.

**Input**: User description: "Integrar los 3 informes compuestos (pérdida de señal, índice de calidad consolidado, rendimiento por proveedor) como tarjetas adicionales dentro de los workpanels de Registro/Despacho/Seguimiento ya definidos en informes-tacticos-simples/frontend, visibles solo para el rol Supervisor."

## Clarifications

<!-- Session notes for Interaction Capability only -->

Ninguna todavía — este stub se completa con `/speckit-clarify` y `/speckit-plan` una vez el backend de este módulo esté implementado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver la tarjeta de pérdida de señal en el workpanel de Seguimiento (Priority: P1)

Un Supervisor de Emergencias abre el workpanel de Seguimiento y Cierre de Casos y ve, además de las 3 tarjetas simples ya existentes, una tarjeta con el listado/porcentaje de misiones con pérdida de señal GPS, indicando cuándo se actualizó por última vez (frescura del dato batch).

**Why this priority**: Es el informe compuesto de mayor prioridad en el backend (P1) — el caso de uso testigo de Airflow.

**Independent Test**: Con el backend de este informe implementado, se puede verificar que la tarjeta aparece en el workpanel de Seguimiento solo para el rol Supervisor, con la marca de frescura visible.

**Acceptance Scenarios**:

1. **Given** el DAG de pérdida de señal ya procesó el período visible, **When** un Supervisor abre el workpanel de Seguimiento, **Then** la tarjeta muestra el listado/porcentaje junto con la fecha de última actualización.
2. **Given** un Operador (no Supervisor) abre el mismo workpanel, **When** la pantalla carga, **Then** la tarjeta de pérdida de señal no se muestra (o se muestra bloqueada), reflejando FR-009 del backend.

---

### User Story 2 - Ver la tarjeta del índice de calidad en el workpanel de Registro (Priority: P2)

Un Supervisor abre el workpanel de Registro de Accidente y ve una tarjeta con el índice consolidado de calidad del histórico y su evolución en el tiempo (no solo el valor actual).

**Why this priority**: Segunda prioridad del backend — depende de que los 4 indicadores base ya existan en el workpanel simple.

**Independent Test**: Con el backend de este informe implementado, se puede verificar que la tarjeta muestra una serie temporal, no un único valor.

**Acceptance Scenarios**:

1. **Given** existen valores del índice para varios períodos, **When** el Supervisor abre la tarjeta, **Then** ve la evolución del índice, no solo el último valor.

---

### User Story 3 - Ver la tarjeta de rendimiento por proveedor en el workpanel de Despacho (Priority: P2)

Un Supervisor abre el workpanel de Despacho Inteligente y ve una tarjeta con el rendimiento de despacho agrupado por proveedor de unidades.

**Why this priority**: Misma prioridad que la historia anterior en el backend — completa la integración de los 3 informes compuestos en sus workpanels respectivos.

**Independent Test**: Con el backend de este informe implementado, se puede verificar que la tarjeta distingue correctamente entre proveedores.

**Acceptance Scenarios**:

1. **Given** existen dos o más proveedores con métricas distintas, **When** el Supervisor abre la tarjeta, **Then** ve el desglose por proveedor, no un agregado único.

## Functional Requirements (UI)

- **FR-UI-001**: Las 3 tarjetas de informes compuestos MUST integrarse dentro de los workpanels ya existentes de `informes-tacticos-simples/frontend` (una por módulo), no como pantallas nuevas separadas.
- **FR-UI-002**: Cada tarjeta compuesta MUST mostrar visiblemente cuándo se actualizó por última vez el dato (frescura batch), distinguiéndose de las tarjetas simples (que son de consulta en tiempo real).
- **FR-UI-003**: Las 3 tarjetas compuestas MUST ser visibles solo para el rol Supervisor, ocultas o bloqueadas para el rol Operador, reutilizando el RBAC ya existente en el frontend.
- **FR-UI-004**: Cuando un período solicitado no ha sido procesado todavía por el DAG correspondiente (FR-008 del backend), la tarjeta MUST mostrar un estado explícito de "aún no calculado para este período", distinto del estado "sin datos" de las tarjetas simples.

## Out of Scope

- Cambiar DAGs, esquema de ClickHouse o RF/RN del backend.
- Disparar manualmente una re-ejecución de un DAG desde el frontend — la frecuencia de actualización es responsabilidad exclusiva de Airflow (ver Assumptions del backend).
- Cualquier informe simple (Pinot directo) — pertenece a `../../informes-tacticos-simples/`, no a este módulo.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Distinción visual clara entre dato en tiempo real (tarjetas simples) y dato batch con frescura declarada (tarjetas compuestas), para que un Supervisor no confunda ambos |
| Functional Suitability | Cita RF-001..RF-010 del backend (Depends-on) |
| Security | Visibilidad restringida a Supervisor (FR-UI-003), reutiliza guards/RBAC existentes |
| Maintainability | Capa FE separada de `backend/`; cada tarjeta compuesta es una adición aislada a un workpanel ya existente, no una reescritura |
| Reliability / Performance / Compatibility / Flexibility / Safety | N/A en este nivel — heredan lo ya declarado en `../backend/spec.md` y en `../../infraestructura/spec.md` |

**Traceability**: Índice del módulo `../informes-tacticos-compuestos.md` en la carpeta padre.
