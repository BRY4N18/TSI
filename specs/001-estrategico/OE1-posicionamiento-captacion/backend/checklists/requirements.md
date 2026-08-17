# Specification Quality Checklist: OE1 — Posicionamiento y Captación Digital

**Purpose**: Validar la completitud y calidad de la especificación antes de pasar a `/speckit-plan`
**Created**: 2026-08-16
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *salvedad heredada de OE6*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *salvedad heredada*
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [ ] ⏸ **Ready for `/speckit-plan`** — **NO.** Ver abajo

**15 / 16**, y el que falta **no se arregla escribiendo**.

---

## Notas

### El ítem que no pasa, y por qué no es un defecto de la spec

**`/speckit-plan` no debe ejecutarse todavía.** Los trece informes consumen hechos que no existen, y
los cargan tres módulos tácticos con **0 tareas hechas de 202**.

Un plan hoy tendría que inventar la forma de las consultas contra tablas que nadie ha creado, y
**no podría verificar nada**. Los tres objetivos que sí tienen plan —OE6, OE3 y OE4— produjeron
**once correcciones al catálogo**, y las once salieron de medir:

| Corrección | Cómo salió |
|---|---|
| El eje de región no existe | Consultando `dim_region` |
| Las regiones no tienen fecha de arranque | `valido_desde = 1970-01-01` |
| E3-02 mezclaba latencia técnica con tiempo operativo | Midiendo 106 s contra una meta de 100 ms |
| E3-12 mide un suceso que no ocurre | 1 082 de 1 083 manuales sin intento previo |
| `distanciamillas` sí existía | Consultando el origen |
| E4-14 lo impide la idempotencia | Viendo que 4 252 filas comparten `cargado_en` |

Ninguna se deduce del catálogo. **Escribir el plan sin datos produciría un documento con la forma de
un plan verificado y el contenido de una suposición.**

### Lo que esta spec sí aporta ahora

**Declara qué necesita la capa estratégica de cada módulo táctico**, antes de que se construyan. Si
`hecho_suscripcion` no congela la periodicidad, E1-01 no puede normalizar el MRR; es más barato
saberlo ahora.

Y detectó **una discrepancia del catálogo sin necesidad de datos**: nombra `hecho_pipeline` como
fuente, y el diseño táctico de Ventas llama a esa tabla `hecho_transicion_embudo`. La tabla que el
catálogo cita **no va a existir**.

### Lo que se verificó, y sí se pudo

Aunque el modelo analítico no tenga estos hechos, **el sistema operativo sí tiene los datos**, y se
midieron:

| Verificado | Resultado |
|---|---|
| Volumen de las fuentes | 4 suscripciones · 6 facturas · 4 clientes · 3 onboardings · 10 prospectos |
| ¿`Dim_Cliente` tiene geografía? | **No.** 14 columnas, ninguna de país o estado → E1-07 y E1-08 ⛔ |
| ¿Existe fuente de costos de marketing? | **No** → E1-05 ⛔ |
| Nombres de los hechos que se construirán | Leídos de los `data-model.md` de los tres tácticos |

### El hallazgo más incómodo

**El objetivo se llama «internacional» y no puede medir un solo mercado.** `Dim_Cliente` no registra
el país del cliente, así que el KPI del BSC «+3 mercados nuevos al año» **no tiene fuente**.

No es un hueco del modelo analítico ni de esta capa: es que **el sistema operativo nunca preguntó de
dónde es el cliente**. Y es un dato que se pide una vez, al alta.

### Riesgo principal cuando llegue el momento de `/plan`

**Que el MRR se calcule sumando precios sin normalizar la periodicidad.** Con 4 suscripciones y
`Fact_Suscripcion.periodicidad` en la tabla, una sola anual inflaría el MRR por doce — y sobre 4
filas, esa sola sería el 25 % de la cartera.
