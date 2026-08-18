# Feature Specification: Informes Tácticos Simples de Ventas y CRM (Backend)

**Feature Branch**: `informes-tacticos-simples-ventas-crm`

**Created**: 2026-08-14

**Status**: Implemented

**Input**: User description: "Informes tácticos simples de Ventas y CRM — listados llanos de solo lectura (backend) que satisfacen OT01, OT02 y OT03, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Cuatro listados llanos de solo lectura sobre el departamento Ventas y CRM. Como en el módulo piloto,
no agregan: una tabla, filtros, orden y paginación. El embudo de conversión, el tiempo medio por
etapa y la carga por ejecutivo son **compuestos** y quedan fuera.

**Lo que distingue a este departamento del piloto**, y la razón de abordarlo en segundo lugar: aquí
el acceso **no es uniforme**. Un Gerente de Ventas solo ve los prospectos que tiene asignados, y esa
restricción ya está verificada en el sistema real. Cuentas y Clientes nunca la ejerció porque el
Administrador lo ve todo. Es la primera vez que la regla de acotamiento del contrato común tiene
consecuencia observable.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común. **Lo allí definido no se repite.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §3 — catálogo y trazabilidad.
- `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/` — módulo piloto; esta spec reutiliza
  su capa transversal sin volver a decidirla.
- `.specify/docs/actors.md` — roles reales.

**Alcance:** solo backend. La ubicación en pantalla se decide por separado.

---

## Nota de alcance: por qué son cuatro listados y no ocho

El catálogo general enumera **ocho** informes simples para este departamento. Al verificarlos contra
el modelo de datos y el código, se resuelven en **cuatro endpoints**:

| Filas del catálogo | Resolución |
|---|---|
| Prospectos registrados con canal · Prospectos por tipo de organización · Prospectos por etapa y ejecutivo · Prospectos perdidos con motivo | **Un solo listado de prospectos con filtros.** Las cuatro son la misma consulta sobre la misma tabla, cambiando qué filtro se aplica. Mantener cuatro endpoints casi idénticos sería duplicación, no cobertura. |
| Reasignaciones del período | Listado propio — otra tabla |
| Demos activas y su expiración | Listado propio — columna derivada distinta (días restantes) |
| Notificaciones de señal de interés enviadas | Listado propio — otra tabla |
| **Notificaciones con envío fallido** | ⛔ **No es construible.** Ver más abajo. |

Esto **no reduce la cobertura**: las cuatro preguntas del catálogo se responden, con un filtro en vez
de con un endpoint. Lo que cambia es el conteo de endpoints, no el de necesidades cubiertas.

> **Consecuencia para el resto del proyecto.** El catálogo cuenta informes como los nombra el usuario
> táctico, y varios de ellos son el mismo listado con distinto filtro. Es previsible que los seis
> departamentos restantes se consoliden de forma parecida, y que los **64 listados pendientes** se
> resuelvan en bastantes menos endpoints. Conviene tenerlo presente al estimar.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar prospectos viendo solo lo que a cada quien le corresponde (Priority: P1)

Como Gerente de Ventas, quiero consultar mis prospectos filtrando por canal de origen, tipo de
organización, etapa del embudo o estado, para trabajar mi cartera sin ver la de mis compañeros. Como
Administrador, quiero la misma consulta sobre todos los prospectos, para supervisar el conjunto.

**Why this priority**: Es el listado central del departamento y **el único de los cuatro donde el
acotamiento por titularidad tiene consecuencia**. Si esta historia funciona, la regla más delicada
del contrato queda validada; si no, ninguna de las restantes debería construirse encima.

**Independent Test**: Se puede consultar el listado de prospectos con cada filtro, con dos roles
distintos, y comprobar el acotamiento, sin que existan los otros tres listados.

**Acceptance Scenarios**:

1. **Given** un Gerente de Ventas con prospectos asignados y existiendo prospectos de otros
   ejecutivos, **When** consulta el listado sin indicar ejecutivo, **Then** obtiene **únicamente los
   suyos**.
2. **Given** un Gerente de Ventas, **When** consulta el listado pidiendo expresamente los prospectos
   de otro ejecutivo, **Then** el sistema responde `403` y **no devuelve ninguna fila** — no se
   sustituye en silencio por los suyos.
3. **Given** un Administrador, **When** consulta el listado sin indicar ejecutivo, **Then** obtiene
   los prospectos de **todos** los ejecutivos.
