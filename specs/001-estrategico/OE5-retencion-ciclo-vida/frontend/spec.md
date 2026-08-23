# Feature Specification: OE5 — Retención y Ciclo de Vida — Frontend

**Feature Branch / capa**: `001-estrategico/OE5-retencion-ciclo-vida/frontend`

**Created**: 2026-08-18

**Status**: Implemented (2026-08-18).

**Depends-on**: [`../backend/spec.md`](../backend/spec.md), su contrato OpenAPI y
[`../../acceso-estrategico.md`](../../acceso-estrategico.md) §4.5, §5 y §6. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que los compuestos tácticos y que OE1/OE2) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

**Input**: continuar la capa estratégica con las pantallas de los nueve informes ya publicados
de OE5; no pintar NPS ni reportes sin corrección; renovación, churn y onboarding se leen en OE1,
no se duplican aquí.

---

## Contexto

El backend de OE5 **ya publica nueve informes** y responde 404 a NPS, a reportes sin corrección
(E5-01, E5-11) y a las cuatro rutas que son de OE1 (E5-09/10/13/14). Esta capa no calcula nada:
pinta lo que el contrato ya corrige.

Entrega **cuatro pantallas nuevas** de lectura de empresa. No se mezclan con:

- los compuestos tácticos de Soporte, Suscripciones o Cuentas;
- el tablero de OE1 (Captación / Ciclo) ni el de OE2 (APIs);
- una encuesta fingida ni un recuadro de «reportes impecables».

Las cifras tácticas y estas **difieren a propósito**: aquí hay ventana comparada, meta BSC y
agregado de **toda** la empresa. MUST distinguirse en menú y en la propia pantalla.

### La autoridad está partida

No hay un tablero único «OE5» que fusione SLA, dinero retenido y riesgo. [`acceso-estrategico.md`](../../acceso-estrategico.md)
§4.5, §5 y §6:

| Materia | Quién entra | Pantalla |
|---|---|---|
| Compromiso de servicio (SLA, carga, reincidencia) | `GerenteExitoCliente` · `Gerente` | **Servicio** |
| Retención neta de ingresos | `DirectorFinanciero` · `Gerente` | **Ingresos retenidos** |
| Plan, movimientos y antigüedad | `DirectorEstrategia` · `Gerente` | **Planes** |
| Cuentas en riesgo (cruce de cuatro señales) | **solo** `Gerente` | **Riesgo** |
| NPS / reportes sin corrección | **nadie** | — |
| Partner u otros cargos | **nadie** | — |

Cuentas y Clientes **no tiene autoridad de negocio**: E5-15 (tramo de cuenta) y las refs de
onboarding/churn no se ceden al Administrador. El Gerente cubre ese hueco (§5).

El `GerenteExitoCliente` **MUST NOT** ver Ingresos retenidos, Planes ni Riesgo. El
`DirectorFinanciero` **MUST NOT** ver Servicio, Planes ni Riesgo. El `DirectorEstrategia`
**MUST NOT** ver Servicio, Ingresos retenidos ni Riesgo. Un partner **MUST NOT** ver ninguna.
El Administrador no sustituye a estas autoridades. El `Gerente` ve las cuatro.

Cada cargo **MUST** ver **solo sus enlaces**. Un ítem gris o un 403 después de entrar descubriría
la superficie.

> **Nota de autoridad HTTP vs menú.** El backend permite SLA por plan al Éxito de Cliente y
> movimientos de plan al Financiero. Esta spec **no** abre Servicio al Estratega ni Planes al
> Financiero: mezclaría carga de agentes con dinero, o NRR con catálogo. SLA por plan y
> movimientos viven en **Planes** (Estrategia). El NRR vive en **Ingresos retenidos** (Finanzas).
> El SLA consolidado vive en **Servicio** (Éxito de Cliente). Si dirección exige el desglose por
> plan al Éxito de Cliente, se añade el bloque en Servicio; no se abre Planes «por si acaso».

### El ojo recorre el patrón Z

