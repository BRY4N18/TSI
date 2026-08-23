# Feature Specification: OE3 — Escalabilidad Multi-Región sin Degradación — Frontend

**Feature Branch / capa**: `001-estrategico/OE3-escalabilidad-multiregion/frontend`

**Created**: 2026-08-18

**Status**: Implemented (2026-08-18). Cuatro pantallas Z (`latencia`, `calidad`, `capacidad`, `respaldo`); cuatro guards; 7 GET. Sin mapa, región ni recuadros bloqueados.

**Depends-on**: [`../backend/spec.md`](../backend/spec.md), su contrato de lectura y
[`../../acceso-estrategico.md`](../../acceso-estrategico.md) §4.3, §5 y §6. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados, metas ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que los compuestos tácticos y que OE1/OE2/OE5/OE6) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

**Input**: continuar la capa estratégica con las pantallas de los **siete informes ya publicados**
de OE3; no pintar los siete bloqueados; no inventar un informe de alcance geográfico; no agrupar
por región; no pintar mapa de personas ni identidad; copiar la cáscara Z, no extraer `shared/`.

---

## Contexto

El backend de OE3 **ya publica siete informes** y **no publica** los otros siete (puesta en marcha
regional, maduración, cohorte, uptime, margen, reasignación manual, cobertura de pruebas). Esta
capa no calcula nada: pinta lo que el contrato ya corrige.

El objetivo tiene dos mitades. **Esta UI solo puede mostrar que el servicio no se degrada.** No
puede mostrar que la operación escala: el modelo no sabe cuándo nació una región ni qué condados
cubre. Un tablero que prometa «escalamos a cualquier mercado» con estas siete cifras **mentiría**.

Entrega **cuatro pantallas nuevas** de lectura de empresa. No se mezclan con:

- los compuestos tácticos de Emergencias ni de Red Operativa;
- las pantallas de OE6 (tiempo de llegada a la persona) ni las de OE4 (inteligencia);
- un mapa, una lista de nombres o un recuadro de «nueva región en N días».

Las cifras tácticas y estas **difieren a propósito**: aquí hay ventana comparada, percentil o tasa
con meta BSC, y agregado de empresa. MUST distinguirse en menú y en la propia pantalla.

Los cuatro informes que OE6 **referencia** (latencia de asignación, error de registro, primer
intento, y el bloqueado de reasignación) **se leen aquí**. OE6 no los reimplementa. Esta capa
MUST pintarlos; MUST NOT volver a pedirlos como si fueran de OE6.

### La autoridad está partida

A diferencia de OE6, **no hay un solo cargo dueño de las cuatro pantallas.**
[`acceso-estrategico.md`](../../acceso-estrategico.md) §4.3: Tecnológico valida, Expansión decide
dónde crecer, Operaciones responde por el despacho. El `Gerente` ve las cuatro. El Partner no
entra. El Administrador no sustituye a nadie.

| Materia | Quién entra | Pantalla |
|---|---|---|
| ¿El despacho se está volviendo más lento? | `DirectorOperaciones` · `Gerente` | **Latencia** |
| ¿El registro y el primer intento aguantan? | `DirectorOperaciones` · `Gerente` | **Calidad** |
| ¿Dónde la demanda aprieta a la flota? | `DirectorExpansion` · `DirectorOperaciones` · `Gerente` | **Capacidad** |
| ¿El condado vecino puede respaldar? | `DirectorExpansion` · `Gerente` | **Respaldo** |
| Puesta en marcha / maduración / cohorte de región | **nadie** | — (inmedible) |
| Uptime, margen, pruebas, reasignación cronometrada | **nadie** | — (sin fuente o suceso no registrado) |
| Partner, Finanzas, Marketing, Éxito de Cliente | **nadie** | — |

Cada cargo **MUST** ver **solo sus enlaces**. Un ítem gris o un 403 después de entrar descubriría
la superficie (Ley de Hick + design-system).

El `DirectorTecnologico` **MUST NOT** ver ninguna pantalla de OE3 en esta capa: el GET de
E3-02 solo admite Operaciones y Gerente. §4.3 le da E3-02; un enlace que abriera un 403
descubriría la superficie. El hueco es de backend, no se tapa con un ítem gris.

El `DirectorExpansion` **MUST NOT** ver Latencia ni Calidad. El `DirectorOperaciones` **MUST NOT**
ver Respaldo. El `DirectorFinanciero` **MUST NOT** ver ninguna (E3-09 está bloqueado: no hay
margen que pintar). Un partner **MUST NOT** ver ninguna.

