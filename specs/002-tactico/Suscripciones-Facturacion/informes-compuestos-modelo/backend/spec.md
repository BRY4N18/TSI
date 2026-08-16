# Feature Specification: Informes Compuestos de Suscripciones y Facturación sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos compuestos de Suscripciones y Facturación — los informes agregados de OT05 a OT07, resueltos con consultas sobre el modelo analítico"

---

## Contexto

Cuarto departamento sobre el modelo analítico. Suscripciones y Facturación responde a **cuánto se
gana y si se cobra**: mantiene el catálogo de planes, sostiene el ciclo de facturación y cobro, y
gestiona los cambios de plan.

**Aquí viven cinco de los indicadores financieros del BSC** —MRR, ingresos, tasa de renovación,
movimientos de plan y NRR— que hoy **no tienen ninguna fuente**. Es el departamento con más
indicadores comprometidos y menos informes construidos.

**Ningún informe compuesto existe.** Solo hay un simple construido: el catálogo de planes.

> ### ⚠️ Cinco hallazgos medidos antes de especificar
>
> **1. Discrepancia del catálogo.** Su tabla resumen atribuye **10 simples y 12 compuestos**;
> contando las filas salen **10 y 13**. Es la **segunda** discrepancia del catálogo, tras la de
> Emergencias. Esta spec va con las filas.
>
> **2. `activo` no refleja el estado, y aquí al revés que en otros departamentos.** Hay una
> suscripción con `estado = 'Cancelada'` y **`activo = true`**. Un informe que use `activo` para
> saber qué está vigente **inflaría el MRR** contando ingresos de una suscripción cancelada.
>
> **3. `motivocancelacion` está poblado en suscripciones activas.** Una suscripción `Activa` lleva
> motivo `'prueba fin de ciclo'`; otras llevan cadena vacía y nulo. **El motivo no implica
> cancelación**, y hay tres formas distintas de decir «sin motivo».
>
> **4. Una suscripción tiene el intervalo de vigencia invertido**: `fecha_fin` **anterior** a
> `fecha_inicio`. Cualquier cálculo de duración o de vigencia produciría un número negativo sin
> avisar.
>
> **5. `idplan_programado = 0` es un centinela**, no un plan. Significa «sin cambio programado», y
> las cuatro suscripciones lo llevan.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Financiero sabe cuánto entra y si se cobra (Priority: P1) 🎯 MVP

Los seis informes de **OT06**: el ingreso recurrente, lo facturado, si se cobra al primer intento, si
el dunning recupera, quién renueva y quién no tiene con qué pagar.

**Why this priority**: contiene **tres indicadores BSC** —MRR, ingresos y tasa de renovación— que hoy
no tienen ninguna fuente. Es el bloque que responde a la pregunta más elemental del departamento, y
ninguno de sus seis informes depende de la aclaración pendiente.

**Independent Test**: pedir el MRR de un mes y comprobar que la suma de las suscripciones vigentes,
normalizadas a mensual, coincide con la cifra devuelta.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 1 | **MRR del período y su variación mes a mes** | OT06 | **BSC** |
| 2 | **Ingresos por período, plan y tipo de cliente** | OT06 | **BSC** |
| 3 | **Tasa de renovación** (renovadas / vencidas del período) | OT06 | **BSC** |
| 4 | Tasa de cobro al primer intento frente a tras reintentos | OT06 | OP16 |
| 5 | **Efectividad del dunning**: recuperación por escalón | OT06 | ± |
| 6 | Clientes sin método de pago activo | OT06 | SRS |

**Acceptance Scenarios**:

1. **Given** una suscripción cancelada que aún tiene `activo = true` en el sistema operativo,
   **When** se pide el MRR, **Then** **no cuenta**. ⚠️ Usar esa columna inflaría el ingreso
   recurrente con una suscripción que ya no existe.
2. **Given** suscripciones con periodicidades distintas, **When** se pide el MRR, **Then** todas se
   normalizan a mensual antes de sumar. Una anual y una mensual del mismo precio no aportan lo mismo.
