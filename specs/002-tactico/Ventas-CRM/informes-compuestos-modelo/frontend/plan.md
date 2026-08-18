# Implementation Plan: Informes Compuestos de Ventas y CRM — Frontend

**Branch**: `002-tactico/Ventas-CRM/informes-compuestos-modelo/frontend` | **Date**: 2026-08-17 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (13 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** en **patrón Z**, copiado de Emergencias y Red Operativa.
Consumen los trece informes que el backend publica. **No** se toca el índice de listados
(`/ventas-crm/informes`) ni el pipeline operativo.

La diferencia que no se copia: **acotamiento por titularidad**. El Director de Marketing y el
Gerente de Ventas ven las **mismas** tres historias; `meta.acotado_a` (`todos` | `propios`) viaja
visible junto al período. Un guard de unión con `GerenteCuentasPublicas` (el de los listados)
metería a quien el backend de compuestos **no** admite.

Una cáscara de layout Z + tres definiciones. Sin librería de gráficas. El período es el único
filtro; pesos del pipeline y la nota del CAC se **muestran** tal como vienen en `meta`, no se
editan.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe, barras de distribución Tailwind (mismo patrón que `emergencias/gestion` y `red-operativa/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/ventas-crm/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z más `zona-alcance`. Pruebas de **exclusión** (Cuentas Públicas / Operador no entran) y de que el alcance se pinta desde `meta.acotado_a`, no desde el rol adivinado en cliente.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend. La pantalla no agrega. Cada zona Z carga en paralelo; un fallo no bloquea las otras. SC-F01: héroe reconocible en <5 s.

**Constraints**: FR-UI-001..022. Máximo 6–8 bloques. Sin mapas. Sin exportar. Ver no habilita a decidir. Dato personal excluido también para el Director. Período = único filtro (no editor de `pesos_etapa`).

**Scale/Scope**: 3 pantallas, 13 informes, 1 cáscara Z, 1 guard, 1 servicio, 3 entradas de sidebar.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y los 13 publicados. No inventa métricas ni un CAC. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de una zona aislado. Vacío ≠ ceros. OT03 vacío de entorno se pinta como vacío. |
| III. Performance Efficiency | PASS | Flujo analítico, no despacho. Sin cómputo en cliente. |
| IV. Interaction Capability | PASS | Núcleo: patrón Z, ≤8 bloques, héroe en <5 s, alcance visible (SC-F01, SC-F09). |
| V. Security | PASS | Guard DirectorMarketing \| GerenteVentas \| Administrador. Sin Cuentas Públicas. Exclusión constitucional en pantalla. |
| VI. Compatibility | N/A | No hay API nueva ni partner. |
| VII. Maintainability | PASS | Cáscara Z + catálogo de definiciones, espejo de los dos departamentos anteriores, módulo propio. No extrae `shared/` (fuera de alcance tocar Emergencias/Red Operativa). |
| VIII. Flexibility | N/A | Canal y etapa por nombre; sin eje de región. |
| IX. Safety | PASS | No hay cadena de despacho. Safety se limita a no inducir decisión comercial falsa: CAC parcial declarado, aviso ignorado fuera de la mediana, vacío ≠ 0 % de nutrición. |

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/frontend/
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
frontend/src/app/modules/ventas-crm/gestion/       # NUEVO — no es listado ni pipeline
├── ventas-crm-gestion.routes.ts
├── guards/
│   └── ventas-crm-gestion.guard.ts                # DirectorMarketing | GerenteVentas | Administrador
├── definiciones/
│   └── pantallas-gestion.definiciones.ts          # las tres historias → zonas Z → informes
├── services/
│   └── informes-compuestos-api.service.ts         # GET /informes-tacticos/ventas-crm/<informe>
├── models/
│   └── informes-compuestos.types.ts               # incluye meta.acotado_a
└── pages/
    ├── pantalla-z.page.ts                         # UNA página, parametrizada por definición
    ├── pantalla-z.page.html                       # las cuatro zonas Z + alcance
    └── apoyo-plegable.component.ts                # carga/pipeline y reglas de disparo

frontend/src/app/shared/layout/nav-links.ts        # +3 enlaces (no los de /ventas-crm/informes)
frontend/src/app/app.routes.ts                     # loadChildren 'ventas-crm/gestion'
```

**Reutilizado, no copiado de layout:** el selector de período de los workpanels / gestión ya
existente (control de fechas). **Prohibido reutilizar** la grilla de `InformeCardComponent` y el
tablero `/ventas-crm/pipeline`: eso **es** la operación diaria, no esta lectura.

**Structure Decision**: carpeta `gestion/` dentro de `modules/ventas-crm/`, rutas
`/ventas-crm/gestion/{embudo|captacion|nutricion}`. El prefijo `/ventas-crm/informes/` ya es de
los listados simples (admite `GerenteCuentasPublicas`). Fusionarlos mezclaría dos productos y
abriría compuestos a quien el backend rechaza.

## Complexity Tracking

*Sin violaciones — no aplica.*
