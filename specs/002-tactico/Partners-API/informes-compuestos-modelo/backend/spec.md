# Feature Specification: Informes Compuestos de Partners y API sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Partners-API/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos compuestos de Partners y API — los informes agregados de OT08 a OT10, resueltos con consultas sobre el modelo analítico"

---

## Contexto

Quinto departamento sobre el modelo analítico. Partners y API responde a **quién consume la
plataforma por integración y cuánto**: incorpora partners externos, controla y tarifica su consumo, y
entrega datos según el alcance contratado.

**Es el único departamento con supervisión real ya construida.** OT09 tiene consola de logs, reporte
mensual y métricas de consumo; OT08 y OT10, nada.

**Y es el departamento del que dependía Suscripciones**: aquí se modela el hecho de llamadas API que
aquel módulo se abstuvo deliberadamente de construir.

> ### ⚠️ Seis hallazgos medidos antes de especificar
>
> **1. Tercera discrepancia del catálogo.** Su resumen atribuye **9 simples y 13 compuestos**;
> contando las filas salen **9 y 14**. La fila del motivo de credencial inactiva está marcada como
> *«reclasificado a compuesto»*, que es la causa más probable de las tres discrepancias detectadas
> —Emergencias, Suscripciones y este—.
>
> **2. ⚠️ Dos fuentes de consumo que no cuadran.** `Fact_APIIntegracion` declara **500 llamadas** con
> 4 errores; `Fact_LogLlamadaAPI` tiene **18 filas** en total. Una es agregada en el origen y la otra
> es el detalle, y **no coinciden en un orden de magnitud**. Ver *Aclaración pendiente*.
>
> **3. El motivo por el que una credencial está inactiva no vive en la credencial.**
> `Dim_CredencialAPI` tiene `activo` y **ninguna columna de motivo**: revocación, cascada y
> expiración son **indistinguibles**. El motivo está en la bitácora de acceso.
>
> **4. Dos centinelas de fecha.** `fecha_expiracion = 253402300799000` es el año **9999**
> —«nunca expira»— y `fecha_retiro = 0` es la época cero —«no retirada»—. Ninguna de las dos es una
> fecha: un promedio de vigencia sobre la primera daría **2,9 millones de días**.
>
> **5. La versión del contrato no está en el log**, pero **sí es derivable del endpoint**:
> `/api/v1/datos/accidentes` contiene `v1`. Cuidado: `version` **no es única** —dos servicios
> distintos comparten `'v1'`—, así que la clave real es (servicio, versión).
>
> **6. El log no registra qué zona se consultó.** Guarda el endpoint, el código y la latencia, pero
> no el ámbito geográfico de la respuesta. Ver *Aclaración pendiente*.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Tecnológico controla el consumo de la API (Priority: P1) 🎯 MVP

Los siete informes de **OT09**: cuánto consume cada partner, por qué endpoint, con qué latencia real,
qué errores devuelve y cuánto ingreso genera el excedente.

**Why this priority**: es el único bloque **con supervisión ya construida** —y con dos defectos
documentados: las métricas actuales dan **solo latencia media, sin p95 ni desglose por endpoint**.
Contiene además dos indicadores BSC.

**Independent Test**: pedir la latencia p95 de un endpoint y comprobar que es mayor o igual que su
media, y que ambas se calculan sobre el mismo conjunto de llamadas.

| # | Informe | OT | Origen | Hoy |
|--:|---|---|---|---|
| 1 | Métricas de consumo por partner | OT09 | **CU-T12** | 🟡 solo media |
| 2 | Reporte mensual de consumo por partner | OT09 | **CU-T12** | 🟢 |
| 3 | Consumo por endpoint y método | OT09 | **CU-T12** | ⚪ |
| 4 | **Latencia p95 por endpoint** | OT09 | **BSC** | ⚪ |
| 5 | Taxonomía de errores y su evolución temporal | OT09 | **CU-T12** | ⚪ |
| 6 | Comparativa entre partners y patrones anómalos | OT09 | ± | ⚪ |
| 7 | **Participación de ingresos por API**: excedente frente al ingreso base | OT09 | **BSC** | ⚪ |

