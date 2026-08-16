# Data Model — Modelo Analítico Táctico

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

El esquema completo de tablas y columnas vive en
[`contracts/esquema-analitico.md`](contracts/esquema-analitico.md). Este documento explica **el
diseño**: qué representa cada pieza, por qué tiene ese grano y cómo se relacionan.

---

## 1. La forma del modelo

```
                    ┌──────────────┐
                    │  dim_tiempo  │
                    └──────┬───────┘
                           │
   ┌───────────────┐       │       ┌──────────────────┐
   │ dim_geografia ├───────┼───────┤  dim_severidad   │
   └───────┬───────┘       │       └────────┬─────────┘
           │        ┌──────┴──────┐         │
           └────────┤   HECHOS    ├─────────┘
                    │             │
           ┌────────┤  accidente  │────────┐
           │        │  despacho   │        │
           │        └─────────────┘        │
   ┌───────┴────────┐            ┌─────────┴──────────┐
   │   dim_unidad   │            │ dim_origen_despacho│
   │  (versionada)  │            └────────────────────┘
   └────────────────┘
```

**Primera fase**: 2 hechos, 5 dimensiones. El resto del modelo —11 hechos y 7 dimensiones más— está
diseñado y se incorpora sin rehacer nada.

---

## 2. Los hechos: qué representa una fila

### Hecho accidente — instantánea acumulada

**Grano: un caso registrado.** Una fila por accidente, actualizada a medida que avanza.

Los hitos viven **en columnas de la misma fila**:

```
registrado → confirmado → primera asignación → primera llegada → cierre
```

**Por qué acumulada y no de transacción.** Convierte los informes de tiempos en **restas dentro de
una fila**. «Tiempo de reportado a confirmado» y «de asignado a cerrado» dejan de necesitar
emparejar filas y ordenar. Y el envejecimiento de la cartera es inmediato: **un hito ausente es un
caso abierto**.

**Métricas:** vehículos, heridos, víctimas, fallecidos, duración total.
**Marcas de proceso:** si fue descartado, si es duplicado y de cuál.

> ⚠️ **Un hito no alcanzado va ausente**, nunca como cero ni como la fecha de carga. Un cierre con
> fecha de carga convertiría todos los casos abiertos en cerrados el día que se cargaron.

---

### Hecho despacho — instantánea acumulada, grano **intento**

**Grano: un intento de asignación a una unidad.** No un caso, no un par unidad-caso.

Hitos: `notificado → confirmado o rechazado → llegada → retiro`.

**Por qué el intento** (research D1). Con grano de caso, estos informes del catálogo **no son
calculables**:

- Asignación automática frente a manual — necesita el origen de cada intento
- Rechazo y vencimiento por unidad — un rechazo **es** un intento fallido
- Despachos resueltos al primer intento — es un recuento de intentos por caso
- Carga por unidad — una unidad que rechaza tres veces no soportó carga

La revisión del sistema documentó un caso con **seis intentos de cuatro orígenes distintos**. Un
grano que los colapse pierde exactamente eso.

**Métricas derivadas:** tiempo de respuesta, de tránsito y de atención — restas entre hitos.
**Marcas:** origen del despacho, si el retiro fue forzado, motivo del rechazo.

> ⚠️ **Consecuencia que hay que conocer:** «cuántos casos se despacharon» **no es un recuento de
> filas**, es un recuento de casos distintos. Está recogido en el contrato de consumo.

---

### Los once hechos restantes

Diseñados, no construidos en la primera fase:

| Hecho | Grano | Tipo | Departamento |
|---|---|---|---|
| Evidencia | Un elemento levantado en campo | Transacción | Emergencias |
| Estado de unidad | Un cambio de estado | Transacción | Red Operativa |
| Ticket | Un ticket | Acumulada | Soporte |
| Facturación | Una factura | Transacción | Suscripciones |
| **Suscripción mensual** | Una suscripción **por mes** | **Periódica** | Suscripciones |
| Transición de embudo | Un cambio de etapa | Transacción | Ventas |
| Interacción de demo | Un evento del prospecto | Transacción | Ventas |
| Consumo de API | Un intervalo por partner y endpoint | Transacción agregada | Partners |
| Incorporación | Una etapa completada | Transacción | Cuentas |
| Cambio de acceso de partner | Un cambio | Transacción | Partners |
| Validación de región | Un intento | Transacción | Red Operativa |

> **La suscripción mensual es periódica por necesidad.** Un ingreso recurrente **no es un suceso**:
> es un estado que se repite cada mes. Calcularlo desde los sucesos de facturación es la vía habitual
> por la que el MRR sale mal —un mes sin factura emitida no es un mes sin ingreso—.

---

## 3. Las dimensiones: qué describe cada una

| Dimensión | Versionada | Qué resuelve |
|---|:--:|---|
| **Tiempo** | — | Día, semana, mes, trimestre, año, día de semana, franja horaria |
| **Geografía** | — | Aplana los cinco niveles del origen: agrupar por condado sin encadenar búsquedas |
| **Severidad** | — | Nombre y orden de gravedad |
| **Unidad** | ✅ | Placa, tipo, capacidad **y su proveedor en cada momento** |
| **Origen de despacho** | — | Automático, manual, escalado a zona vecina |

**Diseñadas para las fases siguientes:** cliente (✅), plan (✅), partner (✅), región operativa (✅),
usuario, servicio y canal de captación.

