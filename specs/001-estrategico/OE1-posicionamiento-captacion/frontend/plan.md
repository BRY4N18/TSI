# Implementation Plan: OE1 — Posicionamiento y Captación — Frontend

**Branch**: `001-estrategico/OE1-posicionamiento-captacion/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE1-posicionamiento-captacion/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (10 GET publicados, E1-05/07/08 → 404). Esta capa no redefine cifras ni OpenAPI.

---

## Summary

Cuatro pantallas nuevas de **lectura de empresa** en **patrón Z**, **copiado** de `estrategico/oe2/` (no importado; no extraer `shared/`). Consumen
`GET /api/v1/informes-estrategicos/oe1/<informe>`. **No** se tocan los compuestos tácticos de
Suscripciones, Ventas o Cuentas, ni OE2.

**La autoridad está partida** (cuatro guards, nunca una unión):

| Pantalla | Roles |
|---|---|
| Ingreso | `DirectorFinanciero` · `Gerente` |
| Cartera | `DirectorEstrategia` · `Gerente` |
| Captación | `DirectorMarketing` · `Gerente` |
| Ciclo | **solo** `Gerente` |

Un guard unión le daría al Financiero el churn y al Marketing el MRR. El partner **no entra**.
El Administrador no está en §4.1.

Período + granularidad + comparación (`ninguna` | `mom` | `yoy`). Envelope `{ data, meta }`.
No hay `acotado_a`. E1-05/07/08 **no se pintan**. Ver no habilita a cambiar un plan ni a cobrar.

---

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals)

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Número héroe y barras Tailwind
(mismo patrón que OE2).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-estrategicos/oe1/<informe>`

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en zonas Z más
`zona-apoyo`, `zona-parcial`, `zona-comparacion`. Pruebas de **exclusión** (Marketing fuera de
Ingreso; Financiero fuera de Captación y Ciclo; Estrategia fuera de Ingreso y Ciclo; Partner
fuera de las cuatro) y de recuento junto al MRR, ARR extrapolado, ceros de embudo, churn sin %,
vacío ≠ 0 €, sin CAC/mapa.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx)

**Project Type**: Web application (frontend nuevo, backend existente)

**Performance Goals**: Cada zona Z carga en paralelo. SC-F01: héroe de MRR reconocible en <5 s.

**Constraints**: FR-UI-001..024. Máximo 6–8 bloques. Sin mapas, cobro, ficha de prospecto ni
exportar. Período + comparación = únicos filtros. No editor de umbral de muestra.

**Scale/Scope**: 4 pantallas, 10 informes, 1 cáscara Z copiada, 4 guards, 1 servicio, 4
entradas de sidebar en grupo **Estratégico**.

---

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Diez publicados. No inventa CAC ni mercados. Parcial y extrapolación se leen como el backend. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de zona aislado. Vacío ≠ ceros. |
| III. Performance Efficiency | PASS | Sin cómputo de negocio en cliente (no divide precio, no inventa %). |
| IV. Interaction Capability | PASS | Núcleo: Z, ≤8 bloques, menú por materia, comparación. |
| V. Security | PASS | Cuatro guards. Partner 403. Ciclo solo Gerente. Sin cobro/ficha. |
| VI. Compatibility | N/A | No hay API nueva. |
| VII. Maintainability | PASS | Cáscara Z copiada a `oe1/`. No extrae `shared/`. No importa `PantallaZPage` de OE2. |
| VIII. Flexibility | PASS | El objetivo es internacional y **no mide mercados**. Sin eje de país. |
| IX. Safety | PASS | Un MRR de 4 filas como KPI cerrado o un CAC = 0 se impide en UI. No hay despacho. |

**Conflictos:** ninguno. Safety no está en juego de despacho.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE1-posicionamiento-captacion/frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ui-contract.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
frontend/src/app/modules/estrategico/oe1/     # NUEVO — copia de oe2, no import
├── oe1.routes.ts
├── guards/oe1.guard.ts                       # cuatro guards
├── definiciones/pantallas-oe1.definiciones.ts
├── services/informes-oe1-api.service.ts      # GET /informes-estrategicos/oe1/<informe>
├── models/informes-oe1.types.ts
├── models/estado-zona.ts
└── pages/
    ├── pantalla-z.page.ts
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts

frontend/src/app/shared/layout/nav-links.ts   # +4 enlaces grupo Estratégico
frontend/src/app/app.routes.ts                # loadChildren 'estrategico/oe1'
```

**Reutilizado:** selector de fechas + granularidad + comparación ya en OE2 (se copia el
comportamiento, no el módulo).

**Prohibido reutilizar:**

- Importar `PantallaZPage` de `estrategico/oe2` o `partners/gestion`
- Guards de OE2 (Tecnológico/Financiero no son las autoridades de OE1)
- `InformeCardComponent` como grilla
- Pintar `acotado_a`
- Rutas `/suscripciones/*`, `/ventas-crm/*`, `/cuentas-clientes/*` tácticas

**Structure Decision**: módulo `estrategico/oe1/`, rutas
`/estrategico/oe1/{ingreso|cartera|captacion|ciclo}`. Grupo de sidebar **Estratégico** (junto
a OE2, no mezclado con táctico).

No se extrae la cáscara Z a `shared/` en esta pasada.

---

## Complexity Tracking

*Sin violaciones — no aplica.*
