# Feature Specification: Informes Compuestos de Emergencias sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Emergencias/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Implemented

**Input**: User description: "Informes tácticos compuestos de Emergencias — los informes agregados de OT21 a OT25, resueltos con consultas sobre el modelo analítico en vez de una tabla y un flujo por informe"

---

## Contexto: qué cambia respecto de todo lo anterior

Los siete módulos de **listados** se resuelven contra la base operativa: una tabla, filtros, orden y
paginación. Estos no. Un informe compuesto **agrega, cruza o mide el paso del tiempo**, y hasta ahora
eso exigía crear una tabla propia y un flujo que la alimentara.

Ese diseño ya existe, con tres informes construidos, y **se sustituye**: con 26 informes solo en este
departamento serían 26 tablas y 26 flujos, cada uno con su forma de calcular lo mismo y su
oportunidad de discrepar.

Desde el 2026-08-14 hay un **modelo analítico** cargado y verificado —5 dimensiones y 4 hechos— sobre
el que un informe es **una consulta**. Este módulo especifica los 26 informes de Emergencias sobre
ese sustrato.

> ## ⚠️ 16 de los 26 ya existen — corrección de alcance
>
> Detectado al planificar: **16 de estos informes ya tienen endpoint construido y funcionando**, en
> el módulo `informes-tacticos-agregados`, agregando **directamente contra Pinot**.
>
> El alcance real de este módulo es: **construir 10 nuevos**, **migrar 3 que dan cifras equivocadas**
> —completitud, ratio demanda/capacidad y pérdida de señal— y **dejar en su sitio los 13 que
> funcionan bien**, vigilados por una prueba de contraste que falla si divergen del modelo.
>
> Migrar trece endpoints correctos sería riesgo de regresión sin valor visible. El detalle y su
> justificación están en [`plan.md`](plan.md).

> **Discrepancia del catálogo, detectada al especificar.** La tabla resumen de
> `TSI-Informes-Tacticos-Requeridos-por-OT.md` atribuye a Emergencias **14 simples y 25 compuestos**.
> Contando las filas reales salen **12 simples, 26 compuestos y 1 que no es un informe** (parámetros
> de asignación, que es configuración). Ambos suman 39, pero el reparto no coincide. **Esta spec va
> con las filas**, que son la fuente, y el resumen queda por corregir.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Operaciones ve qué se registró y con qué calidad (Priority: P1) 🎯 MVP

Los seis informes de **OT21**. Responden a la pregunta más básica de la capa táctica: *cuántos casos
hubo, de qué gravedad, dónde, y con qué calidad quedaron registrados*.

**Why this priority**: es el bloque de entrada al departamento y **el modelo ya lo sostiene por
completo** — cero trabajo de infraestructura previo. Además contiene el informe con el defecto más
grave del catálogo (completitud), cuya corrección ya está construida y sin usar.

**Independent Test**: pedir los seis informes de un período y comprobar que devuelven cifras que
cuadran con el total de casos de ese período, sin que se haya creado ninguna tabla.

**Los seis informes**:

| # | Informe | OT | Origen |
|--:|---|---|---|
| 1 | Distribución por severidad | OT21 | OP32 |
| 2 | Distribución por zona | OT21 | OP32 |
| 3 | **Completitud de campos críticos** | OT21 | **BSC** |
| 4 | Descarte y fusión de reportes | OT21 | OP33 |
| 5 | Ranking de ubicaciones con más casos | OT21 | ± |
| 6 | Impacto humano por ubicación | OT21 | ± |

**Acceptance Scenarios**:

1. **Given** un período con casos registrados, **When** se pide la distribución por severidad,
   **Then** la suma de todas las severidades es igual al total de casos del período.
2. **Given** el mismo período, **When** se pide la distribución por zona, **Then** ningún caso queda
   fuera del reparto: los que no tienen ubicación resoluble aparecen como «Desconocido», no
   desaparecen.
