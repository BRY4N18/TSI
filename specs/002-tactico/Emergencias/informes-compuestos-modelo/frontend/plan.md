# Implementation Plan: Informes Compuestos de Emergencias — Frontend

**Branch**: `002-tactico/Emergencias/informes-compuestos-modelo/frontend` | **Date**: 2026-08-16 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Emergencias/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (13 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** para el Director de Operaciones (y el Administrador), cada una
en **patrón Z**. Consumen solo los trece informes que el backend publica. **No** se toca el workpanel
de Registro / Despacho / Seguimiento (`/emergencias/informes/*`).

Una cáscara de layout Z + tres definiciones. Sin librería de gráficas (el proyecto no tiene ninguna).
Un guard distinto al de los workpanels: el Operador **no** entra.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts (`package.json` no tiene ngx-charts / Chart.js / D3). Visuales: número héroe, barras de distribución Tailwind (patrón `toDist` de Soporte / workpanels), tendencia como barras por período.

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/emergencias/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend (SC-009: al menos tres meses). La pantalla no agrega. Cada zona Z carga en paralelo; un fallo no bloquea las otras.

**Constraints**: FR-UI-001..016. Máximo 6–8 bloques (design-system). Sin mapas. Sin exportar. Ver no habilita a decidir. Dato sensible excluido también para el Director.

**Scale/Scope**: 3 pantallas, 13 informes, 1 cáscara Z, 1 guard, 1 servicio, 3 entradas de sidebar.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y los 13 publicados del backend. No inventa métricas. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de una zona aislado (FR-UI zona independiente). Vacío ≠ ceros. |
| III. Performance Efficiency | PASS | Flujo analítico, no despacho. Sin cómputo en cliente. |
| IV. Interaction Capability | PASS | Núcleo: patrón Z, ≤8 bloques, héroe en <5 s (SC-F01). |
| V. Security | PASS | Guard DirectorOperaciones \| Administrador. Exclusión constitucional en pantalla. |
| VI. Compatibility | N/A | No hay API nueva ni partner. |
| VII. Maintainability | PASS | Cáscara Z + catálogo de definiciones. Red Operativa copia el patrón. |
| VIII. Flexibility | N/A | Sin eje de región; ubicación por nombre. |
| IX. Safety | PASS | Completitud que baja del 100 % y «sin capacidad» visibles; no se pintan como 0. |

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Emergencias/informes-compuestos-modelo/frontend/
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
frontend/src/app/modules/emergencias/gestion/     # NUEVO — no es workpanel ni listado
├── emergencias-gestion.routes.ts
├── guards/
│   └── emergencias-gestion.guard.ts              # DirectorOperaciones | Administrador
├── definiciones/
│   └── pantallas-gestion.definiciones.ts         # las tres historias → zonas Z → informes
├── services/
│   └── informes-compuestos-api.service.ts        # GET parametrizado por nombre de informe
├── models/
│   └── informes-compuestos.types.ts
└── pages/
    ├── pantalla-z.page.ts                        # UNA página, parametrizada por definición
    └── pantalla-z.page.html                      # las cuatro zonas Z
    └── apoyo-plegable.component.ts               # US3: los cuatro de segundo plano

frontend/src/app/shared/layout/nav-links.ts       # +3 enlaces (no los de workpanel)
frontend/src/app/app.routes.ts                    # loadChildren 'emergencias/gestion'
```

**Reutilizado, no copiado de layout:** `pages/shared/periodo-selector` de los workpanels (control de
fechas). **Prohibido reutilizar** `InformeCardComponent` como grilla de tarjetas: eso **es** el
tablero que la spec ignora.

**Structure Decision**: carpeta `gestion/` dentro de `modules/emergencias/`, rutas
`/emergencias/gestion/{calidad|despacho|cierre}`. El prefijo `/emergencias/informes/` ya es de los
workpanels (roles distintos). Fusionarlos mezclaría al Operador con la lectura de gestión.

## Complexity Tracking

*Sin violaciones — no aplica.*
