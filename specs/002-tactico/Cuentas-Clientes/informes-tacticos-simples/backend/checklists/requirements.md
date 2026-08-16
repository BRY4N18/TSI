# Specification Quality Checklist: Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-14
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**Validación ejecutada 2026-08-14, dos iteraciones.**

Correcciones aplicadas en la segunda iteración:

1. **Nombres de tabla fuera de los requisitos.** La primera redacción nombraba `Dim_Cliente`,
   `Fact_Session` y demás dentro de los FR. Son detalle de implementación: los FR ahora describen
   la capacidad y las tablas viven en Key Entities como conceptos de negocio y en `data-model.md`
   cuando se redacte.
2. **Criterios de éxito con lenguaje técnico.** "Responde en menos de 200 ms" se sustituyó por
   SC-002, expresado como tiempo percibido. SC-003 a SC-007 se reformularon como resultados
   verificables sin conocer la implementación.

**Sin marcadores de clarificación.** Las tres decisiones que podían necesitarlos se resolvieron
con defectos razonables documentados en Assumptions:

- *Quién ve cada listado* → el permiso espeja el rol que ya ejerce esa acción en el módulo
  operativo (criterio más restrictivo disponible).
- *Si las cuentas dadas de baja aparecen* → sí, la baja es lógica y la fila sobrevive; ya está
  verificado en el sistema real.
- *Si el período es obligatorio* → no; se distingue entre listados de estado actual y de hechos del
  período, y el contrato común ya lo fija.

**Dos requisitos del catálogo se retiraron con justificación**, documentados en Fuera de alcance:
invitaciones reenviadas (no existe el dato) y usuarios frente al tope del plan (es compuesto).
El catálogo general quedó actualizado en consecuencia.

**Riesgo abierto para `/speckit-plan`**: `apps/informes_tacticos/periodo.py` exige hoy `desde` y
`hasta`. FR-013 necesita rango opcional, así que el plan debe decidir si se extiende ese módulo o
se crea una variante — sin romper los 19 informes que dependen de él.
