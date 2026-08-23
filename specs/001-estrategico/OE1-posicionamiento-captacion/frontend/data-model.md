# Data model — pantalla OE1 (no el almacén)

Esta capa **no crea tablas**. El modelo analítico vive en [`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla compone.

## Entidades de interacción

### Pantalla de historia

Una de cuatro. Identificador = segmento de ruta: `ingreso` | `cartera` | `captacion` | `ciclo`.

| Campo | Regla |
|---|---|
| `id` | Coincide con la ruta |
| `titulo` | H1 |
| `pregunta` | Subtítulo de la spec |
| `zonas` | Cuatro del Z + `apoyo` opcional |
| `guard` | uno de los cuatro |

### Zona Z

| Zona | Informes (slugs backend) |
|---|---|
| `heroe` (ingreso) | `mrr-mensual` |
| `visual` (ingreso) | mismo GET: variación / comparación |
| `lectura` (ingreso) | `arr-proyeccion` (`meta.alcance`) |
| `apoyo` (ingreso) | `tasa-renovacion` |
| `heroe` (cartera) | `cartera-por-plan` |
| `visual` (cartera) | mismo GET: evolución de mezcla |
| `lectura` (cartera) | `mrr-por-segmento` (tipo, no país) |
| `heroe` (captacion) | `embudo-conversion` (tasa de paso) |
| `visual` (captacion) | mismo GET: etapas, ceros visibles |
| `lectura` (captacion) | cruce Ventas–Cuentas si `meta.alcance` |
| `apoyo` (captacion) | `velocidad-ciclo-venta` |
| `heroe` (ciclo) | `churn-por-cohorte` |
| `visual` (ciclo) | `abandono-onboarding` |
| `lectura` (ciclo) | `tiempo-onboarding` (`en_proceso` aparte) |

Cada zona: estado `carga | dato | vacio | error | sin_dato`. Spinner **por zona**.

### Controles globales

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Obligatorios. Inclusive. |
| `granularidad` | `mes` \| `trimestre` \| `anio` |
| `comparacion` | `ninguna` \| `mom` \| `yoy`. Defecto `ninguna` |

Cambiar cualquiera refresca **todas** las zonas. No hay editor de umbral de muestra.

### Envelope de lectura

| Campo | Regla |
|---|---|
| `data` | Array. `[]` → zona **vacio** (flujo) |
| `meta.periodo` | Eco |
| `meta.comparacion` | Objeto o nulo con motivo |
| `meta.objetivo` | Meta BSC si viene |
| `meta.cobertura` | `completa` \| `parcial` |
| `meta.falta` | Lista; se pinta si parcial |
| `meta.alcance` | Texto; obligatorio en ARR y renovación |

Prohibido mapear a `data.resultados` (táctico). Prohibido `acotado_a`.

## Validaciones de pantalla

- `data: []` en flujo → **vacio**, no 0 € / 0 %.
- Recuento de MRR siempre junto al importe.
- `pct_churn` null → **sin_dato** en el %, `n` visible.
- Etapa `transiciones = 0` → **dato** (cero real).
- Prohibido agrupar por país.
- Prohibido columnas de cobro, ficha, contacto.
- Prohibido slugs `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado`.
- Prohibido `acotado_a`.

## Relación con el backend

Los slugs y query params son los del OpenAPI. Un 404 de CAC no se llama. Un 403 de Marketing en Ingreso es exclusión, no vacío.
