# Implementation Plan: Informes Compuestos de Partners y API — Frontend

**Branch**: `002-tactico/Partners-API/informes-compuestos-modelo/frontend` | **Date**: 2026-08-17 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Partners-API/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (13 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** en **patrón Z**, copiado de Emergencias, Red Operativa, Ventas,
Suscripciones y Soporte. Consumen los trece informes que el backend publica. **No** se toca el
índice de listados (`/partners/informes`), la consola (`/partners/consola/*`), el portal del partner
ni las **métricas y el reporte mensual operativos**.

La diferencia que no se copia de Soporte: **no hay `meta.acotado_a`**. El partner **no entra**; no
hay cifra «propios» que declarar. Un guard de listados (admite `DesarrolladorAPIs` y
`PartnerIntegracion`) metería a quien el backend de compuestos responde 403.

La diferencia que no se copia de Suscripciones: **la autoridad no está partida**. Un solo guard
(`DirectorTecnologico` | `Administrador`) para las tres historias.

El envelope trae `data.resultados` y, cuando aplica, `meta.nota_muestras`. El trío
p95 / media / muestras es un solo bloque. Ver no habilita a revocar, suspender ni cambiar un cupo.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe, barras de distribución Tailwind (mismo patrón que `emergencias/gestion`, `red-operativa/gestion`, `ventas-crm/gestion`, `suscripciones/gestion` y `soporte-cliente/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/partners/<informe>`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z más
`zona-apoyo` y `zona-nota-muestras` cuando aplica. Pruebas de **exclusión** (Partner /
`DesarrolladorAPIs` / Operador no entran) y de que el héroe de Consumo muestra **las tres** cifras
del trío. Prueba de que p95 no fiable **no oculta** la fila.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend. La pantalla no agrega. Cada zona Z carga en
paralelo; un fallo no bloquea las otras. SC-F01: héroe reconocible en <5 s.

**Constraints**: FR-UI-001..026. Máximo 6–8 bloques. Sin mapas. Sin exportar. Ver no habilita a
decidir. IP, secreto, contacto y ejecutor excluidos también para el Director. Período = único
filtro global (no editor de `percentil`, `muestra_minima`, `mes` ni `dias_aviso_expiracion`).

**Scale/Scope**: 3 pantallas, 13 informes, 1 cáscara Z, 1 guard, 1 servicio, 3 entradas de sidebar.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y los 13 publicados. No inventa alcance geográfico ni suma clases de error. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de una zona aislado. Vacío ≠ ceros. Fila no fiable visible. |
| III. Performance Efficiency | PASS | Flujo analítico, no despacho. Sin cómputo en cliente (no suma 429+403+5xx, no colapsa `'v1'`). |
| IV. Interaction Capability | PASS | Núcleo: patrón Z, ≤8 bloques, trío p95/media/muestras inseparable, menú por rol (SC-F01, SC-F02). |
| V. Security | PASS | Guard DirectorTecnologico \| Administrador. Sin Partner ni DesarrolladorAPIs. Exclusión constitucional en pantalla. |
| VI. Compatibility | N/A | No hay API nueva. |
| VII. Maintainability | PASS | Cáscara Z + catálogo de definiciones, espejo de los cinco departamentos anteriores, módulo propio. No extrae `shared/` (fuera de alcance tocar módulos verdes). |
| VIII. Flexibility | N/A | Sin eje de región; el alcance geográfico está fuera y se declara. |
| IX. Safety | PASS | No hay cadena de despacho. Safety se limita a no inducir decisión de plataforma falsa: p95 sin muestras prohibido, 100 % sobre quienes ya integran prohibido, 429 ≠ 5xx, vacío ≠ ceros. |

**Conflictos entre características:** ninguno identificado. Safety no está en juego de despacho; no se invoca el Tie-Breaker.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Partners-API/informes-compuestos-modelo/frontend/
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
frontend/src/app/modules/partners/gestion/          # NUEVO — no es listado, consola ni portal
├── partners-gestion.routes.ts
├── guards/
│   └── partners-gestion.guard.ts                   # DirectorTecnologico | Administrador
├── definiciones/
│   └── pantallas-gestion.definiciones.ts           # las tres historias → zonas Z → informes
├── services/
│   └── informes-compuestos-api.service.ts          # GET /informes-tacticos/partners/<informe>
├── models/
│   └── informes-compuestos.types.ts                # Envelope { resultados } + meta.nota_muestras
└── pages/
    ├── pantalla-z.page.ts                          # UNA página, parametrizada por definición
    ├── pantalla-z.page.html                        # las cuatro zonas Z + nota_muestras
    └── apoyo-plegable.component.ts                 # US1: cuatro de segundo plano; US2: uno

frontend/src/app/shared/layout/nav-links.ts         # +3 enlaces (no los de /informes, /consola, /portal)
frontend/src/app/app.routes.ts                      # loadChildren 'partners/gestion'
```

**Reutilizado:** selector de período ya usado en las gestiones anteriores (control de fechas).

**Prohibido reutilizar:**

- `InformeCardComponent` como grilla (anti-Z).
- El índice / guards de `partners/informes/` (admite `DesarrolladorAPIs` y `PartnerIntegracion`).
- Rutas o cáscaras de `partners/consola` (logs, reportes, excepciones) o `partners/portal`.
- Un `canActivate` que una `DesarrolladorAPIs` «porque es del departamento».

**Structure Decision**: carpeta `gestion/` dentro de `modules/partners/`, rutas
`/partners/gestion/{consumo|incorporacion|entrega}`. El prefijo `/partners/informes/` ya es de los
listados (el Partner entra). `/partners/consola/reportes` y `/partners/portal/consumo` son el
operativo (solo media). Fusionarlos mezclaría dos productos y anularía el trío p95/media/muestras.

No se extrae la cáscara Z a `shared/` en esta pasada: tocar cinco módulos ya verdes para un
ahorro que no es de esta capa viola el Out of Scope. Se copia el patrón; una extracción se evalúa
en una spec de refactor.

## Complexity Tracking

*Sin violaciones — no aplica.*
