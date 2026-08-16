# Specification Quality Checklist: Modelo Analítico Táctico

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

**Validación ejecutada 2026-08-14, tres iteraciones** — una más que los módulos anteriores, por la
dificultad de encajar un modelo de datos en una plantilla pensada para funcionalidades.

Correcciones aplicadas:

1. **Nombres de motor y de tabla en los requisitos.** La primera redacción decía «ClickHouse»,
   «MergeTree» y nombres concretos de tabla. Se reescribieron como «el almacén analítico» y por
   concepto de negocio. El motor está fijado por la spec de infraestructura y no corresponde
   redecidirlo aquí.
2. **Vocabulario técnico de modelado.** «SCD tipo 2», «tabla de hechos», «fact table», «grain» se
   sustituyeron por «dimensión versionada con su vigencia», «hecho», «grano». El concepto es el
   mismo y se sostiene sin la jerga.
3. **Criterios de éxito medidos en filas y consultas.** Los primeros medían propiedades internas
   (número de tablas, tamaño de índice). Se reformularon como resultados verificables: que dos
   informes den la misma cifra, que recargar no duplique, que el pasado no se reescriba.

## Cómo se resolvió el desajuste con la plantilla

La plantilla asume usuarios humanos y funcionalidad visible. Un modelo de datos no tiene ninguna de
las dos cosas.

**Solución adoptada:** los usuarios del modelo **son los informes**. Cada historia está escrita desde
el punto de vista de un informe que necesita algo del modelo, y los criterios de éxito miden
propiedades observables desde fuera —cifras coincidentes, historia estable, recargas idempotentes—
en lugar de propiedades internas del esquema.

Es una interpretación de la plantilla, no una desviación: mantiene el módulo dentro del mismo flujo
que los ocho anteriores en vez de inventar un formato aparte.

## El hallazgo que ancla todo el diseño

**El informe de rendimiento por proveedor ya arrastra el defecto que este modelo existe para
resolver**, y está documentado en su propio código:

> *«`Dim_UnidadEmergencia` no historiza cambios de proveedor, así que el flujo usa el proveedor
> actual de la unidad para todos los períodos. Resolverlo requeriría una tabla de historial de
> asignación unidad↔proveedor que no existe.»*

Si una unidad cambia de proveedor, **todos sus despachos pasados se reatribuyen al proveedor nuevo**.
El informe no falla ni avisa: reescribe la historia, y un proveedor puede aparecer respondiendo por
despachos que nunca atendió.

Es el mismo patrón que se ha repetido cinco veces en los listados simples —un dato que parece
correcto y no lo es— pero aquí con una diferencia: **la solución no es un filtro mejor, es un modelo
distinto.** Una dimensión versionada lo resuelve por construcción, y esa es la justificación más
sólida del esquema en estrella en este proyecto.

## Tres decisiones de diseño que conviene revisar

**1. Estrella en lo lógico, desnormalización selectiva en lo físico.** El almacén elegido rinde mejor
leyendo una tabla ancha que uniendo varias estrechas, así que un esquema en estrella de manual
rendiría peor aquí que en un almacén relacional. Se conserva el diseño dimensional —grano explícito,
una definición por concepto, historia versionada— y se copian en el hecho los pocos atributos por los
que casi siempre se agrupa. **Se paga en espacio, que es lo barato.**

**2. Tres tipos de hecho, no uno.** El caso de emergencia es una **instantánea acumulada** —un
proceso con hitos que se actualiza al avanzar—, y reconocerlo convierte media docena de informes de
tiempos en simples restas dentro de una fila. Y el ingreso recurrente necesita **instantánea
periódica**: no es un suceso, es un estado que se repite cada mes, y calcularlo desde los sucesos de
facturación es la vía habitual por la que el MRR sale mal.

**3. Un flujo de carga por hecho, no por informe.** Es la diferencia entre ~13 flujos y ~105.

## La regla que evita volver al punto de partida

**FR-016**: ningún informe crea su propia tabla; si necesita algo que no existe, se modifica el
modelo.

Sin ella, el primer informe que no encaje añadirá su tabla, el segundo también, y en veinte informes
estaremos otra vez donde estamos hoy. Conviene propagarla al contrato común cuando el modelo se
construya.

## Riesgos abiertos para `/speckit-plan`

- **El grano del hecho de despacho es la decisión más condicionante.** Si una fila es un despacho o
  un intento cambia qué informes son posibles y cuáles mentirían. El plan debe resolverlo mirando qué
  pregunta cada informe del catálogo, no por comodidad de carga.
- **La reconstrucción del histórico versionado.** Las versiones se construyen observando la fuente
  entre cargas, así que **el pasado anterior a la primera carga no tiene historia**: solo se conoce
  el estado actual. El plan debe decidir si eso se acepta —el histórico arranca hoy— o si se
  reconstruye algo desde las tablas de historial que sí existen en el origen.
- **Qué se construye primero.** La spec define el modelo completo; el plan debe cortar la primera
  fase. Los hechos de accidente y despacho son los candidatos naturales: cubren la mayoría de los
  compuestos ya especificados y sustituyen a los tres informes con tabla propia.