**Acceptance Scenarios**:

1. **Given** un conjunto de llamadas con latencias dispares, **When** se pide la latencia,
   **Then** devuelve **p95 y media**, y la p95 es mayor o igual. ⚠️ La media sola oculta la cola:
   un endpoint con media de 90 ms puede tener un 5 % de llamadas por encima de 2 segundos.
2. **Given** llamadas a dos endpoints distintos, **When** se pide el consumo, **Then** se desglosan
   **por endpoint y método**, no solo el total del partner.
3. **Given** llamadas con códigos 200, 403, 429 y 500, **When** se pide la taxonomía de errores,
   **Then** las **429 se distinguen de las 500**: una es límite de cupo —un problema de contrato— y
   la otra un fallo del servicio.
4. **Given** un partner que superó su cupo mensual, **When** se pide la participación de ingresos,
   **Then** su excedente aparece **separado del ingreso base**.
5. **Given** un partner sin ninguna llamada en el período, **When** se piden las métricas, **Then**
   aparece con **cero llamadas**, no ausente: un partner que dejó de consumir es justo lo que hay
   que ver.

---

### User Story 2 - El Director Tecnológico vigila la incorporación de partners (Priority: P2)

Los cuatro informes de **OT08**: cuánto tarda un partner en llegar a producción, por qué se rechazan
sus solicitudes, por qué está inactiva una credencial y qué versión del contrato usa cada uno.

**Why this priority**: OT08 **no tiene nada construido** y contiene un indicador BSC. Va después de
OT09 porque el consumo es la pregunta diaria y la incorporación es episódica.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 8 | **Motivo por el que una credencial está inactiva** | OT08 | SRS |
| 9 | **Tiempo de incorporación**: de registro a producción, por etapa | OT08 | ± |
| 10 | **Adopción de versiones del contrato**: % de llamadas por versión | OT08 | **BSC** |
| 11 | Tasa de rechazo de solicitudes de producción y sus motivos | OT08 | ± |

**Acceptance Scenarios**:

1. **Given** una credencial revocada y otra caducada, **When** se pide el motivo de inactividad,
   **Then** **se distinguen**. ⚠️ En el sistema operativo ambas son solo `activo = false`: el motivo
   solo existe en la bitácora de acceso.
2. **Given** una credencial **sin fecha de expiración real** —el centinela del año 9999—, **When**
   se piden las próximas a vencer, **Then** **no aparece**, y su vigencia se trata como **ausente**,
   nunca como una fecha lejanísima.
3. **Given** un partner que aún no llegó a producción, **When** se pide el tiempo de incorporación,
   **Then** queda **fuera de la media** y se cuenta aparte: sigue en proceso, no tardó cero.
4. **Given** llamadas a distintas versiones del contrato, **When** se pide la adopción, **Then** el
   porcentaje se calcula **por (servicio, versión)**: dos servicios distintos comparten el nombre de
   versión.

---

### User Story 3 - El Director Tecnológico verifica la entrega contratada (Priority: P3)

Los tres informes de **OT10**: cuántos clientes tienen integración activa, cuántos expedientes se
entregan por cada canal, y si las consultas respetan el alcance contratado.

**Why this priority**: contiene un indicador BSC con meta explícita (≥70 %), pero **uno de sus tres
informes depende de un dato que el log no registra**.

| # | Informe | OT | Origen | Construible |
|--:|---|---|---|---|
| 12 | **Clientes con integración API activa** — meta ≥70 % | OT10 | **BSC** | ✅ |
| 13 | Volumen de expedientes entregados por cliente y canal | OT10 | ± | ✅ |
| ~~14~~ | ~~Alcance efectivo frente a contratado~~ | OT10 | SRS | ⛔ **fuera de alcance** (FR-024) |

**Acceptance Scenarios**:

1. **Given** clientes con y sin llamadas en el período, **When** se pide el porcentaje con
   integración activa, **Then** el denominador son **todos los clientes**, no solo los que tienen
   partner: si no, el indicador daría siempre 100 %.
