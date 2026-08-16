# Feature Specification: Informes Tácticos Simples de Partners y API (Backend)

**Feature Branch**: `informes-tacticos-simples-partners-api`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos simples de Partners y API — listados llanos de solo lectura (backend) que satisfacen OT08, OT09 y OT10, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Cinco listados llanos de solo lectura sobre el acceso programático a la información de TSI. Es el
sexto módulo de la serie y **el último que acota por organización**: Emergencias introduce un eje
distinto —la cobertura geográfica contratada—, así que aquí se cierra el patrón antes de abrir otro.

**Lo que distingue a este departamento:**

1. **Es el mejor anclado del catálogo.** Tiene dos casos de uso tácticos que describen con precisión
   qué supervisar, así que hay poco margen para inventar alcance.
2. **Es el que más trabajo tiene ya construido.** La consola de consumo y la de registros de llamada
   cubren buena parte de OT09, y este módulo **no las duplica**.
3. **Guarda el secreto con el que un partner se autentica**, del mismo orden que el medio de cobro de
   Suscripciones.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común. **No se repite aquí.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §6 — catálogo y trazabilidad.
- Módulos previos: los cinco anteriores. Se reutilizan y **no se vuelven a decidir**.

**Alcance:** solo backend.

---

## Nota de alcance: por qué una credencial inactiva no dice por qué lo está

Esta es la corrección de fondo del módulo.

**Una credencial de integración puede estar inactiva por tres razones opuestas:**

| Razón | Significa |
|---|---|
| **Revocada por el partner** | Decisión de seguridad: el secreto se comprometió |
| **Desactivada en cascada** | El partner fue suspendido por impago; es administrativo |
| **Expirada** | Venció su plazo de vigencia |

**Y el registro de la credencial no las distingue.** El propio código lo dice al explicar por qué la
reactivación de un partner no pregunta el motivo: *«no podría: las tres razones son indistinguibles»*.
Saber por qué una credencial está inactiva exige leer **la bitácora de cambios de acceso** y
localizar el último evento que le corresponde.

**Consecuencia sobre estos listados:**

- El listado de **credenciales** informa de **si** una credencial está activa, su entorno y su
  vigencia. **No informa de por qué está inactiva.**
- El listado de **bitácora de acceso** sí registra los motivos, cada uno con su fecha y su ejecutor.
- **Unir ambas cosas —«esta credencial está inactiva por esto»— es un informe compuesto**, porque
  exige quedarse con el último evento relevante por credencial y volver a cruzar.

**Por qué importa decirlo.** Un listado de credenciales inactivas que no distinga el motivo pondría
en la misma línea una decisión de seguridad del partner y un impago administrativo. Reactivar sin
mirar la bitácora resucitaría una credencial comprometida — que es exactamente lo que la regla de
reactivación selectiva previene.

### Resto de la consolidación

| Filas del catálogo | Resolución |
|---|---|
| Credenciales por entorno y estado · Credenciales próximas a vencer | **Un solo listado con filtros** |
| Clientes con acceso y zonas habilitadas · Entregas programadas por cliente | **Un solo listado con filtros** |
| Partners por estado y plan · Bitácora de cambios · Versiones del contrato | Listado propio cada uno |
| **Llamadas rechazadas por límite** | ✅ **Ya cubierto.** La consola de registros existente filtra por código de respuesta, acota por partner y pagina. Construir otro endpoint sería duplicarla. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el estado de los partners y de sus credenciales (Priority: P1)

Como Desarrollador de APIs o Administrador, quiero ver en qué punto de su incorporación está cada
partner y qué credenciales tiene vigentes en cada entorno, para saber quién puede operar y quién
está a punto de quedarse sin acceso. Como Partner, quiero ver lo mío.

**Why this priority**: Es el listado central del departamento y donde se materializa la distinción
entre estar inactiva y saber por qué. Además, las credenciales próximas a vencer son la única señal
preventiva: una credencial que caduca el jueves es una integración que deja de funcionar el jueves.

**Independent Test**: Consultar ambos listados de forma aislada, con dos roles distintos, sin que
existan los otros tres.

**Acceptance Scenarios**:

1. **Given** existen partners de varias cuentas, **When** un Partner consulta el listado, **Then**
   obtiene **únicamente el suyo**.
2. **Given** un Partner, **When** consulta pidiendo expresamente los datos de otro, **Then** el
   sistema responde `403` y **no devuelve ninguna fila**.
