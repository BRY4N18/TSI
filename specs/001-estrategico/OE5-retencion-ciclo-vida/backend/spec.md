# Feature Specification: OE5 — Retención, Satisfacción y Ciclo de Vida del Cliente

**Feature Branch**: `001-estrategico/OE5-retencion-ciclo-vida/backend`

**Created**: 2026-08-16

**Status**: Draft — plan desbloqueado (2026-08-18). Los compuestos tácticos de Soporte,
Suscripciones, Cuentas y Partners ya existen. OE1 ya publicó los cuatro compartidos.
E5-01 y E5-11 siguen sin fuente. Backend HTTP publicado (9 GET, 2+4 → 404).

**Input**: User description: "Informes estratégicos del OE5 — los quince informes que miden si los clientes se quedan, si el servicio comprometido se cumple y dónde se pierde una cuenta, resueltos con consultas sobre el modelo analítico."

---

## Contexto

El objetivo dice: *construir relaciones duraderas con cada cliente, sosteniendo altos niveles de
satisfacción, cumplimiento de SLA y renovación a lo largo de todo su ciclo de vida con TSI.*

**Es el objetivo de la perspectiva Cliente**, y el único cuyo indicador principal —el NPS— no depende
de datos del sistema sino de **preguntarle al cliente**. Eso lo hace estructuralmente distinto: los
demás objetivos miden lo que el sistema hizo; este quiere medir **lo que el cliente opina**, y el
sistema nunca se lo preguntó.

---

## ⚠️ Cuatro dependencias, y cuatro informes que no son suyos

### Es el objetivo con más módulos tácticos por delante

| Lo que OE5 consumirá | Lo diseña | Estado |
|---|---|:--:|
| `hecho_ticket`, `hecho_accion_ticket`, `dim_sla_config`, `dim_servicio`, `dim_estado_soporte` | Soporte al Cliente | **0 / 86** |
| `hecho_suscripcion`, `hecho_factura`, `hecho_solicitud_cambio_plan`, `dim_plan`, `dim_cliente` | Suscripciones y Facturación | **0 / 71** |
| `hecho_onboarding`, `hecho_sesion` | Cuentas y Clientes | **0 / 67** |
| `hecho_llamada_api` | Partners y API *(solo E5-12)* | **0 / 68** |

**292 tareas tácticas por delante.** Y E5-12 necesita las cuatro a la vez.

> **Discrepancia del catálogo.** Nombra `hecho_reclamo`; el diseño táctico de Soporte lo llama
> `hecho_ticket`. Esta spec va con el diseño.

### Cuatro informes son de OE1

**E5-09, E5-10, E5-13 y E5-14** son los mismos que **E1-06, E1-11, E1-09 y E1-10**. El catálogo los
declara dos veces porque OE1 los pide como resultado de la captación y OE5 como resultado de la
retención — **ambas lecturas son legítimas y la consulta es una sola** (§7.1 del contrato).

**OE1 es el dueño. Este módulo los referencia y no los reimplementa.**

Quedan **nueve propios construibles** y **dos bloqueados**.

### El dato es de escala de demostración

Medido en el Pinot operativo el 2026-08-16:

| Fuente | Filas | Qué informe sostiene |
|---|--:|---|
| `Fact_Reclamo` | **14** | E5-04, E5-05, E5-06, E5-07, E5-08 |
| `Fact_Historial_Ticket` | 34 | E5-06 |
| `Dim_SLAConfig` | 6 | E5-04, E5-07 |
| `Fact_Suscripcion` | **4** | E5-02, E5-03, E5-15 |
| `Fact_Factura` | **6** | E5-02 |
| `Dim_Cliente` | **4** | E5-15, E5-12 |
| `Fact_Session` | 747 | E5-12 |

**Un cumplimiento de SLA sobre 14 tickets se mueve 7 puntos por cada ticket.** La meta del BSC es
≥95 % mensual: un solo incumplimiento la rompe, y no porque el servicio sea malo.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber si el compromiso de servicio se cumple (Priority: P1) 🎯 MVP

Tres informes: **E5-04**, **E5-05** y **E5-07**. Cuánto se cumple el SLA, cómo evoluciona y si los
planes premium reciben lo que pagan.

