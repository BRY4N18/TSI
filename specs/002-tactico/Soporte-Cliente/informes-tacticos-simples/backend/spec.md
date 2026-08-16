# Feature Specification: Informes Tácticos Simples de Soporte al Cliente (Backend)

**Feature Branch**: `informes-tacticos-simples-soporte-cliente`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos simples de Soporte al Cliente — listados llanos de solo lectura (backend) que satisfacen OT19 y OT20, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Dos listados llanos de solo lectura sobre la atención posterior a la venta. Es el módulo más pequeño
de la serie, y aun así aporta dos cosas que ningún anterior validó.

**Lo que distingue a este departamento:**

1. **Usa el criterio de pertenencia amplio.** Red Operativa y Suscripciones resuelven la cuenta de un
   usuario por ser su administrador local; Soporte lo hace por **estar vinculado** a ella. Es el
   departamento que necesita el *otro* criterio, y por tanto la prueba real de que parametrizarlo
   fue la decisión correcta.
2. **Dos roles distintos acotan por el mismo eje.** Cliente y Partner de integración son ambos
   reportadores, y ninguno puede ver lo del otro. Decidir el acotamiento por «ser Cliente» en vez de
   por «no atender tickets» fue un fallo real que casi se cuela en la revisión anterior.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común. **No se repite aquí.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §8 — catálogo y trazabilidad.
- Módulos previos: `Cuentas-Clientes/`, `Ventas-CRM/`, `Suscripciones-Facturacion/`,
  `Red-Operativa/`. Se reutilizan y **no se vuelven a decidir**.

**Alcance:** solo backend.

---

## Nota de alcance: dos listados, y por qué el segundo es estrecho a propósito

| Filas del catálogo | Resolución |
|---|---|
| Tickets sin clasificar · Tickets sin compromiso de tiempo · Cola por agente y antigüedad · Tickets ligados a una factura en disputa | **Un solo listado de tickets con filtros.** Las cuatro son la misma consulta cambiando el filtro. |
| Escalados del período, separando el automático del humano | Listado propio |
| Configuración de SLA por plan y tipo | Ya construido |

**El listado de escalados no expone el texto de las acciones**, y esa exclusión es deliberada.

El registro de acciones sobre un ticket guarda, junto a cada entrada, **el mensaje escrito** y una
marca de si es una **nota interna**. Las notas internas no pueden llegar al cliente: es una regla ya
verificada, y hoy se aplica filtrando la lista después de leerla.

Un listado táctico de escalados necesita saber **qué pasó, cuándo y quién lo hizo** — no la prosa.
Al no exponer el mensaje, el problema de filtrar notas internas **no llega a plantearse**, en lugar
de resolverse con un filtro que alguien podría olvidar al añadir un campo más adelante.

Además, el listado de escalados queda restringido a los roles de atención. Un escalado es proceso
interno del equipo de soporte, no información que el reportador necesite.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar los tickets viendo solo lo que a cada quien le corresponde (Priority: P1)

Como Agente de Soporte o Administrador, quiero consultar la cola de tickets filtrando por estado,
situación del compromiso de tiempo, agente asignado o vínculo con una factura en disputa, para
priorizar lo que necesita atención. Como Cliente o como Partner de integración, quiero ver los míos
sin ver los de nadie más.

**Why this priority**: Responde cuatro de las seis preguntas del catálogo y es donde el acotamiento
tiene consecuencia. Además es el listado que hace visibles los tickets **sin compromiso de tiempo**,
que hoy nadie vigila.

**Independent Test**: Consultar el listado con cada filtro, con roles de atención y de reporte, y
comprobar el acotamiento, sin que exista el segundo listado.

**Acceptance Scenarios**:

1. **Given** existen tickets de varias cuentas cliente, **When** un Cliente consulta el listado,
   **Then** obtiene **únicamente los de su propia cuenta**.
2. **Given** un Partner de integración con tickets propios y existiendo tickets de otras cuentas,
   **When** consulta el listado, **Then** obtiene **únicamente los suyos** — el acotamiento no
   depende de ser Cliente, sino de no tener ningún rol de atención.
3. **Given** un usuario que es a la vez Cliente **y** Agente de Soporte, **When** consulta el
   listado, **Then** obtiene la cola completa: tener un rol de atención lo saca del acotamiento.
