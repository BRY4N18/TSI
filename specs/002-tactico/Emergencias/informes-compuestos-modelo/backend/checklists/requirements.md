# Specification Quality Checklist: Informes Compuestos de Emergencias sobre el Modelo Analítico

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

### Dos aclaraciones, resueltas el 2026-08-14

1. **Informe #16, estimación de llegada** → **se define en el modelo** (FR-029 a FR-033). El sistema
   operativo no guarda ninguna, así que se deriva del histórico: mediana de despachos comparables
   —mismo condado y severidad— sobre una ventana anterior al despacho medido.

   **La reserva planteada se resolvió por diseño, no ignorándola.** El riesgo era presentar un
   cálculo propio como si fuera un compromiso operativo; FR-032 obliga a etiquetarlo como valor de
   referencia derivado del histórico y prohíbe presentarlo como objetivo o SLA. FR-031 impide además
   que la falta de referencia se disfrace de «llegó a tiempo».

2. **Informe #20, desglose por técnico** → **solo por unidad** (FR-034). La exclusión de identidad
   se mantiene intacta y sin excepciones.

### Verificado durante la redacción, no supuesto

- Las 26 filas de informe compuesto se contaron una a una en el catálogo. **Su tabla resumen dice 25
  y está mal**; queda anotado en la spec.
- Los volúmenes de las nueve fuentes de OT24 y OT25 se midieron contra el sistema operativo real. Las
  cifras del apartado *Riesgos* son medidas, no estimaciones.
- La cobertura del modelo informe por informe se contrastó con su esquema real: 19 se sostienen hoy,
  5 exigen ampliarlo y 2 dependen de estas aclaraciones.
