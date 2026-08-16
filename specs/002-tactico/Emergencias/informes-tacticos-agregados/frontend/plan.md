# Implementation Plan: Informes Tácticos Simples de Emergencias (Frontend)

**Branch**: `informes-tacticos-agregados/frontend` | **Date**: 2026-08-02 | **Spec**: `specs/002-tactico/Emergencias/informes-tacticos-agregados/frontend/spec.md`

**Depends-on**: `../backend/` (16 endpoints ya implementados y verificados contra Pinot real). Este plan no redefine cálculos ni contratos REST.

## Summary

Nuevo módulo Angular `modules/emergencias/` con 3 páginas de workpanel (Registro, Despacho, Seguimiento), cada una mostrando sus informes como tarjetas independientes con estado de carga/error/vacío propio, un selector de período compartido y (en Despacho) un filtro de condado adicional. Sigue el mismo patrón ya usado en `soporte-cliente/pages/dashboard-soporte/` (standalone, signals, `OnPush`, sin librería de gráficas — barras/números con Tailwind).

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (consistente con el resto de `frontend/`).

**Primary Dependencies**: `HttpClient` (sin librería nueva — no hay `ngx-charts`/`chart.js` en el proyecto; las 16 tarjetas se renderizan con texto/barras Tailwind, mismo patrón que `dashboard-soporte`).

**Storage**: N/A (solo lectura vía HTTP a los 16 endpoints del backend).

**Testing**: Jasmine/Karma (mismo patrón que el resto de `frontend/`, `*.page.spec.ts`).

**Target Platform**: SPA Angular servida por `accidentes-frontend` (nginx), consumida por Operador/Administrador autenticados.

**Project Type**: Web application (frontend nuevo, backend ya existente).

**Performance Goals**: Heredado del backend (SC-001 de `../backend/spec.md`, <3s por informe) — sin meta adicional de renderizado, el volumen de datos por tarjeta es pequeño (agregados, no listas largas).

**Constraints**: FR-UI-001..005 de `spec.md` — tarjetas independientes (un fallo no bloquea las demás), selector de período compartido, filtro de condado solo en Despacho, estado "sin datos" explícito, acceso restringido a `Operador`/`Administrador`.

**Scale/Scope**: 3 páginas de workpanel, 16 tarjetas en total (7+6+3), 1 guard de rol, 1 servicio API, 1 archivo de rutas del módulo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| Functional Suitability | PASS | Cita RF-UI-001..005 de `spec.md`, que a su vez cita los 16 RF del backend ya implementado |
| Reliability | N/A | Sin componente en el camino crítico de despacho — solo lectura de agregados históricos |
| Performance Efficiency | PASS | Hereda SC-001 del backend; sin cómputo pesado en cliente (datos ya agregados) |
| Interaction Capability | PASS | Núcleo de esta capa — tarjetas con estado de carga/error/vacío explícito por cada una (Ley de Hick: no bloquear todo el workpanel por un fallo de una tarjeta) |
| Security | PASS | Guard de rol reutilizando `AuthApiService.hasRole()` (mismo patrón que `agenteSoporteGuard`) |
| Compatibility | PASS | Mismo Angular/Tailwind/patrón de componentes ya usado en `soporte-cliente` |
| Maintainability | PASS | Módulo nuevo aislado (`modules/emergencias/`); no modifica `accidentes/`, `despacho/` ni `seguimiento/` existentes |
| Flexibility | PASS | Cada tarjeta es un componente independiente — añadir/quitar un informe no afecta a los demás |
| Safety | N/A | Fuera del camino crítico de seguridad física |

**Post-Design Gate:** PASS — sin violaciones.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Emergencias/informes-tacticos-agregados/frontend/
├── spec.md
├── plan.md          # este archivo
├── research.md
├── quickstart.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/src/app/modules/emergencias/                    # NUEVO módulo
├── emergencias.routes.ts
├── guards/
│   └── emergencias-informes.guard.ts                     # Operador | Administrador
├── services/
│   ├── informes-tacticos-api.service.ts                  # 16 métodos, uno por endpoint
│   └── models/
│       └── informes-tacticos.types.ts                    # tipos de respuesta por informe
└── pages/
    ├── workpanel-registro/
    │   └── workpanel-registro.page.{ts,html}
    ├── workpanel-despacho/
    │   └── workpanel-despacho.page.{ts,html}
    ├── workpanel-seguimiento/
    │   └── workpanel-seguimiento.page.{ts,html}
    └── shared/
        ├── periodo-selector.component.{ts,html}           # selector de período compartido
        └── informe-card.component.{ts,html}                # tarjeta base (loading/error/empty)

frontend/src/app/app.routes.ts                             # + bloque loadChildren 'emergencias'
```

**Structure Decision**: Módulo nuevo `modules/emergencias/`, no dentro de `modules/accidentes/` — los informes tácticos son un dominio distinto (lectura agregada, no registro/despacho operativo) y ya está definido como tal en el backend (app Django separada `informes_tacticos`). Un componente base `InformeCardComponent` reutilizable por las 16 tarjetas evita duplicar la lógica de loading/error/empty 16 veces (Maintainability), siguiendo el mismo espíritu que `app-list-loading-skeleton`/`app-list-error-state`/`app-list-empty-state` ya existentes para listados — aquí se adapta a la forma de "tarjeta de métrica", no de listado.

## Complexity Tracking

*Sin violaciones — no aplica.*
