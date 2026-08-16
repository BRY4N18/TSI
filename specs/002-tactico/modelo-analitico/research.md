# Research — Modelo Analítico Táctico

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones cerradas leyendo el esquema del origen, los flujos de carga existentes y el
catálogo de informes. Dos de ellas —D1 y D2— condicionan el resto.

---

## D1 — El grano del hecho de despacho: un intento, no un caso ⚠️

**La decisión más condicionante del modelo.** Hay tres candidatos:

| Candidato | Una fila por | Qué permite | Qué rompe |
|---|---|---|---|
| **Caso** | Accidente | Contar casos atendidos | **Pierde los intentos**: un caso con cuatro reasignaciones se vería como uno |
| **Intento** ✅ | Cada notificación de despacho a una unidad | Rechazos, vencimientos, reasignaciones, carga por unidad | Contar «casos despachados» exige distinguir |
| **Unidad-caso** | Cada par unidad↔caso | Apoyo múltiple | Colapsa reintentos sobre la misma unidad |

**Decisión: un intento de asignación.**

**Rationale.** El catálogo lo obliga. Estos informes **no son posibles** con grano de caso:

- *Asignación automática frente a manual* — necesita el origen de **cada** intento.
- *Rechazo y vencimiento por unidad* — un rechazo **es** un intento fallido; sin esa fila no existe.
- *Despachos resueltos al primer intento* (KPI del tablero, meta ≥90%) — es literalmente un recuento
  de intentos por caso.
- *Carga por unidad* — una unidad que rechaza tres veces no soportó carga; con grano de caso
  parecería que sí.

Y la revisión del sistema ya dejó constancia de que el caso de prueba **acumuló seis intentos de
cuatro orígenes distintos**. Un grano que los colapse pierde exactamente lo que ese caso demuestra.

**Consecuencia que hay que aceptar.** «Cuántos casos se despacharon» deja de ser un recuento de
filas: es un recuento de casos distintos. Se documenta en el contrato de consumo para que ningún
informe cuente filas creyendo que cuenta casos.

**Alternativa descartada.** *Dos hechos, uno por caso y otro por intento* — duplicaría la carga y
crearía dos fuentes para la misma pregunta, que es justo lo que este modelo existe para evitar.

---

## D2 — El histórico versionado: qué se puede reconstruir y qué no ⚠️

**El origen tiene siete tablas de historial**, pero no historizan lo mismo:

| Dimensión a versionar | ¿Reconstruible desde el origen? | Desde dónde |
|---|---|---|
| **Unidad → proveedor** | ❌ **No** | **Nada lo historiza.** Es el hueco ya documentado |
| Partner → plan de acceso | ✅ Sí | Bitácora de acceso, cambios de tipo «asignación de plan» |
| Región → estado | ✅ Sí | Intentos de validación y estados de región |
| Cliente → plan | ⚠️ Parcial | Solicitudes de cambio **aprobadas**, con su fecha de resolución |
| Cliente → estado | ⚠️ Parcial | Solo transferencias de propiedad; el estado en sí no se historiza |

**Decisión.** Se reconstruye lo reconstruible, y **cada versión declara si su fecha de inicio es real
o si solo significa «desde la primera carga»**.

**Rationale.** Sin esa marca, el modelo cometería el error que esta revisión lleva persiguiendo toda
la sesión: presentar «no lo sabemos» como «siempre fue así». Un informe que agrupe despachos de hace
seis meses por proveedor, con un versionado que empieza hoy, devolvería el proveedor actual para todo
ese período **y parecería correcto**.

Con la marca, el informe puede decir «desde esta fecha la atribución es exacta; antes es el estado
conocido al arrancar», que es honesto y sigue siendo útil.

**Consecuencia sobre el caso ancla.** La atribución unidad↔proveedor **empieza el día de la primera
carga**. No hay forma de saber a qué proveedor pertenecía una unidad hace seis meses: el dato nunca
se guardó. El modelo no arregla el pasado; **impide que se siga rompiendo** desde hoy.

**Alternativa descartada.** *Inferir el proveedor histórico desde otra señal* — no hay ninguna
fiable, y una inferencia aquí produce exactamente el tipo de cifra plausible y equivocada que
justifica todo este trabajo.

---

## D3 — Idempotencia de carga: particiones, no borrados

**Hallazgo.** Los flujos actuales **sí son idempotentes**, y lo consiguen borrando antes de insertar:
`ALTER TABLE … DELETE WHERE periodo IN (…)` seguido del `INSERT`.

**El problema es cómo escala.** En el almacén elegido, ese borrado es una **mutación**: una operación
asíncrona y pesada que reescribe partes enteras de la tabla. Con tres informes y una corrida diaria
se tolera. Con **13 hechos** cargándose con regularidad, las mutaciones se acumulan y compiten entre
sí.

**Decisión.** Los hechos se **particionan por período** —mes—, y la recarga **descarta y repuebla la
partición** en lugar de borrar filas por condición.

**Rationale.** Descartar una partición es una operación de metadatos: instantánea y sin reescritura.
Es el mecanismo idiomático del almacén para exactamente este caso —recargar un período— y convierte
la idempotencia en una propiedad de la estructura en vez de en una operación costosa que hay que
recordar hacer bien.

