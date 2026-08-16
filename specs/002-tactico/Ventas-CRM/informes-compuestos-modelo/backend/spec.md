# Feature Specification: Informes Compuestos de Ventas y CRM sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Ventas-CRM/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos compuestos de Ventas y CRM — los 13 informes agregados de OT01 a OT03, resueltos con consultas sobre el modelo analítico"

---

## Contexto

Tercer departamento sobre el modelo analítico. Ventas y CRM responde a **cómo entra un cliente**:
capta interesados por canales digitales, los conduce por el embudo hasta convertirlos, y los nutre
con demos y avisos por el camino.

**Es el primero cuyo dominio no toca ni una sola tabla del modelo actual.** Emergencias aportó los
hechos de accidente y despacho; Red Operativa reutilizó la unidad. Aquí todo es nuevo: prospectos,
transiciones de embudo, asignaciones, demos y notificaciones.

**Ningún informe existe hoy**, ni simple ni compuesto. La app de informes tácticos solo sirve
Emergencias.

**Y cubre los dos casos de uso tácticos ausentes del proyecto**, CU-T03 y CU-T04, que hasta ahora no
tenían ningún informe que los satisficiera.

> ### ⚠️ Tres hallazgos medidos antes de especificar
>
> **1. El defecto conocido de `activo` está confirmado, y tiene remedio.** `Dim_Prospecto.activo =
> false` cubre a la vez **convertido y perdido** —2 y 1 filas respectivamente—, que son resultados
> opuestos. Pero el origen sí los distingue en `motivo_inactividad` y en `etapa_actual`. Un informe
> que agrupe por `activo` mezclaría el éxito con el fracaso; agrupando por el motivo, no.
>
> **2. Todo OT03 opera sobre tablas vacías.** `Fact_Interaccion_Demo` y `Fact_NotificacionVentas`
> tienen **0 filas**, y sostienen **5 de los 13 informes**.
>
> ⚠️ **Pero el diagnóstico aquí es distinto al de Emergencias**: sus repositorios **sí publican a
> Kafka** —comprobado en el código—, así que la capacidad de escritura existe y el vacío es de
> entorno, no de diseño. Los cinco informes son correctos y funcionarán en cuanto haya demos.
>
> **3. El CAC no es calculable como está definido.** El catálogo lo apoya en prospectos y clientes,
> que dan las conversiones — **pero el coste por canal no existe en ninguna tabla del sistema**. Es
> el mismo hueco que el propio catálogo ya reconoce para el margen operativo por región, no señalado
> aquí. Ver *Aclaración pendiente*.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Marketing conduce el embudo (Priority: P1) 🎯 MVP

Los cinco informes de **OT02**: cuántos prospectos pasan de cada etapa a la siguiente, cuánto tardan,
cuánta carga lleva cada ejecutivo, cuánto vale el pipeline y por qué se pierden los que se pierden.

**Why this priority**: es el corazón del departamento, **tiene datos reales** —24 transiciones de
embudo sobre 10 prospectos— y satisface **CU-T03**, uno de los dos casos de uso tácticos que hoy no
cubre ningún informe.

**Independent Test**: pedir el embudo de un período y comprobar que el número de prospectos que
entran en una etapa es igual a los que salen más los que siguen ahí.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 1 | **Embudo de conversión**: volumen y % de paso entre etapas | OT02 | **CU-T03** |
| 2 | Tiempo medio de permanencia en cada etapa | OT02 | **CU-T03** |
| 3 | **Carga por ejecutivo**: activos, valor en pipeline y conversiones | OT02 | **CU-T03** |
| 4 | Valor estimado del pipeline ponderado por etapa | OT02 | ± |
| 5 | Motivos de pérdida más frecuentes, por etapa de abandono | OT02 | ± |

**Acceptance Scenarios**:

1. **Given** un prospecto que llegó a «Ganado» y otro que llegó a «Perdido», **When** se pide el
   embudo, **Then** **no se cuentan juntos**. ⚠️ Ambos tienen `activo = false` en el sistema
   operativo: agrupar por esa columna mezclaría una conversión con una pérdida.
2. **Given** un prospecto que pasó por cuatro etapas, **When** se pide el tiempo de permanencia,
   **Then** cada etapa recibe **su** duración, medida entre transiciones consecutivas.
3. **Given** un prospecto que sigue en su etapa actual, **When** se pide el tiempo de permanencia,
   **Then** su etapa cuenta **hasta el fin del período**, no hasta su última transición. Sin eso, los
   prospectos estancados —los que más importan— parecerían los más rápidos.
4. **Given** un prospecto reasignado de un ejecutivo a otro, **When** se pide la carga por ejecutivo
   de un período anterior, **Then** sigue contando para el ejecutivo **de entonces**.