Ver **MUST NOT** habilitar a abrir una región, mover flota, despachar ni cambiar un condado.
Abajo a la derecha hay **lectura**, no una acción de expansión.

### El ojo recorre el patrón Z

1. Arriba a la izquierda: métrica principal (héroe), con meta y `cumple` **solo** cuando el
   backend lo declara booleano (`[NORMATIVO]`).
2. Arriba a la derecha: **período** (obligatorio) y **comparación** de igual longitud (`ninguna`,
   mes anterior, mismo tramo del año anterior). Son las únicas acciones de esta capa.
3. Diagonal: el visual más grande.
4. Abajo a la derecha: la **lectura** — qué implica el número, qué no se está midiendo, y el
   recuento o la cobertura.

**No hay mapa ni fichas.** El backend no entrega coordenadas ni identidad. Agrupa por **condado**,
no por región. Esta capa MUST respetarlo: una barra o una tabla por condado, nunca un mapa de
personas ni un eje «región» inventado.

### Lo que no se puede mostrar

Un p95 de tres despachos **MUST verse ausente**, no como percentil cerrado. Es el caso más lento
disfrazado.

Un período **sin despachos** MUST verse **vacío con cobertura completa**, no como 0 min ni como
«cumplimos la meta porque no hubo nada».

E3-02 mide el **proceso operativo** registro→asignación (minutos), no la latencia del algoritmo
(milisegundos). La pantalla MUST declarar ese alcance junto a la cifra. Pintar un rojo contra
100 ms sería leer el catálogo viejo, no el contrato.

`cumple` booleano (verde/rojo) **solo** donde el backend lo envía. E3-11 es `[CALIBRAR]`: MUST
NOT pintarse como semáforo cerrado. Un nulo MUST leerse «sin calibrar», no «incumple».

Un condado con demanda y **sin unidades vigentes** MUST leerse **sin capacidad**, no como ratio
infinito ni como 0. Es el hallazgo de Safety de E3-07.

La capacidad MUST ser la flota **del período**, no la de hoy. La lectura MUST decirlo.

E3-08 MUST contar respaldo solo si el vecino tiene unidad **disponible**, no meramente dada de
alta. La pantalla MUST mostrar el denominador (vecinos considerados) y no un porcentaje huérfano.

E3-13 MUST no fingir «GPS perfecto» sobre una muestra recortada: si el backend declara cobertura
o recuento de posiciones, van **junto a la cifra**.

Los siete bloqueados **MUST NOT** tener recuadro, ítem de menú, «próximamente» ni un 20 000 días
en rojo contra 1970. El tablero promete tres metas `[NORMATIVO]` (uptime, puesta en marcha,
reasignación manual) que **hoy nadie puede verificar**: la UI MUST no tapar ese hueco con un
cero o un semáforo.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Latencia** | ¿El despacho se degrada? | E3-02 p95 + recuento + `cumple` + alcance operativo | E3-03 evolución | Muestra mínima; vacío ≠ 0 min; no es latencia de algoritmo | — |
| **Calidad** | ¿Registro y primer intento aguantan? | E3-10 tasa + campos comprobados + `cumple` | E3-11 primer intento (grano de intento) | E3-11 sin semáforo cerrado (`[CALIBRAR]`); 0 % de error no es «registro perfecto» | — |
| **Capacidad** | ¿Dónde va a romperse? | E3-07 ratio demanda/capacidad (condado) | Condados **sin capacidad** aparte de los tensos | Flota **del período**; sin capacidad ≠ infinito | E3-13 pérdida de señal, con recuento de posiciones |
| **Respaldo** | ¿Hay vecino que pueda cubrir? | E3-08 cobertura de respaldo | Condados con vecino disponible vs solo dados de alta | Denominador a la vista; existir ≠ estar disponible | — |

Latencia tiene dos informes. Cabe en Z. MUST NOT rellenarse con un mapa o con un informe
bloqueado para «completar la pantalla».

Calidad tiene dos. Cabe en Z.

Capacidad tiene tres. E3-13 MUST quedar en apoyo plegado para no pasar de 6–8 bloques.

Respaldo tiene uno. El desglose llena el visual; la definición llena la lectura.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Operaciones ve si el despacho se degrada (Priority: P1) 🎯 MVP

