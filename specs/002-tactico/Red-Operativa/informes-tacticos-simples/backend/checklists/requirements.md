# Specification Quality Checklist: Informes Tácticos Simples de Red Operativa (Backend)

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

Corrección aplicada en la segunda iteración: la Nota de alcance nombraba tablas e histórico de
estados con vocabulario técnico. Se reescribió en términos de negocio —«existencia» frente a
«disponibilidad operativa»— conservando el argumento, que es lo que un lector no técnico necesita
entender para aceptar la exclusión.

**Sin marcadores de clarificación.** Las decisiones que podían necesitarlos se resolvieron con
defectos razonables documentados en Assumptions:

- *Si el listado de regiones incluye las despublicadas* → sí. Una región retirada sigue siendo
  información de supervisión; ocultarla escondería precisamente lo que OT13 vigila.
- *Quién ve las regiones* → Administrador y Director Tecnológico. Una región no pertenece a ningún
  proveedor, así que no hay acotamiento que aplicar.
- *Qué hacer si un proveedor pide la flota de otro* → negativa explícita. Mismo criterio que los dos
  módulos anteriores.

## El hallazgo que cambió el módulo

**La disponibilidad de una unidad no es una propiedad suya.** El catálogo pedía «unidades por
estado, condado y proveedor» como un solo listado simple. Al verificarlo:

- La condición de **alta o baja** sí es una columna de la unidad.
- El **estado operativo** —Activa, Ocupada, En Misión, Fuera de servicio— **solo vive en el
  histórico de estados**, y obtenerlo para un listado exige una consulta por unidad o una agregación
  más un cruce.

Se separan las dos nociones: el listado informa de **composición de flota**, y la disponibilidad
queda como CU-T08, compuesta. FR-006 a FR-008 lo hacen explícito, y FR-008 obliga a que la propia
respuesta declare su alcance para que ningún consumidor lo interprete de otro modo.

**Por qué se le dio tanto peso.** Es el primer módulo de la serie donde un informe equivocado no
produce un número comercial inflado sino una decisión de cobertura sobre unidades que no pueden
atender nada. La distinción entre «existe» y «puede acudir» es la diferencia entre creer que hay
cobertura y tenerla.

## Segunda reclasificación

**«Unidades de alta en lote pendientes de primer acceso» es compuesta**: cruza la flota con el
estado de las credenciales de acceso, dos tablas.

## Riesgos abiertos para `/speckit-plan`

- **El eje «organización» debe generalizar sin cambios.** Aquí el titular es la empresa proveedora,
  igual que la cuenta cliente en Suscripciones. **Si hiciera falta modificar el resolutor, sería
  señal de que aquella generalización quedó corta** — conviene tratarlo como prueba de la pieza, no
  solo como uso.
- **La jerarquía geográfica es el catálogo más profundo de la serie.** Resolver condado y ciudad
  para una página de unidades exige varias consultas de catálogo encadenadas; el plan debe acotar
  cuántas y evitar una por fila.
- **FR-008 es inusual**: obliga a que la respuesta declare su propio alcance. Conviene decidir en el
  plan si eso es un campo del envelope o parte de la documentación del contrato, y ser coherente con
  los tres módulos anteriores.
