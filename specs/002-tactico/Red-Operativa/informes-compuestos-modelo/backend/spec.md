# Feature Specification: Informes Compuestos de Red Operativa sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Red-Operativa/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Informes tácticos compuestos de Red Operativa — los 15 informes agregados de OT11 a OT13, resueltos con consultas sobre el modelo analítico"

---

## Contexto

Segundo departamento sobre el modelo analítico, después de Emergencias. Red Operativa responde a
**quién puede atender, dónde y con qué flota**: valida regiones, mantiene las unidades y retira las
regiones que se quedan sin cobertura.

**Punto de partida distinto al de Emergencias:** allí 16 de 26 informes ya existían; **aquí no existe
ninguno**. La app que sirve informes tácticos solo tiene endpoints de Emergencias. Los 15 son
construcción nueva.

**Y buena parte del sustrato ya está.** `dim_unidad` versionada y `hecho_estado_unidad` se
construyeron con el modelo, y son exactamente lo que ocho de estos informes necesitan.

> ### ⚠️ Dos defectos del sistema operativo, medidos antes de especificar
>
> **1. Un estado de unidad que no está en su catálogo.** `Fact_HistorialEstadoUnidad` usa
> `idestadounidademergencia = 4` («En Misión») **seis veces**, y `Dim_EstadoUnidadEmergencia` solo
> define 1, 2 y 3. Un informe que agrupe uniendo con el catálogo **perdería el 13 % de las
> transiciones** o las dejaría sin etiqueta, sin que nada fallara.
>
> **2. No existe historial del ciclo de vida de una región.** El catálogo de informes apoya tres de
> ellos en `Dim_RegionOperativaEstadoRegion`, suponiendo que registra cuándo una región cambió de
> estado. **No es eso**: su `idestadoregion = 1` apunta a `'Ciudad de Mexico'`, es decir, relaciona la
> región con su **estado geográfico**. El ciclo de vida —Definida, En validación, Producción,
> Despublicada— vive en una sola columna de `Dim_RegionOperativa`, **sin fecha y sin historia**.
>
> Es el mismo patrón que ya obligó a versionar la unidad: el sistema guarda **el estado actual** y
> nunca cuándo cambió. Afecta al alcance de dos informes; ver *Aclaración pendiente*.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Expansión ve el estado real de la flota (Priority: P1) 🎯 MVP

Los ocho informes de **OT12**: qué unidades hay, de qué proveedor, en qué condado, cuánto tiempo
estuvieron realmente disponibles y dónde falta cobertura.

**Why this priority**: es el bloque más grande y **el sustrato ya está construido** —`dim_unidad`
versionada y `hecho_estado_unidad`—, así que entrega valor sin trabajo previo de infraestructura.
Además contiene el indicador de disponibilidad, que hoy no se puede calcular de ninguna forma.

**Independent Test**: pedir la cobertura de flota de un condado y comprobar que la suma de sus
estados es igual al número de unidades de ese condado en ese período.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 1 | Unidades por estado operativo | OT12 | **CU-T08** |
| 2 | Unidades de lote pendientes de primer acceso | OT12 | ± |
| 3 | Rendimiento por proveedor | OT12 | ± |
| 4 | **Cobertura de flota por región**: activas, disponibles y en misión | OT12 | **CU-T08** |
| 5 | **Disponibilidad declarada**: % del tiempo que cada unidad estuvo Activa | OT12 | OP43 |
| 6 | **Condados en cobertura crítica**, con vecinos disponibles | OT12 | **CU-T08** |
| 7 | Rotación de flota: altas frente a bajas por proveedor | OT12 | ± |
| 8 | Bajas forzadas con caso en curso, por proveedor | OT12 | SRS |

**Acceptance Scenarios**:

1. **Given** una unidad que pasó por «En Misión», **When** se piden las unidades por estado,
   **Then** ese estado **aparece**. ⚠️ No está en el catálogo del sistema operativo: si el informe
   uniera con él, esas seis transiciones desaparecerían.
2. **Given** una unidad activa el 60 % del período, **When** se pide la disponibilidad declarada,
   **Then** devuelve 60 %, calculado sobre **el tiempo en cada estado**, no sobre el número de
   cambios.
3. **Given** una unidad que cambió de proveedor, **When** se pide el rendimiento por proveedor de un
   período anterior, **Then** su trabajo sigue atribuido al proveedor de entonces.
4. **Given** un condado sin unidades disponibles y un vecino con ellas, **When** se piden los
   condados en cobertura crítica, **Then** aparece con sus vecinos y su capacidad.
