# Data Model — Informes Tácticos Simples de Suscripciones y Facturación (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema.**

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Fact_Suscripcion` | Entidad principal | L1 |
| `Fact_Factura` | Entidad principal | L2 |
| `Fact_Solicitud_Cambio_Plan` | Entidad principal | L3 |
| `Dim_MetodoPago` | Entidad principal | L4 |
| `Dim_Plan` | Catálogo | L1, L3 |
| `Dim_Cliente` | Catálogo | L1–L4 |
| `Dim_Usuarios` | Catálogo | L3 (quién resolvió) |

Todas de solo lectura.

---

## 2. El eje de acotamiento: la organización

A diferencia de Ventas y CRM, donde el titular era el propio solicitante, aquí hay un salto:
**el usuario pregunta y el resultado se acota a la cuenta cliente a la que pertenece.**

| Listado | Columna de titularidad |
|---|---|
| L1 Suscripciones | `Fact_Suscripcion.idcliente` |
| L2 Facturas | `Fact_Factura.id_cliente` |
| L3 Solicitudes de cambio | `Fact_Solicitud_Cambio_Plan.idcliente` |
| L4 Métodos de pago | `Dim_MetodoPago.idcliente` |

El resolutor devuelve **qué cuenta**; cada repositorio decide **por qué columna** — nótese que
Facturas usa `id_cliente` con guion bajo y las demás `idcliente`, una inconsistencia del esquema que
el repositorio absorbe.

---

## 3. Los cuatro listados

### L1 — Suscripciones · `FR-001`, `FR-002` · OT05/OT07

- **Tabla:** `Fact_Suscripcion`
- **Campos:** `id_suscripcion`*, `cuenta`, `plan`, `nivel`, `estado`, `precio`, `periodicidad`,
  `renovacion_automatica`, `fecha_inicio`, `fecha_fin`, `motivo_cancelacion`, `fecha_cancelacion`,
  `cambio_programado`
- **Orden:** `id_suscripcion DESC` · **Cursor:** escalar
- **Tipo:** estado actual → rechaza el período genérico
- **Acotado por:** `idcliente`
- **Catálogo:** `idplan` → `Dim_Plan.nombre`; `idcliente` → `Dim_Cliente.razon_social`

**Filtros:** `estado`, `plan`, `vence_en_dias`, `con_cambio_programado`, `cancelada_desde`,
`cancelada_hasta`.

**⚠️ `con_cambio_programado` compara contra un centinela, no contra nulidad** (research D2):

| Condición | Significa |
|---|---|
| `idplan_programado > 0` | Hay una reducción aprobada pendiente de aplicarse al cierre del ciclo |
| `idplan_programado = 0` | **No hay ningún cambio** — es el valor que el código escribe por defecto |

**Prohibido usar una comprobación de nulidad**: devolvería *todas* las suscripciones como si todas
tuvieran un cambio pendiente. `cambio_programado` se presenta como **ausencia**, nunca como un plan
con identificador cero.

**Nota sobre las cancelaciones.** `cancelada_desde` / `cancelada_hasta` filtran la **columna** de
fecha de cancelación. No son el período genérico del contrato: esta tabla guarda el estado actual de
cada suscripción, no un histórico de sucesos.

---

### L2 — Facturas · `FR-003` · OT06 / OP16, CU-O38

- **Tabla:** `Fact_Factura`
- **Campos:** `id_factura`*, `cuenta`, `numero_factura`, `periodo`, `tipo_documento`, `monto_base`,
  `impuestos`, `monto_total`, `estado_pago`, `reintentos`, `fecha_emision`, `fecha_vencimiento`,
  `dias_mora`
- **Orden:** `fecha_emision DESC` · **Cursor:** compuesto `fecha_emision|id_factura`
- **Tipo:** **hechos del período** — `desde`/`hasta` opcionales
- **Acotado por:** `id_cliente`

**⚠️ `estado_pago` toma cuatro valores** (research D3):

| Valor | Significa | ¿Cuenta como mora? |
|---|---|---|
| `Pendiente` | Esperando cobro | No |
| `Pagada` | Liquidada | No |
| `Fallida` | Reintentos agotados | **Sí** |
| `En disputa` | **Excluida del cobro automático** mientras se resuelve | **No** |

**El filtro `vencidas` excluye las facturas en disputa.** Presentarlas como mora induciría a
perseguir un cobro que el sistema detuvo a propósito — el defecto que corrigió B41.

`dias_mora` se calcula en el servicio con **reloj inyectable**, y solo se devuelve cuando la factura
está vencida e impaga.

**`tipo_documento`** se expone para distinguir un cargo de una nota de crédito. Hoy la operación
**no emite notas de crédito ni anula facturas** —las columnas se escriben siempre con el mismo
valor—, pero exponerlo evita que, cuando se emitan, un listado de facturación las sume como cargos
(research D6). **No se ofrece filtro** por algo que hoy tiene un solo valor.

---

### L3 — Solicitudes de cambio de plan · `FR-004` · OT07 / CU-O34

- **Tabla:** `Fact_Solicitud_Cambio_Plan`
- **Campos:** `idsolicitud`*, `cuenta`, `plan_actual`, `plan_solicitado`, `estado`, `motivo`,
  `dias_espera`, `resuelta_por`, `motivo_rechazo`, `fecha_solicitud`, `fecha_resolucion`
- **Orden:** `fecha_solicitud ASC` — es una bandeja de trabajo, lo más antiguo primero ·
  **Cursor:** compuesto `fecha_solicitud|idsolicitud`
- **Filtros:** `estado`
- **Tipo:** estado actual
- **Acotado por:** `idcliente`
- **Catálogo:** `idplanactual` / `idplansolicitado` → `Dim_Plan.nombre`; `idadminaprobador` →
  `Dim_Usuarios`

`dias_espera` se calcula en el servicio con reloj inyectable. `resuelta_por` y `motivo_rechazo` se
presentan como ausentes mientras la solicitud siga pendiente.

---

### L4 — Métodos de pago vigentes · `FR-005`, `FR-006`, `FR-007` · OT06 (criterio propio)

- **Tabla:** `Dim_MetodoPago` · filtro `activo = true`
- **Campos:** `idmetodopago`*, `cuenta`, `tipo`, `ultimos_digitos`, `fecha_expiracion`,
  `dias_para_caducar`
- **Orden:** `fechaexpiracion ASC` — lo que antes caduca, primero · **Cursor:** compuesto
- **Filtros:** `caduca_en_dias`
- **Tipo:** estado actual
- **Acotado por:** `idcliente`

**⛔ `tokenpasarela` NO SALE NUNCA.** No es un hash: el servicio de cobro lo pasa a la pasarela para
ejecutar el cargo. Quien lo tenga, puede cobrar. **Columnas enumeradas, prohibido `SELECT *`**, y
prueba que inspecciona la **respuesta serializada completa** (research D4).

**Solo vigentes** (FR-007): reemplazar un método desactiva el anterior sin borrarlo, así que el
filtro `activo = true` es lo que distingue el medio de cobro real de su historial.

`dias_para_caducar` se calcula en el servicio; el filtro `caduca_en_dias` se traduce a una fecha de
corte que **sí viaja a la base**, porque la columna es numérica (research D5) — a diferencia del
listado de demos de Ventas y CRM, que necesitó dos pasos.

\* Identificadores de uso interno. **No se muestran** (`design-system.md` §8).

---

## 4. Reglas transversales

**Acotamiento por organización.** Administrador ve todas las cuentas; un usuario de cuenta queda
forzado a la suya, resuelta por pertenencia; pedir otra es **negativa explícita**. Una cuenta con la
suscripción **suspendida conserva** el acceso a lo suyo (FR-011): es donde ve lo que debe
regularizar.

**Resolución de catálogo.** Dos consultas y unión en memoria — sin JOIN.

**Centinelas.** El cliente de la base ya devuelve ausencia para los centinelas de texto y entero.
**El `0` del plan programado no es uno de ellos**: es un valor escrito a propósito por el código, y
hay que compararlo explícitamente (research D2).

**Paginación.** Keyset, `limit + 1`. El cursor de facturas desempata por texto, que es determinista
aunque no ordene numéricamente — suficiente para no repetir ni saltar filas.

**Retraso de ingesta.** 5–15 s. Una factura recién cobrada puede seguir apareciendo como pendiente.
No se compensa.

---

## 5. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "1786569480560|FAC-202608-00000001", "limit": 50, "has_next": true },
    "filtros": { "estado_pago": "Fallida" },
    "acotado_a": "propios"
  }
}
```

`acotado_a` declara si el resultado está limitado a la cuenta del solicitante. Sin él, un cliente no
puede distinguir «no hay facturas vencidas» de «no hay facturas vencidas **mías**».

---

## 6. Resumen

| # | Listado | Tabla | Tipo | Cuidado |
|---|---|---|---|---|
| L1 | Suscripciones | `Fact_Suscripcion` | Estado actual | ⚠️ el cambio programado es un centinela `0`, no una ausencia |
| L2 | Facturas | `Fact_Factura` | Período opcional | ⚠️ en disputa ≠ impaga · notas de crédito inertes hoy |
| L3 | Solicitudes de cambio | `Fact_Solicitud_Cambio_Plan` | Estado actual | Orden ascendente: es bandeja de trabajo |
| L4 | Métodos de pago | `Dim_MetodoPago` | Estado actual | ⛔ el identificador de cobro no sale jamás |
