# Feature Specification: OE6 — Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Feature Branch**: `001-estrategico/OE6-respuesta-y-vidas/backend`

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Informes estratégicos del OE6 — los doce informes que miden el tiempo entre el reporte de una emergencia y la atención efectiva en sitio, y el resultado sobre la persona atendida, resueltos con consultas sobre el modelo analítico y comparados contra la meta del tablero BSC."

---

## Contexto: qué cambia respecto de la capa táctica

Este es el **primer módulo de la capa estratégica**, y su trabajo es tanto entregar doce informes como
fijar la forma que copiarán los otros cinco OE.

El objetivo estratégico dice: *reducir el tiempo entre el reporte de una emergencia vial y la atención
efectiva en sitio, minimizando el impacto en el tráfico y maximizando la probabilidad de salvaguardar
vidas.* Es el único OE cuya perspectiva BSC incluye **Safety**, y por tanto el único donde el
Principio IX de la constitución —seguridad física por encima de todo— gobierna directamente el diseño
del informe, no solo el de la operación.

> ## ⚠️ Corrección de alcance: la mayor parte del cálculo ya existe
>
> Detectado al especificar, verificándolo contra el código y no contra el catálogo. El módulo táctico
> `Emergencias/informes-compuestos-modelo` construyó **26 consultas sobre el mismo modelo analítico**
> (`dags/lib/consultas/emergencias/`, OT21–OT25), y cubren la materia de **once de los doce**
> informes de OE6.
>
> **El alcance real de este módulo no es calcular de nuevo, es cuatro cosas que la capa táctica no
> hace y no debe hacer.** Están en la §«Qué es nuevo» de abajo.
>
> Escribir doce consultas nuevas desde cero produciría **dos definiciones de la misma métrica** —una
> táctica y una estratégica— que divergirían a la primera corrección. Es exactamente el problema que
> el modelo analítico existe para evitar, un nivel más arriba.

### Discrepancias del catálogo, detectadas al especificar

El catálogo `TSI-Informes-Compuestos-Requeridos-por-OE.md` §6 nombra fuentes que **no coinciden con el
modelo real**. Esta spec va con el modelo, que es la fuente, y el catálogo queda por corregir:

| Informe | Lo que dice el catálogo | Lo que hay |
|---|---|---|
| **E6-01** | `hecho_accidente` × `hecho_despacho` — «JOIN por `idaccidente`» | **No hace falta unir**: `hecho_accidente.hora_primera_llegada` ya está desnormalizada. Es una resta dentro de la misma fila |
| **E6-03** | `hecho_accidente_tipo_estado` | Ese hecho **no existe**. Los cuatro hitos viven en `hecho_accidente` (`hora_confirmacion`, `hora_primera_asignacion`, `hora_primera_llegada`, `hora_cierre`) |
| **E6-06** · **E6-07** | `hecho_ubicacion_unidad` | Se llama `hecho_ping_unidad` |
| **E6-07** | `hecho_despacho.eta_estimado` | **No existe y no va a existir.** Ver la nota de abajo |
| **E6-11** | `hecho_historial_severidad_accidente` | Ese hecho **se decidió no crear**. Es la métrica `num_escaladas_severidad` + `severidad_inicial` de `hecho_accidente` |

> **E6-07 merece explicación aparte.** El catálogo lo plantea como «ETA estimado vs llegada real», pero
> **el sistema no calcula ETA** y calcularlo exigiría coordenadas, que están excluidas del modelo por
> decisión constitucional. La capa táctica ya resolvió la misma pregunta por otro camino: una
> **referencia derivada del histórico** —la mediana de llegadas del mismo condado y severidad en los
> 90 días anteriores— contra la que se mide la desviación. Este módulo adopta esa definición. **No es
> una versión degradada del informe pedido: es la única versión honesta**, porque compara el
> desempeño real contra el desempeño habitual en condiciones comparables, en vez de contra una
> estimación que nadie hizo.

---

## Qué es nuevo, y por qué la capa táctica no puede darlo

Las cuatro diferencias. Ninguna es cosmética: cada una responde a algo que un informe táctico no
puede afirmar.

