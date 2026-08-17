# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 15 informes viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Materia

Decide **quién ve la pantalla**, no solo quién entra al dato.

| Valor | Roles | Pantallas |
|---|---|---|
| `crecimiento` | Director de Expansión, Administrador | `flota`, `mercados` |
| `validacion` | Director Tecnológico, Administrador | `validacion` |

Un informe sin materia en el backend no se pinta. El catálogo UI MUST coincidir con `MATERIAS`.

### Pantalla de historia

Una de tres. Identificador estable: `flota` | `mercados` | `validacion`.

| Campo | Regla |
|---|---|
| `id` | Coincide con el segmento de ruta |
| `titulo` | Lo que lee el director en el H1 |
| `pregunta` | Subtítulo: la pregunta de la spec |
| `materia` | `crecimiento` o `validacion` — el guard de la ruta MUST coincidir |
| `zonas` | Exactamente las cuatro del patrón Z, más `apoyo` opcional |

### Zona Z

| Zona | Qué contiene | Informes (ids de backend) |
|---|---|---|
| `heroe` | Métrica principal, arriba izquierda | ver contrato UI |
| `periodo` | Único filtro, arriba derecha | ninguno — control |
| `visual` | Distribución o serie, diagonal | ver contrato UI |
| `lectura` | Implicación, abajo derecha | ver contrato UI |
| `apoyo` | Segundo plano, plegado en `flota` y `mercados` | ver contrato UI |

Cada zona que pide datos tiene: `informe` (clave de `PUBLICADOS`), estado
`carga | dato | vacio | error | sin_dato`, y **no** comparte spinner con las otras.

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Fechas inclusive. Defecto: últimos 30 días (backend) |
| Única acción | Cambiarlo refresca **todas** las zonas de la pantalla |

No hay editor de umbral, objetivo ni `top` (research D7). Esos valores se **leen** de `meta.filtros`.

### Envelope de lectura

Campos de `meta` que esta capa está obligada a conservar (no recalcular):

| Campo | Cuándo importa |
|---|---|
| `periodo` | las tres |
| `filtros` | umbral, `dias_objetivo`, `top` |
| `medida_exacta_desde` | despublicación (y puesta en operación si el backend la emite) |
| notas (`nota_umbral`, `nota_objetivo`, `nota_historico`, `nota_grano`, `nota_region`, `nota`) | junto a la cifra |

### Lectura que no se inventa en cliente

| Concepto | Cómo se obtiene |
|---|---|
| Sin alternativas | `sin_alternativas === true` |
| Disponibilidad ausente | `pct_disponibilidad === null` (0 es otra cosa: estuvo medida y no disponible) |
| Días / cumplimiento ausentes | `dias === null` / `cumple_objetivo === null` |
| Tasa ausente | `pct_aprobacion_primer_intento === null` |
| Grano de intentos | texto del contrato UI + nota del envelope si viene |
| Vacío ≠ nunca pasó | `data: []` **y** `medida_exacta_desde` visible |

## Validaciones de pantalla

- `data: []` → estado **vacío**, no héroe en 0 %. En despublicación, el vacío **lleva** la fecha de
  medida exacta.
- Una fila con porcentaje `null` → **sin dato**, no 0 %.
- Prohibido pintar columnas que no estén en el contrato UI de esa zona.
- Prohibido coordenadas, identidad (validador), contacto de proveedor.
- Prohibido unir visualmente estados de unidad contra un catálogo de tres valores: se pinta el
  texto que llegó.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—1 Informe publicado (CATALOGO)
Pantalla 1—1 Materia (crecimiento | validacion)
Materia 1—n Rol que entra
```
