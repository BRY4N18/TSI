# Implementation Plan: OE6 — Tiempo de Respuesta y Vidas — Frontend

**Branch**: `001-estrategico/OE6-respuesta-y-vidas/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE6-respuesta-y-vidas/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (12 GET publicados). Esta capa no redefine cifras ni OpenAPI.

---

## Summary

Cuatro pantallas nuevas de **lectura de empresa** en **patrón Z**, **copiado** de `estrategico/oe5/` (no importado; no extraer `shared/`). Consumen
`GET /api/v1/informes-estrategicos/oe6/<informe>`. **No** se tocan los compuestos tácticos de
Emergencias ni OE3/OE4.

**Una sola autoridad** (un guard, las cuatro rutas): `DirectorOperaciones` · `Gerente`. No es
unión de materias distintas: §4.6 da los doce al mismo cargo. El partner **no entra**. Finanzas
y Éxito de Cliente **no** ven el menú. El Administrador no sustituye a Operaciones.

Período + granularidad + comparación (`ninguna` | `mom` | `yoy`). Envelope `{ data, meta }`.
No hay `acotado_a`. No hay mapa ni ETA. Ver no habilita a despachar.

---

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals)

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts ni de mapas. Número héroe y
barras Tailwind (mismo patrón que OE5).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-estrategicos/oe6/<informe>`

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en zonas Z más
`zona-apoyo`, `zona-parcial`, `zona-comparacion`. Pruebas de **exclusión** (Partner, Financiero,
Éxito de Cliente fuera) y de mediana+p95+recuento juntos, p95 ausente si n bajo, vacío ≠ 0 min,
histórico ≠ ETA, tasas con denominador, sin mapa/identidad/OE3.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx)

**Project Type**: Web application (frontend nuevo, backend existente)

**Performance Goals**: Cada zona Z carga en paralelo. SC-F01: héroe de llegada reconocible en <5 s.

**Constraints**: FR-UI-001..024. Máximo 6–8 bloques. Sin mapa, coordenadas, nombres, ETA ni
exportar. Período + comparación = únicos filtros. No editor de umbral de muestra. Agrupación
por condado, no región.

**Scale/Scope**: 4 pantallas, 12 informes, 1 cáscara Z copiada, 1 guard, 1 servicio, 4
entradas de sidebar en grupo **Estratégico**.

---

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Doce publicados. No inventa región, ETA ni mapa. Mediana/p95, vacío y dato escaso se leen como el backend. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de zona aislado. Vacío ≠ 0 min. |
| III. Performance Efficiency | PASS | Sin cómputo de negocio en cliente (no inventa p95, no dibuja mapa). |
| IV. Interaction Capability | PASS | Núcleo: Z, ≤8 bloques, menú por historia, comparación. |
| V. Security | PASS | Guard único de autoridad. Partner 403. Sin identidad ni coordenadas. |
| VI. Compatibility | N/A | No hay API nueva. |
| VII. Maintainability | PASS | Cáscara Z copiada a `oe6/`. No extrae `shared/`. No importa `PantallaZPage` de OE5. |
| VIII. Flexibility | PASS | Agrupa por condado porque la región no es construible. Sin eje inventado. |
| IX. Safety | PASS | Un 0 min fingido, un p95 de 3 casos o un mapa de personas se impide en UI. Esta capa no despacha; evita mentir a quien sí despacha. |

**Conflictos:** ninguno. Safety no está en el camino de despacho; sí en no falsear tiempos.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE6-respuesta-y-vidas/frontend/
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
frontend/src/app/modules/estrategico/oe6/     # NUEVO — copia de oe5, no import
├── oe6.routes.ts
├── guards/oe6.guard.ts                       # un guard, cuatro rutas
├── definiciones/pantallas-oe6.definiciones.ts
├── services/informes-oe6-api.service.ts      # GET /informes-estrategicos/oe6/<informe>
├── models/informes-oe6.types.ts
├── models/estado-zona.ts
└── pages/
    ├── pantalla-z.page.ts
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts

frontend/src/app/shared/layout/nav-links.ts   # +4 enlaces grupo Estratégico
frontend/src/app/app.routes.ts                # loadChildren 'estrategico/oe6'
```

**Reutilizado:** selector de fechas + granularidad + comparación ya en OE5 (se copia el
comportamiento, no el módulo).

**Prohibido reutilizar:**

- Importar `PantallaZPage` de `estrategico/oe5`, `oe1`, `oe2` o `partners/gestion`
- Guards de OE5 (materias distintas)
- `InformeCardComponent` como grilla
- Leaflet / cualquier mapa
- Pintar `acotado_a`
- Rutas `/emergencias/*` tácticas
- Recuadros de OE3

**Structure Decision**: módulo `estrategico/oe6/`, rutas
`/estrategico/oe6/{llegada|diagnostico|ejecucion|personas}`. Grupo **Estratégico**.

No se extrae la cáscara Z a `shared/` en esta pasada.

---

## Complexity Tracking

*Sin violaciones — no aplica.*
