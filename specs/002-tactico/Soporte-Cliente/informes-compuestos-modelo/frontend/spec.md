# Feature Specification: Informes Compuestos de Soporte al Cliente — Frontend

**Feature Branch / capa**: `002-tactico/Soporte-Cliente/informes-compuestos-modelo/frontend`

**Created**: 2026-08-17

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que Emergencias, Red Operativa, Ventas y
Suscripciones) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

---

## Contexto

El backend de este módulo **ya publica los nueve informes** de OT19 y OT20. No hay vigilados que
omitir: los nueve se pintan. El indicador **BSC de cumplimiento de SLA (meta ≥95 %)** tiene
fuente por primera vez.

Esta capa entrega **tres pantallas nuevas**. No se mezclan con los listados simples, con la cola
del agente, con la configuración de SLA ni con el **tablero operativo de cola** que ya existe:
esos se quedan como están. El tablero operativo sigue sirviendo; esta capa no lo retira. Las
cifras **difieren a propósito** en cuanto se pide un período —el operativo no admite corte— y
las dos pantallas MUST distinguirse para que nadie las compare como si midieran lo mismo.

A diferencia de Suscripciones, **la autoridad no está repartida por materia**. El Gerente de
Éxito del Cliente y el agente de soporte ven **las mismas tres historias**. Lo que cambia es el
alcance: el gerente ve el departamento entero; el agente, **sus** tickets. Una cifra acotada y
una completa se ven idénticas; sin declarar el alcance, los dos leerían la misma pantalla con
números distintos y ninguno sabría por qué.

El ojo recorre el **mismo patrón Z**:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que asigne, escale o
   cierre un ticket. Ver no habilita a decidir.

**No hay fichas de ticket ni de persona.** El backend no entrega asunto, descripción, mensajes
ni notas internas. El visual grande es una distribución o una tendencia. El único desglose por
persona es la **clave del agente** en rendimiento y, si se pide, en el tablero; nunca el nombre.

### La cifra que no se puede mostrar sola

Con los datos actuales el cumplimiento sale en torno al **11 %** frente a una meta del 95 %, y
más de un tercio de los tickets **no tenía compromiso**. Mostrar el 11 % sin la cobertura al
lado provoca una reacción desproporcionada: se lee como un departamento en crisis, cuando lo
que hay es una anécdota de catorce tickets y un proceso que no clasifica. El backend ya
devuelve ambas cifras **en la misma fila**; esta capa MUST pintarlas juntas. Separarlas —un
héroe al 11 % y la cobertura en una nota— es exactamente el incentivo que FR-013 impide.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Cumplimiento de SLA** | ¿Atendemos dentro de lo comprometido? | Cumplimiento **y** % sin compromiso, juntos, con la meta ≥95 % | Cumplimiento por plan | Rendimiento por agente: volumen, tiempo, **reaperturas** | Tickets por servicio |
| **Cola en curso** | ¿Qué pasa ahora y se está rompiendo el plazo? | Tablero de cola **con período** | Evolución del incumplimiento (días vacíos a **cero**, no omitidos) | Escalado automático y humano **por separado** | Agrupar el tablero (estado, prioridad, tipo, agente) |
| **Tendencias** | ¿La cola se acumula y quién repite? | Saldo y acumulado del día | Carga entrante frente a resuelta por día | Reincidencia por **tipo de incidencia**, con el hueco de servicio declarado | — |

Cumplimiento tiene cuatro informes. Si los cuatro salen del mismo tamaño, deja de ser Z y se
vuelve catálogo. Tickets por servicio **MUST** quedar en segundo plano: hoy es una sola fila
«sin servicio». Ponerla a la misma altura que el BSC haría que un hueco operativo se leyera
como el indicador de la empresa.

Cola tiene tres. Agrupar el tablero MUST quedar como opción de esa zona, no como un segundo
filtro global: el período es lo único que refresca las tres zonas.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Gerente de Éxito del Cliente mide el cumplimiento (Priority: P1) 🎯 MVP