El Director de Operaciones abre **Latencia**, fija un período y ve de inmediato el p95 de
registro→asignación, el recuento que lo sostiene, si **cumple** la meta normativa y la
declaración de que es tiempo de proceso, no de algoritmo. El visual muestra la **evolución**
para detectar empeoramiento lento. Un período sin despachos se lee vacío, no como 0 min.

**Why this priority**: E3-02 es el único indicador BSC de este objetivo que **sí se semaforiza**
con fuente propia. Una sola vista demuestra Z, autoridad de Operaciones, y que esta lectura no
es el compuesto táctico ni la pantalla de llegada de OE6.

**Independent Test**: un trimestre muestra p95, recuento, alcance y `cumple` **en el mismo
bloque**. Expansión **no** ve el enlace. Un p95 de tres despachos se lee ausente.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones autenticado, **When** abre Latencia, **Then** ve el
   patrón Z: p95 a la izquierda, período y comparación a la derecha, evolución en diagonal,
   lectura de alcance y muestra abajo a la derecha.
2. **Given** el héroe, **When** se muestra, **Then** p95, recuento y `cumple` van **juntos**, y
   se lee que mide minutos de proceso, no milisegundos de algoritmo.
3. **Given** un p95 con muestra insuficiente, **When** se mira, **Then** el p95 se lee
   **ausente**, no como el despacho más lento.
4. **Given** un período sin despachos, **When** se mira, **Then** la zona está **vacía** con
   cobertura completa, no 0 min ni «meta cumplida».
5. **Given** las pantallas tácticas de Emergencias y las de OE6, **When** el cargo navega,
   **Then** esta pantalla **no** las reemplaza ni reutiliza su disposición.
6. **Given** un Director de Expansión, un Partner o un Director Financiero, **When** busca
   Latencia, **Then** no ve el enlace y no entra. El Gerente sí entra.
7. **Given** un Director Tecnológico, **When** busca Latencia, **Then** no ve el enlace y no
   entra (el GET de E3-02 no lo admite).

---

### User Story 2 - Ver registro y primer intento (Priority: P2)

El Director de Operaciones abre **Calidad**. El héroe es la tasa de error de registro con la
**lista de campos que se comprueban** y el `cumple` normativo. El visual es el primer intento
(grano de intento, no de caso). La lectura declara que un 0 % no significa «el expediente es
perfecto» y que E3-11 **no** cierra semáforo (`[CALIBRAR]`).

**Why this priority**: completa la mitad medible del «no se degrada» sin tocar capacidad. Va
después del MVP porque el semáforo de latencia ya demuestra el patrón.

**Independent Test**: los campos comprobados se leen junto a la tasa. Expansión no entra.
E3-11 no se pinta como verde/rojo cerrado.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones, **When** abre Calidad, **Then** ve tasa de error,
   campos comprobados y primer intento en Z.
2. **Given** la tasa de error, **When** se muestra, **Then** MUST listar **qué campos** mide.
   MUST NOT leerse como «registro perfecto» si la lista es corta.
3. **Given** el primer intento, **When** se muestra, **Then** se declara grano de **intento**.
   MUST NOT semaforizarse como KPI cerrado.
4. **Given** un Director Tecnológico o de Expansión, **When** busca Calidad, **Then** no ve el
   enlace.

---

### User Story 3 - Ver dónde la flota no da (Priority: P3)

El Director de Expansión (y el de Operaciones) abre **Capacidad**. El héroe es el ratio
demanda/capacidad **por condado**, con la flota **de ese período**. El visual separa condados
**sin capacidad** de los que están tensos. El apoyo plegado muestra pérdida de señal GPS con
recuento de posiciones. No hay eje de región ni mapa.

**Why this priority**: US1 dice si ya se degradó; esta dice **dónde va a degradarse**. Safety:
un condado con demanda y nadie que atienda.

**Independent Test**: un condado sin unidades vigentes se lee «sin capacidad», no infinito.
Tecnológico no entra. No hay mapa.

**Acceptance Scenarios**:

1. **Given** un Director de Expansión autenticado, **When** abre Capacidad, **Then** ve ratio
   por condado, condados sin capacidad y, al abrir el apoyo, pérdida de señal.
2. **Given** un condado con demanda y sin unidades vigentes en el período, **When** se mira,
   **Then** se lee **sin capacidad**, no un ratio ni un 0.
3. **Given** la lectura, **When** se muestra, **Then** declara que la capacidad es la flota
   **del período**, no la actual.