### 1. El percentil, no el promedio

Los informes tácticos entregan promedios. **La meta del BSC de este OE es una mediana**, y los KPI
`[NORMATIVO]` compartidos con OE3 son **p95**.

No es intercambiable. En tiempos de respuesta la distribución tiene cola larga: un puñado de casos muy
lentos arrastra el promedio hacia arriba y hace parecer mala una operación mayoritariamente buena; y
al revés, un promedio aceptable puede esconder que **uno de cada veinte accidentes espera el triple**.
En un sistema que despacha ambulancias, ese uno de cada veinte es la cifra que importa.

### 2. La ventana comparada

Ningún informe táctico compara períodos. Un tiempo de respuesta de 14 minutos no dice nada por sí
solo; **14 minutos frente a 11 el trimestre pasado** es una decisión de dirección.

Con la regla del contrato §3.1: ventanas de igual longitud, las dos declaradas en la respuesta, y el
período en curso marcado `parcial`.

### 3. El eje de región

La capa táctica agrupa por condado, proveedor y unidad —los ejes de quien supervisa una operación—.
La pregunta estratégica es **por región**, que es la unidad de decisión de expansión y la que permite
comparar mercados entre sí.

⚠️ **Esto es el único trabajo de modelo que el módulo necesita.** Ver §«Lo que falta en el modelo».

### 4. El contraste contra la meta

Un informe táctico entrega la cifra. Uno estratégico entrega **la cifra, la meta, y si la cumple** —
distinguiendo un compromiso `[NORMATIVO]` de una referencia `[CALIBRAR]`, según el §4 del contrato.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Operaciones sabe cuánto tarda en llegar la ayuda (Priority: P1) 🎯 MVP

Dos informes: **E6-01** y **E6-02**. Responden la pregunta que da nombre al objetivo estratégico —
*cuánto pasa desde que se reporta un accidente hasta que llega una unidad al sitio*— globalmente y
desglosada por gravedad.

**Why this priority**: es el KPI del BSC de este OE y **no hay ningún otro informe del que dependa**.
Además se calcula entero dentro de `hecho_accidente`, sin uniones y sin ampliar el modelo: es la
rebanada que demuestra la forma de la capa estratégica con el menor riesgo posible.

**Independent Test**: pedir el tiempo global de respuesta de un trimestre con comparación interanual y
comprobar que devuelve mediana, p95, las dos ventanas comparadas y el número de casos que sostienen
cada cifra — sin que se haya creado ninguna tabla.

| Informe | Ruta | Origen |
|---|---|---|
| **E6-01** Tiempo global de respuesta *(mediana y p95)* | `tiempo-respuesta-global` | **BSC** / **CU-E08** |
| **E6-02** Tiempo de respuesta por severidad | `tiempo-respuesta-por-severidad` | **BSC** / **CU-E08** |

**Acceptance Scenarios**:

1. **Given** un trimestre con casos que llegaron a tener unidad en sitio, **When** se pide el tiempo
   global de respuesta, **Then** devuelve mediana y p95 en minutos, y el recuento de casos que
   entraron en el cálculo.
2. **Given** ese mismo trimestre, **When** se pide con `comparacion=yoy`, **Then** la respuesta declara
   **las dos ventanas exactas** que comparó y la variación entre ellas.
3. **Given** un período con casos **abiertos o sin llegada registrada**, **When** se pide el informe,
   **Then** esos casos **quedan fuera del cálculo del tiempo** y su número se declara aparte. No
   cuentan como tiempo cero.
4. **Given** el período en curso, sin terminar, **When** se pide con comparación, **Then** la respuesta
   marca `parcial: true`.
5. **Given** un desglose por severidad, **When** hay casos cuya severidad no se resolvió, **Then**
   aparecen agrupados como «Desconocido» y **la suma de todas las severidades es igual al total** de
   casos con llegada del período.
6. **Given** cualquiera de los dos informes, **When** lo consulta el `DirectorOperaciones`, **Then**
   la respuesta **no contiene coordenadas ni identidad de implicados**.

---

### User Story 2 - Entender dónde se va ese tiempo (Priority: P2)

