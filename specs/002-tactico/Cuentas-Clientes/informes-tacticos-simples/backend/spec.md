# Feature Specification: Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Feature Branch**: `informes-tacticos-simples-cuentas-clientes`

**Created**: 2026-08-14

**Status**: Implemented

**Input**: User description: "Informes tácticos simples de Cuentas y Clientes — 8 listados llanos de solo lectura (backend) que satisfacen OT04, OT17 y OT18, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Los ocho listados de esta spec son **consultas llanas de solo lectura**: una tabla, filtros, orden y
paginación. No agregan, no calculan ratios y no construyen series temporales. Todo lo que agregue
sobre este mismo departamento —tiempo de onboarding, embudo de abandono, churn por cohorte— es
**compuesto** y queda expresamente fuera.

Sirven al nivel táctico para mirar el dato operativo tal como está, sin transformarlo. Hoy ese dato
solo es alcanzable navegando pantalla por pantalla del módulo operativo.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común de los 66 listados. Fija ruta,
  envelope, paginación, filtros, permisos y las reglas obligatorias de Pinot. **Lo que allí se
  define no se repite aquí.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §2 — el catálogo del que salen
  estos ocho, con su trazabilidad al marco.
- `.specify/docs/architecture/api-standards.md` — convenciones REST.
- `.specify/docs/actors.md` — roles reales del sistema.

**Alcance:** solo backend. La ubicación de cada listado en pantalla es una decisión posterior y
deliberadamente separada: ningún endpoint de esta spec asume un tablero concreto.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vigilar quién tiene acceso al sistema y con qué rol (Priority: P1)

Como Administrador, quiero ver en un listado quiénes tienen acceso al sistema, con qué rol, qué
sesiones están abiertas ahora mismo y qué credenciales siguen siendo temporales, para verificar que
el control de acceso por rol se está cumpliendo sin tener que abrir la ficha de cada usuario.

**Why this priority**: Cuentas y Clientes es la puerta de entrada de toda la plataforma — sin este
módulo ningún otro opera. OT18 es además el objetivo táctico con más listados de esta spec (cuatro
de ocho), todos de estado actual, lo que lo convierte en el mejor punto para fijar el patrón antes
de replicarlo.

**Independent Test**: Se puede solicitar cada uno de los cuatro listados de forma aislada y obtener
la respuesta correcta, sin que existan los listados de OT04 ni de OT17.

**Acceptance Scenarios**:

1. **Given** existen usuarios activos con distintos roles asignados, **When** se solicita el listado
   de usuarios por rol, **Then** el sistema devuelve cada usuario con su nombre y el **nombre** de
   su rol, nunca el identificador interno.
2. **Given** un usuario tiene dos roles asignados, **When** se solicita el listado, **Then** el
   usuario aparece con ambos roles, sin duplicar la fila de forma que parezca dos usuarios distintos.
3. **Given** hay sesiones abiertas y sesiones ya cerradas, **When** se solicita el listado de
   sesiones activas, **Then** solo aparecen las abiertas, con el usuario, el navegador y la hora de
   inicio.
4. **Given** un usuario tiene credencial en estado temporal pendiente de cambio obligatorio,
   **When** se solicita el listado de credenciales temporales, **Then** ese usuario aparece; si ya
   cambió su contraseña, no aparece.
5. **Given** existen accesos técnicos de infraestructura, **When** el Director Tecnológico solicita
   el listado, **Then** obtiene los usuarios de servidor con sus roles técnicos y el mapeo al rol de
   negocio correspondiente.
6. **Given** un Operador de Emergencias autenticado, **When** solicita cualquiera de estos cuatro
   listados, **Then** el sistema responde `403` sin revelar el contenido.

---

### User Story 2 - Seguir la incorporación de clientes nuevos (Priority: P2)

Como Administrador, quiero ver qué solicitudes de alta están esperando mi aprobación y qué clientes
ya aprobados se quedaron a medias en su incorporación, para actuar sobre los que llevan más tiempo
detenidos antes de que abandonen.

**Why this priority**: Es la bandeja de trabajo que hoy obliga a entrar pantalla por pantalla.
Aporta valor inmediato y es independiente del resto, pero afecta a menos volumen de dato que el
control de acceso.

**Independent Test**: Se puede solicitar los dos listados de forma aislada y obtener la respuesta
correcta, sin que existan los de OT18 ni los de OT17.

**Acceptance Scenarios**:

1. **Given** hay solicitudes de alta en estado pendiente, **When** se solicita el listado, **Then**
   el sistema devuelve cada solicitud con su razón social, tipo de organización, fecha de solicitud
   y **días transcurridos** desde entonces.
