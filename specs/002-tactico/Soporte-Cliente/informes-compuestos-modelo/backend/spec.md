# Feature Specification: Informes Compuestos de Soporte al Cliente sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Soporte-Cliente/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos compuestos de Soporte al Cliente — los 9 informes agregados de OT19 y OT20, resueltos con consultas sobre el modelo analítico"

---

## Contexto

Séptimo y último departamento operativo sobre el modelo analítico. Soporte al Cliente responde a
**si se atiende dentro de lo comprometido**: resuelve incidencias bajo un SLA por plan, y escala
automáticamente cuando ese SLA se pone en riesgo.

**Uno de sus nueve informes ya existe**, el tablero de cola, **con dos defectos documentados**: lee
100 000 tickets a memoria y no admite corte temporal ni desglose por agente.

> ### ⚠️ Seis hallazgos medidos antes de especificar
>
> **1. ✅ El SLA está versionado en el origen, y bien.** `Dim_SLAConfig` tiene
> `fechavigenciadesde` y `fechavigenciahasta`, y hay una configuración cuyo tiempo de resolución
> **pasó de 86 400 a 7 200 segundos**: la vieja quedó cerrada y la nueva abierta.
>
> **Es el primer caso del proyecto en que el sistema operativo versiona correctamente**, después de
> ocho departamentos donde no lo hacía. El modelo solo tiene que respetarlo — y respetarlo importa:
> medir un ticket de hace un mes contra el SLA nuevo lo convertiría de cumplido en **incumplido**.
>
> **2. ⚠️ `idservicio` es nulo en los 14 tickets.** El informe «tickets por servicio afectado» **no
> tiene ni un dato**, pese a que el catálogo define 3 servicios.
>
> **3. Los tiempos de SLA valen `0` en los tickets abiertos.** `sla_primera_respuesta`,
> `sla_resolucion` y `tiempo_solucion` son **centinelas**: cero no es «respondió al instante», es
> «aún no».
>
> **4. Solo 8 de 14 tickets tienen SLA asignado.** Tres están `Pendiente_de_clasificacion` y uno
> declara «sin compromiso». Resuelto en FR-011 a FR-014: el cumplimiento se mide solo sobre los
> tickets con compromiso, **y la cobertura se publica en la misma fila**.
>
> **5. El escalado automático es el evento más frecuente**: 13 de las 34 acciones registradas, con 7
> tickets en estado `Escalado` y 8 con SLA incumplido.
>
> **6. `idfactura` es cadena vacía**, no nulo — otra forma de decir «ninguna».

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Gerente de Éxito del Cliente mide el cumplimiento (Priority: P1) 🎯 MVP

Los cuatro informes de **OT19**: cuántos tickets se resuelven en plazo, cómo se reparte por plan, qué
rinde cada agente y qué servicios generan más incidencias.

**Why this priority**: contiene el indicador **BSC de cumplimiento de SLA con meta ≥95 %**, que hoy
no tiene fuente. Y es el bloque que responde a la pregunta que da sentido al departamento: **¿estamos
cumpliendo lo que prometimos?**

**Independent Test**: cambiar el SLA de una configuración y comprobar que un ticket anterior **sigue
midiéndose contra el SLA que estaba vigente cuando ocurrió**.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 1 | **Cumplimiento de SLA**: resueltos en plazo — meta ≥95 % | OT19 | **BSC** |
| 2 | Cumplimiento de SLA **desglosado por plan** | OT19 | ± |
| 3 | **Rendimiento por agente**: volumen, tiempo medio y reaperturas | OT19 | ± |
| 4 | Tickets por servicio afectado y su tiempo de resolución | OT19 | ± |

**Acceptance Scenarios**:

1. **Given** un SLA cuyo tiempo de resolución se acortó de 24 horas a 2, **When** se pide el
   cumplimiento de un ticket **anterior al cambio**, **Then** se mide contra las **24 horas** que
   estaban vigentes. ⚠️ Medirlo contra el nuevo lo convertiría de cumplido en incumplido sin que nada
   hubiera pasado.
2. **Given** un ticket **aún abierto**, **When** se pide el tiempo de resolución, **Then** **no
   cuenta como cero**: los campos de tiempo valen `0` en el sistema operativo mientras el ticket no
   se resuelve, y ese cero es un centinela.
3. **Given** un ticket **sin SLA asignado**, **When** se pide el cumplimiento, **Then** **no cuenta
   como incumplido**: no había compromiso que incumplir. Se cuenta aparte.
4. **Given** un ticket reabierto tras cerrarse, **When** se pide el rendimiento del agente, **Then**
   la **reapertura aparece**: cerrar rápido y reabrir no es resolver.
