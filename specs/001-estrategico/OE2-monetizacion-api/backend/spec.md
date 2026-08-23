# Feature Specification: OE2 — Monetización del Ecosistema de APIs e Integraciones

**Feature Branch**: `001-estrategico/OE2-monetizacion-api/backend`

**Created**: 2026-08-16

**Status**: Implemented — backend (2026-08-18). Diez GET publicados; E2-06 → 404.

**Input**: User description: "Informes estratégicos del OE2 — los once informes que miden si el acceso programático a los datos de TSI se está vendiendo, usando y facturando, resueltos con consultas sobre el modelo analítico."

---

## Contexto

El objetivo dice: *generar nuevas líneas de ingresos recurrentes vendiendo el acceso en tiempo real a
la base de accidentes y despachos vía APIs, logrando que aseguradoras y plataformas de Smart Cities
integren nuestra información en sus sistemas.*

**Es el objetivo que materializa el modelo de negocio del Principio VI de la constitución** —
compatibilidad e interoperabilidad API-first—. Y por eso tiene una particularidad: **sus informes
miden un producto cuyo contrato la constitución protege**. Un partner que ve caer su latencia p95 no
está mirando un indicador interno: está evaluando si sigue integrado.

---

## ⚠️ La dependencia, y lo que la hace distinta de OE1 y OE5

### Un solo departamento

| Lo que OE2 consumirá | Lo diseña | Estado |
|---|---|:--:|
| `hecho_llamada_api`, `hecho_cambio_acceso`, `dim_partner`, `dim_credencial_api`, `dim_version_contrato` | `Partners-API/informes-compuestos-modelo` | ✅ compuestos tácticos (2026-08-18) |

**Es la dependencia más limpia de los tres objetivos que esperaban táctico.** El compuesto de
Partners ya está; OE2 se planifica entero salvo E2-06.

> **Discrepancia del catálogo.** El catálogo nombra `hecho_log_llamada_api` y `hecho_api_integracion`.
> El diseño táctico crea **una sola** tabla: `hecho_llamada_api`, con el detalle evento a evento. Y es
> deliberado — el propio catálogo advierte que *«en el modelo analítico manda el detalle»*, porque es
> el único que permite calcular p95 y taxonomizar errores. **Esta spec va con el diseño.**

### El dato de consumo es de 18 llamadas

Medido en el Pinot operativo el 2026-08-16:

| Fuente | Filas | Qué informe sostiene |
|---|--:|---|
| `Fact_LogLlamadaAPI` | **18** | E2-03, E2-04, E2-05, E2-07, E2-09, E2-10 |
| `Fact_APIIntegracion` | 40 | *(agregado; no se usa — ver abajo)* |
| `Dim_Partner` | 4 | Todos |
| `Dim_CredencialAPI` | 6 | E2-04, E2-11 |
| `Fact_HistorialAccesoPartner` | 15 | E2-11 |

**Un p95 de latencia por endpoint sobre 18 llamadas no es un percentil: es casi el máximo.** Y
repartidas entre endpoints, cada uno tendrá dos o tres.

⚠️ **Las dos fuentes de consumo siguen sin cuadrar**, como el táctico documentó: el agregado declara
40 y el detalle tiene 18. **El modelo se queda con el detalle**, y esta spec prohíbe usar el agregado
para nada que pueda calcularse desde el detalle — porque sobre esas cifras se factura.

---

## Lo que el catálogo dio por bloqueado y no lo está

El catálogo marca E2-01, E2-02 **y E2-08** como dependientes de que exista un precio para el plan de
API. Se comprobó, y **el reparto es distinto**:

| | Lo que hay |
|---|---|
| `Dim_Partner.planapi` | Texto libre, **sin precio ni periodicidad** → E2-01 y E2-02 ⚠️ siguen parciales |
| `Dim_Plan.precio_excedente_llamada` | **Existe** → **E2-08 es construible** |

**E2-08 —el excedente facturable— sale de la lista de parciales.** Es el informe con consecuencia
económica más directa del objetivo: es lo que se cobra de más a un partner que supera su cupo.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Tecnológico ve si la API se usa y cómo responde (Priority: P1) 🎯 MVP

Cuatro informes: **E2-03**, **E2-04**, **E2-05** y **E2-07**. Cuántos partners integran de verdad,
cuánto consumen, cómo responde la API y en qué falla.

**Why this priority**: **E2-03 y E2-05 son indicadores del BSC**, y los cuatro salen de un solo hecho
—`hecho_llamada_api`— sin cruzar con nada. Es la rebanada de menor riesgo y la que da la señal más
temprana: **un ecosistema de API sin llamadas no es un ecosistema**.

**Independent Test**: pedir la intensidad de consumo de un trimestre y comprobar que el total de
llamadas por partner cuadra con el total del período, y que el p95 se declara ausente bajo la muestra
mínima.

