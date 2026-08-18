# Módulo: OE4 — Registro Histórico como Ventaja Competitiva e Inteligencia Predictiva

**Ubicación:** `specs/001-estrategico/OE4-inteligencia-predictiva/`
**Objetivo estratégico:** OE4 · **Perspectiva BSC:** Aprendizaje y crecimiento
**Feature paraguas:** `001-estrategico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../002-tactico/modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Por qué OE4 va después de OE6

Es el **segundo objetivo con sustrato**. Sus quince informes se apoyan casi enteros en
`hecho_accidente` y `hecho_evidencia`, que Emergencias ya cargó y verificó. Los compuestos tácticos
de los siete departamentos **ya están** (2026-08-18); OE2 tiene plan; OE1 y OE5 siguen en spec.

## Los quince informes

| # | Informe | Historia | Estado |
|---|---|:--:|:--:|
| **E4-01** | Índice consolidado de calidad del histórico | US1 | 🔴 migra tabla legada |
| **E4-02** | Completitud de campos críticos | US1 | ✅ |
| **E4-03** | Campos con mayor tasa de ausencia | US1 | ✅ |
| **E4-04** | Calidad por origen: captura central vs campo | US1 | ✅ |
| **E4-05** | Mapa de concentración de siniestralidad | US2 | ✅ |
| **E4-06** | Patrón horario y climático | US2 | ✅ 🆕 columna *(clima escaso)* |
| **E4-12** | Impacto humano por zona | US2 | ✅ |
| **E4-13** | Impacto vial por zona | US2 | ✅ 🆕 columna |
| **E4-15** | Cobertura del histórico por zona | US3 | ✅ *(por condado)* |
| **E4-14** | Latencia de ingesta al analítico | US3 | ⛔ la idempotencia lo impide |
| **E4-07** | Precisión del modelo predictivo | US4 | ⛔ |
| **E4-08** | Contraste predicción vs ocurrencia | US4 | ⛔ |
| **E4-09** | Unidades preposicionadas | US4 | ⛔ |
| **E4-10** | Versiones del modelo predictivo | US4 | ⛔ |
| **E4-11** | Productos de inteligencia comercializados | US4 | ⛔ |

**Nueve construibles, seis bloqueados** *(recuento tras `/plan`)*. Los cinco de US4 esperan tres
tablas que no existen; E4-14 lo impide la regla de idempotencia del modelo.

> **El reparto cambió en `/plan`**: E4-06 y E4-13 pasaron de parciales a completos —el clima y la
> distancia **sí existen en el origen**, solo faltaba cargarlos— y E4-14 pasó de construible a
> bloqueado. Ver [`backend/research.md`](backend/research.md) D3–D5.

## Capas

| Capa | Ruta | Estado |
|---|---|---|
| **Backend** | [`backend/`](./backend/) | **implementado** (9 publicados, 6 → 404) |
| Frontend | *(pendiente)* | aplazada |

## Lo que hay que saber antes de tocar este módulo

**E4-01 ya existe, y con el diseño que el proyecto abandonó.** `indice_calidad_historico` es una tabla
precalculada, una por informe — exactamente el patrón que el modelo analítico sustituyó. Se migra.

**Este es el objetivo cuyo dato de origen es más pobre.** La calificación de cierre tiene **0 filas**,
el resultado de atención **1**, y hay **3 fotografías** en 4 252 casos. Varios informes van a devolver
cifras cercanas a cero, y **es correcto**: el trabajo del módulo es que se lean como «no se registra»
y no como «no ocurre».

**El eje de región no existe** (`decisiones-pendientes.md` #38). E4-15 agrupa por condado.

## Documentos que lo gobiernan

- [`contrato-informes-estrategicos.md`](../contrato-informes-estrategicos.md)
- [`acceso-estrategico.md`](../acceso-estrategico.md) §4.4 — `DirectorDatos`, con `DirectorOperaciones`
  en los que miden el expediente de accidente
- [`OE6-respuesta-y-vidas/`](../OE6-respuesta-y-vidas/OE6-respuesta-y-vidas.md) — el piloto, cuyas
  piezas transversales (período, objetivo, envelope, permisos) **este módulo reutiliza sin rehacer**
- `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §4
