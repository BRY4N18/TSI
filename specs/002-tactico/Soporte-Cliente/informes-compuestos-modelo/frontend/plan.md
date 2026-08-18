# Implementation Plan: Informes Compuestos de Soporte al Cliente — Frontend

**Branch**: `002-tactico/Soporte-Cliente/informes-compuestos-modelo/frontend` | **Date**: 2026-08-17 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (9 endpoints publicados). Esta capa no redefine cifras ni OpenAPI.

## Summary

Tres pantallas nuevas de **gestión** en **patrón Z**, copiado de Emergencias, Red Operativa, Ventas
y Suscripciones. Consumen los nueve informes que el backend publica. **No** se toca el índice de
listados (`/soporte-cliente/informes`), la cola del agente, la configuración de SLA ni el
**tablero operativo** (`/soporte-cliente/dashboard`).

La diferencia que no se copia de Suscripciones: **la autoridad no está partida**. Como en Ventas,
el Gerente de Éxito del Cliente y el agente ven las **mismas** tres historias; `meta.acotado_a`
(`todos` | `propios`) viaja visible junto al período. Un guard de listados (admite Cliente) o el
de la cola operativa (admite `DesarrolladorAPIs` / `DirectorTecnologico`, **no** al Gerente)
metería o dejaría fuera a quien el backend de compuestos ya decidió.

La diferencia que no se copia de Ventas: el par **cumplimiento / cobertura** es un solo bloque
(FR-UI-008), y el envelope trae `data.resultados` + `data.declaraciones`, no un array plano.

Una cáscara de layout Z + tres definiciones. Sin librería de gráficas. El período es el único
filtro global; `agrupar_por` queda como opción **de la zona** del tablero. Ver no habilita a
asignar, responder ni cerrar.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts. Visuales: número héroe, barras de distribución Tailwind (mismo patrón que `emergencias/gestion`, `red-operativa/gestion`, `ventas-crm/gestion` y `suscripciones/gestion`).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-tacticos/soporte/<informe>` (el slug
`cumplimiento-sla-por-plan` se pide como `cumplimiento-sla/por-plan`).

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en las cuatro zonas Z más
`zona-alcance`. Pruebas de **exclusión** (Cliente / Operador / `DesarrolladorAPIs` no entran) y de
que el alcance se pinta desde `meta.acotado_a`, no desde el rol adivinado en cliente. Prueba de que
el héroe de cumplimiento muestra **las dos** cifras del par.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente).

**Performance Goals**: Heredados del backend. La pantalla no agrega. Cada zona Z carga en
paralelo; un fallo no bloquea las otras. SC-F01: héroe reconocible en <5 s.

**Constraints**: FR-UI-001..026. Máximo 6–8 bloques. Sin mapas. Sin exportar. Ver no habilita a
decidir. Texto de ticket e identidad excluidos también para el Gerente. Período = único filtro
global (no editor de `granularidad`, `eje` ni `minimo`).

**Scale/Scope**: 3 pantallas, 9 informes, 1 cáscara Z, 1 guard, 1 servicio, 3 entradas de sidebar.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y los 9 publicados. No inventa métricas ni agrupamiento por servicio. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de una zona aislado. Vacío ≠ ceros. Serie con días en cero, no huecos. |
| III. Performance Efficiency | PASS | Flujo analítico, no despacho. Sin cómputo en cliente (no suma automático+humano, no mensualiza SLA). |
| IV. Interaction Capability | PASS | Núcleo: patrón Z, ≤8 bloques, par cumplimiento/cobertura inseparable, alcance visible (SC-F01, SC-F02). |
| V. Security | PASS | Guard GerenteExitoCliente \| Soporte \| Administrador. Sin Cliente. Exclusión constitucional en pantalla. |
| VI. Compatibility | N/A | No hay API nueva ni partner. |
| VII. Maintainability | PASS | Cáscara Z + catálogo de definiciones, espejo de los cuatro departamentos anteriores, módulo propio. No extrae `shared/` (fuera de alcance tocar módulos verdes). |
| VIII. Flexibility | N/A | Sin eje de región; el servicio llega ausente y se declara. |
| IX. Safety | PASS | No hay cadena de despacho. Safety se limita a no inducir decisión de soporte falsa: 11 % sin cobertura prohibido, 0 % donde no hubo compromiso prohibido, automático ≠ humano, vacío ≠ ceros. |

**Conflictos entre características:** ninguno identificado. Safety no está en juego de despacho; no se invoca el Tie-Breaker.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/frontend/
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
frontend/src/app/modules/soporte-cliente/gestion/   # NUEVO — no es listado, cola ni dashboard
├── soporte-cliente-gestion.routes.ts
├── guards/
│   └── soporte-gestion.guard.ts                    # GerenteExitoCliente | Soporte | Administrador
├── definiciones/
│   └── pantallas-gestion.definiciones.ts           # las tres historias → zonas Z → informes
├── services/
│   └── informes-compuestos-api.service.ts          # GET /informes-tacticos/soporte/<ruta>
├── models/
│   └── informes-compuestos.types.ts                # Envelope { resultados, declaraciones } + meta.acotado_a
└── pages/
    ├── pantalla-z.page.ts                          # UNA página, parametrizada por definición
    ├── pantalla-z.page.html                        # las cuatro zonas Z + alcance + par cobertura
    └── apoyo-plegable.component.ts                 # US1: tickets por servicio

frontend/src/app/shared/layout/nav-links.ts         # +3 enlaces (no los de /informes ni /dashboard)
frontend/src/app/app.routes.ts                      # loadChildren 'soporte-cliente/gestion'
```

**Reutilizado:** selector de período ya usado en las gestiones anteriores (control de fechas).

**Prohibido reutilizar:**

- `InformeCardComponent` como grilla (anti-Z).
- El índice / guards de `soporte-cliente/informes/` (admite Cliente y
  `DesarrolladorAPIs` / `DirectorTecnologico`).
- `agenteSoporteGuard` de la cola y el dashboard (no incluye al Gerente; incluye roles que el
  backend de compuestos rechaza).
- Las pantallas `dashboard-soporte`, `cola-agente`, `detalle-ticket` o `configuracion-sla` como
  cáscara de estos informes.

**Structure Decision**: carpeta `gestion/` dentro de `modules/soporte-cliente/`, rutas
`/soporte-cliente/gestion/{cumplimiento|cola|tendencias}`. El prefijo `/soporte-cliente/informes/`
ya es de los listados (el Cliente entra). `/soporte-cliente/dashboard` es el tablero operativo
sin corte. Fusionarlos mezclaría dos productos, reabriría texto de ticket y anularía el período.

No se extrae la cáscara Z a `shared/` en esta pasada: tocar cuatro módulos ya verdes para un
ahorro que no es de esta capa viola el Out of Scope. Se copia el patrón; una extracción se evalúa
en una spec de refactor.

## Complexity Tracking

*Sin violaciones — no aplica.*