| Informe | Ruta | Meta | Origen |
|---|---|---|---|
| **E2-03** Clientes con integración activa | `integraciones-activas` | ≥70 % `[CALIBRAR]` | **BSC** / **CU-E04** |
| **E2-04** Intensidad de consumo por partner | `consumo-por-partner` | — | **CU-E04** / **CU-T12** |
| **E2-05** Latencia p95 por endpoint | `latencia-por-endpoint` | `[NORMATIVO]` | **BSC** / **CU-E05** |
| **E2-07** Taxonomía de errores 4xx / 5xx | `taxonomia-errores` | — | **CU-E04** / **CU-T12** |

**Acceptance Scenarios**:

1. **Given** un mes con llamadas, **When** se piden las integraciones activas, **Then** cuenta los
   partners con **al menos una llamada en el mes**, sobre el total de partners **con acceso
   concedido** — no sobre el total de partners existentes. Un partner suspendido no cuenta en el
   denominador de adopción.
2. **Given** un endpoint con menos llamadas que la muestra mínima, **When** se pide su p95, **Then**
   sale **ausente**. Con 18 llamadas repartidas entre endpoints, será el caso de casi todos.
3. **Given** la intensidad de consumo, **When** se calcula, **Then** usa **el detalle evento a
   evento**, nunca el agregado. Las dos fuentes no cuadran —40 frente a 18— y **sobre estas cifras se
   factura**.
4. **Given** la taxonomía de errores, **When** se presenta, **Then** separa **4xx de 5xx**: un 4xx es
   un partner que integra mal y un 5xx es un fallo nuestro. Agregarlos en «tasa de error» mezcla un
   problema de documentación con uno de servicio.
5. **Given** cualquiera de los cuatro, **When** se consulta, **Then** **no devuelve secretos de
   autenticación ni el contacto técnico del partner**. `dim_credencial_api` guarda un hash que
   autentica a quien lo tenga.

---

### User Story 2 - Ver cuánto dinero produce la API (Priority: P2)

Tres informes: **E2-01**, **E2-02** y **E2-08**. Cuánto pesa la API en los ingresos, cómo se reparte
por línea de negocio y cuánto hay que facturar de excedente.

**Why this priority**: es la razón de ser del objetivo —«monetización»— y **E2-01 es indicador del
BSC**. Va después de US1 porque **el consumo se mide antes de facturarlo**: sin saber cuántas llamadas
hubo, el excedente no se puede calcular.

**Independent Test**: pedir el excedente facturable de un mes y comprobar que cuadra llamadas sobre
el cupo por el precio unitario, y que los dos informes de ingresos declaran su parte no medible.

| Informe | Ruta | Estado |
|---|---|:--:|
| **E2-08** Excedente facturable por partner | `excedente-facturable` | ✅ **construible** |
| **E2-01** Participación de ingresos por API | `participacion-ingresos-api` | ⚠️ parcial |
| **E2-02** MRR por línea: plataforma vs API | `mrr-por-linea` | ⚠️ parcial |

**Acceptance Scenarios**:

1. **Given** un partner que superó su cupo mensual, **When** se calcula el excedente, **Then**
   multiplica las llamadas sobre `limitellamadasmes` por `precio_excedente_llamada`, y **publica las
   tres cifras**: llamadas, cupo y precio. Un importe sin sus componentes no se puede disputar.
2. **Given** un partner **no tarificable**, **When** se calcula el excedente, **Then** se declara
   aparte, **no se omite**. El silencio ante un consumo no facturable es justo lo que la regla
   RN-APM-014 del módulo operativo prohíbe.
3. **Given** que `Dim_Partner.planapi` no tiene precio, **When** se piden E2-01 o E2-02, **Then**
   entregan **solo la parte de volumen** y declaran `cobertura: "parcial"` con `falta: ["precio del
   plan de API"]`.
4. **Given** el excedente calculado, **When** se compara con lo facturado, **Then** el informe **no
   afirma que se haya cobrado**: calcula lo facturable. Confundir ambos daría un ingreso que no entró.

---

### User Story 3 - Ver la salud del ecosistema (Priority: P3)

Tres informes: **E2-09**, **E2-10** y **E2-11**. Qué versiones del contrato se usan, cómo se comparan
los partners entre sí y si el ecosistema crece.

**Why this priority**: es la mirada de medio plazo. **E2-09 es indicador del BSC** —contratos
versionados sin cambios que rompan— y el que sostiene el Principio VI: no se puede retirar una versión
sin saber quién la usa.

**Independent Test**: pedir la adopción de versiones y comprobar que las llamadas por versión suman el
total, y que un partner rezagado en una versión antigua se identifica.

