# Feature Specification: OE3 — Escalabilidad Multi-Región sin Degradación

**Feature Branch**: `001-estrategico/OE3-escalabilidad-multiregion/backend`

**Created**: 2026-08-16

**Status**: Implemented (2026-08-18). Siete GET publicados; siete bloqueados sin endpoint. Frontend en capa aparte.

**Input**: User description: "Informes estratégicos del OE3 — los catorce informes que miden si la operación puede escalar a nuevos mercados sin degradar el rendimiento del servicio, resueltos con consultas sobre el modelo analítico."

---

## Contexto

Tercer módulo de la capa estratégica. **Reutiliza el armazón que OE6 construyó** —período, ventanas
comparadas, objetivo BSC, envelope, permisos— y no lo redefine.

El objetivo dice: *escalar la operación a cualquier mercado internacional sin degradar el rendimiento
del servicio, garantizando que cada nueva ciudad o región reciba el mismo nivel de respuesta técnica
desde el primer día.*

**Es el OE con más metas `[NORMATIVO]` del tablero**: latencia de despacho ≤100 ms, uptime ≥99,99 %,
puesta en operación regional ≤30 días, tasa de error de registro <1 %, reasignación manual ≤30 s. Son
compromisos, no referencias — y por tanto los únicos informes de toda la capa estratégica que **sí
pueden semaforizarse**, a diferencia de OE6 y OE4, cuyas metas son todas `[CALIBRAR]`.

---

## ⚠️ La mitad que no se puede medir

Este es el hallazgo central, y conviene leerlo antes que nada.

El objetivo tiene dos mitades: **escalar** y **sin degradar**. Verificado contra el almacén:

| Mitad | ¿Medible? | Informes |
|---|:--:|:--:|
| **Que el servicio no se degrada** | ✅ Sí | 7 |
| **Que la operación escala** | ⛔ No | 7 |

### Por qué no se puede medir la escalabilidad

**1. El modelo no sabe cuándo entró en producción ninguna región.**

```
nombre_region         estado_ciclo_vida  valido_desde         inicio_es_real
Centro                Producción         1970-01-01 00:00:00  0
Region Prueba Norte    Producción         1970-01-01 00:00:00  0
```

`inicio_es_real = 0` es la marca de *«desde que empezamos a mirar»*, no una fecha conocida — el
sistema operativo guarda el estado presente de una región y lo sobrescribe, sin historizar la
transición.

⚠️ **El fallo sería espectacular y silencioso.** E3-04 mide «días desde la incorporación hasta la
primera emergencia atendida», con meta ≤30 días `[NORMATIVO]`. Calculado contra `1970-01-01` daría
**más de veinte mil días** por región, en rojo, sin ningún error. Y E3-05 y E3-06 —maduración y
cohorte por antigüedad— **no tienen ni siquiera esa cifra falsa**: sin fecha de arranque no hay
cohortes que formar.

**2. El modelo no sabe qué condados cubre una región.** `decisiones-pendientes.md` #38: la cobertura
se define a nivel de estado, y dos regiones comparten estado. Unir por estado duplica cada caso.

**3. Falta la vecindad entre condados.** E3-08 —cobertura de respaldo— necesita `Dim_CondadoVecino`,
que existe en el sistema operativo y **no se ha cargado al modelo analítico**. Es el único de los
siete bloqueos con una salida barata.

### Y tres informes cuya fuente no es de este sistema

| Informe | Fuente | |
|---|---|---|
| **E3-01** Uptime global por región | Monitoreo de infraestructura (Prometheus) | No lo produce el modelo de negocio |
| **E3-09** Margen operativo por región | Costos de infraestructura por región | No existe fuente de costos |
| **E3-14** Cobertura de pruebas automatizadas | `pytest-cov` / SonarQube | No es un informe de negocio |

**E3-14 no debería estar en este catálogo.** Es una métrica de ingeniería, valiosa, que no sale de
ningún dato de operación. Se conserva en la spec para dejar contado que el tablero la promete.

### Lo que esto significa para el tablero