**Why this priority**: **E5-04 es el indicador BSC del objetivo que sí tiene fuente** —el otro, el
NPS, no la tiene—. Y depende de un solo departamento, Soporte, así que es la rebanada que menos
módulos tácticos necesita.

**Independent Test**: pedir el cumplimiento de SLA de un trimestre y comprobar que el denominador son
los tickets **cerrados con compromiso**, y que los tickets sin compromiso se declaran aparte.

| Informe | Ruta | Meta | Origen |
|---|---|---|---|
| **E5-04** Cumplimiento consolidado de SLA | `cumplimiento-sla` | ≥95 % `[CALIBRAR]` | **BSC** / **CU-E07** |
| **E5-05** Evolución del incumplimiento | `evolucion-incumplimiento` | — | **CU-E07** / ± |
| **E5-07** SLA desglosado por plan | `sla-por-plan` | — | ± |

**Acceptance Scenarios**:

1. **Given** un período con tickets cerrados, **When** se pide el cumplimiento, **Then** el
   denominador son los **cerrados con compromiso de tiempo**, y los tickets **sin compromiso** se
   declaran aparte.
2. **Given** que un cliente sin suscripción activa genera tickets **sin plazo** —hoy ocurre y está
   documentado—, **When** se calcula el cumplimiento, **Then** esos tickets **no entran en el
   denominador** ni como cumplidos ni como incumplidos. Incluirlos como cumplidos inflaría la cifra;
   como incumplidos, la hundiría — y ninguna de las dos sería cierta.
3. **Given** la muestra actual de 14 tickets, **When** se pide cualquiera de los tres, **Then** se
   declara `cobertura: "parcial"`. Con 14 tickets, **un solo caso mueve la cifra 7 puntos**.
4. **Given** el desglose por plan, **When** se presenta, **Then** verifica que los planes premium
   reciben el servicio comprometido — es la comprobación de que el precio se corresponde con algo.
5. **Given** cualquiera de los tres, **When** se consulta, **Then** **no devuelve el texto de los
   mensajes ni las notas internas** del ticket. Un informe estratégico necesita saber qué pasó y
   cuándo, no la prosa — y al no exponerla, el problema de filtrar notas internas **no llega a
   plantearse**.

---

### User Story 2 - Ver si la cartera crece o se erosiona (Priority: P2)

Dos informes propios: **E5-02** y **E5-03**. La retención neta de ingresos y el saldo de los
movimientos de plan.

**Why this priority**: **E5-02 es indicador del BSC** —NRR ≥105 % anual— y es la medida que distingue
una cartera que crece de una que solo no se encoge. Va después de US1 porque **el SLA explica en
buena parte por qué un cliente se queda**.

**Independent Test**: pedir el NRR de un año y comprobar que descompone expansión, contracción y
churn por separado, no solo el neto.

| Informe | Ruta | Meta | Origen |
|---|---|---|---|
| **E5-02** Retención neta de ingresos (NRR) | `retencion-neta-ingresos` | ≥105 % `[CALIBRAR]` | **BSC** / **CU-E07** |
| **E5-03** Movimientos de plan con delta | `movimientos-de-plan` | — | **BSC** / **CU-E07** |

**Referencia:** **E5-09** (tasa de renovación) se consume desde **E1-06**.

**Acceptance Scenarios**:

1. **Given** un año con altas, bajas y cambios de plan, **When** se pide el NRR, **Then** publica
   **expansión, contracción y churn por separado**, además del neto. Un NRR del 100 % puede ser una
   cartera estable o una que ganó tanto como perdió, y son situaciones opuestas.
2. **Given** un cambio de plan aprobado, **When** se calcula el delta de ingreso, **Then** usa el
   precio **congelado en la suscripción**, no el vigente del catálogo. `Fact_Suscripcion` congela el
   precio al alta precisamente para esto; usar `Dim_Plan.precio` reescribiría la historia cada vez que
   se cambia una tarifa.
3. **Given** una solicitud de cambio de plan **pendiente**, **When** se calcula el movimiento,
   **Then** **no cuenta** hasta que se aprueba. Contar lo solicitado como ingreso es contar dinero que
   no entró.
4. **Given** la muestra actual —4 suscripciones—, **When** se pide el NRR, **Then** se declara
   `parcial`.

---