3. **Given** un Desarrollador de APIs, **When** consulta el listado, **Then** obtiene **todos** los
   partners con su estado de incorporación, su plan de acceso y sus cupos.
4. **Given** un partner suspendido, **When** consulta sus propios listados, **Then** **obtiene sus
   datos**: es donde ve qué le pasó y qué debe regularizar.
5. **Given** credenciales de pruebas y de producción del mismo partner, **When** se consulta el
   listado, **Then** aparecen **ambas**, cada una con su entorno: activar producción no elimina el
   acceso de pruebas.
6. **Given** credenciales que caducan en distintas fechas, **When** se filtra por proximidad de
   caducidad, **Then** aparecen solo las que vencen en ese plazo, con los días que les quedan.
7. **Given** una credencial inactiva, **When** aparece en el listado, **Then** se indica que no está
   activa **y el listado no afirma por qué**: esa información vive en la bitácora.
8. **Given** un Operador de Emergencias autenticado, **When** consulta cualquiera de los dos
   listados, **Then** el sistema responde `403`.

---

### User Story 2 - Auditar los cambios de acceso y sus motivos (Priority: P2)

Como Administrador, quiero ver la secuencia de cambios de acceso de un partner —registro, asignación
de plan, activación, revocación, suspensión, reactivación— con quién los ejecutó y por qué, para
entender cómo llegó a su situación actual antes de tomar una decisión sobre él.

**Why this priority**: Es donde viven los motivos que el listado de credenciales no puede dar. Sin
él, la User Story 1 informa de estados sin contexto. Va después porque es de consulta puntual, no de
vigilancia continua.

**Independent Test**: Consultar el listado de forma aislada, con y sin rango de fechas, sin que
existan los otros.

**Acceptance Scenarios**:

1. **Given** un partner con historial de cambios, **When** se consulta el listado, **Then** cada
   entrada muestra el tipo de cambio, el estado del que salió, al que pasó, el motivo cuando lo hubo,
   quién lo ejecutó y la fecha.
2. **Given** una credencial revocada por el partner y otra desactivada por suspensión, **When** se
   consultan los cambios, **Then** **cada una aparece con su tipo de cambio propio**, distinguibles
   entre sí.
3. **Given** una suspensión, **When** aparece en el listado, **Then** trae su motivo: el sistema lo
   exige al cortar el acceso.
4. **Given** una reactivación, **When** aparece en el listado, **Then** puede no traer motivo, porque
   no se exige al devolver el acceso.
5. **Given** no se indica período, **When** se consulta el listado, **Then** el sistema devuelve el
   histórico completo paginado.
6. **Given** un Partner consulta la bitácora, **When** obtiene el resultado, **Then** ve **solo la
   suya**.

---

### User Story 3 - Consultar el contrato vigente y el alcance de datos contratado (Priority: P3)

Como Desarrollador de APIs, quiero ver qué versiones del contrato de integración están publicadas y
cuáles retiradas, y qué alcance de datos tiene habilitado cada cliente, para no retirar una versión
que alguien sigue usando ni entregar datos fuera de lo contratado.

**Why this priority**: Completa OT08 y OT10, pero opera sobre poco volumen y con menos urgencia
diaria.

**Independent Test**: Consultar los dos listados de forma aislada, sin que existan los de las otras
historias.

**Acceptance Scenarios**:

1. **Given** existen versiones publicadas y retiradas del contrato, **When** se consulta el listado,
   **Then** aparecen **todas** con su estado y sus fechas de publicación y retiro.
2. **Given** una versión retirada, **When** se consulta el listado, **Then** **no se omite**: saber
   qué se retiró y cuándo es parte de la supervisión del contrato.
3. **Given** clientes con distinto alcance de datos contratado, **When** se consulta ese listado,
   **Then** cada uno muestra sus zonas geográficas habilitadas y su frecuencia y formato de entrega
   pactados.
4. **Given** un cliente sin preferencias configuradas, **When** aparece en el listado, **Then** se
   presenta con el alcance ausente, no como si tuviera acceso ilimitado.

---

### Edge Cases

- **Resultado vacío.** `200` con `data: []`, nunca `404`.
- **Partner sin credenciales todavía.** Aparece en el listado de partners con su estado de
  incorporación; simplemente no aporta filas al de credenciales.
- **Partner suspendido.** **Conserva el acceso** a sus propios listados: es donde ve su situación.
- **Credencial de pruebas y de producción a la vez.** Ambas aparecen. Son estados compatibles, no
  excluyentes.