3. **Given** un caso al que le falta la severidad o la calle, **When** se pide la completitud,
   **Then** ese caso cuenta como incompleto. ⚠️ **El informe actual no puede detectarlo**: compara
   contra nulidad y el sistema operativo usa valores centinela, así que su respuesta es siempre
   «100 % completo».
4. **Given** un caso descartado y otro fusionado, **When** se piden descartes y fusiones, **Then**
   cada uno cuenta en su categoría y **no se confunden entre sí** ni con los cerrados — el sistema
   operativo los marca los tres igual.
5. **Given** un período, **When** se pide el ranking de ubicaciones, **Then** las ubicaciones vienen
   por nombre y **nunca por coordenadas**.

---

### User Story 2 - El Director de Operaciones mide el desempeño del despacho (Priority: P1)

Los diez informes de **OT22 y OT23**: cuánto se tarda en confirmar, en asignar y en llegar; cuántos
intentos hacen falta; qué unidades rechazan; qué misiones se pierden por el camino.

**Why this priority**: es el corazón del tablero — cuatro de sus informes son indicadores **BSC**
comprometidos. Nueve de los diez ya los sostiene el modelo, y dos de ellos **corrigen defectos
documentados**.

**Independent Test**: cambiar el proveedor de una unidad y comprobar que los informes históricos de
desempeño **no reatribuyen** su trabajo anterior.

**Los diez informes**:

| # | Informe | OT | Origen | Nota |
|--:|---|---|---|---|
| 7 | Asignación automática vs manual | OT22 | OP35 | |
| 8 | Tiempo de reportado a confirmado | OT22 | **BSC** | |
| 9 | Tiempo de respuesta por severidad | OT22 | **BSC** | |
| 10 | Rechazo y timeout por unidad | OT22 | SRS | |
| 11 | Carga por unidad | OT22 | ± | |
| 12 | **Ratio demanda / capacidad por condado** | OT22 | **CU-T08** | ⚠️ corrige defecto |
| 13 | Despachos resueltos al primer intento — meta ≥90 % | OT22 | **BSC** | |
| 14 | **Pérdida de señal** | OT23 | CU-O69 | ⚠️ corrige defecto |
| 15 | Abortos y pérdidas de misión | OT23 | CU-O71 | |
| 16 | Desviación entre estimación de llegada y llegada real | OT23 | ± | ⚠️ estimación derivada, ver FR-029 |

**Acceptance Scenarios**:

1. **Given** un caso con tres intentos de despacho —dos rechazados y uno confirmado—, **When** se
   pide «resueltos al primer intento», **Then** ese caso **no** cuenta como resuelto al primer
   intento, y los tres intentos son visibles. Un informe con grano «caso» los colapsaría en uno y
   **el rechazo desaparecería de las cifras**.
2. **Given** un despacho que terminó abortado, **When** se piden abortos y pérdidas, **Then** cuenta
   como abortado y **no** como en curso ni como rechazado. Son cuatro desenlaces distintos más uno
   sin terminar.
3. **Given** una unidad que cambió de proveedor en junio, **When** se pide el rendimiento de marzo,
   **Then** ese trabajo sigue atribuido al proveedor de marzo.
4. **Given** un período pasado, **When** se pide el ratio demanda/capacidad, **Then** la capacidad
   es la **de aquel período**, no la flota de hoy. ⚠️ El informe actual usa la flota actual: un ratio
   de hace tres meses se calcula contra unidades que quizá no existían.
5. **Given** el conjunto completo de posiciones reportadas, **When** se pide la pérdida de señal,
   **Then** el informe las considera **todas**. ⚠️ El informe actual analiza **10 000 de 59 045**
   —el 16,9 %— y publica el resultado como completo.

---

### User Story 3 - El Director de Operaciones cierra el ciclo: evidencia y desenlace (Priority: P2)

Los diez informes de **OT24 y OT25**: qué evidencia se levantó, cuánto tardó en sincronizarse, cómo
se cerraron los casos y cuáles llevan demasiado tiempo abiertos.