**OE3 puede afirmar que el servicio no se degrada. No puede afirmar que escala.** Con dos regiones
declaradas, una de ellas llamada «Region Prueba Norte», y todos los accidentes en un solo estado, el
objetivo **no tiene todavía el fenómeno que quiere medir**.

Es una conclusión incómoda y es la honesta: el módulo entrega lo medible y **declara el resto con su
prerrequisito**, en vez de publicar cifras que parecerían responder la pregunta.

---

## User Scenarios & Testing *(mandatory)*

> ## ⚠️ Correcciones aplicadas en `/plan` (2026-08-16)
>
> La investigación contra el almacén demostró que **tres puntos de esta spec estaban equivocados**.
> Se corrigen aquí; el detalle y las alternativas descartadas están en [`research.md`](research.md).
>
> | Qué decía | Qué es | Dónde |
> |---|---|---|
> | E3-02 mide «solicitud→confirmación» contra **≤100 ms** | El catálogo **mezcla dos métricas**: la latencia técnica del algoritmo y el tiempo operativo. El informe mide el operativo contra la meta real de `RNF-DES-001`, **`<2 min p95`** — medido 1,77 min, **se cumple**. Contra 100 ms estaría 1 060× por encima | D1 |
> | E3-12 es construible (US1) | **No lo es.** 1 082 de 1 083 despachos manuales no siguen a ningún intento automático: el suceso que mide no se registra. **Pasa a US4** | D2 |
> | E3-08 está bloqueado (US3) | **Se desbloquea.** `Dim_CondadoVecino` existe con datos y es simétrica. Se carga como dimensión. **Pasa a US2** | D3 |
>
> **El total de construibles no cambia —siete—, pero el reparto entre historias sí.**

### User Story 1 - El rendimiento del despacho no se degrada (Priority: P1) 🎯 MVP

Cuatro informes: **E3-02**, **E3-03**, **E3-10** y **E3-11**. Son los que llevan las metas medibles
del tablero, y **tres de ellos los comparte OE6**, que los referencia sin implementarlos.

**Why this priority**: son los únicos informes de toda la capa estratégica que **pueden
semaforizarse** —sus metas son compromisos, no referencias—, y se calculan enteros sobre hechos que
ya existen y están verificados. Máximo valor, mínimo riesgo.

**Independent Test**: pedir la latencia de despacho p95 de un trimestre con comparación interanual y
comprobar que devuelve el valor, la meta ≤100 ms, y un `cumple` **booleano** — el primero de la capa.

| Informe | Ruta | Meta | Origen |
|---|---|---|---|
| **E3-02** Latencia operativa de asignación | `latencia-asignacion` | **`<2 min p95`** `[NORMATIVO]` | **BSC** / **CU-E05** |
| **E3-03** Evolución de la latencia p95 | `evolucion-latencia` | — | **CU-E05** / ± |
| **E3-10** Tasa de error de registro | `tasa-error-registro` | <1 % `[NORMATIVO]` | **BSC** / **CU-E08** |
| **E3-11** Despachos al primer intento | `primer-intento` | ≥90 % `[CALIBRAR]` | **BSC** / **CU-E08** |

**Acceptance Scenarios**:

1. **Given** un período con despachos, **When** se pide la latencia p95, **Then** devuelve el valor y
   `objetivo` con `tipo: "NORMATIVO"` y un `cumple` **booleano**. Es la excepción a la regla de OE6 y
   OE4, donde todo `cumple` es nulo.
2. **Given** la evolución de la latencia, **When** se pide sobre una ventana amplia, **Then** permite
   ver **degradación gradual**, que es el fallo que este objetivo teme: no un salto, sino un empeoramiento
   lento que ninguna alarma dispara.
3. **Given** los despachos al primer intento, **When** se calculan, **Then** usan **grano de intento**
   —ordinal 1 y desenlace confirmado—. Con grano de caso los intentos fallidos desaparecen.
4. **Given** la tasa de error de registro, **When** se calcula, **Then** usa la **ausencia real del
   modelo**, no una comparación contra nulidad sobre el sistema operativo, donde es siempre cierta.