### User Story 3 - Ver dónde se está perdiendo una cuenta (Priority: P3)

Cuatro informes: **E5-06**, **E5-08**, **E5-12** y **E5-15**. Quién atiende y cómo, qué problemas se
repiten, qué cuentas dan señales de irse y cuánto duran las relaciones.

**Why this priority**: es la parte accionable —permite intervenir antes de perder al cliente— pero va
tercera porque **E5-12 necesita los cuatro módulos tácticos a la vez**, y porque sin US1 y US2 no hay
línea base contra la que leer una señal.

**Independent Test**: pedir las cuentas en riesgo y comprobar que la señal se compone de las cuatro
fuentes, y que una cuenta con solo una señal activa **no** se marca en riesgo.

| Informe | Ruta | Origen |
|---|---|---|
| **E5-06** Rendimiento por agente de soporte | `rendimiento-por-agente` | ± |
| **E5-08** Reincidencia de soporte | `reincidencia-soporte` | ± |
| **E5-12** Cuentas en riesgo de churn | `cuentas-en-riesgo` | **CU-E07** / ± |
| **E5-15** Antigüedad media de cuenta | `antiguedad-de-cuenta` | ± |

**Referencias:** **E5-10**, **E5-13** y **E5-14** se consumen desde **E1-11**, **E1-09** y **E1-10**.

**Acceptance Scenarios**:

1. **Given** las cuatro señales —caída de consumo API, alza de tickets, fallos de cobro y ausencia de
   sesiones—, **When** se calcula el riesgo, **Then** una cuenta con **una sola señal no se marca**.
   El informe existe porque ninguna señal por separado predice nada; marcar con una sola lo convierte
   en cuatro alarmas ruidosas.
2. **Given** que una de las cuatro fuentes no esté cargada, **When** se pide E5-12, **Then** declara
   `cobertura: "parcial"` nombrando **qué señal falta**. Un riesgo calculado con tres de cuatro
   señales no es el mismo indicador, y presentarlo como tal daría falsos negativos.
3. **Given** el rendimiento por agente, **When** se presenta, **Then** identifica al agente por su
   **rol y su cola**, y el informe declara que **mide carga de trabajo, no desempeño individual**. Un
   agente con tiempos altos puede tener los tickets más difíciles.
4. **Given** la reincidencia, **When** se calcula, **Then** agrupa por **cliente y servicio**: un
   cliente con tres tickets de tres servicios distintos no es reincidencia, es uso.
5. **Given** la antigüedad media, **When** se calcula, **Then** cuenta **solo relaciones activas**, y
   declara aparte las cerradas. Promediar las dos mezcla fidelidad con rotación.

---

### User Story 4 - Medir la satisfacción declarada (Priority: P4) ⛔ BLOQUEADA

Dos informes: **E5-01** y **E5-11**. **Ninguno es construible**, y el primero es **el indicador
principal del objetivo**.

**Why this priority**: aislada porque su bloqueo no lo resuelve ningún módulo táctico. El NPS no se
calcula: **se pregunta**, y el sistema nunca preguntó.

| Informe | Prerrequisito |
|---|---|
| **E5-01** NPS / satisfacción *(BSC ≥50)* | Una tabla de **encuestas de satisfacción** post-ticket y post-QBR |
| **E5-11** Reportes sin corrección posterior *(BSC ≥98 %)* | Una tabla de **programación y entrega de informes** (OT14) |

**Acceptance Scenarios**:

1. **Given** que no existe tabla de encuestas, **When** se implemente el módulo, **Then** **no se
   publica endpoint para E5-01**.
2. **Given** que `Fact_CierreAccidente.calificacion` existe, **When** alguien proponga usarla como
   NPS, **Then** **se rechaza**: es la valoración de **un caso de emergencia individual**, no la
   satisfacción del cliente con TSI. Además tiene **0 filas**. Usarla sería medir otra cosa y llamarla
   NPS.
3. **Given** el tablero, **When** pida los indicadores de OE5, **Then** **dos del BSC se declaran
   inmedibles**, y uno de ellos es **el que da nombre a la perspectiva Cliente**.

> ⚠️ **El objetivo de la satisfacción del cliente no puede medir la satisfacción del cliente.** Es el
> hueco más importante del catálogo estratégico, y el más barato de cerrar: una encuesta de una
> pregunta al cerrar un ticket.