2. **Given** entregas por portal y por API, **When** se pide el volumen de expedientes, **Then**
   ambos canales aparecen por separado con su total.

---

### Edge Cases

- **Un partner sin llamadas.** Aparece con cero, no ausente.
- **Una credencial que nunca expira.** Su vigencia es **ausente**, no el año 9999.
- **Una versión de contrato no retirada.** Su fecha de retiro es **ausente**, no la época cero.
- **Un endpoint con una sola llamada.** Su p95 **es esa llamada**, y el informe muestra el número de
  muestras para que nadie lea un percentil sobre n=1 como si fuera estable.
- **Una llamada con código 429.** Cuenta como **límite de cupo**, no como error del servicio.
- **Un partner suspendido a mitad de período.** Su consumo cuenta **hasta la suspensión**.
- **Un cliente sin preferencias declaradas.** No tiene zonas contratadas: cualquier consulta suya es
  «sin alcance declarado», que **no es lo mismo** que fuera de alcance.

---

## Requirements *(mandatory)*

### Funcionamiento general

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos por informe.
- **FR-002**: Si falta un dato, DEBE ampliarse el modelo según su procedimiento de crecimiento.
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo.
- **FR-004**: Toda consulta sobre un hecho acumulado o una dimensión DEBE forzar la versión final.
- **FR-005**: Todo informe DEBE aceptar un rango de fechas y devolver solo ese período.

### El consumo

#### La fuente del consumo *(decisión 2026-08-14)*

El sistema operativo tiene **dos fuentes de consumo que no cuadran**: una tabla preagregada que
declara 500 llamadas por fila, y un detalle de 18 registros. Difieren en un orden de magnitud.

- **FR-006**: El consumo DEBE medirse **exclusivamente sobre el detalle de llamadas**. Es la única
  fuente que permite latencia p95, desglose por endpoint y taxonomía de errores — tres informes del
  catálogo que hoy no existen y que una agregación previa hace imposibles.
- **FR-007**: El modelo **NO DEBE** cargar la tabla preagregada del sistema operativo. Tenerla al
  lado invitaría a usarla cuando el detalle diera cifras «demasiado bajas», y el departamento
  volvería a tener dos verdades.
- **FR-008**: Los informes DEBEN devolver el **número de llamadas sobre el que se calcula cada
  medida**. Con el tráfico actual las cifras serán pequeñas, y quien las lea debe poder distinguir
  «poco consumo» de «poco registrado».
- **FR-009**: La latencia DEBE devolverse como **p95 y media**, con el **número de muestras**. Un
  percentil sobre pocas llamadas no es estable, y quien lo lea debe poder saberlo.
- **FR-010**: El consumo DEBE poder desglosarse **por endpoint y método**, no solo por partner.
- **FR-011**: Las llamadas rechazadas por **límite de cupo (429)** DEBEN distinguirse de los **errores
  del servicio (5xx)** y de los **rechazos de autorización (403)**: son tres problemas distintos con
  tres responsables distintos.
- **FR-012**: Un partner **sin llamadas** en el período DEBE aparecer con cero, no omitirse.
- **FR-013**: El consumo de un partner suspendido a mitad de período DEBE contar **hasta la
  suspensión**.
- **FR-014**: El excedente DEBE calcularse contra el **cupo del plan vigente en el período**, y
  presentarse **separado del ingreso base**.

### La incorporación

- **FR-015**: El motivo de inactividad de una credencial DEBE derivarse de la **bitácora de acceso**.
  ⚠️ La credencial solo guarda un indicador de actividad: revocación, cascada y expiración son
  indistinguibles en ella.
- **FR-016**: Los tres motivos —revocada, desactivada en cascada y expirada— DEBEN presentarse por
  separado.
- **FR-017**: Una credencial **sin expiración real** —centinela del año 9999— DEBE tratarse como
  **vigencia ausente**, nunca como una fecha. No aparece entre las próximas a vencer ni entra en
  ningún promedio de vigencia.
- **FR-018**: Una versión de contrato **no retirada** —centinela de época cero— DEBE tratarse como
  **fecha de retiro ausente**.