4. **Given** la pérdida de señal, **When** se abre el apoyo, **Then** el recuento de posiciones
   (o la cobertura) va junto a la cifra. MUST NOT parecer un 100 % sobre una muestra recortada.
5. **Given** un Director Tecnológico, un Partner o Finanzas, **When** busca Capacidad,
   **Then** no ve el enlace. Operaciones y Gerente sí entran.
6. **Given** la pantalla, **When** se recorre, **Then** **no** hay mapa, coordenadas ni agrupación
   por región.

---

### User Story 4 - Ver si el vecino puede cubrir (Priority: P4)

El Director de Expansión abre **Respaldo**. El héroe es la cobertura de respaldo. El visual
distingue vecinos **disponibles** de vecinos solo dados de alta. La tasa lleva **denominador**.
Operaciones **no** ve este enlace.

**Why this priority**: responde la pregunta que sigue a US3. Un solo informe; no mezclarlo en
Capacidad porque Operaciones no es autoridad de E3-08 y un ítem a medias rompería el menú.

**Independent Test**: el denominador está a la vista. Operaciones no ve el enlace. Un 0 % no se
finge cuando no hay vecinos que evaluar.

**Acceptance Scenarios**:

1. **Given** un Director de Expansión, **When** abre Respaldo, **Then** ve cobertura, desglose
   disponible vs alta, y denominador.
2. **Given** un vecino dado de alta y ocupado o fuera de servicio, **When** se mira, **Then**
   **no** cuenta como respaldo.
3. **Given** un período sin pares vecino evaluables, **When** se mira, **Then** está **vacío**,
   no 0 % como éxito.
4. **Given** un Director de Operaciones, **When** busca Respaldo, **Then** no ve el enlace. El
   Gerente sí entra.

---

### User Story 5 - Ni mapa, ni región fingida, ni los siete bloqueados (Priority: P1)

En las cuatro pantallas **no hay** mapa, coordenadas, nombre de implicado, eje de región, recuadro
de puesta en marcha, uptime, margen, pruebas ni reasignación cronometrada. No hay ítem gris
«próximamente». No hay 20 000 días en rojo.

**Why this priority**: el fallo sería silencioso y constitucional. Misma prioridad que el MVP.

**Independent Test**: ninguna de las cuatro contiene mapa, lat/lon, nombre propio, «región» como
eje, ni los siete informes bloqueados. El menú de un Partner está vacío de OE3.

**Acceptance Scenarios**:

1. **Given** cualquiera de las cuatro, **When** se recorre, **Then** **no** hay mapa, coordenadas
   ni ficha de persona.
2. **Given** Capacidad o Respaldo, **When** se agrupa, **Then** el grano es **condado**. MUST NOT
   inventar región.
3. **Given** el menú de cualquier cargo, **When** se busca puesta en marcha, maduración, cohorte,
   uptime, margen, pruebas o reasignación manual, **Then** **no** hay enlace ni recuadro.
4. **Given** OE6, **When** se recorre, **Then** **no** reaparece aquí como duplicado; los
   compartidos se leen en estas pantallas.

---

### Edge Cases

- **Período sin despachos.** Vacío, cobertura completa; no 0 min ni meta cumplida por ausencia.
- **p95 con n mínimo.** Ausente, no el máximo.
- **Condado con demanda y sin flota vigente.** Sin capacidad; no infinito ni error de pantalla.
- **Condado sin demanda.** Distinto de «sin capacidad».
- **Comparación contra una ventana que no existía.** Ausente con motivo, no «caída».
- **Una zona falla.** El resto sigue.
- **Tecnológico.** Sin enlaces OE3; sin 403 visible como ítem.
- **Operaciones buscando Respaldo.** Sin enlace; sin 403 visible como ítem.
- **Finanzas buscando margen (E3-09).** Sin enlace: el informe no se publica.
- **Sin autoridad.** Partner, Marketing, Éxito de Cliente: ningún enlace OE3.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente cuatro pantallas** —Latencia, Calidad,
  Capacidad, Respaldo— y MUST NOT añadir tarjetas a los compuestos tácticos ni a OE6.
- **FR-UI-002**: Las cuatro pantallas MUST mostrar **los siete informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT omitir uno publicado ni pintar los siete
  bloqueados.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**. MUST NOT ser una grilla de siete
  tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar **6–8 bloques** simultáneos. Capacidad MUST plegar
  E3-13.
