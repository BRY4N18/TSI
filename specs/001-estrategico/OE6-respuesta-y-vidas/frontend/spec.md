# Feature Specification: OE6 — Tiempo de Respuesta y Seguridad de Vidas — Frontend

**Feature Branch / capa**: `001-estrategico/OE6-respuesta-y-vidas/frontend`

**Created**: 2026-08-18

**Status**: Implemented (2026-08-18). Cuatro pantallas Z (`llegada`, `diagnostico`, `ejecucion`, `personas`); un guard `DirectorOperaciones` ∪ `Gerente`; 12 GET. Sin mapa, ETA ni recuadros de OE3.

**Depends-on**: [`../backend/spec.md`](../backend/spec.md), su contrato OpenAPI y
[`../../acceso-estrategico.md`](../../acceso-estrategico.md) §4.6. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que los compuestos tácticos y que OE1/OE2/OE5) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

**Input**: continuar la capa estratégica con las pantallas de los doce informes ya publicados
de OE6; no pintar mapa ni identidad; no reimplementar informes de OE3; no tratar un período
vacío o un p95 de tres casos como KPI cerrado.

---

## Contexto

El backend de OE6 **ya publica los doce informes**. Esta capa no calcula nada: pinta lo que el
contrato ya corrige (mediana y p95, ventana comparada, contraste con meta, agrupación por
**condado** — no por región).

Entrega **cuatro pantallas nuevas** de lectura de empresa. No se mezclan con:

- los compuestos tácticos de Emergencias (los 26 OT21–OT25);
- el tablero de OE3 (capacidad / multi-región) ni el de OE4 (inteligencia);
- un mapa, una lista de nombres o un recuadro de «ETA».

Las cifras tácticas y estas **difieren a propósito**: aquí hay ventana comparada, percentil y
meta BSC. MUST distinguirse en menú y en la propia pantalla.

### Una sola autoridad, cuatro historias

A diferencia de OE1 y OE5, **no hay autoridad partida por materia**. [`acceso-estrategico.md`](../../acceso-estrategico.md)
§4.6: los doce informes son de Emergencias. Entran `DirectorOperaciones` y `Gerente`.

| Materia | Quién entra | Pantalla |
|---|---|---|
| Cuánto tarda en llegar la ayuda | `DirectorOperaciones` · `Gerente` | **Llegada** |
| En qué tramo se va ese tiempo | `DirectorOperaciones` · `Gerente` | **Diagnóstico** |
| Qué falla en la ejecución | `DirectorOperaciones` · `Gerente` | **Ejecución** |
| Qué pasó con la persona atendida | `DirectorOperaciones` · `Gerente` | **Personas** |
| Partner, Finanzas, Marketing, Éxito de Cliente | **nadie** | — |

Las cuatro pantallas **MUST** aparecer juntas en el menú para esos dos cargos. Un ítem gris
para el resto **MUST NOT** existir. Un partner **MUST NOT** ver ninguna. El Administrador no
sustituye al Director de Operaciones.

Ver **MUST NOT** habilitar a despachar, reasignar ni cerrar un caso. Abajo a la derecha hay
**lectura**, no una acción de despacho.

### El ojo recorre el patrón Z

1. Arriba a la izquierda: métrica principal (héroe) — **mediana y p95 juntas** cuando el
   informe es de tiempo, con recuento y cobertura.
2. Arriba a la derecha: **período** (obligatorio) y **comparación** de igual longitud (`ninguna`,
   mes anterior, mismo tramo del año anterior).
3. Diagonal: el visual más grande (severidad, tramos, fallos o evidencia).
4. Abajo a la derecha: la **lectura** — qué implica el número (casos sin llegada aparte,
   referencia histórica no ETA, denominador de tasas, dato escaso).

**No hay mapa ni fichas.** El backend no entrega coordenadas ni identidad de implicados. El
Director de Operaciones **tampoco** las ve: es constitucional, no un filtro de rol.

### Lo que no se puede mostrar

Un promedio como héroe **miente** en tiempos de respuesta: la cola larga lo arrastra. MUST
pintar **mediana y p95**. Si el p95 no es fiable (muestra mínima), MUST verse **ausente**, no
como «el caso más lento disfrazado de percentil».