3. **Given** una suscripción **sin periodicidad registrada**, **When** se pide el MRR, **Then**
   queda **fuera** de la cifra y se cuenta aparte: no se puede normalizar lo que no se sabe cada
   cuánto se cobra.
4. **Given** una factura pagada al primer intento y otra tras tres reintentos, **When** se pide la
   tasa de cobro, **Then** se distinguen. Ambas están pagadas: lo que las separa es el esfuerzo.
5. **Given** una factura **en disputa**, **When** se piden las impagas, **Then** **no cuenta como
   impaga**: disputar no es no pagar, y mezclarlas convierte un problema comercial en uno de mora.
6. **Given** una nota de crédito, **When** se piden los ingresos, **Then** **resta**, no suma.

---

### User Story 2 - El Director Financiero sigue los movimientos de la cartera (Priority: P2)

Los cuatro informes de **OT07**: quién sube de plan y quién baja, cuánto ingreso neto retiene la
cartera existente, y cuántas cuentas se suspenden o reactivan.

**Why this priority**: contiene **dos indicadores BSC más** —movimientos de plan y NRR— y mide la
salud de la cartera **ya conseguida**, que es la pregunta que sigue naturalmente a «cuánto entra».

**Independent Test**: aprobar una subida de plan y comprobar que aparece como upgrade con su delta de
ingreso positivo, y que una bajada aparece con delta negativo.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 7 | **Movimientos de plan**: upgrades frente a downgrades con delta de ingreso | OT07 | **BSC** |
| 8 | **Retención neta de ingresos (NRR)** | OT07 | **BSC** |
| 9 | Tasa de suspensión y de reactivación por período | OT07 | ± |
| 10 | Tiempo medio de resolución de solicitudes de cambio | OT07 | ± |

**Acceptance Scenarios**:

1. **Given** una solicitud de cambio **aprobada pero aún no aplicada**, **When** se piden los
   movimientos de plan, **Then** aparece distinguida de una ya aplicada. ⚠️ El cambio programado se
   marca con un **centinela `0`** en el sistema operativo, que no es un plan.
2. **Given** un cliente que subió de plan y otro que se dio de baja, **When** se pide el NRR,
   **Then** ambos afectan a la cifra en sentidos opuestos, y el informe muestra sus componentes:
   expansión, contracción y baja.
3. **Given** una solicitud rechazada, **When** se pide el tiempo de resolución, **Then** cuenta: se
   resolvió, aunque fuera en contra.
4. **Given** una solicitud aún pendiente, **When** se pide el tiempo de resolución, **Then** **no
   cuenta como cero**: sigue abierta.

---

### User Story 3 - El Director de Estrategia evalúa el catálogo de planes (Priority: P3)

Los tres informes de **OT05**: cómo se reparte la cartera entre planes, si los clientes usan lo que
contratan, y si las severidades que pagan son las que realmente atienden.

**Why this priority**: es el bloque que informa el **diseño del catálogo**, no la operación
financiera diaria. Y uno de sus informes depende de un hecho que pertenece a otro departamento (ver
aclaración).

⚠️ **Su autoridad es distinta**: el §5.1 del SRS asigna el catálogo y los precios al **Director de
Estrategia**, no al Financiero. En este departamento la autoridad está repartida.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 11 | Distribución de la cartera por plan y nivel: % e ingreso aportado | OT05 | ± |
| 12 | **Utilización de los límites** frente a lo contratado — unidades y usuarios | OT05 | ± |
| 13 | Severidades habilitadas frente a severidades realmente atendidas | OT05 | ± |

**Acceptance Scenarios**:

1. **Given** un cliente con un plan que permite 25 unidades y 5 dadas de alta, **When** se pide la
   utilización de límites, **Then** muestra 5 de 25 **con ambos números**, no solo el porcentaje.
2. **Given** un plan que habilita severidades 1 y 2 y un cliente que solo tuvo casos de severidad 1,
   **When** se pide el contraste, **Then** aparece la severidad habilitada **y no usada**, que es la
   señal de que paga por algo que no necesita.
3. **Given** un plan de precio cero, **When** se pide la distribución de la cartera, **Then** cuenta
   en el reparto de clientes pero **aporta cero ingreso**, y ambas cifras se ven por separado.

---

