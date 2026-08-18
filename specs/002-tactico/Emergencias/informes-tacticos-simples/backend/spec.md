# Feature Specification: Informes Tácticos Simples de Emergencias (Backend)

**Feature Branch**: `informes-tacticos-simples-emergencias`

**Created**: 2026-08-14

**Status**: Implemented

**Input**: User description: "Informes tácticos simples de Emergencias — listados llanos de solo lectura (backend) que satisfacen OT21, OT22, OT23, OT24 y OT25, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Cinco listados llanos de solo lectura sobre el núcleo del sistema. Es el séptimo módulo de la serie,
el que cubre más objetivos tácticos, y el único que introduce **un eje de acotamiento nuevo**: un
cliente no ve «sus» expedientes por titularidad, sino **los de las zonas geográficas que tiene
contratadas**.

**Nota sobre el nombre.** Este departamento ya tenía un módulo llamado `informes-tacticos-simples`
con los 19 informes **agregados**. Se renombró a `informes-tacticos-agregados` —que es lo que
contiene— y este módulo ocupa el nombre que le corresponde. El código de aquel no se tocó.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común. **No se repite aquí.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §7 — catálogo y trazabilidad.
- Módulos previos: los seis anteriores. Se reutilizan y **no se vuelven a decidir**.
- `specs/002-tactico/Emergencias/informes-tacticos-agregados/` — los 19 informes agregados, que
  cubren OT21, OT22 y OT23 desde el lado de la agregación. **Estos listados no los duplican.**

**Alcance:** solo backend.

---

## Nota de alcance: el estado de un caso no es una propiedad del caso

Es la corrección de fondo del módulo, y la tercera vez que este patrón aparece en la serie.

**Un caso queda inactivo por tres razones muy distintas:**

| Razón | Significa |
|---|---|
| **Cerrado** | La emergencia se atendió y terminó — es el desenlace bueno |
| **Descartado** | Falsa alarma: nunca hubo emergencia |
| **Fusionado** | Es el mismo hecho que otro caso, que sigue vivo |

**Y el registro del caso no guarda su estado.** El estado formal —reportado, buscando unidad,
asignado, en atención, cerrado, descartado, fusionado— vive en el **histórico de estados**, y
conocerlo exige quedarse con el último registro por caso.

**Consecuencia sobre estos listados:**

- El listado de casos expone **lo que sí es propiedad del caso**: si sigue activo, si tiene hora de
  fin, y si apunta a otro caso como duplicado. Con eso se distinguen las tres situaciones sin
  inventar nada.
- **El estado formal es compuesto** y ya está cubierto por los informes agregados existentes.

**Por qué importa.** Un listado de «casos inactivos» sin distinguir pondría en la misma línea
**emergencias atendidas, falsas alarmas y duplicados**. Un recuento así presentaría el trabajo
realizado y el ruido descartado como la misma cosa.

### Y una consecuencia sobre el acotamiento por zona

Filtrar los casos de las zonas contratadas por un cliente exige traducir esas zonas a la ubicación
que el caso guarda, que es más fina que el condado. Hoy el módulo operativo lo resuelve **caso por
caso mientras recorre**, lo que funciona pero no es un filtro.

**Este listado exige resolver las zonas a un conjunto antes de consultar**, para que el filtrado
ocurra en la base y no fila a fila. Si esa traducción resultara impracticable, el acotamiento por
zona dejaría de ser simple — y con él, el acceso del cliente a este listado.

### Resto de la consolidación

| Filas del catálogo | Resolución |
|---|---|
| Listado de casos del período · Casos en borrador con advertencias · Casos abiertos sobre el umbral | **Un solo listado de casos con filtros** |
| Despachos del período · Alertas de agotamiento de candidatas · Misiones en tránsito | **Un solo listado de despachos con filtros** |
| Evidencia sin sincronizar · Casos sin evidencia · Notas de campo por tipo y unidad | **Dos listados** —fotografías y notas— porque son registros distintos |
| Casos cerrados con resultado · Casos cerrados sin observaciones | **Un solo listado de cierres con filtros** |
| Monitoreo de casos activos · Parámetros de asignación | Ya construidos |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar los casos con el alcance que a cada quien corresponde (Priority: P1)

