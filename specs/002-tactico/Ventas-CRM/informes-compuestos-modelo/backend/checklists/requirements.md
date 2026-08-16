# Specification Quality Checklist: Informes Compuestos de Ventas y CRM

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

**Informe #8 → «clientes convertidos por canal», no el CAC** (FR-021 a FR-023).

El coste por canal no existe en ninguna tabla: ni inversión publicitaria, ni presupuesto por campaña,
ni coste imputado. Es el mismo hueco que el catálogo ya reconoce para el margen operativo por región,
y que aquí no estaba señalado.

**FR-022 prohíbe incluso devolver una columna de coste vacía**: una columna así invita a rellenarla
desde fuera, y entonces el tablero mostraría un CAC que el sistema no puede sostener. El BSC queda
parcialmente cubierto **y declarado como tal**.

### Verificado contra el sistema real, no supuesto

- **Las 13 filas de informe compuesto se contaron una a una**, y coinciden con la tabla resumen: 7
  simples y 13 compuestos, más uno ya retirado por falta de dato. **Sin discrepancia**, como en Red
  Operativa y a diferencia de Emergencias.
- **Ningún informe de este departamento existe hoy**, comprobado sobre las rutas registradas.
- **El defecto de `activo` está confirmado con datos**: 2 convertidos y 1 perdido comparten
  `activo = false`, y `motivo_inactividad` sí los distingue.
- **Las dos tablas vacías de OT03 se diagnosticaron leyendo el código**, no suponiendo: ambos
  repositorios publican a Kafka, así que el camino de escritura existe y el vacío es de entorno.
- **Los volúmenes de las seis fuentes están medidos**: 10 prospectos, 24 transiciones, 9
  asignaciones, 4 clientes, y dos tablas a cero.
