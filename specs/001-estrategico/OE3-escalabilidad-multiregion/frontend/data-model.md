# Data model — pantalla OE3 (no el almacén)

Esta capa **no crea tablas**. El modelo analítico vive en [`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla compone.

## Entidades de interacción

### Pantalla de historia

Una de cuatro. Identificador = segmento de ruta: `latencia` | `calidad` | `capacidad` | `respaldo`.

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
| `heroe` (latencia) | `latencia-asignacion` |
| `visual` (latencia) | `evolucion-latencia` |
| `lectura` (latencia) | `meta.alcance` / recuento; vacío ≠ 0 min |
| `heroe` (calidad) | `tasa-error-registro` |
| `visual` (calidad) | `primer-intento` |
| `lectura` (calidad) | campos comprobados; E3-11 sin semáforo |
| `heroe` (capacidad) | `ratio-demanda-capacidad` |
| `visual` (capacidad) | mismos datos: condados tensos vs **sin capacidad** |
| `lectura` (capacidad) | `meta.alcance` (flota del período) |
| `apoyo` (capacidad) | `perdida-de-senal` |
| `heroe` (respaldo) | `cobertura-de-respaldo` |
| `visual` (respaldo) | disponible vs solo alta |
| `lectura` (respaldo) | denominador; vacío ≠ 0 % |

Cada zona: estado `carga | dato | vacio | error | sin_dato | sin_capacidad`. Spinner **por zona**.

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
| `meta.objetivo` | Meta BSC; `cumple` booleano solo en E3-02 y E3-10 |
| `meta.cobertura` | `completa` \| `parcial` |
| `meta.falta` | Lista; se pinta si parcial |
| `meta.alcance` | Texto; obligatorio en latencia (proceso, no algoritmo) y capacidad (flota del período) |

Prohibido `data.resultados`. Prohibido `acotado_a`.

## Validaciones de pantalla

- `data: []` en tiempos → **vacio**, no 0 min ni meta cumplida.
- p95, recuento y `cumple` juntos; p95 `null` → sin_dato.
- Condado con demanda y sin flota → **sin_capacidad**, no infinito.
- Tasas: numerador y denominador visibles.
- `primer-intento` con `cumple` nulo → sin semáforo cerrado.
- Prohibido columnas de nombre, placa, lat/lon.
- Prohibido slugs bloqueados.
- Prohibido agrupar por región en cliente.

## Relación con el backend

Los slugs y query params son los de `oe3_service.PUBLICADOS`. Un 403 de Partner o de Expansión
en latencia es exclusión, no vacío. Un 404 de bloqueado no se pinta como tarjeta.