2. **Given** una solicitud ya fue aprobada o rechazada, **When** se solicita el listado de
   pendientes, **Then** esa solicitud no aparece.
3. **Given** un cliente aprobado tiene etapas de incorporación sin completar, **When** se solicita
   el listado de onboarding incompleto, **Then** aparece una fila por cada etapa pendiente, con el
   nombre de la etapa y el cliente al que pertenece.
4. **Given** un cliente completó todas sus etapas, **When** se solicita el listado, **Then** ese
   cliente no aparece.
5. **Given** se filtra por antigüedad mínima en días, **When** se solicita el listado, **Then** solo
   aparecen las solicitudes o incorporaciones que superan ese umbral.

---

### User Story 3 - Revisar el estado del parque de cuentas (Priority: P3)

Como Administrador, quiero ver el estado en que se encuentra cada cuenta cliente y qué
transferencias de propiedad se han producido, para tener a la vista la situación del conjunto sin
consultar cuenta por cuenta.

**Why this priority**: Completa la cobertura de OT17 y es la base sobre la que después se construirán
los compuestos de churn y antigüedad, pero por sí solo es el de menor urgencia operativa.

**Independent Test**: Se puede solicitar los dos listados de forma aislada, sin que existan los de
OT18 ni los de OT04.

**Acceptance Scenarios**:

1. **Given** existen cuentas activas, suspendidas y dadas de baja, **When** se solicita el listado
   de cuentas por estado, **Then** aparecen todas con su estado actual y su fecha de inicio de
   contrato.
2. **Given** una cuenta fue dada de baja de forma lógica, **When** se solicita el listado, **Then**
   la cuenta **sigue apareciendo** con estado de baja, porque la baja no borra la fila.
3. **Given** se filtra por un estado concreto, **When** se solicita el listado, **Then** solo
   aparecen las cuentas en ese estado.
4. **Given** hubo transferencias de propiedad en el período, **When** se solicita el listado,
   **Then** cada transferencia muestra la cuenta, el **nombre** del propietario anterior, el del
   nuevo y la fecha.
5. **Given** no se indica período, **When** se solicita el listado de transferencias, **Then** el
   sistema devuelve el histórico completo paginado, sin exigir un rango de fechas.

---

### Edge Cases

- **Resultado vacío.** Un listado sin filas devuelve `200` con `data: []`, nunca `404`. Que no haya
  solicitudes pendientes es una respuesta legítima y buena noticia, no un error.
- **Retraso de ingesta.** Una escritura tarda entre 5 y 15 segundos en ser visible. Un listado
  consultado justo después de aprobar una solicitud puede seguir mostrándola. **No se compensa** con
  reintentos ni esperas artificiales.
- **Valores centinela.** Los campos opcionales sin valor no llegan como nulos: llegan como el texto
  `'null'`, el número `0` o una fecha mínima. Un campo ausente se presenta como ausente, nunca como
  la cadena literal `null` ni como una fecha del año 1970.
- **Cursor inestable.** Sin un orden determinista, la paginación repite o salta filas. Todo listado
  declara un desempate por clave primaria.
- **Rol sin usuarios / usuario sin rol.** Un rol sin usuarios asignados simplemente no aporta filas.
  Un usuario sin ningún rol **sí debe aparecer**, marcado como sin rol: es una anomalía que el
  Administrador necesita ver, no una fila que ocultar.
- **Cuenta sin administrador local.** Una cuenta cuyo `admin_local_id` no resuelve a un usuario
  vivo aparece en el listado con el propietario marcado como no resuelto, no se omite la fila.
- **Límite excedido.** Un `limit` mayor que el máximo responde `400` indicando el máximo permitido.
  No se recorta en silencio.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los ocho listados

- **FR-001**: El sistema MUST ofrecer un listado de **solicitudes de alta pendientes de aprobación**,
  con razón social, tipo de organización, fecha de solicitud y días transcurridos. *(OT04, OP04)*
- **FR-002**: El sistema MUST ofrecer un listado de **clientes con incorporación incompleta**, con
  una fila por etapa pendiente, indicando cliente y nombre de la etapa. *(OT04, OP05)*
- **FR-003**: El sistema MUST ofrecer un listado de **cuentas cliente por estado**, incluyendo las
  dadas de baja, con su estado actual y fecha de inicio de contrato. *(OT17, OP07)*
