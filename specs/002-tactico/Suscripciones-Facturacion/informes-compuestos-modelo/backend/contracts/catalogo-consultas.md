# Contrato — Catálogo de consultas de Suscripciones y Facturación

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/suscripciones/`. Rigen las
convenciones del
[catálogo de Emergencias](../../../Emergencias/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md) §1.

---

## 1. La regla de la versión final, por tabla ⚠️

| Tabla | ¿`FINAL`? |
|---|---|
| `dim_plan`, `dim_cliente` | **Obligatorio** |
| **`hecho_suscripcion`** | **Obligatorio** — es instantánea acumulada |
| `hecho_factura`, `hecho_solicitud_cambio_plan` | **Prohibido** — transacción |

⚠️ **`hecho_suscripcion` es la trampa de este departamento.** Los otros dos hechos son de
transacción, así que la costumbre lleva a no forzar versión final — y en el de suscripción eso
**cuenta dos veces una suscripción actualizada e infla el MRR de forma intermitente**.

---

## 2. Cuatro reglas propias del departamento ⚠️

1. **Ninguna consulta lee `activo`** para saber si una suscripción está vigente. Se lee
   `estado_derivado`.
2. **Los ingresos se suman con `monto_con_signo`**, nunca con `monto_total`: las notas de crédito
   deben restar solas.
3. **`En disputa` no entra en ningún cálculo de impago ni de mora.**
4. **Ninguna consulta devuelve medio de cobro, identificador fiscal ni desglose por persona.**

Las cuatro se verifican con pruebas sobre el **texto** de las consultas.

---

## 3. Parámetros propios

| Parámetro | Informe | Por defecto |
|---|---|---|
| `mes` | #1 MRR, #8 NRR | mes natural en curso |
| `escalones_dunning` | #5 efectividad del dunning | `3,5` (días) |
| `dias_aviso_caducidad` | #6 clientes sin método | `30` |

⚠️ **MRR y NRR usan mes natural** (research D8). Un rango arbitrario se resuelve al mes que lo
contiene, y la respuesta lo declara: comparar dos ventanas móviles solapadas no es comparar.

---

## 4. Los 13 ficheros

### OT06 — Ciclo de cobro

| Fichero | Devuelve |
|---|---|
| `ot06_mrr.sql` | `mes, mrr, nuevo, expansion, contraccion, baja, variacion_neta, sin_periodicidad` |
| `ot06_ingresos.sql` | `mes, plan, tipo_cliente, facturado, notas_credito, ingreso_neto` |
| `ot06_tasa_renovacion.sql` | `mes, vencidas, renovadas, pct_renovacion` |
| `ot06_cobro_primer_intento.sql` | `mes, pagadas, primer_intento, tras_reintentos, pct_primer_intento` |
| `ot06_efectividad_dunning.sql` | `mes, escalon, facturas_en_escalon, recuperadas, pct_recuperacion` |
| `ot06_clientes_sin_metodo_pago.sql` | `idcliente, nombre_comercial, tipo, estado_comercial, caduca_en_dias` |

⚠️ **`ot06_mrr.sql`**: cuatro exigencias verificables — normaliza a mensual, usa el precio de la
suscripción, **excluye las de periodicidad ausente** contándolas en `sin_periodicidad`, y descompone
la variación en cuatro componentes que **suman el neto**.

⚠️ **`ot06_ingresos.sql`** suma `monto_con_signo`. `notas_credito` se devuelve aparte para que se vea
cuánto se restó.

⚠️ **`ot06_clientes_sin_metodo_pago.sql`** es una **diferencia de conjuntos**: el cliente sin ninguna
fila de método es el que interesa. Una unión interna lo perdería — exactamente al revés del propósito.

### OT07 — Movimientos

| Fichero | Devuelve |
|---|---|
| `ot07_movimientos_plan.sql` | `mes, tipo_movimiento, solicitudes, delta_ingreso_total` |
| `ot07_nrr.sql` | `mes, mrr_inicial, expansion, contraccion, baja, nrr` |
| `ot07_suspension_reactivacion.sql` | `mes, suspendidas, reactivadas, pct_suspension, pct_reactivacion` |
| `ot07_tiempo_resolucion.sql` | `mes, resueltas, pendientes, segundos_mediana` |

⚠️ **`ot07_nrr.sql`** se calcula sobre la **cohorte de clientes existentes al inicio del mes**, y
**excluye a los nuevos**: incluirlos convertiría el NRR en crecimiento bruto, que es otro indicador.

⚠️ **`ot07_tiempo_resolucion.sql`** cuenta **resueltas**, sea cual sea el sentido —una rechazada se
resolvió—, y las **pendientes van aparte**, nunca como cero. **Sin desglose por administrador.**

⚠️ **`ot07_movimientos_plan.sql`** clasifica por **delta de precio**, no por nivel: el catálogo tiene
un Empresarial más barato que un Profesional.

### OT05 — Catálogo

| Fichero | Devuelve |
|---|---|
| `ot05_distribucion_cartera.sql` | `plan, nivel, clientes, pct_clientes, mrr_aportado, pct_ingreso` |
| `ot05_utilizacion_limites.sql` | `idcliente, plan, unidades_usadas, unidades_limite, usuarios_usados, usuarios_limite, nota_dimension_pendiente` |
| `ot05_severidades_habilitadas_vs_usadas.sql` | `plan, severidad, habilitada, casos_atendidos` |

⚠️ **`ot05_utilizacion_limites.sql` NO devuelve ninguna columna de llamadas API**, ni vacía
(FR-030). `nota_dimension_pendiente` declara que esa dimensión llegará con Partners. Un
`llamadas: null` diría «este cliente no consume la API», que es otra afirmación.

⚠️ **`ot05_distribucion_cartera.sql`**: un plan de precio cero cuenta en `clientes` y aporta **cero**
en `mrr_aportado`. Ambas cifras van por separado para que un plan demo no parezca ni un éxito ni una
ausencia.

---

## 5. Reglas de resultado

Las comunes, más dos propias:

| Regla | Detalle |
|---|---|
| **Importes con moneda y periodicidad** | Todo importe declara ambas; el sistema no registra moneda, así que se asume una y se dice |
| **Declarar el período real usado** | MRR y NRR devuelven el mes natural aplicado, aunque se pidieran fechas arbitrarias |

---

## 6. Lo que ninguna consulta puede devolver

| Excluido | Aunque |
|---|---|
| Token de pasarela, últimos dígitos, tipo de tarjeta | El informe de métodos de pago los tiene al lado |
| Identificador fiscal del cliente | `Dim_Cliente` lo guarda |
| Identidad del administrador que resolvió | El catálogo pide «por administrador» |
| Motivo de anulación y de rechazo | Son texto libre |
| Cualquier columna de llamadas API | Pertenece a Partners |