Como Operador de Emergencias o Administrador, quiero consultar los accidentes filtrando por
severidad, zona, origen del reporte o situación, para entender qué ha ocurrido sin abrir caso por
caso. Como Cliente, quiero ver los casos cerrados de las zonas que tengo contratadas.

**Why this priority**: Es el listado central del departamento y **el único donde el acotamiento por
zona contratada tiene consecuencia**. Además es donde se materializa la distinción entre un caso
atendido, una falsa alarma y un duplicado.

**Independent Test**: Consultar el listado con cada filtro, con un rol interno y con un cliente, sin
que existan los otros cuatro listados.

**Acceptance Scenarios**:

1. **Given** existen casos en varias zonas geográficas, **When** un Cliente consulta el listado,
   **Then** obtiene **únicamente los de las zonas que tiene contratadas**.
2. **Given** un Cliente sin zonas contratadas, **When** consulta el listado, **Then** obtiene un
   resultado vacío, **no** el listado completo.
3. **Given** un Cliente, **When** consulta el listado, **Then** obtiene **solo casos ya cerrados**:
   la emergencia en curso es información operativa, no del cliente.
4. **Given** un Operador de Emergencias, **When** consulta el listado, **Then** obtiene los casos de
   **todas** las zonas, en cualquier situación.
5. **Given** un caso cerrado, uno descartado por falsa alarma y uno fusionado como duplicado,
   **When** se consulta el listado, **Then** **cada uno se distingue del otro**, y el fusionado
   indica de qué caso es duplicado.
6. **Given** casos de distinta severidad, **When** se filtra por severidad, **Then** solo aparecen
   esos, con el **nombre** de la severidad y de la ubicación, no con identificadores.
7. **Given** un caso detenido en borrador porque su registro levantó advertencias, **When** se
   filtra por esa situación, **Then** aparece: es un caso que nadie confirmó ni descartó.
8. **Given** un Partner de integración autenticado, **When** consulta el listado, **Then** el
   sistema responde `403`: el acceso programático a los datos tiene su propio camino.

---

### User Story 2 - Seguir los despachos y las misiones en curso (Priority: P2)

Como Operador de Emergencias o Administrador, quiero ver los despachos producidos, con su origen,
la unidad a la que fueron y en qué punto están, para entender cómo se está resolviendo la asignación
y qué misiones siguen en camino.

**Why this priority**: Sostiene OT22 y OT23 y da visibilidad sobre el eslabón más crítico de la
cadena. Va después de los casos porque depende de que existan.

**Independent Test**: Consultar el listado de forma aislada, con y sin rango de fechas, sin que
existan los otros cuatro.

**Acceptance Scenarios**:

1. **Given** hubo despachos en el período, **When** se consulta el listado, **Then** cada uno muestra
   el caso, la unidad, el **origen** del despacho, la hora de despacho, la de llegada si la hubo y
   la de retiro si la hubo.
2. **Given** despachos de distinto origen —automático, manual, escalado a zona vecina—, **When** se
   filtra por origen, **Then** solo aparecen los de ese origen.
3. **Given** una unidad despachada que aún no ha llegado, **When** se filtra por misiones en
   tránsito, **Then** aparece: es un despacho sin hora de llegada ni de retiro.
4. **Given** un retiro forzado desde la central, **When** aparece en el listado, **Then** se
   distingue de un retiro normal.
5. **Given** varios despachos sobre un mismo caso, **When** se consulta el listado, **Then**
   aparecen **todos**, cada uno con su estado: un caso puede acumular intentos de varios orígenes.
6. **Given** no se indica período, **When** se consulta el listado, **Then** el sistema devuelve el
   histórico completo paginado.

---

### User Story 3 - Revisar la evidencia levantada en campo (Priority: P3)

Como Administrador, quiero ver qué fotografías y qué notas de campo se han registrado, y sobre todo
**cuáles quedaron sin sincronizar**, para recuperar evidencia que se capturó y nunca llegó.

**Why this priority**: Es la única forma de detectar evidencia perdida, un hueco que la revisión
anterior dejó anotado expresamente. Va en tercer lugar porque depende de que existan casos atendidos.

**Independent Test**: Consultar los dos listados de forma aislada, sin que existan los otros tres.

**Acceptance Scenarios**:

1. **Given** existe evidencia capturada sin conexión y aún sin sincronizar, **When** se filtra por
   esa situación, **Then** aparece: es evidencia que se levantó y no llegó.