1. Arriba a la izquierda: métrica principal (héroe), con meta BSC cuando el backend la declara.
2. Arriba a la derecha: **período** (obligatorio) y **comparación** de igual longitud (`ninguna`,
   mes anterior, mismo tramo del año anterior). Son las únicas acciones de esta capa.
3. Diagonal: el visual más grande.
4. Abajo a la derecha: la **lectura** — qué implica el número. Ver no habilita a reabrir un
   ticket, cambiar un plan ni llamar a una cuenta.

**No hay fichas de persona ni de cobro.** El backend no entrega texto de ticket, notas internas,
nombre de agente, medio de pago ni coordenadas. El agente se nombra por **identificador y cola**,
no por desempeño personal.

### Lo que no se puede mostrar

Hoy el SLA se sostiene en **catorce tickets**. Un punto de incumplimiento mueve la cifra **siete
puntos**. El backend ya envía recuento y `cobertura: parcial`; esta capa MUST pintarlos **junto a
la cifra**. Un héroe de «SLA = 95 %» sin recuento es el defecto que el backend acaba de impedir.

Un período **sin tickets cerrados con compromiso** MUST verse como **vacío**, no como 0 % de
cumplimiento. No hubo nada que cumplir.

El NRR MUST mostrar **expansión, contracción y churn por separado**. Un neto del 100 % puede ser
estabilidad o un empate entre altas y bajas; son lecturas opuestas. MUST NOT copiar el stub
táctico de expansión en cero.

Una cuenta con **una sola señal** MUST NOT aparecer en riesgo. Si falta una fuente, MUST decirse
**cuál**, no un semáforo cerrado.

E5-01 y E5-11 **no tienen pantalla ni recuadro**. Pintar un NPS de 0 o «todos los reportes
corregidos» porque no hay encuesta ni tabla de entregas es exactamente lo que el backend prohíbe
con el 404. El usuario acepta resolver esos huecos de origen **después**; esta capa no los
adelanta.

E5-09/10/13/14 **no tienen recuadro en OE5**. Renovación, churn y onboarding se leen en las
pantallas de OE1. Un enlace de OE5 que reimplemente esas cifras mentiría al contrato §7.1.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Servicio** | ¿Se cumple el compromiso de tiempo? | SLA + recuento de cerrados con compromiso + cobertura | Evolución del incumplimiento | Tickets **sin compromiso** aparte; vacío ≠ 0 % | Carga por agente (no desempeño); reincidencia por cliente×servicio |
| **Ingresos retenidos** | ¿La cartera crece o se erosiona? | NRR | Desglose expansión / contracción / churn | Precio **congelado** en la suscripción; no es el stub de expansión 0 | — |
| **Planes** | ¿El plan pagado recibe lo pagado, y cuánto duran las cuentas? | SLA por plan | Movimientos de plan **aprobados**, con delta | Antigüedad de **activas**; cerradas aparte | — |
| **Riesgo** | ¿Qué cuenta se está yendo de verdad? | Cuentas con **≥2 señales** | Señales presentes | Fuentes **faltantes** nombradas; una señal no basta | — |

Servicio tiene cuatro informes. La carga y la reincidencia MUST quedar en apoyo plegado para no
pasar de 6–8 bloques.

Ingresos retenidos tiene uno. El desglose llena el visual; el alcance llena la lectura.

Planes tiene tres. Cabe en Z sin apoyo recargado.

Riesgo tiene uno. El cruce no se disfraza de semáforo con una sola señal.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Gerente de Éxito de Cliente ve si se cumple el SLA (Priority: P1) 🎯 MVP

El Gerente de Éxito de Cliente abre **Servicio**, fija un período y ve de inmediato el
cumplimiento con el **número de tickets cerrados con compromiso** y la etiqueta de cobertura.
Abajo lee los tickets **sin compromiso** aparte. Un período sin cerrados con compromiso se lee
como vacío, no como 0 %. Puede abrir la carga por agente: mide **cola**, no desempeño. La
reincidencia agrupa **cliente y servicio**.

**Why this priority**: E5-04 es el indicador BSC de la perspectiva Cliente que **sí tiene
fuente**. Una sola vista demuestra Z, el recuento junto al %, y que esta lectura no es el
compuesto táctico de Soporte.

