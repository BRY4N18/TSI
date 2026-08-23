# Implementation Plan: OE4 — Histórico e Inteligencia — Frontend

**Branch**: `001-estrategico/OE4-inteligencia-predictiva/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Depends-on**: [`../backend/`](../backend/) (9 GET; 6 → 404). Esta capa no redefine cifras ni OpenAPI.

---

## Summary

Cuatro pantallas Z **copiadas** de `estrategico/oe3/` (no importar `PantallaZPage`; no extraer
`shared/`). Consumen `GET /api/v1/informes-estrategicos/oe4/<informe>`.

**Autoridad partida** (cuatro guards):

| Pantalla | Roles |
|---|---|
| Calidad | `DirectorDatos` · `DirectorOperaciones` · `Gerente` |
| Concentración | `DirectorDatos` · `Gerente` |
| Impacto | `DirectorDatos` · `DirectorOperaciones` · `Gerente` |
| Cobertura | `DirectorDatos` · `Gerente` |

Un guard unión le daría a Operaciones el ranking vendible. Partner fuera. `cumple` nunca
booleano: no hay semáforo. E4-05 es ranking por nombre, no mapa.

---

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals)

**Primary Dependencies**: `HttpClient`. Sin librería de charts ni de mapas.

**Storage**: N/A — HTTP a `/api/v1/informes-estrategicos/oe4/<informe>`

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero. Exclusión de roles; índice+4 piezas;
ranking con ceros; sin mapa; clima parcial; no-dato ≠ 0 víctimas; umbral visible; slugs
bloqueados ausentes.

**Target Platform**: SPA en `accidentes-frontend` (nginx)

**Constraints**: FR-UI-001..024. 6–8 bloques. Sin mapa/región/exportar. Período + comparación.

**Scale/Scope**: 4 pantallas, 9 informes, 4 guards, 1 servicio, 4 ítems de sidebar.

---

## Constitution Check

| Característica | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Nueve publicados. No finge modelo. Cero no registrado ≠ cero. |
| II. Reliability | PASS *(fuera de camino crítico)* | Lectura histórica. Zona aislada. |
| III. Performance Efficiency | PASS | Sin cómputo de negocio en cliente. |
| IV. Interaction Capability | PASS | Z, ≤8, menú por materia. |
| V. Security | PASS | Guards partidos. Sin identidad. |
| VI. Compatibility | N/A | Sin API nueva. |
| VII. Maintainability | PASS | Copia Z a `oe4/`. No `shared/`. |
| VIII. Flexibility | PASS | Condado, no región. Mitad predictiva no fingida. |
| IX. Safety | PASS | Sin mapa de personas, sin precisión 0 %, sin víctimas=0 por no-dato. |

**Post-Design Gate:** PASS.

---

## Project Structure

```text
frontend/src/app/modules/estrategico/oe4/
├── oe4.routes.ts
├── guards/oe4.guard.ts
├── definiciones/pantallas-oe4.definiciones.ts
├── services/informes-oe4-api.service.ts
├── models/informes-oe4.types.ts
├── models/estado-zona.ts
└── pages/pantalla-z.page.ts + .html + apoyo-plegable.component.ts
```

Rutas: `/estrategico/oe4/{calidad|concentracion|impacto|cobertura}`.

**Prohibido:** importar `PantallaZPage` de OE3; Leaflet; slugs bloqueados; `acotado_a`.
