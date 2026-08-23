# Implementation Plan: OE5 — Retención y Ciclo de Vida — Frontend

**Branch**: `001-estrategico/OE5-retencion-ciclo-vida/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE5-retencion-ciclo-vida/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (9 GET publicados; E5-01/11 y refs OE1 → 404). Esta capa no redefine cifras ni OpenAPI.

---

## Summary

Cuatro pantallas nuevas de **lectura de empresa** en **patrón Z**, **copiado** de `estrategico/oe1/` (no importado; no extraer `shared/`). Consumen
`GET /api/v1/informes-estrategicos/oe5/<informe>`. **No** se tocan los compuestos tácticos de
Soporte, Suscripciones o Cuentas, ni OE1/OE2.

**La autoridad está partida** (cuatro guards, nunca una unión):

| Pantalla | Roles |
|---|---|
| Servicio | `GerenteExitoCliente` · `Gerente` |
| Ingresos retenidos | `DirectorFinanciero` · `Gerente` |
| Planes | `DirectorEstrategia` · `Gerente` |
| Riesgo | **solo** `Gerente` |

Un guard unión le daría al Financiero las cuentas en riesgo y al Éxito de Cliente el NRR. El
partner **no entra**. El Administrador no está en §4.5.

Período + granularidad + comparación (`ninguna` | `mom` | `yoy`). Envelope `{ data, meta }`.
No hay `acotado_a`. E5-01/11 y E5-09/10/13/14 **no se pintan**. Ver no habilita a reabrir un
ticket ni a cambiar un plan.

---

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals)

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Número héroe y barras Tailwind
(mismo patrón que OE1).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-estrategicos/oe5/<informe>`

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en zonas Z más
`zona-apoyo`, `zona-parcial`, `zona-comparacion`. Pruebas de **exclusión** (Financiero fuera de
Servicio y Riesgo; Éxito de Cliente fuera de Ingresos y Planes; Estrategia fuera de Servicio e
Ingresos; Partner fuera de las cuatro) y de recuento junto al SLA, vacío ≠ 0 %, NRR descompuesto,
una señal ≠ riesgo, sin NPS/ciclo OE1.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx)

**Project Type**: Web application (frontend nuevo, backend existente)

**Performance Goals**: Cada zona Z carga en paralelo. SC-F01: héroe de SLA reconocible en <5 s.

**Constraints**: FR-UI-001..023. Máximo 6–8 bloques. Sin texto de ticket, cobro, ficha ni
exportar. Período + comparación = únicos filtros. No editor de umbral de muestra.

**Scale/Scope**: 4 pantallas, 9 informes, 1 cáscara Z copiada, 4 guards, 1 servicio, 4
entradas de sidebar en grupo **Estratégico**.

---

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Nueve publicados. No inventa NPS ni reportes. Parcial, vacío y ≥2 señales se leen como el backend. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de zona aislado. Vacío ≠ 0 %. |
| III. Performance Efficiency | PASS | Sin cómputo de negocio en cliente (no inventa NPS, no marca riesgo con una señal). |
| IV. Interaction Capability | PASS | Núcleo: Z, ≤8 bloques, menú por materia, comparación. |
| V. Security | PASS | Cuatro guards. Partner 403. Riesgo solo Gerente. Sin prosa de ticket. |
| VI. Compatibility | N/A | No hay API nueva. |
| VII. Maintainability | PASS | Cáscara Z copiada a `oe5/`. No extrae `shared/`. No importa `PantallaZPage` de OE1. |
| VIII. Flexibility | PASS | El objetivo mide retención, no geografía. Sin eje de país. |
| IX. Safety | PASS | Un SLA de 14 filas como KPI cerrado, un 0 % fingido o un NPS = 0 se impide en UI. No hay despacho. |

**Conflictos:** ninguno. Safety no está en juego de despacho.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE5-retencion-ciclo-vida/frontend/
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
frontend/src/app/modules/estrategico/oe5/     # NUEVO — copia de oe1, no import
├── oe5.routes.ts
├── guards/oe5.guard.ts                       # cuatro guards
├── definiciones/pantallas-oe5.definiciones.ts
├── services/informes-oe5-api.service.ts      # GET /informes-estrategicos/oe5/<informe>
├── models/informes-oe5.types.ts
├── models/estado-zona.ts
└── pages/
    ├── pantalla-z.page.ts
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts

frontend/src/app/shared/layout/nav-links.ts   # +4 enlaces grupo Estratégico
frontend/src/app/app.routes.ts                # loadChildren 'estrategico/oe5'
```

**Reutilizado:** selector de fechas + granularidad + comparación ya en OE1 (se copia el
comportamiento, no el módulo).

**Prohibido reutilizar:**

- Importar `PantallaZPage` de `estrategico/oe1`, `estrategico/oe2` o `partners/gestion`
- Guards de OE1 (Financiero/Marketing no son las autoridades de OE5)
- `InformeCardComponent` como grilla
- Pintar `acotado_a`
- Rutas `/soporte-cliente/*`, `/suscripciones/*`, `/cuentas-clientes/*` tácticas
- Recuadros de `/estrategico/oe1/ciclo`

**Structure Decision**: módulo `estrategico/oe5/`, rutas
`/estrategico/oe5/{servicio|ingresos|planes|riesgo}`. Grupo de sidebar **Estratégico** (junto
a OE1/OE2, no mezclado con táctico).

No se extrae la cáscara Z a `shared/` en esta pasada.

---

## Complexity Tracking

*Sin violaciones — no aplica.*