Los casos **sin llegada** MUST quedar **fuera del tiempo** y **contados aparte**. Pintarlos
como cero minutos inflaría el desempeño.

Un período **sin casos** MUST verse como **vacío con cobertura completa**, no como 0 min ni
como error. En este dominio, «no hubo accidentes» es una noticia distinta de «no se pudo
medir».

La desviación de llegada MUST leerse contra el **histórico comparable** (condado × severidad),
nunca como «ETA vs real». El sistema no calcula ETA.

Las tasas de rechazo, aborto y cierre forzado MUST llevar **denominador a la vista**. Un 12 %
sobre 8 casos no es el mismo juicio que sobre 8 000.

E6-05 y E6-09 arrastran definiciones abiertas en origen. La pantalla MUST **declarar qué
definición mide**, no ocultar el aviso.

El impacto humano MUST **no contar como cero** a quien no tiene víctimas/heridos/fallecidos
registrados. Las escaladas y la evidencia, si el período está casi vacío, MUST decir **dato
escaso**, no «0 % nunca se escala».

Los informes de OE3 que también sirven a este objetivo **no se pintan aquí**. Se leen en OE3.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Llegada** | ¿Cuánto tarda en llegar la ayuda? | Mediana + p95 + recuento + cobertura | Tiempo por severidad | Sin llegada, aparte; comparación de ventanas | — |
| **Diagnóstico** | ¿En qué tramo se va ese tiempo? | Tramos del ciclo (suma = total) | Automático vs manual | Desviación vs **histórico**, no ETA | — |
| **Ejecución** | ¿Qué falla al despachar? | Envejecimiento de abiertos | Rechazo/timeout por unidad + abortos | Cierres forzados: **qué definición** se mide | Tasas con denominador |
| **Personas** | ¿Qué pasó con quien esperaba? | Impacto humano agregado | Escaladas en sitio | Cobertura de evidencia en **cerrados** | Dato escaso declarado |

Llegada tiene dos informes. Cabe en Z.

Diagnóstico tiene tres. La desviación MUST quedar en lectura para no pasar de 6–8 bloques.

Ejecución tiene cuatro. Rechazo y abortos pueden compartir el visual o ir uno al apoyo plegado.

Personas tiene tres. El impacto es el héroe; evidencia y escaladas no se disfrazan de 0 %.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Operaciones ve cuánto tarda la ayuda (Priority: P1) 🎯 MVP

El Director de Operaciones abre **Llegada**, fija un período y ve de inmediato la **mediana y
el p95** con el recuento de casos que sostienen esas cifras. El visual desglosa por severidad
(incluido «Desconocido»). Abajo lee cuántos casos **no tuvieron llegada**. Un período sin casos
se lee vacío, no como 0 minutos.

**Why this priority**: E6-01 es el indicador BSC del objetivo. Una sola vista demuestra Z, el
percentil junto al recuento, y que esta lectura no es el compuesto táctico de Emergencias.

**Independent Test**: un trimestre muestra mediana, p95 y recuento **en el mismo bloque**. Los
casos sin llegada no bajan el tiempo. Finanzas **no** ve el enlace.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones autenticado, **When** abre Llegada, **Then** ve el
   patrón Z: mediana y p95 a la izquierda, período y comparación a la derecha, severidad en
   diagonal, lectura de «sin llegada» abajo a la derecha.
2. **Given** el héroe, **When** se muestra, **Then** mediana, p95 y recuento van **juntos**.
   MUST NOT haber un promedio como cifra principal.
3. **Given** un p95 con muestra insuficiente, **When** se mira, **Then** el p95 se lee
   **ausente**, no como el caso más lento.
4. **Given** casos abiertos o sin llegada, **When** se mira, **Then** están **fuera del tiempo**
   y **contados aparte**. MUST NOT pintarse como 0 min.
5. **Given** un período sin casos, **When** se mira, **Then** la zona está **vacía** con
   cobertura completa, no 0 min ni error.
6. **Given** las pantallas tácticas de Emergencias, **When** el cargo navega, **Then** esta
   pantalla **no** las reemplaza ni reutiliza su disposición.
7. **Given** un Partner, un Director Financiero o un Gerente de Éxito de Cliente, **When** busca
   Llegada, **Then** no ve el enlace y no entra. El Gerente sí entra.

---

