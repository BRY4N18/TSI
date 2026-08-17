# Specification Quality Checklist: OE5 — Retención y Ciclo de Vida del Cliente

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
- [ ] ⏸ **Ready for `/speckit-plan`** — **NO.** Cuatro módulos tácticos, 292 tareas por delante

**15 / 16.**

---

## Notas

### El hallazgo más importante, y no necesitó datos

**El objetivo de la satisfacción del cliente no puede medir la satisfacción del cliente.**

E5-01 —NPS, meta ≥50— es el indicador que da nombre a la perspectiva Cliente del tablero, y **no
tiene fuente**. No es un hueco del modelo analítico ni de la capa táctica: es que **el sistema nunca
le preguntó nada al cliente**. Todos los demás objetivos miden lo que el sistema hizo; este quiere
medir lo que el cliente opina.

Y es, con diferencia, **el prerrequisito más barato de todo el catálogo estratégico**: una encuesta de
una pregunta al cerrar un ticket.

### La trampa que la spec prohíbe explícitamente

`Fact_CierreAccidente.calificacion` existe, se llama «calificación» y es tentadora como NPS.
**FR-OE5-022 lo prohíbe** por dos motivos independientes:

1. Es la valoración de **un caso de emergencia individual**, no la satisfacción del cliente con TSI.
   Un municipio puede estar encantado con el servicio y calificar mal un caso que salió mal.
2. Tiene **0 filas**.

Sin la prohibición escrita, es exactamente el atajo que alguien tomaría para «desbloquear» el
indicador del BSC.

### Lo que se pudo verificar sin el modelo analítico

| Verificado | Resultado |
|---|---|
| Volumen de tickets | **14** en `Fact_Reclamo`, 34 acciones |
| Volumen comercial | 4 suscripciones · 6 facturas · 4 clientes |
| Sesiones | 747 — la única fuente con volumen real, y alimenta E5-12 |
| ¿Existe tabla de encuestas? | **No** → E5-01 ⛔ |
| ¿Existe tabla de programación de informes? | **No** → E5-11 ⛔ |
| Nombre del hecho de soporte | `hecho_ticket`, no `hecho_reclamo` como dice el catálogo |

### La aritmética que conviene tener presente

**14 tickets.** La meta del BSC es ≥95 % de cumplimiento de SLA. Con 14 tickets, **cada uno vale 7,1
puntos**: un solo incumplimiento deja la cifra en 92,9 % y rompe la meta, sin que el servicio haya
empeorado.

Es el argumento más claro de por qué `FR-OE5-006` obliga a declarar `parcial`: la cifra no es falsa,
pero **leerla como un indicador de gestión sí lo sería**.

### Cuatro informes que este módulo no construye

E5-09, E5-10, E5-13 y E5-14 son los mismos que E1-06, E1-11, E1-09 y E1-10. **OE1 es el dueño.**

`SC-007` va más allá de no implementarlos: exige que **sus rutas en OE5 devuelvan `404` con el camino
de OE1**. Un `404` mudo invitaría a alguien a «arreglarlo» implementándolos, que es justo lo que la
regla §7 del contrato evita.

Es la aplicación más visible de esa regla en toda la capa: **el catálogo pide quince y se construyen
once.**

### El riesgo cuando llegue `/plan`

**Que E5-12 se marque con una sola señal.** El informe existe porque ninguna de las cuatro predice
nada por separado; bajar el listón a una lo convierte en cuatro alarmas ruidosas que nadie mirará —
y entonces la señal combinada, que sí valía, se pierde entre ellas.