El Gerente abre **Cumplimiento de SLA**, elige un período y ve de inmediato el porcentaje
respecto de la meta, **con la cobertura al lado**. El visual grande reparte el mismo par de
cifras por plan. Abajo, qué rinde cada agente: un cierre rápido que se reabre **no** se lee
como resolución. El recuento por servicio se puede ver sin competir con el héroe.

**Why this priority**: es el bloque BSC que hasta ahora no tenía pantalla. Una sola vista basta
para demostrar el patrón Z, el par cumplimiento/cobertura y que el agente se señala por clave.

**Independent Test**: un período donde hay tickets sin SLA **no** puede mostrar un cumplimiento
sin el porcentaje sin compromiso visible en el mismo bloque. Un visitante sin autoridad no
entra. Un agente ve las mismas zonas con el alcance **propios** visible.

**Acceptance Scenarios**:

1. **Given** un Gerente de Éxito del Cliente autenticado, **When** abre Cumplimiento de SLA,
   **Then** ve el patrón Z: métrica a la izquierda, período a la derecha, visual grande en el
   centro, lectura abajo a la derecha.
2. **Given** el cumplimiento, **When** se muestra, **Then** el porcentaje **y** el de tickets
   sin compromiso están **en el mismo bloque**. MUST NOT haber un héroe de cumplimiento solo y
   la cobertura en una nota, un pie o otra pantalla.
3. **Given** un período sin tickets con compromiso, **When** se pide el cumplimiento, **Then**
   se lee **sin dato**, nunca 0 %. Un 0 % dispararía una alarma BSC falsa.
4. **Given** un ticket reabierto, **When** se mira el rendimiento del agente, **Then** cuenta
   como reapertura y **no** como resolución exitosa.
5. **Given** tickets aún abiertos, **When** se muestra un tiempo medio, **Then** **no** aportan
   un cero; se cuenta aparte cuántos no llegaron al hito.
6. **Given** tickets sin servicio, **When** se abre el apoyo por servicio, **Then** aparecen
   como **sin servicio**, con su recuento, y la pantalla **declara** que el catálogo existe y la
   operación no asigna. MUST NOT leerse como un servicio llamado «sin servicio» que funciona
   bien.
7. **Given** un Cliente, un Operador o un Director de Marketing, **When** intenta entrar,
   **Then** no ve la pantalla.

---

### User Story 2 - El Gerente vigila la cola con corte temporal (Priority: P1)

El Gerente abre **Cola en curso**. Arriba a la izquierda, el tablero —estado, prioridad, tipo,
sin asignar, SLA en riesgo— **del período pedido**, no de toda la historia. El visual grande es
cómo evoluciona el incumplimiento: un día sin tickets **aparece en cero**, no desaparece.
Abajo, cuánto escala el sistema solo frente a cuánto escala una persona; las dos columnas
**nunca se suman**.

**Why this priority**: sustituye, en lectura táctica, al tablero que ya existe y no admite
período ni agente. Va al mismo nivel que el BSC porque es lo que el gerente usa **hoy** —mal,
pero lo usa— y hay que dejar de mezclarlo con el operativo.

**Independent Test**: dos períodos distintos cambian el tablero. Un día sin actividad en la
serie no deja un hueco. Automático y humano se leen en columnas distintas. El tablero
operativo **sigue existiendo** y no se confunde con esta pantalla.

**Acceptance Scenarios**:

1. **Given** el Gerente, **When** abre Cola en curso, **Then** el héroe es el tablero, el visual
   grande es la evolución y el escalado está abajo a la derecha.
2. **Given** un período de un mes, **When** se muestra el tablero, **Then** **solo** cuenta ese
   mes. MUST NOT devolver la cola entera «porque el operativo lo hace».
3. **Given** varios agentes con tickets, **When** se pide ver el tablero por agente, **Then** se
   desglosa por **clave**, no por nombre. Los sin asignar **aparecen**.
