# Feature Specification: Informes Tácticos Simples de Partners y API (Frontend)

**Feature Branch / capa**: `002-tactico/Partners-API/informes-tacticos-simples/frontend`

**Created**: 2026-08-16

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y
[`../backend/contracts/informes-tacticos-simples.openapi.yaml`](../backend/contracts/informes-tacticos-simples.openapi.yaml).
Esta capa **MUST NOT** redefinir reglas de negocio, filtros ni contratos REST.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)
— contrato común de frontend. **No se repite aquí.**

**Input**: Listados tácticos simples del departamento Partners y API — las mismas cinco consultas
llanas que ya responde el backend, en pantalla. No es patrón Z.

---

## Contexto

Es el **único departamento táctico sin índice de listados**. Los cinco endpoints ya responden; lo
que falta es la pantalla que el resto de departamentos ya tiene (Cuentas, Ventas, Suscripciones,
Soporte, Red Operativa, Emergencias).

No se decide nada de negocio. No se dibuja un tablero. Cada listado es una tabla con filtros y
paginación por cursor, declarada sobre la capa compartida.

### Lo que distingue a esta capa

1. **Dos audiencias, no dos productos.** El Partner ve **tres** listados (los suyos). Los gestores y
   el Director Tecnológico ven **cinco**. Es el mismo índice, filtrado por rol — no un tablero de
   consola fusionado con el portal.
2. **Sí emite `meta.acotado_a`.** Un Partner recibe `propios`; un gestor o el Director, `todos`. El
   aviso de alcance —sobre todo en el estado vacío— se ejercita aquí de punta a punta, igual que en
   Soporte.
3. **La credencial inactiva no dice por qué.** La pantalla **MUST NOT** inventar una columna de
   motivo ni agrupar «inactivas» como si fueran la misma situación. Los motivos viven en cambios de
   acceso, cada uno con su tipo propio (backend FR-006, FR-007).
4. **El secreto no aparece.** Ni en claro, ni transformado, ni como pista en el vacío. El nombre y
   el entorno bastan (backend FR-008).

### Dos superficies, un índice

La consola y el portal **no se fusionan** (design-system §5, ya aplicado en las rutas operativas).
Los informes no reabren esa decisión: hay **una** ruta de índice y **dos entradas de menú** —una
visible a gestores y Director, otra al Partner— para que nadie descubra la superficie operativa del
otro. El índice no muestra datos; solo enlaces, y filtra por rol lo que ofrece.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Consultar los cinco listados con la capa compartida (Priority: P1)

Como Desarrollador de APIs, Administrador o Director Tecnológico, quiero abrir cada listado desde un
índice, filtrar y paginar, para ver el estado de incorporación, las credenciales que vencen, la
bitácora, las versiones del contrato y el alcance contratado sin pedirle a nadie una consulta a la
base.

**Why this priority**: es el entregable. Credenciales es bandeja de trabajo (renovar antes de que
caduquen); cambios de acceso, versiones y alcance son supervisión (backend FR-014c).

**Independent Test**: abrir cada uno de los cinco, filtrar, paginar y volver, sin las otras
historias.

**Acceptance Scenarios**:

1. **Given** un gestor o el Director Tecnológico autenticado, **When** abre el índice, **Then** ve
   **cinco** enlaces y ninguno más.
2. **Given** cualquiera de esos cinco, **When** se abre, **Then** la tabla muestra **las columnas
   que el contrato de backend declara y ninguna más**.
3. **Given** un listado de estado actual (partners, credenciales, versiones, alcance), **When** se
   abre, **Then** la barra **no ofrece** selector de fechas.
4. **Given** el listado de cambios de acceso, **When** se abre, **Then** sí lo ofrece.
5. **Given** el listado de credenciales, **When** se filtra por proximidad de caducidad, **Then** el
   control es el plazo en días que el backend admite — no un rango de fechas.
6. **Given** cualquier listado, **When** se consulta, **Then** **no** aparece recuento total ni
   número de página navegable.

---

### US-FE-2 — Ver lo mío y saber que es solo lo mío (Priority: P1)

Como Partner de integración —también si estoy suspendido— quiero ver mis tres listados de acceso y
saber que no estoy mirando los de otro.

