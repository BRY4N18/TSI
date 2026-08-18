# Feature Specification: OE1 — Posicionamiento y Captación Digital Internacional

**Feature Branch**: `001-estrategico/OE1-posicionamiento-captacion/backend`

**Created**: 2026-08-16

**Status**: Implemented — backend HTTP (2026-08-18). Diez GET publicados; E1-05/07/08 → 404.
Los compuestos tácticos de Suscripciones, Ventas y Cuentas ya existen.

**Input**: User description: "Informes estratégicos del OE1 — los trece informes que miden el ingreso recurrente, la captación digital y el ciclo de vida comercial del cliente, resueltos con consultas sobre el modelo analítico."

---

## Contexto

Cuarto módulo de la capa estratégica en documentarse, y **el primero que se escribe sin sustrato**.
Reutiliza el armazón que OE6 construyó y no lo redefine.

El objetivo dice: *posicionar a TSI en nuevos mercados internacionales comercializando suscripciones
y reportes de siniestralidad, reduciendo los costos de venta mediante captación 100 % digital.*

**Es el objetivo de la perspectiva Financiera**, y por tanto el que un tablero de dirección mira
primero.

---

## ⚠️ La dependencia es doble, y las dos partes faltan

### 1. Los hechos no existen en el modelo analítico

Trece informes, **ninguno construible hoy**. No es un hueco de esta capa: los hechos los diseñan y
los cargan los módulos tácticos de tres departamentos, y **ninguno ha empezado**.

| Lo que OE1 consumirá | Lo diseña | Estado |
|---|---|:--:|
| `hecho_suscripcion`, `hecho_factura`, `hecho_solicitud_cambio_plan`, `dim_plan`, `dim_cliente` | `Suscripciones-Facturacion/informes-compuestos-modelo` | 0 / 71 |
| `hecho_transicion_embudo`, `hecho_asignacion_prospecto`, `dim_prospecto`, `dim_canal` | `Ventas-CRM/informes-compuestos-modelo` | 0 / 64 |
| `hecho_onboarding`, `dim_etapa_onboarding` | `Cuentas-Clientes/informes-compuestos-modelo` | 0 / 67 |

> **Discrepancia del catálogo, detectada al especificar.** El catálogo nombra `hecho_pipeline` como
> fuente de E1-04 y E1-13. **Esa tabla no va a existir con ese nombre**: el diseño táctico de Ventas
> la llama `hecho_transicion_embudo`. Esta spec va con el diseño, que es lo que se construirá.

### 2. El dato de origen es de escala de demostración

Medido en el Pinot operativo el 2026-08-16:

| Fuente | Filas | Qué informe sostiene |
|---|--:|---|
| `Fact_Suscripcion` | **4** | E1-01, E1-02, E1-03, E1-06, E1-12 |
| `Fact_Factura` | **6** | E1-01, E1-02 |
| `Dim_Cliente` | **4** | E1-03, E1-11 |
| `Fact_Onboarding` | **3** | E1-09, E1-10 |
| `Dim_Prospecto` | 10 | E1-04, E1-13 |
| `Fact_Pipeline` | 24 | E1-04, E1-13 |

**Un MRR sobre 4 suscripciones, un churn por cohorte sobre 4 clientes y un embudo sobre 10
prospectos son cifras anecdóticas con forma de indicador.** Y es la perspectiva Financiera del
tablero: nadie mira un MRR y piensa «esto son cuatro filas».

**Consecuencia para el diseño, no solo una advertencia:** todo informe de este módulo **declara su
denominador y su cobertura**, y los que dependan de una muestra insuficiente lo dicen. Es la misma
regla que OE4 aplicó a sus tres fotografías, aquí aplicada a casi todo.

### Por qué la spec se escribe igualmente

Documenta **qué necesita la capa estratégica de cada módulo táctico**, y eso es útil *antes* de que
esos módulos se construyan. Si `hecho_suscripcion` no guarda la periodicidad congelada, E1-01 no
podrá calcular el MRR — y es más barato saberlo ahora que después.

**Lo que no se hace todavía es `/plan`.** Los tres objetivos que sí lo tienen produjeron **once
correcciones al catálogo**, todas salidas de medir contra datos. Sin datos, un plan aquí heredaría el
catálogo sin poder comprobar una sola fuente.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - La dirección ve el ingreso recurrente y de dónde sale (Priority: P1) 🎯 MVP