4. **Given** una serie con un día sin tickets, **When** se muestra la evolución, **Then** ese
   día está en **cero**, no omitido. Un hueco se leería como un buen día.
5. **Given** tickets escalados por el sistema y por una persona, **When** se lee el escalado,
   **Then** hay **dos** recuentos. MUST NOT existir un total «escalados» que los sume.
6. **Given** el tablero operativo que ya existe, **When** el Gerente navega, **Then** esta
   pantalla **no** lo reemplaza en el menú ni reutiliza su disposición. Se distinguen.

---

### User Story 3 - El Gerente anticipa si la cola se forma (Priority: P2)

El Gerente abre **Tendencias**. El héroe es si ese día (o el último del período) la cola creció
o menguó. El visual grande son las dos series diarias —entrantes y resueltos— con saldo y
acumulado; los días sin actividad están en cero. Abajo, qué clientes repiten. El eje es el
**tipo de incidencia**, y junto a esa cifra se declara que **no se puede agrupar por servicio**:
hoy el servicio no está en ningún ticket.

**Why this priority**: permite actuar antes de incumplir, pero con catorce tickets la serie es
corta. La pantalla honesta es esa serie corta, no un tablero que finja volumen.

**Independent Test**: un día con más abiertos que resueltos muestra saldo positivo. Ninguna
zona se titula reincidencia por servicio. Un período sin tickets se lee vacío, no como
acumulado en cero.

**Acceptance Scenarios**:

1. **Given** el Gerente, **When** abre Tendencias, **Then** el héroe es el saldo/acumulado, el
   visual grande es la carga diaria y la reincidencia está abajo a la derecha.
2. **Given** un día con más tickets abiertos que resueltos, **When** se muestra la carga,
   **Then** el saldo es **positivo** y el acumulado crece.
3. **Given** un día sin tickets, **When** aparece la serie, **Then** hay una marca en **cero
   entrantes**, no un salto de línea entre dos días distantes.
4. **Given** un cliente con tres tickets del mismo tipo, **When** se lee la reincidencia,
   **Then** aparece con su recuento, por **clave** y tipo de cliente, nunca por nombre.
5. **Given** la reincidencia, **When** se muestra, **Then** declara que el agrupamiento por
   servicio **no es medible**. MUST NOT haber una columna de servicio, ni vacía: un vacío se
   leería como «nadie repite en el mismo servicio».

---

### User Story 4 - El agente ve lo mismo, acotado, y lo sabe (Priority: P1)

El agente de soporte abre las mismas tres pantallas. El patrón Z no cambia. Las cifras son las
de **sus** tickets, y la pantalla lo dice. Sin esa declaración, él y el gerente discutirían
números distintos creyendo ver el departamento.

**Why this priority**: es el mismo acotamiento por titularidad que Ventas. El permiso demasiado
ancho no produce síntoma; el alcance callado sí. El cliente que abre y sigue **sus** tickets
**no** gana esta lectura de gestión.

**Independent Test**: el agente entra a las tres. Un observador lee en cada una que el alcance
es propios. El gerente lee que ve todos. Un Cliente no entra: esta capa no amplía a quien el
backend no admite.

**Acceptance Scenarios**:

1. **Given** un agente de soporte autenticado, **When** abre cualquiera de las tres, **Then**
   ve el mismo patrón Z que el gerente y el alcance **propios** está visible.
2. **Given** un Gerente de Éxito del Cliente, **When** abre la misma pantalla, **Then** el
   alcance se lee como el departamento entero.
3. **Given** un Administrador, **When** entra, **Then** ve las tres con el acotamiento que ya
   tiene el backend, también declarado.
4. **Given** un Cliente, un Operador o un Director de Marketing, **When** busca estas
   pantallas, **Then** no las ve en su menú y no entra.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no un cumplimiento en 0 %.