- **FR-UI-005**: El **período** es obligatorio. La **comparación** (`ninguna`, mes anterior,
  mismo tramo del año anterior) es la única otra acción. Un cambio MUST refrescar todas las
  zonas. MUST NOT inventarse mapa, filtro de región ni exportación.
- **FR-UI-006**: Un período **sin despachos** MUST verse como vacío con cobertura completa,
  distinguible de 0 min y de error.
- **FR-UI-007**: E3-02 MUST mostrar **p95, recuento, `cumple` y alcance operativo en el mismo
  bloque**. MUST NOT usar el promedio como héroe ni comparar visualmente contra 100 ms.
- **FR-UI-008**: Un p95 no fiable MUST verse **ausente**, no como el despacho más lento.
- **FR-UI-009**: `cumple` booleano MUST pintarse solo cuando el backend lo envía. E3-11 MUST
  leerse sin semáforo cerrado.
- **FR-UI-010**: E3-10 MUST mostrar **qué campos comprueba** junto a la tasa.
- **FR-UI-011**: E3-11 MUST declararse en grano de **intento**, no de caso.
- **FR-UI-012**: E3-07 MUST agrupar por **condado**. Un condado con demanda y sin flota vigente
  MUST leerse **sin capacidad**, no como infinito ni 0.
- **FR-UI-013**: La lectura de E3-07 MUST declarar que la capacidad es la del **período**.
- **FR-UI-014**: E3-08 MUST mostrar **denominador** y MUST NOT contar como respaldo a un vecino
  solo dado de alta.
- **FR-UI-015**: E3-13 MUST mostrar recuento o cobertura de posiciones junto a la cifra.
- **FR-UI-016**: Las cuatro pantallas MUST NOT mostrar mapa, coordenadas, identidad de
  implicados, eje de región, recuadros de informes bloqueados ni botón de despacho o de abrir
  mercado.
- **FR-UI-017**: El menú MUST ser por pantalla y por cargo según la tabla de autoridad. MUST NOT
  haber ítems grises. Partner, Finanzas, Marketing y Éxito de Cliente MUST NOT ver OE3.
- **FR-UI-018**: Ver MUST NOT habilitar despachar, reasignar, abrir región ni mover flota. Abajo
  a la derecha hay **lectura**.
- **FR-UI-019**: Si el backend declara cobertura, recuento, alcance, falta o meta, la pantalla
  MUST mostrarlo junto a la cifra.
- **FR-UI-020**: Una comparación sin ventana anterior MUST mostrarse ausente **con motivo**.
- **FR-UI-021**: MUST NOT existir un enlace que fusione estas historias con los compuestos
  tácticos ni que duplique en OE6 los informes compartidos.
- **FR-UI-022**: Latencia MUST declararse distinta del compuesto táctico y de OE6 Llegada
  (proceso de asignación vs llegada a la persona).
- **FR-UI-023**: La cáscara Z MUST copiarse de OE6 (o de OE5 si se toma la de autoridad
  partida). MUST NOT extraerse un `shared/` en esta pasada.
- **FR-UI-024**: MUST NOT inventarse un informe de alcance geográfico, un mapa de cobertura
  regional ni un recuadro de «días hasta primera emergencia» contra 1970.
- **FR-UI-025**: El `DirectorTecnologico` MUST NOT ver ni entrar a ninguna pantalla de OE3.
- **FR-UI-026**: El `Gerente` MUST ver las cuatro pantallas. El Administrador MUST NOT
  sustituir a Operaciones, Expansión ni Tecnológico.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director de Operaciones identifica p95, recuento y si cumple la meta en
  **menos de 5 segundos** en Latencia, sin leer un párrafo.
- **SC-F02**: No existe un estado en el que se vea el p95 y no se vea, en el mismo bloque, el
  recuento de despachos.
- **SC-F03**: Un período sin despachos no se puede leer como 0 minutos ni como meta cumplida.
- **SC-F04**: Un p95 de tres despachos no se presenta como percentil cerrado.
- **SC-F05**: Un condado sin flota vigente no se puede leer como ratio 0 ni como infinito.
- **SC-F06**: Latencia se distingue de OE6 Llegada y del compuesto táctico: no reutiliza su
  disposición y declara alcance de proceso (minutos), no llegada a la persona.
- **SC-F07**: No hay mapa, coordenadas, nombres ni eje de región en ninguna de las cuatro.
- **SC-F08**: No hay recuadros ni menú de los siete informes bloqueados.
- **SC-F09**: Operaciones ve Latencia, Calidad y Capacidad. Expansión ve Capacidad y Respaldo.
  Tecnológico no ve OE3. El Gerente ve las cuatro. Un partner, ninguna.