4. **Given** un Administrador, **When** filtra por un ejecutivo concreto, **Then** obtiene solo los
   de ese ejecutivo.
5. **Given** prospectos registrados por distintos canales, **When** se filtra por canal de origen,
   **Then** solo aparecen los de ese canal, y cada fila muestra su canal.
6. **Given** prospectos en distintas etapas del embudo, **When** se filtra por etapa, **Then** solo
   aparecen los de esa etapa, con el **nombre** del ejecutivo asignado, no su identificador.
7. **Given** prospectos perdidos, **When** se filtra por estado perdido, **Then** cada fila muestra
   su motivo de pérdida.
8. **Given** un Operador de Emergencias autenticado, **When** consulta el listado, **Then** el
   sistema responde `403`.

---

### User Story 2 - Seguir las reasignaciones de cartera (Priority: P2)

Como Administrador, quiero ver qué prospectos han cambiado de ejecutivo en un período, con el
responsable anterior, el nuevo y el motivo, para entender cómo se está moviendo la cartera.

**Why this priority**: Da visibilidad sobre decisiones de reparto que hoy solo se ven entrando
prospecto por prospecto. Es independiente y valioso, pero afecta a menos volumen que la consulta de
cartera.

**Independent Test**: Se puede consultar el listado de reasignaciones de forma aislada, con y sin
rango de fechas, sin que existan los otros tres listados.

**Acceptance Scenarios**:

1. **Given** hubo reasignaciones en el período, **When** se consulta el listado, **Then** cada fila
   muestra el prospecto, el **nombre** del ejecutivo anterior, el del nuevo, el tipo de asignación y
   el motivo.
2. **Given** no se indica período, **When** se consulta el listado, **Then** el sistema devuelve el
   histórico completo paginado, sin exigir un rango.
3. **Given** una asignación inicial sin responsable previo, **When** aparece en el listado, **Then**
   el ejecutivo anterior se presenta como ausente, no como un dato vacío ni como un cero.

---

### User Story 3 - Vigilar la nutrición del prospecto (Priority: P3)

Como Gerente de Ventas, quiero ver qué demos siguen vigentes y cuánto les queda, y qué alertas de
señal de interés se han enviado, para actuar antes de que la oportunidad se enfríe.

**Why this priority**: Completa la cobertura de OT03 y sostiene la iniciativa de nutrición, pero
depende de que exista actividad de demo previa, así que es el de menor urgencia inmediata.

**Independent Test**: Se pueden consultar los dos listados de forma aislada, sin que existan los de
las otras dos historias.

**Acceptance Scenarios**:

1. **Given** hay demos con fecha de expiración futura, **When** se consulta el listado de demos
   activas, **Then** aparecen con los **días restantes** hasta su expiración.
2. **Given** una demo ya expiró, **When** se consulta el listado, **Then** esa demo **no aparece**.
3. **Given** un Gerente de Ventas consulta las demos, **When** obtiene el resultado, **Then** solo ve
   las de **sus** prospectos, con el mismo acotamiento de la User Story 1.
4. **Given** se enviaron alertas de señal de interés, **When** se consulta el listado de
   notificaciones, **Then** cada fila muestra el prospecto, la regla que la disparó, el canal y la
   fecha.
5. **Given** un Gerente de Ventas consulta las notificaciones, **When** obtiene el resultado, **Then**
   solo ve **aquellas de las que fue destinatario**.

---

### Edge Cases

- **Resultado vacío.** `200` con `data: []`, nunca `404`. Que un ejecutivo no tenga prospectos
  perdidos es una respuesta legítima.
- **Gerente sin cartera.** Un ejecutivo sin ningún prospecto asignado obtiene un listado vacío, no
  un error ni el listado completo.
- **Filtro por ejecutivo ajeno.** Responde `403`. **Nunca** se sustituye silenciosamente por los
  propios: el solicitante debe saber que pidió algo que no le corresponde.
- **Prospecto sin ejecutivo asignado.** Aparece en el listado del Administrador con el ejecutivo
  marcado como ausente. Es una anomalía que la supervisión necesita ver, no una fila a ocultar.
- **Asignación inicial.** La primera asignación de un prospecto no tiene responsable anterior; se
  presenta como ausente, no como vacío ni cero.