**Why this priority**: cierra el ciclo del caso, pero **la mitad exige ampliar el modelo** y varios
se apoyan en fuentes que hoy están prácticamente vacías (ver *Riesgos*). Entregar US1 y US2 antes da
valor sin quedar bloqueado por eso.

**Independent Test**: tomar un caso cerrado con evidencia y otro sin ella y comprobar que la
cobertura de evidencia los distingue.

**Los diez informes**:

| # | Informe | OT | ¿El modelo lo sostiene hoy? |
|--:|---|---|---|
| 17 | Cobertura de evidencia por severidad y región | OT24 | 🟡 falta el recuento de notas |
| 18 | Latencia de sincronización offline | OT24 | ❌ exige un hecho de evidencia |
| 19 | Completitud del enriquecimiento (clima, conductores, implicados) | OT24 | ❌ exige métricas nuevas |
| 20 | Volumen de evidencia **por unidad** | OT24 | 🟡 falta el hecho de evidencia |
| 21 | Escaladas de severidad originadas en sitio | OT24 | ❌ exige un hecho de severidad |
| 22 | Tiempo de asignado a cerrado | OT25 | ✅ |
| 23 | Cierres forzados | OT25 | ✅ |
| 24 | Distribución de resultados y calificación media | OT25 | ❌ exige métricas de cierre |
| 25 | Envejecimiento de la cartera de casos abiertos | OT25 | ✅ |
| 26 | Retiros forzados frente a finalizaciones normales, por proveedor | OT25 | ✅ |

**Acceptance Scenarios**:

1. **Given** un caso cerrado sin ninguna evidencia, **When** se pide la cobertura de evidencia,
   **Then** ese caso cuenta como sin cobertura, y el porcentaje refleja el hueco en vez de omitirlo.
2. **Given** un caso abierto desde hace 40 días, **When** se pide el envejecimiento de la cartera,
   **Then** aparece en el tramo correspondiente. **Un caso abierto no tiene fecha de cierre**, y el
   informe debe tratarlo como abierto, nunca como cerrado el día de la carga.
3. **Given** un caso cerrado y otro descartado, **When** se pide la distribución de resultados,
   **Then** se distinguen: descartar no es cerrar.

---

### Edge Cases

- **Un período sin ningún caso.** El informe devuelve un resultado vacío **explícito**, no un error
  ni una fila de ceros que se confunda con «hubo casos y todos dieron cero».
- **Una división por cero.** Cobertura, ratios y porcentajes sobre un denominador de cero se
  presentan como **sin dato**, no como `0` — que significaría «medido y salió cero».
- **Una unidad sin versión anterior a la primera carga del modelo.** Sus hechos anteriores apuntan a
  la versión «desconocida»; el informe la muestra como tal en vez de atribuirla al proveedor actual.
- **Un caso cuya calle no está en el catálogo.** Aparece bajo «Desconocido». **No desaparece del
  informe**: perder un accidente porque falta una fila en un catálogo de calles es inaceptable.
- **Un hito no alcanzado.** Los promedios de duración **excluyen** los casos que no llegaron a ese
  hito, en vez de contarlos como duración cero.
- **Dos consultas que miden lo mismo por caminos distintos.** Deben coincidir; si no, el informe
  miente por uno de los dos lados.
- **Un período recargado mientras alguien consulta.** El informe puede ver el período a medias
  durante la recarga; se acepta para carga analítica programada y se documenta.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Cómo se resuelve un informe

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos propios.
- **FR-002**: Si un informe necesita un dato que el modelo no tiene, DEBE **ampliarse el modelo**
  siguiendo su procedimiento de crecimiento, y el informe seguir siendo una consulta. **Está
  prohibido crear una tabla por informe.**
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo. Su única fuente es el modelo.
- **FR-004**: Toda consulta sobre un hecho de instantánea acumulada o sobre una dimensión DEBE forzar
  la versión final. Omitirlo produce **cifras infladas de forma intermitente**.

#### Corrección de las cifras