### Por qué la geografía se aplana

El origen encadena país → estado → condado → ciudad → calle. Un informe que agrupe por condado
tendría que recorrer tres saltos. La dimensión guarda **una fila por calle con todos sus
ascendientes**, y agrupar por cualquier nivel es una columna.

### Qué significa «versionada»

Una dimensión versionada guarda **varias filas por entidad**, cada una con su vigencia:

| unidad | proveedor | desde | hasta | vigente |
|---|---|---|---|:--:|
| LOTE-A2 | Rescate Andino | 2026-01-15 | 2026-06-30 | no |
| LOTE-A2 | Grúas del Sur | 2026-07-01 | — | **sí** |

Un despacho de marzo apunta a la **primera** fila. Uno de agosto, a la segunda. Un informe que
agrupe despachos pasados por proveedor obtiene la atribución correcta **por construcción**, sin que
nadie tenga que acordarse.

---

## 4. El defecto que esto resuelve

Hoy, el informe de rendimiento por proveedor tiene documentada esta limitación en su propio código:

> *«no historiza cambios de proveedor, así que usa el proveedor **actual** de la unidad para todos
> los períodos»*

**Si una unidad cambia de proveedor, todos sus despachos pasados se reatribuyen al proveedor nuevo.**
No falla ni avisa: reescribe la historia, y un proveedor puede aparecer respondiendo por despachos
que nunca atendió.

Con dimensión versionada eso **no puede ocurrir**: el hecho quedó apuntando a la versión que estaba
vigente cuando ocurrió.

### Pero el pasado anterior a la primera carga no existe ⚠️

Las versiones se construyen **observando cómo cambia la fuente entre cargas**. Antes de la primera
carga no hay observación: solo se conoce el estado de ese día.

**Por eso cada versión declara si su fecha de inicio es real o significa «desde la primera carga».**
Sin esa marca, el modelo cometería el mismo error que corrige: presentar «no lo sabemos» como
«siempre fue así».

**Qué se puede reconstruir del origen y qué no:**

| Dimensión | Reconstruible | Desde dónde |
|---|:--:|---|
| **Unidad → proveedor** | ❌ | **Nada lo historiza** — es el caso ancla |
| Partner → plan | ✅ | Bitácora de acceso |
| Región → estado | ✅ | Intentos de validación |
| Cliente → plan | ⚠️ Parcial | Solicitudes de cambio aprobadas |
| Cliente → estado | ⚠️ Parcial | Solo transferencias de propiedad |

---

## 5. Cómo se relacionan hechos y dimensiones

**Cada hecho copia los atributos por los que casi siempre se agrupa** (research D4):

| Se copia en el hecho | Se consulta en la dimensión |
|---|---|
| Fecha, mes, día de semana, franja | El resto del calendario |
| Nombre de severidad | Descripción, orden |
| Condado y ciudad | Calle, país |
| Nombre de unidad **y su proveedor al momento del hecho** | Placa, capacidad, tipo, zona |

**El almacén es columnar**: leer tres columnas más de una tabla ancha cuesta casi nada; unir con una
dimensión obliga a materializarla y cruzarla. Con lo más frecuente ya en el hecho, **la mayoría de
los informes del catálogo no une con nada**.

> ⚠️ Los atributos versionados se copian **con su valor al momento del hecho**, no como referencia
> mutable. Copiar «el proveedor actual» reintroduciría el defecto de §4.

---

## 6. Cómo se carga

**Un flujo por hecho, no por informe** — ~13 frente a ~105.

**Orden obligatorio:** dimensiones primero, hechos después. Un hecho necesita saber qué versión de
dimensión estaba vigente, y esa versión tiene que existir.

**Idempotencia por partición** (research D3). Los hechos se particionan por mes; recargar un período
**descarta y repuebla su partición**. Es una operación de metadatos: instantánea, sin reescritura, y
convierte la idempotencia en propiedad de la estructura en lugar de en una operación costosa que hay
que recordar hacer bien.

**Un hecho cuya dimensión no existe se carga igualmente**, con la dimensión marcada como desconocida.
**Nunca se descarta el hecho**: perder un accidente porque su calle no estaba cargada sería
inaceptable.

---

## 7. Qué se conserva de lo construido

| Se conserva | Se retira |
|---|---|
| El patrón de carga por ficheros intermedios | Las tres tablas por informe |
| Los clientes de origen y destino | Los tres flujos por informe |
| La escritura y lectura de ficheros intermedios | |
| **La lógica de detección de huecos de señal** — función pura y probada, pasa a alimentar un hecho | |
| El flujo de referencia y el de recarga histórica | |

**Orden:** las tres tablas se retiran **cuando el modelo cubra sus informes**, no antes. Retirarlas
antes dejaría al sistema sin ellos.

---

## 8. Resumen de la primera fase

| Pieza | Tipo | Grano | Cuidado |
|---|---|---|---|
| **hecho accidente** | Acumulada | Un caso | Hito ausente ≠ cero ni fecha de carga |
| **hecho despacho** | Acumulada | **Un intento** | Contar filas ≠ contar casos |
| dim tiempo | — | Un día | — |
| dim geografía | — | Una calle, con sus ascendientes | — |
| dim severidad | — | Un nivel | — |
| **dim unidad** | **Versionada** | Una versión de unidad | La historia empieza en la primera carga |
| dim origen despacho | — | Un origen | — |