- **Demo sin fecha de expiración.** No se considera activa y no aparece en el listado de demos.
- **Retraso de ingesta.** 5–15 segundos entre escritura y visibilidad. Un prospecto recién
  reasignado puede seguir mostrando su ejecutivo anterior. **No se compensa.**
- **Cursor inestable.** Sin orden determinista la paginación repite o salta filas; todo listado
  declara desempate por clave primaria.
- **Límite excedido.** `limit` sobre el máximo responde `400`, no se recorta en silencio.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los cuatro listados

- **FR-001**: El sistema MUST ofrecer un listado de **prospectos** con su canal de origen, tipo de
  organización, etapa actual, ejecutivo asignado, estado y motivo de pérdida cuando corresponda.
  *(OT01/OT02, OP09, OP10, CU-O19, CU-O21)*
- **FR-002**: El listado de prospectos MUST admitir filtros por **canal de origen, tipo de
  organización, etapa, ejecutivo y estado**, combinables entre sí. Estos filtros son los que hacen
  innecesarios los cuatro endpoints separados que enumeraba el catálogo.
- **FR-003**: El sistema MUST ofrecer un listado de **reasignaciones de prospecto**, con el ejecutivo
  anterior, el nuevo, el tipo de asignación y el motivo. *(OT02, CU-O19)*
- **FR-004**: El sistema MUST ofrecer un listado de **demos activas**, con la fecha de expiración y
  los días restantes. *(OT03, CU-O23)*
- **FR-005**: El sistema MUST ofrecer un listado de **notificaciones de señal de interés enviadas**,
  con la regla disparada, el canal y la fecha. *(OT03, CU-O25)*

#### Acotamiento por titularidad — el requisito central

- **FR-006**: Un **Administrador** MUST obtener los registros de todos los ejecutivos, y MUST poder
  filtrar por un ejecutivo concreto.
- **FR-007**: Un **Gerente de Ventas o Gerente de Cuentas Públicas** que no indique ejecutivo MUST
  obtener **únicamente los registros de los que es titular**.
- **FR-008**: Un Gerente que pida expresamente los registros de **otro** ejecutivo MUST recibir una
  negativa. **MUST NOT** devolvérsele su propia cartera como si su petición se hubiera atendido: la
  sustitución silenciosa oculta un error de quien consulta.
- **FR-009**: El acotamiento MUST aplicarse en **los cuatro listados**: cartera y demos por el
  ejecutivo asignado al prospecto; notificaciones por el ejecutivo destinatario.
- **FR-010**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato. Un informe no puede exponer registros que su solicitante no podría ver navegando.
- **FR-011**: Cualquier rol distinto de Administrador, Gerente de Ventas, Gerente de Cuentas
  Públicas y Director de Marketing MUST recibir una negativa en los cuatro listados.

#### Autoridad departamental

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS. Aquí solo se recoge lo que aplica a este departamento.

- **FR-011a**: El **Director de Marketing**, autoridad de Ventas y CRM, MUST acceder a los cuatro
  listados **sin el acotamiento por titularidad** de FR-007: su función es supervisar el embudo
  completo, y no tiene pantalla operativa que espejar.
- **FR-011b**: Esa exención MUST NOT extenderse a ningún otro rol ni a ningún dato excluido por otra
  razón: las exclusiones de dato personal de FR-013 rigen también para él.
- **FR-011c**: De los cuatro listados, **demos activas y notificaciones enviadas son bandejas de
  trabajo del ejecutivo** —su valor está en actuar antes de que la oportunidad se enfríe—, y
  **reasignaciones es supervisión** del reparto de cartera. El de prospectos sirve a ambos.

#### Naturaleza de los listados

- **FR-012**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla de hechos o
  entidad**. Si requiriera agregación o una segunda tabla de hechos, MUST reclasificarse como
  compuesto y salir de esta spec.
- **FR-013**: El sistema MUST devolver el **nombre** del ejecutivo, la etapa y el motivo, no sus
  identificadores internos.
- **FR-014**: Los listados MUST ser de **solo lectura**.

#### Filtros, orden y paginación

- **FR-015**: Los listados de **prospectos** y **demos activas** describen el estado actual y MUST
  rechazar con `400` un filtro de rango de fechas de registro. El listado de **reasignaciones** y el
  de **notificaciones** son de hechos del período y MUST aceptar rango **opcional**.