Cuatro informes: **E1-01**, **E1-02**, **E1-03** y **E1-12**. El MRR, su proyección anual, su
desglose por segmento y la mezcla de la cartera por plan.

**Why this priority**: **E1-01 es el indicador BSC de este objetivo** —crecimiento del MRR— y los
otros tres lo descomponen. Además dependen de un solo departamento, Suscripciones, así que es la
rebanada que menos módulos tácticos necesita.

**Independent Test**: pedir el MRR de un trimestre con comparación interanual y comprobar que
devuelve el valor, las dos ventanas y **el número de suscripciones que lo sostienen**.

| Informe | Ruta | Origen |
|---|---|---|
| **E1-01** MRR mensual y variación | `mrr-mensual` | **BSC** / **CU-E02** |
| **E1-02** ARR y proyección anual | `arr-proyeccion` | **CU-E02** |
| **E1-03** MRR y ARPU por segmento | `mrr-por-segmento` | **CU-E02** / ± |
| **E1-12** Distribución de la cartera por plan | `cartera-por-plan` | ± |

**Acceptance Scenarios**:

1. **Given** un período con suscripciones activas, **When** se pide el MRR, **Then** devuelve el
   ingreso recurrente normalizado a mes **y el recuento de suscripciones** que lo componen.
2. **Given** suscripciones con periodicidad anual, **When** se calcula el MRR, **Then** se
   **normalizan a mensual**. Sumar un precio anual y uno mensual sin normalizar infla el MRR por un
   factor de doce en la suscripción anual.
3. **Given** una suscripción cancelada a mitad de período, **When** se calcula el MRR de ese mes,
   **Then** el informe declara **qué criterio usa** —activa al inicio, al cierre o prorrateada—. Los
   tres son defendibles y dan cifras distintas.
4. **Given** el ARR, **When** se proyecta, **Then** declara **que es una extrapolación del MRR** y no
   ingreso comprometido, con sus escenarios optimista y conservador diferenciados.
5. **Given** la muestra actual —4 suscripciones—, **When** se pide cualquiera de los cuatro,
   **Then** la respuesta declara `cobertura: "parcial"` mientras esté bajo la muestra mínima.
6. **Given** cualquiera de los cuatro, **When** se consulta, **Then** **no devuelve medios de cobro
   ni identificadores de pago**. Es la exclusión más estricta de este dominio: no es una credencial
   que se pueda rotar, es la capacidad de cobrar.

---

### User Story 2 - Entender cómo llega y cuánto tarda un cliente (Priority: P2)

Dos informes: **E1-04** y **E1-13**. Por dónde entra un interesado, cuánto convierte cada paso y
cuánto tarda el ciclo de venta.

**Why this priority**: es la mitad «captación digital» del objetivo. Va después de US1 porque **el
embudo explica de dónde salió el ingreso**, y sin el ingreso medido no hay nada que explicar.

**Independent Test**: pedir el embudo de un trimestre y comprobar que el volumen de cada etapa es
menor o igual al de la anterior, y que las etapas sin ningún paso se distinguen de las no medidas.

| Informe | Ruta | Origen |
|---|---|---|
| **E1-04** Embudo de conversión digital | `embudo-conversion` | **CU-E03** |
| **E1-13** Velocidad del ciclo de venta | `velocidad-ciclo-venta` | **CU-E03** / **CU-T03** |

**Acceptance Scenarios**:

1. **Given** un período, **When** se pide el embudo, **Then** cada etapa declara su volumen y su
   tasa de paso respecto de la anterior, **y el volumen nunca crece** de una etapa a la siguiente.
2. **Given** una etapa por la que no pasó nadie, **When** se presenta, **Then** aparece con **cero y
   su denominador**, no desaparece del embudo. Una etapa ausente se confunde con una etapa perfecta.
3. **Given** el tramo final del embudo —onboarding completado—, **When** se calcula, **Then** el
   informe declara que **cruza dos departamentos**, Ventas y Cuentas, y que su cobertura depende de
   los dos.
4. **Given** la velocidad del ciclo, **When** se desglosa por ejecutivo, **Then** identifica al
   ejecutivo **por su rol y su cartera, nunca por datos personales del prospecto**.

