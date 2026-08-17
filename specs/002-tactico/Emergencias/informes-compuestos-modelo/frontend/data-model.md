# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 13 informes viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Pantalla de historia

Una de tres. Identificador estable: `calidad` | `despacho` | `cierre`.

| Campo | Regla |
|---|---|
| `id` | Coincide con el segmento de ruta |
| `titulo` | Lo que lee el Director en el H1 |
| `pregunta` | Subtítulo: la pregunta de la spec |
| `zonas` | Exactamente las cuatro del patrón Z, más `apoyo` opcional |

### Zona Z

| Zona | Qué contiene | Informes (ids de backend) |
|---|---|---|
| `heroe` | Métrica principal, arriba izquierda | ver contrato UI |
| `periodo` | Único filtro, arriba derecha | ninguno — control |
| `visual` | Distribución o serie, diagonal | ver contrato UI |
| `lectura` | Implicación, abajo derecha | ver contrato UI |
| `apoyo` | Segundo plano, plegado en `cierre` | ver contrato UI |

Cada zona que pide datos tiene: `informe` (clave de `PUBLICADOS`), estado `carga | dato | vacio | error | sin_dato`, y **no** comparte spinner con las otras.

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Fechas inclusive. Defecto: últimos 30 días (backend) |
| Única acción | Cambiarlo refresca **todas** las zonas de la pantalla |

No hay granularidad en esta capa: se usa el defecto del backend. `tramos_dias` de envejecimiento
queda en el defecto del servidor (`1,3,7,30`); no se expone un editor en el MVP.

### Lectura derivada (no llega como columna)

| Concepto | Cómo se obtiene |
|---|---|
| Campos comprobados | Constante de definición: `severidad`, `condado` (D6) |
| Sin capacidad | `casos > 0` y (`unidades_vigentes = 0` o `ratio` nulo) (D7) |
| Sin dato | porcentaje o desviación `null` (FR-UI-007) |
| Advertencia de desviación | `meta.nota_referencia` si viene; si no, el texto fijo del contrato UI |

## Validaciones de pantalla

- `data: []` → estado **vacío**, no héroe en 0 %.
- Una fila con `pct_* = null` → **sin dato**, no 0 %.
- Prohibido pintar columnas que no estén en el contrato UI de esa zona.
- Prohibido coordenadas, identidad, texto libre.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—1 Informe publicado (CATALOGO ∩ PUBLICADOS)
Informe vigilado  —  no tiene zona
```
