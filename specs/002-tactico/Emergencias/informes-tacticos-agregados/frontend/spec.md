# Feature Specification: Informes Tácticos Simples de Emergencias — Frontend

**Feature Branch / capa**: `informes-tacticos-agregados/frontend`

**Created**: 2026-08-01

**Status**: Draft (stub — se completa después de cerrar `../backend/spec.md`)

**Depends-on**: `../backend/spec.md` (16 endpoints de agregación, RF-001..RF-009). Esta capa **MUST NOT** redefinir cálculos, filtros ni contratos REST del backend.

**Input**: User description: "3 workpanels para el departamento de Emergencias — uno por módulo (Registro de Accidente, Despacho Inteligente, Seguimiento y Cierre de Casos) — cada uno mostrando las tarjetas/gráficas de los informes definidos en ../backend/spec.md, filtrables por período."

## Clarifications

<!-- Session notes for Interaction Capability only -->

Ninguna todavía — este stub se completa con `/speckit-clarify` y `/speckit-plan` una vez el backend esté implementado, siguiendo el orden de trabajo documentado en `../informes-tacticos-agregados.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el workpanel de Registro de Accidente (Priority: P1)

Un Operador o Supervisor abre el workpanel de Registro de Accidente y ve, en tarjetas/gráficas, los 7 informes de esa historia del backend (volumen, severidad, zona, completitud, descarte/fusión, ranking de ubicaciones, impacto humano), con un selector de período que refresca todas las tarjetas a la vez.

**Why this priority**: Es el primer workpanel entregable en cuanto el backend de Registro esté listo (US1 del backend es también P1).

**Independent Test**: Con el backend de Registro implementado, se puede cargar este workpanel de forma aislada y verificar que las 7 tarjetas muestran datos coherentes con lo devuelto por sus endpoints respectivos.

**Acceptance Scenarios**:

1. **Given** el backend de Registro tiene datos para el período por defecto, **When** el Operador abre el workpanel, **Then** las 7 tarjetas cargan sin requerir configuración adicional.
2. **Given** el Operador cambia el selector de período, **When** confirma el cambio, **Then** las 7 tarjetas se actualizan con el nuevo rango.

---

### User Story 2 - Ver el workpanel de Despacho Inteligente (Priority: P1)

Un Operador o Supervisor abre el workpanel de Despacho Inteligente y ve los 6 informes de esa historia del backend (asignación automática/manual, tiempos de respuesta, rechazos, carga por unidad, ratio demanda/capacidad), con los mismos controles de período (y corte por condado donde el informe lo soporte).

**Why this priority**: Igual prioridad que el workpanel de Registro — ambos módulos son P1 en el backend.

**Independent Test**: Con el backend de Despacho implementado, se puede cargar este workpanel de forma aislada.

**Acceptance Scenarios**:

1. **Given** el backend de Despacho tiene datos, **When** el Supervisor abre el workpanel, **Then** las 6 tarjetas cargan correctamente.
2. **Given** el informe de ratio demanda/capacidad soporta corte por condado, **When** el Supervisor selecciona un condado, **Then** solo esa tarjeta se recorta por condado sin afectar las demás.

---

### User Story 3 - Ver el workpanel de Seguimiento y Cierre de Casos (Priority: P2)

Un Operador o Supervisor abre el workpanel de Seguimiento y ve los 3 informes de esa historia del backend (tiempo asignado→cerrado, % cierres forzados, % abortos/pérdidas).

**Why this priority**: Menor cantidad de informes y prioridad P2 en el backend — se entrega después de los otros dos workpanels.

**Independent Test**: Con el backend de Seguimiento implementado, se puede cargar este workpanel de forma aislada.

**Acceptance Scenarios**:

1. **Given** el backend de Seguimiento tiene datos, **When** el Operador abre el workpanel, **Then** las 3 tarjetas cargan correctamente.

## Functional Requirements (UI)

- **FR-UI-001**: Cada workpanel MUST mostrar sus informes como tarjetas o gráficas independientes, cada una con su propio estado de carga/error, sin que el fallo de una tarjeta bloquee las demás.
- **FR-UI-002**: Cada workpanel MUST exponer un selector de período compartido por todas sus tarjetas, con un rango por defecto razonable (ej. últimos 30 días).
- **FR-UI-003**: El workpanel de Despacho MUST exponer un filtro adicional de condado para los informes que lo soporten, sin afectar las tarjetas que no lo usan.
- **FR-UI-004**: Cada tarjeta MUST mostrar un estado explícito de "sin datos en este período" cuando el endpoint correspondiente devuelva vacío (ver Edge Cases del backend), en vez de quedar en blanco.
- **FR-UI-005**: El acceso a los 3 workpanels MUST restringirse a los roles `Operador` y `Administrador` (el rol "Supervisor" no existe en el sistema — ver `.specify/docs/actors.md` y la desviación ya aplicada en `../backend/plan.md`), reutilizando los guards de RBAC ya existentes en el frontend.

## Out of Scope

- Cambiar OpenAPI, validaciones de servidor, Kafka/Pinot o RF/RN del backend.
- Exportación de informes a PDF/Excel — no forma parte de los 16 informes definidos en el backend.
- Cualquier informe compuesto (ClickHouse/Airflow) — pertenece a la spec de "Informes Tácticos Compuestos", no a este módulo.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo de esta capa — 3 workpanels legibles bajo presión operativa, con estados de carga/error/sin-datos explícitos por tarjeta |
| Functional Suitability | Cita RF-001..RF-009 del backend (Depends-on) |
| Security | Reutiliza guards/RBAC existentes (FR-UI-005) |
| Maintainability | Capa FE separada de `backend/`; cada workpanel independiente de los otros dos |
| Reliability / Performance / Compatibility / Flexibility / Safety | N/A en este nivel — sin componente en el camino crítico de despacho; heredan lo ya declarado en `../backend/spec.md` |

**Traceability**: Índice del módulo `../informes-tacticos-agregados.md` en la carpeta padre.