5. **Given** tickets sin servicio asignado, **When** se pide el informe por servicio, **Then**
   aparecen agrupados como **sin servicio**, con su recuento visible: hoy son **todos**.

---

### User Story 2 - El Gerente de Éxito del Cliente vigila la cola en curso (Priority: P2)

Los tres informes de **OT20** que miran el **ahora**: el tablero de la cola, cómo evoluciona el
incumplimiento y cuánto se escala solo.

**Why this priority**: sustituye el tablero ya construido, cuyos dos defectos están documentados. Va
después del cumplimiento porque el tablero **funciona hoy** —mal, pero funciona— y el BSC no tiene
nada.

| # | Informe | OT | Origen | Hoy |
|--:|---|---|---|---|
| 5 | **Tablero de cola**: estado, prioridad, tipo, cliente, SLA en riesgo | OT20 | **CU-T06** | 🟡 |
| 6 | **Evolución temporal** del incumplimiento de SLA | OT20 | **CU-T06** | ⚪ |
| 7 | Tasa de escalado automático por tipo de incidencia y prioridad | OT20 | ± | ⚪ |

**Acceptance Scenarios**:

1. **Given** un período de un mes, **When** se pide el tablero, **Then** **acepta corte temporal**.
   ⚠️ El tablero actual no lo admite: devuelve la cola entera, sin importar cuándo se abrió cada
   ticket.
2. **Given** varios agentes con tickets asignados, **When** se pide el tablero, **Then** **se puede
   desglosar por agente**. El actual tampoco lo permite.
3. **Given** tickets escalados de forma automática y otros escalados por una persona, **When** se
   pide la tasa de escalado, **Then** **se distinguen**: un escalado automático es una señal del
   sistema; uno humano es una decisión.
4. **Given** una serie de varios meses, **When** se pide la evolución del incumplimiento, **Then**
   cada punto usa el **SLA vigente en su momento**, no el actual.

---

### User Story 3 - El Gerente de Éxito del Cliente anticipa la carga (Priority: P3)

Los dos informes de **OT20** que miran la **tendencia**: si la cola se acumula y qué clientes
repiten.

**Why this priority**: son los que permiten actuar **antes** de incumplir, pero requieren series
temporales que hoy no tienen recorrido — 14 tickets en total.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 8 | Carga entrante frente a resuelta por día: acumulación de la cola | OT20 | ± |
| 9 | Reincidencia: clientes con tickets repetidos sobre el mismo servicio | OT20 | ± |

**Acceptance Scenarios**:

1. **Given** un día con más tickets abiertos que resueltos, **When** se pide la carga, **Then** el
   saldo es **positivo** y el acumulado crece: es la señal de que la cola se está formando.
2. **Given** un cliente con tres tickets sobre el mismo servicio, **When** se pide la reincidencia,
   **Then** aparece con su recuento. ⚠️ Con `idservicio` nulo en todos los tickets, hoy la
   reincidencia **solo puede medirse por tipo de incidencia**, y el informe lo declara.

---

### Edge Cases

- **Un ticket sin SLA asignado.** No cuenta como incumplido ni como cumplido: se cuenta aparte.
- **Un ticket aún abierto.** Sus tiempos son **ausentes**, no cero.
- **Un ticket reabierto.** Cuenta como reapertura y **no** como resolución exitosa.
- **Un SLA modificado.** Los tickets anteriores se miden contra el vigente entonces.
- **Un ticket sin agente asignado.** Aparece agrupado como **sin asignar**: es justo lo que la cola
  necesita ver.
- **Un ticket sin servicio.** Se agrupa como **sin servicio**, con su recuento visible.
- **Un día sin tickets.** Devuelve cero entrantes, no una ausencia de fila: en una serie temporal,
  un día sin datos y un día sin actividad son cosas distintas.

---

## Requirements *(mandatory)*

### Funcionamiento general

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos por informe.
- **FR-002**: Si falta un dato, DEBE ampliarse el modelo según su procedimiento de crecimiento.
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo.
- **FR-004**: Toda consulta sobre un hecho acumulado o una dimensión DEBE forzar la versión final.
- **FR-005**: Todo informe DEBE aceptar un rango de fechas y devolver solo ese período.

### El SLA vigente ⚠️

- **FR-006**: El cumplimiento DEBE medirse contra el **SLA vigente cuando ocurrió el ticket**, no
  contra el actual.
- **FR-007**: El modelo DEBE conservar la **vigencia de cada configuración de SLA**, que el sistema
  operativo **ya registra correctamente**. Es el primer historial del proyecto que no hay que
  reconstruir ni declarar incompleto.
- **FR-008**: Un cambio de SLA **NO DEBE** alterar el cumplimiento ya calculado de tickets
  anteriores.

### Los tiempos y sus centinelas

