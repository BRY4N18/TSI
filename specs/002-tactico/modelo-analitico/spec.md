# Feature Specification: Modelo Analítico Táctico (esquema en estrella)

**Feature Branch**: `modelo-analitico`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Definir el modelo analítico sobre el que vivirán los informes tácticos compuestos — esquema en estrella, diseñado mirando el catálogo completo, aceptando que se corregirá al avanzar por los departamentos."

---

## Contexto

Este módulo **no es un informe**: es la base de datos analítica de la que todos los informes
compuestos se sirven. Se sitúa entre la infraestructura —que define los contenedores— y los
informes —que consumen el dato—.

| Módulo | Define |
|---|---|
| `infraestructura/` | Los contenedores y el patrón de carga por ficheros intermedios |
| **`modelo-analitico/`** | **Qué vive dentro del almacén analítico: hechos, dimensiones y granos** |
| `<Departamento>/informes-*` | Los informes que lo consumen |

**Documentos que gobiernan esta spec:**

- `informestacticos/TSI-Marco-Estrategico-y-Casos-de-Uso_3.md` §15.2, que describe el modelo
  Fact-Dim como la capa de la que se sirven reportes, tableros e inteligencia.
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` — los **~105 informes compuestos**
  del catálogo, que son los consumidores de este modelo.
- `specs/002-tactico/infraestructura/spec.md` — el patrón de carga, que **no cambia**.
- `specs/002-tactico/contrato-informes-simples.md` — el contrato hermano, para los listados.

---

## Por qué hace falta este modelo

### Lo construido no escala

Hoy existen tres informes compuestos, y **cada uno tiene su propia tabla**, cuyas columnas son
exactamente sus métricas: un almacén de resultados precalculados, uno por informe.

Con tres informes funciona. **Con ~105 significaría ~105 tablas y ~105 flujos de carga**, cada uno
releyendo la fuente por su cuenta y recalculando las mismas agregaciones base una y otra vez. El
coste no es solo de cómputo: dos informes que midan «casos por severidad» desde tablas distintas
**pueden dar cifras distintas**, y nadie sabría cuál creer.

### Y hay un defecto real que solo un modelo dimensional resuelve

El informe de rendimiento por proveedor tiene una limitación **ya documentada en su propio código**:

> *«`Dim_UnidadEmergencia` no historiza cambios de proveedor, así que el flujo usa el proveedor
> **actual** de la unidad para todos los períodos, no el vigente en el momento histórico de cada
> despacho. Resolverlo requeriría una tabla de historial de asignación unidad↔proveedor que no
> existe.»*

**Consecuencia:** si una unidad cambia de proveedor, **todos sus despachos pasados se reatribuyen al
proveedor nuevo**. El informe no falla: reescribe la historia en silencio, y un proveedor puede
aparecer respondiendo por despachos que nunca atendió.

**Esto es exactamente lo que un modelo dimensional resuelve**, y por un mecanismo estándar: la
dimensión guarda **versiones** de cada entidad con su vigencia, y el hecho apunta a la versión que
estaba vigente cuando ocurrió. El sistema operativo no historiza porque no lo necesita —le importa
el ahora—; el analítico sí, porque su oficio es el pasado.

**No hace falta cambiar el sistema operativo**: el modelo analítico puede construir esa historia
observando cómo cambia la fuente en cada carga.

---

## Nota de diseño: por qué estrella, y con qué matices

### Por qué estrella y no una tabla ancha por informe

Un esquema en estrella —hechos rodeados de dimensiones compartidas— da tres cosas que el diseño
actual no puede dar:

1. **Una sola definición de cada cosa.** «Severidad», «condado» o «plan» significan lo mismo en todos
   los informes porque salen de la misma dimensión. Hoy cada tabla los redefine.
2. **Informes nuevos sin carga nueva.** Una pregunta que combine hechos y dimensiones existentes se
   responde con una consulta, no con un flujo de carga nuevo.
3. **Historia correcta**, mediante versionado de dimensiones (arriba).

### El matiz: el almacén analítico no premia las uniones

El almacén elegido está orientado a columnas y **rinde mucho mejor leyendo una tabla ancha que
uniendo muchas estrechas**. Un esquema en estrella de manual, con toda unión resuelta en consulta,
rendiría peor aquí que en un almacén relacional clásico.

**Decisión:** estrella en el **diseño lógico** —hechos, dimensiones, granos y claves explícitos— con
**desnormalización selectiva** en el físico: cada hecho lleva copiados los pocos atributos de
dimensión por los que casi siempre se filtra o agrupa.

**Rationale.** Se conserva lo que importa del modelo dimensional —una definición por concepto, grano
explícito, historia versionada— y se paga en espacio, que es lo barato, en lugar de en tiempo de
consulta, que es lo que el usuario nota. Es la práctica habitual en almacenes columnares, no un
atajo.

**Lo que NO se desnormaliza:** los atributos que cambian con el tiempo y que un informe puede querer
ver en su versión actual **y** en la histórica. Esos se resuelven contra la dimensión versionada.

### Los tres tipos de hecho, y por qué importan aquí

No todos los hechos son iguales, y tratarlos como si lo fueran es la causa más común de un informe
que miente:

| Tipo | Qué guarda | Ejemplo en TSI |
|---|---|---|
| **Transacción** | Un suceso, inmutable | Una llamada a la API, una transición del embudo |
| **Instantánea periódica** | El estado de algo al cierre de cada período | Una suscripción al cierre de cada mes |
| **Instantánea acumulada** | Un proceso con hitos, que se actualiza al avanzar | Un caso: registrado → asignado → llegada → cierre |

**El caso de emergencia es una instantánea acumulada**, y reconocerlo resuelve de golpe media docena
de informes de tiempos: los hitos viven en columnas de la misma fila, así que «tiempo de reportado a
confirmado» o «de asignado a cerrado» son restas, no uniones.

**El MRR necesita instantánea periódica.** Un ingreso recurrente no es un suceso: es un estado que se
repite cada mes. Intentar calcularlo desde los sucesos de facturación es la vía por la que los
ingresos recurrentes se cuentan mal.

---

## User Scenarios & Testing *(mandatory)*

Los usuarios de este modelo **son los informes**, no las personas.

### User Story 1 - Un informe responde su pregunta sin recalcular nada (Priority: P1)

Como informe compuesto, necesito obtener mis cifras combinando un hecho con sus dimensiones, sin
recorrer el sistema operativo ni recalcular agregaciones que otro informe ya calculó.

**Why this priority**: Es la razón de ser del modelo. Si un informe sigue necesitando su propio flujo
de carga, el modelo no ha resuelto nada y volvemos a una tabla por informe.

**Independent Test**: Se puede tomar un informe del catálogo, escribir su consulta contra el modelo y
comprobar que devuelve la cifra correcta, sin tocar la fuente operativa ni crear tabla alguna.

**Acceptance Scenarios**:

1. **Given** el modelo con el hecho de accidentes y sus dimensiones, **When** un informe pide casos
   por severidad y por mes, **Then** obtiene la cifra con una sola consulta y **sin ningún flujo de
   carga propio**.
2. **Given** dos informes distintos que miden casos por zona, **When** ambos consultan el modelo,
   **Then** obtienen **la misma cifra**, porque leen la misma dimensión geográfica.
3. **Given** un informe que combina el hecho de despachos con la dimensión de unidad, **When**
   agrupa por proveedor, **Then** no necesita conocer cómo se relaciona una unidad con su proveedor:
   la dimensión ya lo resuelve.
4. **Given** una pregunta nueva que combina un hecho y una dimensión ya existentes, **When** se
   formula, **Then** se responde **sin construir nada**.

---

### User Story 2 - Un informe histórico ve el pasado como fue, no como es hoy (Priority: P1)

Como informe que mide períodos pasados, necesito que los atributos de las entidades sean **los que
estaban vigentes cuando ocurrió el hecho**, no los actuales.

**Why this priority**: Es el defecto real que arrastra el informe de rendimiento por proveedor, y
tiene la misma prioridad que la historia anterior porque un modelo que no lo resuelva **produce
cifras equivocadas sin avisar** — que es peor que no tenerlas.

**Independent Test**: Se puede cambiar el proveedor de una unidad, recargar el modelo y comprobar que
los despachos anteriores siguen atribuidos al proveedor anterior.

**Acceptance Scenarios**:

1. **Given** una unidad que cambió de proveedor, **When** un informe agrupa despachos pasados por
   proveedor, **Then** cada despacho cuenta para el proveedor que la unidad tenía **en el momento del
   despacho**.
2. **Given** un cliente que cambió de plan, **When** un informe mide ingresos por plan de un mes
   anterior, **Then** usa el plan vigente en ese mes.
3. **Given** una entidad que nunca ha cambiado, **When** se consulta cualquier período, **Then** el
   resultado es el mismo que si no hubiera versionado: el mecanismo no penaliza el caso simple.
4. **Given** un informe que quiere agrupar por el estado **actual** de una entidad, **When** lo pide,
   **Then** puede hacerlo: el modelo permite **ambas** lecturas, la histórica y la vigente.

---

### User Story 3 - El modelo crece sin rehacer lo construido (Priority: P2)

Como responsable de añadir el siguiente departamento, necesito incorporar hechos y dimensiones
nuevos, y campos a los existentes, sin rehacer lo que ya funciona ni recargar el histórico entero.

**Why this priority**: Está asumido desde el principio que el modelo se diseña de una pasada y se
corregirá al avanzar. Si cada corrección obligara a rehacerlo, el diseño habría fallado.

**Independent Test**: Se puede añadir un hecho nuevo y comprobar que los informes existentes siguen
dando las mismas cifras.

**Acceptance Scenarios**:

1. **Given** el modelo en producción, **When** se añade un hecho nuevo con sus dimensiones,
   **Then** los informes existentes **no cambian de resultado**.
2. **Given** un hecho existente, **When** se le añade una métrica nueva, **Then** las filas
   anteriores la muestran como ausente, no como cero.
3. **Given** una dimensión compartida, **When** se le añade un atributo, **Then** los hechos que ya
   la usaban siguen funcionando.
4. **Given** un informe que necesita un hecho o una dimensión inexistente, **When** se plantea,
   **Then** **se modifica este modelo**, y **no** se crea una tabla propia del informe.

---

### Edge Cases

- **Entidad que cambia de atributo entre cargas.** Se cierra la versión anterior y se abre una nueva;
  los hechos anteriores siguen apuntando a la versión antigua.
- **Entidad que aparece en un hecho antes de existir en su dimensión.** El hecho conserva su
  referencia y la dimensión gana una fila marcada como desconocida. **Nunca se descarta el hecho**:
  perder un accidente porque su calle no estaba cargada sería inaceptable.
- **Carga repetida del mismo período.** El resultado debe ser idéntico: recargar no duplica.
- **Hito que aún no ha ocurrido.** En una instantánea acumulada, un caso sin cierre tiene esa columna
  ausente — **no cero, no la fecha de carga**.
- **Corrección tardía en la fuente.** Un caso cuya severidad se corrige después debe reflejarse en la
  siguiente carga sin duplicar la fila.
- **Dimensión sin uso.** Una dimensión que ningún hecho referencia es señal de diseño sobrante, no de
  previsión.
- **Métrica que no existía.** Al añadir una métrica, las filas históricas la muestran ausente; nunca
  se rellenan con cero, que sería un dato inventado.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Estructura del modelo

- **FR-001**: El modelo MUST organizarse como **hechos rodeados de dimensiones compartidas**, con el
  grano de cada hecho declarado y único.
- **FR-002**: Cada hecho MUST declarar **explícitamente su grano** —qué representa exactamente una
  fila— y ninguna fila MUST representar dos cosas distintas.
- **FR-003**: Cada hecho MUST declarar **de qué tipo es**: de transacción, de instantánea periódica o
  de instantánea acumulada.
- **FR-004**: Las dimensiones compartidas por varios hechos MUST ser **una sola**, con una única
  definición de cada atributo. **MUST NOT** existir dos versiones del mismo concepto.
- **FR-005**: El modelo MUST incluir una **dimensión de tiempo** con los niveles que el catálogo
  necesita: día, semana, mes, trimestre, año, día de la semana y franja horaria.
- **FR-006**: El modelo MUST incluir una **dimensión geográfica** que aplane la jerarquía de cinco
  niveles del sistema operativo, para que un informe pueda agrupar por condado sin encadenar
  búsquedas.

#### Historia de las entidades

- **FR-007**: Las dimensiones cuyos atributos cambian y afectan a la interpretación del pasado MUST
  **guardar versiones con su vigencia**.
- **FR-008**: Un hecho MUST referenciar **la versión de la dimensión vigente en el momento en que el
  hecho ocurrió**.
- **FR-009**: El modelo MUST permitir además consultar por el **estado actual** de una entidad, para
  los informes que lo necesiten.
- **FR-010**: El versionado MUST construirse **observando cómo cambia la fuente entre cargas**, sin
  exigir cambios en el sistema operativo.
- **FR-011**: Como mínimo MUST versionarse: la **unidad de emergencia con su proveedor**, el
  **cliente con su plan y su estado**, y el **partner con su plan de acceso** — los tres casos donde
  el catálogo pide medir períodos pasados.

#### Carga

- **FR-012**: La carga MUST seguir el patrón de ficheros intermedios ya fijado por la spec de
  infraestructura, que **no cambia**.
- **FR-013**: Cada hecho MUST cargarse por **un flujo propio**, y ese flujo MUST alimentar a
  **todos** los informes que usen ese hecho. **MUST NOT** existir un flujo por informe.
- **FR-014**: Recargar un período ya cargado MUST producir **el mismo resultado**, sin duplicar
  filas.
- **FR-015**: Un hecho cuya entidad de dimensión aún no exista MUST cargarse igualmente, con la
  dimensión marcada como desconocida. **MUST NOT** descartarse el hecho.

#### Regla de crecimiento

- **FR-016**: Ningún informe compuesto MUST crear su propia tabla. Si necesita un hecho, una
  dimensión o un campo que no existe, **MUST modificarse este modelo**.
- **FR-017**: Añadir un hecho, una dimensión o una métrica **MUST NOT** alterar el resultado de los
  informes existentes.
- **FR-018**: Una métrica añadida MUST presentarse como **ausente** en las filas anteriores a su
  incorporación, **nunca como cero**.

#### Calidad del dato

- **FR-019**: El modelo MUST distinguir **ausencia de valor** de **valor cero** en todas sus métricas.
- **FR-020**: Los hitos no alcanzados de una instantánea acumulada MUST presentarse como ausentes.
- **FR-021**: El modelo MUST registrar, por cada carga, **cuándo se calculó**, para que un informe
  pueda declarar la vigencia de lo que muestra.

### Key Entities

#### Hechos que el catálogo reclama

| Hecho | Grano — una fila por | Tipo | Da servicio a |
|---|---|---|---|
| **Accidente** | Un caso registrado | Instantánea acumulada | OT21, OT25, OT16 |
| **Despacho** | Un intento de asignación | Instantánea acumulada | OT22, OT23, OT12 |
| **Evidencia** | Un elemento levantado en campo | Transacción | OT24 |
| **Estado de unidad** | Un cambio de estado | Transacción | OT12 |
| **Ticket** | Un ticket de soporte | Instantánea acumulada | OT19, OT20 |
| **Facturación** | Una factura emitida | Transacción | OT06, OT07 |
| **Suscripción mensual** | Una suscripción por mes | **Instantánea periódica** | OT05, OT06, OT07 |
| **Transición de embudo** | Un cambio de etapa de prospecto | Transacción | OT01, OT02 |
| **Interacción de demo** | Un evento del prospecto en la demo | Transacción | OT03 |
| **Consumo de API** | Un intervalo de llamadas por partner y endpoint | Transacción agregada | OT08, OT09, OT10 |
| **Incorporación de cliente** | Una etapa de onboarding completada | Transacción | OT04, OT17 |
| **Cambio de acceso de partner** | Un cambio en el acceso | Transacción | OT08 |
| **Validación de región** | Un intento de validación | Transacción | OT11, OT13 |

#### Dimensiones compartidas

| Dimensión | ¿Versionada? | Compartida por |
|---|:--:|---|
| **Tiempo** | — | Todos |
| **Geografía** (país→estado→condado→ciudad→calle) | — | Accidente, despacho, unidad, región |
| **Severidad** | — | Accidente, despacho |
| **Unidad de emergencia** (con su proveedor) | ✅ | Despacho, estado de unidad, evidencia |
| **Cliente** (con su tipo, plan y estado) | ✅ | Casi todos |
| **Plan** | ✅ | Suscripción, ticket, partner |
| **Partner** (con su plan de acceso) | ✅ | Consumo, cambio de acceso |
| **Usuario** (operadores, agentes, ejecutivos) | — | Ticket, embudo, evidencia, validación |
| **Servicio** | — | Ticket, consumo |
| **Origen de despacho** | — | Despacho |
| **Canal de captación** | — | Embudo |
| **Región operativa** | ✅ | Validación de región |

#### Atributos degenerados

El número de caso, el número de factura y el número de ticket **viven en el hecho**, no en una
dimensión: son identificadores de negocio sin atributos propios que describir.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **Al menos el 80 %** de los informes compuestos del catálogo se resuelve con una
  consulta sobre el modelo, **sin flujo de carga propio**.
- **SC-002**: **Cero** informes con tabla dedicada: el número de tablas del almacén crece con los
  hechos, no con los informes.
- **SC-003**: **El 100 %** de los informes que miden períodos pasados atribuye los hechos a la
  versión de la entidad vigente en ese momento, verificable cambiando un atributo y recargando.
- **SC-004**: Dos informes distintos que midan el mismo concepto sobre la misma dimensión devuelven
  **cifras idénticas**.
- **SC-005**: Recargar un período ya cargado deja el modelo **exactamente igual**: cero filas
  duplicadas, cero cifras alteradas.
- **SC-006**: Añadir un hecho nuevo deja **inalterados** los resultados de todos los informes
  existentes.
- **SC-007**: **Ninguna** métrica presenta un valor ausente como cero, verificable con hitos no
  alcanzados y métricas recién añadidas.
- **SC-008**: **El 100 %** de los hechos cuya entidad de dimensión no existía se conserva, marcado
  como desconocido, en vez de descartarse.

---

## Assumptions

- **La infraestructura no cambia.** El almacén, el orquestador y el patrón de carga por ficheros
  intermedios ya están fijados por su propia spec y se dan por buenos.
- **El sistema operativo no se modifica.** El versionado de dimensiones se construye observando la
  fuente entre cargas, no añadiendo historia al origen. Es una consecuencia de la regla de canal
  único que la infraestructura ya declara.
- **El modelo se diseña completo y se construye por fases.** Esta spec fija los hechos y dimensiones
  que el catálogo entero reclama; qué se construye primero es decisión del plan.
- **El modelo se corregirá.** Está asumido que faltarán campos y tablas, y que aparecerán al
  especificar cada departamento. Por eso FR-016 a FR-018 tratan la evolución como caso normal, no
  como excepción.
- **Lo construido se sustituye.** Las tres tablas por informe y sus tres flujos de carga quedan
  reemplazados por consultas sobre el modelo. Se retiran cuando el modelo las cubra, no antes.
- **Se conservan las librerías de carga existentes** —clientes de origen y destino, escritura de
  ficheros intermedios— que son independientes del diseño del modelo.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| **Los informes compuestos en sí** | Este módulo define la base; cada departamento especifica sus informes encima |
| **El modelo predictivo y su registro** | Depende de tablas que no existen; es OT16 y va después |
| **Los listados simples** | Viven sobre el sistema operativo, no sobre este modelo |
| **Cambios en el sistema operativo** | El modelo se construye observando la fuente, no modificándola |
| **La infraestructura** | Ya especificada; este módulo la usa sin cambiarla |
| **Cualquier pantalla o tablero** | El frontend se decide por separado |
