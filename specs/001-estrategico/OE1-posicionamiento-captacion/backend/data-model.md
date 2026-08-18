# Data Model — OE1, Posicionamiento y Captación

**Fecha:** 2026-08-18 · **Research:** [`research.md`](research.md)

Este módulo **no crea tablas**. Consume el modelo de Suscripciones, Ventas y Cuentas.

---

## 1. Tablas leídas

| Tabla | Tipo | `FINAL` | Aporta |
|---|---|:--:|---|
| `hecho_suscripcion` | Acumulado | **Sí** | MRR, ARR, cartera, renovación (`precio_mensualizado`, `periodicidad`, `estado_derivado`) |
| `hecho_factura` | Transacción | **No** | No es fuente de MRR; no se usa para CAC |
| `dim_plan` | Dimensión | **Sí** | Nombre de plan (E1-12) |
| `dim_cliente` | Dimensión conformada | **Sí** | `tipo`, `cohorte_alta`, `fecha_baja` — **sin país** |
| `hecho_transicion_embudo` | Transacción | **No** | Embudo y velocidad |
| `hecho_asignacion_prospecto` | Transacción | **No** | Ejecutivo vigente (E1-13) |
| `dim_prospecto` | Dimensión | **Sí** | Canal, desenlace — **sin ficha personal** |
| `hecho_onboarding` | Transacción | **No** | Etapas **completadas** |
| `dim_etapa_onboarding` | Dimensión | **Sí** | Catálogo explícito (ceros) |

**No se lee** `tiene_metodo_pago`, `metodo_pago_caduca`, identidad de persona, `idpais`.

**No se recrea** `dim_cliente`.

---

## 2. Lista blanca (columnas)

### `hecho_suscripcion`

`fecha`, `id_suscripcion`, `idcliente`, `tipo_cliente`, `idplan`, `plan`, `fecha_alta`,
`fecha_fin_prevista`, `fecha_cancelacion`, `estado_derivado`, `precio_mensualizado`,
`periodicidad`

### `dim_cliente`

`idcliente`, `tipo`, `estado_comercial`, `fecha_alta`, `cohorte_alta`, `fecha_baja`,
`motivo_baja`, `onboarding_completo`

Prohibido: `tiene_metodo_pago`, `metodo_pago_caduca`, `nombre_comercial` en respuestas de
churn (el segmento usa `tipo`).

### `hecho_transicion_embudo`

`fecha`, `fechahora`, `idprospecto`, `canal`, `etapa_anterior`, `etapa_nueva`, `es_avance`,
`es_terminal`, `segundos_en_etapa_anterior`

### `hecho_onboarding` + `dim_etapa_onboarding`

`idcliente`, `etapa`, `orden_etapa`, `dias_desde_alta` · catálogo `idetapa`, `etapa`, `orden`,
`es_obligatoria`

---

## 3. Los diez informes construibles

| # | Slug HTTP | Grano | Fuente |
|---|---|---|---|
| E1-01 | `mrr-mensual` | período | `precio_mensualizado` vigente al cierre |
| E1-02 | `arr-proyeccion` | período | MRR × 12; escenarios etiquetados |
| E1-03 | `mrr-por-segmento` | tipo × período | `dim_cliente.tipo` |
| E1-12 | `cartera-por-plan` | plan × período | mezcla y evolución |
| E1-04 | `embudo-conversion` | etapa | transiciones; ceros del catálogo |
| E1-13 | `velocidad-ciclo-venta` | etapa / ejecutivo | segundos; sin ficha de prospecto |
| E1-06 | `tasa-renovacion` | período | denominador = vencidas |
| E1-09 | `tiempo-onboarding` | período | días; en proceso aparte |
| E1-10 | `abandono-onboarding` | etapa de catálogo | ausencia, no solo completadas |
| E1-11 | `churn-por-cohorte` | `cohorte_alta` | n bajo umbral → sin % |

**E1-05, E1-07, E1-08** no son filas de este modelo.

---

## 4. Validaciones

- `data: []` en un mes sin movimiento de **flujo** no implica MRR = 0 (el stock puede seguir).
  El MRR vacío solo si no hay vigentes.
- Periodicidad anual **no** se vuelve a dividir.
- Embudo: volumen no creciente; etapa en cero visible.
- Onboarding: JOIN al catálogo; 100 % sin catálogo está prohibido.
- `cobertura: parcial` + `falta` nombra el tamaño de muestra.
- `cumple` de objetivo siempre `null` (`[CALIBRAR]`).

---

## 5. Relación con el táctico y con OE5

Las SQL tácticas `ot06_mrr`, `ot02_embudo_conversion`, `ot17_churn_por_cohorte` ya calculan el
detalle. OE1 **no las parametriza**: tiene ventana comparada, `objetivo` BSC y permiso de
Gerente. El contraste de implementación cuadra el **detalle del período**, no el envelope.

OE5 **referencia** E1-06/09/10/11; no reimplementa.