---

### Edge Cases

- **Un ticket sin compromiso de tiempo.** No entra en el denominador del SLA. Ocurre hoy con clientes
  sin suscripción activa, y ya está documentado como decisión pendiente.
- **Un período sin tickets cerrados.** `data: []` con cobertura completa. **No es un cumplimiento del
  0 %**: es que no hubo nada que cumplir.
- **Un cliente con una sola señal de riesgo.** No se marca. La combinación es el informe.
- **Un cambio de plan pendiente de aprobación.** No cuenta como movimiento.
- **Una cuenta reactivada.** Su antigüedad declara si se cuenta continua o desde la reactivación; son
  dos criterios y dan cifras distintas.
- **Los cuatro informes que son de OE1.** Si alguien los pide en las rutas de OE5, **devuelven `404`
  con el camino de OE1**, no una segunda implementación.

---

## Requirements *(mandatory)*

### Transversales

- **FR-OE5-001**: Reutiliza sin modificar las piezas transversales de OE6.
- **FR-OE5-002**: Los nueve propios DEBEN resolverse con **una consulta sobre el modelo**, y ninguno
  crea los hechos que consume.
- **FR-OE5-003**: Ningún informe DEBE devolver **el texto de los mensajes de un ticket, sus notas
  internas, ni datos personales del reportador**. Al no exponer la prosa, el problema de filtrar notas
  internas no llega a plantearse.
- **FR-OE5-004**: Ningún informe DEBE devolver medios de cobro.
- **FR-OE5-005**: **E5-09, E5-10, E5-13 y E5-14 NO DEBEN implementarse aquí.** Se consumen desde OE1,
  y sus rutas en OE5 **no existen**.
- **FR-OE5-006**: Todo informe DEBE declarar `cobertura: "parcial"` bajo la muestra mínima. **Con 14
  tickets y 4 suscripciones, será el caso en casi todos.**

### Permisos

- **FR-OE5-007**: `GerenteExitoCliente` en los de soporte —E5-04 a E5-08—; `DirectorFinanciero` en
  E5-02; `DirectorEstrategia` en E5-03 y E5-07; `Gerente` en todos (`acceso-estrategico.md` §4.5).
- **FR-OE5-008**: ⚠️ **E5-12 es accesible solo por `Gerente`.** Cruza cuatro departamentos y **ninguno
  es su dueño**; concederlo a las cuatro autoridades daría a cada una las señales de los otros tres
  (§6 de `acceso-estrategico.md`).
- **FR-OE5-009**: **E5-15** queda accesible por `DirectorEstrategia` en su parte de plan; su parte de
  cuenta **no tiene autoridad** —Cuentas y Clientes no la tiene— y solo la ve el `Gerente`.

### US1 — el compromiso de servicio

- **FR-OE5-010**: **E5-04** DEBE usar como denominador los tickets **cerrados con compromiso**, y
  declarar aparte los **sin compromiso**.
- **FR-OE5-011**: **E5-05** DEBE permitir ventanas amplias para correlacionar el incumplimiento con
  eventos —una región nueva, un lanzamiento—.
- **FR-OE5-012**: **E5-07** DEBE cruzar el cumplimiento con el **plan contratado**, para verificar que
  los planes premium reciben lo comprometido.

### US2 — la cartera

- **FR-OE5-013**: **E5-02** DEBE publicar **expansión, contracción y churn por separado**, además del
  neto.
- **FR-OE5-014**: **E5-03** DEBE usar el precio **congelado en la suscripción**, no el vigente del
  catálogo.
- **FR-OE5-015**: **E5-03** DEBE contar solo los movimientos **aprobados**.

### US3 — las señales

- **FR-OE5-016**: **E5-12** DEBE exigir **más de una señal** para marcar una cuenta en riesgo.
- **FR-OE5-017**: **E5-12** DEBE declarar `parcial` nombrando **qué señal falta** si alguna de sus
  cuatro fuentes no está cargada.
- **FR-OE5-018**: **E5-06** DEBE declarar que mide **carga de trabajo, no desempeño individual**.
- **FR-OE5-019**: **E5-08** DEBE agrupar la reincidencia por **cliente y servicio**.
- **FR-OE5-020**: **E5-15** DEBE contar solo relaciones **activas**, declarando las cerradas aparte.