5. **Given** una unidad dada de baja de forma forzada con un caso en curso, **When** se piden las
   bajas forzadas, **Then** aparece distinguida de una baja normal.

---

### User Story 2 - El Director de Expansión mide cómo se abren regiones (Priority: P2)

Los cuatro informes de **OT11**: cuánto se tarda en poner una región en operación, cuántos mercados
hay activos, cuántas validaciones se aprueban a la primera y por qué se rechazan.

**Why this priority**: contiene **dos indicadores BSC**, uno de ellos normativo (≤30 días), pero
opera sobre volúmenes pequeños —2 regiones y 3 validaciones— así que su valor analítico crece con el
negocio, no hoy.

**Independent Test**: pedir la tasa de aprobación al primer intento y comprobar que una región
rechazada dos veces y aprobada a la tercera **no** cuenta como aprobada al primer intento.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 9 | **Tiempo de puesta en operación regional** — `[NORMATIVO]` ≤30 días | OT11 | **BSC** |
| 10 | **Mercados activos**: regiones con ≥1 cliente activo | OT11 | **BSC** |
| 11 | Tasa de aprobación al primer intento, por región | OT11 | ± |
| 12 | **Motivos de rechazo más frecuentes** | OT11 | **CU-T07** |

**Acceptance Scenarios**:

1. **Given** una región con dos validaciones rechazadas y una aprobada, **When** se pide la tasa de
   aprobación al primer intento, **Then** cuenta como **no** aprobada al primero, y sus tres intentos
   son visibles.
2. **Given** una validación aprobada sin motivo registrado, **When** se piden los motivos de rechazo,
   **Then** no aparece: solo se agrupan los rechazos, y un motivo ausente no se cuenta como una
   categoría vacía.
3. **Given** una región que aún no ha llegado a producción, **When** se pide el tiempo de puesta en
   operación, **Then** **no** cuenta como «0 días» ni como incumplimiento: queda fuera de la medida y
   se cuenta aparte.

---

### User Story 3 - El Director de Expansión vigila las regiones en riesgo (Priority: P3)

Los tres informes de **OT13**: qué regiones publicadas están por debajo del umbral de cobertura, y
qué pasa cuando se despublica una.

**Why this priority**: **dos de los tres dependen de un dato que no existe** —la fecha de
despublicación— y su alcance depende de la aclaración pendiente. El tercero sí es construible y es el
que previene el problema en vez de analizarlo después.

**Independent Test**: dejar un condado sin unidades disponibles y comprobar que su región aparece en
riesgo.

| # | Informe | OT | Construible hoy |
|--:|---|---|---|
| 13 | **Regiones en riesgo**: publicadas con cobertura bajo umbral | OT13 | ✅ |
| 14 | Casos activos al despublicar, por región | OT13 | ⚠️ desde la primera carga (FR-032) |
| 15 | Tiempo entre pérdida de cobertura y despublicación efectiva | OT13 | ⚠️ desde la primera carga (FR-032) |

**Acceptance Scenarios**:

1. **Given** una región en producción cuyos condados no tienen unidades disponibles, **When** se
   piden las regiones en riesgo, **Then** aparece con su cobertura actual y el umbral incumplido.
2. **Given** una región con cobertura suficiente, **When** se pide el mismo informe, **Then** no
   aparece.

---

### Edge Cases

- **Una unidad sin ninguna transición de estado.** Su disponibilidad es **ausente**, no 0 %: no se
  sabe en qué estado estuvo, que es distinto de saber que estuvo inactiva.
- **Un estado que el catálogo no define.** Se muestra con su nombre tal como lo registró la
  operación. **Nunca se descarta.**
- **Un condado sin vecinos declarados.** Aparece en cobertura crítica **sin alternativas**, que es
  precisamente la situación más grave, no un caso a omitir.
- **Una región sin validaciones.** No aparece en la tasa de aprobación; no cuenta como 0 %.
- **Una unidad dada de baja a mitad del período.** Cuenta en la flota **hasta su baja**, no el
  período entero ni cero.
- **Un período anterior a la primera carga del modelo.** Las versiones de unidad lo cubren
  declarando que su inicio no es real.

---

## Requirements *(mandatory)*

### Funcionamiento general

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos por informe.
- **FR-002**: Si falta un dato, DEBE ampliarse el modelo según su procedimiento de crecimiento.
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo.
- **FR-004**: Toda consulta sobre un hecho de instantánea acumulada o una dimensión DEBE forzar la
  versión final.
- **FR-005**: Todo informe DEBE aceptar un rango de fechas y devolver solo ese período.

### Estados y disponibilidad

