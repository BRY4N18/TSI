# Feature Specification: Informes Compuestos de Emergencias — Frontend

**Feature Branch / capa**: `002-tactico/Emergencias/informes-compuestos-modelo/frontend`

**Created**: 2026-08-16

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (ver FR-UI-003) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick).

---

## Contexto

El backend de este módulo **ya publica trece informes** de gestión sobre el modelo analítico. Los
otros trece del catálogo se vigilan contra lecturas que ya existen y **no se vuelven a pintar aquí**.

Esta capa entrega **tres pantallas nuevas** para el Director de Operaciones (y el Administrador, con
el mismo acotamiento que ya tiene). No se añaden tarjetas al tablero de Registro / Despacho /
Seguimiento: ese tablero se ignora.

Cada pantalla cuenta **una historia** con pocos elementos, no un catálogo de trece iguales. El ojo
recorre un **patrón Z**:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que despache o cierre casos.
   Ver no habilita a decidir.

**No hay mapas.** El backend no entrega coordenadas (exclusión constitucional). El visual grande es
una distribución o una tendencia, nunca un plano.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Calidad del registro** | ¿El expediente se está llenando de verdad? | Completitud de campos críticos | Reparto completo / incompleto, o qué campo falta | Cuántos casos no entran en el % y por qué | — |
| **Despacho** | ¿El despacho se sostiene? | Primer intento (compromiso ≥90 %) | Desviación de llegada | Pérdida de señal | Ratio demanda / capacidad, incluida la zona **sin capacidad** |
| **Evidencia y cierre** | ¿Se cierra el ciclo con prueba y desenlace? | Envejecimiento de la cartera abierta | Cobertura de evidencia | Resultados / calificación y retiros forzados | Latencia de sincronización, enriquecimiento, volumen por unidad, escaladas — visibles, no protagonistas |

La tercera pantalla tiene ocho informes. Si los ocho salen del mismo tamaño, deja de ser Z y se
vuelve catálogo. Los cuatro de apoyo **MUST** quedar en segundo plano (detalle plegable o franja
menor), para no pasar de 6–8 bloques.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver si el registro es completo de verdad (Priority: P1) 🎯 MVP

El Director de Operaciones abre **Calidad del registro**, elige un período y ve de inmediato el
porcentaje de casos con campos críticos completos. No es el 100 % eterno del tablero anterior: si
falta severidad o ubicación, el número baja, y abajo a la derecha se lee cuántos casos y qué campo.

**Why this priority**: es el único informe de calidad que este módulo **migra** porque el anterior
mentía. Una sola pantalla basta para demostrar el patrón Z y la lectura honesta.

**Independent Test**: con un período que tenga al menos un caso incompleto, la métrica principal
**no** es 100 %, el visual grande muestra el hueco, y la lectura nombra los campos que se
comprobaron. Un visitante sin autoridad no entra.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones autenticado, **When** abre Calidad del registro, **Then** ve
   el patrón Z: métrica a la izquierda, período a la derecha, visual grande en el centro, lectura
   abajo a la derecha.
2. **Given** un período con casos incompletos, **When** carga la pantalla, **Then** la métrica
   principal es menor que 100 % y la lectura **no** omite el recuento de incompletos.
3. **Given** la lectura, **When** se muestra, **Then** declara **qué campos se comprobaron**. Un
   porcentaje sin esa lista se lee como «el registro es perfecto».
4. **Given** un período sin casos, **When** carga, **Then** el vacío se distingue de un período con
   casos que suman cero: no aparece una fila de ceros disfrazada de dato.
5. **Given** un Operador, un Cliente o un Partner, **When** intenta entrar, **Then** no ve la
   pantalla. El listado del día no es esta lectura de gestión.

---

### User Story 2 - Medir el despacho sin confundir oferta con proceso (Priority: P1)

El Director abre **Despacho**. Arriba a la izquierda está el primer intento (el compromiso de ≥90 %).
El visual grande es la desviación de llegada —con la advertencia de que **no es un plazo incumplido**,
es «más lento o más rápido de lo habitual»—. Abajo, el ratio (y las zonas sin quién atienda) y la
pérdida de señal.

**Why this priority**: cuatro lecturas que el backend ya corrigió o estrenó; juntas responden si el
despacho se degrada. Sin esta pantalla, esas correcciones no se ven.

**Independent Test**: cambiar el período refresca las cuatro zonas. Una zona sin unidades vigentes
se lee **sin capacidad**, no como cero ni como infinito. La desviación sin referencia se lee
**ausente**, no como cero.

**Acceptance Scenarios**:

