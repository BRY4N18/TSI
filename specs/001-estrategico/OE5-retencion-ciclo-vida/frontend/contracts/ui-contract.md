# Contrato UI — cuatro pantallas Z de OE5

**No redefine** el OpenAPI. Mapea **zona → informe publicado → campos visibles**.

Prefijo: `GET /api/v1/informes-estrategicos/oe5/{informe}?desde=&hasta=&granularidad=&comparacion=`

| Id publicado | Pantalla |
|---|---|
| `cumplimiento-sla` | servicio |
| `evolucion-incumplimiento` | servicio (visual) |
| `rendimiento-por-agente` | servicio (apoyo) |
| `reincidencia-soporte` | servicio (apoyo) |
| `retencion-neta-ingresos` | ingresos |
| `sla-por-plan` | planes |
| `movimientos-de-plan` | planes (visual) |
| `antiguedad-de-cuenta` | planes (lectura) |
| `cuentas-en-riesgo` | riesgo |

**No publicado:** `nps-satisfaccion`, `reportes-sin-correccion`.

**No se llama aquí (viven en OE1):** `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding`.

Roles: servicio = `GerenteExitoCliente` · `Gerente`. Ingresos = `DirectorFinanciero` · `Gerente`.
Planes = `DirectorEstrategia` · `Gerente`. Riesgo = `Gerente`. Partner = ninguno.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`,
`zona-apoyo`, `zona-parcial`, `zona-comparacion`.

Envelope: `data` (array) + `meta`.

## Prohibido en las cuatro

Texto de ticket; notas internas; nombre de agente; medio de cobro; id de pago; coordenadas;
NPS; reportes sin corrección; recuadros de ciclo OE1; botón de reabrir / cambiar plan /
contactar; exportar; `acotado_a`; ítem de menú gris para quien no entra.

---

## Pantalla `servicio`

Guard: `oe5ServicioGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `cumplimiento-sla` | %, recuento con compromiso, cobertura | recuento **junto** al % |
| Período | — | `desde`, `hasta`, `granularidad`, `comparacion` | comparación ausente con motivo |
| Visual | `evolucion-incumplimiento` | serie de incumplimiento | no es el compuesto táctico |
| Lectura | `meta.alcance` | sin compromiso aparte | vacío ≠ 0 % |
| Apoyo plegado | `rendimiento-por-agente`, `reincidencia-soporte` | idagente + cola; cliente×servicio | carga, no desempeño |

---

## Pantalla `ingresos`

Guard: `oe5IngresosGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `retencion-neta-ingresos` | NRR neto | — |
| Período | — | igual que servicio | — |
| Visual | mismo GET | expansión, contracción, churn | los tres, no solo el neto |
| Lectura | `meta.alcance` | precio congelado | MUST NOT «expansión = 0» de OT07 |

Un GET de NRR alimenta héroe y visual.

---

## Pantalla `planes`

Guard: `oe5PlanesGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `sla-por-plan` | plan, cumplimiento | — |
| Período | — | igual | — |
| Visual | `movimientos-de-plan` | plan origen/destino, delta | solo **aprobados** |
| Lectura | `antiguedad-de-cuenta` | mediana, activas | cerradas aparte |

---

## Pantalla `riesgo`

Guard: `oe5RiesgoGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `cuentas-en-riesgo` | recuento de cuentas ≥2 señales | una señal **no** marca |
| Período | — | igual | — |
| Visual | mismo GET | señales presentes | sin identidad |
| Lectura | `meta.falta` / alcance | fuentes faltantes | nombradas, no semáforo cerrado |

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | filas | cifra / barras |
| sin_dato | métrica `null` | «sin dato», nunca 0 % fingido |
| vacio | `data: []` de compromiso | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |
| parcial | `meta.cobertura = parcial` | banner `zona-parcial` |

## Navegación

Cuatro entradas en el grupo **Estratégico**. No modificar compuestos tácticos de Soporte,
Suscripciones o Cuentas ni las cuatro de OE1.