### Edge Cases

- **Una suscripción con vigencia invertida** —fin antes que inicio—. Queda **excluida de toda métrica
  de duración** y se cuenta aparte como dato inconsistente. Nunca produce una duración negativa.
- **Una suscripción sin periodicidad.** No entra en el MRR: no se puede normalizar lo que no se sabe
  cada cuánto se cobra.
- **Un plan de precio cero.** Cuenta como cliente, aporta cero ingreso, y no se excluye del reparto.
- **Una factura anulada o nota de crédito.** **Resta** de los ingresos; no se ignora ni se suma.
- **Una factura en disputa.** No es impaga. Se cuenta en su propio estado.
- **Un período sin facturas.** Devuelve vacío explícito, distinto de «se facturó cero».
- **Una solicitud de cambio pendiente.** No cuenta como resuelta en cero días.
- **Un cliente sin método de pago.** Aparece aunque no tenga ninguna fila en la tabla de métodos: es
  una **diferencia de conjuntos**, y el que falta es justo el que interesa.

---

## Requirements *(mandatory)*

### Funcionamiento general

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos por informe.
- **FR-002**: Si falta un dato, DEBE ampliarse el modelo según su procedimiento de crecimiento.
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo.
- **FR-004**: Toda consulta sobre un hecho acumulado o una dimensión DEBE forzar la versión final.
- **FR-005**: Todo informe DEBE aceptar un rango de fechas y devolver solo ese período.

### El estado de una suscripción ⚠️

- **FR-006**: Los informes NO DEBEN usar `activo` para determinar si una suscripción está vigente.
  **Hay suscripciones canceladas con esa columna en verdadero.**
- **FR-007**: La vigencia DEBE derivarse del **estado y del intervalo de fechas**, no de una sola
  columna.
- **FR-008**: Una suscripción con **fecha de fin anterior a la de inicio** DEBE excluirse de toda
  métrica de duración y contarse aparte como **dato inconsistente**. Nunca puede producir una
  duración negativa.
- **FR-009**: `motivocancelacion` NO DEBE tomarse como señal de cancelación: **está poblado en
  suscripciones activas**. Solo se lee cuando el estado dice que se canceló.
- **FR-010**: Las tres formas de «sin motivo» del origen —nulo, cadena vacía y ausencia— DEBEN
  unificarse en una sola en el modelo.

### Ingreso recurrente

- **FR-011**: El MRR DEBE calcularse **normalizando toda periodicidad a mensual** antes de sumar.
- **FR-012**: Una suscripción **sin periodicidad** DEBE quedar fuera del MRR y contarse aparte.
- **FR-013**: El MRR DEBE usar el **precio de la suscripción**, no el de lista del plan: es lo que el
  cliente paga realmente, y el catálogo tiene planes con el mismo nivel y precios distintos.
- **FR-014**: La variación mes a mes DEBE descomponerse en **nuevo, expansión, contracción y baja**,
  no solo el neto: un MRR plano puede esconder altas y bajas que se compensan.

### Facturación y cobro

- **FR-015**: Los ingresos DEBEN **restar** las notas de crédito y las facturas anuladas.
- **FR-016**: Una factura **en disputa** NO DEBE contarse como impaga: son problemas distintos, y
  mezclarlas convierte una discrepancia comercial en mora.
- **FR-017**: La tasa de cobro al primer intento DEBE distinguir **pagada sin reintentos** de
  **pagada tras reintentos**: ambas están pagadas, y lo que las separa es el esfuerzo.
- **FR-018**: La efectividad del dunning DEBE medir la recuperación **por escalón de reintento**, no
  el total.
- **FR-019**: Los clientes sin método de pago DEBEN obtenerse como **diferencia de conjuntos**: el
  cliente que no tiene ninguna fila es justo el que interesa, y una unión ordinaria lo perdería.

### Movimientos de plan

- **FR-020**: Los movimientos DEBEN clasificarse en **upgrade, downgrade y lateral**, según el delta
  de precio, y devolver ese delta.
- **FR-021**: Una solicitud **aprobada pero pendiente de aplicar** DEBE distinguirse de una ya
  aplicada. ⚠️ El plan programado usa un **centinela `0`** que significa «ninguno», no un plan.