| Informe | Ruta | Origen |
|---|---|---|
| **E2-09** Adopción de versiones del contrato | `adopcion-versiones` | **BSC** |
| **E2-10** Comparativa entre partners | `comparativa-partners` | ± |
| **E2-11** Crecimiento del ecosistema | `crecimiento-ecosistema` | **CU-E04** |

**Acceptance Scenarios**:

1. **Given** varias versiones publicadas, **When** se pide la adopción, **Then** el reparto por
   versión **suma el total de llamadas**, y los partners rezagados se identifican por nombre.
2. **Given** que la versión **no está en el log** pero es derivable del endpoint, **When** se calcula,
   **Then** el informe declara que **la deriva** y no la lee. ⚠️ Y que `version` **no es única**: dos
   servicios distintos comparten `'v1'`.
3. **Given** la comparativa entre partners, **When** se presenta, **Then** identifica al partner por
   su organización, **nunca por su contacto técnico**.
4. **Given** el crecimiento del ecosistema, **When** se mide, **Then** cuenta **primeras llamadas
   exitosas**, no altas de credencial. Una credencial emitida y nunca usada no es un partner
   integrado — es exactamente lo que E2-03 existe para distinguir.

---

### User Story 4 - Medir la disponibilidad de la API (Priority: P4) ⛔ BLOQUEADA

Un informe: **E2-06**. Uptime de la API pública, meta ≥99,9 %.

**Why this priority**: aislado porque **su fuente no es este sistema**. El log de llamadas dice qué
pasó cuando alguien llamó; no dice nada de los minutos en que **nadie pudo llamar**, que es
precisamente lo que mide la disponibilidad.

**Acceptance Scenarios**:

1. **Given** que la disponibilidad exige un latido de monitoreo externo, **When** se implemente el
   módulo, **Then** **no se publica endpoint para E2-06**. Derivarlo del log daría **100 % de uptime
   siempre**: si el servicio estuvo caído no hay filas, y la ausencia de errores se leería como
   ausencia de problemas.
2. **Given** el tablero, **When** pida la disponibilidad, **Then** se declara inmedible con su
   prerrequisito: **integrar el monitoreo de infraestructura**, el mismo que bloquea E3-01.

---

### Edge Cases

- **Un partner con credencial y cero llamadas.** Cuenta en el denominador de E2-03 y no en el
  numerador. Es el caso que el indicador existe para detectar.
- **Un mes sin ninguna llamada.** `data: []` con cobertura completa. **No es un uptime de cero ni una
  latencia de cero**: es que nadie llamó.
- **Un endpoint con dos llamadas.** Su p95 sale ausente. Con 18 llamadas totales, será lo normal.
- **Un partner suspendido a mitad de mes.** Sus llamadas del período cuentan en el consumo; el partner
  no cuenta en el denominador de adopción del mes siguiente. El informe declara el criterio.
- **Dos servicios con la misma etiqueta de versión.** `version` no es única: la adopción se agrupa por
  **servicio y versión**, no solo por versión.
- **Un excedente sobre un partner no tarificable.** Se declara aparte, nunca se omite.

---

## Requirements *(mandatory)*

### Transversales

- **FR-OE2-001**: Reutiliza sin modificar las piezas transversales de OE6.
- **FR-OE2-002**: Los diez construibles DEBEN resolverse con **una consulta sobre el modelo**, y
  ninguno crea los hechos que consume.
- **FR-OE2-003**: Ningún informe DEBE devolver **secretos de autenticación, hashes de credencial ni
  el contacto técnico del partner**. `client_secret_hash` autentica a quien lo tenga.
- **FR-OE2-004**: Los repositorios DEBEN enumerar sus columnas en **lista blanca**. Es la regla que
  `Dim_CredencialAPI` originó en la capa táctica: una lista negra falla el día que alguien añade una
  columna sensible, y falla **abierta y en silencio**.
- **FR-OE2-005**: Ningún informe DEBE usar el **agregado de consumo** para algo calculable desde el
  detalle. Las dos fuentes no cuadran, y **sobre estas cifras se factura**.

### Permisos

- **FR-OE2-006**: `DirectorTecnologico` y `Gerente` en los diez. `DirectorFinanciero` **además** en
  E2-01, E2-02 y E2-08, que son los de dinero (`acceso-estrategico.md` §4.2).
- **FR-OE2-007**: ⚠️ **Ningún partner accede a estos informes.** El portal del partner tiene su propio
  panel de consumo, acotado a él. Un informe estratégico agrega **todo el ecosistema**, y dárselo a un
  partner le mostraría el consumo de sus competidores.

### US1 — el consumo y su calidad

- **FR-OE2-008**: **E2-03** DEBE usar como denominador los partners **con acceso concedido**, no el
  total existente.
