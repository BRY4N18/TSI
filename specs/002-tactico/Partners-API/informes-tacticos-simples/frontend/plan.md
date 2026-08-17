# Implementation Plan: Informes Tácticos Simples de Partners y API — Frontend

**Branch**: `002-tactico/Partners-API/informes-tacticos-simples/frontend` | **Date**: 2026-08-16 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Partners-API/informes-tacticos-simples/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (cinco endpoints publicados). Esta capa no redefine filtros ni OpenAPI.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

## Summary

Cinco pantallas de **listado** (no patrón Z) sobre la capa compartida `shared/informes/`. Es el único departamento táctico sin índice. Una página parametrizada por catálogo de definiciones, dos guards (acceso / contrato), dos entradas de menú hacia la misma ruta para no fusionar consola y portal.

**Prerrequisito de backend (FR-014a):** el permiso desplegado omite al Director Tecnológico. Sin cerrarlo, el índice le mostraría cinco enlaces que responden `403`. El plan lo cierra **sin** ensanchar `es_gestor()` operativo.

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals), igual que el resto de `frontend/`.

**Primary Dependencies**: `HttpClient` vía `InformesListadoService` ya existente. **Sin** librería de charts. **Sin** servicio HTTP nuevo.

**Storage**: N/A — solo lectura HTTP a `GET /api/v1/informes/partners-api/{listado}`.

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero. Pruebas de **exclusión** (Partner no entra a contrato; Operador no entra a ninguno) además de la entrada. Definiciones comparadas contra el contrato OpenAPI (columnas / `admiteRango`) y contra las constantes de dominio que el backend usa para enumeraciones.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx).

**Project Type**: Web application (frontend nuevo, backend existente con un parche de permiso).

**Performance Goals**: Heredados del backend (primera página en menos de 2 s). La pantalla no agrega ni cuenta el total.

**Constraints**: FR-UI-001..032. Cursor opaco. Sin exportar. Sin motivo en la fila de credencial. Sin secreto. Ausente ≠ ilimitado. Guard no decide filas.

**Scale/Scope**: 5 listados, 1 índice, 1 página, 2 guards, 2 entradas de sidebar, parche de permiso + prueba en backend.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Cita FR-UI y FR-001..023 / FR-014a–c del backend. Cinco listados, no un sexto de logs. Inactiva ≠ motivo. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura. Distingue `400` / `403` / vacío / fallo reintentable. No compensa ingesta. |
| III. Performance Efficiency | PASS | Flujo analítico. Paginación keyset; sin recuento. |
| IV. Interaction Capability | PASS | Núcleo: índice filtrado, aviso `acotado_a` en el vacío, dos menús, vacío de dominio. |
| V. Security | PASS | Dos guards, no la unión. Secreto nunca en pantalla. `es_gestor()` operativo **no** se ensancha. Director entra a informes como gestor de lectura. |
| VI. Compatibility | PASS | Consume el contrato publicado. Alinea el enum `entorno` del OpenAPI con `ENTORNOS` (research D6). |
| VII. Maintainability | PASS | Catálogo + una página, espejo de Soporte/Cuentas. Capa compartida intocada salvo que un filtro condicional demuestre que quedó corta — entonces la corrección va allí. |
| VIII. Flexibility | N/A | No introduce eje de región ni despliegue nuevo. |
| IX. Safety | N/A | No asigna unidades ni clasifica gravedad en curso. El conflicto inactiva/motivo se resolvió en la spec (Suitability + Security). |

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Partners-API/informes-tacticos-simples/frontend/
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
# Prerrequisito FR-014a (mismo trabajo; sin él la UI miente)
backend/apps/partners/domain_constants.py          # + ROL_DIRECTOR_TECNOLOGICO
backend/apps/partners/permissions.py               # ROLES_GESTORES_INFORMES; es_gestor_informes()
backend/apps/partners/views/informes_views.py      # acotar() usa es_gestor_informes, no es_gestor
backend/apps/partners/tests/api/test_informes_permisos.py
backend/apps/partners/tests/unit/test_propiedad_partner.py  # es_gestor() sigue SIN el Director
specs/.../backend/contracts/informes-tacticos-simples.openapi.yaml  # enum entorno

frontend/src/app/modules/partners/informes/         # NUEVO — no es consola ni portal
├── partners-informes.routes.ts
├── guards/
│   └── informes-partners.guard.ts                  # DOS funciones: acceso | contrato
├── definiciones/
│   └── informes-partners.definiciones.ts
├── pages/
│   ├── indice/indice-informes.page.ts
│   └── informe/informe.page.ts                     # UNA página; oculta filtro `partner` al Partner

frontend/src/app/app.routes.ts                      # loadChildren 'partners/informes' ANTES de 'partners'
frontend/src/app/shared/layout/nav-links.ts         # +2 enlaces, misma ruta, roles/textos distintos
```

**Reutilizado:** `shared/informes/` (servicio, store, tabla, filtros, aviso de alcance). Guards de rol al estilo Soporte.

**Prohibido reutilizar / tocar:**

- Un `canActivate` con la unión de los cuatro roles en las rutas de contrato.
- `gestorPartnersGuard` (no incluye al Director; incluirlo ahí abriría la consola operativa).
- La consola de registros (`/partners/consola/logs`) como «sexto listado».
- Extraer o forkar la capa compartida para este departamento.

**Structure Decision**: carpeta `informes/` dentro de `modules/partners/`, ruta
`/partners/informes`. Se registra en `app.routes.ts` **antes** de `path: 'partners'` para que no la
trague el `redirectTo: 'consola'` del módulo operativo. Consola y portal no se tocan.

## Complexity Tracking

*Sin violaciones — no aplica.*