2. **Given** una fotografía capturada sin conexión y sincronizada después, **When** aparece en el
   listado, **Then** muestra **la hora en que se capturó**, no la hora en que se subió.
3. **Given** una nota registrada en línea, **When** aparece en el listado, **Then** su hora de
   captura y su hora de registro coinciden — el contraste que demuestra que la primera no se está
   sustituyendo por la segunda.
4. **Given** dos unidades atendiendo el mismo caso, **When** se consulta el listado, **Then** la
   evidencia de cada una aparece atribuida a quien la levantó, sin mezclarse.
5. **Given** notas de distinto tipo, **When** se filtra por tipo, **Then** solo aparecen las de ese
   tipo.

---

### User Story 4 - Consultar cómo se cerraron los casos (Priority: P4)

Como Administrador, quiero ver el resultado con el que se cerró cada caso y su calificación, y
cuáles se cerraron sin dejar observaciones, para valorar la calidad del cierre.

**Why this priority**: Completa OT25 y es la base de los análisis posteriores de calidad de
atención, pero por sí solo es el de menor urgencia.

**Independent Test**: Consultar el listado de forma aislada, sin que existan los otros cuatro.

**Acceptance Scenarios**:

1. **Given** casos cerrados con distinto resultado de atención, **When** se consulta el listado,
   **Then** cada uno muestra el caso, el resultado, la calificación y las observaciones.
2. **Given** un caso cerrado sin observaciones, **When** se filtra por esa situación, **Then**
   aparece con las observaciones ausentes, no con una cadena vacía.
3. **Given** un caso cerrado sin calificación, **When** aparece en el listado, **Then** la
   calificación se presenta como ausente, **no como cero**: no calificar no es calificar mal.

---

### Edge Cases

- **Resultado vacío.** `200` con `data: []`, nunca `404`.
- **Cliente sin zonas contratadas.** Resultado vacío, **nunca** el listado completo. De las dos
  lecturas posibles de «sin zonas», es la única segura.
- **Caso sin ubicación resoluble.** Aparece con la ubicación ausente. **No se omite**: un caso cuya
  calle no resuelve es una anomalía que la supervisión necesita ver — y además nunca podrá acotarse
  a ninguna zona.
- **Caso fusionado.** Sigue apareciendo, marcado como duplicado y apuntando a su caso padre. **No se
  borra**, que es lo que el sistema garantiza.
- **Caso descartado.** Sigue apareciendo, distinguible de un cierre.
- **Despacho sin llegada ni retiro.** Es una misión en tránsito, no un dato incompleto.
- **Evidencia sincronizada.** Su hora de captura y su hora de registro **difieren**, y esa
  diferencia es información, no un error.
- **Calificación ausente.** Nunca se presenta como cero.
- **Retraso de ingesta.** 5–15 segundos. Un caso recién cerrado puede seguir apareciendo abierto.
  **No se compensa.**
- **Límite excedido.** `limit` sobre el máximo responde `400`.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los cinco listados

- **FR-001**: El sistema MUST ofrecer un listado de **casos** con la ubicación, la severidad, el
  origen del reporte, el impacto humano registrado, la hora del accidente, si sigue activo, su hora
  de fin si la tiene y el caso del que es duplicado si lo es. *(OT21/OT25, OP32, OP33)*
- **FR-002**: El listado de casos MUST admitir filtros por **severidad, ubicación, origen del
  reporte, situación —activo, cerrado, duplicado, descartado— y rango de fecha del accidente**,
  combinables.

  > ⚠️ **Corregido el 2026-08-15 al implementar: se retira «en borrador».** `BORRADOR` es un
  > **estado formal** que vive en el histórico de estados, igual que `REPORTADO` o `ASIGNADO`, y
  > `Fact_Accidente` no guarda ninguna columna que lo distinga. Un caso en borrador es
  > `activo = true` sin hora de fin — **idéntico a cualquier otro caso en curso**.
  >
  > Implementarlo con esas dos condiciones devolvería **todos los casos activos** etiquetados como
  > detenidos en borrador: la forma correcta con el contenido equivocado. Obtenerlo de verdad exige
  > el último registro del histórico por caso, que es justo lo que **FR-008 prohíbe**. Los dos
  > requisitos se contradicen, y se resuelve a favor de FR-008, que es el que protege la honestidad
  > del dato.