- **Credencial inactiva.** Se indica que no lo está, **sin afirmar el motivo**.
- **Reactivación sin motivo.** Se presenta como ausencia, no como cadena vacía: el motivo es
  obligatorio al cortar el acceso, no al devolverlo.
- **Cliente sin preferencias de entrega.** Alcance ausente, nunca interpretado como ilimitado.
- **Retraso de ingesta.** 5–15 segundos. Una credencial recién revocada puede seguir apareciendo
  activa. **No se compensa.**
- **Límite excedido.** `limit` sobre el máximo responde `400`.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los cinco listados

- **FR-001**: El sistema MUST ofrecer un listado de **partners** con la cuenta cliente, el nombre, el
  estado de incorporación, el plan de acceso, los cupos de consumo y, si está suspendido, la fecha y
  el motivo. *(OT08, OP26)*
- **FR-002**: El sistema MUST ofrecer un listado de **credenciales de integración** con el partner, el
  nombre de la credencial, el entorno, si está activa y su fecha de expiración, filtrable por
  proximidad de caducidad. *(OT08, CU-O49)*
- **FR-003**: El sistema MUST ofrecer un listado de **cambios de acceso** con el tipo de cambio, los
  estados de origen y destino, el motivo, el ejecutor y la fecha. *(OT08, OT09)*
- **FR-004**: El sistema MUST ofrecer un listado de **versiones del contrato de integración** con su
  estado y sus fechas de publicación y retiro, incluidas las retiradas. *(OT08, CU-O50)*
- **FR-005**: El sistema MUST ofrecer un listado de **alcance de datos contratado por cliente**, con
  las zonas geográficas habilitadas, la frecuencia y el formato de entrega pactados. *(OT10, OP31)*

#### La distinción entre estar inactiva y saber por qué

- **FR-006**: El listado de credenciales MUST indicar **si** una credencial está activa. **MUST NOT**
  afirmar por qué no lo está.
- **FR-007**: El listado de cambios de acceso MUST distinguir **cada motivo con su tipo propio** —en
  particular, una revocación decidida por el partner de una desactivación por suspensión—, porque son
  situaciones opuestas: la primera es una decisión de seguridad y la segunda es administrativa.

#### Protección del secreto de autenticación

- **FR-008**: El sistema **MUST NOT** exponer, en ninguna respuesta y bajo ninguna circunstancia, el
  secreto con el que un partner se autentica, ni en claro ni transformado. El nombre de la credencial
  y su entorno bastan para identificarla.

#### Acotamiento por organización

- **FR-009**: Un **gestor** —Desarrollador de APIs o Administrador— MUST obtener los registros de
  todos los partners, y MUST poder filtrar por uno concreto.
- **FR-010**: Un **Partner** MUST obtener únicamente los registros de su propia organización,
  resueltos por su pertenencia, sin necesidad de indicarla.
- **FR-011**: Un Partner que pida expresamente los registros de **otro** MUST recibir una negativa.
  **MUST NOT** devolvérsele los suyos como si su petición se hubiera atendido.
- **FR-012**: Un partner **suspendido** MUST conservar el acceso a sus propios listados: es donde ve
  su situación y qué debe regularizar.
- **FR-013**: Los listados de **versiones del contrato** y de **alcance de datos** MUST estar
  restringidos a los gestores.
- **FR-014**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato.

#### Autoridad departamental

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS.

- **FR-014a**: El **Director Tecnológico**, autoridad de Partners y API, MUST acceder a los cinco
  listados sin acotamiento por partner.
- **FR-014b**: La exención **MUST NOT** alcanzar a FR-008: el secreto con el que un partner se
  autentica sigue sin exponerse a nadie.
- **FR-014c**: De los cinco listados, **credenciales es bandeja de trabajo** del Desarrollador de
  APIs —renovar antes de que venzan—, mientras que cambios de acceso, versiones del contrato y
  alcance de datos son supervisión: auditoría, decisión de retiro y verificación de cumplimiento.

#### Naturaleza de los listados

- **FR-015**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla**.
- **FR-016**: El sistema MUST devolver el **nombre** del partner, de la cuenta, del ejecutor y del
  servicio, no sus identificadores internos.
- **FR-017**: Los listados MUST ser de **solo lectura**.

#### Filtros, orden y paginación