---

### User Story 3 - Medir el ciclo de vida del cliente (Priority: P3)

Cuatro informes: **E1-06**, **E1-09**, **E1-10** y **E1-11**. Renovación, tiempo de incorporación,
dónde se abandona y cuánta cartera se pierde.

**Why this priority**: **OE1 es dueño de los cuatro, y OE5 los referencia** — el catálogo los declara
dos veces con otro nombre (§7.1 del contrato). Van en tercer lugar porque son los que peor dato
tienen: 3 onboardings y 4 clientes.

**Independent Test**: pedir el churn por cohorte y comprobar que la cohorte se forma por período de
alta, y que una cohorte con menos casos que la muestra mínima **se declara** en vez de publicar un
porcentaje.

| Informe | Ruta | Origen | También es |
|---|---|---|---|
| **E1-06** Tasa de renovación | `tasa-renovacion` | **BSC** / **CU-E07** | **E5-09** |
| **E1-09** Tiempo de onboarding | `tiempo-onboarding` | **BSC** / **CU-E03** | **E5-13** |
| **E1-10** Embudo de abandono en onboarding | `abandono-onboarding` | ± | **E5-14** |
| **E1-11** Churn de cliente por cohorte | `churn-por-cohorte` | **BSC** / **CU-E07** | **E5-10** |

**Acceptance Scenarios**:

1. **Given** el onboarding, **When** se mide el abandono, **Then** se mide **por ausencia contra un
   catálogo explícito de etapas esperadas**. ⚠️ El sistema **solo registra lo completado**: un
   embudo mal diseñado mostraría **100 % de finalización** y parecería un proceso perfecto.
2. **Given** una cohorte de alta con menos clientes que la muestra mínima, **When** se pide su churn,
   **Then** se declara **sin muestra suficiente**, no un porcentaje. Con 4 clientes, un abandono es
   un churn del 25 %.
3. **Given** la tasa de renovación, **When** se calcula, **Then** el denominador son las
   suscripciones **vencidas en el período**, no las activas. Usar las activas da una tasa que mejora
   sola cuando nadie vence.
4. **Given** que estos cuatro se comparten con OE5, **When** OE5 los necesite, **Then** los consume
   **desde aquí**; no existe una segunda implementación.

---

### User Story 4 - Medir la expansión internacional (Priority: P4) ⛔ BLOQUEADA

Tres informes: **E1-05**, **E1-07** y **E1-08**. **Ninguno es construible**, y su bloqueo **no lo
resuelve ningún módulo táctico**.

**Why this priority**: aislada al final porque su bloqueo es de otro orden. Los diez anteriores
esperan a que se construya algo ya diseñado; estos tres esperan **datos que el sistema no tiene**.

| Informe | Prerrequisito | Tipo |
|---|---|---|
| **E1-05** CAC por canal *(BSC, −20 % anual)* | Una fuente de **inversión de marketing por canal** | No existe en el sistema |
| **E1-07** Mercados activos *(BSC, +3 al año)* | `idpais` / `idestado` en `Dim_Cliente` | Falta la columna |
| **E1-08** Cartera y MRR por mercado | Ídem | Falta la columna |

**Acceptance Scenarios**:

1. **Given** que no hay fuente de costos, **When** se implemente el módulo, **Then** **no se publica
   endpoint para E1-05**. Un CAC de 0 € se lee como una captación gratis perfecta.
2. **Given** que `Dim_Cliente` no tiene geografía, **When** se implemente, **Then** **no se publican
   E1-07 ni E1-08**. Verificado: la tabla tiene 14 columnas y **ninguna es país ni estado**.
3. **Given** el tablero, **When** pida los indicadores de este objetivo, **Then** **dos del BSC se
   declaran inmedibles**: CAC y mercados activos.

> ⚠️ **El objetivo se llama «internacional» y no puede medir un solo mercado.** `Dim_Cliente` no sabe
> de qué país es un cliente, así que «+3 mercados nuevos al año» no tiene fuente. Es el hueco más
> llamativo del catálogo estratégico: **el nombre del objetivo promete algo que el modelo de datos no
> registra.**

---

### Edge Cases

- **Un período sin ninguna suscripción nueva.** `data: []` con cobertura completa. No es un MRR de
  cero: el MRR lo sostienen las suscripciones vigentes, no las nuevas.