- **FR-003**: El sistema MUST ofrecer un listado de **despachos** con el caso, la unidad, el origen
  del despacho, la hora de despacho, la de llegada, la de retiro y si el retiro fue forzado.
  *(OT22/OT23, OP35, OP36, OP37, OP38)*
- **FR-004**: El sistema MUST ofrecer un listado de **fotografías de evidencia** y otro de **notas de
  campo**, ambos con el caso, quien las levantó, si están sincronizadas, **la hora de captura** y la
  hora de registro. *(OT24, OP40, OP42)*
- **FR-005**: El sistema MUST ofrecer un listado de **cierres de caso** con el resultado de la
  atención, la calificación y las observaciones finales. *(OT25, OP45)*

#### La distinción entre las tres formas de quedar inactivo

- **FR-006**: El listado de casos MUST permitir distinguir un caso **cerrado**, uno **descartado por
  falsa alarma** y uno **fusionado como duplicado**, a partir de lo que el propio caso registra.
- **FR-007**: Un caso **fusionado** MUST indicar de qué caso es duplicado, y **MUST NOT** omitirse
  del listado: el sistema garantiza que no se borra.
- **FR-008**: El listado **MUST NOT** afirmar el estado formal del caso, que no es una propiedad
  suya. Los estados formales se obtienen de los informes agregados existentes.

#### Acotamiento por zona contratada

- **FR-009**: Un **rol interno** —Operador de Emergencias, Administrador— MUST obtener los casos de
  todas las zonas y en cualquier situación.
- **FR-010**: Un **Cliente** MUST obtener únicamente los casos de **las zonas geográficas que tiene
  contratadas**, y **solo los ya cerrados**.
- **FR-011**: Un Cliente **sin zonas contratadas** MUST obtener un resultado vacío. **MUST NOT**
  interpretarse la ausencia de zonas como acceso a todas.
- **FR-012**: El acotamiento por zona MUST resolverse como **filtro sobre el conjunto de ubicaciones
  contratadas**, no comprobando caso por caso mientras se recorre.
- **FR-013**: Los listados de **despachos**, **evidencia** y **cierres** MUST estar restringidos a
  roles internos.
- **FR-014**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato.

#### Autoridad departamental

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS.

- **FR-014a**: El **Director de Operaciones**, autoridad de Emergencias, MUST acceder a los cinco
  listados sin acotamiento por zona ni por situación del caso.
- **FR-014b**: ⚠️ La exención **MUST NOT** alcanzar a FR-015 ni FR-016: **las coordenadas del
  accidente y la identidad de las personas implicadas siguen sin exponerse también para él**. Son
  exclusiones constitucionales, no de acotamiento, y el cargo no las levanta.
- **FR-014c**: De los cinco listados, **los de evidencia son bandeja de trabajo** pese a parecer
  supervisión: la evidencia sin sincronizar hay que ir a recuperarla, y quien la recupera es el
  Operador. **Cierres es supervisión**; casos y despachos sirven a ambas capas.

#### Protección del dato sensible

- **FR-015**: El listado de casos **MUST NOT** exponer las coordenadas geográficas del accidente. La
  ubicación se expresa con el nombre de la calle, la ciudad y el condado.
- **FR-016**: Los listados **MUST NOT** exponer la identidad de conductores, implicados ni víctimas.

#### Naturaleza de los listados

- **FR-017**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla**.
- **FR-018**: El sistema MUST devolver el **nombre** de la severidad, la ubicación, la unidad, el
  origen del despacho y el autor, no sus identificadores internos. Se exceptúa el **número de caso**,
  que es lenguaje de negocio.
- **FR-019**: Los listados MUST ser de **solo lectura**.

#### Filtros, orden y paginación

- **FR-020**: Los listados de **casos**, **despachos** y **evidencia** son de hechos del período y
  MUST aceptar rango de fechas **opcional**. El de **cierres** también.
- **FR-021**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria.
- **FR-022**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  válidos.
- **FR-023**: Un `limit` superior al máximo MUST responder `400`. MUST NOT recortarse en silencio.

#### Calidad del dato

- **FR-024**: La **hora de captura** de una evidencia MUST devolverse tal como se registró en el
  sitio. **MUST NOT** sustituirse por la hora de subida, que se devuelve aparte.
