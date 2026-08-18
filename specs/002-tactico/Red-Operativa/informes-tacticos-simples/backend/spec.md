# Feature Specification: Informes Tácticos Simples de Red Operativa (Backend)

**Feature Branch**: `informes-tacticos-simples-red-operativa`

**Created**: 2026-08-14

**Status**: Implemented

**Input**: User description: "Informes tácticos simples de Red Operativa — listados llanos de solo lectura (backend) que satisfacen OT11, OT12 y OT13, bajo el contrato specs/002-tactico/contrato-informes-simples.md"

---

## Contexto

Cuatro listados llanos de solo lectura sobre el escenario donde ocurre la operación: la flota de
unidades y las regiones operativas. Como en los tres módulos anteriores, no agregan.

**Lo que distingue a este departamento:**

1. **Es el primero cuyos datos son geográficos.** La ubicación se resuelve por una jerarquía de
   cinco niveles —país, estado, condado, ciudad, calle—, más profunda que cualquier catálogo
   anterior.
2. **Es el primero donde un informe equivocado tiene consecuencia operativa, no comercial.** Una
   lectura errónea de la flota lleva a decisiones de cobertura erróneas, y la cobertura es lo que
   determina si hay alguien para atender un accidente.
3. **Reutiliza el eje de acotamiento por organización** construido en Suscripciones: una empresa
   proveedora ve **solo sus propias unidades**. Es la confirmación de que esa pieza generaliza.

**Documentos que gobiernan esta spec:**

- `specs/002-tactico/contrato-informes-simples.md` — contrato común. **No se repite aquí.**
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §5 — catálogo y trazabilidad.
- Módulos previos: `Cuentas-Clientes/` (capa transversal), `Ventas-CRM/` (acotamiento por persona),
  `Suscripciones-Facturacion/` (acotamiento por organización). Se reutilizan y **no se vuelven a
  decidir**.

**Alcance:** solo backend.

---

## Nota de alcance: la disponibilidad de una unidad no es un listado

Esta es la corrección más importante del módulo, y conviene entenderla antes de leer los requisitos.

**Una unidad tiene dos nociones de estado que el catálogo confundía en una sola:**

| Noción | Dónde vive | Qué significa |
|---|---|---|
| **Existencia** | Columna de la propia unidad | La unidad está dada de alta o dada de baja |
| **Disponibilidad operativa** | **Solo en su histórico de estados** | Activa, Ocupada, En Misión o Fuera de servicio |

La disponibilidad **no es una columna de la unidad**: solo se conoce leyendo el **último registro de
su histórico de estados**. Obtenerla para un listado de N unidades exige, o bien una consulta por
cada unidad, o bien agregar el histórico para quedarse con el último por unidad y volver a cruzar.
**Cualquiera de las dos vías lo convierte en compuesto.**

**Consecuencia:** el listado de flota de esta spec informa de **la composición de la flota**
—qué unidades tiene cada proveedor, dónde y de qué tipo—, **no de cuáles están disponibles ahora
mismo**. La cobertura disponible por región es **CU-T08**, es compuesta, y ya está clasificada como
tal en el catálogo.

**Por qué importa decirlo así de claro.** Un listado de flota filtrado por «la unidad existe» y
presentado como «flota disponible» contaría unidades fuera de servicio, ocupadas o ya en camino a
otro accidente. En un departamento comercial eso sería un número inflado; aquí es una decisión de
cobertura tomada sobre unidades que no pueden atender nada.

### Resto de la consolidación

| Filas del catálogo | Resolución |
|---|---|
| Unidades por estado, condado y proveedor · Unidades por tipo y capacidad | **Un solo listado de flota con filtros**, sin la disponibilidad operativa (ver arriba) |
| Regiones por estado · Regiones detenidas en validación más de N días · Regiones despublicadas con causa | **Un solo listado de regiones con filtros** |
| Bajas de unidad del período | Listado propio |
| Historial de intentos de validación | Listado propio |
| **Unidades de alta en lote pendientes de primer acceso** | ⚠️ **Reclasificado a compuesto** — cruza la flota con el estado de las credenciales, dos tablas |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar la composición de la flota (Priority: P1)

