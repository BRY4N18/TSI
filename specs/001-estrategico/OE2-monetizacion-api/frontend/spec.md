# Feature Specification: OE2 — Monetización del Ecosistema de APIs — Frontend

**Feature Branch / capa**: `001-estrategico/OE2-monetizacion-api/frontend`

**Created**: 2026-08-18

**Status**: Implemented — frontend (2026-08-18). Tres pantallas Z; E2-06 sin recuadro.

**Depends-on**: [`../backend/spec.md`](../backend/spec.md), su contrato OpenAPI y
[`../../acceso-estrategico.md`](../../acceso-estrategico.md) §4.2. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que los compuestos tácticos) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

**Input**: continuar la capa estratégica de OE2 con las pantallas de los diez informes ya
publicados; no pintar disponibilidad.

---

## Contexto

El backend de OE2 **ya publica diez informes** y responde 404 a la disponibilidad (E2-06). Esta
capa no calcula nada: pinta lo que el contrato ya corrige.

Entrega **tres pantallas nuevas** de lectura de empresa. No se mezclan con:

- los compuestos tácticos de Partners (Consumo / Incorporación / Entrega);
- el portal acotado del partner;
- la consola de logs ni las métricas operativas.

Las cifras tácticas y estas **difieren a propósito**: aquí hay ventana comparada, meta BSC y
agregado de **todo** el ecosistema. MUST distinguirse en menú y en la propia pantalla, para que
nadie compare un p95 táctico de un partner con el p95 estratégico como si midieran lo mismo.

### La autoridad está partida

No hay un tablero único «OE2» que fusione consumo y dinero. [`acceso-estrategico.md`](../../acceso-estrategico.md)
§4.2 y FR-OE2-006/007:

| Materia | Quién entra | Pantalla |
|---|---|---|
| Uso y respuesta | `DirectorTecnologico` · `Gerente` | **Uso de la API** |
| Dinero | esos **más** `DirectorFinanciero` | **Dinero de la API** |
| Ecosistema | `DirectorTecnologico` · `Gerente` | **Ecosistema** |
| Cualquier rol de partner | **nadie** | — |

El `DirectorFinanciero` **MUST NOT** ver Uso ni Ecosistema. Un partner **MUST NOT** ver ninguna:
son cifras de competidores, no PII. El Administrador no sustituye a estas autoridades en esta
capa (no está en §4.2). El `Gerente` ve las tres.

Cada cargo **MUST** ver **solo sus enlaces**. Un ítem gris o un 403 después de entrar descubriría
la superficie.

### El ojo recorre el patrón Z

1. Arriba a la izquierda: contexto o métrica principal (héroe), con meta BSC cuando el backend
   la declara.
2. Arriba a la derecha: **período** (obligatorio) y **comparación** de igual longitud (`ninguna`,
   mes anterior, mismo tramo del año anterior). Son las únicas acciones de esta capa.
3. Diagonal: el visual más grande.
4. Abajo a la derecha: la **lectura** — qué implica el número. Ver no habilita a facturar, retirar
   una versión ni revocar una credencial.

**No hay fichas de llamada ni de persona.** El backend no entrega IP, secreto, hash ni contacto
técnico. Los partners se nombran por organización.

### Lo que no se puede mostrar solo

Hoy hay **dieciocho llamadas** de detalle. Un p95 de dos observaciones **puede ser el máximo**.
El backend ya envía media, p95, muestras y si el percentil es fiable; esta capa MUST pintarlas
**juntas**. Un héroe de «p95 = 90 ms» y las muestras en una nota es el defecto que el backend
acaba de impedir.

E2-01 y E2-02 salen **parciales** (falta el precio del plan de API). Pintarlos como mix de
ingresos completo mentiría. MUST verse `cobertura: parcial` y qué falta **junto a la cifra**.

E2-08 es **facturable, no cobrado**. MUST leerse así. Un importe sin llamadas, cupo y precio no
se puede disputar.

