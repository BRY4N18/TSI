# Research — Informes Compuestos de Soporte al Cliente

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Ocho decisiones. Las cifras están **medidas contra el sistema real**.

---

## D1 — El SLA versionado se respeta, no se reconstruye ⚠️

**Hallazgo.** `Dim_SLAConfig` tiene `fechavigenciadesde` y `fechavigenciahasta`, y contiene **dos
configuraciones para la misma combinación** (plan 1, prioridad alta, incidencia técnica):

| Config | Vigencia | Tiempo de resolución |
|---|---|---|
| `idslaconfig = 1` | cerrada | **86 400 s** (24 h) |
| `idslaconfig = 6` | abierta desde ese mismo instante | **7 200 s** (2 h) |

**Es el primer historial correcto del proyecto.** Seis departamentos antes, el sistema guardaba el
estado actual y nunca cuándo cambió — de ahí que hubiera que versionar la unidad y la región, y
declarar que su historia empezaba en la primera carga.

**Decisión.** La dimensión se carga **con sus vigencias tal como vienen**, y el cumplimiento se mide
contra la configuración **vigente cuando ocurrió el ticket**.

**Rationale.** Aplicar `versionado.py` aquí sería un error, no una redundancia: ese módulo
**construye** historia comparando el estado actual con el vigente en el modelo, y marca lo construido
con `inicio_es_real = 0`. Usarlo produciría versiones **declaradas como no reales cuando sí lo son**,
que es exactamente la mentira que esa marca existe para evitar — en la dirección contraria.

**Y respetarlo importa.** Ese SLA se acortó de 24 horas a 2. Un ticket resuelto en 5 horas **antes**
del cambio cumplía; medido contra la configuración actual, **incumple**. Sin la vigencia, acortar un
SLA reescribiría el pasado y haría caer el indicador BSC sin que nadie hubiera hecho nada peor.

---

## D2 — Los tiempos valen cero mientras no hay hito ⚠️

**Hallazgo.** `sla_primera_respuesta`, `sla_resolucion` y `tiempo_solucion` valen **`0`** en los
tickets abiertos. No es que se respondiera al instante: es que aún no se respondió.

**Decisión.** Los tres se traducen a **ausente** cuando el ticket no alcanzó ese hito, y los
promedios los excluyen contándolos aparte.

**Rationale.** Es el mismo patrón de los hitos de accidente y despacho, y el mismo error potencial:
un promedio de tiempo de primera respuesta que incluya los ceros de los tickets abiertos **dice que
se responde casi al instante**, y mejora cuanto más tickets sin atender haya.

Con 14 tickets y varios abiertos, ese sesgo sería inmediato y grande.

---

## D3 — El denominador del cumplimiento, y su cobertura al lado ⚠️

**Hallazgo.** De 14 tickets, **solo 8 tienen SLA asignado**: tres están `Pendiente_de_clasificacion`,
uno declara «sin compromiso» y dos no tienen configuración aplicable.

**Decisión (del usuario, 2026-08-14).** El cumplimiento se mide **solo sobre los tickets con
compromiso**, y el porcentaje **sin compromiso se publica en la misma fila**.

**Rationale.** Un ticket sin SLA no puede incumplirlo: contarlo como incumplimiento sería acusar de
romper una promesa que nadie hizo. Pero excluirlo sin más **premia dejar tickets sin clasificar** —
un departamento que dejara de clasificar llegaría al 100 % de cumplimiento.

**La cobertura en la misma fila es lo que desactiva el juego.** No lo elimina: quien deje de
clasificar **seguirá** viendo subir su cumplimiento. Lo que cambia es que verá subir **a la vez** el
porcentaje sin compromiso, en el mismo sitio y ante los mismos ojos. **Un incentivo visible deja de
ser un incentivo.**

**Alternativa descartada.** *Publicar la cobertura en un endpoint aparte* — nadie compara dos
pantallas, y un tablero mostraría el 100 % sin el contexto que lo desmiente.

**Y los motivos se separan** (FR-014): pendiente de clasificar es un fallo del proceso; «sin
compromiso» es una decisión; «sin configuración aplicable» es un hueco del catálogo de SLA. Sumarlos
escondería cuál hay que arreglar.

---

## D4 — El ticket es una instantánea acumulada

**Hallazgo.** Un ticket avanza por hitos —creación, primera respuesta, resolución, cierre
confirmado— y su estado cambia sin dejar de ser el mismo ticket. Hay 7 estados en el catálogo y 34
acciones registradas para 14 tickets.

