# Research — OE3 frontend

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z de OE6, no extraer `shared/`

**Decision:** módulo `estrategico/oe3/` espejo de `estrategico/oe6/` en página y envelope.
Los **cuatro guards** se copian del patrón de `estrategico/oe5/`. No se importa
`PantallaZPage`. No se mueve la cáscara a `shared/`.

**Rationale:** AGENTS.md: extraer ahora acopla cinco objetivos. Copiar es el patrón táctico →
OE2 → OE1 → OE5 → OE6.

**Alternatives considered:** importar OE6 — acopla vidas y capacidad. Extraer `shared/` — fuera
de alcance.

## D2 — Cuatro guards, nunca una unión; Tecnológico fuera

**Decision:**

| Guard | Roles | Pantalla |
|---|---|---|
| `oe3LatenciaGuard` | `DirectorOperaciones` · `Gerente` | latencia |
| `oe3CalidadGuard` | `DirectorOperaciones` · `Gerente` | calidad |
| `oe3CapacidadGuard` | `DirectorExpansion` · `DirectorOperaciones` · `Gerente` | capacidad |
| `oe3RespaldoGuard` | `DirectorExpansion` · `Gerente` | respaldo |

Prohibido `Administrador`, `PartnerIntegracion`, `DirectorFinanciero`, `GerenteExitoCliente`,
`DirectorTecnologico`.

**Rationale:** §4.3 parte la autoridad. Un `canActivate` único le daría a Expansión la latencia
(el backend responde 403, pero el menú ya habría descubierto la superficie).

**Hueco documentado:** [`acceso-estrategico.md`](../../acceso-estrategico.md) §4.3 da E3-02 a
`DirectorTecnologico`. `AUTORIDAD_OE3_DESPACHO` en código es solo Operaciones · Gerente. Esta
capa **no** pone un enlace que abra 403. El hueco es de backend; no se tapa con ítem gris.

**Menú más estrecho que HTTP:** Operaciones **puede** GET `cobertura-de-respaldo`; el **menú**
de Respaldo no se lo da (spec US4). Mezclaría respaldo vecinal con el despacho.

**Alternatives considered:** reusar `oe6Guard` — una sola autoridad, incorrecta aquí. Un guard
unión — viola §4.3. Incluir Tecnológico en Latencia — 403 en el héroe.

## D3 — Rutas bajo `/estrategico/oe3/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Latencia | `/estrategico/oe3/latencia` |
| Calidad | `/estrategico/oe3/calidad` |
| Capacidad | `/estrategico/oe3/capacidad` |
| Respaldo | `/estrategico/oe3/respaldo` |

Grupo **Estratégico**, no «Emergencias» ni «Red operativa».

**Rationale:** mezclarlas con OT21–OT25 pondría dos lecturas de despacho en el mismo grupo. OE6
Llegada (persona) y OE3 Latencia (proceso) deben verse como historias distintas.

## D4 — Envelope `{ data, meta }` y slugs del servicio

**Decision:** `data` array; `meta.cobertura`, `meta.falta`, `meta.alcance`, `meta.objetivo`
(con `cumple` booleano solo en `latencia-asignacion` y `tasa-error-registro`),
`meta.comparacion`. Prohibido `data.resultados` o `acotado_a`.

Slugs = `PUBLICADOS` de `oe3_service.py` (no los paths del OpenAPI si divergieran):

| Informe | Slug |
|---|---|
| E3-02 | `latencia-asignacion` |
| E3-03 | `evolucion-latencia` |
| E3-10 | `tasa-error-registro` |
| E3-11 | `primer-intento` |
| E3-07 | `ratio-demanda-capacidad` |
| E3-08 | `cobertura-de-respaldo` |
| E3-13 | `perdida-de-senal` |

**No se llama:** `uptime-por-region`, `tiempo-puesta-operacion`, `curva-maduracion`,
`cohorte-region`, `margen-operativo`, `reasignacion-manual`, `cobertura-pruebas`.