1. **Given** el Director, **When** abre Despacho, **Then** el héroe es el primer intento, el visual
   grande es la desviación, y la pérdida de señal está en la lectura de abajo a la derecha.
2. **Given** la desviación, **When** se muestra, **Then** la pantalla dice que la referencia es
   histórica y **no** un acuerdo de servicio. Pintarla como incumplimiento inventaría un SLA.
3. **Given** un condado con demanda y ninguna unidad vigente en el período, **When** aparece el
   ratio, **Then** se declara **sin capacidad** y no se muestra un 0 ni un infinito.
4. **Given** despachos sin histórico comparable, **When** se muestra la desviación, **Then** esos
   casos se ven **sin dato**, no como desviación 0.
5. **Given** un cambio de período, **When** se confirma, **Then** las cuatro zonas se actualizan
   juntas. Un fallo de una zona no deja el resto en blanco eterno: las otras siguen visibles.

---

### User Story 3 - Cerrar el ciclo: evidencia y desenlace (Priority: P2)

El Director abre **Evidencia y cierre**. El héroe es lo que sigue abierto (envejecimiento). El visual
grande es si los cierres trajeron prueba (cobertura de evidencia). Abajo a la derecha, cómo terminó
el caso (resultados, calificación, retiros forzados). El resto —latencia offline, enriquecimiento,
volumen por unidad, escaladas— se puede ver sin competir con el héroe.

**Why this priority**: son los ocho informes que no existían en ningún tablero. Valen como cierre del
ciclo, no como ocho portadas.

**Independent Test**: la vista principal no muestra ocho bloques del mismo peso. Un caso cerrado sin
evidencia **baja** la cobertura; no desaparece. Una calificación ausente se ve ausente, nunca como
cero.

**Acceptance Scenarios**:

1. **Given** el Director, **When** abre Evidencia y cierre, **Then** el héroe es el envejecimiento, el
   visual grande es la cobertura de evidencia, y la lectura de cierre está abajo a la derecha.
2. **Given** la vista principal, **When** se cuenta lo que compite por atención, **Then** hay **como
   máximo 8 bloques**, y los cuatro de apoyo no tienen el mismo tamaño que el visual grande.
3. **Given** cierres sin foto ni nota, **When** se muestra la cobertura, **Then** esos casos cuentan
   como sin cobertura. Omitirlos inflaría el %.
4. **Given** un cierre sin calificar, **When** aparece en resultados, **Then** la calificación se ve
   **ausente**, nunca como 0.
5. **Given** evidencia capturada sin conexión, **When** se mira la latencia, **Then** se distinguen
   captura en sitio y llegada al sistema.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no una métrica en 0 %.
- **Una zona falla y las otras no.** El resto de la pantalla sigue; la zona fallida lo dice. Un
  error no borra la historia.
- **Cifra parcial.** Si el backend declara que el dato no cubre todo lo que el nombre promete, la
  pantalla **lo dice junto a la cifra**. Esconderlo convierte un hueco en un indicador.
- **Entidad desconocida.** Un condado o unidad sin nombre **aparece como desconocido** y sigue en el
  total. No se omite la fila.
- **Sin autoridad.** Operador, Cliente, Partner y cualquier rol ajeno a Emergencias no entran.
- **Dato sensible.** Ninguna de las tres pantallas muestra coordenadas, identidad de personas ni
  texto libre interno, **tampoco al Director**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Calidad del registro,
  Despacho, Evidencia y cierre— y MUST NOT añadir tarjetas al tablero de Registro / Despacho /
  Seguimiento.
- **FR-UI-002**: Las tres pantallas MUST mostrar **solo los trece informes que el backend publica**.
  Los trece vigilados MUST NOT reaparecer aquí.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**: métrica o contexto arriba a la izquierda;
  período arriba a la derecha; visual principal en la diagonal; lectura o implicación abajo a la
  derecha. MUST NOT ser una grilla de tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques** simultáneos del sistema de
  diseño. En Evidencia y cierre, los cuatro informes de apoyo MUST quedar en segundo plano.
- **FR-UI-005**: El período MUST ser la única acción de filtrado de esta capa. Un cambio MUST
  refrescar todas las zonas de la pantalla. MUST NOT inventarse exportación: el backend no la ofrece.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de un período con ceros
  reales (backend FR-019).
- **FR-UI-007**: Un denominador ausente o una referencia que no existe MUST verse **sin dato**, nunca
  como 0 (backend FR-017, SC-011).
- **FR-UI-008**: En Calidad del registro, la lectura MUST nombrar **los campos comprobados**. MUST
  NOT mostrar solo el porcentaje.