Como Empresa Proveedora de Unidades, quiero ver mis unidades filtrando por condado, tipo o estado de
alta, para saber con qué cuento y dónde. Como Administrador, quiero la misma consulta sobre la flota
completa, para supervisar el conjunto de proveedores.

**Why this priority**: Es el listado central del departamento y **el único donde el acotamiento por
organización tiene consecuencia**. Además es donde se materializa la distinción entre existencia y
disponibilidad, que es la corrección de fondo del módulo.

**Independent Test**: Consultar el listado con cada filtro, con dos roles distintos, sin que existan
los otros tres listados.

**Acceptance Scenarios**:

1. **Given** existen unidades de varias empresas proveedoras, **When** una Empresa Proveedora
   consulta el listado, **Then** obtiene **únicamente las suyas**.
2. **Given** una Empresa Proveedora, **When** consulta pidiendo expresamente las unidades de otro
   proveedor, **Then** el sistema responde `403` y **no devuelve ninguna fila**.
3. **Given** un Administrador, **When** consulta el listado, **Then** obtiene las unidades de
   **todos** los proveedores, y puede filtrar por uno concreto.
4. **Given** unidades en distintos condados, **When** se filtra por condado, **Then** solo aparecen
   las de ese condado, cada una con el **nombre** del condado y su ciudad, no con identificadores.
5. **Given** unidades de distinto tipo, **When** se filtra por tipo, **Then** solo aparecen las de
   ese tipo, con su placa y capacidad.
6. **Given** unidades dadas de alta y dadas de baja, **When** se filtra por estado de alta, **Then**
   la distinción es entre **existir o estar dada de baja**, y el listado declara expresamente que
   **no informa de disponibilidad operativa**.
7. **Given** un Operador de Emergencias autenticado, **When** consulta el listado, **Then** el
   sistema responde `403`.

---

### User Story 2 - Seguir las bajas de unidad y su impacto (Priority: P2)

Como Administrador, quiero ver qué unidades se dieron de baja en un período, con su motivo y si la
baja interrumpió una misión en curso, para entender el impacto de las salidas de flota.

**Why this priority**: Da visibilidad sobre decisiones que hoy solo se ven unidad por unidad, e
incluye la distinción entre una baja ordenada y una que dejó un accidente sin unidad. Es
independiente y valioso, pero de menor volumen que la composición de flota.

**Independent Test**: Consultar el listado de forma aislada, con y sin rango de fechas, sin que
existan los otros tres.

**Acceptance Scenarios**:

1. **Given** hubo bajas en el período, **When** se consulta el listado, **Then** cada fila muestra la
   unidad, el proveedor, el motivo, el tipo de baja y quién la ejecutó.
2. **Given** una baja se produjo con la unidad atendiendo un caso, **When** aparece en el listado,
   **Then** se distingue como **baja forzada** e indica **el caso que quedó afectado**.
3. **Given** una baja ordinaria sin caso en curso, **When** aparece en el listado, **Then** se
   distingue como baja normal y el caso afectado se presenta como ausente.
4. **Given** no se indica período, **When** se consulta el listado, **Then** el sistema devuelve el
   histórico completo paginado.
5. **Given** una Empresa Proveedora consulta las bajas, **When** obtiene el resultado, **Then** solo
   ve las de **sus** unidades.

---

### User Story 3 - Supervisar las regiones operativas y su validación (Priority: P3)

Como Administrador, quiero ver en qué estado está cada región operativa, cuáles llevan demasiado
tiempo detenidas en validación y qué intentos de validación se han producido con su resultado, para
desatascar las incorporaciones y entender por qué se rechazan.

**Why this priority**: Sostiene OT11 y OT13 completos y alimenta el criterio de validación que hoy
no está definido, pero opera sobre menos volumen y con menos urgencia diaria que la flota.