- **Una suscripción con periodicidad anual.** Se normaliza a mensual para el MRR y **no** para el
  ARR. Confundirlas multiplica o divide por doce.
- **Un cliente que se da de baja y vuelve.** Cuenta como churn en su cohorte y como alta nueva. El
  informe declara si la reactivación se resta del churn — son dos criterios y dan cifras distintas.
- **Un prospecto convertido cuyo onboarding nunca terminó.** Es cliente para Ventas y no lo es para
  Cuentas. El embudo declara en qué etapa lo cuenta.
- **Las dos fuentes de nutrición comercial con cero filas.** `Fact_Interaccion_Demo` y
  `Fact_NotificacionVentas` están vacías; no sostienen ningún informe de OE1 —son de OE-nada, las usa
  OT03— pero afectan al tramo «demo» del embudo de E1-04, que debe declararlo.

---

## Requirements *(mandatory)*

### Transversales

- **FR-OE1-001**: Este módulo **reutiliza sin modificar** las piezas transversales de OE6.
- **FR-OE1-002**: Los informes construibles DEBEN resolverse con **una consulta sobre el modelo**.
  Ninguno crea una tabla propia, **y ninguno crea los hechos que consume**: los cargan los tácticos.
- **FR-OE1-003**: Ningún informe DEBE devolver **medios de cobro, identificadores de pago, ni datos
  personales de prospectos o clientes**. Es la exclusión más estricta del dominio comercial.