Tres informes: **E6-03**, **E6-04** y **E6-07**. US1 dice *cuánto se tarda*; esta dice *en qué tramo*,
*si influye cómo se asignó* y *si el retraso es anómalo o el habitual de esa zona*.

**Why this priority**: sin ella, el número de US1 es un termómetro sin diagnóstico. Un director que ve
subir la mediana y no puede decir si el retraso está en asignar, en salir o en circular, no puede
decidir nada. Va después porque **US1 tiene que existir primero para que haya algo que explicar**.

**Independent Test**: tomar un período con la mediana degradada respecto al anterior y comprobar que el
desglose por tramos localiza en cuál se produjo la diferencia, y que los tramos suman el tiempo total.

| Informe | Ruta | Origen |
|---|---|---|
| **E6-03** Desglose de tiempos por tramo del ciclo | `tramos-del-ciclo` | **CU-E08** / ± |
| **E6-04** Asignación automática vs manual y sus tiempos | `origen-de-asignacion` | **CU-E08** / ± |
| **E6-07** Desviación frente a la referencia histórica | `desviacion-de-llegada` | ± |

**Acceptance Scenarios**:

1. **Given** un período con casos cerrados, **When** se piden los tramos del ciclo, **Then** la suma
   de los tramos es igual al tiempo total de esos casos, sin residuo sin explicar.
2. **Given** casos que no alcanzaron un hito, **When** se calcula el tramo que lo usa, **Then** esos
   casos se excluyen **de ese tramo** y siguen contando en los tramos que sí completaron.
3. **Given** un período, **When** se compara la asignación automática con la manual, **Then** cada
   origen declara su recuento y su tiempo, y **los porcentajes suman 100 %** incluyendo el origen
   «escalado a zona».
4. **Given** un condado y severidad **sin muestra suficiente** en los 90 días previos, **When** se
   pide la desviación de llegada, **Then** la referencia viene **ausente** y la desviación también.
   No se devuelve cero ni se compara contra una mediana de dos casos.
5. **Given** la desviación de llegada, **When** se presenta, **Then** declara explícitamente que la
   referencia es **el histórico comparable**, no un ETA estimado.

---

### User Story 3 - Ver qué falla en la ejecución (Priority: P3)

Cuatro informes: **E6-05**, **E6-06**, **E6-09** y **E6-10**. Los modos de fallo: unidades que rechazan
o dejan vencer el ofrecimiento, misiones que se abortan, cierres empujados desde central y casos que
envejecen sin resolverse.

**Why this priority**: es la historia con **tres decisiones abiertas encima** —`decisiones-pendientes.md`
#34, #35 y #36—, y por eso está aislada aquí: si estuviera repartida entre US1 y US2, un bloqueo de
esquema pararía el MVP. Aislarla permite entregar US1 y US2 mientras se resuelven.

**Independent Test**: pedir los cuatro informes de un período y comprobar que cada tasa publica su
denominador, y que ninguno de los tres informes afectados por una decisión abierta se publica sin
declararlo.

| Informe | Ruta | Origen | Bloqueo |
|---|---|---|:--:|
| **E6-05** Tasa de rechazo y timeout por unidad | `rechazo-y-timeout-por-unidad` | **CU-E08** | ⚠️ #34 |
| **E6-06** Abortos y misiones fallidas | `abortos-y-misiones-fallidas` | **CU-E08** | — |
| **E6-09** Cierres forzados desde central | `cierres-forzados` | **CU-E08** | ⚠️ #36 |
| **E6-10** Envejecimiento de casos abiertos | `envejecimiento-de-casos-abiertos` | **CU-E08** / ± | — |

**Acceptance Scenarios**:

1. **Given** un período, **When** se pide la tasa de rechazo por unidad, **Then** el denominador son
   **intentos de despacho ofrecidos**, nunca transiciones de estado, y el informe lo declara.
2. **Given** una unidad que aceptó y completó todos sus despachos, **When** se calcula su tasa,
   **Then** su tasa **no baja por haber trabajado más**. *(Es el defecto #34: hoy el endpoint táctico
   premia a quien más trabaja, con un factor medido de 2,6.)*