- **FR-009**: Los tiempos de primera respuesta, resolución y solución DEBEN tratarse como
  **ausentes** cuando el ticket no ha llegado a ese hito. ⚠️ El sistema operativo los guarda como
  `0`, y un cero significaría «respondió al instante».
- **FR-010**: Los promedios de tiempo DEBEN excluir los tickets que no alcanzaron el hito, y
  **contarlos aparte**.

### El cumplimiento

- **FR-011**: Un ticket **sin SLA asignado** NO DEBE contar como incumplido: no había compromiso. El
  denominador del cumplimiento son **solo los tickets con compromiso**.
- **FR-012**: El informe DEBE devolver **en la misma fila** el porcentaje de cumplimiento **y el
  porcentaje de tickets sin compromiso**. ⚠️ No es un adorno: excluir los tickets sin SLA crea un
  incentivo perverso —**cuantos más se queden sin clasificar, mejor sale el indicador**—, y un
  departamento que dejara de clasificar llegaría al 100 %.
- **FR-013**: La cobertura NO DEBE presentarse en un endpoint aparte ni en una nota al pie: va
  **junto a la cifra que condiciona**. Separarlas permitiría publicar un cumplimiento del 100 % sin
  que se viera que la mitad de los tickets no tenía compromiso.
- **FR-014**: El informe DEBE desglosar los tickets sin compromiso por **motivo** —pendiente de
  clasificar, sin compromiso declarado, sin configuración aplicable—: los tres significan cosas
  distintas y solo el primero es un fallo del proceso.
- **FR-015**: El cumplimiento DEBE poder desglosarse **por plan**, usando el plan vigente del cliente
  en el momento del ticket.
- **FR-016**: Una **reapertura** DEBE contar como tal y **no** como resolución exitosa: cerrar rápido
  y reabrir no es resolver.

### La cola y el escalado

- **FR-017**: El tablero de cola DEBE **aceptar corte temporal**. ⚠️ El tablero actual devuelve la
  cola entera sin importar cuándo se abrió cada ticket.
- **FR-018**: El tablero DEBE poder desglosarse **por agente**, cosa que el actual no permite.
- **FR-019**: El escalado **automático** DEBE distinguirse del **humano**: uno es una señal del
  sistema, el otro una decisión.
- **FR-020**: Los tickets **sin agente asignado** DEBEN aparecer agrupados como **sin asignar**: es
  justo lo que la cola necesita ver.

### Las tendencias

- **FR-021**: La carga entrante y la resuelta DEBEN devolverse por día, con su **saldo y su
  acumulado**.
- **FR-022**: Un día **sin tickets** DEBE devolver cero entrantes, **no omitirse**: en una serie
  temporal, un día sin datos y un día sin actividad son cosas distintas.
- **FR-023**: La reincidencia DEBE agruparse por cliente y servicio. ⚠️ Con el servicio ausente en
  todos los tickets, el informe DEBE **declararlo** y ofrecer el agrupamiento por **tipo de
  incidencia** como alternativa medible.

### Presentación y límites

- **FR-024**: Ninguna respuesta DEBE incluir **el texto de los tickets**: ni asunto, ni descripción,
  ni mensajes del historial, ni **notas internas**. Se cuentan y se clasifican.
- **FR-025**: El agente DEBE identificarse **por su clave**, nunca por su nombre. El informe de
  rendimiento necesita señalar a alguien para ser accionable, y quien deba actuar resuelve la
  identidad en el sistema operativo, donde ese acceso queda auditado.
- **FR-026**: Ninguna respuesta DEBE incluir identidad del cliente más allá de su clave y su tipo.
- **FR-027**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-028**: Un período sin tickets DEBE devolver un resultado vacío explícito.

### Acceso

- **FR-029**: Los informes DEBEN ser de solo lectura.
- **FR-030**: El **Gerente de Éxito del Cliente** —autoridad de Soporte según el §5.1 del SRS— DEBE
  acceder sin acotamiento por titularidad.
- **FR-031**: Un **agente de soporte** DEBE ver los informes **acotados a sus propios tickets**.
- **FR-032**: Un **cliente** NO DEBE acceder a ningún informe de este módulo.
- **FR-033**: La exención de la autoridad NO DEBE alcanzar al dato sensible.

### Ampliaciones del modelo

- **FR-034**: El modelo DEBE incorporar un **hecho de ticket** como instantánea acumulada, con sus
  hitos —creación, primera respuesta, resolución, cierre— y su desenlace de SLA.
- **FR-035**: El modelo DEBE incorporar un **hecho de acción sobre ticket**, con su tipo y su
  instante, **sin mensajes ni notas**.
- **FR-036**: El modelo DEBE incorporar una **dimensión de configuración de SLA versionada**, con su
  vigencia.