**Independent Test**: un período con catorce tickets muestra SLA, recuento y `parcial` **en el
mismo bloque**. Un período sin compromiso se ve vacío. Finanzas **no** ve el enlace.

**Acceptance Scenarios**:

1. **Given** un Gerente de Éxito de Cliente autenticado, **When** abre Servicio, **Then** ve el
   patrón Z: SLA a la izquierda, período y comparación a la derecha, evolución del
   incumplimiento en diagonal, lectura de «sin compromiso» abajo a la derecha.
2. **Given** el SLA, **When** se muestra, **Then** el recuento de cerrados con compromiso y la
   cobertura van **junto a la cifra**. MUST NOT haber un héroe de porcentaje solo.
3. **Given** catorce tickets, **When** se mira, **Then** se lee `parcial` y que la muestra es
   insuficiente. MUST NOT maquillarse como indicador cerrado.
4. **Given** un período sin tickets cerrados con compromiso, **When** se mira, **Then** la zona
   está **vacía**, no en 0 %.
5. **Given** la carga por agente, **When** se abre el apoyo, **Then** no hay nombre de persona
   ni juicio de desempeño; se declara carga de trabajo.
6. **Given** las pantallas tácticas de Soporte, **When** el cargo navega, **Then** esta pantalla
   **no** las reemplaza ni reutiliza su disposición. Se declara la ventana comparada.
7. **Given** un Director Financiero, un Partner o un Director de Estrategia, **When** busca
   Servicio, **Then** no ve el enlace y no entra.

---

### User Story 2 - El Director Financiero ve si la cartera se erosiona (Priority: P2)

El Director Financiero abre **Ingresos retenidos**. El héroe es el NRR. El visual muestra
**expansión, contracción y churn** por separado. La lectura declara precio congelado en la
suscripción, no la tarifa vigente del catálogo.

**Why this priority**: E5-02 es indicador BSC (≥105 % anual, a calibrar). Va después de US1
porque el SLA explica en parte por qué un cliente se queda.

**Independent Test**: el neto no aparece solo. Un 100 % se lee con sus tres componentes. Éxito
de Cliente no entra.

**Acceptance Scenarios**:

1. **Given** un Director Financiero autenticado, **When** abre Ingresos retenidos, **Then** el
   héroe es el NRR y el visual descompone expansión, contracción y churn.
2. **Given** el NRR, **When** se muestra, **Then** MUST NOT heredarse un «expansión = 0» de
   un compuesto táctico. Si un componente viene vacío, se declara; no se finge cero de negocio.
3. **Given** la lectura, **When** se mira, **Then** el alcance habla de precio **congelado**, no
   de tarifa de catálogo.
4. **Given** un Gerente de Éxito de Cliente o un Director de Marketing, **When** busca Ingresos
   retenidos, **Then** no ve el enlace. El Gerente sí entra.
5. **Given** un Partner, **When** busca Ingresos retenidos, **Then** no lo ve y no entra.

---

### User Story 3 - El Director de Estrategia ve plan, movimiento y antigüedad (Priority: P3)

El Director de Estrategia abre **Planes**. El héroe es el SLA por plan (¿el premium recibe lo
que paga?). El visual son los movimientos **aprobados** con delta. La antigüedad cuenta solo
cuentas **activas**; las cerradas van aparte.

**Why this priority**: descompone el compromiso y la cartera sin mezclarlos con el héroe de SLA
global ni con el NRR.

**Independent Test**: no hay movimientos pendientes contados. Las cerradas no inflan la
antigüedad. Éxito de Cliente y Finanzas no entran a esta pantalla.

**Acceptance Scenarios**:

1. **Given** un Director de Estrategia autenticado, **When** abre Planes, **Then** el héroe es
   SLA por plan y el visual son movimientos aprobados.
2. **Given** una solicitud de cambio pendiente, **When** se mira el visual, **Then** **no
   cuenta**. MUST NOT pintarse como ingreso ya ganado.
