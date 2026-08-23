# Data model — pantalla OE5 (no el almacén)

Esta capa **no crea tablas**. El modelo analítico vive en [`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla compone.

## Entidades de interacción

### Pantalla de historia

Una de cuatro. Identificador = segmento de ruta: `servicio` | `ingresos` | `planes` | `riesgo`.

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
| `heroe` (servicio) | `cumplimiento-sla` |
| `visual` (servicio) | `evolucion-incumplimiento` |
| `lectura` (servicio) | `meta.alcance` del SLA (sin compromiso aparte) |
| `apoyo` (servicio) | `rendimiento-por-agente`, `reincidencia-soporte` |
| `heroe` (ingresos) | `retencion-neta-ingresos` (neto) |
| `visual` (ingresos) | mismo GET: expansión / contracción / churn |
| `lectura` (ingresos) | `meta.alcance` (precio congelado) |
| `heroe` (planes) | `sla-por-plan` |
| `visual` (planes) | `movimientos-de-plan` (aprobados) |
| `lectura` (planes) | `antiguedad-de-cuenta` (activas; cerradas aparte) |
| `heroe` (riesgo) | `cuentas-en-riesgo` |
| `visual` (riesgo) | mismo GET: señales presentes |
| `lectura` (riesgo) | `meta.falta` / alcance: fuentes faltantes; una señal no basta |

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
| `data` | Array. `[]` → zona **vacio** (compromiso / flujo) |
| `meta.periodo` | Eco |
| `meta.comparacion` | Objeto o nulo con motivo |
| `meta.objetivo` | Meta BSC si viene |
| `meta.cobertura` | `completa` \| `parcial` |
| `meta.falta` | Lista; se pinta si parcial (obligatorio en riesgo) |
| `meta.alcance` | Texto; obligatorio en SLA y NRR |

Prohibido mapear a `data.resultados` (táctico). Prohibido `acotado_a`.

## Validaciones de pantalla

- `data: []` en SLA → **vacio**, no 0 %.
- Recuento de cerrados con compromiso siempre junto al %.
- Una señal de riesgo → no se pinta como cuenta en riesgo (el backend ya filtra; la UI no «completa»).
- Movimiento pendiente → no aparece (solo aprobados).
- Prohibido agrupar agente por nombre.
- Prohibido columnas de ticket, cobro, contacto.
- Prohibido slugs `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding`.
- Prohibido `acotado_a`.

## Relación con el backend

Los slugs y query params son los del OpenAPI. Un 404 de NPS no se llama. Un 403 de Financiero en Servicio es exclusión, no vacío.