5. **Given** un prospecto perdido en «Propuesta», **When** se piden los motivos de pérdida, **Then**
   aparece con su motivo **y con la etapa en que se abandonó**, no solo con el motivo.

---

### User Story 2 - El Director de Marketing mide la captación por canal (Priority: P2)

Los tres informes de **OT01**: por qué canal llegan los interesados, cuáles convierten mejor y cuánto
cuesta cada cliente conseguido.

**Why this priority**: satisface **CU-T04** —el segundo caso de uso táctico ausente— y contiene un
indicador BSC. Va después del embudo porque **uno de sus tres informes depende de un dato que no
existe** (ver aclaración), y porque la conversión por canal solo tiene sentido cuando el embudo ya
está medido.

**Independent Test**: comprobar que la suma de prospectos de todos los canales es igual al total de
prospectos registrados en el período.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 6 | Volumen de captación por canal y período | OT01 | **CU-T04** |
| 7 | **Tasa de conversión por canal** | OT01 | **CU-T04** |
| 8 | **Clientes convertidos por canal** — la mitad medible del CAC | OT01 | **BSC** *(parcial)* |

**Acceptance Scenarios**:

1. **Given** prospectos de tres canales distintos, **When** se pide el volumen de captación,
   **Then** los tres aparecen y su suma es el total del período; los prospectos sin canal registrado
   aparecen como **Desconocido**, no se descartan.
2. **Given** un canal con 10 prospectos de los que 2 se convirtieron, **When** se pide la tasa de
   conversión, **Then** devuelve 20 % **con su denominador visible**: un 20 % sobre 10 y sobre 1 000
   son afirmaciones muy distintas.
3. **Given** un canal sin ningún prospecto en el período, **When** se pide la tasa de conversión,
   **Then** devuelve **sin dato**, nunca 0 %.

---

### User Story 3 - El Director de Marketing evalúa la nutrición del prospecto (Priority: P3)

Los cinco informes de **OT03**: cuánto se usa la demo, qué partes, si nutrir sirve de algo y cuánto
tarda el equipo en reaccionar a una señal de interés.

**Why this priority**: **las dos tablas que los sostienen están vacías**. Los informes son correctos
y su capacidad de escritura existe, pero hoy devolverían cero. Entregar US1 y US2 antes da valor real
sin esperar a que la operación genere demos.

**Independent Test**: con interacciones sintéticas, comprobar que la efectividad de la nutrición
distingue prospectos con demo de prospectos sin demo.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 9 | Intensidad de uso de la demo: eventos y secciones distintas | OT03 | CU-O24 |
| 10 | Secciones más visitadas de la demo | OT03 | CU-O24 |
| 11 | **Efectividad de la nutrición**: conversión con demo frente a sin demo | OT03 | **CU-T04** |
| 12 | **Latencia de reacción comercial**: del aviso al siguiente avance | OT03 | ± |
| 13 | Reglas de disparo por tasa de acierto | OT03 | ± |

**Acceptance Scenarios**:

1. **Given** un prospecto con demo que convirtió y otro sin demo que no, **When** se pide la
   efectividad de la nutrición, **Then** los dos grupos aparecen con **su propio denominador**.
2. **Given** una notificación sin ningún avance posterior del prospecto, **When** se pide la latencia
   de reacción, **Then** ese aviso cuenta como **sin reacción**, no como latencia cero.
3. **Given** un período sin ninguna interacción de demo, **When** se piden los informes de OT03,
   **Then** devuelven **vacío explícito**, distinguible de «hubo demos y no se usaron».

---

### Edge Cases

- **Un prospecto que retrocede de etapa.** El embudo lo cuenta en ambos pasos; el porcentaje de paso
  se calcula sobre transiciones, no sobre prospectos únicos, y el informe lo declara.
- **Un prospecto sin ninguna transición.** Está en su etapa inicial: cuenta en el embudo como
  presente en esa etapa, y su permanencia se mide desde su registro.
- **Un canal ausente.** Aparece como **Desconocido** y suma en los totales.
- **Un motivo de pérdida vacío.** Se agrupa como «sin motivo registrado», que es información: dice
  que se perdió un prospecto y nadie anotó por qué.
- **Un ejecutivo sin prospectos.** No aparece con carga 0 salvo que se pida explícitamente el listado
  completo de ejecutivos: ausencia de datos no es un dato de cero.
- **Una notificación sin avance posterior.** Latencia **ausente**, contada aparte como sin reacción.

---

## Requirements *(mandatory)*

### Funcionamiento general

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos por informe.
- **FR-002**: Si falta un dato, DEBE ampliarse el modelo según su procedimiento de crecimiento.
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo.
- **FR-004**: Toda consulta sobre un hecho acumulado o una dimensión DEBE forzar la versión final.
- **FR-005**: Todo informe DEBE aceptar un rango de fechas y devolver solo ese período.

