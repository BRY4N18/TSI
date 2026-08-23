# Feature Specification: OE4 — Registro Histórico como Ventaja Competitiva e Inteligencia Predictiva

**Feature Branch**: `001-estrategico/OE4-inteligencia-predictiva/backend`

**Created**: 2026-08-16

**Status**: Implemented

**Input**: User description: "Informes estratégicos del OE4 — los quince informes que miden la calidad del histórico de accidentes, lo convierten en inteligencia de mercado vendible y evalúan el modelo predictivo, resueltos con consultas sobre el modelo analítico."

---

## Contexto

Segundo módulo de la capa estratégica. **Reutiliza el armazón que OE6 construyó** —período, ventanas
comparadas, objetivo BSC, envelope, permisos— y no lo redefine. Lo que aporta es su dominio.

El objetivo dice: *transformar el registro histórico de accidentes en una ventaja competitiva,
usando análisis predictivo para anticipar zonas de alta siniestralidad, ubicar preventivamente las
unidades y vender inteligencia de mercado de alto valor.*

**Es el único OE cuyo producto se vende.** E4-12 y E4-13 no son informes de gestión interna: son el
dato que una aseguradora o un municipio paga por recibir. Eso cambia el listón de dos cosas —la
calidad del dato y la honestidad sobre sus huecos— porque un cliente que compra un mapa de
siniestralidad no puede distinguir un cero real de un cero por falta de registro.

### La condición previa del objetivo, y por qué US1 es el MVP

Un registro histórico solo es una ventaja competitiva **si es fiable**. Los cinco informes que
venden inteligencia (US2) descansan sobre un histórico cuya calidad nadie mide todavía, y los cinco
del modelo predictivo (US4) se entrenan con él.

Por eso el MVP no es el mapa de siniestralidad, que es lo vistoso: **es medir la calidad del
histórico**, que es lo que dice si lo demás vale algo.

---

## Tres hallazgos que salieron al verificar contra el almacén

### 1. E4-01 ya existe, con el diseño que el proyecto abandonó 🔴

`indice_calidad_historico` es una tabla en `tsi_tactico` con **182 filas**, una por día, y columnas
que son exactamente sus métricas: `pct_completitud`, `pct_descarte`, `pct_fusion`,
`pct_cobertura_evidencia`, `indice_consolidado`.

**Es una tabla por informe** — el patrón que el modelo analítico existe para sustituir, y del que su
propia spec dice: *«con ~105 informes significaría ~105 tablas y ~105 flujos de carga»*.

Y sus cifras **no cuadran con el modelo** en la única métrica donde hay algo que comparar:

| Día | `pct_cobertura_evidencia` legado | Calculado sobre el modelo |
|---|--:|--:|
| 2026-08-13 | 0,50 | 0,00 |
| 2026-08-12 | 1,00 | 0,25 |

⚠️ **No se afirma aquí que el legado esté mal.** Con **3 fotografías en 4 252 casos**, ninguna de las
dos cifras es concluyente: son dos y cuatro casos de diferencia. Precisamente por eso el informe se
migra a una consulta sobre el modelo **con una prueba de contraste**, en vez de dar por buena la
tabla o por buena la consulta. Es el mismo tratamiento que el módulo táctico dio a sus 13 informes
vigilados, y que encontró tres defectos reales.

> Las otras dos tablas legadas —`perdida_senal_gps` y `rendimiento_por_proveedor`— **no son de OE4**.
> La primera ya fue migrada por el módulo táctico, que descubrió que analizaba 10 000 de 59 045
> posiciones. Se mencionan aquí solo para dejar claro que el patrón se repitió tres veces.

### 2. Dos informes parecían parciales — ✅ **los dos se completan** *(corregido en `/plan`)*

| Informe | Lo que parecía faltar | Lo que se comprobó |
|---|---|---|
| **E4-06** Patrón horario **y climático** | La condición climática, porque `num_elementos_clima` es un recuento | ✅ **La condición existe** en `Dim_EstadosClimas` del origen. Se carga como columna de `hecho_accidente`. ⚠️ Pero son **3 casos de 4 252**, así que la mitad climática se entrega con la **escasez declarada** |
| **E4-13** Impacto vial: duración **y extensión** | La distancia afectada | ✅ **`distanciamillas` existe** en `Fact_Accidente`, con **4 200 de 4 252 casos (98,8 %)**. Se carga como métrica |