E2-06 **no tiene pantalla ni recuadro**. Inventar un 100 % de disponibilidad porque no hubo
filas de error es exactamente lo que el backend prohíbe con el 404.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Uso de la API** | ¿Se usa y cómo responde? | Adopción (partners con ≥1 llamada / con acceso), meta ≥70 % `[CALIBRAR]` a la vista | Taxonomía **4xx ≠ 5xx** | Consumo frente al cupo; ceros visibles | Latencia: p95, media y muestras **en el mismo bloque**, con marca de fiabilidad |
| **Dinero de la API** | ¿Cuánto se puede facturar y qué peso tiene? | Excedente facturable: llamadas, cupo, precio e importe | Partners no tarificables **declarados**, no ocultos | Alcance: no afirma cobro | Participación y MRR por línea con **parcial** y el precio que falta |
| **Ecosistema** | ¿Quién usa qué contrato y si crece? | Crecimiento: primeras llamadas **exitosas**, no altas de credencial | Adopción por **(servicio, versión)**, versión **declarada derivada** | Comparativa: volumen, error, latencia; ceros visibles | — |

Uso tiene cuatro informes. La latencia MUST quedar en apoyo para no pasar de 6–8 bloques.

Dinero tiene tres. Participación y MRR MUST quedar en apoyo: el BSC de monetización más
accionable hoy es el excedente, que sí tiene precio.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Tecnológico ve si la API se usa (Priority: P1) 🎯 MVP

El Director Tecnológico abre **Uso de la API**, fija un período y ve de inmediato la adopción
frente a la meta. El visual grande separa 4xx de 5xx. Abajo, quién se pasa de cupo. Puede abrir
la latencia: p95, media y muestras viajan juntas; si la muestra no alcanza, se lee que el
percentil **no es fiable** y la fila **sigue**.

**Why this priority**: contiene dos indicadores BSC (adopción y latencia) y es la rebanada que
el backend ya sirve sin cruzar facturación. Una sola vista demuestra Z, el trío de latencia y
que esta lectura no es el compuesto táctico de Partners.

**Independent Test**: un período con pocas llamadas muestra p95, media y muestras **en el mismo
bloque**, con la marca de no fiable. Un partner con acceso y cero llamadas está en el
denominador y no en el numerador, y aparece en consumo con **cero**. Un partner autenticado
**no** ve el enlace. El compuesto táctico de Partners **sigue** en su menú, distinto.

**Acceptance Scenarios**:

1. **Given** un Director Tecnológico autenticado, **When** abre Uso de la API, **Then** ve el
   patrón Z: métrica a la izquierda, período y comparación a la derecha, visual grande,
   lectura abajo a la derecha.
2. **Given** la adopción, **When** se muestra, **Then** el denominador son partners **con
   acceso concedido**, no el catálogo entero, y la meta ≥70 % está **a la vista**.
3. **Given** la latencia, **When** se abre el apoyo, **Then** p95, media y muestras están **en
   el mismo bloque**. MUST NOT haber un héroe de p95 solo.
4. **Given** un endpoint bajo la muestra mínima, **When** se mira, **Then** el percentil se lee
   **ausente o no fiable** y la fila no desaparece.
5. **Given** 4xx y 5xx, **When** se mira la taxonomía, **Then** hay **dos** clases. MUST NOT
   existir un total «errores» que las sume.
6. **Given** un partner con acceso y cero llamadas, **When** se pide consumo, **Then** aparece
   con **cero**, no omitido.
7. **Given** las pantallas tácticas de Partners, **When** el Director navega, **Then** esta
   pantalla **no** las reemplaza ni reutiliza su disposición. Se declara que el período
   comparado **no es** el recorte táctico.
8. **Given** un Partner, un Desarrollador de APIs o un Director Financiero, **When** busca Uso
   de la API, **Then** no ve el enlace y no entra.

---

### User Story 2 - Ver cuánto dinero produce la API (Priority: P2)

El Director Financiero (también Tecnológico y Gerente) abre **Dinero de la API**. El héroe es
el excedente **facturable**: llamadas, cupo, precio e importe juntos. El visual grande lista a
quien no se puede tarificar. Abajo se lee que **no afirma cobro**. Participación y MRR se
abren en apoyo con la etiqueta **parcial** y el precio de plan API que falta.

**Why this priority**: es la razón de ser del objetivo. Va después de US1 porque el consumo se
mira antes de tasarlo.

**Independent Test**: el excedente muestra los tres componentes. Un partner sin precio no
desaparece. Participación no se lee como mix completo. El Tecnológico **entra**. El partner
**no**. El Financiero **no** ve Uso ni Ecosistema.

**Acceptance Scenarios**:

1. **Given** un Director Financiero autenticado, **When** abre Dinero de la API, **Then** el
   héroe es el excedente con llamadas, cupo, precio e importe.
