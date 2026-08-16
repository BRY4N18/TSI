# Specification Quality Checklist: Informes Tácticos Simples de Partners y API (Backend)

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

Corrección aplicada en la segunda iteración: FR-008 nombraba la columna del secreto. Se reformuló
como «el secreto con el que un partner se autentica, ni en claro ni transformado», que es lo que un
lector no técnico necesita entender y no depende del nombre de la columna.

**Sin marcadores de clarificación.** Las decisiones que podían necesitarlos se resolvieron con
defectos razonables documentados en Assumptions:

- *Si un partner suspendido conserva acceso a sus informes* → sí (FR-012), por el mismo criterio que
  el cliente moroso en Suscripciones: es donde ve qué debe regularizar.
- *Si las versiones retiradas del contrato se listan* → sí. Saber qué se retiró y cuándo es parte de
  la supervisión.
- *Qué significa un cliente sin preferencias configuradas* → alcance ausente, **nunca** acceso
  ilimitado (FR-023). Es la interpretación segura de las dos posibles.

## La predicción se cumplió, y el código la enuncia mejor de lo previsto

Antes de verificar quedó anotada la sospecha de que `activo = false` en una credencial cubriría
razones opuestas. **Se confirmó, y con una precisión que la predicción no alcanzaba**: no es que un
listado *pudiera* confundirlas, es que **el registro de la credencial no puede distinguirlas en
absoluto**. El código lo dice al explicar la reactivación selectiva: *«no podría: las tres razones
son indistinguibles»*.

Eso cambia la conclusión. No basta con «distinguir bien los motivos en el listado»: **el motivo no
está donde se creía**. Vive en la bitácora de cambios de acceso, y unirlo a la credencial exige
localizar el último evento relevante por credencial — una operación compuesta.

Es la cuarta vez que aparece el patrón y **la segunda que obliga a partir el alcance** de un listado,
como ocurrió con la flota en Red Operativa.

## Un hallazgo que ahorra trabajo

**«Llamadas rechazadas por límite» ya está cubierto.** La consola de registros construida en su
momento filtra por código de respuesta, acota por partner y pagina con cursor real. Construir un
endpoint aparte sería duplicarla.

Merece la pena anotar cómo se descubrió: leyendo la vista existente antes de escribir el requisito,
no después. Las cinco specs anteriores establecieron ese hábito y aquí evitó trabajo redundante.

## Riesgos abiertos para `/speckit-plan`

- **El secreto de autenticación es del mismo orden que el medio de cobro de Suscripciones.** El
  módulo ya tiene un mecanismo de campos sensibles; el plan debe reutilizarlo, no inventar otro, y la
  prueba correspondiente debe inspeccionar la respuesta serializada completa.
- **El acotamiento de un Partner pasa por su organización.** Conviene confirmar que la resolución
  funciona para usuarios de partner, dado lo aprendido en Soporte: la tabla de vínculos no la escribe
  nadie y todo cae en el administrador local.
- **Este módulo no debería necesitar tocar la capa transversal.** Es el segundo que solo la consume.
  Si hiciera falta modificarla, conviene entender por qué antes de hacerlo.