- **FR-022**: El NRR DEBE calcularse sobre la **cohorte de clientes existentes al inicio del
  período**, y mostrar sus componentes: expansión, contracción y baja.
- **FR-023**: El tiempo de resolución DEBE contar las solicitudes **resueltas**, sea cual sea el
  sentido: una rechazada se resolvió.
- **FR-024**: Una solicitud **pendiente** NO DEBE contar como resuelta en cero días.

### Catálogo y uso

- **FR-025**: Los límites del plan DEBEN quedar **desplegados en columnas** en el modelo. El origen
  los guarda como texto estructurado, y obligar a cada consulta a interpretarlo repartiría esa lógica
  por todo el catálogo.
- **FR-026**: Las severidades habilitadas DEBEN quedar igualmente desplegadas y comparables con las
  atendidas.
- **FR-027**: La utilización de límites DEBE devolver **lo usado y lo contratado**, no solo el
  porcentaje: 5 de 25 y 500 de 2 500 son situaciones distintas.
- **FR-028**: Un plan de **precio cero** DEBE contar en el reparto de clientes y aportar **cero
  ingreso**, con ambas cifras visibles por separado.

#### La dimensión de límites que pertenece a otro departamento *(decisión 2026-08-14)*

Los límites del plan tienen tres dimensiones: unidades, usuarios y llamadas API. Las dos primeras se
resuelven con datos ya modelados; **las llamadas viven en el dominio de Partners y API**, aún sin
especificar.

- **FR-029**: La utilización de límites DEBE entregar **unidades y usuarios** ahora, cada una con lo
  usado y lo contratado.
- **FR-030**: El informe DEBE **declarar explícitamente** que la dimensión de llamadas API está
  pendiente, y **no DEBE** devolver un campo de llamadas vacío ni en cero. Un cero significaría «no
  consume la API», que es una afirmación distinta de «todavía no lo medimos».
- **FR-031**: Este módulo **NO DEBE** modelar el hecho de llamadas API. Pertenece a Partners y API, y
  adelantarse obligaría a ese departamento a vivir con un diseño que no eligió o a rehacerlo.

### Presentación y límites

- **FR-032**: Ninguna respuesta DEBE incluir **medios de cobro**: ni token de pasarela, ni últimos
  dígitos, ni identificador fiscal. Se informa **si hay método vigente**, no cuál.
- **FR-033**: Ninguna respuesta DEBE desglosar por **persona**. ⚠️ El catálogo pide el tiempo de
  resolución «por administrador»: se entrega agregado, como ya se decidió con el técnico de campo y
  el validador de región.
- **FR-034**: Los textos libres —motivo de anulación, motivo de rechazo— NO DEBEN copiarse al modelo;
  se clasifican y se cuentan.
- **FR-035**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-036**: Todo importe DEBE devolverse con su **moneda y periodicidad** explícitas.

### Acceso

- **FR-037**: Los informes DEBEN ser de solo lectura.
- **FR-038**: El **Director Financiero** DEBE acceder sin acotamiento a los informes de facturación,
  cobro y cartera.
- **FR-039**: El **Director de Estrategia** DEBE acceder sin acotamiento a los informes de catálogo y
  precios. ⚠️ La autoridad de este departamento **está repartida** según el §5.1 del SRS.
- **FR-040**: Un **cliente** NO DEBE acceder a ningún informe de este módulo: son cifras agregadas de
  toda la cartera.
- **FR-041**: La exención de la autoridad NO DEBE alcanzar al dato sensible.

### Ampliaciones del modelo

- **FR-042**: El modelo DEBE incorporar una **dimensión de plan** con sus límites y severidades
  desplegados.
- **FR-043**: El modelo DEBE incorporar una **dimensión de cliente** con su tipo y su estado
  comercial, sin identificador fiscal ni datos de contacto.
- **FR-044**: El modelo DEBE incorporar un **hecho de suscripción** como instantánea acumulada, con
  sus hitos —alta, renovación, suspensión, cancelación— y su precio normalizado a mensual.