2. **Given** el excedente, **When** se lee el alcance, **Then** declara que es **facturable, no
   cobrado**. MUST NOT usarse la palabra «cobrado» como afirmación.
3. **Given** un partner no tarificable, **When** se mira el visual, **Then** está **declarado**.
   MUST NOT omitirse.
4. **Given** participación o MRR, **When** se abren, **Then** se ve `parcial` y `falta` nombra
   el precio del plan de API. MUST NOT pintarse como ingreso completo.
5. **Given** un Director Tecnológico o un Gerente, **When** busca Dinero, **Then** lo ve y
   entra (FR-OE2-006).
6. **Given** un Director Financiero, **When** mira el menú, **Then** ve Dinero y **no** Uso ni
   Ecosistema.
7. **Given** un Partner, **When** busca Dinero, **Then** no lo ve y no entra.

---

### User Story 3 - Ver la salud del ecosistema (Priority: P3)

El Director Tecnológico abre **Ecosistema**. El héroe es cuántos partners hicieron su
**primera llamada exitosa** en el período — no cuántas credenciales se emitieron. El visual
grande reparte llamadas por servicio y versión, y dice que la versión **se deriva**. Abajo, la
comparativa con ceros a la vista. Dos servicios con `'v1'` son **dos** agrupaciones.

**Why this priority**: E2-09 es indicador BSC y sostiene el Principio VI: no se retira una
versión a ciegas.

**Independent Test**: dos servicios `'v1'` no se colapsan. Una credencial del mes sin 2xx no
incrementa el héroe. El partner no entra.

**Acceptance Scenarios**:

1. **Given** el Director Tecnológico, **When** abre Ecosistema, **Then** el héroe es el
   crecimiento por primera 2xx, el visual es adopción por (servicio, versión) y la comparativa
   está abajo a la derecha.
2. **Given** dos servicios con etiqueta `'v1'`, **When** se muestra la adopción, **Then** hay
   **dos** agrupaciones. MUST NOT colapsarlas en una barra `'v1'`.
3. **Given** la adopción, **When** se muestra, **Then** declara que la versión es **derivada**.
4. **Given** una credencial emitida sin llamadas 2xx, **When** se mira el crecimiento, **Then**
   **no** incrementa. MUST NOT contarse el alta de credencial.
5. **Given** un partner con acceso y cero llamadas, **When** se mira la comparativa, **Then**
   aparece en cero.
6. **Given** un Partner o un Director Financiero, **When** busca Ecosistema, **Then** no lo ve
   y no entra.

---

### User Story 4 - La disponibilidad no se finge (Priority: P1)

En las tres pantallas **no hay** recuadro, pestaña ni enlace de disponibilidad. El tablero no
ofrece un 100 % porque el log estuvo callado.

**Why this priority**: el fallo sería silencioso y grave. Misma prioridad que el MVP de US1:
si se pinta de más, US1 miente.

**Independent Test**: ninguna de las tres contiene un indicador de uptime. No hay ruta de
pantalla para E2-06.

**Acceptance Scenarios**:

1. **Given** cualquiera de las tres pantallas, **When** se recorre, **Then** **no** hay un
   bloque de disponibilidad ni un 99,9 %.
2. **Given** un período sin llamadas, **When** se muestra Uso, **Then** se lee **vacío**, no
   latencia 0 ni uptime 0 ni uptime 100.

---

### Edge Cases

- **Período vacío.** Vacío explícito, no 0 ms ni 0 % de uptime.
- **Dieciocho llamadas.** No se ocultan denominadores ni la marca de fiabilidad.
- **Partner con credencial y cero llamadas.** En denominador de adopción; en consumo con cero.
- **Comparación año anterior sin ventana.** Se lee la comparación **ausente con motivo**, no un
  error de pantalla.
- **Cobertura parcial.** Participación y MRR no se maquillan de completas.
- **Una zona falla.** El resto sigue; la zona fallida lo dice.
- **Sin autoridad.** Partner y roles ajenos no entran; el Financiero no ve Uso ni Ecosistema.
- **Dato sensible.** Ninguna pantalla muestra IP, secreto, hash ni contacto, **tampoco al
  Gerente**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Uso de la API, Dinero
  de la API, Ecosistema— y MUST NOT añadir tarjetas a los compuestos tácticos de Partners, al
  portal del partner ni a la consola operativa.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los diez informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT inventar un undécimo (disponibilidad) ni
  omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**. MUST NOT ser una grilla de diez
  tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar **6–8 bloques** simultáneos. En Uso, la latencia MUST
  quedar en apoyo. En Dinero, participación y MRR MUST quedar en apoyo.
