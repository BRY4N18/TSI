# Feature Specification: OE1 — Posicionamiento y Captación Digital — Frontend

**Feature Branch / capa**: `001-estrategico/OE1-posicionamiento-captacion/frontend`

**Created**: 2026-08-18

**Status**: Implemented (2026-08-18).

**Depends-on**: [`../backend/spec.md`](../backend/spec.md), su contrato OpenAPI y
[`../../acceso-estrategico.md`](../../acceso-estrategico.md) §4.1 y §5. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que los compuestos tácticos y que OE2) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

**Input**: continuar la capa estratégica con las pantallas de los diez informes ya publicados
de OE1; no pintar CAC ni mercados; el hueco de dato de origen se declara, no se inventa.

---

## Contexto

El backend de OE1 **ya publica diez informes** y responde 404 a CAC y a mercados (E1-05, E1-07,
E1-08). Esta capa no calcula nada: pinta lo que el contrato ya corrige.

Entrega **cuatro pantallas nuevas** de lectura de empresa. No se mezclan con:

- los compuestos tácticos de Suscripciones, Ventas o Cuentas;
- el tablero de OE2 (APIs);
- un mapa o un selector de país.

Las cifras tácticas y estas **difieren a propósito**: aquí hay ventana comparada, meta BSC y
agregado de **toda** la empresa. MUST distinguirse en menú y en la propia pantalla.

### La autoridad está partida

No hay un tablero único «OE1» que fusione dinero, embudo y churn. [`acceso-estrategico.md`](../../acceso-estrategico.md)
§4.1 y §5:

| Materia | Quién entra | Pantalla |
|---|---|---|
| Ingreso recurrente y renovación | `DirectorFinanciero` · `Gerente` | **Ingreso** |
| Mezcla de cartera y segmento | `DirectorEstrategia` · `Gerente` (`DirectorFinanciero` también ve segmento) | **Cartera** |
| Captación digital | `DirectorMarketing` · `Gerente` | **Captación** |
| Onboarding y churn | **solo** `Gerente` | **Ciclo** |
| CAC / mercados | **nadie** | — |
| Partner u otros cargos | **nadie** | — |

Cuentas y Clientes **no tiene autoridad de negocio**: E1-09/10/11 no se ceden al Administrador
ni a un director de cuentas. Solo el Gerente.

El `DirectorFinanciero` **MUST NOT** ver Captación ni Ciclo. El `DirectorMarketing` **MUST NOT**
ver Ingreso, Cartera ni Ciclo. El `DirectorEstrategia` **MUST NOT** ver Ingreso (MRR/ARR/renovación),
Captación ni Ciclo; entra a **Cartera**. Un partner **MUST NOT** ver ninguna. El Administrador
no sustituye a estas autoridades. El `Gerente` ve las cuatro.

Cada cargo **MUST** ver **solo sus enlaces**. Un ítem gris o un 403 después de entrar descubriría
la superficie.

El segmento (E1-03) lo pueden ver Finanzas y Estrategia. Vive en **Cartera**, no duplicado en
Ingreso, para no mezclar autoridad dentro de la misma vista.

### El ojo recorre el patrón Z

1. Arriba a la izquierda: métrica principal (héroe), con meta BSC cuando el backend la declara.
2. Arriba a la derecha: **período** (obligatorio) y **comparación** de igual longitud (`ninguna`,
   mes anterior, mismo tramo del año anterior). Son las únicas acciones de esta capa.
3. Diagonal: el visual más grande.
4. Abajo a la derecha: la **lectura** — qué implica el número. Ver no habilita a cambiar un
   plan, aprobar un descuento ni dar de baja una cuenta.

**No hay fichas de cobro ni de persona.** El backend no entrega medio de pago, identificador de
cobro, nombre de prospecto ni país. Los segmentos se nombran por **tipo** de cliente.

### Lo que no se puede mostrar

Hoy el MRR se sostiene en **cuatro suscripciones**. Un 25 % de churn es **un** abandono. El
backend ya envía recuento y `cobertura: parcial`; esta capa MUST pintarlos **junto a la cifra**.
Un héroe de «MRR = 12 000» sin recuento es el defecto que el backend acaba de impedir.

El ARR es **extrapolación**, no compromiso. MUST leerse así.

El embudo MUST mostrar etapas en **cero**. Una etapa ausente se lee como etapa perfecta.

El churn con n bajo MUST verse **sin porcentaje cerrado**, no un 25 % de KPI.

