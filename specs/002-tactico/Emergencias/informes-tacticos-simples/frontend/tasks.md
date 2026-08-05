---

description: "Task list for feature implementation"
---

# Tasks: Informes Tácticos Simples de Emergencias (Frontend)

**Input**: Design documents from `specs/002-tactico/Emergencias/informes-tacticos-simples/frontend/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [quickstart.md](quickstart.md)

**Organization**: Tareas agrupadas por historia de usuario de `spec.md`. US1 (Registro) y US2 (Despacho) son P1; US3 (Seguimiento) es P2.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Crear `frontend/src/app/modules/emergencias/{guards,services/models,pages/shared}` con los archivos base
- [X] T002 [P] Crear `frontend/src/app/modules/emergencias/services/models/informes-tacticos.types.ts` (tipos de request/response de los 16 informes, reutilizando `ApiEnvelope<T>`)
- [X] T003 [P] Crear `frontend/src/app/modules/emergencias/guards/emergencias-informes.guard.ts` (`Operador`/`Administrador`, mismo patrón que `agenteSoporteGuard`)

## Phase 2: Foundational

- [X] T004 Implementar `frontend/src/app/modules/emergencias/services/informes-tacticos-api.service.ts` con los 16 métodos (uno por endpoint de `../backend/contracts/informes-tacticos-simples.openapi.yaml`)
- [X] T005 [P] Implementar `frontend/src/app/modules/emergencias/pages/shared/informe-card.component.{ts,html}` (loading/error/empty/data, `@Input` genérico)
- [X] T006 [P] Implementar `frontend/src/app/modules/emergencias/pages/shared/periodo-selector.component.{ts,html}` (emite `{desde, hasta}`, rango por defecto: últimos 30 días)
- [X] T007 Crear `frontend/src/app/modules/emergencias/emergencias.routes.ts` con las 3 rutas (`informes/registro`, `informes/despacho`, `informes/seguimiento`), todas con `canActivate: [emergenciasInformesGuard]`
- [X] T008 Registrar el módulo en `frontend/src/app/app.routes.ts` (`loadChildren` → `emergencias.routes`)
- [X] T009 Añadir entradas de navegación al sidebar existente (mismo lugar que "Registrar accidente"/"Lista de accidentes")

## Phase 3: User Story 1 - Workpanel de Registro (P1) 🎯 MVP

- [X] T010 [US1] Implementar `workpanel-registro.page.{ts,html}` con las 7 tarjetas (volumen, severidad, zona, completitud, descarte/fusión, ranking, impacto humano), usando `InformeCardComponent` + `PeriodoSelectorComponent`
- [X] T011 [US1] Verificar en navegador: las 7 tarjetas cargan, el selector de período las refresca a todas (quickstart.md pasos 1-2)

## Phase 4: User Story 2 - Workpanel de Despacho (P1)

- [X] T012 [US2] Implementar `workpanel-despacho.page.{ts,html}` con las 6 tarjetas + filtro de condado adicional (solo afecta `asignacion-automatica-vs-manual` y `tiempo-respuesta-por-severidad`)
- [X] T013 [US2] Verificar en navegador: las 6 tarjetas cargan, el filtro de condado solo recorta las 2 tarjetas que lo soportan (quickstart.md paso 3)

## Phase 5: User Story 3 - Workpanel de Seguimiento (P2)

- [X] T014 [US3] Implementar `workpanel-seguimiento.page.{ts,html}` con las 3 tarjetas
- [X] T015 [US3] Verificar en navegador: las 3 tarjetas cargan (quickstart.md paso 4)

## Phase 6: Polish

- [X] T016 [P] `ng build` de producción sin errores nuevos
- [X] T017 [P] Verificar aislamiento de fallos y control de acceso (quickstart.md pasos 5-6)
- [X] T018 Actualizar `../informes-tacticos-simples.md` (índice del módulo) marcando frontend como completo

## Notes

- Reutiliza `AuthApiService`, `TablerIconComponent`, patrón `toDist()` de `dashboard-soporte.page.ts` — sin dependencias nuevas.
- No hay tests unitarios Jasmine/Karma en el entorno de ejecución de esta sesión (sin Chrome local) — verificación vía `tsc --noEmit`, `ng build`, y recorrido real en el navegador embebido.