- **FR-019**: El tiempo de incorporación DEBE medirse **solo sobre los partners que llegaron a
  producción**; los que siguen en proceso se cuentan aparte y **no como cero**.
- **FR-020**: La adopción de versiones DEBE calcularse por **(servicio, versión)**: el nombre de
  versión **no es único** entre servicios.
- **FR-021**: La versión de una llamada DEBE derivarse del endpoint y **declararse como derivada**.
  El log no la registra, y una derivación basada en la forma del path se rompe si el path cambia.

### La entrega

- **FR-022**: El porcentaje de clientes con integración activa DEBE usar como denominador **todos los
  clientes**, no solo los que tienen partner: si no, daría siempre 100 %.
- **FR-023**: El volumen de expedientes DEBE separar **portal y API** como canales distintos.
#### El alcance geográfico queda fuera *(decisión 2026-08-14)*

- **FR-024**: El informe de **alcance efectivo frente a contratado queda fuera de alcance** mientras
  el log no registre el ámbito geográfico de cada consulta. Guarda endpoint, código y latencia, y
  nada más.
- **FR-025**: El modelo **NO DEBE** inferir la zona consultada interpretando los parámetros del
  endpoint. Esa derivación **falla en silencio**: en cuanto un cliente consulte con otro parámetro,
  el informe no distinguiría «consulta fuera de zona» de «no supe leerla», y las dos se verían igual.
- **FR-026**: El hueco DEBE quedar registrado como **carencia del sistema operativo**, no como
  informe pendiente de este módulo: lo que falta es que el log registre la zona.

### Presentación y límites

- **FR-027**: Ninguna respuesta DEBE incluir **secretos de autenticación**: ni hash de secreto, ni
  token, ni valor de credencial. Se informa el **nombre** de la credencial y su estado.
- **FR-028**: Ninguna respuesta DEBE incluir **contacto técnico del partner** ni **IP de origen** de
  las llamadas. La IP identifica a un consumidor concreto y ningún informe del catálogo la necesita.
- **FR-029**: Ninguna respuesta DEBE desglosar por **persona que ejecutó un cambio** de acceso.
- **FR-030**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-031**: Un período sin llamadas DEBE devolver un resultado vacío explícito.

### Acceso

- **FR-032**: Los informes DEBEN ser de solo lectura.
- **FR-033**: El **Director Tecnológico** —autoridad de Partners y API según el §5.1 del SRS— DEBE
  acceder sin acotamiento por titularidad.
- **FR-034**: Un **partner** NO DEBE acceder a los informes de este módulo: son cifras comparadas de
  todos los partners. Su propio consumo lo ve por el autoservicio ya existente.
- **FR-035**: La exención de la autoridad NO DEBE alcanzar al dato sensible.

### Ampliaciones del modelo

- **FR-036**: El modelo DEBE incorporar un **hecho de llamada API**, con endpoint, método, código,
  latencia y versión derivada, **sin IP de origen**.
- **FR-037**: El modelo DEBE incorporar una **dimensión de partner** con su plan, sus cupos y su
  estado, **sin contacto técnico**.
- **FR-038**: El modelo DEBE incorporar una **dimensión de credencial** con su entorno, su estado y su
  motivo de inactividad derivado, **sin secreto**.
- **FR-039**: El modelo DEBE incorporar un **hecho de cambio de acceso** derivado de la bitácora, con
  su tipo y su instante.
- **FR-040**: El modelo DEBE incorporar una **dimensión de versión de contrato** con su vigencia.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los **13 informes en alcance** se obtienen sin que exista ninguna tabla dedicada a un
  informe.
- **SC-011**: Toda medida de consumo declara **sobre cuántas llamadas** se calculó, de modo que «poco
  consumo» y «poco registrado» sean distinguibles.
- **SC-012**: El modelo **no contiene** la tabla de consumo preagregada del sistema operativo: hay
  **una sola fuente** de consumo.
- **SC-002**: La latencia se devuelve como **p95 y media**, con el número de muestras. Hoy solo hay
  media.
- **SC-003**: Revocada, en cascada y expirada **se distinguen** como motivos de inactividad, pese a
  ser indistinguibles en la credencial del sistema operativo.