E1-05, E1-07 y E1-08 **no tienen pantalla ni recuadro**. Inventar un CAC de 0 € o «un mercado»
porque no hay columna de país es exactamente lo que el backend prohíbe con el 404. El usuario
acepta resolver esos huecos de origen **después**; esta capa no los adelanta.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Ingreso** | ¿Cuánto ingreso recurrente hay y se renueva? | MRR + recuento de suscripciones + cobertura | Variación frente al período comparado | ARR: **extrapolación**, no compromiso | Tasa de renovación (denominador = vencidas) |
| **Cartera** | ¿De qué tipo y de qué plan sale? | Mezcla por plan | Evolución de la mezcla | Segmento = **tipo**, no país | MRR/ARPU por tipo; desconocidos visibles |
| **Captación** | ¿Cómo llega y cuánto tarda? | Conversión del embudo | Embudo con **ceros** visibles | Cruce Ventas–Cuentas declarado | Velocidad por etapa; ejecutivo por rol/cartera, sin ficha de prospecto |
| **Ciclo** | ¿Dónde se pierde al cliente? | Churn de cohorte **sin %** si n es bajo | Abandono de onboarding contra **catálogo** | Onboarding en proceso **aparte**, no cero días | Tiempo de onboarding |

Ingreso tiene tres informes. El ARR MUST quedar en lectura para no pasar de 6–8 bloques.

Cartera tiene dos. Cabe en Z sin apoyo recargado.

Captación tiene dos. El embudo es el visual; la velocidad es apoyo.

Ciclo tiene tres. El churn no se disfraza de KPI con n=4.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Financiero ve el ingreso recurrente (Priority: P1) 🎯 MVP

El Director Financiero abre **Ingreso**, fija un período y ve de inmediato el MRR con el
**número de suscripciones** que lo sostienen y la etiqueta de cobertura. Abajo lee que el ARR
es una extrapolación. Puede abrir la renovación: el denominador son las **vencidas**, no el
stock de activas.

**Why this priority**: E1-01 es el indicador BSC de la perspectiva Financiera. Una sola vista
demuestra Z, el recuento junto al MRR y que esta lectura no es el compuesto táctico de
Suscripciones.

**Independent Test**: un período con cuatro suscripciones muestra MRR, recuento y `parcial` **en
el mismo bloque**. El ARR no se lee como ingreso firmado. Marketing **no** ve el enlace.

**Acceptance Scenarios**:

1. **Given** un Director Financiero autenticado, **When** abre Ingreso, **Then** ve el patrón Z:
   MRR a la izquierda, período y comparación a la derecha, visual de variación, lectura de ARR
   abajo a la derecha.
2. **Given** el MRR, **When** se muestra, **Then** el recuento de suscripciones y la cobertura
   van **junto a la cifra**. MUST NOT haber un héroe de importe solo.
3. **Given** cuatro suscripciones, **When** se mira, **Then** se lee `parcial` y que la muestra
   es insuficiente. MUST NOT maquillarse como indicador cerrado.
4. **Given** el ARR, **When** se lee, **Then** declara **extrapolación**, no compromiso.
5. **Given** la renovación, **When** se abre el apoyo, **Then** el denominador se lee como
   **vencidas en el período**, no como activas.
6. **Given** las pantallas tácticas de Suscripciones, **When** el Director navega, **Then** esta
   pantalla **no** las reemplaza ni reutiliza su disposición. Se declara la ventana comparada.
7. **Given** un Director de Marketing, un Partner o un Director de Estrategia, **When** busca
   Ingreso, **Then** no ve el enlace y no entra. (Estrategia entra a **Cartera**, no aquí.)

---

### User Story 2 - Ver de qué se compone la cartera (Priority: P2)

El Director de Estrategia (y el Gerente; el Financiero ve el segmento también vía backend, pero
**no** tiene enlace a esta pantalla: el segmento se consulta aquí) abre **Cartera**. El héroe es
la mezcla por plan. El visual muestra su evolución. El segmento es **tipo de cliente**, no
geografía. Los tipos desconocidos **aparecen**.

**Why this priority**: descompone el MRR sin mezclarlo con el importe héroe. Va después de US1
porque primero se ve cuánto hay y luego de qué está hecho.

**Independent Test**: no hay eje de país. Un tipo desconocido no se omite. Marketing no entra.

**Acceptance Scenarios**:

1. **Given** un Director de Estrategia autenticado, **When** abre Cartera, **Then** el héroe es
   la mezcla por plan y el visual es su evolución, no una foto única.
