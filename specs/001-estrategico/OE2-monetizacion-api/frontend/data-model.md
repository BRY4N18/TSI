# Data model — pantalla OE2 (no el almacén)

Esta capa **no crea tablas**. El modelo analítico vive en [`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla compone.

## Entidades de interacción

### Pantalla de historia

Una de tres. Identificador = segmento de ruta: `uso` | `dinero` | `ecosistema`.

| Campo | Regla |
|---|---|
| `id` | Coincide con la ruta |
| `titulo` | H1 |
| `pregunta` | Subtítulo de la spec |
| `zonas` | Cuatro del Z + `apoyo` opcional |
| `guard` | `uso-ecosistema` o `dinero` |

### Zona Z

| Zona | Informes (slugs backend) |
|---|---|
| `heroe` (uso) | `integraciones-activas` |
| `visual` (uso) | `taxonomia-errores` |
| `lectura` (uso) | `consumo-por-partner` |
| `apoyo` (uso) | `latencia-por-endpoint` |
| `heroe` (dinero) | `excedente-facturable` |
| `visual` (dinero) | mismo GET: filas `no_tarificable` |
| `lectura` (dinero) | alcance de `meta.alcance` |
| `apoyo` (dinero) | `participacion-ingresos-api`, `mrr-por-linea` |
| `heroe` (ecosistema) | `crecimiento-ecosistema` |
| `visual` (ecosistema) | `adopcion-versiones` |
| `lectura` (ecosistema) | `comparativa-partners` |

Cada zona: estado `carga | dato | vacio | error | sin_dato`. Spinner **por zona**.

### Controles globales

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Obligatorios. Inclusive. |
| `granularidad` | `mes` \| `trimestre` \| `anio` |
| `comparacion` | `ninguna` \| `mom` \| `yoy`. Defecto `ninguna` |

Cambiar cualquiera refresca **todas** las zonas. No hay editor de `muestra_minima`.

### Envelope de lectura

| Campo | Regla |
|---|---|
| `data` | Array de filas. `[]` → zona **vacio** |
| `meta.periodo` | Eco |
| `meta.comparacion` | Objeto o nulo con motivo |
| `meta.objetivo` | Meta BSC si viene |
| `meta.cobertura` | `completa` \| `parcial` |
| `meta.falta` | Lista; se pinta si cobertura parcial |
| `meta.alcance` | Texto; obligatorio de mostrar en excedente |

Prohibido mapear a `data.resultados` (táctico).

### Lectura derivada (no se calcula negocio)

| Concepto | Origen |
|---|---|
| Trío latencia | mismas filas de `latencia-por-endpoint` |
| No fiable | `percentil_fiable = 0` o p95 `null` |
| Parcial | `meta.cobertura` |
| No cobrado | `meta.alcance` |
| Dos `'v1'` | dos filas `(servicio, version)` |

## Validaciones de pantalla

- `data: []` → **vacio**, no 0 ms / 0 % uptime.
- p95 `null` → **sin dato**, fila visible.
- `llamadas = 0` en fila presente → cero real.
- Prohibido sumar 4xx+5xx.
- Prohibido agrupar adopción solo por `version`.
- Prohibido columnas de IP, secreto, contacto.
- Prohibido slug `disponibilidad-api`.
- Prohibido `acotado_a`.

## Relación con el backend

Los slugs y query params son los del OpenAPI. Un 404 de `disponibilidad-api` no se llama. Un 403 de partner o de Financiero en Uso es exclusión, no vacío.
