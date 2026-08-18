# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 13 informes viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Materia

Decide **quién ve la pantalla**, no solo quién entra al dato.

| Valor | Roles | Pantallas |
|---|---|---|
| `finanzas` | Director Financiero, Administrador | `cobro`, `movimientos` |
| `catalogo` | Director de Estrategia, Administrador | `catalogo` |

Un informe sin materia en el backend no se pinta. El catálogo UI MUST coincidir con `MATERIAS`.

### Pantalla de historia

Una de tres. Identificador estable: `cobro` | `movimientos` | `catalogo`.

| Campo | Regla |
|---|---|
| `id` | Coincide con el segmento de ruta |
| `titulo` | Lo que lee el director en el H1 |
| `pregunta` | Subtítulo: la pregunta de la spec |
| `materia` | `finanzas` o `catalogo` — el guard de la ruta MUST coincidir |
| `zonas` | Exactamente las cuatro del patrón Z, más `apoyo` opcional |

### Zona Z

| Zona | Qué contiene | Informes (ids de backend) |
|---|---|---|
| `heroe` | Métrica principal, arriba izquierda | ver contrato UI |
| `periodo` | Único filtro, arriba derecha | ninguno — control |
| `mes` | Mes natural declarado, junto al período | viene en `meta.mes` / `meta.nota_periodo` de MRR o NRR |
| `visual` | Distribución o serie, diagonal | ver contrato UI |
| `lectura` | Implicación, abajo derecha | ver contrato UI |
| `apoyo` | Segundo plano, plegado en `cobro` y `movimientos` | ver contrato UI |

Cada zona que pide datos tiene: `informe` (clave de `PUBLICADOS`), estado
`carga | dato | vacio | error | sin_dato`, y **no** comparte spinner con las otras.

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Fechas inclusive. Defecto: últimos 30 días (backend) |
| Única acción | Cambiarlo refresca **todas** las zonas de la pantalla |

No hay editor de `escalones_dunning` ni de `dias_aviso_caducidad` (research D7). Esos valores se
**leen** de `meta.filtros`. No hay segundo selector de mes.

### Envelope de lectura

Campos de `meta` que esta capa está obligada a conservar (no recalcular):

| Campo | Cuándo importa |
|---|---|
| `periodo` | las tres |
| `filtros` | escalones, días de aviso |
| `mes` | MRR y NRR |
| `nota_periodo` | MRR y NRR: declara que se midió mes natural |

### Lectura que no se inventa en cliente

| Concepto | Cómo se obtiene |
|---|---|
| Cancelada fuera del MRR | cifra `mrr` del backend; no hay columna `activo` que pintar |
| Sin periodicidad | `sin_periodicidad` (aparte, nunca como 0 de MRR) |
| Notas de crédito restan | `notas_credito` visible junto a `facturado` / `ingreso_neto` |
| Disputa ≠ impago | no hay zona de «impagas»; dunning no las incluye |
| Pendiente fuera de la mediana | `pendientes` visible; `segundos_mediana` puede ser `null` |
| Downgrade por precio | `tipo_movimiento` tal cual llega |
| Plan precio cero | `clientes` > 0 y `mrr_aportado` = 0, ambas cifras |
| Dimensión API pendiente | `nota_dimension_pendiente`; **sin** campo de llamadas |
| Mes aplicado | `meta.mes` + `meta.nota_periodo` |
| Sin dato | porcentaje o mediana `null` |
| Vacío | `data: []` |

## Validaciones de pantalla

- `data: []` → estado **vacío**, no héroe en 0 %.
- Una fila con `pct_* = null` o `segundos_mediana = null` → **sin dato**, no 0.
- Prohibido pintar columnas que no estén en el contrato UI de esa zona.
- Prohibido medio de cobro, fiscal, identidad de quien resolvió, mapas, columna de llamadas.
- Prohibido un enlace desde «sin método» hacia el listado de métodos de pago.
- Importes: si el backend trae `moneda` (y periodicidad, cuando aplica), se muestran junto a la cifra.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—n Informe publicado (CATALOGO)
Pantalla 1—1 Materia (finanzas | catalogo)
Materia 1—n Rol que entra
Listado simple / catálogo de planes / billing  —  no tienen zona en esta capa
```