- **FR-UI-005**: El **período** es obligatorio. La **comparación** (`ninguna`, mes anterior,
  mismo tramo del año anterior) es la única otra acción. Un cambio MUST refrescar todas las
  zonas. MUST NOT inventarse exportación ni filtro de partner: el backend no acota.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de ceros reales
  (partner con acceso y sin llamadas).
- **FR-UI-007**: Un p95 ausente MUST verse **sin dato**, nunca como 0 ms.
- **FR-UI-008**: En Uso, p95, media y muestras MUST mostrarse **en el mismo bloque**. MUST NOT
  separar las muestras a un pie.
- **FR-UI-009**: En Uso, cuando el percentil no es fiable, la pantalla MUST declararlo **junto
  a la cifra** y MUST NOT ocultar la fila.
- **FR-UI-010**: En Uso, 4xx y 5xx MUST verse **por separado**. MUST NOT existir un total
  «errores».
- **FR-UI-011**: En Uso, un partner con acceso y cero llamadas MUST aparecer con **cero**.
- **FR-UI-012**: En Uso, el denominador de adopción MUST leerse como acceso concedido, y la
  meta ≥70 % MUST estar a la vista.
- **FR-UI-013**: En Uso y Ecosistema, la pantalla MUST declararse distinta de los compuestos
  tácticos de Partners (ventana comparada, no recorte operativo).
- **FR-UI-014**: En Dinero, llamadas, cupo, precio e importe MUST ir **juntos**.
- **FR-UI-015**: En Dinero, el alcance MUST decir que es facturable y **no afirma cobro**.
- **FR-UI-016**: En Dinero, los no tarificables MUST estar declarados.
- **FR-UI-017**: En Dinero, participación y MRR MUST mostrar cobertura **parcial** y el precio
  de plan API que falta.
- **FR-UI-018**: En Ecosistema, la adopción MUST agruparse por **(servicio, versión)** y MUST
  declarar que la versión es **derivada**.
- **FR-UI-019**: En Ecosistema, el crecimiento MUST contar primeras llamadas exitosas. MUST
  NOT contar altas de credencial.
- **FR-UI-020**: En Ecosistema, la comparativa MUST mostrar ceros y MUST identificar
  organización, no contacto.
- **FR-UI-021**: Las tres pantallas MUST NOT mostrar disponibilidad, uptime ni un 99,9 %
  derivado del silencio del log.
- **FR-UI-022**: Las tres pantallas MUST NOT mostrar IP, secreto, hash ni contacto técnico,
  para ningún rol.
- **FR-UI-023**: Uso y Ecosistema MUST ser visibles para `DirectorTecnologico` y `Gerente`.
  Dinero MUST serlo para esos **más** `DirectorFinanciero`. Partner y el resto MUST NOT verlas
  en el menú ni entrar.
- **FR-UI-024**: `DirectorFinanciero` MUST NOT ver enlaces de Uso ni Ecosistema.
- **FR-UI-025**: Ver MUST NOT habilitar facturar, retirar versión ni revocar credencial. Abajo
  a la derecha hay **lectura**, no una acción de negocio.
- **FR-UI-026**: Si el backend declara muestras, fiabilidad, derivación, parcial, falta o
  alcance, la pantalla MUST mostrarlo junto a la cifra.
- **FR-UI-027**: Una comparación sin ventana anterior MUST mostrarse ausente **con motivo**, no
  como fallo de la pantalla.
- **FR-UI-028**: MUST NOT existir un enlace que fusione estas tres historias con el táctico de
  Partners o con el portal del partner.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director Tecnológico identifica adopción, período y si el p95 es fiable en
  **menos de 5 segundos** en Uso de la API, sin leer un párrafo.
- **SC-F02**: No existe un estado de pantalla en el que se vea el p95 y no se vea, en el mismo
  bloque, el número de muestras.
- **SC-F03**: Un percentil marcado como no fiable sigue visible y se lee como no fiable.
- **SC-F04**: 4xx y 5xx no se suman en ninguna zona.
- **SC-F05**: Un partner con acceso y cero llamadas aparece; no hay un listado que solo muestre
  a quien llamó.