**Why this priority**: es el eje de acotamiento del departamento. Un vacío sin aviso vuelve
ambigua la pregunta «¿no hay nada, o no hay **mío**?».

**Independent Test**: entrar como Partner, con y sin filas, sin que existan las pantallas de
contrato.

**Acceptance Scenarios**:

1. **Given** un Partner autenticado, **When** abre el índice, **Then** ve **tres** enlaces
   (partners, credenciales, cambios de acceso) y **no** ve versiones del contrato ni alcance de
   datos.
2. **Given** un Partner, **When** consulta cualquiera de esos tres, **Then** aparece el aviso de
   que solo ve sus registros.
3. **Given** un Partner **sin filas**, **When** consulta, **Then** el estado vacío dice que no hay
   resultados **entre los suyos** — no un «no hay partners» a secas.
4. **Given** un gestor o el Director, **When** consulta, **Then** **no** aparece aviso de alcance:
   ven todo y un cartel permanente sería ruido.
5. **Given** un Partner suspendido, **When** abre sus tres listados, **Then** **entra**: es donde ve
   su situación y qué debe regularizar.
6. **Given** un Partner, **When** mira la barra de filtros, **Then** **no** aparece un selector de
   partner ajeno: pedir el de otro es una negativa, no un filtro.

---

### US-FE-3 — Distinguir «está inactiva» de «por qué lo está» (Priority: P1)

Como Desarrollador de APIs quiero ver si una credencial está activa y cuándo caduca; como Director
Tecnológico quiero ver en la bitácora si se revocó por seguridad o se apagó por suspensión, porque
son decisiones opuestas.

**Why this priority**: es la corrección de fondo del módulo. Pintar un motivo en la fila de la
credencial —o agrupar las inactivas como si fueran lo mismo— pondría en la misma línea una
credencial comprometida y un impago. Reactivar guiándose por eso resucitaría la comprometida.

**Independent Test**: abrir credenciales y cambios de acceso sobre el mismo partner, con una
revocación y una desactivación por cascada.

**Acceptance Scenarios**:

1. **Given** una credencial inactiva, **When** aparece, **Then** se indica que **no está activa** y
   **no hay columna ni texto que afirme el motivo**.
2. **Given** esa misma credencial, **When** se consulta cambios de acceso, **Then** la revocación y
   la desactivación por cascada se leen **con tipos distintos**, no agrupadas.
3. **Given** cualquier pantalla de estos listados, **When** se inspecciona, **Then** **no** aparece
   el secreto de autenticación ni un hash ni un campo que lo sugiera.
4. **Given** credenciales de pruebas y de producción del mismo partner, **When** se listan, **Then**
   aparecen **ambas**, cada una con su entorno.

---

### US-FE-4 — Entender por qué una consulta no devolvió nada (Priority: P1)

Como cualquiera de los cuatro roles, quiero distinguir «no hay registros», «tu filtro está mal» y
«no tienes acceso».

**Why this priority**: un backend que rechaza con `400`/`403` y una pantalla que lo pinta como
tabla vacía desperdician el trabajo de rechazar en vez de recortar.

**Independent Test**: forzar cada caso en un listado, sin las otras historias.

**Acceptance Scenarios**:

1. **Given** un filtro con un valor que el backend no admite, **When** se consulta, **Then** se
   muestra **el mensaje del backend**, que nombra los valores válidos — no un texto genérico.
2. **Given** ese mismo error, **When** se muestra, **Then** **no** se ofrece «Reintentar».
3. **Given** un Partner que entra a versiones del contrato o a alcance de datos, **When** el guard o
   el backend lo niegan, **Then** ve una negativa, **no** una tabla vacía.
4. **Given** un rol ajeno al departamento (p. ej. Operador de despacho), **When** entra al índice o
   a un listado, **Then** ve una negativa.
5. **Given** un fallo del servidor, **When** ocurre, **Then** sí se ofrece «Reintentar».
6. **Given** una consulta correcta sin resultados y `acotado_a: todos`, **When** se muestra, **Then**
   el vacío habla del dominio —«no hay versiones retiradas»— y **no** dice «sin datos».

---

### US-FE-5 — Leer un dato ausente como ausente (Priority: P2)

Como gestor quiero que un cliente sin preferencias, una reactivación sin motivo y un partner que no
está suspendido se vean vacíos, no como «ilimitado», «sin motivo» inventado o una fecha de 1970.