- **FR-025**: Una **calificación ausente** MUST presentarse como ausente, **nunca como cero**.
- **FR-026**: Un caso **sin ubicación resoluble** MUST aparecer con la ubicación ausente en lugar de
  ser omitido.

### Key Entities

- **Caso de accidente**: el hecho registrado, con su ubicación, severidad, origen del reporte,
  impacto humano, horas de inicio y fin, y el caso del que es duplicado si lo es. Alimenta FR-001.
- **Despacho**: cada intento de asignar una unidad a un caso, con su origen, sus horas y si el retiro
  fue forzado. Alimenta FR-003.
- **Fotografía de evidencia** y **nota de campo**: los registros levantados en el sitio, con su hora
  de captura, su hora de registro y su estado de sincronización. Alimentan FR-004, FR-024.
- **Cierre de caso**: el desenlace de la atención, con resultado, calificación y observaciones.
  Alimenta FR-005.
- **Zona contratada**: el conjunto de ubicaciones que un cliente tiene habilitadas. Determina qué ve
  (FR-010 a FR-012).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Cliente obtiene **el 100 %** de los casos cerrados de sus zonas y **cero** de zonas
  ajenas, verificable con casos en dos zonas distintas.
- **SC-002**: Un Cliente sin zonas contratadas obtiene **cero** casos, no el listado completo.
- **SC-003**: Un Cliente obtiene **cero** casos aún abiertos.
- **SC-004**: **El 100 %** de los casos cerrados, descartados y fusionados es distinguible entre sí,
  verificable con uno de cada clase.
- **SC-005**: **En ninguna** respuesta aparecen coordenadas geográficas ni identidad de personas
  implicadas.
- **SC-006**: **El 100 %** de la evidencia capturada sin conexión conserva su hora de captura,
  distinta de su hora de registro, verificable con evidencia sincronizada y evidencia en línea.
- **SC-007**: Los cinco listados devuelven su primera página en **menos de 2 segundos**.
- **SC-008**: Recorrer un listado por páginas devuelve **cada fila exactamente una vez**.
- **SC-009**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**.

---

## Assumptions

- **El contrato común está vigente** y la capa transversal de los seis módulos previos se reutiliza.
  Esta spec **no** vuelve a decidirla.
- **El acotamiento por zona es un eje nuevo** y previsiblemente exigirá ampliar el resolutor
  transversal. Es la primera vez desde Red Operativa que se prevé tocarlo, y por una razón legítima:
  ninguno de los ejes anteriores acota por cobertura geográfica.
- **Un cliente solo ve casos cerrados.** Es lo que el módulo operativo ya aplica en el expediente del
  cliente, y el listado no puede ser más amplio que esa pantalla.
- **Un caso fusionado o descartado no se borra.** Está verificado en el sistema real.
- **La hora de captura y la de subida se guardan por separado.** Es la regla central del módulo de
  evidencia, y está verificada.
- **Los roles son los reales del sistema.** Operador de Emergencias, Administrador y Cliente existen
  en `.specify/docs/actors.md`.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance, y con más razón aquí por
  tratarse de datos de siniestralidad.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| **El estado formal de un caso** | ⚠️ **No es una propiedad del caso.** Vive en el histórico de estados y conocerlo exige el último registro por caso. Ya lo cubren los informes agregados existentes. |
| Volumen de casos, distribución por severidad y zona, ranking de ubicaciones, impacto humano agregado | **Ya construidos** como informes agregados |
| Asignación automática vs manual, tiempos de respuesta, carga por unidad, ratio demanda/capacidad | **Ya construidos** como informes agregados |
| Tiempo de asignado a cerrado, cierres forzados, abortos y pérdidas | **Ya construidos** como informes agregados |
| Cobertura de evidencia, latencia de sincronización, completitud del enriquecimiento | Son agregaciones → compuestos |
| Envejecimiento de la cartera, distribución de resultados, retiros forzados por proveedor | Son agregaciones → compuestos |
| Desviación entre tiempo estimado y llegada real | Es una agregación y cruza tablas → compuesto |
| Monitoreo de casos activos, parámetros de asignación | Ya construidos |
| **Coordenadas del accidente e identidad de implicados** | Dato sensible bajo control de acceso y auditoría propios; un listado táctico no los necesita |
| Cualquier pantalla o tablero | El frontend se decide por separado. |