- **FR-006**: Los informes de estado de unidad DEBEN usar **el estado tal como lo registró la
  operación**, y NO DEBEN depender del catálogo de estados para decidir qué filas incluir. ⚠️ El
  catálogo está incompleto: le falta el estado usado en 6 de 45 transiciones.
- **FR-007**: La disponibilidad declarada DEBE calcularse sobre **el tiempo permanecido en cada
  estado**, no sobre el número de cambios. Una unidad que cambió mucho no es menos disponible.
- **FR-008**: Una unidad **sin ninguna transición** en el período DEBE aparecer con disponibilidad
  **ausente**, nunca 0 %.
- **FR-009**: El tiempo en el estado vigente al final del período DEBE contarse **hasta el fin del
  período**, no hasta el último cambio. Ignorarlo subestimaría toda disponibilidad.

### Flota y cobertura

- **FR-010**: La flota de un período DEBEN ser las **versiones de unidad vigentes entonces**, no las
  unidades activas hoy.
- **FR-011**: Todo informe que agrupe por proveedor DEBE usar el proveedor **vigente cuando ocurrió
  el hecho**.
- **FR-012**: Una unidad dada de baja durante el período DEBE contar **hasta su baja**.
- **FR-013**: Los condados en cobertura crítica DEBEN incluir sus **vecinos declarados** y la
  capacidad de estos.
- **FR-014**: Un condado **sin vecinos declarados** DEBE aparecer igualmente, señalado como sin
  alternativas.
- **FR-015**: Las bajas DEBEN distinguir **normal, forzada y forzada con reasignación**, y señalar
  las que ocurrieron con un caso en curso.

### Regiones

- **FR-016**: El tiempo de puesta en operación DEBE medirse solo sobre las regiones que **llegaron a
  producción**. Las que no llegaron se cuentan aparte y **no** como cero días ni como incumplimiento.
- **FR-017**: La tasa de aprobación al primer intento DEBE contar los **intentos de validación**, no
  las regiones: una región rechazada dos veces y aprobada a la tercera no aprobó al primer intento.
- **FR-018**: Los motivos de rechazo DEBEN agruparse **solo sobre validaciones rechazadas**. Un
  motivo ausente no es una categoría.
- **FR-019**: Las regiones en riesgo DEBEN compararse contra un **umbral de cobertura parametrizable**.

### Presentación y límites

- **FR-020**: La ubicación DEBE expresarse por nombre. Ninguna respuesta incluye coordenadas.
- **FR-021**: Ninguna respuesta DEBE incluir identidad de personas. ⚠️ Alcanza al **validador de una
  región**, que el catálogo pedía como desglose: es la misma decisión ya tomada en Emergencias con el
  técnico de campo.
- **FR-022**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-023**: Un período sin datos DEBE devolver un resultado vacío explícito.

### Acceso

- **FR-024**: Los informes DEBEN ser de solo lectura.
- **FR-025**: El **Director de Expansión** —autoridad de crecimiento de Red Operativa— y el
  **Director Tecnológico** —autoridad de validación de región— DEBEN acceder sin acotamiento por
  titularidad, cada uno a su materia. ⚠️ En este departamento la autoridad **está repartida**, según
  el §5.1 del SRS.
- **FR-026**: La exención NO DEBE alcanzar al dato sensible.

### Ampliaciones del modelo

- **FR-027**: El modelo DEBE incorporar una **dimensión de región operativa versionada**: una fila
  por versión, con su estado de ciclo de vida, su geografía y sus condados.
- **FR-028**: El modelo DEBE incorporar un **hecho de baja de unidad** con su tipo, su motivo y si
  hubo un caso en curso.
- **FR-029**: El modelo DEBE incorporar un **hecho de validación de región** con su resultado, su
  motivo y su número de intento.
- **FR-030**: El modelo DEBE incorporar la **vecindad entre condados** como atributo consultable.
- **FR-031**: El modelo DEBE conservar el **alta de cada unidad** para poder medir rotación.

#### El ciclo de vida de la región, que el origen no historiza *(decisión 2026-08-14)*

El sistema operativo guarda el estado actual de cada región y **nunca cuándo cambió**. Se decidió
**versionar la región en el modelo**, con el mismo mecanismo ya construido y probado para la unidad.

- **FR-032**: Un cambio de estado de región DEBE abrir una **versión nueva**, cerrando la anterior,
  de modo que un informe histórico atribuya cada caso al estado vigente entonces.
- **FR-033**: La primera versión de cada región DEBE declarar que **su fecha de inicio no es real**:
  abre por la izquierda y cubre todo el pasado, porque el estado se conoce pero no desde cuándo.
  Presentarla como una fecha observada sería afirmar algo que nadie registró.
