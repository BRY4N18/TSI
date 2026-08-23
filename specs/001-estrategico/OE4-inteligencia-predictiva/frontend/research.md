# Research — OE4 frontend

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar Z de OE3, no extraer `shared/`

**Decision:** módulo `estrategico/oe4/` espejo de `oe3/`. No importar `PantallaZPage`.

**Rationale:** AGENTS.md: extraer ahora acopla seis objetivos.

## D2 — Cuatro guards según HTTP

**Decision:**

| Guard | Roles |
|---|---|
| `oe4CalidadGuard` | `DirectorDatos` · `DirectorOperaciones` · `Gerente` |
| `oe4ConcentracionGuard` | `DirectorDatos` · `Gerente` |
| `oe4ImpactoGuard` | `DirectorDatos` · `DirectorOperaciones` · `Gerente` |
| `oe4CoberturaGuard` | `DirectorDatos` · `Gerente` |

**Rationale:** `AUTORIDAD_OE4_EXPEDIENTE` vs `AUTORIDAD_OE4_INTELIGENCIA`. Menú que abriera 403
descubrirá la superficie.

## D3 — E4-05 es ranking, no mapa

**Decision:** barras/lista por `zona` (nombre). Prohibido Leaflet y lat/lon.

**Rationale:** el contrato entrega nombre; la constitución prohíbe mapa de personas.

## D4 — Sin semáforo

**Decision:** no pintar `cumple` como verde/rojo. Todas las metas son `CALIBRAR`.

## D5 — Slugs de `oe4_service.PUBLICADOS`

`indice-calidad-historico`, `completitud-campos-criticos`, `campos-mas-ausentes`,
`calidad-por-origen`, `concentracion-siniestralidad`, `patron-horario-climatico`,
`impacto-humano-por-zona`, `impacto-vial-por-zona`, `cobertura-del-historico`.

**No llamar:** `precision-del-modelo`, `contraste-prediccion-ocurrencia`,
`unidades-preposicionadas`, `versiones-del-modelo`, `productos-de-inteligencia`,
`latencia-de-ingesta`.

## D6 — Envelope `{ data, meta }`

Igual que OE3. `data` array. Prohibido `resultados` y `acotado_a`.

## D7 — Clima parcial

E4-06: si `casos_con_clima` < mínimo o `cobertura` parcial, copy de anécdota, no patrón.

## D8 — No-dato ≠ cero

E4-12 usa `casos_con_dato`. E4-13 usa `casos_con_duracion` y `casos_con_distancia`.

## D9 — Cobertura por condado + umbral

E4-15: `sin_masa_critica` y `umbral_casos` visibles. Sin editor de umbral en UI.

## D10 — Período + granularidad + comparación

`desde`, `hasta`, `granularidad`, `comparacion`. Un método HTTP, no nueve.

## D11 — Carga por zona

GET por informe. Un 500 en origen no borra el índice.

## D12 — Sidebar

Grupo `Estratégico`, tras OE3. Operaciones sin Concentración ni Cobertura.
