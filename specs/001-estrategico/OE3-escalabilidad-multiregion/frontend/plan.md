# Implementation Plan: OE3 — Escalabilidad Multi-Región — Frontend

**Branch**: `001-estrategico/OE3-escalabilidad-multiregion/frontend` | **Date**: 2026-08-18 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE3-escalabilidad-multiregion/frontend/spec.md`

**Depends-on**: [`../backend/`](../backend/) (7 GET publicados; 7 bloqueados → 404). Esta capa no redefine cifras ni OpenAPI.

---

## Summary

Cuatro pantallas nuevas de **lectura de empresa** en **patrón Z**, **copiado** de `estrategico/oe6/` (cáscara) y **guards partidos** al estilo `estrategico/oe5/` (no importar `PantallaZPage`; no extraer `shared/`). Consumen
`GET /api/v1/informes-estrategicos/oe3/<informe>`. **No** se tocan los compuestos tácticos ni OE6/OE4.

**La autoridad está partida** (cuatro guards, nunca una unión de las cuatro rutas):

| Pantalla | Roles |
|---|---|
| Latencia | `DirectorOperaciones` · `Gerente` |
| Calidad | `DirectorOperaciones` · `Gerente` |
| Capacidad | `DirectorExpansion` · `DirectorOperaciones` · `Gerente` |
| Respaldo | `DirectorExpansion` · `Gerente` |

Un guard unión le daría a Expansión la latencia de despacho. El partner **no entra**. Tecnológico **no entra** (el GET de E3-02 no lo admite). El Administrador no está en §4.3.

Período + granularidad + comparación (`ninguna` | `mom` | `yoy`). Envelope `{ data, meta }`.
No hay `acotado_a`. No hay mapa ni eje de región. Ver no habilita a despachar ni a abrir mercado.
`cumple` booleano solo en E3-02 y E3-10.

---

## Technical Context

**Language/Version**: TypeScript 5.x / Angular 19+ (standalone, `OnPush`, signals)

**Primary Dependencies**: `HttpClient`. **Sin** librería de charts ni de mapas. Número héroe y
barras Tailwind (mismo patrón que OE6).

**Storage**: N/A — solo lectura HTTP a `/api/v1/informes-estrategicos/oe3/<informe>`

**Testing**: Jasmine/Karma, `*.spec.ts` junto al fichero, `data-testid` en zonas Z más
`zona-apoyo`, `zona-parcial`, `zona-comparacion`. Pruebas de **exclusión** (Expansión fuera de
Latencia/Calidad; Operaciones fuera de Respaldo; Tecnológico, Partner y Financiero fuera de las
cuatro) y de p95+recuento+`cumple` juntos, p95 ausente si n bajo, vacío ≠ 0 min, sin capacidad ≠
infinito, tasas con denominador, E3-11 sin semáforo cerrado, sin mapa/región/bloqueados.

**Target Platform**: SPA Angular en `accidentes-frontend` (nginx)

**Project Type**: Web application (frontend nuevo, backend existente)

**Performance Goals**: Cada zona Z carga en paralelo. SC-F01: héroe de latencia reconocible en <5 s.

**Constraints**: FR-UI-001..026. Máximo 6–8 bloques. Sin mapa, coordenadas, nombres, región ni
exportar. Período + comparación = únicos filtros. No editor de umbral de muestra ni de GPS.
Agrupación por condado, no región.

**Scale/Scope**: 4 pantallas, 7 informes, 1 cáscara Z copiada, 4 guards, 1 servicio, 4
entradas de sidebar en grupo **Estratégico**.

---

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| I. Functional Suitability | PASS | Siete publicados. No inventa región, uptime ni 20 000 días. Vacío, p95 ausente, sin capacidad y `cumple` se leen como el backend. |
| II. Reliability | PASS *(fuera del camino crítico)* | Lectura histórica. Fallo de zona aislado. Vacío ≠ 0 min. |
| III. Performance Efficiency | PASS | Sin cómputo de negocio en cliente (no inventa p95, no dibuja mapa). |
| IV. Interaction Capability | PASS | Núcleo: Z, ≤8 bloques, menú por materia, comparación. |
| V. Security | PASS | Cuatro guards. Partner 403. Tecnológico sin menú. Sin identidad ni coordenadas. |
| VI. Compatibility | N/A | No hay API nueva. |
| VII. Maintainability | PASS | Cáscara Z copiada a `oe3/`. No extrae `shared/`. No importa `PantallaZPage` de OE6. |
| VIII. Flexibility | PASS | Agrupa por condado porque la región no es construible. Sin eje inventado. La mitad «escalar» no se finge. |
| IX. Safety | PASS | Un 0 min fingido, un p95 de 3 despachos, un ratio infinito o un mapa de personas se impide en UI. Esta capa no despacha; evita mentir a quien mueve flota. |

**Conflictos:** ninguno. Safety no está en el camino de despacho; sí en no falsear capacidad.

**Post-Design Gate:** PASS — sin violaciones. Complexity Tracking vacío.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE3-escalabilidad-multiregion/frontend/
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
frontend/src/app/modules/estrategico/oe3/     # NUEVO — copia de oe6, guards al estilo oe5
├── oe3.routes.ts
├── guards/oe3.guard.ts                       # cuatro guards
├── definiciones/pantallas-oe3.definiciones.ts
├── services/informes-oe3-api.service.ts      # GET /informes-estrategicos/oe3/<informe>
├── models/informes-oe3.types.ts
├── models/estado-zona.ts
└── pages/
    ├── pantalla-z.page.ts
    ├── pantalla-z.page.html
    └── apoyo-plegable.component.ts

frontend/src/app/shared/layout/nav-links.ts   # +4 enlaces grupo Estratégico
frontend/src/app/app.routes.ts                # loadChildren 'estrategico/oe3'
```

**Reutilizado:** selector de fechas + granularidad + comparación ya en OE6 (se copia el
comportamiento, no el módulo).

**Prohibido reutilizar:**

- Importar `PantallaZPage` de `estrategico/oe6`, `oe5`, `oe1`, `oe2`
- Guard único de OE6 (aquí la autoridad está partida)
- `InformeCardComponent` como grilla
- Leaflet / cualquier mapa
- Pintar `acotado_a`
- Rutas `/emergencias/*` tácticas
- Recuadros de informes bloqueados o de OE6 Llegada
- Slugs de OpenAPI distintos a `PUBLICADOS` del servicio (`latencia-asignacion`, etc.)

**Structure Decision**: módulo `estrategico/oe3/`, rutas
`/estrategico/oe3/{latencia|calidad|capacidad|respaldo}`. Grupo **Estratégico**.

No se extrae la cáscara Z a `shared/` en esta pasada.

---

## Complexity Tracking

*Sin violaciones — no aplica.*