**Why this priority**: de las dos lecturas de un vacío, la peligrosa es tratarlo como permiso
total o como cero.

**Acceptance Scenarios**:

1. **Given** un cliente sin alcance configurado, **When** aparece, **Then** las zonas y las
   condiciones de entrega se ven **ausentes**. **MUST NOT** leerse como acceso a todas las zonas.
2. **Given** una reactivación, **When** aparece en cambios de acceso, **Then** el motivo se ve
   ausente — no es un dato incompleto.
3. **Given** un partner que no está suspendido, **When** aparece, **Then** fecha y motivo de
   suspensión se ven ausentes.
4. **Given** un valor numérico que **sí** es cero (p. ej. cupo agotado), **When** aparece, **Then**
   se muestra `0` — no se confunde con la ausencia.
5. **Given** una versión publicada, **When** aparece, **Then** la fecha de retiro se ve ausente; una
   retirada **no se omite**.

---

### Edge Cases

- **Partner sin credenciales todavía.** Aparece en el listado de partners; el de credenciales puede
  estar vacío **entre los suyos**, y el aviso de alcance lo dice.
- **Partner suspendido.** Conserva los tres listados de acceso. El índice no lo echa.
- **Sesión caducada.** El listado no inventa un manejo propio: se apoya en el de la aplicación.
- **Pantalla estrecha.** Tabla en escritorio, tarjetas en móvil; ninguna columna declarada desaparece
  sin estar marcada como solo-escritorio.
- **Filtro `partner`.** Solo lo ven quienes el backend autoriza a indicar un partner. Mostrárselo al
  Partner es ofrecerle un control cuyo único efecto útil es un `403`.
- **Retraso de ingesta.** Una credencial recién revocada puede seguir apareciendo activa unos
  segundos. La pantalla **no** lo compensa ni inventa un «actualizado hace…» que el backend no
  envía.

---

## Functional Requirements (UI)

### Las cinco pantallas y el índice

- **FR-UI-001**: El sistema MUST ofrecer una pantalla por cada uno de los cinco listados
  (partners, credenciales, cambios de acceso, versiones del contrato, alcance de datos), bajo una
  ruta propia del departamento, y un índice desde el que se llegue a ellas.
- **FR-UI-002**: Cada pantalla MUST declarar sus columnas y sus filtros y **MUST NOT** maquetar su
  propia tabla ni su propia paginación. Consumen la capa compartida del contrato de frontend.
- **FR-UI-003**: Las columnas mostradas MUST coincidir **exactamente** con las que el contrato
  OpenAPI del backend declara para ese listado. **MUST NOT** añadirse columnas de motivo en
  credenciales, ni secreto, ni identificadores internos.
- **FR-UI-004**: El índice MUST filtrar los enlaces por rol: el Partner ve los tres de acceso; el
  Desarrollador de APIs, el Administrador y el Director Tecnológico ven los cinco.
- **FR-UI-005**: MUST existir **dos entradas de menú** hacia el mismo índice —una para gestores y
  Director, otra para el Partner— de modo que la consola y el portal **no compartan** el enlace ni
  el texto. El Partner no lee «todos los partners»; el gestor no lee «mi integración».

### Filtros

- **FR-UI-006**: Los filtros de enumeración MUST ofrecer **solo** los valores válidos del contrato.
- **FR-UI-007**: El selector de rango de fechas MUST aparecer **únicamente** en cambios de acceso.
- **FR-UI-008**: El filtro de proximidad de caducidad MUST aparecer **únicamente** en credenciales.
- **FR-UI-009**: El filtro por partner MUST aparecer **únicamente** para gestores y Director, y
  **MUST NOT** mostrarse al Partner.
- **FR-UI-010**: Un filtro sin valor **MUST NOT** viajar en la petición. Cambiar de filtros MUST
  volver a la primera página.

### Alcance y estados

- **FR-UI-011**: El aviso de `acotado_a` MUST mostrarse cuando la respuesta lo declare distinto de
  `todos`, **también en el estado vacío**.
- **FR-UI-012**: `acotado_a: todos` **MUST NOT** producir aviso.
- **FR-UI-013**: Un `400` MUST mostrarse con el `detail` del backend y **MUST NOT** presentarse como
  resultado vacío. **MUST NOT** ofrecer «Reintentar».
