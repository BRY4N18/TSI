# Feature Specification: Informes Tácticos Simples de Suscripciones y Facturación (Backend)

**Feature Branch**: `informes-tacticos-simples-suscripciones-facturacion`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos simples de Suscripciones y Facturación — listados llanos de solo lectura (backend) que satisfacen OT05, OT06 y OT07, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Cuatro listados llanos de solo lectura sobre el contrato comercial recurrente. Como en los dos
módulos anteriores, no agregan: una tabla, filtros, orden y paginación. El MRR, la retención neta de
ingresos, la efectividad del cobro por reintento y los movimientos de plan con delta de ingreso son
**compuestos** y quedan fuera.

**Lo que distingue a este departamento de los dos anteriores**, y la razón de abordarlo en tercer
lugar:

1. **El acotamiento es por organización, no por persona.** En Ventas y CRM el titular era el propio
   solicitante. Aquí un usuario pregunta y el resultado se acota a **la cuenta cliente a la que
   pertenece**, con un salto de indirección en medio.
2. **Es el primer departamento mayoritariamente de hechos del período.** Facturas emitidas, cobros
   fallidos y cancelaciones son sucesos fechados, no estados de ahora.
3. **Es donde vive el dato más delicado del sistema.** El método de pago guarda el token con el que
   se cobra al cliente. No es una credencial que haya que romper: es la capacidad de cobrar.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común. **No se repite aquí.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §4 — catálogo y trazabilidad.
- Módulos previos: `Cuentas-Clientes/` (capa transversal) y `Ventas-CRM/` (acotamiento). Se
  reutilizan y **no se vuelven a decidir**.

**Alcance:** solo backend.

---

## Nota de alcance: cuatro listados a partir de diez filas del catálogo

| Filas del catálogo | Resolución |
|---|---|
| Clientes por plan contratado · Suscripciones que vencen en N días · Cuentas suspendidas por impago · Reducciones aprobadas pendientes de aplicar · Cancelaciones con motivo | **Un solo listado de suscripciones con filtros.** Las cinco son la misma consulta sobre la misma tabla cambiando el filtro. |
| Facturas del período con estado · Facturas vencidas e impagas con días de mora | **Un solo listado de facturas con filtros.** |
| Solicitudes de cambio de plan pendientes | Listado propio |
| **Clientes sin método de pago activo** | ⚠️ **Reclasificado a compuesto** — ver abajo |
| Planes vigentes del catálogo | Ya construido (pantalla de planes) |

**Se añade un listado no previsto en el catálogo**: métodos de pago vigentes, con los próximos a
expirar. Es la mitad simple de la fila que resultó compuesta, y responde de forma preventiva la
misma preocupación: una tarjeta que caduca la semana que viene es un cobro que va a fallar.
Queda marcado como **criterio propio**, no como exigencia del marco.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el estado comercial de las suscripciones (Priority: P1)

Como Administrador, quiero consultar las suscripciones filtrando por estado, plan, proximidad de
vencimiento o cambio de plan pendiente de aplicar, para saber qué cuentas necesitan atención antes
de que el problema se materialice. Como Cliente, quiero ver la mía sin ver las de nadie más.

**Why this priority**: Responde cinco de las diez preguntas del catálogo y es el listado donde el
acotamiento por organización tiene consecuencia. Si esta historia funciona, la generalización del
acotamiento queda validada para los departamentos que faltan.

**Independent Test**: Consultar el listado con cada filtro, con dos roles distintos, sin que existan
los otros tres listados.

**Acceptance Scenarios**:

1. **Given** existen suscripciones de varias cuentas cliente, **When** un Cliente consulta el
   listado, **Then** obtiene **únicamente la de su propia cuenta**.
2. **Given** un Cliente, **When** consulta pidiendo expresamente la suscripción de otra cuenta,
   **Then** el sistema responde `403` y **no devuelve ninguna fila**.
3. **Given** un Administrador, **When** consulta el listado, **Then** obtiene las suscripciones de
   **todas** las cuentas, y puede filtrar por una concreta.
4. **Given** suscripciones activas, suspendidas y canceladas, **When** se filtra por estado,
   **Then** solo aparecen las de ese estado, con el **nombre** del plan y de la cuenta.
5. **Given** una suscripción con una reducción de plan aprobada pendiente de aplicarse al cierre del
   ciclo, **When** se filtra por cambio programado, **Then** esa suscripción aparece indicando el
   plan al que pasará y la fecha en que se aplicará.
6. **Given** una suscripción sin ningún cambio programado, **When** se filtra por cambio programado,
   **Then** esa suscripción **no aparece**.
