# Contrato UI — cuatro pantallas Z de OE6

**No redefine** el OpenAPI. Mapea **zona → informe publicado → campos visibles**.

Prefijo: `GET /api/v1/informes-estrategicos/oe6/{informe}?desde=&hasta=&granularidad=&comparacion=`

| Id publicado | Pantalla |
|---|---|
| `tiempo-respuesta-global` | llegada |
| `tiempo-respuesta-por-severidad` | llegada (visual) |
| `tramos-del-ciclo` | diagnostico |
| `origen-de-asignacion` | diagnostico (visual) |
| `desviacion-de-llegada` | diagnostico (lectura) |
| `envejecimiento-de-casos-abiertos` | ejecucion |
| `rechazo-y-timeout-por-unidad` | ejecucion (visual) |
| `abortos-y-misiones-fallidas` | ejecucion (visual/apoyo) |
| `cierres-forzados` | ejecucion (lectura) |
| `impacto-humano` | personas |
| `escaladas-de-severidad` | personas (visual) |
| `cobertura-de-evidencia` | personas (lectura) |

**No se llama:** informes de OE3; ningún slug de mapa.

Roles: las cuatro = `DirectorOperaciones` · `Gerente`. Partner = ninguno.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`,
`zona-apoyo`, `zona-parcial`, `zona-comparacion`.

Envelope: `data` (array) + `meta`.

## Prohibido en las cuatro

Mapa; lat/lon; nombre de implicado; placa; ETA como título; recuadros OE3; botón de despacho /
reasignar / cerrar; exportar; `acotado_a`; ítem de menú gris para quien no entra; promedio como
héroe de tiempo.

---

## Pantalla `llegada`

Guard: `oe6Guard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `tiempo-respuesta-global` | mediana, p95, recuento, cobertura | p95 nulo → sin dato |
| Período | — | `desde`, `hasta`, `granularidad`, `comparacion` | comparación ausente con motivo |
| Visual | `tiempo-respuesta-por-severidad` | severidad (incl. desconocido), tiempos | — |
| Lectura | alcance | casos **sin llegada** aparte | vacío ≠ 0 min |

---

## Pantalla `diagnostico`

Guard: `oe6Guard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `tramos-del-ciclo` | tramos | suman el total de hitos completados |
| Período | — | igual | — |
| Visual | `origen-de-asignacion` | automático / manual / escalado | % suman 100 % |
| Lectura | `desviacion-de-llegada` | desvío + alcance | MUST NOT «ETA» |

---

## Pantalla `ejecucion`

Guard: `oe6Guard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `envejecimiento-de-casos-abiertos` | tramos de edad | abiertos ≠ cerrados |
| Período | — | igual | — |
| Visual | rechazo + abortos | tasa **y** denominador | vacío de abortos ≠ 0 % |
| Lectura | `cierres-forzados` | cifra + `meta.alcance` | qué definición se mide |
| Apoyo | si no caben tasas | denominadores | — |

---

## Pantalla `personas`

Guard: `oe6Guard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `impacto-humano` | víctimas / heridos / fallecidos | no-dato ≠ cero |
| Período | — | igual | — |
| Visual | `escaladas-de-severidad` | recuento | dato escaso declarado |
| Lectura | `cobertura-de-evidencia` | % en **cerrados** | sin identidad |

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | filas | cifra / barras |
| sin_dato | p95 `null` | «sin dato» en esa cifra |
| vacio | `data: []` | vacío explícito (no 0 min) |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |
| parcial | `meta.cobertura = parcial` | banner `zona-parcial` |

## Navegación

Cuatro entradas en el grupo **Estratégico**, mismos roles. No modificar compuestos tácticos de
Emergencias ni OE3.