- **FR-004**: El sistema MUST ofrecer un listado de **transferencias de propiedad**, con la cuenta,
  el propietario anterior, el nuevo y la fecha. *(OT17, CU-O15)*
- **FR-005**: El sistema MUST ofrecer un listado de **usuarios y sus roles asignados**, con el
  nombre del rol. *(OT18, OP02)*
- **FR-006**: El sistema MUST ofrecer un listado de **sesiones actualmente abiertas**, con usuario,
  navegador y hora de inicio. *(OT18, CU-O05)*
- **FR-007**: El sistema MUST ofrecer un listado de **credenciales en estado temporal pendientes de
  cambio obligatorio**. *(OT18, CU-O04)*
- **FR-008**: El sistema MUST ofrecer un listado de **accesos técnicos de infraestructura** y su
  mapeo a roles de negocio. *(OT18, CU-O08)*

#### Naturaleza de los listados

- **FR-009**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla de hechos o
  entidad**. Si un listado requiriera agregación o una segunda tabla de hechos, MUST reclasificarse
  como compuesto y salir de esta spec.
- **FR-010**: El sistema MUST resolver los identificadores contra su tabla catálogo y devolver el
  **nombre**, no el número. Esto aplica a rol, etapa, estado, tipo de organización y usuario.
- **FR-011**: Los listados MUST ser de **solo lectura**. Ninguno acepta métodos de escritura.

#### Filtros, orden y paginación

- **FR-012**: Los listados de **estado actual** —FR-001, FR-002, FR-003, FR-005, FR-006, FR-007,
  FR-008— MUST rechazar con `400` un filtro de rango de fechas: describen la situación de ahora, no
  un intervalo.
- **FR-013**: El listado de **hechos del período** —FR-004— MUST aceptar un rango de fechas
  **opcional**; omitirlo devuelve el histórico completo paginado.
- **FR-014**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria, para que la paginación por cursor no repita ni salte filas.
- **FR-015**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  valores válidos. MUST NOT ignorarse en silencio.
- **FR-016**: Un `limit` superior al máximo permitido MUST responder `400`. MUST NOT recortarse
  en silencio.

#### Acceso

- **FR-017**: Todos los listados MUST exigir autenticación. Ninguno es accesible de forma anónima.
- **FR-018**: FR-001 a FR-007 MUST estar restringidos al **Administrador**, que es quien ejerce esas
  mismas acciones en el módulo operativo.
- **FR-019**: FR-008 MUST estar restringido al **Director Tecnológico**, coherente con CU-O08, más
  el Administrador por su función de supervisión.
- **FR-020**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato. Un informe no puede exponer registros que su solicitante no podría ver navegando.

#### Autoridad departamental — **el caso singular de la serie**

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS.

**Este departamento no tiene autoridad de negocio.** El §5.1 le asigna únicamente el Director
Tecnológico, y con alcance limitado: *«en Cuentas y Clientes, el Director Tecnológico gobierna
únicamente la capa de accesos técnicos, no el departamento completo»*.

- **FR-020a**: El Director Tecnológico MUST acceder **solo al listado de accesos técnicos**
  (FR-008). Ampliarlo a los otros siete contradiría el §5.1.
- **FR-020b**: Los siete listados restantes **no tienen autoridad por encima del Administrador**, que
  es a la vez responsable operativo del departamento y su única visión de conjunto. **No se asigna
  ninguna otra jefatura**: hacerlo sería inventar una que el SRS no reconoce.
- **FR-020c**: De los ocho listados, **solicitudes de alta, incorporación incompleta, sesiones
  abiertas y credenciales temporales son bandejas de trabajo** del Administrador; cuentas por estado,
  transferencias y accesos técnicos son supervisión; usuarios y roles sirve a ambas.

> **Anotado como decisión pendiente.** Que este departamento carezca de autoridad de negocio puede
> ser intencional —el Administrador *es* el responsable— o puede faltar un cargo en el §5.1. Queda
> en `decisiones-pendientes.md` para que se decida, no se resuelve aquí.

#### Calidad del dato

- **FR-021**: El sistema MUST tratar los valores centinela como ausencia de valor al presentarlos.
  MUST NOT devolver la cadena literal `'null'`, el `0` de una métrica vacía ni una fecha mínima como
  si fueran datos reales.
- **FR-022**: El sistema MUST NOT usar una comprobación de nulidad como filtro de completitud, dado
  que la base de datos analítica no almacena nulos y esa comprobación es siempre cierta.
- **FR-023**: Un usuario sin ningún rol asignado MUST aparecer en FR-005 marcado como tal, en lugar
  de ser omitido.

