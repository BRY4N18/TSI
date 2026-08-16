# Specification Quality Checklist: Informes Tácticos Simples de Ventas y CRM (Backend)

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

Corrección aplicada en la segunda iteración: los nombres de tabla y de columna
(`Dim_Prospecto`, `estado_envio`) se retiraron de los FR y quedaron en Key Entities como
conceptos de negocio y en Fuera de alcance como justificación de la exclusión.

**Sin marcadores de clarificación.** Las decisiones que podían necesitarlos se resolvieron con
defectos razonables documentados en Assumptions:

- *Qué hacer si un Gerente pide la cartera de otro* → negativa explícita, **nunca** sustitución
  silenciosa por la propia. Es el comportamiento que el módulo operativo ya implementa para la
  consulta de notificaciones, y el más seguro de los dos: sustituir en silencio oculta al
  solicitante que pidió algo indebido.
- *Si Gerente de Cuentas Públicas se acota igual* → sí, mismo trato, como ya hace el módulo
  operativo.
- *Cuándo una demo está activa* → expiración futura; sin fecha, no activa.

## Dos hallazgos que cambiaron el alcance

**1. De ocho listados a cuatro endpoints.** Cuatro filas del catálogo —prospectos por canal, por
tipo de organización, por etapa y ejecutivo, y perdidos con motivo— son **la misma consulta sobre
la misma tabla con distinto filtro**. Se consolidan en un listado con filtros combinables (FR-002).
La cobertura no baja: las cuatro preguntas se responden.

Esta consolidación se apoya en la definición del propio contrato común (§1: *una tabla, filtros,
orden y paginación*) y en la prioridad por defecto de Maintainability de la constitución. **Es
reversible**: si se prefieren endpoints separados por claridad de consumo, basta con partir FR-001
en cuatro, sin tocar nada más.

**2. «Notificaciones con envío fallido» no es construible.** La columna de estado de envío existe en
el esquema pero **ningún código la escribe** — cero apariciones en todo el repositorio. El despacho
fallido lanza una excepción y deja un aviso en el log de aplicación. Es el tercer caso de la serie,
tras las invitaciones reenviadas y los intentos de acceso fallidos: **el esquema declara columnas
que la operación nunca llena.**

**Riesgo abierto para `/speckit-plan`**: el acotamiento por titularidad (FR-006 a FR-009) es la
primera vez que la capa transversal `core/informes/` debe soportar filtrado por fila según el
solicitante. Si no lo contempla, hay que extenderla **antes** de seguir con los seis departamentos
restantes, no después.