3. **Given** cualquier tasa de este módulo, **When** se devuelve, **Then** **acompaña su denominador**.
   Un 12,5 % sobre 8 casos y sobre 8 000 son afirmaciones distintas.
4. **Given** los cierres forzados, **When** se publican, **Then** el informe declara **cuál de las dos
   definiciones mide** — el indicador del despacho o el retiro manual desde central. *(Difieren en un
   factor de 451; ver #36.)*
5. **Given** el envejecimiento de la cartera, **When** se pide, **Then** los casos abiertos se
   distribuyen por tramos de antigüedad y **ningún caso abierto aparece como cerrado**.
6. **Given** un período sin ningún aborto, **When** se pide el informe, **Then** devuelve resultado
   vacío con cobertura `completa`, no un cero que se confunda con «no medido».

---

### User Story 4 - Medir el resultado sobre la persona atendida (Priority: P4)

Tres informes: **E6-08**, **E6-11** y **E6-12**. Es lo que distingue OE6 de OE3: **OE3 mide el proceso
de infraestructura; OE6 mide el resultado sobre quien esperaba una ambulancia.**

**Why this priority**: es la parte más valiosa del objetivo y la que menos depende de las anteriores,
pero va última porque **dos de los tres se apoyan en datos que hoy están casi vacíos** y su valor real
llega cuando el histórico crezca. Entregarlos antes daría tableros en blanco que nadie sabría
interpretar.

**Independent Test**: pedir el impacto humano de un período y comprobar que las sumas de víctimas,
heridos y fallecidos cuadran con el total de casos, y que los dos informes de dato escaso declaran su
escasez en vez de devolver ceros.

| Informe | Ruta | Origen |
|---|---|---|
| **E6-08** Impacto humano agregado | `impacto-humano` | **BSC** / **CU-E08** |
| **E6-11** Escaladas de severidad originadas en sitio | `escaladas-de-severidad` | ± |
| **E6-12** Cobertura de evidencia por severidad | `cobertura-de-evidencia` | ± |

**Acceptance Scenarios**:

1. **Given** un período, **When** se pide el impacto humano, **Then** devuelve víctimas, heridos y
   fallecidos por severidad y región, y **los casos sin esos datos registrados no cuentan como cero**.
2. **Given** el informe de escaladas, **When** el período tiene muy pocas o ninguna, **Then** lo
   **declara como dato escaso** en vez de presentar un 0 % que se lea como «nunca se escala».
3. **Given** la cobertura de evidencia, **When** se pide, **Then** distingue los casos **cerrados con
   foto y nota** de los cerrados sin ellas, y solo considera casos cerrados.
4. **Given** cualquiera de los tres, **When** los consulta la autoridad del departamento, **Then**
   **no aparece identidad de implicados, de conductores ni del técnico que capturó la evidencia**.

---

### Edge Cases

- **Un período sin ningún caso.** `data` vacío y `cobertura: completa`. No es un cero ni un error: es
  la afirmación de que no hubo accidentes, que en este dominio es una buena noticia y hay que poder
  distinguirla de un fallo de carga.
- **Un caso registrado en un período y llegado en el siguiente.** Se atribuye al período **del
  accidente**, no al de la llegada. Atribuirlo por la llegada movería casos entre meses según lo que
  se tardó en atenderlos, y haría que un mes malo se descargara sobre el siguiente.
- **Una región creada a mitad del período comparado.** La comparación interanual contra una ventana en
  la que la región no existía **no es una caída**: se declara que no hay término de comparación.
- **Un caso con varios despachos.** El tiempo de respuesta usa **la primera llegada**, no la última.
  Contar filas de despacho aquí inflaría la cifra en proporción a los rechazos —peor imagen cuanto
  peor haya ido la operación— que es la Regla 3 del contrato de consumo.
- **El p95 de un período con tres casos.** No es un percentil: es el caso más lento. Por debajo de una
  muestra mínima, el p95 se declara **ausente**.
- **Un caso descartado o fusionado.** No entra en ningún tiempo de respuesta: nunca hubo emergencia, o
  es el mismo hecho que otro caso. Contarlos mezclaría trabajo real con ruido descartado.

---

## Requirements *(mandatory)*

### Requisitos transversales

- **FR-OE6-001**: Los doce informes DEBEN resolverse con **una consulta sobre el modelo analítico**.
  Ninguno crea una tabla propia (Regla 1 del contrato de consumo).
- **FR-OE6-002**: Toda consulta sobre `hecho_accidente`, `hecho_despacho` y las dimensiones DEBE
  forzar la versión final; **está prohibido** hacerlo sobre `hecho_ping_unidad` y `hecho_evidencia`,
  que son hechos de transacción.
- **FR-OE6-003**: Todo informe DEBE exigir `desde`, `hasta` y `granularidad`. Omitir cualquiera
  responde `400` nombrando lo que falta.
- **FR-OE6-004**: Todo informe DEBE aceptar `comparacion` (`mom` · `yoy` · `ninguna`) y, cuando no es
  `ninguna`, declarar **las dos ventanas comparadas** con igual longitud.
- **FR-OE6-005**: Un período en curso DEBE marcarse `parcial: true`.
- **FR-OE6-006**: Todo informe con meta del tablero DEBE declararla en `meta.objetivo` con su `tipo`
  (`NORMATIVO` o `CALIBRAR`), y `cumple` DEBE ser `null` en todo objetivo `CALIBRAR`.
- **FR-OE6-007**: Toda tasa o porcentaje DEBE publicar **su denominador**.
- **FR-OE6-008**: Todo informe DEBE admitir agrupación **por condado**, además de la agrupación
  propia de cada uno. ⚠️ **Corregido el 2026-08-16 en `/plan`** — decía «por región». Ver la nota de
  abajo.

> ### ⚠️ Corrección de FR-OE6-008: la región no es construible
>
> Esta spec pedía agrupación **por región** y anotó como pendiente de verificar si la cadena
> `condado → estado → región` era válida. **Se verificó contra el stack y no lo es**, por dos
> motivos independientes:
>
> 1. **Dos regiones vivas comparten el mismo estado** (`Centro` y `Region Prueba Norte`, ambas sobre
>    Ciudad de México). Unir por estado **duplicaría cada caso**: 4 252 accidentes saldrían como
>    8 504, cada región mostrando el total completo. Y no fallaría.
> 2. **No existe ninguna relación región↔condado en el sistema operativo.** La cobertura de una
>    región se define a nivel de estado (`Dim_RegionOperativaEstadoRegion`), y
>    `incorporacion-regional/data-model.md` ya lo declaraba.
>
> Se agrupa por **condado**, que es además la clave con la que el despacho encuentra unidades
> candidatas: agrupar por lo que el sistema opera es más honesto que agrupar por una etiqueta
> administrativa que no llega hasta el hecho.
>
> **La spec estaba equivocada y se corrige, no se adapta el código a ella.** El detalle y las
> alternativas descartadas están en [`research.md`](research.md) D1. El prerrequisito para levantar
> la limitación —una tabla puente región↔condado— queda registrado como decisión pendiente, y
> **afecta igual a OE3**, cuyos E3-01 a E3-08 piden el mismo eje.
- **FR-OE6-009**: Ningún informe DEBE devolver coordenadas, identidad de implicados, de conductores,
  de operadores ni de técnicos de campo — **tampoco al `DirectorOperaciones`**. La exención de
  autoridad no levanta una exclusión constitucional.
- **FR-OE6-010**: Los repositorios DEBEN enumerar sus columnas. Ninguna consulta usa `SELECT *`.
- **FR-OE6-011**: Los casos **descartados** y los **fusionados** DEBEN excluirse de todo cálculo de
  tiempo y de todo denominador de desempeño.
- **FR-OE6-012**: Un hito no alcanzado DEBE excluir a ese caso del cálculo que lo usa, **nunca contar
  como cero**, y el informe DEBE declarar cuántos quedaron fuera.

### Permisos

- **FR-OE6-013**: Los doce informes son accesibles por **`DirectorOperaciones`** (autoridad de
  Emergencias) y por **`Gerente`**, según `acceso-estrategico.md` §4.6 y §2.
- **FR-OE6-014**: Ningún otro rol accede. Un rol operativo de Emergencias —Operador, Despacho,
  Unidad— recibe `403`: la versión de empresa de su operación no es una ampliación de su pantalla.
- **FR-OE6-015**: No se emite `meta.acotado_a`. Estos informes no acotan por titularidad.

### US1 — el tiempo hasta la llegada

- **FR-OE6-016**: **E6-01** DEBE devolver **mediana y p95** del tiempo entre `fechahora_accidente` y
  `hora_primera_llegada`, en minutos, con el recuento de casos que lo sostienen.
- **FR-OE6-017**: **E6-01** DEBE declarar el p95 **ausente** cuando la muestra del período esté por
  debajo del mínimo configurado.
- **FR-OE6-018**: **E6-02** DEBE desglosar lo mismo por severidad, ordenada **por gravedad y no
  alfabéticamente**, y agrupar como «Desconocido» los casos sin severidad resuelta.
- **FR-OE6-019**: La suma de los recuentos por severidad DEBE ser igual al total de casos con llegada
  del período.

### US2 — dónde se va el tiempo

- **FR-OE6-020**: **E6-03** DEBE desglosar el ciclo en los tramos que los hitos de `hecho_accidente`
  permiten medir: registro→confirmación, confirmación→primera asignación, primera asignación→primera
  llegada, y primera llegada→cierre.
- **FR-OE6-021**: **E6-03** DEBE entregarse **por período**, no por unidad. *(Resuelve #35: la
  duración de un caso es propiedad del caso, y repartirla entre unidades exige elegir una de forma no
  determinista. Al no atribuir, el defecto desaparece en vez de heredarse.)*
- **FR-OE6-022**: La suma de los tramos DEBE ser igual al tiempo total del caso, sin residuo.
- **FR-OE6-023**: **E6-04** DEBE comparar recuento y tiempo de respuesta por origen de despacho,
  incluyendo **«escalado a zona»** como origen propio, y sus porcentajes DEBEN sumar 100 %.
- **FR-OE6-024**: **E6-07** DEBE medir la desviación contra la **referencia histórica** del mismo
  condado y severidad en los 90 días anteriores al despacho medido.
- **FR-OE6-025**: **E6-07** DEBE devolver referencia y desviación **ausentes** cuando la ventana no
  alcance la muestra mínima, y DEBE declarar en la respuesta que la referencia es histórica y **no un
  ETA estimado**.

### US3 — los modos de fallo

- **FR-OE6-026**: **E6-05** DEBE usar como denominador los **intentos de despacho ofrecidos a esa
  unidad**, nunca las transiciones de estado.
- **FR-OE6-027**: **E6-05** DEBE separar **rechazo** de **vencimiento**: son decisiones distintas —una
  es una negativa, la otra una ausencia de respuesta— y agregarlas oculta cuál de las dos ocurre.
- **FR-OE6-028**: **E6-06** DEBE distinguir los abortos por causa, y contar **misiones**, no
  transiciones.
- **FR-OE6-029**: **E6-09** DEBE declarar explícitamente qué definición de «forzado» publica. Mientras
  #36 no se resuelva, publica **el indicador del despacho** y lo dice; **no** puede presentarse como
  el retiro manual desde central.
- **FR-OE6-030**: **E6-10** DEBE distribuir los casos abiertos en tramos de antigüedad (<1 h, 1–4 h,
  4–24 h, >24 h) tomados en el instante de la consulta, y considerar abierto **solo** al caso sin
  hora de cierre.

### US4 — el resultado sobre la persona

- **FR-OE6-031**: **E6-08** DEBE agregar víctimas, heridos y fallecidos por severidad, región y
  período, distinguiendo **«cero» de «no registrado»**.
- **FR-OE6-032**: **E6-11** DEBE calcularse desde `num_escaladas_severidad` y `severidad_inicial`, y
  DEBE **declarar la escasez del dato** cuando la muestra sea insuficiente para leer una tendencia.
- **FR-OE6-033**: **E6-12** DEBE considerar únicamente casos **cerrados**, y distinguir la cobertura
  de foto de la de nota antes de combinarlas.

### Key Entities

Todo informe devuelve **filas agregadas** con esta forma común, heredada del módulo táctico:

| Campo | Qué es |
|---|---|
| **Claves de agrupación** | Período, y una o dos de: severidad · región · condado · unidad · origen · tramo |
| **Medidas** | Mediana, p95, recuentos o porcentajes según el informe |
| **Denominador** | Obligatorio siempre que haya porcentaje |
| **Cobertura del dato** | Cuántas filas del período aportaron la medida, y cuántas quedaron fuera por hito ausente |
| **Objetivo** | Meta, tipo (`NORMATIVO` / `CALIBRAR`) y cumplimiento, cuando el informe tiene meta |
| **Comparación** | Las dos ventanas y la variación, cuando se pidió |

---

## Lo que falta en el modelo

**Nada.** ✅ *(Resuelto en `/plan`, 2026-08-16.)*

Este es el primer módulo del proyecto que **no necesita ampliar el modelo analítico**: no añade
tablas, ni dimensiones, ni métricas. Es la consecuencia directa de que Emergencias ya lo hiciera
crecer para sus 26 informes tácticos.

Lo que sí falta está **fuera del modelo analítico**, en el sistema operativo, y por eso ninguno de
los dos huecos se puede tapar desde aquí:

| Hueco | Qué desbloquea | Dónde vive |
|---|---|---|
| Relación **región↔condado** | El eje de región, en OE6 **y en OE3** | Sistema operativo (tabla puente) |
| Columna derivada **`retiro_manual`** en `hecho_despacho` | E6-09 completo, sin la limitación de #36 | Flujo de carga de otro módulo |

El segundo tiene salida conocida y compatible con la exclusión constitucional: un booleano calculado
al cargar desde `idusuario IS NOT NULL`, **sin copiar el identificador**. Conserva el hecho y no la
identidad. Ver [`research.md`](research.md) D7.

---

## Decisiones abiertas que este módulo hereda

Las tres viven en US3 a propósito. **Ninguna bloquea US1 ni US2.**

| # | Qué pasa | Efecto en OE6 |
|:--:|---|---|
| **#34** | El endpoint táctico de rechazo/timeout divide entre transiciones de estado y trunca la tabla a 10 000 de 19 528 filas | **E6-05.** La consulta correcta **ya está escrita** (`ot22_rechazo_timeout_por_unidad.sql`): FR-OE6-026 la adopta. No se hereda el defecto |
| **#35** | `tiempo-asignado-cerrado` atribuye cada caso a una unidad de forma no determinista (441 de 3 651 casos) | **E6-03.** Se **disuelve**: FR-OE6-021 entrega por período y no atribuye. Es la opción A de #35 |
| **#36** | «Retiro forzado» y «cierre forzado» difieren en un factor de 451, y el modelo no puede reproducir la segunda definición sin copiar identidad de usuario | **E6-09.** Es el único que queda **realmente limitado**. FR-OE6-029 obliga a declarar qué mide |

**#36 es el que hay que decidir.** La salida propuesta en la propia decisión —un booleano derivado
«el retiro fue manual», calculado al cargar desde `idusuario IS NOT NULL` **sin copiar el
identificador**— es compatible con la exclusión constitucional y resolvería E6-09 por completo. Es un
cambio de esquema, y por eso pertenece a `/plan`, no aquí.

---

## Cumplimiento ISO/IEC 25010:2023

Declaración exigida por el Golden Rule de la constitución.

| Característica | Aplica | Cómo |
|---|:--:|---|
| **Idoneidad funcional** | ✅ | Los doce salen del catálogo con origen trazado a CU-E08 y al BSC. Cada FR es verificable con una consulta. Las cinco discrepancias del catálogo se corrigen contra el modelo real en vez de heredarse |
| **Fiabilidad** | ✅ | FR-OE6-002 (versión final) evita la cifra inflada intermitente; FR-OE6-012 impide que un hito ausente se lea como cero |
| **Eficiencia de desempeño** | ✅ | Regla 7: toda consulta filtra por fecha para descartar particiones. Sin ello, un informe anual se degrada según crece el histórico, sin que nada avise |
| **Capacidad de interacción** | ⚪ | **No aplica en esta capa.** El frontend está aplazado; la spec de la capa de presentación lo declarará |
| **Seguridad** | ✅ | FR-OE6-009 y FR-OE6-010: exclusión constitucional del dato sensible aplicada también a la autoridad, y lista blanca de columnas en el repositorio en vez de lista negra |
| **Compatibilidad** | ✅ | Contrato OpenAPI versionado bajo el envelope común del §2 del contrato estratégico |
| **Mantenibilidad** | ✅ | El módulo **reutiliza las consultas tácticas** en vez de duplicar la métrica. Dos definiciones de la misma cifra es el defecto que más caro sale de corregir |
| **Flexibilidad** | ✅ | FR-OE6-008: el eje de región es el que permite comparar mercados nuevos con maduros sin rehacer el informe |
| **Seguridad física (Safety)** | ✅ | Es la razón de ser del OE. Un tiempo de respuesta mal medido —por promediar en vez de usar percentil, o por contar como cero un caso sin llegada— **oculta precisamente los casos en que la ayuda no llegó a tiempo** |

**Conflictos entre características:** *ninguno identificado.* El único candidato —Seguridad frente a
Idoneidad, en E6-09, donde la definición correcta del informe exige un dato de identidad excluido— **no
se resuelve relajando la exclusión**: se resuelve con un booleano derivado que conserva el hecho y no
la identidad. No hay trade-off que documentar porque no hay que sacrificar nada.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los doce informes se entregan **sin crear ninguna tabla**: el recuento de tablas del
  almacén analítico es el mismo antes y después.
- **SC-002**: El tiempo global de respuesta se puede comparar entre dos trimestres consecutivos y
  entre el mismo trimestre de dos años, con las dos ventanas declaradas en la respuesta.
- **SC-003**: Ningún informe devuelve un porcentaje sin su denominador.
- **SC-004**: Un caso sin llegada registrada **nunca** aparece como tiempo de respuesta cero en
  ninguno de los doce informes.
- **SC-005**: Los doce informes, consultados con el rol de máxima autoridad del departamento, no
  devuelven ningún campo de coordenadas ni de identidad de persona.
- **SC-006**: Un rol operativo de Emergencias recibe `403` en los doce, no un resultado acotado.
- **SC-007**: Las cifras de los informes que existen en las dos capas **coinciden** con su
  contraparte táctica cuando se piden con la misma agrupación y período — salvo E6-05 y E6-09, cuya
  divergencia está declarada y explicada por #34 y #36.
- **SC-008**: Todo objetivo `[CALIBRAR]` se devuelve con `cumple: null`; ningún informe presenta una
  meta sin línea base como incumplimiento.
- **SC-009**: Un período sin datos se distingue de un período no medido en los doce informes.

---

## Assumptions

- **El modelo analítico está cargado y al día.** Los doce informes leen lo que los DAG de Emergencias
  ya cargan; este módulo no añade flujos de carga.
- **La muestra mínima para percentiles y para la referencia histórica es configurable**, y se hereda
  del valor que el módulo táctico ya usa para la desviación de llegada. No se decide aquí un número
  nuevo.
- ~~**La región se resuelve por el estado geográfico** mientras `/plan` no demuestre lo contrario.~~
  ❌ **Refutada el 2026-08-16.** Se comprobó contra el stack: dos regiones comparten estado y no
  existe relación región↔condado. Era la única suposición de esta spec capaz de cambiar el diseño de
  las consultas, y cambió — ver la corrección de `FR-OE6-008`.
- **Los informes compartidos con OE3** (E3-02, E3-10, E3-11, E3-12) **no se implementan aquí**. Se
  referencian; su dueño es OE3.
- **El frontend queda fuera de alcance.** Ninguna decisión de esta spec asume una pantalla.
- **`Gerente` todavía no existe como rol sembrado.** Los permisos se escriben contra él igualmente;
  hasta que se siembre, solo `DirectorOperaciones` podrá ejercerlos en la práctica.