## D5 — Semáforo solo donde el backend es booleano

**Decision:** pintar `meta.objetivo.cumple` como cumple/no cumple **solo** si el valor es
`true`/`false`. `primer-intento` (`[CALIBRAR]`) → sin semáforo cerrado.

**Rationale:** FR-UI-009. Un verde en E3-11 fingiría KPI cerrado.

## D6 — Vacío de despachos ≠ 0 min ni meta cumplida

**Decision:** `data: []` en latencia → **vacio**, copy «sin despachos en el período». Prohibido
0 min y prohibido leerse como meta cumplida.

## D7 — p95 nulo si n bajo

**Decision:** p95 `null` → **sin_dato** en esa cifra; el recuento sigue si existe. Prohibido
sustituir por el máximo.

## D8 — Alcance operativo, no 100 ms

**Decision:** el héroe de Latencia muestra `meta.alcance` (proceso registro→asignación, meta
&lt;2 min p95). Prohibido titular o comparar contra 100 ms.

## D9 — Sin capacidad ≠ infinito

**Decision:** un condado con demanda y sin unidades vigentes se pinta con estado **sin
capacidad** (etiqueta), no como ratio ni como 0. Distinto de un condado sin demanda.

## D10 — Flota del período

**Decision:** copy de lectura de Capacidad toma `meta.alcance` del ratio: capacidad = versiones
vigentes **en el período**.

## D11 — Tasas con denominador; respaldo = disponible

**Decision:** error de registro, primer intento y cobertura de respaldo pintan numerador y
denominador. Un vecino solo dado de alta no se pinta como respaldo (el backend ya lo excluye;
la UI no lo «recupera»).

## D12 — GPS: recuento junto a la cifra

**Decision:** `perdida-de-senal` en apoyo plegado de Capacidad. Recuento o cobertura de
posiciones junto a la tasa. Sin editor de `umbral_seg` (default del backend).

## D13 — Sin librería de gráficas ni de mapas

**Decision:** barras Tailwind por condado. Prohibido Leaflet, Chart.js, D3, eje de región.

## D14 — Período + granularidad + comparación

**Decision:** `desde`, `hasta`, `granularidad` (`mes` | `trimestre` | `anio`), `comparacion`
(`ninguna` | `mom` | `yoy`). Sin editor de umbral. Comparación nula con motivo → **ausente**.
`cobertura-de-respaldo` acepta granularidad omitida en backend; el cliente **igual** envía las
cuatro claves para no tener dos modos de filtro.

## D15 — Carga por zona

**Decision:** cada zona su GET. Un 500 en pérdida de señal no borra el héroe de ratio.

## D16 — Condado, no región

**Decision:** se pintan las claves que trae el payload (condado). Prohibido `groupBy` región o
país en cliente. Prohibido un informe de «alcance geográfico».

## D17 — Sin identidad

**Decision:** ninguna columna de nombre, placa, teléfono, foto identificable o coordenadas.

## D18 — Vacío vs cero vs sin_dato vs sin_capacidad

| Señal | Estado |
|---|---|
| `data: []` en latencia / respaldo | **vacio** |
| condado con 0 demanda y fila presente | **dato**: cero real |
| p95 `null` | **sin_dato** en esa cifra |
| demanda > 0 y sin unidades vigentes | **sin_capacidad** |
| comparación nula con motivo | **ausente** |
| `cumple: null` | **sin calibrar**, no rojo |

## D19 — Sidebar: cuatro enlaces, roles distintos

**Decision:** grupo `Estratégico`, después de OE6. Partner **ausente**. Financiero **ausente**.
Tecnológico **ausente**. Operaciones sin Respaldo. Expansión sin Latencia ni Calidad.

## D20 — Copiar, no compartir con OE6

**Decision:** duplicar `pantalla-z` y `apoyo-plegable` en `oe3/`. Un cambio de copy de vidas no
debe romper capacidad.
