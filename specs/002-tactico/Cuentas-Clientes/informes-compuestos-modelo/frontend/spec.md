# Feature Specification: Informes Compuestos de Cuentas y Clientes — Frontend

**Feature Branch / capa**: `002-tactico/Cuentas-Clientes/informes-compuestos-modelo/frontend`

**Created**: 2026-08-18

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que Emergencias, Red Operativa, Ventas, Suscripciones,
Soporte y Partners) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

---

## Contexto

El backend de este módulo **ya publica los nueve informes** de OT17, OT04 y OT18. No hay vigilados
que omitir: los nueve se pintan. Dos indicadores BSC tienen fuente por primera vez: churn por
cohorte y tiempo de onboarding.

Esta capa entrega **tres pantallas nuevas**. No se mezclan con los listados simples, con la
gestión de cuenta del cliente ni con el flujo de incorporación operativa: esos se quedan como
están.

### La diferencia: no hay un solo jefe

Como en Suscripciones y Red Operativa, la autoridad **está repartida** (SRS §5.1, backend FR-030):

| Materia | Quién la gobierna | Qué ve |
|---|---|---|
| **Ciclo de vida** | Administrador | Churn, antigüedad, ocupación, cuentas en riesgo |
| **Incorporación** | Administrador | Tiempo de onboarding, embudo, aprobación |
| **Acceso técnico** | Director Tecnológico **y** Administrador | Concurrencia de sesiones y roles incompatibles |

El Director Tecnológico **MUST NOT** ver ciclo de vida ni incorporación. No hay un tablero único
«Cuentas» que fusione las tres materias «porque es el mismo departamento». Eso es el error que el
backend ya impide.

Cada cargo **MUST** ver **solo sus enlaces**. Un ítem gris o un acceso denegado después de entrar
descubrirá al otro cargo.

El ojo recorre el **mismo patrón Z**:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que dé de baja una cuenta
   o cambie un rol. Ver no habilita a decidir.

**No hay fichas de persona ni de sesión.** El backend no entrega token, nombre, correo, teléfono,
género ni fecha de nacimiento. El informe de roles muestra **clave de usuario**, nunca el nombre.

### Las cifras que no se pueden mostrar solas

Hoy **solo el 9,5 %** de los usuarios tiene organización declarada. Pintar «1 de 10 usuarios» sin
la cobertura se lee como ocupación real. El backend ya envía `pct_cobertura_pertenencia`; esta
capa MUST pintarla junto a la ocupación.

El embudo, si solo mostrara las etapas que alguien completó, afirmaría **100 % de finalización**.
MUST aparecer **todas** las etapas del catálogo, incluidas las que tienen cero clientes.

La duración de sesión, si ocultara cuántas no cerraron, describiría **el 27 %** como si fuera el
total. MUST verse `sesiones_sin_cierre` junto a la mediana.

### Qué entra en cada pantalla

| Pantalla | Audiencia | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|---|
| **Ciclo de vida** | Administrador | ¿Quién se va y quién está al límite? | Churn por **cohorte de alta** | Ocupación: usuarios, tope y **cobertura de pertenencia** | Cuentas en riesgo: sin actividad conocida **≠** 0 días | Antigüedad media |
| **Incorporación** | Administrador | ¿Dónde se atasca el alta? | Tiempo de onboarding (en proceso **aparte**) | Embudo: **todas** las etapas del catálogo, ceros incluidos | Tasa de aprobación | — |
| **Acceso** | Tecnológico y Admin | ¿Cuánta gente entra a la vez y quién acumula de más? | Concurrencia máxima **por solape**, no por inicios | Franjas; sesión que cruza medianoche en **ambas** | Roles incompatibles: **cero filas** si no hay política | Duración con `sesiones_sin_cierre` |

Ciclo de vida tiene cuatro informes. Antigüedad MUST quedar en segundo plano para no pasar de
6–8 bloques.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Administrador sostiene el ciclo de vida (Priority: P1) 🎯 MVP

El Administrador abre **Ciclo de vida**, elige un período y ve de inmediato el churn por cohorte
de alta, no por mes de baja. El visual grande es la ocupación frente al tope, **con la cobertura
del 9,5 % a la vista**. Abajo, quién lleva tiempo sin entrar: nunca haber tenido sesión **no** se
lee como cero días. La antigüedad se puede abrir sin competir con el héroe.