- **FR-045**: El modelo DEBE incorporar un **hecho de factura** con su estado, sus reintentos y su
  condición de nota de crédito, **sin medios de cobro**.
- **FR-046**: El modelo DEBE incorporar un **hecho de solicitud de cambio de plan** con su resultado,
  su delta de precio y su tiempo de resolución.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los 13 informes se obtienen sin que exista ninguna tabla dedicada a un informe.
- **SC-002**: Una suscripción cancelada **no aporta MRR**, pese a tener la columna de actividad en
  verdadero.
- **SC-003**: El MRR de suscripciones con periodicidades distintas es igual a la suma de sus precios
  **normalizados a mensual**.
- **SC-004**: La suscripción con vigencia invertida **no produce ninguna duración negativa** y se
  reporta como dato inconsistente.
- **SC-005**: Una factura en disputa **no aparece** entre las impagas.
- **SC-006**: Los ingresos con una nota de crédito son **menores** que sin ella.
- **SC-007**: Una solicitud pendiente **no aparece** con tiempo de resolución cero.
- **SC-008**: La variación del MRR se descompone en cuatro componentes que suman el neto.
- **SC-009**: Ningún informe devuelve medios de cobro ni desglosa por persona, **para ningún rol**.
- **SC-010**: Un cliente con plan de precio cero cuenta en el reparto y aporta cero ingreso.
- **SC-011**: Añadir estos informes **no altera** ninguna cifra de los tres departamentos anteriores.

---

## Assumptions

- **El modelo analítico está cargado**, y las fases 1 y 2 de Emergencias implementadas: este módulo
  reutiliza su plomería.
- **El período por defecto** son los últimos 30 días; los informes de MRR y NRR usan **mes natural**,
  porque comparar meses parciales no tiene sentido financiero.
- **La moneda es única**: el sistema no registra ninguna, así que se asume una sola y se declara.
- **Los escalones de dunning** por defecto son D+3 y D+5, parametrizables.
- **El frontend queda fuera de alcance.**

---

## Riesgos ⚠️

### Los cinco indicadores BSC se calcularán sobre cuatro suscripciones

Medido: **4 suscripciones, 6 facturas, 6 planes, 3 métodos de pago, 4 solicitudes de cambio**.

Es el departamento con **más indicadores comprometidos y menos datos** de todo el proyecto. Los
informes serán **correctos y no representativos**: un NRR sobre cuatro clientes no es un indicador,
es una anécdota.

**No bloquea nada.** Se registra para que nadie lleve esas cifras a una decisión antes de que la
cartera crezca.

### Dos defectos de dato ya presentes en cuatro filas

Con solo cuatro suscripciones ya aparecen **una con vigencia invertida** y **una cancelada marcada
como activa**. En una cartera de cientos, esa proporción sería un problema serio de calidad de dato.

El modelo los detecta y los aísla en vez de propagarlos, pero **el origen sigue produciéndolos**.

---

## Aclaración, resuelta el 2026-08-14

**Informe #12 → entrega unidades y usuarios; las llamadas API quedan para Partners** (FR-029 a
FR-031).

Los límites tienen tres dimensiones. Las dos primeras se resuelven con datos ya modelados; las
llamadas viven en `Fact_LogLlamadaAPI`, corazón de **Partners y API**, aún sin especificar.

**Lo que hace honesta a la decisión es FR-030**: el informe declara que esa dimensión falta y **no
devuelve un campo de llamadas vacío ni en cero**. Un cero diría «este cliente no consume la API»,
que es una afirmación completamente distinta de «todavía no lo medimos».

**Y FR-031 impide adelantarse**: modelar aquí el hecho de llamadas obligaría a Partners a vivir con
un diseño que no eligió, o a rehacerlo. Cuando ese departamento se especifique, este informe se
amplía con la tercera dimensión.

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato.
- **[`Emergencias/informes-compuestos-modelo/`](../../Emergencias/informes-compuestos-modelo/)** —
  aporta la plomería.
- **[`Red-Operativa/informes-compuestos-modelo/`](../../Red-Operativa/informes-compuestos-modelo/)** —
  `dim_unidad` sirve para contar unidades contra el límite contratado.
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — la autoridad repartida de este departamento.
