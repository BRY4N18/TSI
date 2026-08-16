# Specification Quality Checklist: Informes Tácticos Simples de Emergencias (Backend)

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

Corrección aplicada en la segunda iteración: la Nota de alcance nombraba tablas del histórico de
estados. Se reescribió en términos de negocio —«el estado formal vive en el histórico, no en el
caso»— conservando el argumento.

**Sin marcadores de clarificación.** Las decisiones que podían necesitarlos se resolvieron con
defectos razonables documentados en Assumptions:

- *Qué ve un cliente sin zonas contratadas* → **nada** (FR-011). De las dos lecturas posibles de un
  campo vacío, es la única segura; la contraria daría acceso total a quien no contrató ninguna zona.
- *Si un cliente ve casos en curso* → **no** (FR-010). Es lo que el módulo operativo ya aplica en el
  expediente del cliente, y el listado no puede ser más amplio que esa pantalla.
- *Si los casos fusionados y descartados se listan* → **sí** (FR-007). El sistema garantiza que no se
  borran, y ocultarlos escondería el ruido que hay que poder medir.

## Las tres predicciones se cumplieron

Antes de verificar quedaron anotadas tres sospechas. Las tres se confirmaron:

**1. `activo = false` cubre razones opuestas.** Cerrado, descartado y fusionado dejan el caso
inactivo. Es la quinta vez que aparece este patrón en la serie —tras perdido/convertido, existe/puede
acudir, disputa/mora y revocación/cascada— y **la tercera que obliga a partir el alcance** de un
listado.

**2. El estado formal no es una propiedad del caso.** Vive en el histórico de estados. Igual que la
disponibilidad de una unidad y el motivo de una credencial inactiva.

**3. El acotamiento por zona no es un filtro, hoy.** El módulo operativo lo resuelve **caso por caso
mientras recorre**, resolviendo la ubicación de cada fila. Funciona porque se detiene pronto, pero no
es filtrado en la base. FR-012 exige resolverlo como conjunto **antes** de consultar.

## El riesgo que puede cambiar el alcance

**FR-012 es una apuesta que el plan debe verificar.** Traducir las zonas contratadas a un conjunto de
ubicaciones consultable puede producir un conjunto demasiado grande para usarlo como filtro. Si
resultara impracticable:

- El acotamiento por zona dejaría de ser simple.
- Y con él, **el acceso del cliente al listado de casos** — que es la User Story 1 completa.

Es el primer módulo de la serie donde un hallazgo del plan podría eliminar una historia entera, no
solo recortar campos. Conviene resolverlo antes que nada.

## Nota sobre el renombrado

Este módulo ocupa el nombre `informes-tacticos-simples`, que estaba tomado por los 19 informes
agregados. Aquel módulo se renombró a `informes-tacticos-agregados`, **sin tocar su código**, y sus
referencias internas quedaron actualizadas. El contrato común recoge el cambio en su §9.