**Why this priority**: contiene el BSC de churn. Una sola vista basta para demostrar el patrón Z,
la cohorte de alta y que el Tecnológico no ve esta materia.

**Independent Test**: un cliente de alta en enero y baja en junio aparece en la cohorte de enero.
Ocupación y cobertura van en el mismo bloque. Un Director Tecnológico **no** ve el enlace ni
entra. Período vacío → vacío, no 0 %.

**Acceptance Scenarios**:

1. **Given** un Administrador autenticado, **When** abre Ciclo de vida, **Then** ve el patrón Z.
2. **Given** el churn, **When** se muestra, **Then** las barras o filas son por **cohorte de
   alta**. MUST NOT agruparse por mes de baja.
3. **Given** la ocupación, **When** se muestra, **Then** se ven usuarios, tope y
   `pct_cobertura_pertenencia` **juntos**. MUST NOT haber un héroe de % ocupación solo.
4. **Given** un cliente sin plan, **When** aparece, **Then** la ocupación se lee **sin dato**,
   nunca 0 %.
5. **Given** un cliente sin ninguna sesión, **When** se leen las cuentas en riesgo, **Then**
   aparece como **sin actividad conocida**, no con 0 días.
6. **Given** un Director Tecnológico, un Cliente o un Operador, **When** intenta entrar,
   **Then** no ve la pantalla.

---

### User Story 2 - El Administrador vigila la incorporación (Priority: P2)

El Administrador abre **Incorporación**. El héroe es cuántos días tarda el alta, con quienes
aún están en proceso **fuera de la mediana**. El visual grande es el embudo: las etapas que
nadie ha completado **aparecen en cero**. Abajo, cuántas solicitudes se aprueban.

**Why this priority**: el segundo BSC y el informe que dice dónde arreglar el proceso. Un
embudo mal pintado afirmaría un proceso perfecto.

**Independent Test**: una etapa del catálogo sin ningún cliente **está** en el embudo con cero.
Un cliente en proceso no aporta cero días. El Tecnológico no entra.

**Acceptance Scenarios**:

1. **Given** el Administrador, **When** abre Incorporación, **Then** el héroe es el tiempo, el
   visual es el embudo y la aprobación está abajo a la derecha.
2. **Given** el embudo, **When** se muestra, **Then** aparecen **todas** las etapas del
   catálogo, en su orden, incluidas las de cero clientes. MUST NOT omitir la etapa fantasma.
3. **Given** la nota de catálogo del backend, **When** hay embudo, **Then** se lee junto al
   visual.
4. **Given** clientes aún en proceso, **When** se muestra el tiempo, **Then** van en
   `en_proceso` y **no** hunden la mediana a cero.
5. **Given** un Director Tecnológico, **When** busca esta pantalla, **Then** no la ve en su
   menú y no entra.

---

### User Story 3 - El Director Tecnológico controla el acceso (Priority: P3)

El Director Tecnológico abre **Acceso**. El héroe es la concurrencia máxima por **solape de
intervalos**, no el recuento de inicios. El visual reparte por franja; una sesión que cruza la
medianoche cuenta en **ambas**, y la pantalla lo dice. Abajo, usuarios con un par de roles
**declarado incompatible**: si no hay política, la zona está **vacía** —el multi-rol es el
mecanismo previsto—. La duración declara cuántas sesiones no cerraron.

**Why this priority**: es la única materia que el Tecnológico gobierna aquí. Pintarla en el
mismo tablero que el churn le daría el ciclo de vida.

**Independent Test**: diez inicios repartidos y diez simultáneos no se leen igual. Sin pares
declarados, cero filas de incompatibles. El Administrador también entra. Un Cliente no.

**Acceptance Scenarios**:

1. **Given** el Director Tecnológico, **When** abre Acceso, **Then** ve el patrón Z con
   concurrencia, franjas y roles.
2. **Given** la concurrencia, **When** se muestra, **Then** hay `concurrencia_maxima` **y**
   `sesiones_iniciadas`. MUST NOT titularse como si el recuento de inicios fuera la carga.
3. **Given** sesiones sin cierre, **When** se mira la duración, **Then** `sesiones_sin_cierre`
   está **a la vista** junto a la mediana.