5. **Given** la tasa de error de registro, **When** se publica, **Then** declara **qué campos
   comprueba**. Su valor medido es 0 %, y un indicador que estructuralmente nunca se mueve no es una
   señal: sin la lista se lee como «el registro es perfecto» en vez de «los dos campos que miro están
   completos».
6. **Given** cualquiera de los cuatro, **When** OE6 los necesita, **Then** los consume **desde aquí**;
   no existe una segunda implementación.

---

### User Story 2 - Detectar la tensión antes de que degrade (Priority: P2)

Tres informes: **E3-07**, **E3-08** y **E3-13**. Miden dónde la operación está al límite —demanda
contra capacidad—, si esa zona tiene a quién recurrir, y dónde el seguimiento de unidades falla.

> **E3-08 estaba en US3 y sube aquí.** `/plan` comprobó que `Dim_CondadoVecino` existe con datos y es
> simétrica, así que se desbloquea cargándola como dimensión. Encaja en esta historia porque responde
> la pregunta que sigue naturalmente a la de E3-07: *este condado está en tensión, ¿hay alguien al
> lado que pueda respaldarlo?*

**Why this priority**: US1 dice si el servicio se degradó; esta dice **dónde va a degradarse**. Va
después porque avisar de un riesgo antes de saber medir el daño es un orden inútil.

**Independent Test**: pedir el ratio demanda/capacidad de un trimestre pasado y comprobar que la
capacidad es la **vigente entonces**, no la flota de hoy.

| Informe | Ruta | Origen |
|---|---|---|
| **E3-07** Ratio demanda / capacidad por condado | `ratio-demanda-capacidad` | **BSC** / **CU-E05** |
| **E3-08** Cobertura de respaldo por condado vecino | `cobertura-de-respaldo` | **CU-E05** / ± |
| **E3-13** Pérdida de señal GPS | `perdida-de-senal` | **CU-E08** / ± |

**Acceptance Scenarios**:

1. **Given** un trimestre pasado, **When** se pide el ratio demanda/capacidad, **Then** la capacidad
   son **las versiones de unidad vigentes en ese período**, no las unidades activas hoy. Usar la flota
   actual calcularía un ratio de hace tres meses contra unidades que quizá no existían.
2. **Given** la pérdida de señal, **When** se pide, **Then** analiza **todas** las posiciones del
   período. El flujo legado analizaba 10 000 de 59 045 y publicaba el resultado como completo.
3. **Given** un condado sin ninguna unidad vigente, **When** se calcula su ratio, **Then** se declara
   **sin capacidad**, no un ratio infinito ni una división que falla.
4. **Given** la cobertura de respaldo, **When** el condado vecino tiene unidades dadas de alta pero
   todas ocupadas o fuera de servicio, **Then** **no cuenta como respaldo**. Existir no es estar
   disponible — es el error que Red Operativa documentó como el más caro de su departamento.

---

### User Story 3 - Medir la maduración regional (Priority: P3) ⛔ BLOQUEADA

Tres informes: **E3-04**, **E3-05** y **E3-06**. Son **el corazón del objetivo** —si una región nueva
alcanza el nivel de servicio de las maduras, y en cuánto tiempo— y ninguno es construible.

> **E3-08 estaba aquí y se movió a US2**: era el único bloqueo de esta historia con salida barata, y
> `/plan` comprobó que la tiene. Lo que queda son **tres informes con un único prerrequisito común**.

**Why this priority**: está aislada porque **su bloqueo es de datos del sistema operativo**, no de
diseño, y no debe detener las dos historias que sí funcionan.

