# Research — OE6 frontend

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z de OE5, no extraer `shared/`

**Decision:** módulo `estrategico/oe6/` espejo de `estrategico/oe5/`. No se importa
`PantallaZPage`. No se mueve la cáscara a `shared/`.

**Rationale:** AGENTS.md: extraer ahora acopla cuatro objetivos. Copiar es el patrón táctico →
OE2 → OE1 → OE5.

**Alternatives considered:** importar OE5 — acopla vidas y retención. Extraer `shared/` — fuera
de alcance.

## D2 — Un guard, no cuatro autoridades

**Decision:** `oe6Guard` = `DirectorOperaciones` · `Gerente`, aplicado a las **cuatro** rutas.
Prohibido `Administrador`, `PartnerIntegracion`, `DirectorFinanciero`, `GerenteExitoCliente`.

**Rationale:** §4.6 es una sola autoridad. Cuatro guards idénticos duplicarían código sin partir
acceso. Eso **no** es la unión prohibida de OE1/OE5 (allí las materias tienen cargos distintos).

**Alternatives considered:** cuatro guards iguales — ruido. Guard por informe — el menú ya es
por historia, no por informe.

## D3 — Rutas bajo `/estrategico/oe6/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Llegada | `/estrategico/oe6/llegada` |
| Diagnóstico | `/estrategico/oe6/diagnostico` |
| Ejecución | `/estrategico/oe6/ejecucion` |
| Personas | `/estrategico/oe6/personas` |

Grupo **Estratégico**, no «Emergencias».

**Rationale:** mezclarlas con OT21–OT25 pondría dos medianas en el mismo grupo.

## D4 — Envelope `{ data, meta }`

**Decision:** `data` array; `meta.cobertura`, `meta.falta`, `meta.alcance`, `meta.objetivo`,
`meta.comparacion`. Prohibido `data.resultados` o `acotado_a`.

## D5 — Mediana, p95 y recuento juntos

**Decision:** el héroe de Llegada pinta mediana, p95 (o «sin dato») y recuento **en el mismo
bloque**. `cobertura === 'parcial'` → `zona-parcial`.

**Rationale:** FR-UI-007. Un p95 huérfano o un promedio como héroe miente la cola.

## D6 — Vacío de casos ≠ 0 min

**Decision:** `data: []` en tiempo de respuesta → **vacio**, copy «sin casos en el período».
Prohibido 0 min / 0 %.

## D7 — p95 nulo si n bajo

**Decision:** p95 `null` → **sin_dato** en esa cifra; la mediana y el recuento siguen si
existen. Prohibido sustituir por el máximo.

## D8 — Histórico, no ETA

**Decision:** desviación-de-llegada en lectura de Diagnóstico. Copy de `meta.alcance`. Prohibido
titular ETA. Prohibido mapa.

## D9 — Tasas con denominador

**Decision:** rechazo, abortos y cierres pintan numerador y denominador en el mismo renglón.

## D10 — Sin librería de gráficas ni de mapas

**Decision:** barras Tailwind. Prohibido Leaflet, Chart.js, D3.

## D11 — Período + granularidad + comparación

**Decision:** `desde`, `hasta`, `granularidad` (`mes` | `trimestre` | `anio`), `comparacion`
(`ninguna` | `mom` | `yoy`). Sin editor de umbral. Comparación nula con motivo → **ausente**.

## D12 — Carga por zona

**Decision:** cada zona su GET. Un 500 en evidencia no borra el héroe de impacto.

## D13 — Condado, no región

**Decision:** se pintan las claves que trae el payload (condado). Prohibido `groupBy` región o
país en cliente.

## D14 — Sin identidad

**Decision:** ninguna columna de nombre, placa, teléfono, foto identificable o coordenadas.

## D15 — Vacío vs cero vs sin_dato

| Señal | Estado |
|---|---|
| `data: []` en tiempos / abortos | **vacio** |
| tramo o severidad con 0 casos y fila presente | **dato**: cero real |
| p95 `null` | **sin_dato** en esa cifra |
| comparación nula con motivo | **ausente** |

## D16 — Sidebar: cuatro enlaces, mismos roles

**Decision:** grupo `Estratégico`. Las cuatro: `DirectorOperaciones` · `Gerente`. Partner
**ausente**. Financiero **ausente**.

## D17 — Copiar, no compartir con OE5

**Decision:** duplicar `pantalla-z` y `apoyo-plegable` en `oe6/`. Un cambio de copy de retención
no debe romper tiempos de emergencia.