4. **Given** una sesión que cruza medianoche, **When** se miran las franjas, **Then** cuenta en
   las dos y se declara el solape.
5. **Given** usuarios con dos roles y **sin** política de pares, **When** se lee incompatibles,
   **Then** hay **cero filas**. MUST NOT marcar «más de un rol» como hallazgo.
6. **Given** un par declarado, **When** hay esa combinación, **Then** aparece `idusuario` y
   ambos roles, **nunca** el nombre de la persona.
7. **Given** un Administrador, **When** navega, **Then** también ve Acceso, además de las otras
   dos.
8. **Given** un Cliente o un Operador, **When** busca Acceso, **Then** no lo ve y no entra.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no churn 0 % ni concurrencia 0.
- **Cobertura 9,5 %.** Se lee junto a la ocupación; no se esconde en un pie.
- **Etapa fantasma.** Cero visible, no omitida.
- **Sesión abierta.** Fuera de la mediana de duración; contada aparte.
- **Pares vacíos.** Informe de roles vacío; no es un error.
- **Cliente sin plan.** Ocupación sin dato.
- **Una zona falla y las otras no.** El resto sigue.
- **Sin autoridad.** Tecnológico fuera de ciclo e incorporación. Cliente, Operador y cargos
  ajenos fuera de las tres.
- **Dato sensible.** Ninguna pantalla muestra token, nombre, correo, teléfono ni identidad,
  **tampoco al Administrador**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Ciclo de vida,
  Incorporación, Acceso— y MUST NOT añadir tarjetas a los listados simples, a la gestión de
  cuenta ni a la incorporación operativa.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los nueve informes que el backend publica**,
  cada uno en la pantalla de su materia. MUST NOT inventar un décimo ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**. MUST NOT ser una grilla de tarjetas
  del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques**. En Ciclo de vida, la
  antigüedad MUST quedar en segundo plano.
- **FR-UI-005**: El período MUST ser la única acción de filtrado global. MUST NOT inventarse
  exportación. `dias_inactividad`, `mes_cohorte` y `pares_incompatibles` MUST NOT ser un
  segundo constructor de informes en el MVP: viajan los defectos del servidor (pares vacíos).
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de ceros reales.
- **FR-UI-007**: Un denominador ausente o un cliente sin plan MUST verse **sin dato**, nunca
  0 % de ocupación.
- **FR-UI-008**: En Ciclo de vida, el churn MUST agruparse por **cohorte de alta**.
- **FR-UI-009**: En Ciclo de vida, ocupación MUST mostrar usuarios, tope y
  **cobertura de pertenencia** en el mismo bloque (backend nota_cobertura).
- **FR-UI-010**: En Ciclo de vida, sin actividad conocida MUST distinguirse de N días sin
  sesión. MUST NOT pintarse 0 días para quien nunca entró.
- **FR-UI-011**: En Incorporación, el embudo MUST mostrar **todas** las etapas del catálogo, en
  orden, con ceros. MUST leerse `nota_catalogo` si el backend la envía.
- **FR-UI-012**: En Incorporación, un cliente en proceso MUST contarse aparte y MUST NOT
  aportar cero días a la mediana.
- **FR-UI-013**: En Acceso, concurrencia MUST mostrarse como solape (`concurrencia_maxima`)
  junto a inicios. MUST NOT titularse como recuento de logins.
- **FR-UI-014**: En Acceso, `sesiones_sin_cierre` MUST verse junto a la duración mediana.
- **FR-UI-015**: En Acceso, el cruce de medianoche MUST declararse (`nota_solape` si el backend
  la envía).
- **FR-UI-016**: En Acceso, sin política de pares, roles incompatibles MUST mostrar **cero
  filas**, no un recuento de multi-rol.
- **FR-UI-017**: En Acceso, un hallazgo de roles MUST mostrar `idusuario` y ambos roles, nunca
  el nombre de la persona.
- **FR-UI-018**: Las tres pantallas MUST NOT mostrar token, nombre, correo, teléfono, género ni
  fecha de nacimiento, para ningún rol.
- **FR-UI-019**: Ciclo de vida e Incorporación MUST ser visibles solo para **Administrador**.
  Acceso MUST ser visible para **Director Tecnológico** y **Administrador**. Cliente, Operador
  y cargos ajenos MUST NOT verlas en el menú ni entrar.