- **FR-034**: Los informes #14 y #15 DEBEN indicar **desde qué fecha su medida es exacta**. Antes de
  la primera carga del modelo no hay despublicaciones que detectar — no porque no ocurrieran, sino
  porque no se guardaron.
- **FR-035**: Una región que **nunca se despublicó** NO DEBE contarse como despublicada con tiempo
  cero. Queda fuera de la medida.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los 15 informes se obtienen sin que exista ninguna tabla dedicada a un informe.
- **SC-002**: El estado «En Misión» **aparece** en los informes de estado, pese a no estar en el
  catálogo del sistema operativo.
- **SC-003**: La disponibilidad declarada de una unidad activa todo el período es **100 %**, y la de
  una unidad sin transiciones es **ausente**, no 0 %.
- **SC-004**: El 100 % de las unidades conserva su atribución de proveedor tras un cambio.
- **SC-005**: La suma de los estados de un condado iguala su número de unidades en el período.
- **SC-006**: Ningún informe devuelve coordenadas ni identidad de personas, **para ningún rol**.
- **SC-007**: Una región que nunca llegó a producción **no aparece** como incumplimiento del
  indicador normativo de 30 días.
- **SC-008**: Un condado sin vecinos declarados aparece en cobertura crítica, señalado.
- **SC-009**: Añadir estos informes **no altera** ninguna cifra de los informes de Emergencias.
- **SC-010**: Tras despublicar una región, un informe de un período **anterior** sigue mostrándola
  como publicada: el cambio no reescribe el pasado.
- **SC-011**: Las versiones iniciales de región declaran **todas** que su inicio no es real, y los
  informes #14 y #15 muestran desde qué fecha su medida es exacta.

---

## Assumptions

- **El modelo analítico está cargado.** `dim_unidad` y `hecho_estado_unidad` ya existen y sostienen
  ocho de los quince informes.
- **El período por defecto** son los últimos 30 días.
- **El umbral de cobertura crítica** por defecto es **1 unidad disponible por condado**, y es
  parametrizable. El sistema operativo no lo define: `Dim_ParametrosDespacho` tiene **0 filas**.
- **El frontend queda fuera de alcance.**
- **El rendimiento por proveedor** ya está resuelto sobre el modelo por el módulo del modelo
  analítico; aquí se expone, no se recalcula de otra forma.

---

## Riesgos ⚠️

### El departamento entero opera sobre volúmenes muy pequeños

Medido el 2026-08-14: **2 regiones**, 3 validaciones, 2 relaciones de vecindad, **2 bajas de unidad**,
18 unidades y 45 transiciones de estado.

A diferencia de Emergencias —donde cinco fuentes estaban **vacías**—, aquí los flujos operativos **sí
escriben**: hay validaciones con motivo, bajas con tipo y transiciones reales. El problema no es que
falte el dato, es que **hay poco**.

**Consecuencia práctica:** varios informes serán estadísticamente irrelevantes hoy —una tasa de
aprobación sobre 3 intentos, unos motivos de rechazo sobre 2 rechazos— y ganarán sentido conforme
crezca la operación. **Son correctos; simplemente aún no dicen mucho.**

### El catálogo de informes se apoya en una tabla que no contiene lo que parece

`Dim_RegionOperativaEstadoRegion` relaciona región con **estado geográfico**, no con estado de ciclo
de vida. Tres informes del catálogo —uno simple y dos compuestos— la citan como fuente del historial
de despublicación, que **no existe en ninguna parte**.

Es el séptimo caso en este proyecto del mismo patrón. Queda anotado también en el catálogo global.

---

## Aclaración, resuelta el 2026-08-14

**Informes #14 y #15 → se construyen versionando la región** (FR-032 a FR-035).

El sistema operativo guarda el estado actual y nunca cuándo cambió, así que el modelo lo historiza
**desde su primera carga**, con el mismo mecanismo probado para la unidad y su proveedor.

**Lo que esto entrega y lo que no.** Desde hoy, cada despublicación queda fechada y ambos informes
son exactos. **El pasado no se reconstruye**: no hay despublicaciones anteriores que mostrar, no
porque no ocurrieran sino porque nadie las guardó. Los informes lo declaran (FR-034) en vez de
presentar un histórico vacío como si significara «nunca pasó».

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato.
- **[`Emergencias/informes-compuestos-modelo/`](../../Emergencias/informes-compuestos-modelo/)** —
  módulo hermano; comparte `dim_unidad`, `hecho_estado_unidad` y el catálogo de consultas. **Sin
  dependencia de orden entre ambos.**
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — la autoridad repartida de este departamento.