- **FR-OE2-009**: **E2-05** DEBE devolver el p95 **ausente** bajo la muestra mínima, por endpoint.
- **FR-OE2-010**: **E2-07** DEBE separar **4xx de 5xx**, con su denominador cada uno.
- **FR-OE2-011**: **E2-04** DEBE publicar el consumo frente al **cupo contratado**, para que la cifra
  se lea contra su límite.

### US2 — el dinero

- **FR-OE2-012**: **E2-08** DEBE publicar **llamadas, cupo y precio unitario** junto al importe. Un
  importe sin sus componentes no se puede disputar.
- **FR-OE2-013**: **E2-08** DEBE declarar aparte los partners **no tarificables**, nunca omitirlos.
- **FR-OE2-014**: **E2-08** DEBE presentar lo **facturable**, y declarar explícitamente que no
  afirma que se haya cobrado.
- **FR-OE2-015**: **E2-01** y **E2-02** DEBEN entregar la parte de volumen con `cobertura: "parcial"`
  y `falta: ["precio del plan de API"]`.

### US3 — el ecosistema

- **FR-OE2-016**: **E2-09** DEBE agrupar por **servicio y versión**, porque `version` no es única.
- **FR-OE2-017**: **E2-09** DEBE declarar que la versión **se deriva del endpoint**, no se lee del log.
- **FR-OE2-018**: **E2-11** DEBE contar **primeras llamadas exitosas**, no altas de credencial.

### US4 — lo bloqueado

- **FR-OE2-019**: **E2-06 NO DEBE publicarse.** Derivar el uptime del log daría **100 % siempre**.
- **FR-OE2-020**: La documentación DEBE declarar que la disponibilidad queda sin fuente, y que su
  prerrequisito **es el mismo que bloquea E3-01**.

---

## Cumplimiento ISO/IEC 25010:2023

| Característica | Aplica | Cómo |
|---|:--:|---|
| **Idoneidad funcional** | ✅ | Los diez trazados a CU-E02, CU-E04 y CU-E05. Se corrige el catálogo en dos puntos: el nombre del hecho, y que **E2-08 no está bloqueado** |
| **Fiabilidad** | ✅ | Versión final donde toca. FR-OE2-005 evita la fuente que no cuadra |
| **Eficiencia de desempeño** | ✅ | Regla 7. E2-05 calcula percentiles sobre el detalle, que es lo que exige la partición por mes |
| **Capacidad de interacción** | ⚪ | No aplica en esta capa. Frontend implementado en [`../frontend/`](../frontend/) |
| **Seguridad** | ✅ | FR-OE2-003, FR-OE2-004 y **FR-OE2-007**: ningún partner ve el ecosistema. Es la exclusión propia de este módulo, y no es de dato sensible sino **de alcance competitivo** |
| **Compatibilidad** | ✅ | **Es el objetivo que mide el Principio VI.** E2-09 es lo que permite retirar una versión sabiendo quién la usa; sin él, un retiro rompe integraciones activas a ciegas |
| **Mantenibilidad** | ✅ | Reutiliza el armazón de OE6. Un solo departamento de origen |
| **Flexibilidad** | ✅ | El ecosistema de partners es el vehículo de expansión sin infraestructura propia, y E2-11 lo mide |
| **Seguridad física (Safety)** | ⚪ | **No aplica.** Ningún informe influye en el despacho |

**Conflicto identificado y su resolución:** *Idoneidad* pedía los once; *Fiabilidad* impide E2-06.
Regla 2 del Tie-Breaker —no hay Safety—: **no se publica un uptime que sería 100 % por construcción**.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los diez construibles se entregan **sin crear ninguna tabla**.
- **SC-002**: El p95 por endpoint sale ausente bajo la muestra mínima, verificable con el volumen
  actual de 18 llamadas.
- **SC-003**: El excedente facturable publica **llamadas, cupo y precio** junto al importe.
- **SC-004**: Los partners no tarificables aparecen declarados, nunca omitidos.
- **SC-005**: E2-01 y E2-02 declaran `parcial` nombrando el precio que falta.
- **SC-006**: Ninguna respuesta contiene secretos, hashes ni contacto técnico, con el rol de máxima
  autoridad.
- **SC-007**: **Ningún rol de partner accede a ninguno de los diez.**
- **SC-008**: Ningún informe usa el agregado de consumo para algo calculable desde el detalle.
- **SC-009**: E2-06 **no tiene endpoint**.

---

## Assumptions

- ✅ **`Partners-API/informes-compuestos-modelo` ya está implementado** (2026-08-18).
- **`hecho_llamada_api` conserva `latencia_ms` y `codigo_http` por evento** (DDL táctico). E2-05
  es calculable; el p95 sigue sujeto a muestra mínima.
- **El armazón de OE6 está construido.**
- **La muestra mínima se hereda de OE6.** Con 18 llamadas, casi todo caerá por debajo.
- **Esta spec no define pantallas.** El frontend está en [`../frontend/`](../frontend/) (implementado).