**Independent Test**: Consultar los dos listados de forma aislada, sin que existan los de las otras
historias.

**Acceptance Scenarios**:

1. **Given** existen regiones en distintos estados, **When** se consulta el listado, **Then**
   aparecen todas con su estado, el **nombre** del estado geográfico al que pertenecen y su fecha de
   última actualización.
2. **Given** se filtra por regiones detenidas más de un número de días, **When** se consulta,
   **Then** solo aparecen las que llevan ese tiempo sin cambiar de estado, indicando cuántos días
   llevan.
3. **Given** una región fue despublicada, **When** se consulta el listado, **Then** aparece con su
   estado de despublicada y **no se omite**: una región retirada sigue siendo información de
   supervisión.
4. **Given** hubo intentos de validación sobre una región, **When** se consulta ese listado,
   **Then** cada intento muestra la región, el resultado, el motivo cuando lo hubo, y el **nombre**
   de quien lo ejecutó.
5. **Given** una región acumuló varios rechazos, **When** se consultan sus intentos, **Then**
   aparecen **todos**, en orden, sin que el último sustituya a los anteriores.
6. **Given** una Empresa Proveedora consulta cualquiera de los dos listados, **Then** el sistema
   responde `403`: las regiones no pertenecen a ningún proveedor.

---

### Edge Cases

- **Resultado vacío.** `200` con `data: []`, nunca `404`. Que un proveedor no tenga bajas es una
  buena noticia.
- **Proveedor sin flota.** Obtiene un listado vacío, no un error ni la flota completa.
- **Unidad sin condado asignado.** Aparece con la ubicación marcada como ausente. **No se omite**:
  una unidad sin condado no puede encontrarse como candidata en un despacho, y esa es exactamente la
  anomalía que la supervisión necesita ver.
- **Baja sin caso afectado.** Se presenta como ausencia, nunca como un identificador de caso vacío
  o cero.
- **Región sin ningún intento de validación.** No aparece en el listado de intentos; sí en el de
  regiones, con su estado inicial.
- **Retraso de ingesta.** 5–15 segundos entre escritura y visibilidad. Una unidad recién dada de
  baja puede seguir apareciendo como alta. **No se compensa.**
- **Cursor inestable.** Sin orden determinista la paginación repite o salta filas.
- **Límite excedido.** `limit` sobre el máximo responde `400`, no se recorta en silencio.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Los cuatro listados

- **FR-001**: El sistema MUST ofrecer un listado de **unidades de la flota** con la placa, el tipo,
  la capacidad, el proveedor, la ubicación de cobertura y si la unidad está dada de alta o de baja.
  *(OT12, OP21, OP22)*
- **FR-002**: El listado de flota MUST admitir filtros por **proveedor, condado, tipo de unidad y
  estado de alta**, combinables entre sí.
- **FR-003**: El sistema MUST ofrecer un listado de **bajas de unidad** con la unidad, el proveedor,
  el motivo, el tipo de baja, quién la ejecutó y el caso afectado cuando lo hubo.
  *(OT12, CU-O42)*
- **FR-004**: El sistema MUST ofrecer un listado de **regiones operativas** con su estado, el estado
  geográfico al que pertenecen y el tiempo que llevan sin cambiar de estado. *(OT11/OT13, OP23,
  OP24, OP25)*
- **FR-005**: El sistema MUST ofrecer un listado de **intentos de validación de región**, con el
  resultado, el motivo y quién lo ejecutó, conservando **todos** los intentos. *(OT11, CU-O44)*

#### La distinción entre existir y estar disponible

- **FR-006**: El listado de flota MUST informar de si una unidad está **dada de alta o de baja**, y
  **MUST NOT** presentar ese dato como disponibilidad operativa.
- **FR-007**: El listado de flota **MUST NOT** afirmar ni sugerir que una unidad esté disponible para
  atender un accidente. La disponibilidad operativa depende del estado en que la unidad se encuentre
  en cada momento, que no forma parte de este listado.
