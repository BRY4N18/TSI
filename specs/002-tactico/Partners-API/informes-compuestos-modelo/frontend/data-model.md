# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 13 informes viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Pantalla de historia

Una de tres. Identificador estable: `consumo` | `incorporacion` | `entrega`.

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
| `periodo` | Único filtro global, arriba derecha | ninguno — control |
| `visual` | Distribución o serie, diagonal | ver contrato UI |
| `lectura` | Implicación, abajo derecha | ver contrato UI |
| `apoyo` | Segundo plano, plegado en `consumo` e `incorporacion` | ver contrato UI |

No hay zona `alcance`: el envelope no envía `acotado_a` (research D4).

Cada zona que pide datos tiene: `informe` (clave de `PUBLICADOS`), estado
`carga | dato | vacio | error | sin_dato`, y **no** comparte spinner con las otras — salvo
Entrega, donde héroe y lectura **comparten** el GET de integración (research D9).

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Fechas inclusive. Defecto: últimos 30 días (backend) |
| Única acción global | Cambiarlo refresca **todas** las zonas de la pantalla |

No hay editor de `percentil`, `muestra_minima`, `mes` ni `dias_aviso_expiracion`. Viajan los
defectos del servidor.

### Envelope de lectura

| Campo | Regla |
|---|---|
| `data.resultados` | Filas del informe. Array vacío → zona **vacio** |
| `data.periodo` | El corte que el backend aplicó |
| `meta.periodo` | Eco del rango pedido |
| `meta.nota_muestras` | Presente en informes de `INFORMES_MUESTRAS` cuando hay filas no fiables |
| `meta.filtros` | Eco; no se edita en esta capa |

### Lectura derivada (no llega como columna de negocio)

| Concepto | Cómo se obtiene |
|---|---|
| Trío p95/media/muestras | misma(s) fila(s) de `latencia-p95` (D6) |
| No fiable | `percentil_fiable = 0` y/o `meta.nota_muestras` |
| Implicación del 100 % | misma fila de integración: `con_integracion` vs `clientes_totales` (D9) |
| Sin dato | porcentaje, p95 o `dias` `null` |
| Cero de partner | `llamadas = 0` en una fila presente (D16) |
| En proceso | `en_proceso = 1` y `dias` nulo |

## Validaciones de pantalla

- `resultados: []` → estado **vacio**, no héroe en 0 ms / 0 %.
- Una fila con `pct = null` o `dias = null` (y no en proceso) → **sin dato**, no 0.
- `percentil_fiable = 0` → se pinta la cifra **y** la marca; no se oculta la fila.
- Prohibido pintar columnas que no estén en el contrato UI de esa zona.
- Prohibido IP, secreto, contacto técnico, ejecutor, mapas, zona geográfica.
- Prohibido un total que sume `limite_cupo` + `autorizacion` + `error_servicio`.
- Prohibido agrupar adopción solo por `version`.
- Prohibido navegar desde una fila a la consola de logs o al portal de consumo.
- Un partner con `llamadas = 0` se muestra; no se filtra en cliente.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—n Informe publicado (CATALOGO)
Listado simple / consola / portal  —  no tiene zona en esta capa
```
