# Specification Quality Checklist: OE2 — Monetización del Ecosistema de APIs

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
- [x] **Ready for `/speckit-plan`** — sustrato de Partners cargado (2026-08-18)

**16 / 16.**

---

## Notas

### Lo que se pudo verificar sin el modelo analítico

| Verificado | Resultado |
|---|---|
| Volumen del consumo | **18 llamadas** en `Fact_LogLlamadaAPI`, 40 en el agregado |
| ¿`Dim_Partner.planapi` tiene precio? | **No** → E2-01 y E2-02 parciales, confirmado |
| ¿Existe precio de excedente? | **Sí**, `Dim_Plan.precio_excedente_llamada` → **E2-08 se desbloquea** |
| Nombre del hecho que se construirá | `hecho_llamada_api`, uno solo, del `data-model.md` táctico |

### La corrección al catálogo que salió sin datos analíticos

El catálogo agrupa E2-01, E2-02 **y E2-08** como dependientes del precio del plan de API. **E2-08 no
lo es**: se calcula con `limitellamadasmes` del partner y `precio_excedente_llamada` del plan, y las
dos columnas existen.

Importa porque **E2-08 es el informe con consecuencia económica más directa del objetivo** —es lo que
se cobra de más— y estaba clasificado como bloqueado sin serlo.

### La segunda corrección: el catálogo nombra dos hechos y habrá uno

`hecho_log_llamada_api` y `hecho_api_integracion` en el catálogo; `hecho_llamada_api` en el diseño
táctico. Y es deliberado: el propio catálogo dice que *«en el modelo analítico manda el detalle»*,
porque es el único que permite p95 y taxonomía de errores.

### Un requisito que no es de dato sensible sino de alcance competitivo

**FR-OE2-007: ningún partner accede a estos informes.** No es una exclusión de dato personal — es que
un informe estratégico agrega **todo el ecosistema**, y dárselo a un partner le mostraría el consumo
de sus competidores.

El partner ya tiene su panel propio, acotado a él, construido en la capa operativa. La distinción
entre «tu consumo» y «el consumo del ecosistema» es la misma que separa una pantalla operativa de un
informe estratégico, y aquí tiene consecuencia comercial.

### El riesgo que `/plan` cierra por diseño

**Que E2-06 se derive del log de llamadas.** El plan no publica la ruta: un GET a
`disponibilidad-api` es 404. Si el servicio estuvo caído no hay filas; publicar 100 % mentiría.

### Lo mejor de este módulo

**Dependencia de un solo departamento**, ya construida. `/plan` cierra el recuento: 10 publicados,
E2-06 sin endpoint, E2-01/E2-02 parciales, E2-08 construible.