**Son los dos informes que este objetivo vende**, y entregaban la mitad del producto. Las dos
ampliaciones son `ALTER TABLE … ADD COLUMN` sobre un hecho existente, no tablas nuevas. Ver
[`research.md`](research.md) D3 y D4.

### 2.bis ⛔ **E4-14 no es medible** *(hallazgo de `/plan`)*

Esta spec lo daba por construible en US3. **No lo es, y no por falta de datos.**

`cargado_en` no mide la latencia de ingesta: las **4 252 filas comparten exactamente el mismo valor**
—una sola carga—, así que la resta devuelve la antigüedad del accidente, no cuándo estuvo disponible.
Y no se arregla esperando: **la regla de idempotencia del modelo lo impide por diseño**, porque cada
recarga hace `DROP PARTITION` e inserta de nuevo, reescribiendo la columna entera.

Pasa a **no construible**, dentro de US3. Ver [`research.md`](research.md) D5.

### 3. El dato de origen de este objetivo es pobre, y hay que decirlo

Medido sobre los 4 252 casos:

| Dato | Filas con valor |
|---|--:|
| `num_notas`, `num_elementos_clima`, `severidad_inicial` | 4 252 ✅ |
| Casos con alguna fotografía | **2** |
| Fotografías totales | **3** |
| `resultado_atencion` | **1** |
| `calificacion` | **0** |

**Varios informes van a devolver cifras cercanas a cero, y será correcto.** El trabajo de este módulo
es que se lean como *«esto no se registra»* y no como *«esto no ocurre»* — que son conclusiones
opuestas y llevan a decisiones opuestas: la primera se arregla con formación y la segunda con nada.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Datos sabe si el histórico es fiable (Priority: P1) 🎯 MVP

Cuatro informes: **E4-01**, **E4-02**, **E4-03** y **E4-04**. Responden si el registro histórico
—el activo que este objetivo quiere convertir en ventaja competitiva— tiene la calidad para serlo.

**Why this priority**: es la condición previa de todo lo demás. Vender un mapa de siniestralidad
construido sobre un histórico incompleto es vender un producto defectuoso, y entrenar un modelo
predictivo con él es peor. Además **migra la última tabla legada de este dominio**.

**Independent Test**: pedir el índice de calidad de un trimestre y comprobar que sus cuatro
componentes son consultables por separado, que cuadran con el índice consolidado, y que la tabla
`indice_calidad_historico` **no ha hecho falta**.

| Informe | Ruta | Origen |
|---|---|---|
| **E4-01** Índice consolidado de calidad | `indice-calidad-historico` | **BSC** / **CU-E06** |
| **E4-02** Completitud de campos críticos | `completitud-campos-criticos` | **BSC** / **CU-T14** |
| **E4-03** Campos con mayor tasa de ausencia | `campos-mas-ausentes` | **CU-T14** |
| **E4-04** Calidad por origen: central vs campo | `calidad-por-origen` | ± |

**Acceptance Scenarios**:

1. **Given** un trimestre con casos registrados, **When** se pide el índice consolidado, **Then**
   devuelve sus cuatro componentes por separado **además** del índice, para que se pueda ver cuál lo
   arrastra.
2. **Given** la completitud, **When** se calcula, **Then** usa la **ausencia real del modelo**, no
   una comparación contra nulidad sobre el sistema operativo, donde la condición es siempre cierta.
3. **Given** el ranking de campos ausentes, **When** un campo no tiene ninguna ausencia, **Then**
   aparece con cero, **no desaparece del ranking**. Un campo que sale de la lista se confunde con un
   campo que nadie revisó.
4. **Given** el mismo período, **When** se comparan las cifras con `indice_calidad_historico`,
   **Then** la prueba de contraste **declara toda divergencia con su causa**, en vez de tolerarla.
5. **Given** cualquiera de los cuatro, **When** lo consulta `DirectorDatos`, **Then** la respuesta no
   contiene identidad de operadores ni de técnicos de campo.

---

### User Story 2 - Convertir el histórico en inteligencia vendible (Priority: P2)

Cuatro informes: **E4-05**, **E4-06**, **E4-12** y **E4-13**. Es el producto: dónde se concentran los
accidentes, cuándo, a cuánta gente afectan y cuánto tráfico paralizan.

