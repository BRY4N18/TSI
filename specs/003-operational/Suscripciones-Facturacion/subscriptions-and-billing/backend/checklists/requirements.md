# Specification Quality Checklist: Actor RF-SUSF-001 → Director de Estrategia

**Purpose**: Validar la enmienda documental (Session 2026-07-30) antes de `/speckit-implement` (Phase 11 T091–T095)
**Created**: 2026-07-30
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details in actor/RF wording beyond JWT role slug needed for RBAC traceability
- [x] Focused on user value (quién gestiona el catálogo)
- [x] Written for stakeholders (`actors.md` + §3 Actores)
- [x] Mandatory sections of parent billing spec retained

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain (defaults: rol `DirectorEstrategia`; Admin conserva RF-003/006; pricing regional fuera de v1)
- [x] RF-SUSF-001 actor unambiguous
- [x] RNF-SUSF-002 updated and testable
- [x] Success criteria parent module unchanged (CA-SUSF-*)
- [x] Acceptance path: Director crea/edita/desactiva; Admin 403 en mutación planes
- [x] Edge: Admin sigue en downgrade/facturas
- [x] Scope bounded (sin pricing dinámico regional en v1)
- [x] Dependencies: `actors.md`, OpenAPI, Phase 11 tasks

## Feature Readiness

- [x] RF-SUSF-001 has clear actor + precondiciones
- [x] User scenarios still valid with new actor on Esc. 15 (desactivación)
- [x] Measurable outcomes of parent module still apply
- [ ] **Code not yet aligned** — T091–T095 pendientes (expected; next `/speckit-implement`)

## Notes

- Enmienda sobre feature existente `subscriptions-and-billing` (no greenfield).
- `SuscripcionesFacturacion.md` no existe en repo; alias CU-O99 documentado en RF-SUSF-001 / Clarifications.
- `module-map.md` sin columna de actor — sin cambio requerido por actor swap.