- **Cumplimiento sin cobertura.** Prohibido. El par viaja siempre junto.
- **Once por ciento sobre catorce tickets.** La pantalla no oculta los denominadores ni la
  meta; tampoco adorna el número para que parezca un indicador maduro.
- **«Sin servicio».** Una sola fila con todos los tickets. Se declara; no se maquilla como un
  servicio real.
- **Una zona falla y las otras no.** El resto de la pantalla sigue; la zona fallida lo dice.
- **Cifra parcial o convención.** Alcance acotado, cobertura, eje de reincidencia, diferencia
  con el tablero operativo: la pantalla **lo dice junto a la cifra**.
- **Ticket sin agente.** En el tablero aparece como **sin asignar**. En rendimiento, no
  pertenece a nadie.
- **Tres motivos sin compromiso.** Pendiente de clasificar, sin compromiso declarado y sin
  configuración aplicable se leen aparte; juntarlos esconde cuál hay que arreglar.
- **Sin autoridad.** Cliente, Operador y cargos ajenos no entran.
- **Dato sensible.** Ninguna de las tres muestra asunto, descripción, mensajes, notas internas
  ni el nombre del agente o del cliente, **tampoco al Gerente**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Cumplimiento de SLA,
  Cola en curso, Tendencias— y MUST NOT añadir tarjetas a los listados simples, a la cola del
  agente, a la configuración de SLA ni al tablero operativo de cola.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los nueve informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT inventar un décimo ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**: métrica o contexto arriba a la
  izquierda; período arriba a la derecha; visual principal en la diagonal; lectura o
  implicación abajo a la derecha. MUST NOT ser una grilla de tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques** simultáneos del sistema
  de diseño. En Cumplimiento, tickets por servicio MUST quedar en segundo plano. En Cola, el
  agrupamiento del tablero MUST quedar como opción de esa zona, no como filtro global.
- **FR-UI-005**: El período MUST ser la única acción de filtrado de esta capa. Un cambio MUST
  refrescar todas las zonas de la pantalla. MUST NOT inventarse exportación: el backend no la
  ofrece.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de un período con
  ceros reales (backend FR-028).
- **FR-UI-007**: Un denominador ausente MUST verse **sin dato**, nunca como 0 % de cumplimiento
  (backend FR-027).
- **FR-UI-008**: En Cumplimiento de SLA, el porcentaje de cumplimiento y el de tickets **sin
  compromiso** MUST mostrarse **en el mismo bloque**. MUST NOT separar la cobertura a otra
  zona, pie o pantalla (backend FR-012, FR-013, SC-004, SC-012).
- **FR-UI-009**: En Cumplimiento de SLA, los tickets sin compromiso MUST poder leerse por
  **motivo** —pendiente de clasificar, sin compromiso declarado, sin configuración— y MUST NOT
  fundirse en un solo recuento opaco (backend FR-014).
- **FR-UI-010**: En Cumplimiento de SLA, una reapertura MUST verse como tal en el rendimiento
  del agente y MUST NOT inflar las resoluciones (backend FR-016, SC-005).
- **FR-UI-011**: En Cumplimiento de SLA, un tiempo de ticket abierto MUST NOT pintarse como
  cero. Los excluidos del promedio MUST contarse a la vista (backend FR-009, FR-010, SC-003).
- **FR-UI-012**: En Cumplimiento de SLA, los tickets sin servicio MUST agruparse como **sin
  servicio**, con recuento visible y con la declaración de que la operación no asigna
  servicio. MUST NOT omitirse la fila ni titularse como un servicio del catálogo.
- **FR-UI-013**: En Cola en curso, el tablero MUST aplicar el período pedido. MUST NOT
  presentar la cola histórica como si fuera el corte (backend FR-017, SC-006).
- **FR-UI-014**: En Cola en curso, el tablero MUST poder desglosarse por agente, por **clave**,
  y los tickets sin asignar MUST aparecer (backend FR-018, FR-020).