**Why this priority**: es lo que el objetivo llama *inteligencia de mercado de alto valor*, y lo que
una aseguradora o un municipio compra. Va después de US1 porque **vender un mapa construido sobre un
histórico cuya calidad no se ha medido es vender a ciegas**.

**Independent Test**: pedir el mapa de concentración de un trimestre y comprobar que la suma de los
casos por ubicación es igual al total del período, y que los dos informes parciales declaran qué les
falta.

| Informe | Ruta | Origen | |
|---|---|---|:--:|
| **E4-05** Mapa de concentración de siniestralidad | `concentracion-siniestralidad` | **CU-E06** / **CU-T15** | ✅ |
| **E4-06** Patrón horario y climático | `patron-horario-climatico` | **CU-E06** / **CU-T15** | ✅ 🆕 |
| **E4-12** Impacto humano por zona | `impacto-humano-por-zona` | **CU-E06** / ± | ✅ |
| **E4-13** Impacto vial por zona | `impacto-vial-por-zona` | **CU-E06** / ± | ✅ 🆕 |

> **Los cuatro se entregan completos**, tras las dos ampliaciones del modelo que `/plan` desbloqueó.
> 🆕 marca los que necesitan una columna nueva en `hecho_accidente`.

**Acceptance Scenarios**:

1. **Given** un período, **When** se pide el mapa de concentración, **Then** la suma de casos por
   ubicación **es igual** al total del período, y los casos sin ubicación resoluble aparecen como
   «Desconocido» en vez de desaparecer.
2. **Given** el patrón horario y climático, **When** se pide, **Then** entrega el patrón horario
   sobre los 4 252 casos **y** la condición climática, declarando `cobertura: "parcial"` mientras la
   muestra climática —3 casos— esté por debajo del mínimo. Un reparto por clima sobre tres casos
   tiene la forma de un patrón y el significado de una anécdota.
3. **Given** el impacto vial, **When** se pide, **Then** entrega **duración y distancia**, con
   `casos_con_duracion` y `casos_con_distancia` **por separado**: si fueran iguales, la distancia
   estaría entrando como cero en los casos sin dato.
4. **Given** el impacto humano, **When** un caso no tiene víctimas registradas, **Then** **no cuenta
   como cero víctimas**: se declara aparte en el denominador.
5. **Given** cualquiera de los cuatro, **When** se pide, **Then** la ubicación se expresa **por
   nombre** y nunca por coordenadas.

---

### User Story 3 - Saber si el histórico sirve para entrenar (Priority: P3)

Dos informes: **E4-15** ✅ y **E4-14** ⛔. Responden si hay suficiente volumen por zona como para
entrenar un modelo, y si el dato llega a tiempo al analítico — **lo segundo no es medible**.

> **E4-14 pasó a bloqueado en `/plan`.** No falta el dato: la **regla de idempotencia** del modelo
> impide medirlo. Cada recarga reescribe `cargado_en` de la partición entera, así que la columna
> nunca puede decir cuándo estuvo disponible un caso por primera vez. Se queda en esta historia,
> declarado, porque su pregunta pertenece aquí. Ver [`research.md`](research.md) D5.

**Why this priority**: son los dos que **preparan US4**. Entrenar un modelo sobre una zona con
cuarenta casos produce un modelo que parece funcionar y no generaliza; y un dato que tarda dos días
en llegar al analítico no sirve para un producto que se vende como tiempo real.

**Independent Test**: pedir la latencia de ingesta y la cobertura por zona, y comprobar que las zonas
por debajo del umbral de masa crítica se identifican explícitamente.

| Informe | Ruta | Origen | |
|---|---|---|:--:|
| **E4-15** Cobertura del histórico por zona | `cobertura-del-historico` | **CU-T15** / ± | ✅ |
| **E4-14** Latencia de ingesta al analítico | — | ± | ⛔ |

**Acceptance Scenarios**:

1. **Given** la cobertura del histórico, **When** una zona no alcanza el umbral, **Then** se marca
   explícitamente como **sin masa crítica para entrenar**, y **el umbral se publica en la respuesta**:
   sin él, la afirmación no es accionable.
2. **Given** que no hay modelo todavía —los cinco informes que lo evalúan están bloqueados—, **When**
   se fija el umbral, **Then** es un **parámetro**, no un valor fijo en la spec. El número de casos
   que necesita un modelo depende del modelo.