- **FR-018**: El listado de **cambios de acceso** es de hechos del período y MUST aceptar rango de
  fechas **opcional**. Los de **partners**, **credenciales**, **versiones** y **alcance de datos**
  describen el estado actual y MUST rechazar un rango de fechas; el filtro por fecha de publicación
  o retiro de una versión es un filtro de columna, no un período.
- **FR-019**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria.
- **FR-020**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  válidos.
- **FR-021**: Un `limit` superior al máximo MUST responder `400`. MUST NOT recortarse en silencio.

#### Calidad del dato

- **FR-022**: El sistema MUST tratar los valores centinela como ausencia: un partner sin suspender,
  una reactivación sin motivo y un cliente sin preferencias se presentan como ausentes.
- **FR-023**: Un cliente **sin alcance de datos configurado** MUST presentarse con el alcance
  ausente. **MUST NOT** interpretarse como acceso ilimitado.

### Key Entities

- **Partner de integración**: la organización que consume la información de forma programática, con
  su estado de incorporación, su plan de acceso, sus cupos y su situación de suspensión.
  Alimenta FR-001.
- **Credencial de integración**: el medio con el que un partner se autentica, con su entorno, su
  vigencia y su condición de activa. Alimenta FR-002, FR-006, FR-008.
- **Cambio de acceso**: cada movimiento registrado en la vida del acceso de un partner, con su tipo,
  motivo, ejecutor y fecha. Alimenta FR-003, FR-007.
- **Versión del contrato de integración**: cada versión publicada del acuerdo técnico, con su estado
  y sus fechas. Alimenta FR-004.
- **Alcance de datos contratado**: las zonas geográficas y las condiciones de entrega pactadas con
  cada cliente. Alimenta FR-005, FR-023.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Partner obtiene **el 100 %** de sus registros y **cero** de otros partners,
  verificable con dos partners con actividad simultánea.
- **SC-002**: **Ningún** intento de consultar los registros de otro partner devuelve datos.
- **SC-003**: **En ninguna** de las respuestas de los cinco listados aparece el secreto de
  autenticación, verificable inspeccionando la respuesta completa.
- **SC-004**: **El 100 %** de las revocaciones decididas por el partner es distinguible de las
  desactivaciones por suspensión, verificable con una de cada clase sobre el mismo partner.
- **SC-005**: Un partner suspendido obtiene sus propios listados en **el 100 %** de los casos.
- **SC-006**: **El 100 %** de los clientes sin alcance configurado se presenta como alcance ausente,
  y **ninguno** como acceso ilimitado.
- **SC-007**: Los cinco listados devuelven su primera página en **menos de 2 segundos**.
- **SC-008**: Recorrer un listado por páginas devuelve **cada fila exactamente una vez**.
- **SC-009**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**.

---

## Assumptions

- **El contrato común está vigente** y la capa transversal de los cinco módulos previos se reutiliza,
  incluido el eje «organización» del acotamiento con su criterio parametrizable.
- **El módulo ya tiene disciplina de campos sensibles.** El servicio de consulta de partners enumera
  los campos que nunca salen; los listados reutilizan ese mecanismo en vez de crear otro.
- **Las credenciales de pruebas y de producción coexisten.** Está verificado: activar producción no
  elimina el acceso de pruebas.
- **La suspensión exige motivo; la reactivación no.** Es la regla del sistema, y el listado la
  refleja en vez de tratar la ausencia como un defecto.
- **Los roles son los reales del sistema.** Administrador, Desarrollador de APIs y Partner de
  integración existen en `.specify/docs/actors.md`.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| **Motivo por el que una credencial está inactiva** | ⚠️ **Compuesto.** El registro de la credencial no distingue revocación, cascada ni expiración; averiguarlo exige localizar el último evento relevante en la bitácora y volver a cruzar. Los motivos **sí** son listables en el listado de cambios de acceso (FR-003). |
| **Llamadas rechazadas por límite** | ✅ **Ya cubierto** por la consola de registros existente, que filtra por código de respuesta, acota por partner y pagina. Duplicarla no aportaría nada. |
| Consumo por endpoint, latencia p95, taxonomía de errores, comparativa entre partners | Son agregaciones → compuestos |
| Tiempo de incorporación del partner, adopción de versiones del contrato, tasa de rechazo | Son agregaciones y cruzan tablas → compuestos |
| Clientes con integración API activa, volumen de expedientes entregados, alcance efectivo vs contratado | Son agregaciones → compuestos |
| Métricas y reportes de consumo por partner | Ya construidos |
| Cualquier pantalla o tablero | El frontend se decide por separado. |
