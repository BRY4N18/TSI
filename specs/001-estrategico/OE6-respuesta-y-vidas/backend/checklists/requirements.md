# Specification Quality Checklist: OE6 — Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Purpose**: Validar la completitud y calidad de la especificación antes de pasar a `/speckit-plan`
**Created**: 2026-08-16
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *con la salvedad documentada abajo*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *con la salvedad documentada abajo*
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
- [x] No implementation details leak into specification — *con la salvedad documentada abajo*

**16 / 16.**

---

## Notas

### La salvedad de los tres ítems marcados

La spec nombra hechos y columnas del modelo analítico (`hecho_accidente.hora_primera_llegada`,
`num_escaladas_severidad`), rutas de endpoint y un fichero de consulta.

**Es deliberado y consistente con los diez módulos anteriores del proyecto.** En un módulo de
informes, el modelo analítico **no es implementación: es el dominio**. Un requisito que dijera «el
sistema debe medir el tiempo de respuesta» sin decir contra qué hito se mide no sería más limpio, sería
**menos verificable** — y la §«Discrepancias del catálogo» existe precisamente porque cinco fuentes
que el catálogo daba por buenas no coincidían con el modelo real. Sin nombrarlas no se habría
detectado.

Lo que sí se respetó: **ninguna decisión de implementación** (motor de consulta, estructura de
servicios, cómo se resuelve la región) entra aquí. Todas quedan explícitamente derivadas a `/plan`.

### Cero marcadores de clarificación, y por qué

No hubo que abrir ninguno. Las tres ambigüedades candidatas se resolvieron **leyendo el código y el
modelo**, no suponiendo:

| Candidata | Cómo se resolvió |
|---|---|
| Qué es el «ETA estimado» de E6-07 | No existe ni puede existir sin coordenadas. Se adopta la referencia histórica que el módulo táctico ya derivó |
| Dónde vive el historial de severidad de E6-11 | El hecho **se decidió no crear**; son dos métricas de `hecho_accidente` |
| Si E6-03 debe atribuirse por unidad | La decisión #35 ya planteaba las opciones; entregar por período es su opción A y **disuelve** el defecto |

La única incertidumbre real —la cardinalidad región↔estado— **no es una clarificación de negocio**:
es un hecho comprobable contra el origen, y comprobarlo es trabajo de `research`. Marcarla con
`[NEEDS CLARIFICATION]` habría pedido al usuario que adivinara algo que el sistema puede responder.

### Lo que esta spec deja explícitamente abierto

1. **El eje de región** (§«Lo que falta en el modelo»). Único trabajo de modelo pendiente.
2. **La decisión #36**, que limita E6-09. Es el único informe que no puede entregarse completo.
3. **La muestra mínima** para percentiles: se hereda, no se decide aquí.

### Riesgo principal a vigilar en `/plan`

**Que el módulo acabe reimplementando las consultas tácticas en vez de reutilizarlas.** Es el camino
de menor resistencia —cada consulta estratégica necesita percentil, ventana comparada y región, y
retocar la táctica parece más trabajo que escribir una nueva— y produciría dos definiciones de la
misma métrica que divergirían a la primera corrección.

SC-007 existe para detectarlo: obliga a que las cifras coincidan entre capas cuando se piden con la
misma agrupación y período.