7. **Given** suscripciones que vencen en distintas fechas, **When** se filtra por días hasta el
   vencimiento, **Then** solo aparecen las que vencen dentro de ese plazo.
8. **Given** suscripciones canceladas en distintas fechas, **When** se acota por fecha de
   cancelación, **Then** solo aparecen las canceladas en ese rango, cada una con su motivo.

---

### User Story 2 - Seguir la facturación y la salud del cobro (Priority: P2)

Como Administrador, quiero ver las facturas emitidas con su estado de pago y cuáles están vencidas
e impagas, y qué métodos de pago están a punto de caducar, para actuar sobre la mora antes de que
suspenda cuentas. Como Cliente, quiero ver mis propias facturas.

**Why this priority**: Es donde el dinero se hace visible y donde la mora se anticipa. Depende de que
existan facturas emitidas, así que va después del estado de las suscripciones, pero es lo que aporta
valor económico más directo.

**Independent Test**: Consultar los dos listados de forma aislada, con y sin rango de fechas, sin que
existan los de las otras historias.

**Acceptance Scenarios**:

1. **Given** hay facturas emitidas en el período, **When** se consulta el listado, **Then** cada una
   muestra la cuenta, el número de factura, el período facturado, el importe total, el estado de pago
   y la fecha de vencimiento.
2. **Given** no se indica período, **When** se consulta el listado de facturas, **Then** el sistema
   devuelve el histórico completo paginado.
3. **Given** hay facturas vencidas e impagas, **When** se filtra por vencidas, **Then** cada una
   muestra los **días de mora** transcurridos desde su vencimiento.
4. **Given** una factura marcada como en disputa, **When** aparece en el listado, **Then** su estado
   lo refleja, porque una factura en disputa está excluida del cobro automático y no debe leerse como
   simplemente impaga.
5. **Given** un Cliente consulta las facturas, **When** obtiene el resultado, **Then** solo ve las de
   su propia cuenta.
6. **Given** existen métodos de pago registrados, **When** se consulta ese listado, **Then** cada uno
   muestra la cuenta, el tipo, los últimos dígitos y su fecha de expiración, **y en ningún caso el
   dato con el que se ejecuta el cobro**.
7. **Given** un método de pago caduca dentro del plazo consultado, **When** se filtra por próximos a
   expirar, **Then** aparece indicando los días que le quedan.
8. **Given** un método de pago fue reemplazado, **When** se consulta el listado de vigentes,
   **Then** el anterior **no aparece** como vigente, aunque su registro siga existiendo.

---

### User Story 3 - Atender las solicitudes de cambio de plan (Priority: P3)

Como Administrador, quiero ver qué solicitudes de cambio de plan esperan mi decisión y cuánto llevan
esperando, para resolverlas sin que el cliente se quede bloqueado.

**Why this priority**: Es una bandeja de trabajo acotada, valiosa pero de menor volumen que las dos
anteriores.

**Independent Test**: Consultar el listado de forma aislada, sin que existan los otros tres.

**Acceptance Scenarios**:

1. **Given** hay solicitudes pendientes de resolución, **When** se consulta el listado, **Then** cada
   una muestra la cuenta, el **nombre** del plan actual, el del plan solicitado, la fecha de
   solicitud y los días que lleva esperando.
2. **Given** una solicitud ya fue aprobada o rechazada, **When** se filtra por pendientes,
   **Then** esa solicitud no aparece.
3. **Given** una solicitud rechazada, **When** se filtra por rechazadas, **Then** aparece con su
   motivo de rechazo y el nombre de quien la resolvió.

---

### Edge Cases

- **Resultado vacío.** `200` con `data: []`, nunca `404`. Que no haya facturas vencidas es una buena
  noticia, no un error.
- **Cliente sin suscripción.** Un usuario de una cuenta que aún no ha contratado obtiene un listado
  vacío, no un error ni el listado completo.
- **Cuenta suspendida.** Un cliente con la suscripción suspendida **conserva el acceso** a sus
  propios listados de facturación: es precisamente donde ve lo que debe regularizar.
- **Factura en disputa.** No es lo mismo que impaga. Se distingue en el estado, porque está excluida
  del cobro automático mientras se resuelve.
- **Método de pago reemplazado.** El anterior queda inactivo, no se borra. El listado de vigentes lo
  excluye; el registro sigue existiendo.
- **Suscripción sin cambio programado.** Se presenta como ausencia de cambio, nunca como un plan con
  identificador cero.
- **Retraso de ingesta.** 5–15 segundos entre escritura y visibilidad. Una factura recién cobrada
  puede seguir apareciendo como pendiente. **No se compensa.**
- **Límite excedido.** `limit` sobre el máximo responde `400`, no se recorta en silencio.
- **Cursor inestable.** Sin orden determinista la paginación repite o salta filas.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los cuatro listados