4. **Given** un Agente de Soporte, **When** consulta el listado, **Then** obtiene los tickets de
   **todas** las cuentas, y puede filtrar por agente asignado.
5. **Given** tickets con distinta situación de compromiso de tiempo, **When** se filtra por los que
   **no tienen compromiso**, **Then** aparecen solo esos, que son los que ningún vigilante está
   revisando.
6. **Given** un ticket aún **sin clasificar**, **When** se consulta el listado, **Then** aparece sin
   plazo asociado, y el listado no le atribuye un compromiso que no tiene.
7. **Given** tickets vinculados a una factura en disputa, **When** se filtra por ese vínculo,
   **Then** aparecen solo esos, con el número de la factura.
8. **Given** un Operador de Emergencias autenticado, **When** consulta el listado, **Then** el
   sistema responde `403`.

---

### User Story 2 - Distinguir el escalado automático del humano (Priority: P2)

Como Administrador, quiero ver los escalados producidos en un período sabiendo cuáles los decidió
una persona y cuáles los disparó el sistema por incumplimiento de plazo, para entender si la cola se
está desbordando sola o si el equipo está derivando.

**Why this priority**: Sostiene OT20 y hace visible una distinción que se perdía cuando el escalado
automático se registraba como si lo hubiera hecho el supervisor. Es independiente y de menor volumen
que la cola.

**Independent Test**: Consultar el listado de forma aislada, con y sin rango de fechas, sin que
exista el listado de tickets.

**Acceptance Scenarios**:

1. **Given** hubo escalados en el período, **When** se consulta el listado, **Then** cada entrada
   muestra el ticket, el estado del que salió, al que pasó, la fecha y **quién lo hizo**.
2. **Given** un escalado lo decidió una persona, **When** aparece en el listado, **Then** se
   identifica a esa persona por su nombre.
3. **Given** un escalado lo disparó el sistema por incumplimiento de plazo, **When** aparece en el
   listado, **Then** se identifica **como acción del sistema**, no atribuido a ninguna persona.
4. **Given** no se indica período, **When** se consulta el listado, **Then** el sistema devuelve el
   histórico completo paginado.
5. **Given** un Cliente o un Partner consulta este listado, **Then** el sistema responde `403`: el
   escalado es proceso interno del equipo de atención.
6. **Given** el registro de acciones contiene mensajes y notas internas, **When** se consulta este
   listado, **Then** **ningún texto de mensaje aparece en la respuesta**.

---

### Edge Cases

- **Resultado vacío.** `200` con `data: []`, nunca `404`. Que no haya tickets sin compromiso es una
  buena noticia.
- **Cliente sin tickets.** Obtiene un listado vacío, no un error ni la cola completa.
- **Usuario con rol mixto.** Alguien que sea Cliente y Agente a la vez **no** queda acotado: el
  acotamiento se decide por no tener ningún rol de atención, no por tener uno de reporte.
- **Ticket sin clasificar.** Aparece sin plazo y sin situación de compromiso. **No se le atribuye**
  ninguna, ni se le trata como incumplido.
- **Ticket sin compromiso de tiempo.** Aparece marcado como tal. **No se omite**: es exactamente el
  ticket que ningún vigilante revisa, y por eso hay que poder listarlo.
- **Ticket sin agente asignado.** Aparece con el agente ausente, no se omite.
- **Escalado sin autor humano.** Se presenta como acción del sistema, nunca con el autor en blanco ni
  atribuido a quien lo recibió.
- **Retraso de ingesta.** 5–15 segundos. Un ticket recién resuelto puede seguir apareciendo abierto.
  **No se compensa.**
- **Límite excedido.** `limit` sobre el máximo responde `400`, no se recorta en silencio.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los dos listados

- **FR-001**: El sistema MUST ofrecer un listado de **tickets** con la cuenta, el asunto, el estado,
  la prioridad, el tipo de incidencia, el agente asignado, la situación del compromiso de tiempo, la
  factura vinculada cuando exista y la fecha de registro. *(OT19, OP47, OP48, CU-O84)*
- **FR-002**: El listado de tickets MUST admitir filtros por **estado, situación del compromiso,
  prioridad, tipo de incidencia, agente asignado y existencia de factura vinculada**, combinables.
  Estos filtros son los que hacen innecesarios los cuatro endpoints separados que enumeraba el
  catálogo.