### Key Entities

- **Cuenta cliente**: la organización dada de alta. Conserva razón social, tipo, estado y fecha de
  inicio de contrato incluso tras la baja lógica. Alimenta FR-001, FR-003.
- **Etapa de incorporación**: cada paso del onboarding guiado de una cuenta, con su marca de
  completado. Alimenta FR-002.
- **Transferencia de propiedad**: el cambio de titular de una cuenta, con propietario anterior,
  nuevo y fecha. Alimenta FR-004.
- **Usuario y su asignación de rol**: la relación entre una persona y los roles que ejerce.
  Alimenta FR-005, FR-023.
- **Sesión**: cada acceso al sistema, con su estado, navegador y horas de inicio y cierre.
  Alimenta FR-006.
- **Credencial**: el estado de la contraseña de un usuario, incluido el estado temporal que fuerza
  el cambio. Alimenta FR-007.
- **Acceso técnico de infraestructura**: los usuarios de servidor, sus roles técnicos y el mapeo a
  roles de negocio. Alimenta FR-008.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Administrador obtiene la lista completa de solicitudes de alta pendientes en **una
  sola consulta**, frente a las múltiples navegaciones que exige hoy el módulo operativo.
- **SC-002**: Los ocho listados devuelven su primera página en **menos de 2 segundos** con el
  volumen de datos actual.
- **SC-003**: **El 100 %** de los identificadores internos que llegan al consumidor viene resuelto a
  su nombre legible, verificable revisando la respuesta de los ocho listados.
- **SC-004**: **Ningún** listado devuelve valores centinela presentados como datos reales,
  verificable con registros que tengan campos opcionales vacíos.
- **SC-005**: Recorrer un listado completo por páginas devuelve **cada fila exactamente una vez**,
  sin repeticiones ni omisiones, verificable comparando el recorrido paginado con el total.
- **SC-006**: Un usuario sin el rol requerido recibe una negativa en **el 100 %** de los ocho
  listados, sin que ninguna fila se filtre en la respuesta.
- **SC-007**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**,
  en los ocho casos.

---

## Assumptions

- **El contrato común está vigente.** Ruta, envelope, formato de error, paginación por cursor,
  límites y reglas de Pinot se heredan de `contrato-informes-simples.md` y no se redefinen aquí.
- **Se reutiliza la infraestructura táctica existente.** El envelope, el parseo de período y el
  patrón de clase de permiso de `apps/informes_tacticos/` se aprovechan; el parseo de período se
  extiende para admitir rango opcional, que hoy es obligatorio.
- **Los roles son los reales del sistema.** Administrador y Director Tecnológico existen en
  `.specify/docs/actors.md`. No se introduce ningún rol nuevo.
- **El permiso espeja la pantalla operativa.** Ante duda sobre quién puede ver un listado, se
  concede al mismo rol que ya ejecuta esa acción en el módulo operativo. Es el criterio más
  restrictivo disponible y evita abrir una puerta trasera.
- **La baja de cuenta es lógica.** El listado de cuentas por estado incluye las dadas de baja
  porque la fila sobrevive con su historial; esto ya está verificado en el sistema real.
- **El volumen actual cabe en una consulta paginada.** No se prevé materialización ni caché para
  estos ocho listados. Si el volumen creciera hasta hacerlo necesario, dejarían de ser simples.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance, igual que en el contrato.

---

## Fuera de alcance

Lo siguiente pertenece al mismo departamento pero **no** a esta spec:

| Excluido | Por qué |
|---|---|
| Tiempo de onboarding, embudo de abandono, tasa de aprobación | Son agregaciones → compuestos |
| Churn por cohorte, antigüedad media de cuenta, cuentas en riesgo | Son agregaciones → compuestos |
| Sesiones concurrentes por franja, roles incompatibles | Son agregaciones → compuestos |
| **Invitaciones de onboarding reenviadas** | **No hay dato.** El reenvío solo deja traza en el log de aplicación (`audit_service.log_reenvio_invitacion` escribe con el logger); ninguna tabla lo registra. No es construible sin persistir antes ese evento. |
| **Usuarios por cliente frente al tope de su plan** | **Reclasificado a compuesto.** Exige contar usuarios por cliente y cruzar con los límites del plan: agregación más segunda tabla. |
| Intentos de acceso fallidos | Se registran en el log de aplicación, no en tabla consultable. Además es monitoreo de servicio, no OT18 — ver catálogo §2. |
| Cualquier pantalla o tablero | El frontend se decide por separado, después. |
