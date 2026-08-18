# Contrato UI — tres pantallas Z, dos audiencias

**No redefine** [`../backend/contracts/informes-compuestos-suscripciones.openapi.yaml`](../backend/contracts/informes-compuestos-suscripciones.openapi.yaml).
Mapea **zona de pantalla → informe publicado → campos que la zona está obligada a mostrar**.

Prefijo de lectura: `GET /api/v1/informes-tacticos/suscripciones/{informe}?desde=&hasta=`

| Pantalla | Roles que entran | Roles que **no** entran (ni ven el enlace) |
|---|---|---|
| `cobro`, `movimientos` | `DirectorFinanciero`, `Administrador` | `DirectorEstrategia`, Cliente, Proveedor, Operador |
| `catalogo` | `DirectorEstrategia`, `Administrador` | `DirectorFinanciero`, Cliente, Proveedor, Operador |

Cualquier otro: la pantalla no existe para ellos (403 / access-denied). Un ítem deshabilitado **no**
cumple este contrato.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-mes`, `zona-visual`, `zona-lectura`,
`zona-apoyo`.

Los trece slugs publicados MUST aparecer en exactamente una zona de exactamente una pantalla.

---

## Prohibido en las tres

Medio de cobro (token, últimos dígitos, tipo de tarjeta); identificador fiscal; identidad de quien
resolvió una solicitud; mapas; botones de emitir / cobrar / cambiar plan / editar catálogo;
exportar; un tablero único de departamento; cualquier columna de llamadas API, ni vacía; enlace
desde clientes sin método hacia `/suscripciones/metodos-pago`.

---

## Pantalla `cobro` — Cobro e ingreso · materia `finanzas`

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `mrr` | `mrr`, `nuevo`, `expansion`, `contraccion`, `baja`, `variacion_neta`, `sin_periodicidad`, `moneda` | cancelada **no** está en la cifra; `sin_periodicidad` aparte, nunca como 0; los cuatro componentes se ven, no solo el neto |
| Período | — | `desde`, `hasta` | — |
| Mes | — | `meta.mes`, `meta.nota_periodo` | siempre visible en esta pantalla |
| Visual | `ingresos` | `plan`, `tipo_cliente`, `facturado`, `notas_credito`, `ingreso_neto`, `moneda` | las notas **restan**; el neto es menor que el facturado cuando hay crédito |
| Lectura | `tasa-renovacion` | `vencidas`, `renovadas`, `pct_renovacion` | `pct_renovacion` nulo → **sin dato**, no 0 % |
| Apoyo plegado | `cobro-primer-intento`, `efectividad-dunning`, `clientes-sin-metodo-pago` | `pagadas`, `primer_intento`, `tras_reintentos`, `pct_primer_intento`; `escalon`, `facturas_en_escalon`, `recuperadas`, `pct_recuperacion`; `nombre_comercial`, `tipo`, `estado_comercial`, `caduca_en_dias` | disputa **no** se lee como impago; escalones: `meta.filtros`; sin instrumento de cobro |

Vista principal ≤ 8 bloques (héroe, período+mes, visual, lectura, apoyo como **un** bloque
plegado).

---

## Pantalla `movimientos` — Movimientos de cartera · materia `finanzas`

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `nrr` | `nrr`, `mrr_inicial`, `expansion`, `contraccion`, `baja`, `moneda` | la cohorte es de **existentes**; los nuevos no inflan; componentes visibles |
| Período | — | `desde`, `hasta` | — |
| Mes | — | `meta.mes`, `meta.nota_periodo` | siempre visible en esta pantalla |
| Visual | `movimientos-plan` | `tipo_movimiento`, `solicitudes`, `delta_ingreso_total` | el tipo sale del **delta de precio**, no del nivel; no retitular «upgrade» por el nombre del plan |
| Lectura | `tiempo-resolucion-solicitudes` | `resueltas`, `pendientes`, `segundos_mediana` | pendiente **aparte**; mediana nula → **sin dato**, no 0 s; sin desglose por persona |
| Apoyo plegado | `suspension-reactivacion` | `suspendidas`, `reactivadas`, `pct_suspension`, `pct_reactivacion` | nulo → sin dato |

---

## Pantalla `catalogo` — Catálogo y uso · materia `catalogo`

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `distribucion-cartera` | `plan`, `nivel`, `clientes`, `pct_clientes`, `mrr_aportado`, `pct_ingreso` | plan de precio cero **cuenta** en clientes y aporta **cero** ingreso; ambas cifras se ven |
| Período | — | `desde`, `hasta` | — |
| Visual | `utilizacion-limites` | `plan`, `unidades_usadas`, `unidades_limite`, `usuarios_usados`, `usuarios_limite`, `nota_dimension_pendiente` | usado **y** contratado, no solo %; la nota de dimensión pendiente visible; **sin** columna de llamadas |
| Lectura | `severidades-habilitadas-vs-usadas` | `plan`, `severidad`, `habilitada`, `casos_atendidos` | habilitada y no usada **aparece** |

Sin zona de apoyo. `idcliente` de utilización, si llega, es clave: no se resuelve a fiscal ni a
persona. Sin `zona-mes` (estos informes no se resuelven a mes natural).

---

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | `data` con filas y métrica no nula | cifra / barras |
| sin_dato | métrica `null` con período que sí tiene contexto | «sin dato», nunca 0 |
| vacio | `data: []` | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue. Un 403 en materia ajena no se «recupera» pintando ceros |

## Navegación

Tres entradas de sidebar, grupo Suscripciones, **roles del guard de esa pantalla**. No modificar
«Informes de suscripciones», catálogo de planes, métodos de pago ni facturas del cliente. No añadir
un índice que liste las tres a quien solo gobierna una.