**Decisión.** `hecho_ticket` es una **instantánea acumulada** —una fila por ticket, una columna por
hito—, y `hecho_accion_ticket` es de transacción.

**Rationale.** Es el cuarto hecho acumulado del modelo, y aquí el argumento es el más visible de
todos: **el tablero actual reconstruye el estado de cada ticket en memoria**, y por eso lee 100 000
filas. Con una fila por ticket y sus hitos en columnas, el estado de la cola es un `GROUP BY`.

⚠️ **Sus consultas deben forzar la versión final.** Un ticket actualizado aparecería dos veces y la
cola saldría inflada de forma intermitente.

---

## D5 — Ni texto de ticket, ni mensajes, ni notas internas ⚠️

**Hallazgo.** `Fact_Reclamo` guarda `asunto` y `descripcion` —escritos por el cliente— y
`Fact_Historial_Ticket` guarda `mensaje` y **`es_nota_interna`**.

**Decisión.** **Nada de eso entra al modelo.** Se cuentan las acciones y se clasifican por tipo.

**Rationale.** Las notas internas son el caso más claro: son **comentarios del equipo sobre el
cliente**, escritos con la expectativa de que el cliente no los lea. Llevarlas a un almacén analítico
—consultable por cualquier informe futuro, incluido en copias de seguridad— es exactamente el tipo de
filtración que ocurre sin que nadie lo decida.

Y ningún informe del catálogo los necesita: todos cuentan, agrupan o miden tiempos.

**Es la séptima vez** que esta exclusión aparece en la serie, y la séptima con la misma resolución.

---

## D6 — El agente se identifica por su clave

**Hallazgo.** El informe de rendimiento por agente **necesita señalar a alguien**: «el equipo resolvió
X tickets» no permite gestionar un equipo.

**Decisión.** Se identifica por **la clave del agente**, nunca por su nombre.

**Rationale.** Es la misma solución que en Cuentas y Clientes con los roles incompatibles, y por la
misma razón: hay informes cuyo objeto **es** una persona, y agregarlos los vacía de utilidad.

La clave identifica sin exponer, y quien deba actuar resuelve el nombre en el sistema operativo,
**donde ese acceso queda auditado**.

⚠️ **Con una diferencia que conviene decir.** Este informe **evalúa el desempeño de una persona**, y
eso lo hace más delicado que detectar un riesgo de segregación de funciones. La clave no es una
protección técnica frente a quien tenga acceso al sistema operativo: es una barrera **deliberada**
para que consultar el nombre sea un acto explícito y registrado, no un efecto secundario de abrir un
tablero.

---

## D7 — El informe por servicio se entrega, aunque hoy salga vacío ⚠️

**Hallazgo.** **`idservicio` es nulo en los 14 tickets**, pese a que `Dim_Servicio` define tres
servicios.

**Decisión.** El informe **se construye**, devuelve «sin servicio» con su recuento, y **declara** que
la asignación de servicio no se está registrando.

**Rationale.** Es un informe correcto sobre un dato que la operación no rellena. Las alternativas
son peores:

- **Retirarlo del alcance** dejaría el hueco invisible: nadie sabría que falta hasta que alguien
  preguntara por qué no hay informe.
- **Inferir el servicio** del tipo de incidencia sería inventar una clasificación que nadie hizo.

Entregándolo vacío y declarado, **el informe es la evidencia del hueco**: cada vez que alguien lo
abra verá que 14 de 14 tickets no tienen servicio, y eso es más elocuente que una nota en un
documento.

**Consecuencia sobre la reincidencia.** El informe de clientes que repiten **tampoco puede agrupar
por servicio**, así que ofrece el **tipo de incidencia** como eje alternativo y lo declara.

---

## D8 — El tablero actual sigue sirviendo, y sus cifras diferirán

**Hallazgo.** El tablero de cola existe, con dos defectos: lee 100 000 tickets a memoria y **no admite
corte temporal ni desglose por agente**.

**Decisión.** Este módulo entrega su equivalente corregido y **deja el original sirviendo**.

**Rationale.** Es la misma situación de Emergencias y Partners: retirarlo depende de la decisión
pendiente #20, y apagarlo aquí dejaría la cola sin tablero mientras tanto.

⚠️ **Y sus cifras diferirán a propósito**, en cuanto se pida un período: el actual devuelve **toda**
la cola, el nuevo solo el período pedido. Quien los compare sin contexto pensará que faltan tickets.

**Con 14 tickets, ninguno de los dos defectos se nota.** Son de diseño, no de volumen, y **se
notarán todos a la vez** el día que la cola crezca — que es precisamente cuando un tablero importa.
