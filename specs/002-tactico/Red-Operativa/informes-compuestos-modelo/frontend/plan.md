# Implementation Plan: Informes Compuestos de Red Operativa — Frontend

**Branch**: `002-tactico/Red-Operativa/informes-compuestos-modelo/frontend` | **Date**: 2026-08-16 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (15 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** en **patrón Z**, copiado de Emergencias. Consumen los quince
informes que el backend publica. **No** se toca el índice de listados.

La diferencia que no se copia: **no hay un solo jefe**. Dos guards (crecimiento / validación), tres
enlaces de sidebar con roles distintos. Un tablero único de departamento anularía FR-025.

Una cáscara de layout Z + tres definiciones. Sin librería de gráficas. El período es el único filtro;
umbrales y objetivos se **muestran** tal como vienen en `meta.filtros` y las notas, no se editan.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe, barras de distribución Tailwind (mismo patrón que `emergencias/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/red-operativa/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z. Pruebas de **exclusión cruzada** (Expansión no ve validación; Tecnológico no ve flota/mercados) — un permiso de unión pasaría si solo se comprueba que cada uno entra a la suya.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend. La pantalla no agrega. Cada zona Z carga en paralelo; un fallo no bloquea las otras.

**Constraints**: FR-UI-001..020. Máximo 6–8 bloques. Sin mapas. Sin exportar. Ver no habilita a decidir. Dato sensible excluido también para el director de esa materia. Sidebar por rol: sin ítems grises de la materia ajena.

**Scale/Scope**: 3 pantallas, 15 informes, 1 cáscara Z, 2 guards, 1 servicio, 3 entradas de sidebar (2+1 roles).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y los 15 publicados. No inventa métricas. Agrupa por materia, no por OT. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de una zona aislado. Vacío ≠ ceros. |
| III. Performance Efficiency | PASS | Flujo analítico, no despacho. Sin cómputo en cliente. |
| IV. Interaction Capability | PASS | Núcleo: patrón Z, ≤8 bloques, héroe en <5 s, menú por materia (SC-F01, SC-F03). |
| V. Security | PASS | Dos guards, no una unión. Exclusión constitucional en pantalla (validador, coordenadas, contacto). |
| VI. Compatibility | N/A | No hay API nueva ni partner. |
| VII. Maintainability | PASS | Cáscara Z + catálogo de definiciones, espejo de Emergencias, módulo propio. |
| VIII. Flexibility | N/A | Ubicación por nombre; cobertura por región declara el hueco #38. |
| IX. Safety | PASS | Ausente ≠ 0 %; sin alternativas visible; `medida_exacta_desde` junto al vacío de despublicación. |

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Red-Operativa/informes-compuestos-modelo/frontend/
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
frontend/src/app/modules/red-operativa/gestion/    # NUEVO — no es el índice de listados
├── red-operativa-gestion.routes.ts
├── guards/
│   └── red-operativa-gestion.guard.ts             # DOS funciones: crecimiento | validación
├── definiciones/
│   └── pantallas-gestion.definiciones.ts          # las tres historias → zonas Z → informes
├── services/
│   └── informes-compuestos-api.service.ts         # GET …/red-operativa/<informe>
├── models/
│   └── informes-compuestos.types.ts               # Envelope + medida_exacta_desde
└── pages/
    ├── pantalla-z.page.ts                         # UNA página, parametrizada por definición
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts                # US1: cinco de segundo plano; US2: dos

frontend/src/app/shared/layout/nav-links.ts        # +3 enlaces con roles DISTINTOS
frontend/src/app/app.routes.ts                     # loadChildren 'red-operativa/gestion'
```

**Reutilizado:** selector de período de Emergencias (`periodo-selector`), si ya es compartido; si
vive dentro de workpanels, copiar el control, no el tablero.

**Prohibido reutilizar:**

- `InformeCardComponent` como grilla (anti-Z).
- El índice / guards de `red-operativa/informes/` (admiten Cliente/Proveedor en flota).
- Un único `canActivate` con la unión `DirectorExpansion | DirectorTecnologico`.

**Structure Decision**: carpeta `gestion/` dentro de `modules/red-operativa/`, rutas
`/red-operativa/gestion/{flota|mercados|validacion}`. El prefijo `/red-operativa/informes/` ya es de
los listados (roles y producto distintos). Fusionarlos mezclaría al proveedor con la lectura de
gestión y a los dos directores entre sí.

No se extrae la cáscara Z a `shared/` en esta pasada: tocar Emergencias para compartir layout es
riesgo sin beneficio de producto. Se copia el patrón; una extracción se evalúa cuando haya un
tercer departamento.

## Complexity Tracking

*Sin violaciones — no aplica.*
