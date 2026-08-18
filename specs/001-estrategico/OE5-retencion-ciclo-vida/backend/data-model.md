# Data Model — OE5, Retención y Ciclo de Vida

**Fecha:** 2026-08-18 · **Research:** [`research.md`](research.md)

Este módulo **no crea tablas**. Consume el modelo de Soporte, Suscripciones, Cuentas y Partners.

---

## 1. Tablas leídas

| Tabla | Tipo | `FINAL` | Aporta |
|---|---|:--:|---|
| `hecho_ticket` | Acumulado | **Sí** | SLA, agente, reincidencia (`tiene_compromiso`, `desenlace_sla`) |
| `hecho_accion_ticket` | Transacción | **No** | Historial sin texto |
| `dim_sla_config` | Dimensión | **Sí** | No se une al vigente para reescribir el pasado |
| `dim_servicio` | Dimensión | **Sí** | Servicio de reincidencia |
| `hecho_suscripcion` | Acumulado | **Sí** | NRR, antigüedad (`precio_mensualizado`, `estado_derivado`) |
| `hecho_factura` | Transacción | **No** | Señal de cobro de E5-12 (`estado_pago`, `pagada_primer_intento`) |
| `hecho_solicitud_cambio_plan` | Transacción | **No** | E5-02/03 (`delta_precio`, `estado`) |
| `dim_plan` | Dimensión | **Sí** | Nombre de plan (E5-07); **no** el precio vigente |
| `dim_cliente` | Dimensión conformada | **Sí** | Antigüedad, riesgo — **sin país, sin cobro** |
| `hecho_sesion` | Transacción | **No** | Señal de inactividad |
| `hecho_llamada_api` | Transacción | **No** | Señal de consumo API |

**No se lee** texto de ticket, `idmetodopago`, `calificacion` de cierre de accidente.

**No se recrea** `dim_cliente`. **No se copian** las SQL de OE1.

---

## 2. Lista blanca (columnas)

### `hecho_ticket`

`fecha`, `id_reclamo`, `idcliente`, `idplan`, `plan`, `idagente`, `tiene_agente`, `tipo`,
`servicio`, `estado`, `tiene_compromiso`, `motivo_sin_compromiso`, `segundos_respuesta_max`,
`segundos_resolucion_max`, `hora_resolucion`, `hora_cierre`, `segundos_resolucion`,
`desenlace_sla`, `fue_reabierto`, `reaperturas`

Prohibido: asunto, descripción.

### `hecho_suscripcion`

`fecha`, `id_suscripcion`, `idcliente`, `idplan`, `plan`, `fecha_alta`, `fecha_fin_prevista`,
`fecha_cancelacion`, `estado_derivado`, `precio_mensualizado`

### `hecho_solicitud_cambio_plan`

`fecha`, `idcliente`, `plan_actual`, `plan_solicitado`, `tipo_movimiento`, `delta_precio`,
`estado`, `esta_resuelta`

### `hecho_factura` (solo E5-12)

`fecha`, `idcliente`, `estado_pago`, `pagada_primer_intento`, `reintentos`, `dias_mora`

Prohibido: método de pago.

### `hecho_sesion` / `hecho_llamada_api`

`fecha`, `idusuario`/`idcliente` según DDL · sin token, sin IP, sin secreto.

### `dim_cliente`

`idcliente`, `tipo`, `fecha_alta`, `fecha_baja` — sin `tiene_metodo_pago`.

---

## 3. Los nueve informes construibles

| # | Slug HTTP | Grano | Fuente |
|---|---|---|---|
| E5-04 | `cumplimiento-sla` | período | cerrados con compromiso |
| E5-05 | `evolucion-incumplimiento` | período | serie de incumplidos / con compromiso |
| E5-07 | `sla-por-plan` | plan × período | cruce `idplan` copiado en el hecho |
| E5-02 | `retencion-neta-ingresos` | período | cohorte inicial + movimientos + bajas |
| E5-03 | `movimientos-de-plan` | movimiento × período | solicitudes aprobadas/aplicadas |
| E5-06 | `rendimiento-por-agente` | agente | `idagente`; alcance = carga |
| E5-08 | `reincidencia-soporte` | cliente × servicio | no tres servicios distintos |
| E5-12 | `cuentas-en-riesgo` | cuenta | ≥2 de 4 señales |
| E5-15 | `antiguedad-de-cuenta` | período | solo `fecha_baja IS NULL` |

**E5-01, E5-11** no son filas de este modelo. **E5-09/10/13/14** viven en OE1.

---

## 4. Validaciones

- Período sin cerrados-con-compromiso → `data: []`, no 0 % de SLA.
- Ticket sin compromiso fuera del denominador y declarado.
- NRR: expansión + contracción + churn visibles; no un solo neto.
- Pendiente de cambio de plan no mueve ingreso.
- Una sola señal de E5-12 → no marcado.
- Fuente ausente en E5-12 → `parcial` + `falta` nombra la señal.
- `cobertura: parcial` bajo umbral 20.
- `cumple` de objetivo siempre `null`.

---

## 5. Relación con el táctico y con OE1

OT19 (SLA), OT20 (incumplimiento, reincidencia, agente), OT07 (NRR stub / movimientos),
OT17 (inactividad) ya calculan el detalle. OE5 **no las parametriza como endpoint**: tiene
ventana comparada, objetivo BSC y permiso partido. El contraste cuadra el **detalle del
período**, no el envelope.

**Excepción:** OT07 deja expansión/contracción en 0. E5-02 las calcula de verdad (D3).

OE1 **posee** E1-06/09/10/11; este módulo referencia.