| Informe | Prerrequisito |
|---|---|
| **E3-04** Tiempo de puesta en operación *(≤30 días `[NORMATIVO]`)* | Fecha real de entrada en producción de cada región |
| **E3-05** Curva de maduración (30 / 60 / 90 días) | Ídem, más el eje de región (#38) |
| **E3-06** Rendimiento por cohorte de antigüedad | Ídem |

**Acceptance Scenarios**:

1. **Given** que las regiones no tienen fecha real de arranque, **When** se implementa el módulo,
   **Then** **no se publica endpoint** para E3-04, E3-05 ni E3-06. Publicar E3-04 daría más de veinte
   mil días por región, en rojo permanente contra una meta `[NORMATIVO]`.
2. **Given** el tablero estratégico, **When** pide la puesta en operación regional, **Then** se
   declara **inmedible** con su prerrequisito, no en incumplimiento.
3. **Given** que los tres comparten prerrequisito, **When** se historice el estado de región en el
   sistema operativo, **Then** los tres se desbloquean **a la vez**. No hay que resolverlos uno a uno.

> ⚠️ **Aquí se pierden dos indicadores del BSC**: tiempo de puesta en operación regional y —vía la
> imposibilidad de comparar regiones— buena parte del valor del ratio demanda/capacidad. El primero
> es `[NORMATIVO]`: **el tablero promete un compromiso que hoy nadie puede verificar.**

---

### User Story 4 - Lo que el sistema no registra ni produce (Priority: P4) ⛔

Cuatro informes: **E3-12**, **E3-01**, **E3-09** y **E3-14**. No están bloqueados por un hueco del
modelo analítico: **el dato no lo produce ni lo registra nadie**.

**Why this priority**: se documentan y no se construyen. Están separados de US3 porque el tipo de
bloqueo es distinto: US3 se desbloquea historizando datos propios; esto exige **instrumentar la
aplicación o integrar una fuente externa**, que son decisiones de arquitectura ajenas a este módulo.

| Informe | Qué haría falta | Tipo |
|---|---|---|
| **E3-12** Tiempo de reasignación manual *(≤30 s `[NORMATIVO]`)* | Que la aplicación registre «asignación automática sin candidatas» con su instante | Suceso no instrumentado |
| **E3-01** Uptime global por región *(≥99,99 % `[NORMATIVO]`)* | Integrar el monitoreo de infraestructura como fuente del analítico | Fuente externa |
| **E3-09** Margen operativo por región *(≥30 % `[CALIBRAR]`)* | Una fuente de costos de infraestructura por región | Fuente externa |
| **E3-14** Cobertura de pruebas automatizadas | Herramienta de cobertura. **No es un informe de negocio** | Fuente externa |

> **E3-12 llegó aquí desde US1**, y es la corrección menos evidente del plan. Su definición —tiempo
> entre la falla del algoritmo y la intervención del operador— exige que la intervención manual siga
> a un intento automático fallido. Medido: **1 082 de 1 083 despachos manuales no siguen a ninguno**.
> El operador despacha a mano desde el principio, y el sistema no anota en ningún sitio que un
> algoritmo se rindiera. Ver [`research.md`](research.md) D2.

**Acceptance Scenarios**:

1. **Given** que las tres fuentes son externas, **When** se implementa el módulo, **Then** **no se
   publica ningún endpoint** para ellas.
2. **Given** el catálogo estratégico, **When** se actualice, **Then** E3-14 se marca como métrica de
   ingeniería y **candidata a salir del tablero de negocio**: mide el proceso de desarrollo, no la
   operación del servicio.

---

### Edge Cases

- **Un condado con casos y sin unidades vigentes.** Ratio **sin capacidad**, no infinito ni error. Es
  además el hallazgo operativo más valioso del informe: demanda sin nadie que la atienda.
- **Un período sin ningún despacho manual.** La reasignación manual devuelve medida ausente, no cero
  segundos — que se leería como reasignación instantánea.
- **La latencia p95 de un período con tres despachos.** No es un percentil: es el más lento. Bajo la
  muestra mínima se declara ausente.
- **Una región despublicada.** Debe **seguir apareciendo** en los informes de los meses en que operó.
  `dim_region` es versionada precisamente para eso — aunque hoy la elección sea teórica, porque
  ninguna versión tiene fecha real.
- **Un `cumple: false` contra una meta `[NORMATIVO]`.** Es un incumplimiento real y debe presentarse
  como tal. Es la diferencia con OE6 y OE4, donde un rojo sería inventado.

---

## Requirements *(mandatory)*

### Transversales

- **FR-OE3-001**: Este módulo **reutiliza sin modificar** las piezas transversales de OE6.
- **FR-OE3-002**: Los siete informes construibles DEBEN resolverse con **una consulta sobre el
  modelo**. Ninguno crea una tabla propia.
- **FR-OE3-003**: Toda consulta sobre `hecho_accidente`, `hecho_despacho` y las dimensiones DEBE
  forzar la versión final; **está prohibido** sobre `hecho_ping_unidad`.
- **FR-OE3-004**: Ningún informe DEBE agrupar por región ni unir con `dim_region` (#38). Se agrupa
  por **condado**.
- **FR-OE3-005**: Ningún informe DEBE devolver coordenadas ni identidad de personas.

### Permisos — autoridad repartida

- **FR-OE3-006**: La autoridad **no es única** (`acceso-estrategico.md` §4.3). `DirectorOperaciones`
  accede a los de despacho y registro; `DirectorExpansion` a los de crecimiento y capacidad;
  `DirectorTecnologico` a los de validación e infraestructura; `Gerente` a todos.
- **FR-OE3-007**: La asignación se declara **por informe**, no por departamento. Un
  `es_autoridad_de(departamento)` concedería de más justo donde el SRS pide lo contrario.

### US1 — el rendimiento

- **FR-OE3-008**: **E3-02** DEBE medir el tiempo entre el registro del accidente y la **primera
  asignación de unidad**, contra la meta `<2 min p95` de `RNF-DES-001`, con `objetivo` de tipo
  `NORMATIVO` y `cumple` **booleano**.
- **FR-OE3-008b**: **E3-02** DEBE emitir `meta.alcance` declarando que mide el **proceso operativo** y
  no la latencia técnica del algoritmo. Sin esa declaración, la cifra se compara mentalmente con los
  ≤100 ms que el catálogo anuncia y parece un incumplimiento de 1 060×.
- **FR-OE3-009**: **E3-03** DEBE permitir ventanas amplias para detectar **degradación gradual**.
- **FR-OE3-010**: **E3-11** DEBE usar **grano de intento**: ordinal 1 con desenlace confirmado.
- **FR-OE3-011**: **E3-10** DEBE medir la ausencia contra el modelo, no contra centinelas del sistema
  operativo, y DEBE **publicar la lista de campos que comprueba**.
- **FR-OE3-012**: ~~E3-12 DEBE considerar los despachos de origen Manual.~~ ❌ **Retirado el
  2026-08-16**: E3-12 no es construible. Ver US4 y `research.md` D2.
- **FR-OE3-013**: Los cuatro informes compartidos DEBEN ser **la única implementación**: OE6 los
  consume desde aquí.

### US2 — la tensión

- **FR-OE3-014**: **E3-07** DEBE usar como capacidad las **versiones de unidad vigentes en el
  período**, no la flota actual.
- **FR-OE3-015**: **E3-07** DEBE declarar **«sin capacidad»** para un condado con demanda y ninguna
  unidad vigente, en vez de un ratio infinito.
- **FR-OE3-016**: **E3-13** DEBE analizar **todas** las posiciones del período.
- **FR-OE3-016b**: **E3-08** DEBE contar como respaldo únicamente los condados vecinos con al menos
  una unidad **disponible** —último estado registrado—, no con unidades meramente dadas de alta.

### US3 y US4 — lo bloqueado

- **FR-OE3-017**: Los siete informes de US3 y US4 **NO DEBEN publicarse como endpoint**.
- **FR-OE3-018**: La documentación DEBE declarar que **tres indicadores `[NORMATIVO]` del BSC quedan
  sin fuente** —uptime, puesta en operación regional y tiempo de reasignación manual— con su
  prerrequisito nombrado.
- **FR-OE3-019**: ✅ **Resuelto en `/plan`.** `Dim_CondadoVecino` existe con datos y es simétrica; se
  carga como dimensión y E3-08 se desbloquea. Ver `research.md` D3.

---

## Cumplimiento ISO/IEC 25010:2023

| Característica | Aplica | Cómo |
|---|:--:|---|
| **Idoneidad funcional** | ⚠️ | Los siete construibles están trazados. **Los otros siete se declaran inmedibles con su prerrequisito**, que es la única forma honesta de cubrirlos |
| **Fiabilidad** | ✅ | El módulo mide la fiabilidad, no participa en ella. Versión final obligatoria |
| **Eficiencia de desempeño** | ✅ | Regla 7. E3-03 usa ventanas amplias, así que el filtrado de particiones importa aquí más que en ningún otro informe |
| **Capacidad de interacción** | ⚪ | No aplica en esta capa. Frontend implementado en [`../frontend/`](../frontend/) |
| **Seguridad** | ✅ | FR-OE3-005, con la exención de autoridad que no levanta exclusiones |
| **Compatibilidad** | ✅ | Contrato OpenAPI bajo el envelope común |
| **Mantenibilidad** | ✅ | Reutiliza el armazón de OE6 y es **la única implementación** de los cuatro informes compartidos |
| **Flexibilidad** | ⛔ | **Es la característica que este objetivo existe para medir, y es la que no puede medir.** Sin fecha de arranque regional ni eje de región, la adaptabilidad a nuevos mercados no es verificable |
| **Seguridad física (Safety)** | ✅ | E3-07 detecta condados con demanda y sin capacidad — es decir, **zonas donde una emergencia no tiene quién la atienda**. Es el informe con consecuencia física más directa del módulo |

**Conflicto identificado y su resolución:** *Idoneidad funcional* pedía publicar los catorce informes
del catálogo; *Fiabilidad* y *Safety* lo impiden para siete de ellos. Rige la regla 1 del
Tie-Breaker: **hay Safety en juego**. Un E3-04 en rojo permanente por comparar contra 1970, o un
uptime inventado, degradan la confianza en el tablero que vigila la capacidad de despachar
ambulancias. **Se prioriza no publicar.** Lo sacrificado es cobertura aparente del catálogo; lo
ganado es que ninguna cifra del tablero afirme algo que el sistema no sabe.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los siete informes construibles se entregan **sin crear ninguna tabla de informe**. La
  única ampliación del modelo es la dimensión compartida `dim_condado_vecino`, y el recuento de tablas
  pasa de 13 a 14 por ella y solo por ella.
- **SC-002**: **E3-02 y E3-10** devuelven un `cumple` **booleano** contra sus metas `[NORMATIVO]` —los
  primeros de la capa estratégica que pueden semaforizarse—, y **E3-11 devuelve `null`** porque la
  suya es `[CALIBRAR]`.
- **SC-002b**: E3-02 declara en `meta.alcance` que mide el proceso operativo, y su `objetivo.valor`
  es **2 minutos**, no 100 ms.
- **SC-003**: Los siete bloqueados **no tienen endpoint**, y cada uno nombra su prerrequisito.
- **SC-004**: Un ratio demanda/capacidad de un período pasado se calcula contra la flota **de
  entonces**, verificable contra un período en que la flota haya cambiado.
- **SC-005**: Un condado con demanda y sin unidades se distingue de un condado sin demanda.
- **SC-006**: Los cuatro informes compartidos con OE6 tienen **una sola implementación**, y una prueba
  lo verifica.
- **SC-007**: Ningún informe devuelve coordenadas ni identidad, con el rol de máxima autoridad.
- **SC-008**: La asignación de acceso es **por informe**: `DirectorExpansion` no accede a los de
  despacho, y `DirectorOperaciones` no accede a los de capacidad regional.

---

## Assumptions

- **El armazón de OE6 está construido.** Si no, las fases 1 y 2 de su `tasks.md` son prerrequisito.
- **OE6 no implementa los cuatro compartidos.** Su spec ya lo declara. Si se implementara OE6 antes y
  los construyera, este módulo los adopta en vez de duplicarlos.
- ~~**`Dim_CondadoVecino` se puede cargar al modelo**, a verificar en `research`.~~ ✅ **Verificada el
  2026-08-16**: existe, tiene 2 filas simétricas y se carga como dimensión. Era la única suposición
  capaz de ampliar el alcance, y lo amplió.
- **La muestra mínima para percentiles** se hereda de OE6.
- **No se integra ninguna fuente externa.** Prometheus, costos y cobertura de pruebas quedan fuera:
  integrarlas es una decisión de arquitectura que excede a un módulo de informes.
- **Esta spec no define pantallas.** El frontend está en [`../frontend/`](../frontend/) (implementado).