3. **Given** que el eje de región no existe, **When** se pide la cobertura, **Then** se agrupa **por
   condado** y la respuesta lo declara.
4. **Given** que `cargado_en` se reescribe en cada recarga, **When** se implementa el módulo,
   **Then** **no se publica endpoint para E4-14**. Publicarlo devolvería una mediana de ~1 971 horas
   que parece una latencia de ingesta y es la antigüedad del accidente.

---

### User Story 4 - Evaluar el modelo predictivo (Priority: P4) ⛔ BLOQUEADA

Cinco informes: **E4-07** a **E4-11**. **Ninguno es construible hoy**, y no por falta de diseño: las
tres tablas que los sostienen no existen en ningún sitio del sistema.

**Why this priority**: está aislada al final **precisamente porque está bloqueada**. Repartir estos
cinco entre las historias anteriores habría hecho que un prerrequisito de datos detuviera el MVP.

| Informe | Prerrequisito |
|---|---|
| **E4-07** Precisión del modelo predictivo *(BSC, meta ≥80 %)* | `registro_modelos` |
| **E4-08** Contraste predicción vs ocurrencia real | `registro_predicciones` |
| **E4-09** Unidades preposicionadas *(BSC, meta ≥60 %)* | `registro_predicciones` |
| **E4-10** Versiones del modelo predictivo | `registro_modelos` |
| **E4-11** Productos de inteligencia comercializados *(BSC)* | `catalogo_productos_inteligencia` |

**Acceptance Scenarios**:

1. **Given** que las tres tablas no existen, **When** se implementa este módulo, **Then** **no se
   publica ningún endpoint** para los cinco. Un `200` con ceros diría que el modelo predictivo tiene
   una precisión del 0 %, cuando lo cierto es que no hay modelo del que hablar.
2. **Given** el tablero estratégico, **When** pide los indicadores BSC de este objetivo, **Then**
   **tres de ellos se declaran inmedibles** con su prerrequisito nombrado.

> ⚠️ **Esto deja tres indicadores del tablero sin fuente**: precisión del modelo, unidades
> preposicionadas y productos de inteligencia. Los tres pertenecen a la perspectiva de Aprendizaje y
> crecimiento, que es la de este objetivo. **OE4 solo puede cubrir hoy la mitad de su propio BSC**, y
> es lo primero que hay que saber al leer su tablero.

---

### Edge Cases

- **Un período sin ningún accidente.** `data: []` con `cobertura: "completa"`. En este dominio es una
  buena noticia, y hay que poder distinguirla de un fallo de carga.
- **Un campo que nunca falta.** Aparece en el ranking de ausencias con cero, no se omite.
- **Una zona con un solo caso.** No entra en el mapa de concentración como zona de riesgo: un caso no
  es una concentración. Se declara bajo el umbral.
- **Un caso cargado con retraso.** Cuenta en la latencia de ingesta del período de **su accidente**,
  no del de su carga. Atribuirlo por la carga escondería precisamente los retrasos.
- **La calificación de cierre, con cero filas.** Cualquier informe que la use devuelve la medida
  **ausente**, nunca 0 — que en una escala de calificación sería la peor nota posible.

---

## Requirements *(mandatory)*

### Transversales — heredados, no redefinidos

- **FR-OE4-001**: Este módulo **reutiliza sin modificar** las piezas transversales que OE6 construyó:
  `periodo_estrategico.py`, `objetivo.py`, `envelope.py` y el repositorio del almacén. **No las
  redefine.** Si alguna necesitara cambiar, se cambia allí y para los seis OE.
- **FR-OE4-002**: Los diez informes construibles DEBEN resolverse con **una consulta sobre el modelo**.
  Ninguno crea una tabla propia.
- **FR-OE4-003**: Toda consulta sobre `hecho_accidente` y las dimensiones DEBE forzar la versión
  final; **está prohibido** sobre `hecho_evidencia`, que es de transacción.
- **FR-OE4-004**: Ningún informe DEBE devolver coordenadas ni identidad de personas —implicados,
  conductores, operadores o técnicos de campo—, **tampoco para `DirectorDatos`**.