- **FR-016**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria.
- **FR-017**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  válidos. MUST NOT ignorarse.
- **FR-018**: Un `limit` superior al máximo MUST responder `400`. MUST NOT recortarse en silencio.

#### Calidad del dato

- **FR-019**: El sistema MUST tratar los valores centinela como ausencia de valor. Un prospecto sin
  ejecutivo, una asignación sin responsable previo y un prospecto sin motivo de pérdida se presentan
  como ausentes, nunca como la cadena literal `null`, un cero o una fecha mínima.
- **FR-020**: Un prospecto **sin ejecutivo asignado** MUST aparecer en el listado del Administrador,
  marcado como tal, en lugar de ser omitido.

### Key Entities

- **Prospecto**: la organización interesada que aún no es cliente. Conserva canal de origen, tipo de
  organización, etapa del embudo, ejecutivo asignado, estado, motivo de inactividad y la vigencia de
  su demo. Alimenta FR-001, FR-004.
- **Asignación de prospecto**: el registro de a quién se asignó un prospecto, con responsable
  anterior, nuevo, tipo y motivo. Alimenta FR-003.
- **Notificación de señal de interés**: la alerta enviada a un ejecutivo cuando el prospecto muestra
  interés, con la regla que la disparó y el canal. Alimenta FR-005.
- **Ejecutivo comercial**: el usuario titular de una cartera. Determina qué ve cada solicitante
  (FR-006 a FR-009).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Gerente de Ventas obtiene **el 100 %** de sus prospectos y **cero** prospectos de
  otros ejecutivos, verificable con dos carteras pobladas simultáneamente.
- **SC-002**: **Ningún** intento de consultar la cartera de otro ejecutivo devuelve datos: todos
  reciben una negativa explícita.
- **SC-003**: Las cuatro preguntas que el catálogo planteaba por separado —por canal, por tipo de
  organización, por etapa y ejecutivo, y perdidos con motivo— se responden con **un solo listado**
  aplicando filtros.
- **SC-004**: Los cuatro listados devuelven su primera página en **menos de 2 segundos** con el
  volumen actual.
- **SC-005**: **El 100 %** de los identificadores internos llega resuelto a su nombre legible.
- **SC-006**: Recorrer un listado por páginas devuelve **cada fila exactamente una vez**, sin
  repeticiones ni omisiones.
- **SC-007**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**, en
  los cuatro casos.

---

## Assumptions

- **El contrato común está vigente.** Ruta, envelope, paginación por cursor, límites y reglas de la
  base analítica se heredan y no se redefinen.
- **Se reutiliza la capa transversal del módulo piloto.** El período opcional, la paginación keyset y
  el envelope construidos para Cuentas y Clientes se usan tal cual. Esta spec **no** vuelve a
  decidirlos.
- **El acotamiento sigue el patrón ya implementado en el módulo operativo.** La consulta de
  notificaciones de ventas ya resuelve exactamente este problema —Administrador ve todo, Gerente
  queda forzado a lo suyo, y pedir lo ajeno es una negativa—; los listados heredan ese
  comportamiento en vez de inventar uno nuevo.
- **Los roles son los reales del sistema.** Administrador, Gerente de Ventas y Gerente de Cuentas
  Públicas existen en `.specify/docs/actors.md`. No se introduce ninguno nuevo.
- **Los dos roles de gerente se tratan igual.** Gerente de Cuentas Públicas es el equivalente para el
  segmento público y recibe el mismo acotamiento, como ya hace el módulo operativo.
- **Una demo está activa si su expiración es futura.** Sin fecha de expiración, no se considera
  activa.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Embudo de conversión, tiempo medio por etapa, carga por ejecutivo | Son agregaciones → compuestos |
| Volumen de captación por canal, tasa de conversión por canal, coste por canal | Son agregaciones → compuestos |
| Intensidad de uso de la demo, secciones más visitadas, efectividad de la nutrición | Son agregaciones → compuestos |
| Latencia de reacción comercial, reglas por tasa de acierto, motivos de pérdida frecuentes | Son agregaciones → compuestos |
| **Notificaciones con envío fallido** | ⛔ **No hay dato.** La columna de estado de envío existe en el esquema pero **ningún código la escribe** (cero apariciones en el repositorio). El despacho fallido lanza una excepción y deja un aviso en el log de aplicación, sin registrar el estado. No es construible sin persistir antes ese resultado. |
| Cualquier pantalla o tablero | El frontend se decide por separado, después. |
