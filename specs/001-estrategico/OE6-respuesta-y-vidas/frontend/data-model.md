# Data model — pantalla OE6 (no el almacén)

Esta capa **no crea tablas**. El modelo analítico vive en [`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla compone.

## Entidades de interacción

### Pantalla de historia

Una de cuatro. Identificador = segmento de ruta: `llegada` | `diagnostico` | `ejecucion` | `personas`.

| Campo | Regla |
|---|---|
| `id` | Coincide con la ruta |
| `titulo` | H1 |
| `pregunta` | Subtítulo de la spec |
| `zonas` | Cuatro del Z + `apoyo` opcional |
| `guard` | el único `oe6Guard` |

### Zona Z

| Zona | Informes (slugs backend) |
|---|---|
| `heroe` (llegada) | `tiempo-respuesta-global` |
| `visual` (llegada) | `tiempo-respuesta-por-severidad` |
| `lectura` (llegada) | `meta.alcance` / recuento sin llegada |
| `heroe` (diagnostico) | `tramos-del-ciclo` |
| `visual` (diagnostico) | `origen-de-asignacion` |
| `lectura` (diagnostico) | `desviacion-de-llegada` (histórico, no ETA) |
| `heroe` (ejecucion) | `envejecimiento-de-casos-abiertos` |
| `visual` (ejecucion) | `rechazo-y-timeout-por-unidad`, `abortos-y-misiones-fallidas` |
| `lectura` (ejecucion) | `cierres-forzados` (`meta.alcance` = definición) |
| `apoyo` (ejecucion) | tasas con denominador si no caben en visual |
| `heroe` (personas) | `impacto-humano` |
| `visual` (personas) | `escaladas-de-severidad` |
| `lectura` (personas) | `cobertura-de-evidencia` |

Cada zona: estado `carga | dato | vacio | error | sin_dato`. Spinner **por zona**.

### Controles globales

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Obligatorios. Inclusive. |
| `granularidad` | `mes` \| `trimestre` \| `anio` |
| `comparacion` | `ninguna` \| `mom` \| `yoy`. Defecto `ninguna` |

Cambiar cualquiera refresca **todas** las zonas. No hay editor de umbral ni filtro de mapa.

### Envelope de lectura

| Campo | Regla |
|---|---|
| `data` | Array. `[]` → zona **vacio** |
| `meta.periodo` | Eco |
| `meta.comparacion` | Objeto o nulo con motivo |
| `meta.objetivo` | Meta BSC si viene |
| `meta.cobertura` | `completa` \| `parcial` |
| `meta.falta` | Lista; se pinta si parcial |
| `meta.alcance` | Texto; obligatorio en desviación y cierres forzados |

Prohibido `data.resultados`. Prohibido `acotado_a`.

## Validaciones de pantalla

- `data: []` en tiempos → **vacio**, no 0 min.
- Mediana, p95 y recuento juntos; p95 `null` → sin_dato.
- Casos sin llegada no se pintan como 0 min.
- Tasas: numerador y denominador visibles.
- Abortos `[]` → vacio, no 0 %.
- Prohibido columnas de nombre, placa, lat/lon.
- Prohibido slugs de OE3.
- Prohibido agrupar por región en cliente.

## Relación con el backend

Los slugs y query params son los del OpenAPI. Un 403 de Partner es exclusión, no vacío.