- **FR-UI-009**: En Despacho, una zona con demanda y sin unidades vigentes MUST leerse **sin
  capacidad**, no como ratio 0 ni como infinito.
- **FR-UI-010**: En Despacho, la desviación de llegada MUST llevar la advertencia de que la
  referencia es histórica y **no** un acuerdo de servicio.
- **FR-UI-011**: Las tres pantallas MUST NOT mostrar coordenadas, identidad de personas ni texto
  libre interno, para ningún rol (backend FR-015, FR-016, FR-022).
- **FR-UI-012**: Las tres pantallas MUST NOT dibujar mapas ni pedir posiciones.
- **FR-UI-013**: Acceden el **Director de Operaciones** (sin acotamiento de titularidad) y el
  **Administrador** (con el acotamiento que ya tiene). El Operador, el Cliente y el Partner MUST NOT
  entrar (backend FR-021, FR-023).
- **FR-UI-014**: Ver un informe MUST NOT habilitar despachar, cerrar, forzar ni cualquier acción
  operativa. No hay llamada a la acción de negocio en la esquina inferior derecha: hay **lectura**.
- **FR-UI-015**: Si el backend declara cobertura incompleta o un alcance, la pantalla MUST mostrarlo
  junto a la cifra. MUST NOT silenciarlo.
- **FR-UI-016**: Las tres pantallas MUST ser de solo lectura y MUST compartir el mismo patrón Z, para
  que Red Operativa pueda copiarlo después sin reinventar la historia.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director de Operaciones recorre las tres pantallas y, en cada una, identifica la
  métrica principal en **menos de 5 segundos** sin leer un párrafo.
- **SC-F02**: En un período con casos incompletos, Calidad del registro **no** muestra 100 % como
  única cifra, y nombra los campos comprobados.
- **SC-F03**: Un condado sin capacidad se lee como tal en Despacho; un observador no lo confunde con
  «ratio cero».
- **SC-F04**: La desviación de llegada no se interpreta como incumplimiento de un plazo: la
  advertencia está visible junto al visual grande.
- **SC-F05**: Evidencia y cierre no presenta ocho bloques del mismo peso; un recuento de la vista
  principal queda en **8 o menos**.
- **SC-F06**: Un Operador, un Cliente y un Partner **no** acceden a ninguna de las tres.
- **SC-F07**: En ninguna de las tres aparecen coordenadas, nombres de implicados ni mapas.
- **SC-F08**: Un período sin datos no se parece a un período con ceros.
- **SC-F09**: Las tres pantallas se distinguen del tablero de Registro / Despacho / Seguimiento: no
  reutilizan su disposición ni le añaden tarjetas.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni el tablero operativo.
- **Zona Z**: métrica, período, visual grande, lectura. Cuatro zonas, no trece tarjetas.
- **Período**: el único filtro; por defecto los últimos 30 días (igual que el backend).
- **Lectura**: el texto o bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los trece publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días, como asume el backend.
- El Administrador entra con el mismo acotamiento que en los listados; el Director ve el
  departamento entero.
- Red Operativa copiará este patrón cuando tenga su frontend; por eso las tres pantallas son la
  misma forma tres veces, no tres inventos.
- No hay exportación ni programación de envío en esta pasada.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Tablero de Registro / Despacho / Seguimiento | Se ignora a propósito; no se le añaden tarjetas |
| Los trece informes vigilados | Ya tienen lectura; publicarlos aquí duplicaría la cifra |
| Mapas y coordenadas | Exclusión constitucional; el backend no las entrega |
| Acciones operativas (despachar, cerrar, forzar) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Operador, Cliente, Partner | No son la autoridad de estos informes |
| Cambiar OpenAPI, consultas o permisos del backend | Depends-on |
| Frontend de Red Operativa u otros departamentos | Mismo patrón, otro módulo |
| Informes estratégicos (OE6 / OE3) | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período único. SC-F01. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (completitud, sin capacidad, sin dato). No inventa métricas. |
| **Security** | Reutiliza quién entra (Director / Administrador). Exclusión constitucional de dato sensible también en pantalla. |
| **Safety** | Un 100 % falso o un ratio 0 donde no hay quién atienda se lee mal bajo presión; FR-UI-008 y FR-UI-009 lo impiden. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas comparten el mismo patrón. |
| **Performance Efficiency** | Heredada del backend (SC-009). La pantalla no recalcula. |
| **Compatibility** | No aplica: no hay intercambio con sistemas externos en esta capa. |
| **Flexibility** | No aplica: no se agrupa por región; la ubicación llega por nombre. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