2. **Given** el segmento, **When** se muestra, **Then** agrupa por **tipo**. MUST NOT haber un
   eje de país, estado o mercado.
3. **Given** clientes sin tipo, **When** se mira, **Then** hay un grupo **desconocido** visible.
4. **Given** un Director Financiero o un Director de Marketing, **When** busca Cartera, **Then**
   no ve el enlace. El Financiero ya vio el MRR en Ingreso; el segmento estratégico no es su
   menú. El Gerente sí entra.
5. **Given** un Partner, **When** busca Cartera, **Then** no lo ve y no entra.

> **Nota de autoridad:** el HTTP permite segmento al Financiero. Esta spec **no** le da la
> pantalla Cartera para no duplicar menús. Si dirección exige que Finanzas vea segmento, se
> añade el bloque en Ingreso; no se inventa geografía.

---

### User Story 3 - Ver cómo llega el cliente (Priority: P3)

El Director de Marketing abre **Captación**. El héroe es la conversión del embudo. El visual
grande muestra **todas** las etapas, incluidas las de volumen cero. Abajo se declara el cruce
con Cuentas. La velocidad del ciclo va en apoyo, por etapa, con el ejecutivo identificado por
**rol y cartera**, no por ficha del prospecto.

**Why this priority**: es la mitad «captación digital» del objetivo. Va después del ingreso.

**Independent Test**: una etapa vacía está. El volumen no se pinta creciente. No hay nombre de
prospecto. Finanzas no entra.

**Acceptance Scenarios**:

1. **Given** un Director de Marketing autenticado, **When** abre Captación, **Then** ve embudo
   en el visual grande, período arriba a la derecha y lectura abajo.
2. **Given** una etapa sin pasos, **When** se mira el embudo, **Then** aparece con **cero**.
   MUST NOT desaparecer.
3. **Given** el embudo, **When** se lee, **Then** el volumen **no se presenta creciente** entre
   etapas consecutivas. Si el dato lo viola, se declara; no se «arregla» en pantalla.
4. **Given** la velocidad, **When** se abre el apoyo, **Then** no hay nombre, correo ni ficha
   de prospecto.
5. **Given** un Director Financiero o de Estrategia, **When** busca Captación, **Then** no ve
   el enlace. El Gerente sí.
6. **Given** las pantallas tácticas de Ventas, **When** se navega, **Then** esta pantalla no las
   sustituye.

---

### User Story 4 - El Gerente ve dónde se pierde al cliente (Priority: P3)

El Gerente abre **Ciclo**. El héroe es el churn por cohorte: si n es bajo, **no hay porcentaje
como KPI cerrado**. El visual es el abandono de onboarding contra el **catálogo** de etapas
(ceros visibles). El tiempo de onboarding declara aparte a quien sigue en proceso (no 0 días).

**Why this priority**: OE1 es dueño de estos cuatro para OE5. Solo el Gerente tiene autoridad.
Va con P3 porque el dato es el más anecdótico (3 onboardings, 4 clientes).

**Independent Test**: n=4 no publica un 25 % cerrado. Una etapa de catálogo con 0 completadas
está. Finanzas, Marketing y Estrategia **no** ven el enlace.

**Acceptance Scenarios**:

1. **Given** un Gerente autenticado, **When** abre Ciclo, **Then** ve Z con churn, catálogo de
   abandono y tiempo de onboarding.
2. **Given** una cohorte de 4 clientes, **When** se mira el churn, **Then** se lee **sin muestra
   suficiente** / porcentaje ausente, no un 25 % de tablero.
3. **Given** una etapa de onboarding del catálogo sin completadas, **When** se mira el abandono,
   **Then** aparece con **cero**. MUST NOT un 100 % por omitirla.
4. **Given** clientes aún en proceso, **When** se mira el tiempo, **Then** van **aparte**, no
   como cero días.
5. **Given** un Director Financiero, de Estrategia o de Marketing, **When** busca Ciclo, **Then**
   no ve el enlace y no entra.

---

### User Story 5 - CAC y mercados no se fingen (Priority: P1)

En las cuatro pantallas **no hay** recuadro, pestaña ni enlace de CAC, mercados activos ni MRR
por mercado. El tablero no ofrece 0 € de adquisición ni «un mercado» porque falta la columna.

**Why this priority**: el fallo sería silencioso y grave. Misma prioridad que el MVP: si se
pinta de más, US1 miente el nombre «internacional».

