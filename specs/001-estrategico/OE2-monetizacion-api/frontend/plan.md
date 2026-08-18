# Implementation Plan: OE2 — Monetización de APIs — Frontend

**Branch**: `001-estrategico/OE2-monetizacion-api/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE2-monetizacion-api/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (10 GET publicados, E2-06 → 404). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **lectura de empresa** en **patrón Z**, copiado de `partners/gestion` (y Cuentas, no extraído a `shared/`). Consumen los diez informes de
`GET /api/v1/informes-estrategicos/oe2/<informe>`. **No** se toca `/partners/gestion/*`, el portal del partner ni la consola.

**La autoridad está partida** (como Cuentas, no como Partners táctico): dos guards. Uso y Ecosistema = `DirectorTecnologico` | `Gerente`. Dinero = esos **más** `DirectorFinanciero`. Un guard unión le daría al Financiero la latencia de todos. El partner **no entra**.

A diferencia del táctico, hay **período + granularidad + comparación** (`ninguna` | `mom` | `yoy`). El envelope es `{ data, meta }` con `cobertura`, `falta` y `alcance`. No hay `acotado_a`. E2-06 **no se pinta**. Ver no habilita a facturar ni a retirar una versión.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe y barras Tailwind (mismo patrón que `partners/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-estrategicos/oe2/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z más `zona-apoyo`, `zona-parcial` y `zona-comparacion`. Pruebas de **exclusión** (Partner fuera de las tres; Financiero fuera de Uso y Ecosistema) y de trío p95, parcial, facturable≠cobrado, (servicio, versión), vacío ≠ 0 ms.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente). Primera carpeta de la capa estratégica en el SPA.

**Performance Goals**: Heredados del backend. Cada zona Z carga en paralelo; un fallo no bloquea las otras. SC-F01: héroe de adopción reconocible en <5 s.

**Constraints**: FR-UI-001..028. Máximo 6–8 bloques. Sin mapas, IP, secreto ni exportar. Período + comparación = únicos filtros. No editor de `muestra_minima`.

**Scale/Scope**: 3 pantallas, 10 informes, 1 cáscara Z, 2 guards, 1 servicio, 3 entradas de sidebar en grupo **Estratégico**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Diez publicados. No inventa disponibilidad. Parcial y facturable se leen como el backend. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de zona aislado. Vacío ≠ ceros. Comparación ausente con motivo. |
| III. Performance Efficiency | PASS | Sin cómputo en cliente (no suma 4xx+5xx, no colapsa `'v1'`). |
| IV. Interaction Capability | PASS | Núcleo: Z, ≤8 bloques, trío inseparable, menú por materia, comparación. |
| V. Security | PASS | Dos guards. Partner 403. Sin IP/secreto en pantalla. |
| VI. Compatibility | N/A | No hay API nueva. |
| VII. Maintainability | PASS | Cáscara Z copiada a módulo propio. No extrae `shared/`. |
| VIII. Flexibility | N/A | Sin eje de región. El ecosistema se muestra; no se infiere geografía. |
| IX. Safety | PASS | No hay despacho. Un p95 de 2 muestras o un 100 % de uptime fingido se impide en UI. |

**Conflictos:** ninguno. Safety no está en juego de despacho.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE2-monetizacion-api/frontend/
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
frontend/src/app/modules/estrategico/oe2/     # NUEVO — primera carpeta estratégica
├── oe2.routes.ts
├── guards/oe2.guard.ts                       # dos guards, nunca una unión
├── definiciones/pantallas-oe2.definiciones.ts
├── services/informes-oe2-api.service.ts      # GET /informes-estrategicos/oe2/<informe>
├── models/informes-oe2.types.ts              # Envelope { data, meta }
├── models/estado-zona.ts
└── pages/
    ├── pantalla-z.page.ts                    # UNA página, parametrizada
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts

frontend/src/app/shared/layout/nav-links.ts   # +3 enlaces grupo Estratégico
frontend/src/app/app.routes.ts                # loadChildren 'estrategico/oe2'
```

**Reutilizado:** selector de fechas ya usado en gestiones tácticas, **más** granularidad y comparación (no existen en táctico).

**Prohibido reutilizar:**

- Importar `PantallaZPage` de `partners/gestion` (acoplamiento entre capas).
- Guards de `/partners/gestion` (admiten `Administrador`; el Financiero no entra al táctico).
- `InformeCardComponent` como grilla (anti-Z).
- Pintar `acotado_a` (el envelope estratégico no lo envía).

**Structure Decision**: módulo `estrategico/oe2/`, rutas `/estrategico/oe2/{uso|dinero|ecosistema}`. No colgar de `/partners/gestion/`: esa carpeta es táctica y el Partner ya sabe que existe. Un grupo de sidebar **Estratégico** evita mezclar p95 táctico con p95 de empresa.

No se extrae la cáscara Z a `shared/` en esta pasada.

## Complexity Tracking

*Sin violaciones — no aplica.*