- **FR-001**: El sistema MUST ofrecer un listado de **suscripciones** con la cuenta, el plan, el
  estado, el precio, el inicio y fin del ciclo, el motivo de cancelación cuando exista, y el cambio
  de plan programado cuando exista. *(OT05/OT07, OP15, OP17, CU-O34, CU-O35, CU-O37)*
- **FR-002**: El listado de suscripciones MUST admitir filtros por **estado, plan, días hasta el
  vencimiento, existencia de cambio programado y rango de fecha de cancelación**, combinables. Estos
  filtros son los que hacen innecesarios los cinco endpoints separados que enumeraba el catálogo.
- **FR-003**: El sistema MUST ofrecer un listado de **facturas** con la cuenta, el número, el período
  facturado, el importe, el estado de pago, la fecha de emisión, la de vencimiento y los días de mora
  cuando esté vencida e impaga. *(OT06, OP16, CU-O38)*
- **FR-004**: El sistema MUST ofrecer un listado de **solicitudes de cambio de plan** con la cuenta,
  el plan actual, el solicitado, el estado, los días de espera y, si fue resuelta, quién la resolvió
  y con qué motivo. *(OT07, CU-O34)*
- **FR-005**: El sistema MUST ofrecer un listado de **métodos de pago vigentes**, con la cuenta, el
  tipo, los últimos dígitos y la fecha de expiración, filtrable por proximidad de caducidad.
  *(OT06 — criterio propio, ver Nota de alcance)*

#### Protección del medio de cobro

- **FR-006**: El sistema **MUST NOT** exponer, en ninguna respuesta y bajo ninguna circunstancia, el
  identificador con el que se ejecuta el cobro contra la pasarela de pagos. Los últimos dígitos de la
  tarjeta son suficientes para identificar el método ante el usuario.
- **FR-007**: El listado de métodos de pago MUST devolver **únicamente los vigentes**. Un método
  reemplazado conserva su registro pero no se presenta como disponible.

#### Acotamiento por organización

- **FR-008**: Un **Administrador** MUST obtener los registros de todas las cuentas cliente, y MUST
  poder filtrar por una concreta.
- **FR-009**: Un usuario perteneciente a una cuenta cliente MUST obtener **únicamente los registros
  de su propia cuenta**, resueltos a partir de su pertenencia, sin necesidad de indicarla.
- **FR-010**: Un usuario que pida expresamente los registros de **otra cuenta** MUST recibir una
  negativa. **MUST NOT** devolvérsele los de su propia cuenta como si su petición se hubiera
  atendido.
- **FR-011**: Una cuenta con la suscripción **suspendida** MUST conservar el acceso a sus propios
  listados de facturación: es donde el cliente ve lo que debe regularizar.
- **FR-012**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato.

#### Autoridad departamental — **repartida por materia**

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS.

Este departamento **no tiene una jefatura única**: el SRS reparte la autoridad por materia, y los
listados lo respetan.

- **FR-012a**: El **Director de Estrategia**, que decide catálogo y precios, MUST acceder a los
  listados de **suscripciones** y **solicitudes de cambio de plan**, sin acotamiento por cuenta.
- **FR-012b**: El **Director Financiero**, que responde por el resultado económico, MUST acceder a
  los listados de **facturas** y **métodos de pago**, sin acotamiento por cuenta.
- **FR-012c**: Ninguna de las dos autoridades MUST recibir acceso a los listados de la otra materia
  por defecto: el reparto refleja qué decisión alimenta cada informe, no una jerarquía.
- **FR-012d**: La exención de acotamiento **MUST NOT** alcanzar a FR-006: el identificador con el que
  se ejecuta el cobro sigue sin exponerse a nadie, tenga el cargo que tenga.
- **FR-012e**: De los cuatro listados, **solicitudes de cambio de plan y métodos de pago son bandejas
  de trabajo** del Administrador —resolver y prevenir el cobro fallido—; suscripciones y facturas
  sirven a ambas capas.

#### Naturaleza de los listados

- **FR-013**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla**. Si requiriera
  agregación o combinar dos tablas de hechos, MUST reclasificarse como compuesto.
- **FR-014**: El sistema MUST devolver el **nombre** del plan, del estado y de la cuenta, no sus
  identificadores internos.
- **FR-015**: Los listados MUST ser de **solo lectura**.

#### Filtros, orden y paginación

- **FR-016**: El listado de **facturas** es de hechos del período y MUST aceptar rango de fechas
  **opcional**. Los listados de **suscripciones**, **solicitudes** y **métodos de pago** describen el
  estado actual y MUST rechazar un rango genérico de fechas; el filtro por fecha de cancelación de
  FR-002 es un filtro de columna, no un período.