- **FR-005**: La completitud de campos críticos DEBE contar como incompleto un caso al que le falte
  severidad o ubicación. **Hoy no puede: su condición es siempre cierta.**
- **FR-006**: El ratio demanda/capacidad DEBE usar la capacidad **vigente en el período consultado**,
  no la flota actual.
- **FR-007**: Todo informe que agrupe por proveedor DEBE usar el proveedor **vigente cuando ocurrió
  el hecho**.
- **FR-008**: Los informes sobre posiciones reportadas DEBEN considerar **todas** las del período.
  Ninguna consulta puede truncar en silencio.
- **FR-009**: Los desenlaces de un despacho DEBEN distinguirse entre sí: confirmado, rechazado,
  vencido, abortado y en curso son cinco cosas distintas.
- **FR-010**: Descartado, fusionado y cerrado DEBEN distinguirse. El sistema operativo los marca los
  tres igual, y confundirlos falsea a la vez el volumen y la calidad.

#### Grano y agregación

- **FR-011**: Los informes de despacho DEBEN medirse con **grano de intento**, no de caso.
- **FR-012**: Los informes de duración DEBEN calcularse como diferencia entre hitos, **excluyendo**
  los casos que no alcanzaron el hito final.
- **FR-013**: Todo informe DEBE aceptar un **rango de fechas** y devolver únicamente ese período.
- **FR-014**: Todo informe agregado DEBE poder desglosarse por al menos una dimensión de su OT
  (severidad, zona, unidad, proveedor u origen), según su definición.

#### Presentación y límites

- **FR-015**: Los informes DEBEN expresar la ubicación **por nombre**. Ninguna respuesta incluye
  coordenadas.
- **FR-016**: Ninguna respuesta DEBE incluir identidad de personas, secretos de autenticación, medios
  de cobro ni texto libre interno. Es una exclusión **constitucional**: no la levanta ninguna
  autoridad departamental.
- **FR-017**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-018**: Una entidad que el modelo no pudo resolver DEBE aparecer etiquetada como
  **desconocida**, y el hecho DEBE seguir contando en los totales.
- **FR-019**: Un período sin datos DEBE devolver un resultado vacío explícito, distinguible de un
  período con datos que suman cero.

#### Acceso

- **FR-020**: Los informes DEBEN ser de **solo lectura**.
- **FR-021**: El **Director de Operaciones** —autoridad de Emergencias según el §5.1 del SRS— DEBE
  acceder a todos los informes del departamento **sin acotamiento por titularidad**.
- **FR-022**: La exención de la autoridad **NO DEBE alcanzar al dato sensible**: las exclusiones de
  FR-015 y FR-016 rigen para todos los roles, sea cual sea el cargo.
- **FR-023**: Un solicitante sin autoridad ni papel operativo en Emergencias NO DEBE obtener datos
  del departamento.

#### Ampliaciones del modelo que estos informes requieren

- **FR-024**: Para la cobertura de evidencia, el modelo DEBE poder contar **notas** además de fotos.
- **FR-025**: Para la latencia de sincronización, el modelo DEBE conservar **cuándo se capturó y
  cuándo se sincronizó** cada evidencia.
- **FR-026**: Para la completitud del enriquecimiento, el modelo DEBE contar los elementos asociados
  a cada caso: clima, conductores e implicados.
- **FR-027**: Para las escaladas de severidad, el modelo DEBE conservar los cambios de severidad con
  su instante, su origen y su severidad anterior y nueva.
- **FR-028**: Para la distribución de desenlaces, el modelo DEBE conservar el **resultado de atención
  y la calificación** de cada caso cerrado. La observación final **no se copia**: es texto libre.

#### La estimación de llegada, que no existe en el origen *(decisión 2026-08-14)*

El sistema operativo **no guarda ninguna estimación de llegada**: no hay columna de ETA ni parámetro
del que derivarla. Se decidió construir una **referencia derivada del histórico** en vez de dejar el
informe fuera de alcance.