- **FR-037**: El modelo DEBE incorporar una **dimensión de servicio** y una de **estado de soporte**.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los 9 informes se obtienen sin que exista ninguna tabla dedicada a un informe.
- **SC-002**: Tras acortar un SLA, el cumplimiento de un ticket **anterior no cambia**.
- **SC-003**: Un ticket abierto **no aporta un tiempo de resolución de cero** a ningún promedio.
- **SC-004**: Un ticket sin SLA **no cuenta como incumplido**, y el informe declara cuántos quedaron
  fuera **en la misma fila** que el cumplimiento.
- **SC-012**: Dejar tickets sin clasificar **sube el cumplimiento y sube el porcentaje sin
  compromiso a la vez**, de modo que el efecto sea visible en la propia cifra.
- **SC-005**: Una reapertura aparece como tal en el rendimiento del agente.
- **SC-006**: El tablero **acepta corte temporal y desglose por agente**; el actual no admite
  ninguno de los dos.
- **SC-007**: El escalado automático y el humano se cuentan por separado.
- **SC-008**: Una serie de carga diaria **incluye los días sin tickets** con cero entrantes.
- **SC-009**: Ningún informe devuelve asunto, descripción, mensajes ni notas internas, **para ningún
  rol**.
- **SC-010**: Un agente solo obtiene datos de sus propios tickets.
- **SC-011**: Añadir estos informes **no altera** ninguna cifra de los seis departamentos anteriores.

---

## Assumptions

- **El modelo analítico está cargado**, las fases 1 y 2 de Emergencias implementadas, y
  **`dim_cliente` y `dim_plan` cargadas por Suscripciones**.
- **El período por defecto** son los últimos 30 días.
- **El umbral de «SLA en riesgo»** por defecto es el **80 % del tiempo comprometido**, parametrizable.
  El sistema no define ninguno.
- **La reincidencia** se considera a partir de **2 tickets** del mismo cliente sobre el mismo eje, en
  el período consultado.
- **El frontend queda fuera de alcance.**

---

## Riesgos ⚠️

### Un informe sin ningún dato, y no es un defecto del informe

**`idservicio` es nulo en los 14 tickets.** El informe «tickets por servicio afectado» devolvería una
sola fila —«sin servicio: 14»— y la reincidencia por servicio no podría calcularse.

`Dim_Servicio` define tres servicios; la operación **no los asigna**. Es el séptimo caso del mismo
patrón en el proyecto, y aquí deja un informe del catálogo **estructuralmente correcto y
materialmente vacío**.

### El indicador BSC dará una cifra alarmante que no significa nada

Con los datos actuales: **8 tickets incumplidos, 1 cumplido**. El cumplimiento saldría en torno al
**11 %** frente a una meta del 95 %.

Sobre 14 tickets, esa cifra **no es un indicador, es una anécdota** — y es exactamente el tipo de
número que, mostrado en un tablero sin contexto, provoca una reacción desproporcionada. FR-012 obliga
a devolver los denominadores por eso.

### El tablero que se sustituye funciona hoy

Lee 100 000 tickets a memoria y no admite corte temporal ni desglose por agente. **Con 14 tickets
reales, ninguno de esos defectos se nota**: son de diseño, no de volumen, y se notarán todos a la vez
cuando el volumen llegue.

---

## Aclaración, resuelta el 2026-08-14

**El cumplimiento se mide solo sobre los tickets con compromiso, y la cobertura se publica al lado**
(FR-011 a FR-014).

Un ticket sin SLA no puede incumplirlo, así que no entra en el denominador. **Lo que neutraliza el
incentivo perverso es FR-013**: la cobertura va **en la misma fila** que el cumplimiento, no en un
endpoint aparte ni en una nota al pie.

Así, un departamento que dejara de clasificar tickets vería subir su cumplimiento **y subir a la vez
el porcentaje sin compromiso, en el mismo sitio**. El juego deja de ser invisible, que es la única
forma de desactivarlo sin acusar a nadie de incumplir un compromiso que nunca existió.

**Y FR-014 separa tres cosas que no son iguales**: pendiente de clasificar es un fallo del proceso;
«sin compromiso declarado» es una decisión; «sin configuración aplicable» es un hueco del catálogo de
SLA. Contarlas juntas escondería cuál hay que arreglar.

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato.
- **[`Emergencias/informes-compuestos-modelo/`](../../Emergencias/informes-compuestos-modelo/)** —
  aporta la plomería.
- **[`Suscripciones-Facturacion/informes-compuestos-modelo/`](../../Suscripciones-Facturacion/informes-compuestos-modelo/)** —
  aporta `dim_cliente` y `dim_plan`, necesarias para el desglose por plan.
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — quién ve qué.