3. **Given** la antigüedad, **When** se muestra, **Then** el recuento de activas va junto a la
   cifra y las cerradas se declaran aparte.
4. **Given** un Gerente de Éxito de Cliente o un Director Financiero, **When** busca Planes,
   **Then** no ve el enlace. El Gerente sí.
5. **Given** un Partner, **When** busca Planes, **Then** no lo ve y no entra.

---

### User Story 4 - El Gerente ve dónde se está perdiendo una cuenta (Priority: P3)

El Gerente abre **Riesgo**. El héroe es el recuento de cuentas con **al menos dos señales**. El
visual muestra las señales (caída de API, alza de tickets, cobro, ausencia de sesiones). Si una
fuente no está, se nombra. Una sola señal no marca la cuenta.

**Why this priority**: es el único informe del catálogo sin departamento dueño (§6). Solo el
Gerente tiene autoridad. El dato es el más anecdótico (4 clientes).

**Independent Test**: n=4 con una sola señal **no** aparece como riesgo. Finanzas, Éxito de
Cliente y Estrategia **no** ven el enlace.

**Acceptance Scenarios**:

1. **Given** un Gerente autenticado, **When** abre Riesgo, **Then** ve Z con recuento de cuentas
   en riesgo, señales y fuentes faltantes.
2. **Given** una cuenta con una sola señal, **When** se mira, **Then** **no** está en el héroe
   como riesgo.
3. **Given** una fuente vacía, **When** se mira, **Then** se lee **qué señal falta**, no un
   semáforo cerrado.
4. **Given** un Director Financiero, de Estrategia o Gerente de Éxito de Cliente, **When** busca
   Riesgo, **Then** no ve el enlace y no entra.

---

### User Story 5 - NPS, reportes impecables y el ciclo de OE1 no se fingen (Priority: P1)

En las cuatro pantallas **no hay** recuadro, pestaña ni enlace de NPS, de reportes sin
corrección, ni de renovación/churn/onboarding de OE1. El tablero no ofrece 0 de satisfacción ni
«ciclo de vida completo» porque faltan encuesta, tabla de entregas o porque esas cifras ya
viven en OE1.

**Why this priority**: el fallo sería silencioso y grave. Misma prioridad que el MVP: si se
pinta de más, US1 miente el nombre «satisfacción».

**Independent Test**: ninguna de las cuatro contiene NPS ni «reportes sin corrección». No hay
ruta de pantalla para E5-01/11 ni recuadros de E5-09/10/13/14.

**Acceptance Scenarios**:

1. **Given** cualquiera de las cuatro pantallas, **When** se recorre, **Then** **no** hay un
   bloque de NPS, de reportes entregados ni de renovación/churn/onboarding.
2. **Given** un período, **When** se muestra Servicio o Riesgo, **Then** no se lee «NPS = 0» ni
   «todas las cuentas en riesgo».
3. **Given** el menú, **When** alguien busca el ciclo de vida de OE1 desde OE5, **Then** no hay
   enlace que reimplemente esas cifras. (Se leen en OE1.)

---

### Edge Cases

- **Período vacío de compromiso.** Vacío explícito en SLA; no 0 %.
- **Catorce tickets / cuatro suscripciones.** Recuento y `parcial` visibles; no se ocultan.
- **Comparación año anterior sin ventana.** Ausente **con motivo**, no error de pantalla.
- **Una zona falla.** El resto sigue; la zona fallida lo dice.
- **Sin autoridad.** Cada cargo solo ve sus enlaces; partner ninguna.
- **Dato sensible.** Ninguna pantalla muestra texto de ticket, notas, medio de cobro, nombre de
   agente ni coordenadas, **tampoco al Gerente**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente cuatro pantallas** —Servicio, Ingresos
  retenidos, Planes, Riesgo— y MUST NOT añadir tarjetas a los compuestos tácticos de Soporte,
  Suscripciones o Cuentas.
- **FR-UI-002**: Las cuatro pantallas MUST mostrar **los nueve informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT inventar NPS/reportes/ciclo de OE1 ni omitir
  uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**. MUST NOT ser una grilla de nueve
  tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar **6–8 bloques** simultáneos.
