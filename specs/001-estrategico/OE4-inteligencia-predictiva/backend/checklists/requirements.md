# Specification Quality Checklist: OE4 — Inteligencia Predictiva

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
- [x] No implementation details leak into specification — *salvedad heredada*

**16 / 16.**

---

## Notas

### Una historia entera bloqueada, y por qué eso no invalida la spec

**US4 no es construible**: sus cinco informes esperan tres tablas que no existen. Podría haberse
sacado del alcance, y **se decidió no hacerlo**.

El motivo es que el catálogo los declara y **tres son indicadores del BSC**. Una spec que los omitiera
dejaría la impresión de que OE4 cubre su tablero, cuando cubre la mitad. Al dejarlos dentro y
aislados en su propia historia, el coste de no tenerlos queda contado — que es lo que un tablero
estratégico necesita saber de sí mismo.

`FR-OE4-021` impide lo peor: publicar los cinco con ceros. Una precisión del modelo predictivo del
0 % no dice «el modelo es malo», dice «no hay modelo», y son cosas distintas.

### Lo que se verificó contra datos, y lo que no

| Verificado | Cómo |
|---|---|
| `indice_calidad_historico` existe y es el diseño legado | 182 filas, columnas = métricas |
| Sus cifras de evidencia divergen del modelo | 0,50 vs 0,00 y 1,00 vs 0,25 en los dos días con dato |
| El clima es un recuento, no una condición | `DESCRIBE hecho_accidente` |
| No existe `distancia_millas` | `DESCRIBE hecho_accidente` |
| El dato de origen es pobre | 3 fotos, 1 resultado de atención, 0 calificaciones en 4 252 casos |

**Lo que NO se afirma:** que la tabla legada esté equivocada. Con tres fotografías en el histórico,
ninguna de las dos cifras es concluyente, y decir lo contrario sería exactamente el tipo de conclusión
apresurada que este proyecto ha corregido tres veces. Por eso la spec pide **contraste**, no
sustitución a ciegas.

### Cero marcadores de clarificación

Las dos incertidumbres reales —el umbral de masa crítica y si la fórmula del índice consolidado es
correcta— **no son decisiones de negocio del usuario**: la primera se resuelve mirando cuántos casos
necesita el modelo, y la segunda comparando contra el legado. Ambas son trabajo de `research`.

### Riesgo principal a vigilar en `/plan`

**Que la migración de E4-01 cambie la fórmula del índice sin darse cuenta.** Hay 182 días ya
calculados con la fórmula legada; una fórmula distinta produciría una serie que parece continua y
tiene un salto en el medio, justo donde nadie mira. La suposición de la spec —conservar la fórmula
salvo prueba en contra— existe por eso.