- **FR-008**: La respuesta MUST declarar explícitamente que el listado describe **composición de
  flota**, no cobertura disponible, para que ningún consumidor lo interprete de otro modo.

#### Acotamiento por organización

- **FR-009**: Un **Administrador** MUST obtener los registros de todos los proveedores, y MUST poder
  filtrar por uno concreto.
- **FR-010**: Una **Empresa Proveedora** MUST obtener únicamente los registros de **sus propias
  unidades**, resueltos a partir de su pertenencia, sin necesidad de indicarla.
- **FR-011**: Una Empresa Proveedora que pida expresamente los registros de **otro proveedor** MUST
  recibir una negativa. **MUST NOT** devolvérsele su propia flota como si su petición se hubiera
  atendido.
- **FR-012**: Los listados de **regiones** y de **intentos de validación** MUST estar restringidos al
  Administrador y al Director Tecnológico: una región no pertenece a ningún proveedor.
- **FR-013**: El alcance de un listado MUST NOT ser más amplio que el de la pantalla operativa del
  mismo dato.

#### Autoridad departamental — **repartida por materia**

> Asignación completa en [`../../../acceso-tactico.md`](../../../acceso-tactico.md), derivada del
> §5.1 del SRS.

Como en Suscripciones, el SRS reparte la autoridad de este departamento entre dos cargos.

- **FR-013a**: El **Director de Expansión**, que decide dónde crecer, MUST acceder a los listados de
  **flota**, **bajas de unidad** y **regiones**, sin acotamiento por proveedor.
- **FR-013b**: El **Director Tecnológico**, que decide la validación de regiones, MUST acceder a los
  listados de **regiones** e **intentos de validación**. El de validaciones es específicamente suyo:
  es donde se ve por qué se rechaza una región, que es el criterio que él fija.
- **FR-013c**: La exención de acotamiento **MUST NOT** alcanzar a FR-015: la posición geográfica de
  las unidades sigue sin exponerse a nadie.
- **FR-013d**: De los cuatro listados, **bajas de unidad e intentos de validación son supervisión**
  —impacto acumulado y criterios de rechazo—, mientras que flota y regiones sirven también al trabajo
  diario del proveedor y del Administrador.

#### Naturaleza de los listados

- **FR-014**: Cada listado MUST resolverse como consulta llana sobre **una sola tabla**. Si
  requiriera agregación o combinar dos tablas de hechos, MUST reclasificarse como compuesto.
- **FR-015**: El sistema MUST devolver el **nombre** del condado, la ciudad, el proveedor, el estado
  y el ejecutor, no sus identificadores internos.
- **FR-016**: Los listados MUST ser de **solo lectura**.

#### Filtros, orden y paginación

- **FR-017**: Los listados de **bajas** y de **intentos de validación** son de hechos del período y
  MUST aceptar rango de fechas **opcional**. Los de **flota** y **regiones** describen el estado
  actual y MUST rechazar un rango de fechas.
- **FR-018**: Cada listado MUST declarar un orden por defecto **determinista**, con desempate por
  clave primaria.
- **FR-019**: Un valor no reconocido en un filtro de enumeración MUST responder `400` nombrando los
  válidos.
- **FR-020**: Un `limit` superior al máximo MUST responder `400`. MUST NOT recortarse en silencio.

#### Calidad del dato

- **FR-021**: El sistema MUST distinguir una **baja forzada** —producida con la unidad atendiendo un
  caso— de una baja ordinaria, e indicar el caso afectado en la primera.
- **FR-022**: El sistema MUST tratar los valores centinela como ausencia: una unidad sin condado, una
  baja sin caso afectado y un intento de validación sin motivo se presentan como ausentes.
- **FR-023**: Una unidad **sin condado asignado** MUST aparecer en el listado del Administrador,
  marcada como tal, en lugar de ser omitida.

### Key Entities

- **Unidad de emergencia**: el vehículo de la flota, con su placa, tipo, capacidad, proveedor
  titular, condado de cobertura y su condición de alta o baja. Alimenta FR-001.
