# Specification Quality Checklist: Informes Tácticos Simples de Suscripciones y Facturación (Backend)

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

Corrección aplicada en la segunda iteración: FR-006 nombraba la columna del token de pasarela.
Se reformuló como «el identificador con el que se ejecuta el cobro», que es lo que un lector no
técnico necesita entender y no depende del nombre de la columna.

**Sin marcadores de clarificación.** Las decisiones que podían necesitarlos se resolvieron con
defectos razonables documentados en Assumptions:

- *Si una cuenta suspendida conserva acceso a sus facturas* → sí (FR-011). Está verificado en el
  sistema real: el suspendido conserva el acceso mínimo para regularizar. Negárselo lo dejaría
  atrapado sin poder pagar.
- *Si el motivo de cancelación puede faltar* → no. El módulo operativo lo exige al cancelar.
- *Qué hacer si un usuario pide los datos de otra cuenta* → negativa explícita, nunca sustitución
  silenciosa. Mismo criterio que Ventas y CRM.

## Tres hallazgos que cambiaron el alcance

**1. Diez filas del catálogo se resuelven en cuatro listados.** Cinco son el mismo listado de
suscripciones con distinto filtro; dos son el mismo listado de facturas. Es la segunda vez que
ocurre (Ventas y CRM fue la primera) y confirma que **el catálogo cuenta preguntas, no endpoints**.

**2. «Clientes sin método de pago activo» es compuesto, no simple.** Exige restar de las cuentas con
suscripción aquellas que tienen método vigente: una diferencia de conjuntos entre dos tablas, que la
base analítica no resuelve en una consulta. Se reclasifica y se ofrece en su lugar un listado de
métodos vigentes con los próximos a caducar, que cubre la misma preocupación de forma preventiva.
**Ese listado añadido es criterio propio**, no exigencia del marco, y está marcado como tal.

**3. Una predicción mía resultó equivocada, y conviene dejarlo escrito.** Anticipé que el motivo de
cancelación y el plan programado podrían no persistirse, como ocurrió en los dos módulos anteriores.
**Ambos se escriben correctamente**: la cancelación exige motivo y lo guarda, y el cambio programado
se registra y lo aplica el job de renovación. No todo lo que el esquema declara está vacío.

**Riesgos abiertos para `/speckit-plan`:**

- **El «sin cambio programado» se representa con un valor centinela, no con ausencia.** El filtro de
  FR-002 y la presentación de FR-020 deben distinguirlo de un plan real. Es la misma familia de
  defecto que ya causó el informe de completitud que no mide nada.
- **El acotamiento por organización necesita generalizar el resolutor de Ventas y CRM**, que asume
  que el titular es el propio solicitante. Aquí hay un salto de indirección. El módulo operativo ya
  lo resuelve para su propio uso; hay que subirlo a la capa transversal antes de los tres
  departamentos que faltan, que acotan por el mismo eje.
- **FR-006 es la exigencia de seguridad más fuerte de la serie.** El identificador de cobro no es un
  hash que haya que romper: sirve para cobrar. La prueba correspondiente debe inspeccionar la
  respuesta completa, no solo los campos declarados en el contrato.
