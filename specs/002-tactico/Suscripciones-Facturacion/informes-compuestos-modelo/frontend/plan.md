# Implementation Plan: Informes Compuestos de Suscripciones y Facturación — Frontend

**Branch**: `002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/frontend` | **Date**: 2026-08-17 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (13 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** en **patrón Z**, copiado de Emergencias, Red Operativa y Ventas.
Consumen los trece informes que el backend publica. **No** se toca el índice de listados
(`/suscripciones/informes`) ni el catálogo de planes, ni los flujos de cobro del cliente.

La diferencia que no se copia de Ventas: **no hay un solo jefe**. Como en Red Operativa, dos guards
(finanzas / catálogo), tres enlaces de sidebar con roles distintos. Un tablero único de departamento
anularía FR-UI-025 y el backend FR-038 / FR-039.

Una cáscara de layout Z + tres definiciones. Sin librería de gráficas. El período es el único filtro;
escalones de dunning y días de aviso se **muestran** tal como vienen en `meta.filtros`, no se
editan. MRR y NRR declaran `meta.mes` y `meta.nota_periodo`.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe, barras de distribución Tailwind (mismo patrón que `emergencias/gestion`, `red-operativa/gestion` y `ventas-crm/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/suscripciones/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z más `zona-mes` cuando aplica. Pruebas de **exclusión cruzada** (Financiero no ve catálogo; Estrategia no ve cobro/movimientos) — un permiso de unión pasaría si solo se comprueba que cada uno entra a la suya.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend. La pantalla no agrega. Cada zona Z carga en paralelo; un fallo no bloquea las otras. SC-F01 / SC-F02: héroe reconocible en <5 s.

**Constraints**: FR-UI-001..025. Máximo 6–8 bloques. Sin mapas. Sin exportar. Ver no habilita a cobrar, emitir ni cambiar plan. Dato sensible excluido también para el director de esa materia. Sidebar por rol: sin ítems grises de la materia ajena. Sin columna de llamadas, ni vacía.

**Scale/Scope**: 3 pantallas, 13 informes, 1 cáscara Z, 2 guards, 1 servicio, 3 entradas de sidebar (2+1 roles).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y los 13 publicados. No inventa métricas ni consumo de API. Agrupa por materia, no por OT. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de una zona aislado. Vacío ≠ ceros. |
| III. Performance Efficiency | PASS | Flujo analítico, no despacho. Sin cómputo en cliente (no mensualiza, no deriva vigencia). |
| IV. Interaction Capability | PASS | Núcleo: patrón Z, ≤8 bloques, héroe en <5 s, menú por materia (SC-F01, SC-F03). |
| V. Security | PASS | Dos guards, no una unión. Exclusión constitucional en pantalla (medio de cobro, fiscal, quién resolvió). Cliente/Proveedor no entran. |
| VI. Compatibility | N/A | No hay API nueva ni partner. |
| VII. Maintainability | PASS | Cáscara Z + catálogo de definiciones, espejo de los tres departamentos anteriores, módulo propio. No extrae `shared/` (fuera de alcance tocar Emergencias / Red Operativa / Ventas). |
| VIII. Flexibility | N/A | Plan y tipo de cliente por nombre; sin eje de región. |
| IX. Safety | PASS | No hay cadena de despacho. Safety se limita a no inducir decisión financiera falsa: cancelada fuera del MRR, notas restan, pendiente fuera de la mediana, llamadas no se pintan, vacío ≠ 0 %. |

**Conflictos entre características:** ninguno identificado. Safety no está en juego de despacho; no se invoca el Tie-Breaker.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/frontend/
├── spec.md
├── plan.md              # este archivo
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui-contract.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
frontend/src/app/modules/suscripciones/gestion/    # NUEVO — no es listado, catálogo ni billing
├── suscripciones-gestion.routes.ts
├── guards/
│   └── suscripciones-gestion.guard.ts             # DOS funciones: finanzas | catalogo
├── definiciones/
│   └── pantallas-gestion.definiciones.ts          # las tres historias → zonas Z → informes
├── services/
│   └── informes-compuestos-api.service.ts         # GET …/suscripciones/<informe>
├── models/
│   └── informes-compuestos.types.ts               # Envelope + meta.mes / nota_periodo
└── pages/
    ├── pantalla-z.page.ts                         # UNA página, parametrizada por definición
    ├── pantalla-z.page.html                       # las cuatro zonas Z + mes natural
    └── apoyo-plegable.component.ts                # US1: tres de segundo plano; US2: uno

frontend/src/app/shared/layout/nav-links.ts        # +3 enlaces con roles DISTINTOS
frontend/src/app/app.routes.ts                     # loadChildren 'suscripciones/gestion'
```

**Reutilizado:** selector de período ya usado en las gestiones anteriores (control de fechas).

**Prohibido reutilizar:**

- `InformeCardComponent` como grilla (anti-Z).
- El índice / guards de `suscripciones/informes/` (admiten Cliente y Proveedor; mezclan listados).
- Un único `canActivate` con la unión `DirectorFinanciero | DirectorEstrategia`.
- Las pantallas de `catalogo-planes`, `metodos-pago`, `historial-facturas` o `aprobaciones-downgrade`
  como cáscara de estos informes.

**Structure Decision**: carpeta `gestion/` dentro de `modules/suscripciones/`, rutas
`/suscripciones/gestion/{cobro|movimientos|catalogo}`. El prefijo `/suscripciones/informes/` ya es
de los listados (roles y producto distintos). Fusionarlos mezclaría al cliente que ve su deuda con
la lectura de cartera, y a los dos directores entre sí.

No se extrae la cáscara Z a `shared/` en esta pasada: tocar tres módulos ya verdes para un ahorro
que no es de esta capa viola el Out of Scope. Se copia el patrón; una extracción se evalúa en una
spec de refactor.

## Complexity Tracking

*Sin violaciones — no aplica.*