### User Story 2 - Entender dónde se va ese tiempo (Priority: P2)

El Director abre **Diagnóstico**. El héroe son los tramos del ciclo (asignar, salir, circular)
cuya suma es el total. El visual compara automático vs manual. La lectura es la desviación
frente al **histórico del condado y la severidad**, no un ETA.

**Why this priority**: sin esto, la mediana de US1 es un termómetro sin diagnóstico.

**Independent Test**: los tramos se leen como partes de un total. La desviación no se titula
ETA. Finanzas no entra.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones, **When** abre Diagnóstico, **Then** ve tramos, origen
   de asignación y desviación vs histórico.
2. **Given** los tramos, **When** se muestran, **Then** se declara que **suman el tiempo total**
   de los casos que completaron esos hitos; los hitos no alcanzados se excluyen de ese tramo.
3. **Given** la desviación, **When** se lee, **Then** MUST decir **histórico comparable**. MUST
   NOT decir ETA ni coordenadas.
4. **Given** un condado×severidad sin muestra suficiente, **When** se mira la desviación,
   **Then** la referencia está **ausente**, no es cero.
5. **Given** un Partner, **When** busca Diagnóstico, **Then** no ve el enlace.

---

### User Story 3 - Ver qué falla al despachar (Priority: P3)

El Director abre **Ejecución**. El héroe es el envejecimiento de casos **abiertos**. El visual
muestra rechazo/timeout por unidad y abortos, **cada tasa con su denominador**. La lectura
declara **qué definición** usan los cierres forzados. Un período sin abortos se lee vacío
completo, no 0 %.