- **SC-F10**: Una tasa nunca aparece sin denominador a la vista (E3-08, E3-10, E3-11).
- **SC-F11**: E3-11 no se puede leer como semáforo verde/rojo cerrado.
- **SC-F12**: Cada vista principal queda en **8 o menos** bloques.
- **SC-F13**: Un Director Financiero no encuentra margen operativo en el menú.
- **SC-F14**: Nadie puede leer «más de veinte mil días de puesta en marcha» ni un uptime
  inventado.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las cuatro; no es un listado táctico ni un mapa.
- **Zona Z**: métrica, período/comparación, visual grande, lectura.
- **Marca de parcial / recuento / p95 ausente / sin capacidad / dato escaso / sin calibrar**:
  impide leer un KPI cerrado o un 0 fingido.
- **Lectura**: el bloque de abajo a la derecha; no es un botón de expansión ni de despacho.
- **Ítem de menú por cargo**: presencia o ausencia; nunca deshabilitado.

---

## Assumptions

- El backend de los siete publicados está en servicio. Esta capa no calcula cifras.
- El período es obligatorio; no hay valor por defecto que sustituya desde / hasta /
  granularidad.
- «Por región» no es construible: se agrupa por condado, como ya decidió el backend. Esta spec
  no adelanta un mapa ni un informe de alcance geográfico.
- Los siete bloqueados siguen bloqueados. No se «rellenan» en UI.
- El patrón Z ya está demostrado en táctico, OE2, OE1, OE5 y OE6; esta capa lo copia (no extrae
  `shared/`).
- Los compuestos tácticos de Emergencias y Red Operativa no se tocan ni se retiran.
- OE6 no reimplementa los compartidos; esta capa los muestra.
- No hay exportación ni programación de envío.
- El mínimo de muestra lo resuelve el backend. Esta capa no ofrece un control extra de umbral.
- El frontend de OE4 ya está implementado en su capa.
- El seed de `Gerente` y los agujeros de dato de origen no son esta capa.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Compuestos tácticos de Emergencias y Red Operativa | Ya existen |
| Pantallas de OE6 (llegada a la persona) | Dueño: OE6; aquí solo los compartidos de proceso |
| Informes de OE4 | Dueño: OE4 |
| Mapa, coordenadas, identidad | Constitución |
| Eje de región / informe de alcance geográfico | No hay relación región↔condado; no se inventa |
| E3-04, E3-05, E3-06 | Sin fecha real de arranque regional |
| E3-01, E3-09, E3-14 | Fuente externa |
| E3-12 | Suceso no registrado |
| Acciones de despacho o de expansión | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Partner, Finanzas, Éxito de Cliente, Marketing como autoridad | No están en §4.3 para estos siete |
| Cambiar OpenAPI, SQL o permisos del backend | Depends-on |
| Extraer `shared/` de la cáscara Z | Fuera de esta pasada |
| Frontend de OE4 | Otra capa |
| Tablero integral CU-E01 | Contrato §11 |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período + comparación, menú por rol sin ítems grises. SC-F01, SC-F12. |
| **Functional Suitability** | Muestra los siete publicados; declara inmedible lo bloqueado. Vacío ≠ 0; p95 ausente; sin capacidad ≠ infinito; `cumple` solo si es booleano. |
| **Security** | Reutiliza quién entra, **por pantalla**. Partner y Finanzas fuera. Sin identidad. Administrador no sustituye. |
| **Safety** | Un 0 min fingido, un p95 de 3 despachos, un ratio infinito o un mapa de personas induciría una decisión de flota o despacho falsa. FR-UI-006/008/012/016 lo impiden. Esta capa **no despacha**; sí evita mentir al que sí mueve capacidad. |
| **Reliability** | Vacío ≠ 0; fallo de zona aislado; comparación ausente se declara. |
| **Maintainability** | Capa `frontend/` separada; copia Z, sin extraer librería. |
| **Performance Efficiency** | Heredada del backend. Umbral: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio externo en esta capa. |
| **Flexibility** | Agrupa por condado porque la región no es construible. Se declara; no se inventa geografía. La mitad «escalar» del objetivo **no se finge**. |

**Traceability**: índice [`../OE3-escalabilidad-multiregion.md`](../OE3-escalabilidad-multiregion.md).