- **FR-UI-014**: Un `403` MUST distinguirse de un resultado vacío.
- **FR-UI-015**: Solo los errores reintentables MUST ofrecer «Reintentar».
- **FR-UI-016**: El estado vacío de cada listado MUST hablar de su dominio. El del Partner MUST
  mencionar el acotamiento.

### Paginación

- **FR-UI-017**: La navegación MUST ser siguiente/anterior. **MUST NOT** mostrarse recuento total
  ni navegación por número de página.
- **FR-UI-018**: Recorrer un listado hacia delante y hacia atrás **MUST NOT** repetir ni perder
  filas.

### Acceso

- **FR-UI-019**: Las rutas de los **tres listados de acceso** MUST admitir Partner de integración,
  Desarrollador de APIs, Administrador y Director Tecnológico (backend FR-009, FR-010, FR-014a).
- **FR-UI-020**: Las rutas de **versiones del contrato** y **alcance de datos** MUST admitir
  Desarrollador de APIs, Administrador y Director Tecnológico, y **MUST NOT** admitir al Partner
  (backend FR-013, FR-014a).
- **FR-UI-021**: El índice MUST estar protegido por el conjunto **amplio** (los cuatro roles).
  Guardarlo solo con gestores dejaría al Partner y al Director sin forma de llegar a lo suyo.
- **FR-UI-022**: Son **dos guards, no uno con la unión**. Un guard único le daría al Partner los
  dos listados de contrato.
- **FR-UI-023**: El guard **MUST NOT** decidir qué filas se ven. Abre la puerta; el alcance lo
  decide el backend.
- **FR-UI-024**: Un Partner suspendido MUST conservar la entrada a sus tres listados de acceso.

### Presentación del dato

- **FR-UI-025**: Un valor ausente MUST mostrarse como ausente y **MUST NOT** rellenarse con cero,
  con una fecha de época, con «ilimitado» ni con una cadena vacía.
- **FR-UI-026**: Un cliente sin alcance configurado MUST leerse como alcance **ausente**. **MUST
  NOT** interpretarse en pantalla como acceso a todas las zonas (backend FR-023).
- **FR-UI-027**: El listado de credenciales MUST indicar **si** está activa. **MUST NOT** afirmar
  por qué no lo está, ni agrupar revocación, cascada y expiración como un solo estado visible.
- **FR-UI-028**: El listado de cambios de acceso MUST conservar cada tipo de cambio **por
  separado**. En particular, una revocación decidida por el partner y una desactivación por
  suspensión **MUST NOT** agruparse ni relabelarse como «inactiva».
- **FR-UI-029**: Las pantallas MUST mostrar nombres (partner, cuenta, ejecutor, servicio), no
  identificadores internos.
- **FR-UI-030**: **MUST NOT** exponerse el secreto de autenticación en ninguna forma, ni como
  columna oculta, ni en el estado vacío, ni en un detalle al expandir la fila.
- **FR-UI-031**: Las versiones **retiradas** MUST listarse. Omitirlas escondería justo lo que hay
  que mirar antes de retirar una más.
- **FR-UI-032**: Ver un listado MUST NOT habilitar suspender, reactivar, rotar el secreto, aprobar
  producción ni cualquier acción operativa. Son de **solo lectura**.

---

## Success Criteria *(mandatory)*

- **SC-UI-001**: Los **cinco** listados se consultan desde la interfaz con las columnas declaradas
  por el contrato de backend.
- **SC-UI-002**: Un Partner ve **tres** enlaces; un gestor o el Director Tecnológico ve **cinco**.
  Verificable con ambos públicos sobre la misma sesión de aplicación.
- **SC-UI-003**: Un Partner ve el aviso de alcance; un gestor **no** lo ve. Un Partner sin filas ve
  un vacío que **menciona el acotamiento**.
- **SC-UI-004**: **Ninguna** de las cinco pantallas implementa su propia tabla, paginación o manejo
  de error: las cinco consumen la capa compartida.
- **SC-UI-005**: **El 100 %** de los `400` muestra el mensaje del backend; **cero** se presentan
  como tabla vacía.
- **SC-UI-006**: Un `403` es distinguible de un resultado vacío en los cinco, incluido el Partner
  ante los dos listados de contrato.