- **SC-F06**: Uso de la API se distingue del compuesto táctico de Partners: no reutiliza su
  disposición y declara la ventana comparada.
- **SC-F07**: Dos servicios con la misma etiqueta de versión no se colapsan en una sola barra.
- **SC-F08**: Una credencial sin 2xx no incrementa el héroe de crecimiento.
- **SC-F09**: El excedente muestra llamadas, cupo y precio junto al importe, y se lee como no
  cobrado.
- **SC-F10**: Participación y MRR no se pueden leer como mix completo: parcial y falta están a
  la vista.
- **SC-F11**: Un Partner **no** accede a ninguna de las tres. El Financiero accede **solo** a
  Dinero. El Tecnológico y el Gerente a las tres.
- **SC-F12**: En ninguna aparecen IP, secreto, hash, contacto técnico, uptime ni mapa.
- **SC-F13**: Un período sin datos no se parece a un período con ceros.
- **SC-F14**: Uso de la API no presenta cuatro bloques del mismo peso; el recuento de la vista
  principal queda en **8 o menos**.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado táctico ni el portal del partner.
- **Zona Z**: métrica, período/comparación, visual grande, lectura.
- **Período y comparación**: únicos controles; la comparación de igual longitud es lo que
  distingue esta capa de la táctica.
- **Trío p95 / media / muestras**: viajan juntas.
- **Marca de parcial / alcance**: texto que impide leer un mix completo o un cobro.
- **Lectura**: el bloque de abajo a la derecha; no es un botón de negocio.

---

## Assumptions

- El backend de los diez publicados está en servicio. Esta capa no calcula cifras.
- El período es obligatorio; no hay valor por defecto que sustituya `desde` / `hasta` /
  `granularidad`.
- `DirectorTecnologico` y `Gerente` ven las tres historias; `DirectorFinanciero` solo Dinero;
  el partner ninguna — alineado con FR-OE2-006/007 y §4.2. Si el HTTP negara el dinero al
  Tecnológico, **se corrige el HTTP**, no esta spec.
- El patrón Z ya está demostrado en táctico; esta capa lo copia y añade comparación.
- Los compuestos tácticos de Partners, el portal del partner y la consola no se tocan ni se
  retiran.
- No hay exportación ni programación de envío.
- Las cifras de consumo salen de **dieciocho llamadas**: son correctas y no representativas.
  La pantalla muestra lo que hay y enseña las muestras.
- El mínimo de muestras lo resuelve el backend. Esta capa no ofrece un control extra de umbral.
- E2-06 sigue sin fuente; no reaparece por inferencia.
- Los frontends de OE1–OE6 de informes estratégicos ya están implementados en sus capas.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Compuestos tácticos de Partners | Ya existen; no se les añaden tarjetas |
| Portal acotado del partner | Sigue sirviendo al partner; esta lectura es de ecosistema |
| Un tablero de diez iguales | Rompe Z y la Ley de Hick |
| Disponibilidad / uptime / mapas | El log no mide minutos en silencio; inferirlo acusaría |
| IP, secreto, hash, contacto técnico | Exclusión constitucional; el backend no los entrega |
| Acciones de negocio (facturar, retirar versión, revocar) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Partner, Desarrollador de APIs, cargos ajenos | No son la autoridad de estos informes |
| Cambiar OpenAPI, SQL o permisos del backend | Depends-on — salvo alinear HTTP con FR-OE2-006 si divergiera |
| Frontend de OE3, OE4 | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período + comparación, trío de latencia inseparable, menú por rol. SC-F01, SC-F02, SC-F14. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (p95 con muestras, 4xx≠5xx, parcial, facturable≠cobrado, versión derivada). No inventa disponibilidad. |
| **Security** | Reutiliza quién entra. El partner no ve comparativas de todos (alcance competitivo). Sin IP ni secreto en pantalla. |
| **Safety** | Un p95 de dos llamadas o un 100 % de uptime fingido induciría una decisión de plataforma falsa. FR-UI-008 y FR-UI-021 lo impiden. No hay cadena de despacho. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras; comparación ausente se declara. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas copian Z ya usado. |
| **Performance Efficiency** | Heredada del backend. La pantalla no recalcula. Umbral: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio externo en esta capa. |
| **Flexibility** | El ecosistema de partners es el vehículo de expansión; Ecosistema lo muestra. Sin eje de región. |

**Traceability**: índice [`../OE2-monetizacion-api.md`](../OE2-monetizacion-api.md).