- **FR-UI-005**: El **período** es obligatorio. La **comparación** (`ninguna`, mes anterior,
  mismo tramo del año anterior) es la única otra acción. Un cambio MUST refrescar todas las
  zonas. MUST NOT inventarse exportación, filtro de cliente ni ficha de ticket.
- **FR-UI-006**: Un período sin datos de **compromiso** MUST verse como vacío, distinguible de
  un 0 % de incumplimiento.
- **FR-UI-007**: El SLA MUST mostrar recuento de cerrados con compromiso y cobertura **en el
  mismo bloque** que el porcentaje.
- **FR-UI-008**: Los tickets sin compromiso MUST declararse **aparte**, no como cumplidos ni
  como incumplidos.
- **FR-UI-009**: El NRR MUST mostrar expansión, contracción y churn **por separado**, además del
  neto.
- **FR-UI-010**: Planes MUST contar solo movimientos **aprobados**. MUST NOT pintar pendientes
  como ingreso.
- **FR-UI-011**: La antigüedad MUST contar **activas** y declarar las cerradas aparte.
- **FR-UI-012**: La carga por agente MUST leerse como **carga de trabajo**, no como desempeño
  individual. MUST NOT mostrar nombre de persona.
- **FR-UI-013**: La reincidencia MUST agrupar por **cliente y servicio**.
- **FR-UI-014**: El riesgo MUST exigir **≥2 señales**. Una señal MUST NOT marcar la cuenta.
- **FR-UI-015**: Si falta una fuente de riesgo, la pantalla MUST nombrar **cuál**.
- **FR-UI-016**: Las cuatro pantallas MUST NOT mostrar NPS, reportes sin corrección, texto de
  ticket, notas, medio de cobro, coordenadas ni recuadros de renovación/churn/onboarding de OE1.
- **FR-UI-017**: Servicio MUST ser visible para `GerenteExitoCliente` y `Gerente`. Ingresos
  retenidos para `DirectorFinanciero` y `Gerente`. Planes para `DirectorEstrategia` y `Gerente`.
  Riesgo **solo** `Gerente`. El resto MUST NOT verlas en el menú ni entrar.
- **FR-UI-018**: Ver MUST NOT habilitar reabrir ticket, cambiar plan, cobrar ni contactar una
  cuenta. Abajo a la derecha hay **lectura**, no una acción de negocio.
- **FR-UI-019**: Si el backend declara cobertura, recuento, alcance o falta, la pantalla MUST
  mostrarlo junto a la cifra.
- **FR-UI-020**: Una comparación sin ventana anterior MUST mostrarse ausente **con motivo**.
- **FR-UI-021**: MUST NOT existir un enlace que fusione estas historias con los compuestos
  tácticos de Soporte, Suscripciones o Cuentas, ni con las pantallas de ciclo de OE1.
- **FR-UI-022**: Servicio MUST declararse distinta del compuesto táctico de Soporte (ventana
  comparada, no recorte operativo).
- **FR-UI-023**: El cascarón Z MUST copiarse de OE1/OE2. MUST NOT extraerse un `shared/` en
  esta pasada.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Gerente de Éxito de Cliente identifica SLA, recuento y si la cobertura es
  parcial en **menos de 5 segundos** en Servicio, sin leer un párrafo.
- **SC-F02**: No existe un estado de pantalla en el que se vea el SLA y no se vea, en el mismo
  bloque, el recuento de cerrados con compromiso.
- **SC-F03**: Un período sin compromiso no se puede leer como 0 % de cumplimiento.
- **SC-F04**: El NRR no se puede leer como un solo neto: expansión, contracción y churn están a
  la vista.
- **SC-F05**: Una cuenta con una sola señal no aparece como riesgo.
- **SC-F06**: Servicio se distingue del compuesto táctico de Soporte: no reutiliza su
  disposición y declara la ventana comparada.