**Independent Test**: ninguna de las cuatro contiene CAC ni mapa. No hay ruta de pantalla para
E1-05/07/08.

**Acceptance Scenarios**:

1. **Given** cualquiera de las cuatro pantallas, **When** se recorre, **Then** **no** hay un
   bloque de CAC, de mercados ni de mapa.
2. **Given** un período, **When** se muestra Ingreso o Cartera, **Then** no se lee «mercado
   único» ni «CAC = 0».
3. **Given** el menú, **When** un Director de Expansión busca mercados de OE1, **Then** no hay
   enlace. (El hueco de país se resuelve en origen, no aquí.)

---

### Edge Cases

- **Período vacío de flujo.** Vacío explícito en embudo/movimientos de ciclo; el MRR de stock
  no se pinta como 0 si hay vigentes.
- **Cuatro suscripciones.** Recuento y `parcial` visibles; no se ocultan.
- **Comparación año anterior sin ventana.** Ausente **con motivo**, no error de pantalla.
- **Una zona falla.** El resto sigue; la zona fallida lo dice.
- **Sin autoridad.** Cada cargo solo ve sus enlaces; partner ninguna.
- **Dato sensible.** Ninguna pantalla muestra medio de cobro, id de pago, ficha de prospecto
  ni país, **tampoco al Gerente**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente cuatro pantallas** —Ingreso, Cartera,
  Captación, Ciclo— y MUST NOT añadir tarjetas a los compuestos tácticos de Suscripciones,
  Ventas o Cuentas.
- **FR-UI-002**: Las cuatro pantallas MUST mostrar **los diez informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT inventar CAC/mercados ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**. MUST NOT ser una grilla de diez
  tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar **6–8 bloques** simultáneos.
- **FR-UI-005**: El **período** es obligatorio. La **comparación** (`ninguna`, mes anterior,
  mismo tramo del año anterior) es la única otra acción. Un cambio MUST refrescar todas las
  zonas. MUST NOT inventarse exportación, filtro de cliente ni filtro de país.
- **FR-UI-006**: Un período sin datos de **flujo** MUST verse como vacío, distinguible de ceros
  reales (etapa de embudo con cero pasos).
- **FR-UI-007**: El MRR MUST mostrar recuento de suscripciones y cobertura **en el mismo
  bloque** que el importe.
- **FR-UI-008**: El ARR MUST leerse como **extrapolación**, no como ingreso comprometido.
- **FR-UI-009**: La renovación MUST declarar denominador de **vencidas**.
- **FR-UI-010**: Cartera MUST agrupar por **tipo** y por **plan**. MUST NOT agrupar por país.
- **FR-UI-011**: Los tipos desconocidos MUST ser visibles.
- **FR-UI-012**: El embudo MUST mostrar etapas en cero. MUST NOT ocultarlas.
- **FR-UI-013**: El embudo MUST NOT pintar un volumen creciente entre etapas como si fuera
  correcto; si el dato lo viola, se declara.
- **FR-UI-014**: La velocidad MUST identificar ejecutivo por rol/cartera, sin ficha de
  prospecto.
- **FR-UI-015**: El churn con n bajo MUST verse sin porcentaje cerrado.
- **FR-UI-016**: El abandono de onboarding MUST partir del catálogo de etapas, con ceros.
- **FR-UI-017**: El tiempo de onboarding MUST separar «en proceso» de los completados.
- **FR-UI-018**: Las cuatro pantallas MUST NOT mostrar CAC, mercados, mapa, medio de cobro,
  id de pago ni contacto.
- **FR-UI-019**: Ingreso MUST ser visible para `DirectorFinanciero` y `Gerente`. Cartera para
  `DirectorEstrategia` y `Gerente`. Captación para `DirectorMarketing` y `Gerente`. Ciclo
  **solo** `Gerente`. El resto MUST NOT verlas en el menú ni entrar.
- **FR-UI-020**: Ver MUST NOT habilitar cambiar plan, cobrar, ni dar de baja. Abajo a la
  derecha hay **lectura**, no una acción de negocio.
- **FR-UI-021**: Si el backend declara cobertura, recuento, alcance o falta, la pantalla MUST
  mostrarlo junto a la cifra.
- **FR-UI-022**: Una comparación sin ventana anterior MUST mostrarse ausente **con motivo**.
- **FR-UI-023**: MUST NOT existir un enlace que fusione estas historias con los compuestos
  tácticos de Suscripciones, Ventas o Cuentas.
