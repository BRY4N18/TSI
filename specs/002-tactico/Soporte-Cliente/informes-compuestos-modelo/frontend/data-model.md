# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 9 informes viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Pantalla de historia

Una de tres. Identificador estable: `cumplimiento` | `cola` | `tendencias`.

| Campo | Regla |
|---|---|
| `id` | Coincide con el segmento de ruta |
| `titulo` | Lo que lee el Gerente / agente en el H1 |
| `pregunta` | Subtítulo: la pregunta de la spec |
| `zonas` | Exactamente las cuatro del patrón Z, más `apoyo` opcional |

### Zona Z

| Zona | Qué contiene | Informes (ids de backend) |
|---|---|---|
| `heroe` | Métrica principal, arriba izquierda | ver contrato UI |
| `periodo` | Único filtro global, arriba derecha | ninguno — control |
| `alcance` | `todos` / `propios`, junto al período | viene en `meta.acotado_a` de cualquier GET de la pantalla |
| `visual` | Distribución o serie, diagonal | ver contrato UI |
| `lectura` | Implicación, abajo derecha | ver contrato UI |
| `apoyo` | Segundo plano, plegado en `cumplimiento` | ver contrato UI |

Cada zona que pide datos tiene: `informe` (clave de `PUBLICADOS`), estado
`carga | dato | vacio | error | sin_dato`, y **no** comparte spinner con las otras — salvo
Tendencias, donde héroe y visual **comparten** el GET de carga (research D10).

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Fechas inclusive. Defecto: últimos 30 días (backend) |
| Única acción global | Cambiarlo refresca **todas** las zonas de la pantalla |

No hay editor de `granularidad`, `eje` ni `minimo` en el MVP. Viajan los defectos del servidor.

`agrupar_por` **no** es período: es un control local del tablero (research D9).

### Alcance de vista

| Valor | Quién lo recibe hoy | Qué se lee |
|---|---|---|
| `todos` | Gerente de Éxito del Cliente | departamento entero |
| `propios` | Agente de soporte, Administrador | tickets del solicitante |

Se pinta **siempre** que el envelope lo traiga. No se infiere del rol.

### Envelope de lectura

| Campo | Regla |
|---|---|
| `data.resultados` | Filas del informe. Array vacío → zona **vacio** |
| `data.declaraciones` | Lista (puede ser `[]`). Cada `mensaje` se muestra junto a la zona |
| `data.periodo` | El corte que el backend aplicó (tablero: puede diferir del operativo) |
| `meta.acotado_a` | `todos` \| `propios` |
| `meta.periodo` | Eco del rango pedido |

### Lectura derivada (no llega como columna de negocio)

| Concepto | Cómo se obtiene |
|---|---|
| Par cumplimiento/cobertura | misma fila: `pct_cumplimiento` + `pct_sin_compromiso` (D7) |
| Último bucket | última fila de `resultados` ordenada por `periodo` o `dia`; no se suma la serie |
| Saldo del día | `creados - resueltos` de esa fila (campos ya entregados) |
| Sin dato | porcentaje o media `null` (FR-UI-007) |
| Cero de serie | `tickets = 0` / `creados = 0` en una fila presente (D15) |
| Hueco de servicio | declaración `servicio_no_registrado` / `eje_servicio_sustituido` |

## Validaciones de pantalla

- `resultados: []` → estado **vacio**, no héroe en 0 %.
- Una fila con `pct_* = null` o `media_resolucion_s = null` → **sin dato**, no 0 %.
- Prohibido pintar columnas que no estén en el contrato UI de esa zona.
- Prohibido asunto, descripción, mensajes, notas, nombre de agente, nombre de cliente, mapas.
- Prohibido un total que sume `con_escalado_automatico` + `con_escalado_humano`.
- `id_agente` / `id_cliente` solo como clave; no se resuelven a persona.
- Prohibido navegar desde una fila al detalle operativo del ticket.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—n Informe publicado (CATALOGO)
Listado simple / dashboard operativo  —  no tiene zona en esta capa
```
