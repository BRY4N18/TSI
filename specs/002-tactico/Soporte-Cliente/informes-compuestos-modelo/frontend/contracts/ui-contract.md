# Contrato UI — tres pantallas Z

**No redefine** [`../backend/contracts/informes-compuestos-soporte.openapi.yaml`](../backend/contracts/informes-compuestos-soporte.openapi.yaml).
Mapea **zona de pantalla → informe publicado → campos que la zona está obligada a mostrar**.

Prefijo de lectura: `GET /api/v1/informes-tacticos/soporte/{ruta}?desde=&hasta=`

| Id publicado | Ruta HTTP |
|---|---|
| `cumplimiento-sla` | `cumplimiento-sla` |
| `cumplimiento-sla-por-plan` | `cumplimiento-sla/por-plan` |
| `rendimiento-agentes` | `rendimiento-agentes` |
| `tickets-por-servicio` | `tickets-por-servicio` |
| `tablero-cola` | `tablero-cola` |
| `evolucion-incumplimiento` | `evolucion-incumplimiento` |
| `escalado-automatico` | `escalado-automatico` |
| `carga-entrante-resuelta` | `carga-entrante-resuelta` |
| `reincidencia-clientes` | `reincidencia-clientes` |

Roles que entran: `GerenteExitoCliente`, `Soporte`, `Administrador`. Cualquier otro: la pantalla
no existe para ellos (403 / access-denied). Cliente, Operador, `DesarrolladorAPIs` y
`DirectorTecnologico` **no** entran.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-alcance`, `zona-visual`,
`zona-lectura`, `zona-apoyo`.

Envelope: `data.resultados`, `data.declaraciones`, `meta.acotado_a`. Las declaraciones de cada
GET se leen **junto a la zona** que los pidió.

---

## Prohibido en las tres

Asunto, descripción, mensajes o notas internas; nombre de agente o de cliente; mapas; botones
de asignar / responder / escalar / cerrar; exportar; enlace al detalle operativo del ticket;
resolver `id_agente` / `id_cliente` a un nombre; total que sume escalado automático y humano;
columna de servicio en reincidencia.

---

## Pantalla `cumplimiento` — Cumplimiento de SLA

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `cumplimiento-sla` | De la **última** fila: `pct_cumplimiento`, `pct_sin_compromiso`, `con_compromiso`, `sin_compromiso`, `tickets`, `sin_compromiso_por_motivo`; meta ≥95 % | **el par viaja en el mismo bloque**; `pct_cumplimiento` nulo → **sin dato**, no 0 % |
| Período | — | `desde`, `hasta` | — |
| Alcance | — | `meta.acotado_a` | siempre visible |
| Visual | `cumplimiento-sla-por-plan` | `plan` (o «sin plan»), `pct_cumplimiento`, `pct_sin_compromiso`, `con_compromiso` | misma regla del par; no omitir «sin plan» |
| Lectura | `rendimiento-agentes` | `id_agente` (clave), `asignados`, `resueltos`, `reabiertos`, `media_resolucion_s`, `sin_resolver`, `incumplidos` | reapertura visible; media nula + `sin_resolver` a la vista; sin nombres |
| Apoyo plegado | `tickets-por-servicio` | `servicio`, `tickets`, `incumplidos` | fila **sin servicio** visible; declaración de que la operación no asigna |

Vista principal ≤ 8 bloques (héroe, período+alcance, visual, lectura, apoyo como **un** bloque
plegado).

---

## Pantalla `cola` — Cola en curso

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `tablero-cola` | `clave`, `tickets`, `sin_agente`, `sin_primera_respuesta`, `incumplidos`; control local `agrupar_por` | el período **se aplica**; declaración `periodo_acotado_difiere_del_tablero` visible; sin asignar aparece |
| Período | — | `desde`, `hasta` | — |
| Alcance | — | `meta.acotado_a` | siempre visible |
| Visual | `evolucion-incumplimiento` | `periodo`, `incumplidos`, `pct_cumplimiento` o el % de incumplimiento que traiga la fila, `tickets`, `pct_sin_compromiso` | un período con `tickets = 0` **se pinta en cero**, no se omite |
| Lectura | `escalado-automatico` | `tipo_incidencia`, `prioridad`, `tickets`, `con_escalado_automatico`, `con_escalado_humano`, `pct_escalado_automatico` | **dos** recuentos; prohibido un total suma; % nulo → sin dato |

Sin apoyo. Vacío: `resultados: []` → no mostrar 0 %.

---

## Pantalla `tendencias` — Tendencias

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `carga-entrante-resuelta` (última fila del **mismo** GET que el visual) | `dia`, `creados`, `resueltos`, saldo (`creados - resueltos`), `neto_acumulado` | saldo positivo = la cola crece |
| Período | — | `desde`, `hasta` | — |
| Alcance | — | `meta.acotado_a` | siempre visible |
| Visual | `carga-entrante-resuelta` | `dia`, `creados`, `resueltos`, `neto_acumulado` | días en cero **presentes**; no unir dos días distantes |
| Lectura | `reincidencia-clientes` | `id_cliente` (clave), `tipo_cliente`, `tickets`, `tipos_distintos`, `reaperturas` | declaración de eje (no servicio) visible; **sin** columna de servicio |

Un solo GET para héroe+visual (research D10). `eje` y `minimo` no se editan.

---

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | `resultados` con filas y métrica no nula | cifra / barras |
| sin_dato | métrica `null` con período que sí tiene contexto | «sin dato», nunca 0 |
| vacio | `resultados: []` | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |

## Navegación

Tres entradas de sidebar, grupo Soporte, roles del guard. No modificar «Informes de soporte»,
«Dashboard de soporte», «Cola de soporte», «Mis tickets» ni «Configuración de SLA».