- **FR-UI-024**: Ingreso y Captación MUST declararse distintas de esos compuestos (ventana
  comparada, no recorte operativo).

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director Financiero identifica MRR, recuento y si la cobertura es parcial en
  **menos de 5 segundos** en Ingreso, sin leer un párrafo.
- **SC-F02**: No existe un estado de pantalla en el que se vea el MRR y no se vea, en el mismo
  bloque, el recuento de suscripciones.
- **SC-F03**: El ARR no se puede leer como compromiso: la extrapolación está a la vista.
- **SC-F04**: Una etapa de embudo en cero permanece visible.
- **SC-F05**: Un churn con n=4 no se presenta como porcentaje de tablero cerrado.
- **SC-F06**: Ingreso se distingue del compuesto táctico de Suscripciones: no reutiliza su
  disposición y declara la ventana comparada.
- **SC-F07**: No hay eje de país ni mapa en ninguna de las cuatro.
- **SC-F08**: No hay recuadro de CAC ni de mercados.
- **SC-F09**: El Financiero accede **solo** a Ingreso. Marketing **solo** a Captación.
  Estrategia **solo** a Cartera. El Gerente a las cuatro. Un partner a ninguna.
- **SC-F10**: En ninguna aparecen medio de cobro, id de pago, ficha de prospecto ni país.
- **SC-F11**: Un período sin datos de flujo no se parece a un período con ceros de etapa.
- **SC-F12**: Cada vista principal queda en **8 o menos** bloques.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las cuatro; no es un listado táctico.
- **Zona Z**: métrica, período/comparación, visual grande, lectura.
- **Período y comparación**: únicos controles.
- **Marca de parcial / recuento / extrapolación**: impide leer un KPI cerrado o un compromiso.
- **Lectura**: el bloque de abajo a la derecha; no es un botón de negocio.

---

## Assumptions

- El backend de los diez publicados está en servicio. Esta capa no calcula cifras.
- El período es obligatorio; no hay valor por defecto que sustituya desde / hasta /
  granularidad.
- Huecos de CAC y geografía: el usuario los resolverá en origen **después**. Esta spec no
  adelanta pantallas.
- El dato de demostración (4 suscripciones, 4 clientes) es anecdótico; `parcial` es la
  lectura correcta, no un defecto de UI.
- El patrón Z ya está demostrado en táctico y en OE2; esta capa lo copia (no extrae un
  `shared/` de OE2: se copia el cascarón).
- Los compuestos tácticos de Suscripciones, Ventas y Cuentas no se tocan ni se retiran.
- No hay exportación ni programación de envío.
- El mínimo de muestra lo resuelve el backend. Esta capa no ofrece un control extra de umbral.
- E1-05/07/08 siguen sin fuente; no reaparecen por inferencia.
- Los frontends de OE1–OE6 de informes estratégicos ya están implementados en sus capas.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Compuestos tácticos de Suscripciones, Ventas, Cuentas | Ya existen |
| CAC, mercados, mapa | El origen no tiene costos ni país |
| Un tablero de diez iguales | Rompe Z y la Ley de Hick |
| Medios de cobro, ficha de prospecto | Exclusión del backend |
| Acciones de negocio (cambiar plan, cobrar, dar de baja) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Partner, Administrador como autoridad de Ciclo | No están en §4.1 / §5 |
| Cambiar OpenAPI, SQL o permisos del backend | Depends-on |
| Frontend de OE3, OE4 | Otra capa |
| Tablero integral CU-E01 / escenarios / reporte gerencial | Contrato §11 |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período + comparación, menú por rol. SC-F01, SC-F12. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (recuento, parcial, extrapolación, ceros de embudo, churn sin %). No inventa CAC ni mercados. |
| **Security** | Reutiliza quién entra. Partner no ve la cartera. Sin cobro ni ficha. Ciclo solo Gerente. |
| **Safety** | Un MRR de 4 filas pintado como KPI cerrado o un CAC = 0 induciría una decisión financiera falsa. FR-UI-007 y FR-UI-018 lo impiden. No hay cadena de despacho. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras; comparación ausente se declara. |
| **Maintainability** | Capa `frontend/` separada; las pantallas copian Z ya usado, sin extraer librería de OE2. |
| **Performance Efficiency** | Heredada del backend. Umbral: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio externo en esta capa. |
| **Flexibility** | El objetivo es internacional y **no mide mercados**. Se declara; no se inventa geografía. |

**Traceability**: índice [`../OE1-posicionamiento-captacion.md`](../OE1-posicionamiento-captacion.md).