### El desenlace de un prospecto ⚠️

- **FR-006**: Los informes NO DEBEN usar `activo` para determinar el desenlace de un prospecto.
  **Esa columna cubre a la vez convertido y perdido**, que son resultados opuestos.
- **FR-007**: El desenlace DEBE derivarse del **motivo de inactividad y de la etapa alcanzada**, que
  sí los distinguen: convertido, perdido y en curso son tres estados separados.
- **FR-008**: Un prospecto **en curso** NO DEBE contarse como perdido por no haber convertido
  todavía.

### El embudo

- **FR-009**: El embudo DEBE medirse sobre **transiciones de etapa**, no sobre el estado actual del
  prospecto: el estado actual no dice por dónde pasó.
- **FR-010**: El porcentaje de paso entre dos etapas DEBE venir **con su denominador**.
- **FR-011**: El tiempo de permanencia en una etapa DEBE medirse entre transiciones consecutivas, y
  la **etapa vigente al final del período** DEBE contarse **hasta el fin del período**. Sin eso, los
  prospectos estancados parecerían los más rápidos.
- **FR-012**: Un prospecto **sin ninguna transición** DEBE contar en su etapa inicial, con
  permanencia medida desde su registro.
- **FR-013**: Los motivos de pérdida DEBEN agruparse **con la etapa de abandono**: el mismo motivo
  significa cosas distintas en «Contactado» y en «Negociación».
- **FR-014**: Un motivo de pérdida ausente DEBE aparecer como **sin motivo registrado**, que es
  información, no como una fila descartada.

### Asignación y carga

- **FR-015**: La carga por ejecutivo DEBE atribuirse al ejecutivo **vigente en el momento medido**,
  no al actual. Una reasignación no debe reescribir la carga histórica de nadie.
- **FR-016**: El valor del pipeline DEBE poder ponderarse **por etapa**, con los pesos como parámetro
  del informe y no como constante horneada.
- **FR-017**: El informe DEBE declarar que esos pesos son **una convención suya**, no una política de
  la empresa: el sistema operativo no define ninguno.

### Canales y conversión

- **FR-018**: El canal de captación DEBE tomarse del origen declarado por el prospecto, y los
  prospectos **sin canal** DEBEN aparecer como **Desconocido** y sumar en los totales.
- **FR-019**: La tasa de conversión por canal DEBE calcularse sobre los prospectos **de ese canal**,
  con denominador visible.
- **FR-020**: Un canal sin prospectos en el período DEBE devolver **sin dato**, nunca 0 %.

#### El CAC, que no es calculable entero *(decisión 2026-08-14)*

El coste de cada canal **no existe en ninguna tabla del sistema**. Se decidió entregar la mitad
medible en vez de dejar el indicador sin nada o inventar el numerador.

- **FR-021**: El informe DEBE entregar **clientes convertidos por canal**, con el volumen de
  prospectos de ese canal como denominador.
- **FR-022**: El informe **NO DEBE** presentarse como CAC ni devolver ningún campo de coste, importe
  o inversión. Ni siquiera vacío: una columna `coste` en la respuesta invita a rellenarla desde
  fuera, y entonces el tablero mostraría un CAC que el sistema no puede sostener.
- **FR-023**: El informe DEBE declarar explícitamente que **es la parte medible del indicador BSC** y
  cuál es la que falta, para que quien lo lea sepa que no está viendo un coste de adquisición.

### Nutrición

- **FR-024**: La efectividad de la nutrición DEBE comparar dos grupos —con demo y sin demo— **cada
  uno con su propio denominador**.
- **FR-025**: La latencia de reacción DEBE medirse desde el aviso hasta **el siguiente avance de
  etapa** del prospecto. Un aviso sin avance posterior cuenta como **sin reacción**, no como latencia
  cero.
- **FR-026**: Los informes de OT03 DEBEN distinguir **«no hubo demos»** de **«hubo demos y no se
  usaron»**: son conclusiones opuestas sobre el producto.

### Presentación y límites

- **FR-027**: Ninguna respuesta DEBE incluir **identidad ni contacto de un prospecto**: nombre,
  apellidos, correo, teléfono ni cargo. Se agrega por empresa, canal, tipo de organización y etapa.
- **FR-028**: El **ejecutivo asignado** DEBE identificarse por su rol en el informe de carga, que es
  su función y no su identidad personal; ningún otro informe DEBE desglosar por persona.
- **FR-029**: Las notas y los textos libres de una transición NO DEBEN copiarse al modelo.
- **FR-030**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-031**: Un período sin datos DEBE devolver un resultado vacío explícito.

### Acceso

