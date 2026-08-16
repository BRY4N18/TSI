# Specification Quality Checklist: Informes Compuestos de Cuentas y Clientes

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-14
**Feature**: [spec.md](../spec.md)

## Content Quality

- [X] No implementation details (languages, frameworks, APIs)
- [X] Focused on user value and business needs
- [X] Written for non-technical stakeholders
- [X] All mandatory sections completed

## Requirement Completeness

- [X] No [NEEDS CLARIFICATION] markers remain
- [X] Requirements are testable and unambiguous
- [X] Success criteria are measurable
- [X] Success criteria are technology-agnostic (no implementation details)
- [X] All acceptance scenarios are defined
- [X] Edge cases are identified
- [X] Scope is clearly bounded
- [X] Dependencies and assumptions identified

## Feature Readiness

- [X] All functional requirements have clear acceptance criteria
- [X] User scenarios cover primary flows
- [X] Feature meets measurable outcomes defined in Success Criteria
- [X] No implementation details leak into specification

## Notes

### La aclaración, resuelta el 2026-08-14

**Se usa la relación explícita usuario ↔ cliente, con la cobertura declarada** (FR-037 a FR-040).

**FR-038 es lo que la hace honesta**: los informes devuelven **qué porcentaje de usuarios tiene
pertenencia conocida** —hoy **9,5 %**—. Sin ese número, «1 de 10 usuarios» se leería como ocupación
real cuando es cobertura del dato, y un cliente parecería tener sitio de sobra cuando quizá esté
lleno.

**FR-040 impide la tentación razonable**: combinar ambas fuentes daría más cobertura a costa de
contar administradores y miembros como si fueran lo mismo.

### Verificado contra el sistema real, no supuesto

- **Las filas se contaron una a una**: **8 simples y 9 compuestos**, más uno ya retirado. **Coincide
  con la tabla resumen** — sin discrepancia, a diferencia de Emergencias, Suscripciones y Partners.
- **Ningún informe compuesto de este departamento existe** en la app de informes tácticos.
- **La cobertura de pertenencia está medida**: 2 usuarios de 21 (9,5 %).
- **El onboarding se inspeccionó fila a fila**: 3 registros, **todos `completado = true`** y todos del
  mismo cliente. No hay ningún registro de abandono en el sistema.
- **Las sesiones se contaron por estado**: 513 inicios, 195 cierres, 10 expulsiones. La mayoría **no
  tiene cierre**.
- **`Fact_Session` guarda `token`**, y `Dim_Usuarios` guarda género y fecha de nacimiento: es el
  departamento con el dato personal más delicado después de Ventas.