- **SC-004**: Una credencial que nunca expira **no aparece** entre las próximas a vencer, y no
  contribuye ningún valor a los promedios de vigencia.
- **SC-005**: Las llamadas 429 **no se cuentan** como errores del servicio.
- **SC-006**: Un partner sin llamadas aparece con cero, no desaparece del informe.
- **SC-007**: El porcentaje de clientes con integración activa **puede ser menor que 100 %**: su
  denominador son todos los clientes.
- **SC-008**: Ningún informe devuelve secretos, contacto técnico ni IP de origen, **para ningún rol**.
- **SC-009**: Un partner que aún no llegó a producción **no aparece** con tiempo de incorporación
  cero.
- **SC-010**: Añadir estos informes **no altera** ninguna cifra de los cuatro departamentos
  anteriores.

---

## Assumptions

- **El modelo analítico está cargado**, y las fases 1 y 2 de Emergencias implementadas.
- **El período por defecto** son los últimos 30 días; el reporte mensual usa mes natural.
- **El cupo del plan** se toma del partner, que lo guarda por mes y por minuto.
- **`Dim_Cliente` ya existe** en el modelo: la creó Suscripciones como dimensión conformada. Este
  módulo **la usa, no la recrea**.
- **El frontend queda fuera de alcance.**

---

## Riesgos ⚠️

### Siete informes dependen de una tabla de 18 filas

`Fact_LogLlamadaAPI` sostiene **la mitad del departamento** —consumo por endpoint, p95, taxonomía de
errores, comparativa entre partners, adopción de versiones, integración activa y alcance— y tiene
**18 filas**, con solo **dos endpoints distintos** y cuatro códigos.

Una latencia p95 sobre 18 llamadas es **un número, no un indicador**. Los informes serán correctos y
sus cifras no significarán nada hasta que haya tráfico real. FR-008 y FR-009 obligan a devolver el
número de llamadas y de muestras precisamente por eso.

### El departamento con supervisión construida es también el que más la necesita corregir

Las métricas de consumo actuales dan **solo latencia media**. Un endpoint con media de 90 ms puede
tener un 5 % de llamadas por encima de dos segundos, y el tablero no lo mostraría. **El BSC pide
p95**, y hasta ahora nadie podía calcularlo.

---

## Aclaraciones, resueltas el 2026-08-14

### 1. Manda el detalle de llamadas *(FR-006 a FR-008)*

De las dos fuentes que no cuadran —una preagregada con 500 llamadas por fila, otra con 18 registros
de detalle— **manda el detalle**, y la preagregada **no se carga al modelo**.

**Es la única que permite p95, desglose por endpoint y taxonomía de errores**: tres informes del
catálogo que hoy no existen y que cualquier agregación previa vuelve imposibles.

**El precio, dicho claro:** las cifras serán bajas. FR-008 obliga a devolver el número de llamadas
sobre el que se calcula cada medida, para que nadie confunda **poco consumo** con **poco registrado**.

**Y FR-007 impide la recaída**: tener la tabla preagregada al lado invitaría a usarla el día que el
detalle diera un número incómodo, y el departamento volvería a tener dos verdades.

### 2. El alcance geográfico queda fuera *(FR-024 a FR-026)*

El informe se retira del alcance: **el log no registra la zona consultada**, y derivarla de los
parámetros del endpoint **falla en silencio** — no distinguiría «consulta fuera de zona» de «no supe
leerla».

Queda registrado como **carencia del sistema operativo**, no como informe pendiente de este módulo.
Lo que falta es que el log guarde la zona.

**Alcance final: 13 informes construibles de los 14 del catálogo.**

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato.
- **[`Emergencias/informes-compuestos-modelo/`](../../Emergencias/informes-compuestos-modelo/)** —
  aporta la plomería.
- **[`Suscripciones-Facturacion/informes-compuestos-modelo/`](../../Suscripciones-Facturacion/informes-compuestos-modelo/)** —
  aporta `dim_cliente` y `hecho_factura`, y **espera de este módulo** el hecho de llamadas API para
  completar su informe de utilización de límites.
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — quién ve qué.