- **FR-003**: El sistema MUST ofrecer un listado de **escalados** con el ticket, el estado anterior,
  el nuevo, la fecha y el autor. *(OT20, OP50)*

#### La situación del compromiso de tiempo

- **FR-004**: El listado de tickets MUST distinguir las situaciones de compromiso que el dominio
  escribe, **importándolas de él** en lugar de enumerarlas aquí. Hoy son **cinco**: en curso, en
  riesgo, incumplido, **sin compromiso** y **cumplido**.

  > ⚠️ **Corregido el 2026-08-15 al implementar.** Esta spec decía «cuatro» y omitía `cumplido`, que
  > `resolver_ticket_service` escribe al resolver un ticket dentro de plazo. Implementar las cuatro
  > al pie de la letra habría dejado el filtro rechazando con `400` un valor legítimo —«no es
  > válido» cuando sí lo es— y **habría hecho imposible listar los tickets resueltos a tiempo**.
  > Por eso los valores se importan del dominio y una prueba comprueba que el enum del contrato
  > coincide con él.
- **FR-005**: Un ticket **sin compromiso de tiempo** MUST aparecer marcado como tal y **MUST NOT**
  omitirse ni presentarse como si estuviera en curso. Es el ticket que ningún vigilante revisa, y
  listarlo es el propósito de esta distinción.
- **FR-006**: Un ticket **sin clasificar** MUST aparecer sin plazo y sin situación de compromiso.
  El sistema **MUST NOT** atribuirle una.

#### Protección del contenido interno

- **FR-007**: El listado de escalados **MUST NOT** devolver el texto de los mensajes registrados en
  cada acción. Ese texto puede contener notas internas dirigidas al equipo de atención, y un listado
  táctico solo necesita saber qué ocurrió, cuándo y quién lo hizo.
- **FR-008**: El listado de escalados MUST estar restringido a los **roles de atención**. Un
  reportador no accede a él.

#### Acotamiento por quién atiende y quién reporta

- **FR-009**: Un usuario **con algún rol de atención** MUST obtener los tickets de todas las cuentas,
  y MUST poder filtrar por agente asignado o por cuenta.
- **FR-010**: Un usuario **sin ningún rol de atención** —sea Cliente o Partner de integración— MUST
  obtener únicamente los tickets de su propia cuenta, resueltos por su vínculo con ella.
- **FR-011**: El acotamiento **MUST decidirse por la ausencia de rol de atención**, no por la
  presencia de un rol concreto de reporte. Decidirlo por «ser Cliente» dejaría al Partner viendo
  tickets ajenos.
- **FR-012**: Un usuario que tenga a la vez un rol de reporte y uno de atención **MUST NOT** quedar
  acotado.
- **FR-013**: Un usuario sin ningún rol de reporte ni de atención MUST recibir una negativa en ambos
  listados.
- **FR-014**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato.

#### Autoridad departamental

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS.

- **FR-014a**: El **Gerente de Éxito del Cliente**, autoridad de Soporte, MUST acceder a los dos
  listados sin acotamiento por cuenta.
- **FR-014b**: Ese rol **MUST NOT** confundirse con el supervisor de soporte que ya existe: este
  último es el **destinatario operativo** de un escalado automático; el Gerente de Éxito del Cliente
  es la autoridad del departamento. Conviven, y sus permisos son independientes.
- **FR-014c**: La exención **MUST NOT** alcanzar a FR-007: el texto de los mensajes sigue sin
  consultarse, así que tampoco llega a él.
- **FR-014d**: De los dos listados, **tickets es bandeja de trabajo** del Agente —prioriza su cola—
  además de supervisión, y **escalados es supervisión** pura.

#### Naturaleza de los listados

- **FR-015**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla**.
- **FR-016**: El sistema MUST devolver el **nombre** de la cuenta, del agente, del servicio y del
  estado, no sus identificadores internos.
- **FR-017**: Los listados MUST ser de **solo lectura**.

#### Filtros, orden y paginación

- **FR-018**: El listado de **escalados** es de hechos del período y MUST aceptar rango de fechas
  **opcional**. El de **tickets** describe el estado actual y MUST rechazar un rango de fechas.
