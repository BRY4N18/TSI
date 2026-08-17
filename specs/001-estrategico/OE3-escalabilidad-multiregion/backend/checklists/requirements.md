# Specification Quality Checklist: OE3 — Escalabilidad Multi-Región

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

### La mitad del objetivo no es medible, y la spec lo dice en el título

Es lo más importante de esta especificación. OE3 se llama *escalabilidad sin degradación*, y solo la
segunda mitad tiene datos. Siete informes de catorce quedan sin endpoint.

**No se ocultó reduciendo el alcance.** Sacar los siete del catálogo habría producido una spec limpia
que da la impresión de cubrir el objetivo. Al dejarlos dentro, agrupados por tipo de bloqueo y con su
prerrequisito, el coste queda contado: **dos indicadores `[NORMATIVO]` del tablero prometen un
compromiso que hoy nadie puede verificar.**

### El bloqueo que más sorprende

`dim_region.valido_desde = 1970-01-01` en las tres regiones, con `inicio_es_real = 0`.

E3-04 mide días hasta la primera emergencia atendida contra una meta de ≤30 días `[NORMATIVO]`.
Publicado sin más, daría **más de veinte mil días** por región, en rojo permanente, **sin un solo
error**. Es el fallo silencioso más grande encontrado en la capa estratégica hasta ahora, y el motivo
de que `FR-OE3-017` prohíba publicar.

### Lo que se verificó contra datos

| Verificado | Resultado |
|---|---|
| Fecha de arranque de las regiones | `1970-01-01`, `inicio_es_real = 0` en las tres |
| Reparto de orígenes de despacho | Automático 2 847 · Manual 1 083 · Escalado 384 = 4 314 ✓ |
| `Dim_CondadoVecino` en el modelo | **No está** — existe en el operativo, no se ha cargado |
| Consultas tácticas de Red Operativa | 2 de las previstas; el módulo va 22/67 |

### La única salida barata, y por qué merece mirarse en `/plan`

De los siete bloqueos, **seis exigen historizar datos o integrar fuentes externas**. El séptimo
—E3-08, cobertura de respaldo por condado vecino— solo necesita **cargar una tabla que ya existe** en
el sistema operativo, siguiendo el procedimiento del §4.bis. `FR-OE3-019` obliga a evaluarlo.

Si sale, US3 pasa de cuatro bloqueados a tres.

### Este es el módulo que puede semaforizar

OE6 y OE4 tienen todas sus metas en `[CALIBRAR]`, así que sus `cumple` son siempre nulos. **OE3 trae
las primeras metas `[NORMATIVO]` de la capa**: latencia ≤100 ms, error de registro <1 %,
reasignación ≤30 s.

⚠️ Conviene tenerlo presente al implementar: la prueba transversal de OE6 —«ningún `cumple`
booleano»— **no aplica aquí y sería un error copiarla**. Aquí la comprobación es la inversa: que esos
tres informes **sí** devuelvan un booleano.

### Cero marcadores de clarificación

Las incertidumbres —si `Dim_CondadoVecino` se puede cargar, y si el sistema operativo podría
historizar el estado de región— son comprobables contra el origen, no decisiones de negocio. Son
trabajo de `research`.