- **FR-OE1-004**: Ningún informe DEBE agrupar por región ni por país (#38 y la ausencia de `idpais`).
- **FR-OE1-005**: Todo informe DEBE declarar `cobertura: "parcial"` mientras su muestra esté por
  debajo del mínimo. **Con los volúmenes actuales, será el caso en casi todos.**

### Permisos — autoridad repartida, y cuatro informes sin autoridad

- **FR-OE1-006**: Según `acceso-estrategico.md` §4.1: `DirectorFinanciero` en los de resultado
  económico; `DirectorEstrategia` en los de catálogo y segmento; `DirectorMarketing` en los de
  embudo; `DirectorExpansion` en los de mercado; `Gerente` en todos.
- **FR-OE1-007**: ⚠️ **E1-09, E1-10 y E1-11 no tienen autoridad departamental** —Cuentas y Clientes
  no la tiene (§5 de `acceso-estrategico.md`)— y quedan accesibles **solo por `Gerente`**. **No se
  concede al Administrador**: es un rol operativo.

### US1 — el ingreso recurrente

- **FR-OE1-008**: **E1-01** DEBE normalizar toda periodicidad a mensual, y **declarar el criterio**
  con el que cuenta una suscripción cancelada a mitad de período.
- **FR-OE1-009**: **E1-01** DEBE publicar el **recuento de suscripciones** que sostienen la cifra.
- **FR-OE1-010**: **E1-02** DEBE declarar que el ARR es **una extrapolación**, no ingreso
  comprometido, con sus dos escenarios diferenciados.
- **FR-OE1-011**: **E1-03** DEBE segmentar por tipo de cliente —aseguradora, municipio, Smart City,
  proveedor— usando `dim_cliente.tipo`, y agrupar como «Desconocido» los no resueltos.
- **FR-OE1-012**: **E1-12** DEBE publicar la mezcla de cartera por plan **y su evolución**, no solo
  la foto actual.

### US2 — la captación

- **FR-OE1-013**: **E1-04** DEBE entregar volumen y tasa de paso por etapa, **con el volumen nunca
  creciente** entre etapas consecutivas.
- **FR-OE1-014**: **E1-04** DEBE incluir las etapas **sin ningún paso, con cero y su denominador**.
- **FR-OE1-015**: **E1-04** DEBE declarar que su tramo final **cruza a Cuentas y Clientes**, y que su
  cobertura depende de los dos departamentos.
- **FR-OE1-016**: **E1-13** DEBE medir el tiempo por etapa desde `hecho_transicion_embudo`, **sin
  identificar al prospecto**.

### US3 — el ciclo de vida

- **FR-OE1-017**: **E1-10** DEBE medir el abandono **por ausencia contra un catálogo explícito de
  etapas esperadas**, porque el origen solo registra lo completado.
- **FR-OE1-018**: **E1-11** DEBE formar cohortes por período de alta, y **declarar sin muestra
  suficiente** las cohortes bajo el mínimo.
- **FR-OE1-019**: **E1-06** DEBE usar como denominador las suscripciones **vencidas en el período**.
- **FR-OE1-020**: Los cuatro informes de esta historia DEBEN ser **la única implementación**: OE5 los
  consume desde aquí.

### US4 — lo bloqueado

- **FR-OE1-021**: E1-05, E1-07 y E1-08 **NO DEBEN publicarse como endpoint**.
- **FR-OE1-022**: La documentación DEBE declarar que **dos indicadores del BSC quedan sin fuente** —
  CAC y mercados activos— y que **el objetivo no puede medir su dimensión internacional**.

---

## Cumplimiento ISO/IEC 25010:2023

| Característica | Aplica | Cómo |
|---|:--:|---|
| **Idoneidad funcional** | ⚠️ | Los diez construibles están trazados a CU-E02, CU-E03 y CU-E07. **Tres se declaran inmedibles.** Y se corrige una discrepancia del catálogo: `hecho_pipeline` no existirá con ese nombre |
| **Fiabilidad** | ✅ | El módulo mide, no participa en la operación. Versión final obligatoria en los hechos acumulados |
| **Eficiencia de desempeño** | ✅ | Regla 7. E1-11 y E1-13 usan ventanas amplias por cohorte |
| **Capacidad de interacción** | ⚪ | No aplica: frontend aplazado |
| **Seguridad** | ✅ | FR-OE1-003. **El medio de cobro es el dato más delicado del sistema**: no es una credencial que se rote, es la capacidad de cobrar |
| **Compatibilidad** | ✅ | Contrato OpenAPI bajo el envelope común, cuando se planifique |
| **Mantenibilidad** | ✅ | Reutiliza el armazón de OE6 y **es la única implementación** de los cuatro compartidos con OE5 |
| **Flexibilidad** | ⛔ | **Es el objetivo de la expansión internacional y no puede medir un mercado.** `Dim_Cliente` no tiene país |
| **Seguridad física (Safety)** | ⚪ | **No aplica.** Ningún informe de OE1 influye en el despacho ni en la atención de una emergencia. Es el primer módulo del proyecto que puede declararlo sin matices |

**Conflicto identificado:** *Idoneidad* pedía los trece; *Fiabilidad* impide tres. Rige la regla 2 del
Tie-Breaker —no hay Safety— y ganan Mantenibilidad e Idoneidad: **no se publica lo que no se puede
medir**. Lo sacrificado es cobertura aparente del catálogo.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los diez construibles se entregan **sin crear ninguna tabla**, consumiendo los hechos
  que los tácticos carguen.
- **SC-002**: El MRR normaliza toda periodicidad a mensual, verificable con una suscripción anual y
  una mensual del mismo precio anualizado.
- **SC-003**: Todo informe publica el **recuento que sostiene su cifra**, y declara `parcial` bajo la
  muestra mínima.
- **SC-004**: El embudo nunca crece entre etapas, y las etapas vacías aparecen con cero.
- **SC-005**: Los tres bloqueados **no tienen endpoint**, y la documentación nombra sus dos
  prerrequisitos.
- **SC-006**: Ninguna respuesta contiene medios de cobro, identificadores de pago ni datos personales,
  consultada con el rol de máxima autoridad.
- **SC-007**: Los cuatro compartidos con OE5 tienen **una sola implementación**.
- **SC-008**: Ningún `cumple` es booleano: todas las metas de OE1 son `[CALIBRAR]`.

---

## Assumptions

- ✅ **Los tres módulos tácticos ya están implementados** (2026-08-18). Esta suposición dejó de
  bloquear `/plan`.
- **Los hechos tendrán la forma que sus `data-model.md` declaran.** Esta spec se escribió leyéndolos;
  si al construirse cambian, hay que revisarla — y ese es precisamente **el valor de escribirla
  ahora**: declara qué necesita la capa estratégica de cada uno.
- **El armazón de OE6 está construido.** Si no, sus fases 1 y 2 son prerrequisito.
- **La muestra mínima se hereda de OE6.** Con los volúmenes actuales, casi todo caerá por debajo.
- **El frontend queda fuera de alcance.**