- **FR-032**: Los informes DEBEN ser de solo lectura.
- **FR-033**: El **Director de Marketing** —autoridad de Ventas y CRM según el §5.1 del SRS— DEBE
  acceder sin acotamiento por titularidad.
- **FR-034**: Un **ejecutivo comercial** DEBE ver los informes **acotados a sus propios prospectos**.
- **FR-035**: La exención de la autoridad NO DEBE alcanzar al dato sensible.

### Ampliaciones del modelo

- **FR-036**: El modelo DEBE incorporar una **dimensión de prospecto**, sin datos de contacto.
- **FR-037**: El modelo DEBE incorporar un **hecho de transición de embudo**, con etapa anterior,
  etapa nueva, motivo de pérdida y duración en la etapa anterior.
- **FR-038**: El modelo DEBE incorporar un **hecho de asignación**, para atribuir la carga al
  ejecutivo vigente en cada momento.
- **FR-039**: El modelo DEBE incorporar un **hecho de interacción de demo** y un **hecho de
  notificación de ventas**, aunque hoy sus fuentes estén vacías.
- **FR-040**: El modelo DEBE conservar la **conversión de prospecto a cliente**, para poder cerrar el
  ciclo de captación.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los 13 informes se obtienen sin que exista ninguna tabla dedicada a un informe.
- **SC-002**: Un prospecto convertido y otro perdido **nunca se cuentan juntos**, pese a compartir el
  mismo valor en la columna de actividad del sistema operativo.
- **SC-003**: En el embudo, los prospectos que entran en una etapa son iguales a los que salen más
  los que permanecen.
- **SC-004**: Un prospecto estancado en una etapa muestra **la permanencia mayor**, no la menor.
- **SC-005**: El 100 % de la carga histórica por ejecutivo se conserva tras una reasignación.
- **SC-006**: La suma de prospectos de todos los canales, incluido «Desconocido», es igual al total
  del período.
- **SC-007**: Ningún informe devuelve nombre, correo, teléfono ni cargo de un prospecto, **para
  ningún rol**.
- **SC-008**: Un ejecutivo comercial solo obtiene datos de sus propios prospectos.
- **SC-009**: Los informes de OT03 distinguen «no hubo demos» de «hubo demos y no se usaron».
- **SC-010**: Añadir estos informes **no altera** ninguna cifra de Emergencias ni de Red Operativa.

---

## Assumptions

- **El modelo analítico está cargado.** Este departamento **no reutiliza ninguno de sus hechos**: los
  cinco que necesita son nuevos.
- **El período por defecto** son los últimos 30 días.
- **Los pesos de ponderación del pipeline** por defecto son crecientes por etapa y **parametrizables**.
  El sistema operativo no define ninguno.
- **El frontend queda fuera de alcance.**
- **Las fases 1 y 2 de Emergencias están implementadas**: este módulo reutiliza su plomería y no crea
  ninguna propia.

---

## Riesgos ⚠️

### Cinco informes sobre tablas vacías, pero por una razón distinta

`Fact_Interaccion_Demo` y `Fact_NotificacionVentas` tienen **0 filas**, y sostienen todo OT03.

**El diagnóstico importa y aquí sí se pudo hacer:** ambos repositorios **publican a Kafka**, así que
el camino de escritura existe y está implementado. El vacío es de **entorno** —nadie ha ejercitado
una demo—, no de diseño.

Es mejor situación que la de Emergencias, donde no se pudo determinar si la operación llegaba a
escribir. Aquí los cinco informes funcionarán en cuanto haya demos, y sus pruebas van con datos
sintéticos.

### Volúmenes pequeños en el resto

10 prospectos, 24 transiciones, 9 asignaciones, 4 clientes. El embudo tiene datos suficientes para
ser correcto y **no para ser representativo**.

---

## Aclaración, resuelta el 2026-08-14

**Informe #8 → se entrega «clientes convertidos por canal», no el CAC** (FR-021 a FR-023).

El coste de cada canal no existe en ninguna tabla: no hay inversión publicitaria, ni presupuesto por
campaña, ni coste imputado. Es el mismo hueco que el catálogo ya reconoce para el margen operativo
por región, y que aquí no estaba señalado.

**Lo que se entrega es la mitad medible del indicador, y se dice que lo es.** FR-022 prohíbe incluso
devolver una columna de coste vacía: una columna así invita a rellenarla desde fuera, y entonces el
tablero mostraría un CAC que el sistema no puede sostener. El BSC queda **parcialmente cubierto y
declarado como tal**, que es más honesto que un indicador completo con un número inventado.

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato y su procedimiento de
  crecimiento.
- **[`Emergencias/informes-compuestos-modelo/`](../../Emergencias/informes-compuestos-modelo/)** —
  aporta la plomería: cargador de consultas, repositorio, período y permisos.
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — quién ve qué.