- **SC-UI-007**: **Cero** celdas de credencial afirman el motivo de inactividad. **Cero** pantallas
  muestran el secreto.
- **SC-UI-008**: **El 100 %** de los clientes sin alcance configurado se lee como ausente, y
  **ninguno** como ilimitado.
- **SC-UI-009**: **En ninguna** pantalla aparece un recuento total ni un número de página
  navegable.
- **SC-UI-010**: Recorrer cualquier listado por páginas devuelve cada fila exactamente una vez.
- **SC-UI-011**: Un Partner suspendido abre sus tres listados de acceso en **el 100 %** de los
  casos de prueba.

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo de esta capa: índice filtrado por rol, aviso de alcance en el vacío, vacío de dominio, dos entradas de menú para no fusionar consola y portal. |
| Functional Suitability | Cita FR-001 a FR-023 y FR-014a–c del backend. Completitud: los cinco listados, no un sexto de «llamadas rechazadas». Corrección: inactiva ≠ motivo; ausente ≠ ilimitado. |
| Security | Dos guards (no la unión). El secreto no se pinta. El Partner no ve un selector que pida cuentas ajenas. El Director entra a los cinco porque es la autoridad del departamento, no por un atajo de UI. |
| Maintainability | Capa FE separada; reutiliza `shared/informes`. Si la capa común no alcanza, la corrección va allí. |
| Reliability | Distingue `400`, `403`, vacío y fallo reintentable. No compensa el retraso de ingesta. |
| Performance Efficiency | Heredada: primera página en el umbral del backend; paginación por cursor, sin contar el total. |
| Compatibility | Consume el contrato ya publicado. **MUST NOT** pedir campos que el OpenAPI no declara. |
| Flexibility | N/A: no introduce un eje de región ni un despliegue nuevo. |
| Safety | N/A: estos listados no asignan unidades ni clasifican gravedad de un accidente en curso. |

**Conflicto documentado (tie-breaker).** Mostrar *por qué* una credencial está inactiva sería más
reconocible en el momento (Interaction Capability). El backend lo prohíbe porque el registro no
distingue revocación de cascada ni de expiración, y confundirlas es un riesgo de reactivar un
secreto comprometido (Functional Suitability + Security). **No está en juego Safety física.** Ganan
Functional Suitability y Security, que es el default del mecanismo cuando Safety no aplica.

**Traceability**: índice del módulo [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

---

## Assumptions

- **La capa compartida está construida y probada.** Esta spec la consume. Si hiciera falta
  modificarla, la corrección va a `shared/informes`, no a un fork del departamento.
- **El contrato HTTP no se toca.** Los cinco endpoints existen. Esta capa solo los consume.
- **Los roles son los del backend spec**, no una lista nueva: Partner de integración (tres
  listados, `propios`); Desarrollador de APIs, Administrador y **Director Tecnológico** (cinco,
  `todos`).
- **FR-014a cerrado en el permiso de informes, no en `es_gestor()`.** El Director Tecnológico
  entra a los cinco listados vía `es_gestor_informes()` / `ROLES_GESTORES_INFORMES`. La consola
  operativa (`es_gestor()`) sigue sin incluirlo.
- **No se duplica la consola de registros.** «Llamadas rechazadas por límite» ya está cubierta.
- **No se fusionan consola y portal.** Dos entradas de menú, una ruta de índice.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Tableros Z / informes compuestos de Partners | Tienen su propio módulo, aún spec-only en backend |
| Motivo por el que una credencial está inactiva, en la fila de la credencial | ⚠️ Compuesto. Vive en cambios de acceso, con tipo propio |
| Duplicar la consola de registros / llamadas rechazadas por límite | Ya cubierta |
| Exportación a CSV/Excel, gráficas, filtros guardados | Fuera del contrato común |
| Recuento total de resultados | ⛔ Imposible con cursor opaco |
| Modificar la capa compartida | Si hace falta, va a `shared/informes` |
| Acciones operativas (suspender, reactivar, rotar secreto, aprobar producción) | Los listados son de solo lectura |
| Abrir al Director Tecnológico la consola operativa | Fuera de esta capa; aquí solo los cinco listados |
| Workpanels de Emergencias, Analítica (OE4), informes de mantenimiento | Fuera del departamento |