- **FR-UI-015**: En Cola en curso, un día sin tickets en la evolución MUST mostrarse en **cero**,
  no omitirse (backend FR-022).
- **FR-UI-016**: En Cola en curso, escalado automático y humano MUST mostrarse **por separado**.
  MUST NOT existir un total que los sume (backend FR-019, SC-007).
- **FR-UI-017**: En Tendencias, la carga MUST mostrar entrantes, resueltos, saldo y acumulado
  por día, con los días sin actividad en cero (backend FR-021, FR-022, SC-008).
- **FR-UI-018**: En Tendencias, la reincidencia MUST agruparse por cliente (clave y tipo) y
  tipo de incidencia. MUST declarar que el eje por servicio no es medible, y MUST NOT mostrar
  una columna de servicio, ni vacía (backend FR-023).
- **FR-UI-019**: Las tres pantallas MUST NOT mostrar asunto, descripción, mensajes ni notas
  internas, para ningún rol (backend FR-024, SC-009).
- **FR-UI-020**: El desglose por persona MUST ser por **clave de agente** o **clave de
  cliente**. MUST NOT mostrarse el nombre (backend FR-025, FR-026).
- **FR-UI-021**: Las tres pantallas MUST NOT dibujar mapas ni pedir posiciones.
- **FR-UI-022**: Las tres pantallas MUST ser visibles y accesibles para el **Gerente de Éxito
  del Cliente** (sin acotamiento de titularidad), el **agente de soporte** (acotado a sus
  tickets) y el **Administrador** (con el acotamiento que ya tiene el backend). Cliente,
  Operador y cargos ajenos MUST NOT verlas en el menú ni entrar (backend FR-030, FR-031,
  FR-032).
- **FR-UI-023**: Cuando el alcance no es el departamento entero, cada pantalla MUST declarar
  **acotado a propios** (o el valor que el backend ya envía) junto al período. MUST NOT dejar
  que gerente y agente vean la misma disposición con cifras distintas y sin etiqueta.
- **FR-UI-024**: Ver un informe MUST NOT habilitar asignar, escalar, responder, cerrar ni
  cualquier acción sobre un ticket. No hay llamada a la acción de negocio en la esquina
  inferior derecha: hay **lectura**.
- **FR-UI-025**: Si el backend declara cobertura, motivo sin compromiso, alcance, eje de
  reincidencia o que el período hace diferir las cifras del tablero operativo, la pantalla
  MUST mostrarlo junto a la cifra. MUST NOT silenciarlo.
- **FR-UI-026**: MUST NOT existir un enlace que fusione estas tres historias con el tablero
  operativo ni con los listados simples. Son lecturas distintas; mezclarlas anula el corte
  temporal y vuelve a mostrar texto de ticket.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Gerente de Éxito del Cliente identifica el cumplimiento **y** la cobertura de
  Cumplimiento de SLA en **menos de 5 segundos** sin leer un párrafo.
- **SC-F02**: No existe un estado de pantalla en el que se vea el cumplimiento y no se vea, en
  el mismo bloque, el porcentaje sin compromiso.
- **SC-F03**: Un período sin tickets con compromiso no se lee como 0 % de cumplimiento.
- **SC-F04**: Una reapertura no aumenta las resoluciones visibles del agente.
- **SC-F05**: Un ticket abierto no aporta un tiempo de resolución de cero a ningún promedio
  visible.
- **SC-F06**: Dos períodos distintos cambian el tablero de Cola en curso; no se parece al
  tablero operativo que ignora el corte.
- **SC-F07**: En la evolución, un día sin tickets está presente en cero; no hay un hueco que se
  lea como buen día.
- **SC-F08**: Automático y humano no se suman en ninguna zona de escalado.
- **SC-F09**: Un agente ve las tres pantallas con el alcance propios visible. Un Cliente y un
  Operador **no** acceden a ninguna.
