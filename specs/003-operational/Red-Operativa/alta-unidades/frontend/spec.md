# Feature Specification: Alta de Unidades — Frontend

**Feature Branch / capa**: `alta-unidades/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-CAM-*, RNF-CAM-*, CA-CAM-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿CU-O59 / disponibilidad externa Operador? → A: **Retirado** — sin ruta FE; disponibilidad vía CU-O30 (`evidencia-unidad`).
- Q: ¿Actor UI? → A: Solo **Proveedor** dueño (`proveedorFlotaGuard`); Admin sin override (RN-CAM-002).
- Q: ¿Campo geográfico? → A: Selector `idcondado` — no texto libre `zonacobertura` (RN-CAM-005).

## User Scenarios & Testing

### US-FE-1 — Catálogo y alta individual (P1)

Proveedor Activo lista su flota y registra unidad con placa e idcondado (RF-CAM-001).

### US-FE-2 — Importación lote (P1)

Upload CSV con gmail por fila; reporte fila a fila; todo-o-nada (RF-CAM-002).

### US-FE-3 — Edición (P1)

Proveedor edita campos permitidos; bloqueo UI si despacho activo (RF-CAM-003).

### US-FE-4 — Baja y reactivación (P1)

Flujo baja con motivo y reactivación con manejo 409 placa (RF-CAM-004).

## Functional Requirements (UI)

- **FR-UI-001**: Página `catalogo` — listado solo unidades del Proveedor autenticado (RF-CAM-001, RNF-CAM-004).
- **FR-UI-002**: Formulario alta individual en catálogo — placa, idcondado, tipo, gmail opcional (RF-CAM-001).
- **FR-UI-003**: Importación lote — input archivo + tabla errores por fila; max 500 (RF-CAM-002, RNF-CAM-002).
- **FR-UI-004**: Feedback 409 placa/gmail duplicados en alta y lote (RN-CAM-003, RN-CAM-007).
- **FR-UI-005**: Página `edicion/:id` — campos RF-CAM-003; idcliente no editable (RN-CAM-006).
- **FR-UI-006**: Confirmación extra si despacho activo al editar campos críticos (RF-CAM-003).
- **FR-UI-007**: Página `baja/:id` — baja lógica + reactivación (RF-CAM-004).
- **FR-UI-008**: `proveedorFlotaGuard` — requiere rol Proveedor y cliente Activo (RN-CAM-008).
- **FR-UI-009**: `UnidadEmergenciaApiService` + `UnidadEmergenciaFacadeService`.
- **FR-UI-010**: Sin rutas/páginas CU-O59 retiradas (RF-CAM-005 backend).
- **FR-UI-011**: Selector condado poblado desde catálogo backend — no entrada libre de región.

## Out of Scope

- Declaración disponibilidad unidad (CU-O30 — evidencia-unidad).
- Override Administrador sobre flotas ajenas.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — catálogo flota Proveedor |
| Functional Suitability | FR-UI citan RF-CAM-* |
| Security | Guard scope idcliente |
| Safety | Indirecta — catálogo correcto alimenta despacho |

**Traceability**: [`../alta-unidades.md`](../alta-unidades.md).