- **Baja de unidad**: la salida de una unidad de la flota, con su motivo, su tipo y el caso que
  quedó afectado si lo hubo. Alimenta FR-003, FR-021.
- **Región operativa**: el territorio habilitado para operar, con su estado dentro del protocolo de
  incorporación. Alimenta FR-004.
- **Intento de validación de región**: cada evaluación de una región contra los criterios de
  producción, con su resultado y motivo. Alimenta FR-005.
- **Empresa proveedora**: la organización titular de una flota. Determina qué ve cada solicitante
  (FR-009 a FR-011).
- **Jerarquía geográfica**: condado y ciudad como catálogos que dan nombre a la ubicación de cada
  unidad y región.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una Empresa Proveedora obtiene **el 100 %** de sus unidades y **cero** unidades de
  otros proveedores, verificable con dos flotas pobladas simultáneamente.
- **SC-002**: **Ningún** intento de consultar la flota de otro proveedor devuelve datos.
- **SC-003**: **Ninguna** respuesta del listado de flota presenta la condición de alta como
  disponibilidad operativa, verificable revisando la respuesta y su declaración de alcance.
- **SC-004**: **El 100 %** de las bajas producidas con un caso en curso se distingue de las
  ordinarias e indica el caso afectado.
- **SC-005**: **El 100 %** de los identificadores internos llega resuelto a su nombre legible,
  incluida la jerarquía geográfica.
- **SC-006**: Los cuatro listados devuelven su primera página en **menos de 2 segundos**.
- **SC-007**: Recorrer un listado por páginas devuelve **cada fila exactamente una vez**.
- **SC-008**: Un listado sin resultados devuelve una respuesta vacía correcta, **nunca un error**.

---

## Assumptions

- **El contrato común está vigente** y la capa transversal de los tres módulos previos se reutiliza:
  período opcional, paginación por cursor, envelope con acotamiento declarado, y el resolutor de
  acotamiento con sus dos ejes. Esta spec **no** los vuelve a decidir.
- **El eje «organización» del acotamiento generaliza sin cambios.** El titular aquí es la empresa
  proveedora, resuelta igual que la cuenta cliente en Suscripciones. Si hiciera falta modificarlo,
  sería señal de que aquella generalización quedó corta.
- **Los roles son los reales del sistema.** Administrador, Director Tecnológico y Empresa Proveedora
  existen en `.specify/docs/actors.md`. No se introduce ninguno nuevo.
- **La condición de alta o baja de una unidad sí es una propiedad suya**, y por tanto consultable en
  un listado llano. Es solo la disponibilidad operativa la que no lo es.
- **El histórico de intentos de validación es acumulativo.** Está verificado en el sistema real: dos
  rechazos seguidos producen dos intentos con su motivo, sin que el segundo borre al primero.
- **Sin exportación.** La descarga en CSV o Excel queda fuera de alcance.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| **Disponibilidad operativa de las unidades** | ⚠️ **No es un listado.** El estado operativo solo se conoce leyendo el último registro del histórico de estados de cada unidad: una consulta por unidad, o una agregación más un cruce. Es **CU-T08** y ya está clasificado como compuesto. |
| Cobertura de flota por región, condados en cobertura crítica | Son agregaciones → compuestos, y dependen de lo anterior |
| Disponibilidad declarada por unidad (% de tiempo activa) | Es una agregación sobre el histórico → compuesto |
| Rotación de flota, tasa de aprobación al primer intento, motivos de rechazo frecuentes | Son agregaciones → compuestos |
| Tiempo de puesta en operación regional, regiones en riesgo de despublicación | Son agregaciones y cruzan tablas → compuestos |
| **Unidades de alta en lote pendientes de primer acceso** | ⚠️ **Reclasificado a compuesto.** Cruza la flota con el estado de las credenciales de acceso: dos tablas. |
| Cualquier pantalla o tablero | El frontend se decide por separado. |