- **SC-F10**: En ninguna de las tres aparecen asunto, mensajes, notas, nombre de agente, nombre
  de cliente ni mapas.
- **SC-F11**: Un período sin datos no se parece a un período con ceros.
- **SC-F12**: Las tres pantallas se distinguen de los listados simples y del tablero operativo:
  no reutilizan su disposición ni les añaden tarjetas.
- **SC-F13**: La reincidencia no se lee como agrupada por servicio: no hay columna de
  servicio, y la declaración del eje está visible.
- **SC-F14**: Cumplimiento de SLA no presenta cuatro bloques del mismo peso; un recuento de la
  vista principal queda en **8 o menos**.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni el tablero operativo.
- **Zona Z**: métrica, período, visual grande, lectura. Cuatro zonas, no nueve tarjetas.
- **Período**: el único filtro; por defecto los últimos 30 días.
- **Alcance**: todos o propios; viaja visible junto al período cuando no es el departamento
  entero.
- **Par cumplimiento/cobertura**: las dos cifras que MUST viajar juntas; no son dos widgets.
- **Lectura**: el texto o bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los nueve publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días, como asume el backend.
- El Gerente de Éxito del Cliente ve el departamento entero; el agente y el Administrador
  entran acotados, como ya decide el backend.
- El Cliente sigue viendo y abriendo **sus** tickets en los flujos operativos; no gana estas
  lecturas de gestión.
- El patrón Z ya está demostrado; esta capa lo copia, no lo reinventa. Lo que no se copia es
  el acotamiento por titularidad, que aquí sí existe —igual que en Ventas.
- Los listados simples, la cola del agente, la configuración de SLA y el tablero operativo no
  se tocan ni se retiran.
- No hay exportación ni programación de envío en esta pasada.
- Las cifras de hoy salen de **catorce tickets**: son correctas y no representativas. La
  pantalla no inventa volumen; muestra lo que hay y enseña los denominadores.
- El umbral de «SLA en riesgo» lo resuelve el backend (80 % del compromiso, salvo que ya envíe
  otro). Esta capa no ofrece un control extra de umbral.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Listados simples, cola del agente, configuración de SLA | Ya existen; no se les añaden tarjetas |
| Retirar el tablero operativo de cola | Sigue sirviendo; la retirada no es de esta capa |
| Un tablero único de nueve iguales | Rompe el patrón Z y la Ley de Hick |
| Asunto, mensajes, notas e identidad de persona | Exclusión constitucional; el backend no las entrega |
| Acciones operativas (asignar, responder, escalar, cerrar) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Inventar el agrupamiento por servicio | El origen no asigna servicio |
| Cliente, Operador, cargos ajenos | No son la autoridad de estos compuestos |
| Cambiar OpenAPI, consultas o permisos del backend | Depends-on |
| Frontend de Emergencias, Red, Ventas, Suscripciones u otros | Mismo patrón, otro módulo |
| Informes estratégicos | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período único, par cumplimiento/cobertura inseparable, alcance visible. SC-F01, SC-F02. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (cobertura al lado, reapertura no es resolución, abierto no es tiempo cero, vacío ≠ ceros, automático ≠ humano). No inventa métricas. |
| **Security** | Reutiliza quién entra (Gerente / agente / Administrador). Exclusión constitucional de texto de ticket e identidad también en pantalla. Alcance declarado para no filtrar a ojo. |
| **Safety** | Un 11 % sin cobertura, o un 0 % donde no hubo compromiso, se lee mal al decidir plantilla o SLA; FR-UI-008 y FR-UI-007 lo impiden. No hay cadena de despacho: Safety se limita a no inducir una decisión de soporte falsa. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas copian el patrón Z ya usado. |
| **Performance Efficiency** | Heredada del backend. La pantalla no recalcula. Umbral de esta capa: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio con sistemas externos en esta capa. |
| **Flexibility** | No aplica: no se agrupa por región; el servicio llega ausente y se declara. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