- **FR-029**: La llegada esperada de un despacho DEBE derivarse del **comportamiento histórico de
  despachos comparables** —mismo condado y misma severidad—, usando la **mediana** de sus tiempos de
  llegada. La mediana y no el promedio: un solo traslado extremo desplazaría el promedio y volvería
  «normal» lo que no lo es.
- **FR-030**: La referencia DEBE calcularse sobre una **ventana anterior al despacho medido**, nunca
  incluyéndolo. Un despacho no puede formar parte de su propia expectativa: eso haría que cualquier
  desempeño pareciera normal.
- **FR-031**: Si no hay **suficientes despachos comparables** para una referencia fiable, la
  desviación DEBE presentarse como **sin dato**, nunca como cero. Cero significaría «llegó justo a
  tiempo», que es lo contrario de «no sabemos qué esperar».
- **FR-032**: El informe DEBE presentar la expectativa **etiquetada como valor de referencia
  derivado del histórico**, y NO DEBE presentarla como un compromiso operativo, un objetivo ni un
  SLA. Nadie se comprometió a ese tiempo: es lo que suele tardarse.
- **FR-033**: Los despachos que **nunca llegaron** DEBEN quedar fuera del cálculo de la referencia.
  Incluirlos como duración cero o infinita corrompería la mediana en ambos sentidos.

#### El desglose por persona queda excluido *(decisión 2026-08-14)*

- **FR-034**: El volumen de evidencia DEBE desglosarse **por unidad**, y NO por técnico de campo. El
  desglose por persona es identidad, y FR-016 no admite excepciones ni para la autoridad
  departamental. El informe responde «qué unidades documentan bien», no «qué personas».

### Key Entities

- **Caso**: un accidente registrado, con su gravedad, su ubicación por nombre, sus hitos de proceso y
  su impacto humano. Grano de la mayoría de los informes de OT21, OT24 y OT25.
- **Intento de despacho**: una asignación a una unidad, con su desenlace, su ordinal dentro del caso
  y el proveedor de la unidad **en ese momento**. Grano de OT22 y OT23.
- **Versión de unidad**: la unidad tal como era en un instante, incluido su proveedor y su condado.
  Es lo que permite que un informe histórico no se reescriba.
- **Posición reportada**: un instante en que una unidad comunicó estar operativa, **sin coordenadas**.
  Sostiene la continuidad de señal.
- **Cambio de estado de unidad**: una transición de disponibilidad, con su duración en el estado
  anterior.
- **Período**: el rango de fechas que acota todo informe.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los **26 informes** del catálogo se obtienen sin que exista ninguna tabla dedicada a un
  informe concreto.
- **SC-002**: La completitud de campos críticos deja de ser constante: ante un caso al que le falta
  severidad o ubicación, el resultado **baja del 100 %**.
- **SC-003**: El **100 %** de los intentos de despacho anteriores a un cambio de proveedor conserva
  su atribución original tras recargar.
- **SC-004**: La pérdida de señal considera el **100 %** de las posiciones del período; hoy considera
  el 16,9 %.
- **SC-005**: Dos formas distintas de medir un mismo informe —por columna copiada y cruzando con la
  dimensión— devuelven **cifras idénticas**.
- **SC-006**: Ningún informe devuelve coordenadas, identidad de personas ni texto libre interno,
  **para ningún rol**.
- **SC-007**: La suma de las categorías de todo informe de distribución es **igual al total** del
  período: ningún caso se pierde por no poder clasificarse.
- **SC-008**: Un informe recién añadido al catálogo no requiere **ninguna** tabla ni flujo nuevos si
  el modelo ya tiene sus hechos y dimensiones.
- **SC-009**: Los informes responden en tiempo aceptable con **al menos tres meses** de datos
  cargados.
- **SC-010**: Añadir los informes de este módulo **no altera** ninguna cifra de los informes ya
  existentes.
- **SC-011**: La desviación de llegada nunca sale `0` por ausencia de referencia: los despachos sin
  histórico comparable suficiente aparecen como **sin dato**.