- **FR-OE4-005**: Ningún informe DEBE agrupar por región ni unir con `dim_region`
  (`decisiones-pendientes.md` #38). Se agrupa por **condado**.

### Permisos

- **FR-OE4-006**: Acceden **`DirectorDatos`** y **`Gerente`**. En los informes que miden el expediente
  de accidente —E4-01 a E4-04, E4-12, E4-13— accede además **`DirectorOperaciones`**, porque el
  expediente es de su departamento y su calidad se mide contra su operación
  (`acceso-estrategico.md` §4.4).
- **FR-OE4-007**: Ningún otro rol accede. Un rol operativo recibe `403`.

### US1 — la calidad del histórico

- **FR-OE4-008**: **E4-01** DEBE devolver los **cuatro componentes por separado** además del índice
  consolidado: completitud, descarte, fusión y cobertura de evidencia. Un índice único sin sus partes
  dice que la calidad bajó y no dice por qué, que es lo único accionable.
- **FR-OE4-009**: **E4-01** DEBE declarar cómo se compone el índice. Un número consolidado cuya
  fórmula no se publica no es verificable por quien lo lee.
- **FR-OE4-010**: **E4-01** DEBE **sustituir a `indice_calidad_historico`**, y la tabla legada queda
  para contraste, no como fuente.
- **FR-OE4-011**: **E4-02** DEBE medir la completitud contra la **ausencia real del modelo**.
- **FR-OE4-012**: **E4-03** DEBE incluir en el ranking **todos** los campos críticos, también los que
  no tienen ninguna ausencia, con cero.
- **FR-OE4-013**: **E4-04** DEBE distinguir la calidad del dato capturado en central de la del
  capturado en campo, usando la categoría de la nota de `hecho_evidencia`.

### US2 — la inteligencia vendible

- **FR-OE4-014**: **E4-05** DEBE entregar la concentración por condado, ciudad y calle, con top N y
  porcentaje acumulado, y los casos sin ubicación resoluble como «Desconocido».
- **FR-OE4-015**: **E4-06** DEBE entregar el patrón por **franja horaria y día de semana** sobre los
  4 252 casos, **y la condición climática** desde la columna nueva, declarando `cobertura: "parcial"`
  mientras la muestra climática esté por debajo del mínimo.
- **FR-OE4-016**: **E4-12** DEBE distinguir «cero víctimas» de «víctimas no registradas», publicando
  `casos_con_dato` como denominador real.
- **FR-OE4-017**: **E4-13** DEBE entregar **duración y distancia**, con sus dos denominadores por
  separado, y DEBE declarar **desde cuándo existe la métrica de distancia** (Regla 6).
- **FR-OE4-017b**: Las dos métricas nuevas DEBEN cargarse como `Nullable` **sin valor por defecto**.
  Rellenar con `0` las filas anteriores hundiría el promedio y presentaría «no lo medíamos» como «no
  hubo afectación».
- **FR-OE4-017c**: La carga DEBE **fallar** si algún caso tiene más de un elemento climático. Hoy la
  cardinalidad es 1:0..1; si cambiara, una columna desnormalizada **elegiría uno en silencio**.
- **FR-OE4-018**: Los cuatro informes de esta historia DEBEN expresar la ubicación **por nombre**.

### US3 — la aptitud del histórico

- **FR-OE4-019**: ~~E4-14 DEBE medir el retraso entre el accidente y su disponibilidad.~~ ❌
  **Retirado el 2026-08-16**: no es medible. `cargado_en` se reescribe entero en cada recarga por la
  regla de idempotencia. Ver US3 y `research.md` D5.
- **FR-OE4-020**: **E4-15** DEBE marcar explícitamente las zonas **por debajo del umbral de masa
  crítica**, con el umbral **configurable** y **declarado en la respuesta**.

### US4 y E4-14 — lo bloqueado

- **FR-OE4-021**: Los cinco informes de US4 **y E4-14** —seis en total— **NO DEBEN publicarse como
  endpoint**. No se devuelve `200` con ceros.
- **FR-OE4-022**: La documentación del módulo DEBE declarar que **tres indicadores del BSC de este
  objetivo quedan sin fuente**, con su prerrequisito nombrado.

---

## Cumplimiento ISO/IEC 25010:2023

| Característica | Aplica | Cómo |
|---|:--:|---|
| **Idoneidad funcional** | ✅ | Los quince salen del catálogo con origen trazado. Los tres huecos que el catálogo no declaraba —clima, distancia, región— se declaran aquí en vez de heredarse |
| **Fiabilidad** | ✅ | El módulo **no participa en la operación**: mide su registro. La regla de versión final evita la cifra inflada intermitente |
| **Eficiencia de desempeño** | ✅ | Regla 7: filtrar particiones por fecha. E4-05 acota además con top N |
| **Capacidad de interacción** | ⚪ | No aplica en esta capa. Frontend implementado en [`../frontend/`](../frontend/) |
| **Seguridad** | ✅ | FR-OE4-004. Es el OE donde más importa: sus productos **se venden a terceros**, y un mapa de siniestralidad con coordenadas exactas o identidad de implicados sería una fuga con destinatario comercial |
| **Compatibilidad** | ✅ | Contrato OpenAPI bajo el envelope común. E4-12 y E4-13 son candidatos a exponerse vía la API de partners, lo que hace su contrato más sensible al cambio que el del resto |
| **Mantenibilidad** | ✅ | Reutiliza el armazón de OE6 sin duplicarlo, y **retira la última tabla legada** de este dominio |
| **Flexibilidad** | ⚠️ | Igual que OE6: el eje de región no existe. E4-15 agrupa por condado |
| **Seguridad física (Safety)** | ✅ | Indirecta pero real: E4-09 mide si las unidades se preposicionan según el modelo, y **un modelo mal evaluado desplaza ambulancias a las zonas equivocadas**. Que esté bloqueado no lo hace menos crítico — lo hace más urgente |

**Conflictos entre características:** *ninguno identificado.*

---

## Success Criteria *(mandatory)*

- **SC-001**: Los **nueve** informes construibles se entregan **sin crear ninguna tabla** —el recuento
  del almacén no cambia—, y `indice_calidad_historico` deja de ser fuente de nada.
- **SC-002**: El índice de calidad se puede descomponer en sus cuatro partes desde la propia
  respuesta, y **reproduce la fórmula del legado** sobre sus 182 días.
- **SC-003**: **E4-06 y E4-13 entregan sus dos mitades.** La climática de E4-06 declara
  `cobertura: "parcial"` mientras la muestra sea insuficiente; la distancia de E4-13 publica su propio
  denominador, distinto del de duración.
- **SC-004**: Ningún dato ausente se presenta como cero: ni víctimas no registradas, ni calificación
  sin registrar, ni campos sin revisar, **ni las métricas nuevas en las filas anteriores a su
  incorporación**.
- **SC-005**: Los **seis** informes bloqueados —los cinco de US4 y E4-14— **no tienen endpoint**, y la
  documentación nombra sus cuatro prerrequisitos.
- **SC-005b**: **Ningún `cumple` es booleano** en todo el módulo: todas las metas de OE4 son
  `[CALIBRAR]`.
- **SC-006**: Ningún informe devuelve coordenadas ni identidad, consultado con el rol de máxima
  autoridad.
- **SC-007**: Las cifras coinciden con su equivalente táctico donde exista, y **toda divergencia con
  `indice_calidad_historico` se declara con su causa** en vez de tolerarse.
- **SC-008**: Un rol operativo recibe `403` en los diez.

---

## Assumptions

- **El armazón de OE6 está construido.** Este módulo depende de él y no lo reimplementa. Si OE6 no se
  ha implementado, las fases 1 y 2 de su `tasks.md` son prerrequisito de este módulo.
- ✅ **El umbral de masa crítica** — resuelto en `/plan`: **parámetro configurable**, referencia
  inicial 500, publicado en la respuesta. No se fija en la spec porque no hay modelo todavía.
- ✅ **La fórmula del índice consolidado** — **descifrada y verificada** en `/plan` contra seis filas
  del legado: `(completitud + (1−descarte) + (1−fusión) + cobertura_evidencia) / 4`. Se conserva. Es
  una media **sin ponderar**, lo cual es discutible, y revisarla queda como cambio posterior y
  aislado: cambiarla a la vez que se migra el informe haría imposible saber cuál de los dos movió las
  cifras.
- **Las tres tablas de US4 no se diseñan aquí.** Pertenecen al módulo operativo de Analítica-ML
  (`predictive-ai-accident-rate`), que ya existe como spec.
- **Esta spec no define pantallas.** El frontend está en [`../frontend/`](../frontend/) (implementado).