- **FR-019**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria.
- **FR-020**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  válidos.
- **FR-021**: Un `limit` superior al máximo MUST responder `400`. MUST NOT recortarse en silencio.

#### Calidad del dato

- **FR-022**: El sistema MUST identificar un escalado **automático como acción del sistema**, no
  atribuirlo a la persona que lo recibió ni presentarlo con el autor en blanco.
- **FR-023**: El sistema MUST tratar los valores centinela como ausencia: un ticket sin agente
  asignado, sin factura vinculada o sin prioridad se presentan como ausentes.

### Key Entities

- **Ticket de soporte**: la incidencia reportada, con su cuenta, asunto, estado, prioridad, tipo de
  incidencia, agente asignado, situación del compromiso de tiempo y factura vinculada cuando la
  hubiera. Alimenta FR-001.
- **Acción sobre un ticket**: cada movimiento registrado en su historia, con el tipo de acción, los
  estados de origen y destino, el autor y la fecha. Alimenta FR-003.
- **Compromiso de tiempo**: el plazo aplicable a un ticket según el plan de su cuenta y el tipo de
  incidencia. Determina las cuatro situaciones de FR-004.
- **Rol de atención**: la condición que distingue a quien resuelve tickets de quien los reporta.
  Determina el acotamiento (FR-009 a FR-012).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un reportador obtiene **el 100 %** de los tickets de su cuenta y **cero** de otras,
  verificable con dos cuentas con tickets simultáneos.
- **SC-002**: Un Partner de integración queda acotado **igual que un Cliente**, verificable con
  ambos roles sobre los mismos datos.
- **SC-003**: Un usuario con rol de reporte **y** de atención obtiene la cola completa: **cero**
  tickets ocultados.
- **SC-004**: **En ninguna** respuesta del listado de escalados aparece texto de mensaje,
  verificable inspeccionando la respuesta completa.
- **SC-005**: **El 100 %** de los escalados automáticos se identifica como acción del sistema y
  **ninguno** aparece atribuido a una persona.
- **SC-006**: **El 100 %** de los tickets sin compromiso de tiempo es listable, y ninguno aparece
  como si estuviera en curso.
- **SC-007**: Los dos listados devuelven su primera página en **menos de 2 segundos**.
- **SC-008**: Recorrer un listado por páginas devuelve **cada fila exactamente una vez**.
- **SC-009**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**.

---

## Assumptions

- **El contrato común está vigente** y la capa transversal de los cuatro módulos previos se
  reutiliza. Esta spec **no** vuelve a decidirla.
- **El criterio de pertenencia es el amplio.** La cuenta de un usuario se resuelve por su vínculo con
  ella, no por ser su administrador local. Es el criterio que la pantalla operativa de soporte ya
  usa, y el listado debe usar el mismo para no restringir por informe lo que la pantalla permite.
- **El acotamiento reutiliza la condición ya implementada** en el módulo operativo, que decide por
  ausencia de rol de atención. No se reimplementa ni se sustituye por una comparación de roles.
- **Los roles son los reales del sistema.** Administrador, Agente de Soporte, Cliente y Partner de
  integración existen en `.specify/docs/actors.md`.
- **Un ticket sin clasificar no tiene plazo.** Está verificado: el compromiso se asigna al
  clasificar, y antes de eso no hay contador.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Cumplimiento de SLA, rendimiento por agente, SLA desglosado por plan | Son agregaciones → compuestos |
| Evolución temporal del incumplimiento, tasa de escalado automático | Son agregaciones → compuestos |
| Carga entrante frente a resuelta, reincidencia por cliente y servicio | Son agregaciones → compuestos |
| Tickets por servicio afectado y su tiempo de resolución | Es una agregación → compuesto |
| **El texto de los mensajes y las notas internas** | ⛔ **Excluido a propósito.** Un listado táctico necesita saber qué ocurrió, cuándo y quién lo hizo, no la prosa. Al no exponer el texto, el riesgo de filtrar una nota interna al reportador **no llega a plantearse**, en vez de depender de un filtro que alguien podría olvidar al añadir un campo. |
| Configuración de SLA por plan y tipo | Ya construido |
| Cualquier pantalla o tablero | El frontend se decide por separado. |
