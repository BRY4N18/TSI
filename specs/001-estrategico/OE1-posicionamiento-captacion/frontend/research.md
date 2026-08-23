# Research — OE1 frontend

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z de OE2, no extraer `shared/`

**Decision:** módulo `estrategico/oe1/` espejo de `estrategico/oe2/`: una página parametrizada
por definiciones. No se importa `PantallaZPage` de OE2 ni de Partners. No se mueve la cáscara
a `shared/`.

**Rationale:** la spec y AGENTS.md: extraer ahora acopla OE1 y OE2. Copiar es el patrón ya
usado de táctico → OE2.

**Alternatives considered:** importar OE2 — acopla dos objetivos. Extraer `shared/informes-z/`
— fuera de alcance.

## D2 — Cuatro guards, nunca una unión

**Decision:**

| Guard | Roles | Pantalla |
|---|---|---|
| `oe1IngresoGuard` | `DirectorFinanciero` · `Gerente` | ingreso |
| `oe1CarteraGuard` | `DirectorEstrategia` · `Gerente` | cartera |
| `oe1CaptacionGuard` | `DirectorMarketing` · `Gerente` | captacion |
| `oe1CicloGuard` | `Gerente` | ciclo |

**Rationale:** FR-UI-019. Un `canActivate` único le daría al Financiero el churn (el backend
responde 403, pero el menú ya habría descubierto la superficie). El HTTP permite segmento al
Financiero; el **menú** de Cartera no se lo da (spec US2). Si dirección exige segmento en
Ingreso, se añade el bloque allí — no se abre Cartera al Financiero «por si acaso».

**Alternatives considered:** reusar guards de OE2 — roles distintos. Un guard unión — viola §4.1.

## D3 — Rutas bajo `/estrategico/oe1/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Ingreso | `/estrategico/oe1/ingreso` |
| Cartera | `/estrategico/oe1/cartera` |
| Captación | `/estrategico/oe1/captacion` |
| Ciclo | `/estrategico/oe1/ciclo` |

Grupo de sidebar **Estratégico**, no «Suscripciones» ni «Ventas».

**Rationale:** mezclarlas con el MRR táctico pondría dos MRR en el mismo grupo.

## D4 — Envelope `{ data, meta }`

**Decision:** el cliente tipa `data` como array y lee `meta.cobertura`, `meta.falta`,
`meta.alcance`, `meta.objetivo`, `meta.comparacion`. Prohibido `data.resultados` o
`acotado_a`.

## D5 — Recuento y parcial van con el MRR

**Decision:** el héroe de Ingreso pinta importe, recuento y `cobertura` **en el mismo bloque**.
`cobertura === 'parcial'` → `zona-parcial`. Prohibido un número solo.

**Rationale:** FR-UI-007. Con n=4, un MRR huérfano se lee como KPI de empresa.

## D6 — ARR es copy de alcance, no un segundo héroe

**Decision:** el ARR alimenta la zona de **lectura**. El texto de extrapolación sale de
`meta.alcance`. Prohibido titular «ingreso anual comprometido».

## D7 — Sin librería de gráficas

**Decision:** número héroe + barras Tailwind. El embudo es una pila de barras con ceros
explícitos, no un chart de embudo de librería.

## D8 — Período + granularidad + comparación

**Decision:** `desde`, `hasta`, `granularidad` (`mes` | `trimestre` | `anio`), `comparacion`
(`ninguna` | `mom` | `yoy`). Sin editor de umbral de muestra. Comparación nula con motivo →
**ausente**, no 400 de UI.

## D9 — E1-05/07/08 no existen en UI

**Decision:** ningún slug `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado` en
definiciones, rutas ni GET. Ningún mapa.

**Rationale:** FR-UI-018. Un recuadro vacío de CAC se leería como 0 €.

## D10 — Carga por zona

**Decision:** cada zona dispara su GET. Un 500 en renovación no borra el héroe de MRR.

## D11 — Segmento = tipo; desconocidos visibles

**Decision:** Cartera pinta `tipo` (o equivalente del payload). Prohibido agrupar por país.
Filas de tipo vacío/desconocido **se muestran**.

## D12 — Embudo: ceros visibles, volumen no «arreglado»

**Decision:** todas las etapas del payload se pintan, incluidas `transiciones = 0`. El cliente
**no** reordena ni rellena etapas. Si el volumen crece, no se oculta: se declara (el backend
ya no lo corrige en silencio).

## D13 — Churn: n bajo → sin %

**Decision:** si el backend manda `pct_churn` nulo o cobertura parcial por muestra, la UI
muestra **sin porcentaje cerrado**, no `25 %`. El recuento `n` sigue visible.

## D14 — Onboarding en proceso aparte

**Decision:** `en_proceso` no se pinta como 0 días en la mediana. Zona distinta o línea
etiquetada.

## D15 — Vacío vs cero

| Señal | Estado |
|---|---|
| `data: []` en flujo | **vacio** |
| etapa con `transiciones = 0` | **dato**: cero real |
| MRR con vigentes | **dato**, aunque el flujo esté vacío |
| `pct_churn` null | **sin_dato** en el %, `n` visible |
| comparación nula con motivo | **ausente** |

## D16 — Sidebar: cuatro enlaces, roles partidos

**Decision:** grupo `Estratégico`. PartnerIntegracion **ausente**. Administrador **ausente**.
DirectorExpansion **ausente** (no hay mercados que mostrar).

## D17 — Copiar, no compartir con OE2

**Decision:** duplicar `pantalla-z` y `apoyo-plegable` dentro de `oe1/`. Un cambio de copy de
OE2 no debe romper OE1 en caliente.