**Why this priority**: aísla las definiciones abiertas (#34, #36) para no bloquear el MVP.

**Independent Test**: ninguna tasa aparece sin denominador. Un 0 % de abortos no se finge cuando
no hubo misiones. Partner fuera.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones, **When** abre Ejecución, **Then** ve envejecimiento,
   tasas de fallo y la declaración de definición de cierres forzados.
2. **Given** una tasa, **When** se muestra, **Then** el **denominador está a la vista**.
3. **Given** un período sin abortos, **When** se mira, **Then** está **vacío** (cobertura
   completa), no «0 % de abortos» como éxito medido.
4. **Given** los cierres forzados, **When** se leen, **Then** se declara si miden el indicador
   de despacho o el retiro manual — no se oculta que no son lo mismo.
5. **Given** un caso abierto, **When** se mira el envejecimiento, **Then** **no** aparece como
   cerrado.

---

### User Story 4 - Ver el resultado sobre la persona (Priority: P4)

El Director abre **Personas**. El héroe es el impacto humano agregado **sin contar como cero** a
quien no tiene dato. El visual son las escaladas en sitio (dato escaso si aplica). La lectura es
la cobertura de evidencia **solo en cerrados**. No hay nombres ni fotos identificables.

**Why this priority**: es lo que distingue OE6 de OE3 (proceso vs persona). Va última porque el
histórico de evidencia/escaladas está casi vacío.

**Independent Test**: un 0 de escaladas se lee como dato escaso, no como «nunca se escala».
Identidad ausente. Partner fuera.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones, **When** abre Personas, **Then** ve impacto, escaladas
   y evidencia en Z.
2. **Given** casos sin víctimas/heridos/fallecidos registrados, **When** se mira el impacto,
   **Then** **no** cuentan como cero.
3. **Given** un período con pocas o ninguna escalada, **When** se mira, **Then** se declara
   **dato escaso**, no un 0 % de tablero.
4. **Given** la evidencia, **When** se muestra, **Then** solo casos **cerrados**; sin identidad
   del implicado ni del técnico.
5. **Given** un Partner, **When** busca Personas, **Then** no ve el enlace.

---

### User Story 5 - Ni mapa, ni nombres, ni ETA, ni OE3 (Priority: P1)

En las cuatro pantallas **no hay** mapa, coordenadas, nombre de implicado, recuadro de ETA ni
informes de OE3. El tablero no ofrece «un tiempo de 0 min» porque no hubo casos, ni un p95 con
tres filas.

**Why this priority**: el fallo sería silencioso y constitucional. Misma prioridad que el MVP.

**Independent Test**: ninguna de las cuatro contiene mapa, lat/lon, nombre propio ni la palabra
ETA como cifra. No hay recuadros de informes de OE3.

**Acceptance Scenarios**:

1. **Given** cualquiera de las cuatro, **When** se recorre, **Then** **no** hay mapa, coordenadas
   ni ficha de persona.
2. **Given** Diagnóstico, **When** se lee la desviación, **Then** **no** se titula ETA.
3. **Given** el menú, **When** se busca capacidad de OE3, **Then** no hay enlace que la
   reimplemente dentro de OE6.

---

### Edge Cases

- **Período sin casos.** Vacío, cobertura completa; no 0 min.
- **p95 con n mínimo.** Ausente, no el máximo.
- **Caso registrado en un mes y llegada en el siguiente.** Cuenta en el mes del **registro**.
- **Varios despachos.** El tiempo usa la **primera** llegada.
- **Caso descartado o fusionado.** No entra.
- **Comparación contra una agrupación que no existía.** Ausente con motivo, no «caída».
- **Una zona falla.** El resto sigue.
- **Sin autoridad.** Partner y Finanzas no ven enlaces.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente cuatro pantallas** —Llegada, Diagnóstico,
  Ejecución, Personas— y MUST NOT añadir tarjetas a los compuestos tácticos de Emergencias.
- **FR-UI-002**: Las cuatro pantallas MUST mostrar **los doce informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT omitir uno publicado ni pintar informes de OE3.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**. MUST NOT ser una grilla de doce
  tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar **6–8 bloques** simultáneos.
- **FR-UI-005**: El **período** es obligatorio. La **comparación** (`ninguna`, mes anterior,
  mismo tramo del año anterior) es la única otra acción. Un cambio MUST refrescar todas las
  zonas. MUST NOT inventarse mapa, filtro de unidad como acción principal ni exportación.
- **FR-UI-006**: Un período **sin casos** MUST verse como vacío con cobertura completa,
  distinguible de 0 min y de error.
- **FR-UI-007**: Los tiempos MUST mostrar **mediana, p95 y recuento en el mismo bloque**. MUST
  NOT usar el promedio como héroe.
- **FR-UI-008**: Un p95 no fiable MUST verse **ausente**, no como el caso más lento.
- **FR-UI-009**: Los casos sin llegada MUST declararse **aparte** y MUST NOT entrar al tiempo
  como 0 min.
- **FR-UI-010**: La desviación MUST leerse como **histórico comparable**. MUST NOT titularse ETA.
- **FR-UI-011**: Toda tasa MUST mostrar su **denominador**.
- **FR-UI-012**: Un período sin abortos MUST verse **vacío**, no 0 % de abortos como éxito.
- **FR-UI-013**: Cierres forzados MUST declarar **qué definición** se está midiendo.
- **FR-UI-014**: El impacto humano MUST NOT contar como cero a quien no tiene dato registrado.
- **FR-UI-015**: Escaladas y evidencia con muestra escasa MUST declararse **escasas**, no 0 %.
- **FR-UI-016**: Las cuatro pantallas MUST NOT mostrar mapa, coordenadas, identidad de
  implicados, identidad de técnicos, recuadros de OE3 ni botón de despacho.
- **FR-UI-017**: Las cuatro MUST ser visibles para `DirectorOperaciones` y `Gerente`. El resto
  MUST NOT verlas en el menú ni entrar.
- **FR-UI-018**: Ver MUST NOT habilitar despachar, reasignar ni cerrar. Abajo a la derecha hay
  **lectura**, no una acción de despacho.
- **FR-UI-019**: Si el backend declara cobertura, recuento, alcance, falta o meta, la pantalla
  MUST mostrarlo junto a la cifra.
- **FR-UI-020**: Una comparación sin ventana anterior MUST mostrarse ausente **con motivo**.
- **FR-UI-021**: MUST NOT existir un enlace que fusione estas historias con los compuestos
  tácticos de Emergencias ni con OE3.
- **FR-UI-022**: Llegada MUST declararse distinta del compuesto táctico (percentil + ventana
  comparada, no recorte operativo).
- **FR-UI-023**: El cascarón Z MUST copiarse de OE5/OE1. MUST NOT extraerse un `shared/` en
  esta pasada.
- **FR-UI-024**: La agrupación geográfica MUST ser la que envía el backend (condado). MUST NOT
  inventar un eje de región ni un mapa.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director de Operaciones identifica mediana, p95 y recuento en **menos de 5
  segundos** en Llegada, sin leer un párrafo.
- **SC-F02**: No existe un estado en el que se vea el tiempo y no se vea, en el mismo bloque, el
  recuento de casos.
- **SC-F03**: Un período sin casos no se puede leer como 0 minutos de respuesta.
- **SC-F04**: Un p95 de tres casos no se presenta como percentil cerrado.
- **SC-F05**: La desviación no se puede leer como ETA.
- **SC-F06**: Llegada se distingue del compuesto táctico de Emergencias: no reutiliza su
  disposición y declara percentil y ventana comparada.
- **SC-F07**: No hay mapa, coordenadas ni nombres en ninguna de las cuatro.
- **SC-F08**: No hay recuadros de informes de OE3.
- **SC-F09**: Operaciones y Gerente acceden a las **cuatro**. Un partner a ninguna. Finanzas a
  ninguna.
- **SC-F10**: Una tasa nunca aparece sin denominador a la vista.
- **SC-F11**: Un período vacío de abortos no se parece a un 0 % de abortos medido.
- **SC-F12**: Cada vista principal queda en **8 o menos** bloques.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las cuatro; no es un listado táctico ni un mapa.
- **Zona Z**: métrica (mediana+p95), período/comparación, visual grande, lectura.
- **Marca de parcial / recuento / p95 ausente / sin llegada / dato escaso**: impide leer un KPI
  cerrado o un 0 fingido.
- **Lectura**: el bloque de abajo a la derecha; no es un botón de despacho.

---

## Assumptions

- El backend de los doce publicados está en servicio. Esta capa no calcula cifras.
- El período es obligatorio; no hay valor por defecto que sustituya desde / hasta /
  granularidad.
- «Por región» no es construible: se agrupa por condado, como ya decidió el backend. Esta spec
  no adelanta un mapa.
- Las definiciones abiertas de rechazo y cierre forzado se **declaran**, no se resuelven aquí.
- El patrón Z ya está demostrado en táctico, OE2, OE1 y OE5; esta capa lo copia (no extrae
  `shared/`).
- Los compuestos tácticos de Emergencias no se tocan ni se retiran.
- Los informes de OE3 no se reimplementan.
- No hay exportación ni programación de envío.
- El mínimo de muestra lo resuelve el backend. Esta capa no ofrece un control extra de umbral.
- El frontend de OE4 ya está implementado en su capa.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Compuestos tácticos de Emergencias | Ya existen |
| Informes de OE3 (capacidad, latencia de red, etc.) | Dueño: OE3 |
| Mapa, coordenadas, identidad | Constitución / §4.6 |
| ETA calculado | El sistema no lo tiene; la referencia es histórica |
| Eje de región | No hay relación región↔condado |
| Acciones de despacho | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Partner, Finanzas, Éxito de Cliente como autoridad | No están en §4.6 |
| Cambiar OpenAPI, SQL o permisos del backend | Depends-on |
| Extraer `shared/` de la cáscara Z | Fuera de esta pasada |
| Frontend de OE4 | Otra capa |
| Tablero integral CU-E01 | Contrato §11 |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período + comparación, menú por rol. SC-F01, SC-F12. |
| **Functional Suitability** | Muestra mediana/p95, recuento, vacío ≠ 0, histórico ≠ ETA, tasas con denominador. No inventa región ni mapa. |
| **Security** | Reutiliza quién entra. Partner fuera. Sin identidad. |
| **Safety** | Un tiempo de 0 min fingido, un p95 de 3 casos o un mapa de personas induciría una decisión de despacho falsa. FR-UI-006/008/016 lo impiden. Esta capa **no despacha**; sí evita mentir al que sí despacha. |
| **Reliability** | Vacío ≠ 0; fallo de zona aislado; comparación ausente se declara. |
| **Maintainability** | Capa `frontend/` separada; copia Z de OE5, sin extraer librería. |
| **Performance Efficiency** | Heredada del backend. Umbral: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio externo en esta capa. |
| **Flexibility** | Agrupa por condado porque la región no es construible. Se declara; no se inventa geografía. |

**Traceability**: índice [`../OE6-respuesta-y-vidas.md`](../OE6-respuesta-y-vidas.md).