- **FR-UI-020**: Ver un informe MUST NOT habilitar dar de baja, cambiar un rol ni cerrar una
  sesión. Hay **lectura**, no acción de negocio.
- **FR-UI-021**: Si el backend declara cobertura, catálogo o solape, la pantalla MUST
  mostrarlo junto a la cifra.
- **FR-UI-022**: MUST NOT existir un enlace que fusione las tres historias en un tablero único
  de departamento, ni que las mezcle con listados u onboarding operativo.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Administrador identifica el churn por cohorte de alta en **menos de 5 segundos**.
- **SC-F02**: No existe un estado de pantalla con ocupación y sin cobertura de pertenencia en
  el mismo bloque.
- **SC-F03**: Un cliente sin sesiones no se lee como 0 días. Un cliente sin plan no se lee
  como 0 % de ocupación.
- **SC-F04**: El embudo muestra etapas con cero; no afirma 100 % de finalización por omitirlas.
- **SC-F05**: Un cliente en proceso no aporta cero días a la mediana visible.
- **SC-F06**: Concurrencia e inicios se distinguen. `sesiones_sin_cierre` está a la vista.
- **SC-F07**: Sin pares incompatibles, la zona de roles está vacía. Con un par, aparece la
  clave, no el nombre.
- **SC-F08**: El Director Tecnológico ve Acceso y **no** Ciclo ni Incorporación, ni en el menú.
  El Administrador ve las tres.
- **SC-F09**: En ninguna de las tres aparecen token, nombre, correo ni mapas.
- **SC-F10**: Un período sin datos no se parece a un período con ceros.
- **SC-F11**: Las tres pantallas se distinguen de los listados y de la incorporación operativa.
- **SC-F12**: Ciclo de vida no presenta cuatro bloques del mismo peso; la vista principal
  queda en **8 o menos**.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni el alta operativa.
- **Zona Z**: métrica, período, visual grande, lectura.
- **Período**: único filtro global; por defecto los últimos 30 días.
- **Par ocupación/cobertura**: usuarios, tope y cobertura; no son tres widgets sueltos.
- **Catálogo de etapas**: el embudo se lee contra él, no contra lo observado.
- **Lectura**: el bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los nueve publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días.
- `pares_incompatibles` viaja vacío por defecto; esta capa no ofrece un editor de política en
  el MVP.
- El patrón Z ya está demostrado; esta capa lo copia.
- Los listados simples, la gestión de cuenta y la incorporación operativa no se tocan ni se
  retiran.
- No hay exportación en esta pasada.
- La cobertura de pertenencia (~9,5 %) es correcta y no representativa de la cartera real; la
  pantalla la declara.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Listados simples, gestión de cuenta, incorporación operativa | Ya existen; no se les añaden tarjetas |
| Un tablero único de nueve iguales | Rompe el Z, Hick y la autoridad partida |
| Editor de pares incompatibles | El vacío por defecto es deliberado |
| Token, identidad, mapas | Exclusión constitucional |
| Acciones (baja, cambio de rol, cierre de sesión) | Ver no habilita a decidir |
| Exportar | El backend no lo ofrece |
| Cliente, Operador, cargos ajenos | No son la autoridad de estos compuestos |
| Cambiar OpenAPI o permisos del backend | Depends-on |
| Frontend de otros departamentos | Mismo patrón, otro módulo |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, ≤8 bloques, menú por materia, par ocupación/cobertura, embudo con ceros. SC-F01, SC-F02, SC-F08. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (cohorte de alta, cobertura, etapa fantasma, duración con abiertas aparte, pares vacíos). |
| **Security** | Dos audiencias, no una unión. Exclusión constitucional también en pantalla. Tecnológico fuera de ciclo e incorporación. |
| **Safety** | Un 100 % de embudo o una ocupación sin cobertura se lee mal al decidir altas o cupos; FR-UI-009 y FR-UI-011 lo impiden. No hay despacho. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; cáscara Z copiada, no extraída. |
| **Performance Efficiency** | Heredada del backend. Héroe reconocible en <5 s. |
| **Compatibility** | No aplica. |
| **Flexibility** | No aplica: sin eje de región. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