- **SC-012**: Ningún informe del módulo permite desglosar por persona.

---

## Assumptions

- **El modelo analítico está cargado y sus flujos corriendo.** Es prerrequisito duro: sin él no hay
  sustrato. Verificado el 2026-08-14.
- **El período por defecto** de un informe sin rango explícito son los **últimos 30 días**, coherente
  con los listados del contrato común.
- **La agregación temporal por defecto es diaria**, y los informes que declaren evolución permiten
  además agrupación mensual.
- **Los informes se sirven al Director de Operaciones y a los responsables operativos** de
  Emergencias, según la clasificación ya decidida en `acceso-tactico.md`.
- **La ubicación se expresa por condado y ciudad.** Es el nivel al que se toman las decisiones
  tácticas, y evita las coordenadas.
- **El frontend queda fuera de alcance**, como en todos los módulos tácticos: dónde vive cada informe
  en los tableros se decide después.
- **Los tres informes ya construidos** —pérdida de señal, índice de calidad y rendimiento por
  proveedor— siguen sirviéndose desde sus tablas propias hasta que se decida qué pasa con sus
  endpoints (decisión pendiente #20). Este módulo los redefine sobre el modelo; no los apaga.

---

## Riesgos ⚠️

### Cinco fuentes de OT24 y OT25 están vacías o casi

Medido el 2026-08-14 contra el sistema operativo, con **4 252 casos registrados**:

| Fuente | Filas | Informes que la necesitan |
|---|--:|---|
| `Fact_Conductor_Accidente` | **0** | Completitud del enriquecimiento (#19) |
| `Dim_ParametrosDespacho` | **0** | Umbrales de asignación |
| `Dim_ParametrosSeguimiento` | **0** | Umbral de pérdida de señal (#14) |
| `Fact_HistorialSeveridadAccidente` | **1** | Escaladas de severidad (#21) |
| `Fact_CierreAccidente` | **1** | Distribución de resultados y calificación (#24) |
| `Dim_EvidenciaFoto` | **3** | Cobertura de evidencia (#17), latencia (#18) |
| `Dim_ElementoClimaticosAccidente`, `Dim_Implicado` | **3** | Completitud del enriquecimiento (#19) |
| `Dim_NotaAccidente` | **51** | Cobertura de evidencia (#17) |

**Es el sexto caso en este proyecto del mismo patrón**: el esquema declara algo que la operación
casi nunca rellena. Los informes son especificables y construibles, pero **reportarán cerca de cero**,
y hay que saber si eso es la verdad del negocio o un hueco del sistema operativo antes de publicar
esas cifras como indicadores.

**Consecuencia concreta ya observada:** `Dim_ParametrosSeguimiento` vacía es la razón de que el
umbral de pérdida de señal caiga siempre a su valor por defecto de 60 segundos. El parámetro es
configurable sobre el papel y en la práctica nadie lo ha configurado nunca.

**No bloquea esta spec.** Se registra para que quien construya US3 no interprete un 0 % de cobertura
como un defecto de su consulta.

### Dos informes ya construidos difieren de lo que dará el modelo

Verificado: la pérdida de señal pasará de 714 huecos a 3 942, y los rechazos por proveedor de 344 a
661. **No es un error de migración**: los informes actuales truncan en silencio. Quien compare sin
contexto lo tomará por una regresión.

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato. Prerrequisito duro.
- **[`contrato-consumo.md`](../../../modelo-analitico/contracts/contrato-consumo.md)** — las 8 reglas
  de consulta.
- **[`esquema-analitico.md`](../../../modelo-analitico/contracts/esquema-analitico.md)** — el esquema
  y el §4.bis, procedimiento para las ampliaciones de FR-024 a FR-028.
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — quién ve qué.
- **[`informes-tacticos-simples/`](../../informes-tacticos-simples/)** — módulo hermano; los 12
  listados llanos del mismo departamento. **Sin dependencia entre ambos.**