**Alternativa descartada.** *Motor con deduplicación por clave* — resuelve duplicados, pero la
deduplicación ocurre en segundo plano y **una consulta puede leer ambas versiones mientras tanto**.
Para hechos de transacción eso es inaceptable: un informe daría cifras infladas de forma
intermitente.

**Excepción.** Los hechos de **instantánea acumulada** —caso y despacho— sí necesitan actualizar
filas existentes cuando el proceso avanza. Para ellos se usa un motor con deduplicación por clave,
**y las consultas deben forzar la versión final**. Se documenta como regla de consumo, porque es la
trampa clásica de ese motor.

---

## D4 — Qué se copia en el hecho y qué se deja en la dimensión

**Decisión.** Cada hecho copia los atributos por los que **casi siempre** se filtra o agrupa, y deja
en la dimensión los que se consultan ocasionalmente o cambian con el tiempo.

| Se copia en el hecho | Se deja en la dimensión |
|---|---|
| Fecha, mes, día de la semana, franja horaria | El resto del calendario |
| Nombre de severidad | Descripción y orden |
| Condado y ciudad | Calle, país, coordenadas del catálogo |
| Nombre de la unidad y su proveedor **al momento del hecho** | Placa, capacidad, tipo, zona de cobertura |
| Tipo de cliente y nivel de plan | Razón social, contacto, límites |

**Rationale.** El almacén es columnar: leer tres columnas más de una tabla ancha cuesta casi nada,
mientras que unir con una dimensión obliga a materializar la tabla pequeña y cruzarla. Con las
agrupaciones más frecuentes ya en el hecho, la mayoría de los informes del catálogo **no une con
nada**.

**Y lo que NO se copia** es igual de importante: los atributos versionados se copian **con su valor
al momento del hecho**, no como referencia mutable. Copiar «el proveedor actual» reintroduciría el
defecto que D2 resuelve.

---

## D5 — Caso y despacho son instantáneas acumuladas

**Hallazgo.** Ambos son procesos con hitos, no sucesos puntuales:

| Proceso | Hitos |
|---|---|
| **Caso** | Registrado → confirmado → asignado → llegada → cierre |
| **Despacho** | Notificado → confirmado o rechazado → llegada → retiro |

**Decisión.** Una fila por caso y una por intento, **con una columna por hito**, actualizada a medida
que el proceso avanza.

**Rationale.** Convierte media docena de informes de tiempos en **restas dentro de una misma fila**:
tiempo de reportado a confirmado, de asignado a cerrado, de tránsito, de atención. Con hechos de
transacción, cada uno de esos tiempos exigiría emparejar dos filas y ordenar — más caro y más fácil
de equivocar.

Además hace trivial el envejecimiento de la cartera: un hito ausente **es** el caso abierto.

**Regla que se hereda de la spec.** Un hito no alcanzado se guarda **ausente**, nunca como cero ni
como la fecha de carga. Un cierre con fecha de carga convertiría todos los casos abiertos en cerrados
el día que se cargaron.

---

## D6 — Qué se construye en la primera fase

**Decisión.** Los hechos de **accidente** y **despacho**, con sus dimensiones: tiempo, geografía,
severidad, unidad (versionada) y origen de despacho.

**Rationale.** Tres razones se acumulan:

1. **Sustituyen a lo que ya existe.** Los tres informes con tabla propia se recalculan desde estos
   dos hechos, así que la primera fase **cierra** el diseño viejo en vez de convivir con él.
2. **Cubren la mayor parte de lo ya especificado.** Los compuestos de OT21, OT22, OT23 y OT25 salen
   de aquí.
3. **Contienen el caso ancla.** La atribución unidad↔proveedor versionada es el defecto que
   justificó el modelo; construirla primero es probar la tesis, no aplazarla.

**Lo que espera.** Ticket, facturación, suscripción mensual, embudo, demo, consumo de API,
incorporación, acceso de partner, validación de región y estado de unidad. Se añaden sin rehacer
nada, que es lo que FR-017 exige.

---

## D7 — Las tres tablas actuales se retiran, sus flujos no del todo

**Decisión.** Las tres tablas por informe y sus tres flujos **se retiran cuando el modelo las cubra**,
no antes. Lo que se conserva:

| Se conserva | Por qué |
|---|---|
| El patrón de carga por ficheros intermedios | Está fijado por la spec de infraestructura y es independiente del modelo |
| Los clientes de origen y destino, y la escritura de ficheros | Independientes del diseño |
| La lógica de detección de huecos de señal | Es una función pura y probada; pasa a alimentar un hecho en vez de una tabla propia |
| El flujo de referencia y el de recarga histórica | Ejemplos del patrón, no informes |

**Rationale.** El diseño de tabla-por-informe se sustituye; el trabajo de tubería, no. En particular
la lógica de huecos de señal recorre pings ordenados y emite huecos: eso sigue siendo necesario, solo
que su resultado pasa a ser una columna de un hecho en lugar de una tabla suya.

**Orden.** Retirar antes de que el modelo cubra esos tres informes dejaría al sistema sin ellos. Se
retiran en la fase en que sus consultas equivalentes estén verificadas.
