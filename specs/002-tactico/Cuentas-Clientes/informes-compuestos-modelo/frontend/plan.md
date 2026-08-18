# Implementation Plan: Informes Compuestos de Cuentas y Clientes — Frontend

**Branch**: `002-tactico/Cuentas-Clientes/informes-compuestos-modelo/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (9 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** en **patrón Z**, copiado de Emergencias, Red Operativa, Ventas, Suscripciones, Soporte y Partners. Consumen los nueve informes que el backend publica. **No** se toca el índice de listados (`/cuentas-clientes/informes`), la gestión de cuenta (`/cuentas-clientes/gestion-cuenta`) ni la incorporación operativa.

**La autoridad está partida** (como Suscripciones, no como Partners): dos guards. El Administrador cubre ciclo e incorporación. El Director Tecnológico cubre **solo** Acceso. Un guard unión le daría al Tecnológico el churn.

El envelope trae `data.resultados` y, cuando aplica, `meta.nota_cobertura`, `meta.nota_catalogo` o `meta.nota_solape`. Ocupación y cobertura van en el mismo bloque. El embudo muestra etapas en cero. Ver no habilita a dar de baja ni a cambiar un rol.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe y barras Tailwind (mismo patrón que `partners/gestion` y `suscripciones/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/cuentas/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z más `zona-apoyo`. Pruebas de **exclusión** (Tecnológico fuera de ciclo e incorporación; Cliente/Operador fuera de las tres) y de cobertura, etapa fantasma, vacío ≠ ceros.

**Target Platform**: SPA Angular servida desde nginx en el contenedor `accidentes-frontend`.

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend. Cada zona Z carga en paralelo; un fallo no bloquea las otras. SC-F01: héroe de churn reconocible en <5 s.

**Constraints**: FR-UI-001..022. Máximo 6–8 bloques. Sin identidad, token ni mapas. Período = único filtro global (no editor de `dias_inactividad`, `mes_cohorte` ni `pares_incompatibles` en el MVP).

**Scale/Scope**: 3 pantallas, 9 informes, 1 cáscara Z, 2 guards, 1 servicio, 3 entradas de sidebar.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Justificación |
|---|---|---|
| I. Idoneidad funcional | PASS | Nueve publicados, dos BSC visibles, cobertura/embudo/duración/pares vacíos como el backend. |
| II. Fiabilidad | PASS | Lectura histórica. Fallo de una zona aislado. Vacío ≠ ceros. |
| III. Eficiencia | PASS | Sin cómputo en cliente. |
| IV. Capacidad de interacción | PASS | Núcleo: patrón Z, ≤8 bloques, menú por materia. |
| V. Seguridad | PASS | Dos guards. Token e identidad fuera de pantalla. Tecnológico fuera de ciclo e incorporación. |
| VI. Compatibilidad | N/A | No hay API nueva. |
| VII. Mantenibilidad | PASS | Cáscara Z copiada, módulo propio. No extrae `shared/`. |
| VIII. Flexibilidad | N/A | Sin eje de región. |
| IX. Seguridad operacional | PASS | No hay despacho. Un 100 % de embudo o una ocupación sin cobertura se lee mal; la UI lo impide. |

**Post-Design Gate:** PASS — sin violaciones.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/frontend/
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
frontend/src/app/modules/cuentas-clientes/gestion/
├── cuentas-gestion.routes.ts
├── guards/cuentas-gestion.guard.ts          # dos guards, nunca una unión
├── definiciones/pantallas-gestion.definiciones.ts
├── services/informes-compuestos-api.service.ts
├── models/informes-compuestos.types.ts
├── models/estado-zona.ts
└── pages/
    ├── pantalla-z.page.ts
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts

frontend/src/app/shared/layout/nav-links.ts   # +3 enlaces por materia
frontend/src/app/app.routes.ts                # loadChildren 'cuentas-clientes/gestion'
```

**Prohibido reutilizar:** el índice `/cuentas-clientes/informes` (el Tecnológico entra al índice de listados), `gestion-cuenta`, incorporación operativa, `InformeCardComponent` como grilla, un `canActivate` unión.

**Structure Decision**: carpeta `gestion/` dentro de `modules/cuentas-clientes/`, rutas `/cuentas-clientes/gestion/{ciclo|incorporacion|acceso}`. No se extrae la cáscara Z a `shared/`.

## Complexity Tracking

*Sin violaciones — no aplica.*