- **FR-017**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria.
- **FR-018**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  válidos.
- **FR-019**: Un `limit` superior al máximo MUST responder `400`. MUST NOT recortarse en silencio.

#### Calidad del dato

- **FR-020**: El sistema MUST presentar la **ausencia de cambio de plan programado** como ausencia,
  nunca como un plan con identificador cero. El filtro de cambios programados MUST distinguir el
  valor que representa «sin cambio» de un plan real.
- **FR-021**: El sistema MUST distinguir una factura **en disputa** de una simplemente impaga, porque
  la primera está excluida del cobro automático mientras se resuelve.
- **FR-022**: El sistema MUST tratar los valores centinela como ausencia de valor: una suscripción sin
  fecha de cancelación, un motivo vacío o un resolutor ausente se presentan como ausentes.

### Key Entities

- **Suscripción**: el contrato vigente entre una cuenta y un plan, con su estado, precio, ciclo,
  motivo de cancelación y el plan al que pasará si hay un cambio programado. Alimenta FR-001.
- **Factura**: cada cobro o intento de cobro sobre una suscripción, con su período, importe, estado
  de pago y vencimiento. Alimenta FR-003.
- **Solicitud de cambio de plan**: la petición de subir o bajar de plan, con su estado, resolutor y
  motivo de rechazo. Alimenta FR-004.
- **Método de pago**: el medio con el que se cobra a una cuenta, del que solo se exponen tipo,
  últimos dígitos y caducidad. Alimenta FR-005, FR-006.
- **Cuenta cliente**: la organización titular. Determina qué ve cada solicitante (FR-008 a FR-011).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario de una cuenta cliente obtiene **el 100 %** de los registros de su cuenta y
  **cero** de otras cuentas, verificable con dos cuentas con facturación simultánea.
- **SC-002**: **Ningún** intento de consultar los registros de otra cuenta devuelve datos.
- **SC-003**: **En ninguna** de las respuestas de los cuatro listados aparece el identificador con el
  que se ejecuta el cobro, verificable inspeccionando la respuesta completa.
- **SC-004**: Las cinco preguntas que el catálogo planteaba por separado sobre suscripciones se
  responden con **un solo listado** aplicando filtros.
- **SC-005**: **El 100 %** de las suscripciones sin cambio de plan programado se presenta como
  ausencia de cambio, y **ninguna** aparece en el filtro de cambios programados.
- **SC-006**: Los cuatro listados devuelven su primera página en **menos de 2 segundos**.
- **SC-007**: Recorrer un listado por páginas devuelve **cada fila exactamente una vez**.
- **SC-008**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**.

---

## Assumptions

- **El contrato común está vigente** y la capa transversal de los dos módulos previos se reutiliza:
  período opcional, paginación por cursor, envelope con acotamiento declarado, y el resolutor de
  titularidad. Esta spec **no** los vuelve a decidir.
- **El acotamiento por organización generaliza el resolutor existente.** El módulo operativo ya
  resuelve la pertenencia de un usuario a su cuenta antes de dejarle ver su facturación; los
  listados heredan ese comportamiento, ampliándolo para que el Administrador vea todas las cuentas.
- **Los roles son los reales del sistema.** Administrador, Cliente y Proveedor existen en
  `.specify/docs/actors.md`. No se introduce ninguno nuevo.
- **La cancelación siempre tiene motivo.** El módulo operativo lo exige al cancelar, así que el
  listado puede mostrarlo sin tratarlo como opcional.
- **Un método de pago reemplazado se desactiva, no se borra.** Está verificado en el sistema real.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance — y aquí con más razón, por
  tratarse de datos económicos por cuenta.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| MRR y su variación, retención neta de ingresos, ingresos por período y plan | Son agregaciones → compuestos |
| Tasa de cobro al primer intento, efectividad del dunning, tasa de renovación | Son agregaciones → compuestos |
| Movimientos de plan con delta de ingreso, tasa de suspensión y reactivación | Son agregaciones → compuestos |
| Distribución de la cartera por plan, utilización real de los límites | Son agregaciones → compuestos |
| **Clientes sin método de pago activo** | ⚠️ **Reclasificado a compuesto.** Exige restar de todas las cuentas con suscripción aquellas que tienen método vigente: una diferencia de conjuntos entre dos tablas, que la base analítica no resuelve en una consulta. El listado de métodos vigentes de FR-005 cubre la misma preocupación por el lado positivo. |
| Catálogo de planes vigentes | Ya construido |
| Cualquier pantalla o tablero | El frontend se decide por separado. |