### US4 — lo bloqueado

- **FR-OE5-021**: **E5-01 y E5-11 NO DEBEN publicarse.**
- **FR-OE5-022**: ⚠️ **`Fact_CierreAccidente.calificacion` NO DEBE usarse como NPS.** Es la valoración
  de un caso de emergencia individual, tiene **0 filas**, y usarla sería medir otra cosa con el nombre
  del indicador comprometido.
- **FR-OE5-023**: La documentación DEBE declarar que **el indicador principal del objetivo no tiene
  fuente**, y que su prerrequisito —una encuesta de una pregunta al cerrar un ticket— es el más barato
  de todo el catálogo estratégico.

---

## Cumplimiento ISO/IEC 25010:2023

| Característica | Aplica | Cómo |
|---|:--:|---|
| **Idoneidad funcional** | ⚠️ | Los nueve propios trazados a CU-E07. **Dos se declaran inmedibles, y uno es el indicador principal.** Se corrige el catálogo: `hecho_reclamo` se llamará `hecho_ticket` |
| **Fiabilidad** | ✅ | El módulo mide, no participa en la operación |
| **Eficiencia de desempeño** | ✅ | Regla 7. E5-05 y E5-15 usan ventanas amplias |
| **Capacidad de interacción** | ⚪ | No aplica: frontend aplazado |
| **Seguridad** | ✅ | FR-OE5-003 y FR-OE5-004. La exclusión del texto de los tickets **elimina el problema en vez de resolverlo con un filtro** que alguien podría olvidar al añadir un campo |
| **Compatibilidad** | ✅ | Contrato OpenAPI bajo el envelope común, cuando se planifique |
| **Mantenibilidad** | ✅ | **No reimplementa los cuatro informes de OE1.** Es la aplicación más clara de la regla §7 del contrato: el catálogo pide quince y se construyen once |
| **Flexibilidad** | ⚠️ | E5-04 no puede desglosarse por región (#38 y la ausencia de geografía comercial) |
| **Seguridad física (Safety)** | ⚪ | **No aplica.** Ningún informe influye en el despacho |

**Conflicto identificado:** *Idoneidad* pedía los quince; *Fiabilidad* impide dos y *Mantenibilidad*
impide reimplementar cuatro. Regla 2 del Tie-Breaker: **se construyen nueve**. Lo sacrificado es
cobertura aparente; lo ganado es que no hay dos definiciones de la tasa de renovación.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los nueve propios se entregan **sin crear ninguna tabla**.
- **SC-002**: El cumplimiento de SLA excluye del denominador los tickets sin compromiso, y los declara.
- **SC-003**: El NRR descompone expansión, contracción y churn, no solo el neto.
- **SC-004**: Los movimientos de plan usan el precio **congelado**, verificable cambiando la tarifa
  del catálogo y comprobando que el histórico **no se mueve**.
- **SC-005**: Una cuenta con una sola señal **no** aparece en riesgo.
- **SC-006**: E5-12 declara qué señal falta cuando una fuente no está cargada.
- **SC-007**: **Las cuatro rutas de los informes de OE1 no existen en OE5** y devuelven `404` con el
  camino correcto.
- **SC-008**: E5-01 y E5-11 **no tienen endpoint**, y ninguna respuesta usa la calificación de cierre
  de accidente como NPS.
- **SC-009**: Ninguna respuesta contiene texto de tickets, notas internas ni medios de cobro.
- **SC-010**: Ningún `cumple` es booleano: todas las metas de OE5 son `[CALIBRAR]`.

---

## Assumptions

- ✅ **Los cuatro módulos tácticos ya cargaron los hechos** (2026-08-18).
- ✅ **OE1 ya publicó E1-06/09/10/11.** Este módulo no los reimplementa.
- **Los hechos tienen la forma de `dags/lib/ddl.py`.** En particular, `hecho_ticket` con
  `tiene_compromiso` y `desenlace_sla`; si no los conservara, E5-04 deja de ser calculable.
- **El armazón de OE6 está construido.**
- **La muestra mínima se hereda de OE6.** Con 14 tickets y 4 suscripciones, casi todo caerá por debajo.
- **El frontend queda fuera de alcance.**
