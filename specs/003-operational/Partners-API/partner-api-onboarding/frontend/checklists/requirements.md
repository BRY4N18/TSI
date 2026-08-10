# Specification Quality Checklist: Onboarding de Partners API — Frontend

**Purpose**: Validar la completitud y calidad de la especificación antes de pasar a `/speckit-tasks`
**Created**: 2026-08-09
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

**Resultado: 16/16 ✅** — la spec puede avanzar a `/speckit-tasks`.

### Correcciones aplicadas durante la validación

Tres ítems fallaron en la primera pasada y se corrigieron:

1. **«No implementation details»** — la versión inicial nombraba `localStorage`, `sessionStorage` y
   cabeceras HTTP concretas dentro de los FR-UI. Reescritos en términos de resultado observable
   («no se persiste en el almacenamiento del navegador», «envía una clave de idempotencia»). El
   detalle técnico vive en [`contracts/`](../contracts/) y [`plan.md`](../plan.md), que es donde
   corresponde.
2. **«Success criteria are technology-agnostic»** — SC-001…008 se redactaron sobre resultados de
   usuario (tiempo de incorporación, secretos perdidos, credenciales duplicadas) en vez de sobre
   métricas de sistema.
3. **«Dependencies identified»** — se añadió la sección **Dependencias de backend** con
   `BE-DELTA-01` y `BE-DELTA-02`, que estaban implícitos y son **bloqueantes**.

### Aclaraciones resueltas (no quedan marcadores abiertos)

Las tres preguntas materiales se resolvieron en sesión y están registradas en la sección
*Clarifications* de la spec:

| Tema | Resolución |
|---|---|
| El partner no puede descubrir su propio `idpartner` | Añadir `GET /partners/me` (`BE-DELTA-01`) |
| El Administrador recibía el secreto de producción del partner | No mostrarlo; el partner lo emite y lo ve él (`BE-DELTA-02`) |
| ¿La lista lleva `pencil`? | No — el backend no expone PATCH de ficha; variante **Ver-only** del design-system |

### Riesgo abierto para la fase siguiente

**`BE-DELTA-01` y `BE-DELTA-02` reabren la capa `backend/`**, que estaba cerrada con 81/81 tareas,
208 tests y verificación contra Pinot real. No alteran ninguna regla de negocio verificada, pero
`/speckit-tasks` debe colocarlos como **tareas previas y bloqueantes** de toda tarea de UI que
dependa de ellos, con sus propios tests de contrato y una reejecución de la suite del módulo.
