# Specification Quality Checklist: Informes Compuestos de Suscripciones y Facturación

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

**Informe #12 → unidades y usuarios ahora; llamadas API cuando se especifique Partners** (FR-029 a
FR-031).

**FR-030 es lo que hace honesta a la decisión**: el informe declara que falta esa dimensión y **no
devuelve un campo de llamadas vacío ni en cero**. Un cero diría «este cliente no consume la API», que
es una afirmación completamente distinta de «todavía no lo medimos».

**FR-031 impide adelantarse**: modelar aquí el hecho de llamadas obligaría a Partners a vivir con un
diseño que no eligió, o a rehacerlo.

### Verificado contra el sistema real, no supuesto

- **Las filas se contaron una a una**: salen **10 simples y 13 compuestos**, frente a los 10 y 12 de
  la tabla resumen. Es la **segunda discrepancia** del catálogo, tras la de Emergencias.
- **Ningún informe compuesto existe** en este departamento; el único simple construido es el catálogo
  de planes.
- **Los cinco defectos del origen están medidos, no supuestos**: una suscripción cancelada con
  `activo = true`; `motivocancelacion` poblado en activas; una vigencia invertida; el centinela `0`
  en el plan programado; y tres representaciones distintas de «sin motivo».
- **Los volúmenes están medidos**: 4 suscripciones, 6 facturas, 6 planes, 3 métodos de pago, 4
  solicitudes. Los cinco indicadores BSC se calcularían sobre eso.
- **El formato de `limites` y `severidades_desbloqueadas` se inspeccionó**: es texto estructurado
  parseable, así que desplegarlo en columnas al cargar es viable.
