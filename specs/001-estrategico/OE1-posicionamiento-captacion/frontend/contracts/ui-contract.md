# Contrato UI — cuatro pantallas Z de OE1

**No redefine** el OpenAPI. Mapea **zona → informe publicado → campos visibles**.

Prefijo: `GET /api/v1/informes-estrategicos/oe1/{informe}?desde=&hasta=&granularidad=&comparacion=`

| Id publicado | Pantalla |
|---|---|
| `mrr-mensual` | ingreso |
| `arr-proyeccion` | ingreso (lectura) |
| `tasa-renovacion` | ingreso (apoyo) |
| `cartera-por-plan` | cartera |
| `mrr-por-segmento` | cartera (lectura) |
| `embudo-conversion` | captacion |
| `velocidad-ciclo-venta` | captacion (apoyo) |
| `churn-por-cohorte` | ciclo |
| `abandono-onboarding` | ciclo (visual) |
| `tiempo-onboarding` | ciclo (lectura) |

**No publicado:** `cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado`.

Roles: ingreso = `DirectorFinanciero` · `Gerente`. Cartera = `DirectorEstrategia` · `Gerente`.
Captación = `DirectorMarketing` · `Gerente`. Ciclo = `Gerente`. Partner = ninguno.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`,
`zona-apoyo`, `zona-parcial`, `zona-comparacion`.

Envelope: `data` (array) + `meta`.

## Prohibido en las cuatro

Medio de cobro; id de pago; ficha de prospecto; país; mapa; CAC; mercados; botón de cambiar
plan / cobrar / dar de baja; exportar; `acotado_a`; ítem de menú gris para quien no entra.

---

## Pantalla `ingreso`

Guard: `oe1IngresoGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `mrr-mensual` | importe, recuento, cobertura | recuento **junto** al importe |
| Período | — | `desde`, `hasta`, `granularidad`, `comparacion` | comparación ausente con motivo |
| Visual | mismo GET / comparación | variación | no es el compuesto táctico |
| Lectura | `arr-proyeccion` | ARR + `meta.alcance` | extrapolación visible |
| Apoyo plegado | `tasa-renovacion` | tasa, vencidas, renovadas | denominador = vencidas |

---

## Pantalla `cartera`

Guard: `oe1CarteraGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `cartera-por-plan` | plan, recuento / mix | — |
| Período | — | igual que ingreso | — |
| Visual | mismo GET | evolución de mezcla | no solo foto |
| Lectura | `mrr-por-segmento` | `tipo`, mrr, recuento | tipo ≠ país; desconocidos visibles |

---

## Pantalla `captacion`

Guard: `oe1CaptacionGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `embudo-conversion` | tasa / volumen de paso | — |
| Período | — | igual | — |
| Visual | mismo GET | etapa, transiciones | ceros visibles |
| Lectura | `meta.alcance` | cruce Ventas–Cuentas si viene | — |
| Apoyo plegado | `velocidad-ciclo-venta` | etapa, tiempo, ejecutivo | sin ficha de prospecto |

---

## Pantalla `ciclo`

Guard: `oe1CicloGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `churn-por-cohorte` | `n`, `pct_churn` nullable | sin % cerrado si n bajo |
| Período | — | igual | — |
| Visual | `abandono-onboarding` | etapa de catálogo, completados | ceros del catálogo |
| Lectura | `tiempo-onboarding` | mediana, `completados`, `en_proceso` | en proceso ≠ 0 días |

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | filas | cifra / barras |
| sin_dato | % o mediana `null` | «sin dato», nunca 0 % fingido |
| vacio | `data: []` de flujo | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |
| parcial | `meta.cobertura = parcial` | banner `zona-parcial` |

## Navegación

Cuatro entradas en el grupo **Estratégico**. No modificar compuestos tácticos de Suscripciones,
Ventas o Cuentas ni las tres de OE2.