- **SC-F07**: No hay recuadro de NPS ni de reportes sin corrección en ninguna de las cuatro.
- **SC-F08**: No hay recuadro de renovación, churn u onboarding de OE1 en OE5.
- **SC-F09**: El Éxito de Cliente accede **solo** a Servicio. Finanzas **solo** a Ingresos
  retenidos. Estrategia **solo** a Planes. El Gerente a las cuatro. Un partner a ninguna.
- **SC-F10**: En ninguna aparecen texto de ticket, notas, medio de cobro, nombre de agente ni
  coordenadas.
- **SC-F11**: Un período vacío de compromiso no se parece a un período con 0 % de
  incumplimiento.
- **SC-F12**: Cada vista principal queda en **8 o menos** bloques.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las cuatro; no es un listado táctico.
- **Zona Z**: métrica, período/comparación, visual grande, lectura.
- **Período y comparación**: únicos controles.
- **Marca de parcial / recuento / sin compromiso / señal faltante**: impide leer un KPI cerrado
  o un 0 % fingido.
- **Lectura**: el bloque de abajo a la derecha; no es un botón de negocio.

---

## Assumptions

- El backend de los nueve publicados está en servicio. Esta capa no calcula cifras.
- El período es obligatorio; no hay valor por defecto que sustituya desde / hasta /
  granularidad.
- Huecos de NPS y de entregas de reportes: el usuario los resolverá en origen **después**. Esta
  spec no adelanta pantallas.
- El dato de demostración (14 tickets, 4 suscripciones, 4 clientes) es anecdótico; `parcial` es
  la lectura correcta, no un defecto de UI.
- El patrón Z ya está demostrado en táctico, OE2 y OE1; esta capa lo copia (no extrae un
  `shared/` de OE1: se copia el cascarón).
- Los compuestos tácticos de Soporte, Suscripciones y Cuentas no se tocan ni se retiran.
- Las pantallas de ciclo de OE1 no se tocan ni se reimplementan.
- No hay exportación ni programación de envío.
- El mínimo de muestra lo resuelve el backend. Esta capa no ofrece un control extra de umbral.
- E5-01/11 siguen sin fuente; no reaparecen por inferencia ni por la calificación de un cierre
  de emergencia.
- Los frontends de OE1–OE6 de informes estratégicos ya están implementados en sus capas.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Compuestos tácticos de Soporte, Suscripciones, Cuentas | Ya existen |
| NPS, reportes sin corrección | El origen no tiene encuesta ni tabla de entregas |
| Recuadros de renovación / churn / onboarding | Dueño: OE1; aquí 404 |
| Un tablero de nueve iguales | Rompe Z y la Ley de Hick |
| Texto de ticket, notas, medio de cobro, nombre de agente | Exclusión del backend |
| Acciones de negocio (reabrir, cambiar plan, contactar) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Partner, Administrador como autoridad de Riesgo | No están en §4.5 / §6 |
| Cambiar OpenAPI, SQL o permisos del backend | Depends-on |
| Frontend de OE3, OE4 | Otra capa |
| Tablero integral CU-E01 / escenarios / reporte gerencial | Contrato §11 |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período + comparación, menú por rol. SC-F01, SC-F12. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (recuento, parcial, vacío ≠ 0 %, NRR descompuesto, ≥2 señales). No inventa NPS ni reportes impecables. |
| **Security** | Reutiliza quién entra. Partner no ve retención. Sin prosa de ticket. Riesgo solo Gerente. |
| **Safety** | Un SLA de 14 filas pintado como KPI cerrado, un 0 % fingido o un NPS = 0 induciría una decisión de cliente falsa. FR-UI-007, FR-UI-006 y FR-UI-016 lo impiden. No hay cadena de despacho. |
| **Reliability** | Vacío ≠ 0 %; fallo de una zona no tumba las otras; comparación ausente se declara. |
| **Maintainability** | Capa `frontend/` separada; las pantallas copian Z ya usado, sin extraer librería de OE1. |
| **Performance Efficiency** | Heredada del backend. Umbral: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio externo en esta capa. |
| **Flexibility** | El objetivo mide retención, no geografía. Se declara; no se inventa mercado. |

**Traceability**: índice [`../OE5-retencion-ciclo-vida.md`](../OE5-retencion-ciclo-vida.md).
