# Feature Specification: Incorporación Regional — Frontend

**Feature Branch / capa**: `incorporacion-regional/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-REGON-*, RNF-REGON-*, CA-REGON-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Checklist técnico automatizado en UI? → A: No — formulario captura resultado manual Aprobada/Rechazada + motivo (RF-REGON-001 §6).
- Q: ¿Historial validaciones? → A: UI muestra `estadoregion_actual` tras ejecutar; historial completo vía API listado (RNF-REGON-001).

## User Scenarios & Testing

### US-FE-1 — Catálogo regiones (P1)

Admin/Director consultan regiones y estados actuales antes de validar (consulta operativa).

### US-FE-2 — Ejecutar validación (P1)

Formulario CU-O55 — alta región si aplica, resultado y motivo si rechazada (RF-REGON-001, RF-REGON-002).

### US-FE-3 — Reevaluación / despublicación (P1)

Director degrada a En_Alerta o Despublicada desde región en Producción (RF-REGON-003).

## Functional Requirements (UI)

- **FR-UI-001**: Página `catalogo-regiones` — listado con badge `estadoregion` (En_Validación, Producción, En_Alerta, Despublicada).
- **FR-UI-002**: Página `validacion` — formulario ejecutar protocolo; campos resultado/motivo (RF-REGON-001).
- **FR-UI-003**: Tras submit validación, mostrar `estadoregion_actual` devuelto por API (RF-REGON-001 salida).
- **FR-UI-004**: Flujo rechazo → remediación: CTA reintentar (nueva validación) o rechazo definitivo activo=false (RF-REGON-002).
- **FR-UI-005**: Página `reevaluacion/:id` — select En_Alerta | Despublicada + motivo (RF-REGON-003).
- **FR-UI-006**: Guard Admin+Director en catálogo/validación; solo Director en reevaluación (matriz §3 backend).
- **FR-UI-007**: `RegionOperativaApiService` + `RegionOperativaFacadeService` — sin lógica de transición en componentes.
- **FR-UI-008**: Mensaje informativo: despublicación no cancela casos activos (RN-REGON-004) — copy en confirmación.
- **FR-UI-009**: CU-O62 despublicación automática — sin UI humana; opcional badge/indicador en catálogo si API expone estado reciente.
- **FR-UI-010**: Estados async estándar en formularios de validación/reevaluación.

## Out of Scope

- Despublicación automática CU-O62 (job Sistema).
- FK unidad↔región pendiente (RN-REGON-005 mecanismo disparo).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — protocolo validación regional |
| Functional Suitability | FR-UI citan RF-REGON-* |
| Security | Guards Administrador / DirectorTecnologico |
| Safety | Copy continuidad casos activos al despublicar |

**Traceability**: [`../incorporacion-regional.md`](../incorporacion-regional.md).
