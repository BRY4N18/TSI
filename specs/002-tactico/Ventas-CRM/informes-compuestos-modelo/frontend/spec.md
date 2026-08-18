# Feature Specification: Informes Compuestos de Ventas y CRM — Frontend

**Feature Branch / capa**: `002-tactico/Ventas-CRM/informes-compuestos-modelo/frontend`

**Created**: 2026-08-17

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que Emergencias y Red Operativa) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

---

## Contexto

El backend de este módulo **ya publica los trece informes** de OT01 a OT03. No hay vigilados que
omitir: aquí los trece son construcción nueva y los trece se pintan.

Esta capa entrega **tres pantallas nuevas**. No se mezclan con los listados simples del
departamento: esos listados, si existen, se quedan como están.

A diferencia de Red Operativa, **la autoridad no está repartida por materia**. El Director de
Marketing y el ejecutivo comercial ven **las mismas tres historias**. Lo que cambia es el
alcance: el director ve el departamento entero; el ejecutivo, **sus** prospectos. Una cifra
acotada y una completa se ven idénticas; sin declarar el alcance, los dos leerían la misma
pantalla con números distintos y ninguno sabría por qué.

El ojo recorre el **mismo patrón Z**:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que asigne o dispare un
   aviso. Ver no habilita a decidir.

**No hay mapas ni fichas de persona.** El backend no entrega coordenadas ni identidad del
prospecto. El visual grande es una distribución o una tendencia. El único desglose por persona
es la **clave del ejecutivo** en carga, y solo ahí.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Embudo comercial** | ¿Dónde se atasca y se pierde el pipeline? | Paso entre etapas | Permanencia por etapa (el estancado es el más lento) | Motivos de pérdida **con la etapa de abandono** | Carga por ejecutivo, pipeline ponderado |
| **Captación por canal** | ¿Por dónde entran y cuáles convierten? | Volumen por canal | Tasa de conversión por canal | Convertidos por canal — **mitad medible del CAC**, con lo que falta declarado | — |
| **Nutrición del prospecto** | ¿La demo y el aviso mueven el embudo? | Efectividad con demo / sin demo, cada grupo con su base | Intensidad de uso y secciones visitadas | Latencia de reacción: el aviso ignorado **no** mejora la mediana | Reglas de disparo |

Embudo comercial tiene cinco informes. Si los cinco de apoyo salen del mismo tamaño que el visual
grande, deja de ser Z. Carga y pipeline **MUST** quedar en segundo plano (detalle plegable o
franja menor), para no pasar de 6–8 bloques.

Nutrición tiene cinco. Intensidad y secciones pueden compartir el visual grande; las reglas de
disparo **MUST** quedar en segundo plano. Hoy las fuentes de demo y aviso están **vacías en el
entorno**: la pantalla honesta es el vacío, no un tablero de ceros.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Marketing ve dónde se atasca el embudo (Priority: P1) 🎯 MVP

El Director de Marketing abre **Embudo comercial**, elige un período y ve de inmediato cómo
pasan los prospectos de una etapa a la siguiente. El visual grande es el tiempo en cada etapa:
quien lleva semanas sin moverse aparece como el más lento, no como el más rápido. Abajo, por qué
se pierden y **en qué etapa**. Carga y valor ponderado se pueden ver sin competir con el héroe.

**Why this priority**: es CU-T03, tiene datos reales en el origen, y una sola pantalla basta para
demostrar el patrón Z, el alcance declarado y que convertido no se pinta junto a perdido.

**Independent Test**: con un período que tenga al menos un prospecto estancado, la permanencia de
esa etapa es la mayor, no la menor. Un visitante sin autoridad no entra. Un ejecutivo ve las
mismas zonas con el alcance **propios** visible.

**Acceptance Scenarios**:

1. **Given** un Director de Marketing autenticado, **When** abre Embudo comercial, **Then** ve el
   patrón Z: métrica a la izquierda, período a la derecha, visual grande en el centro, lectura
   abajo a la derecha.
2. **Given** un prospecto convertido y otro perdido, **When** se muestra el embudo, **Then** **no
   se cuentan juntos** ni aparecen como un solo grupo de «inactivos».
3. **Given** un prospecto sin transiciones que sigue en su etapa, **When** se muestra la
   permanencia, **Then** esa etapa cuenta hasta el fin del período y el estancado no parece el
   más rápido.
4. **Given** un prospecto perdido en «Propuesta», **When** se leen los motivos, **Then** aparece
   el motivo **y** la etapa de abandono. Un motivo ausente se lee «sin motivo registrado», no se
   omite.
5. **Given** el pipeline ponderado, **When** se muestra, **Then** la pantalla dice que los pesos
   son **una convención del informe**, no una política de la empresa.
6. **Given** un Operador, un Cliente o un Director de Operaciones, **When** intenta entrar,
   **Then** no ve la pantalla.

---

### User Story 2 - El Director de Marketing mide la captación sin inventar un CAC (Priority: P1)

El Director abre **Captación por canal**. Arriba a la izquierda, cuántos llegan por cada canal
—incluido **Desconocido**, que suma—. El visual grande es quién convierte, con el denominador a
la vista. Abajo, cuántos clientes salieron de cada canal, y **junto a esa cifra** que es la parte
medible del coste de adquisición: falta el coste, y el sistema no lo tiene.

**Why this priority**: es CU-T04. Sin esta pantalla, el hueco del CAC se rellenaría en el tablero
con un número que el sistema no sostiene.

**Independent Test**: la suma de canales, Desconocido incluido, es el total del período. Ninguna
zona se titula «CAC» ni muestra coste. Un canal sin prospectos se lee **sin dato**, no 0 %.

**Acceptance Scenarios**:

1. **Given** el Director, **When** abre Captación por canal, **Then** el héroe es el volumen, el
   visual grande es la tasa de conversión, y los convertidos están en la lectura de abajo a la
   derecha.
2. **Given** prospectos sin canal, **When** aparece el volumen, **Then** hay una fila
   **Desconocido** y cuenta en el total. Omitirla haría que los canales sumaran menos que el
   embudo.
3. **Given** un canal con conversiones, **When** se muestra la tasa, **Then** el denominador es
   visible. Un 20 % sin base no se puede comparar.
4. **Given** un canal sin prospectos en el período, **When** se pide su tasa, **Then** se lee
   **sin dato**, nunca 0 %.
5. **Given** la lectura de convertidos, **When** se muestra, **Then** declara que es la parte
   medible del indicador y **cuál falta**. MUST NOT aparecer una columna de coste, ni vacía, ni
   el nombre «CAC» como si el número estuviera completo.

---

### User Story 3 - Ver si la demo y el aviso mueven el embudo, o si no hubo nada (Priority: P2)

El Director abre **Nutrición del prospecto**. El héroe compara a quienes usaron la demo con
quienes no, **cada grupo con su base**. El visual grande es cómo se usó el producto (eventos y
secciones). Abajo, cuánto tardó el ejecutivo en reaccionar a un aviso: el ignorado cuenta aparte
y **no** baja la mediana. Si en el período no hubo demos, la pantalla está vacía —eso no es lo
mismo que «hubo demo y no se usó».

**Why this priority**: son cinco informes sobre fuentes que hoy están vacías en el entorno. Pintar
ceros afirmaría que se midió el producto y nadie lo tocó.

**Independent Test**: un período sin demos no muestra filas de 0 eventos. Un aviso sin avance
posterior no aparece como latencia 0. El ejecutivo acotado ve las mismas zonas, con alcance
propios.

**Acceptance Scenarios**:

1. **Given** el Director, **When** abre Nutrición del prospecto, **Then** el héroe es la
   efectividad en dos grupos, el visual grande es el uso de la demo, y la latencia está abajo a
   la derecha.
2. **Given** los dos grupos, **When** se muestran, **Then** cada uno trae su denominador. Un
   porcentaje sin base no permite comparar un grupo de 3 con uno de 300.
3. **Given** un período sin ninguna interacción de demo, **When** carga, **Then** el vacío se
   distingue de un período con demos cuyos eventos suman cero.
4. **Given** un aviso sin avance posterior, **When** se muestra la latencia, **Then** cuenta como
   **sin reacción** y no entra a la mediana. Contarlo como cero haría que los peores casos
   mejoraran el indicador.
5. **Given** la vista principal, **When** se cuenta lo que compite por atención, **Then** hay
   **como máximo 8 bloques**, y las reglas de disparo no tienen el mismo tamaño que el visual
   grande.

---

### User Story 4 - El ejecutivo ve lo mismo, acotado, y lo sabe (Priority: P1)

El Gerente de Ventas abre las mismas tres pantallas. El patrón Z no cambia. Las cifras son las
de **sus** prospectos, y la pantalla lo dice. Sin esa declaración, él y el director discutirían
números distintos creyendo ver el departamento.

**Why this priority**: es el único departamento de compuestos que acota por titularidad. El
permiso demasiado ancho no produce síntoma; el alcance callado sí.

**Independent Test**: el ejecutivo entra a las tres. Un observador lee en cada una que el alcance
es propios. El director lee que ve todos. Un Gerente de Cuentas Públicas no entra: esta capa no
amplía a quien el backend no admite.

**Acceptance Scenarios**:

1. **Given** un Gerente de Ventas autenticado, **When** abre cualquiera de las tres, **Then** ve
   el mismo patrón Z que el director y el alcance **propios** está visible.
2. **Given** un Director de Marketing, **When** abre la misma pantalla, **Then** el alcance se
   lee como el departamento entero.
3. **Given** un Administrador, **When** entra, **Then** ve las tres con el acotamiento que ya
   tiene el backend, también declarado.
4. **Given** un Gerente de Cuentas Públicas, un Operador o un Cliente, **When** busca estas
   pantallas, **Then** no las ve en su menú y no entra.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no una métrica en 0 %.
- **OT03 sin demos.** Vacío explícito; no es «hubo producto y no se usó».
- **Una zona falla y las otras no.** El resto de la pantalla sigue; la zona fallida lo dice.
- **Cifra parcial o convención.** Pesos del pipeline, mitad medible del CAC, alcance acotado: la
  pantalla **lo dice junto a la cifra**. Esconderlo convierte un hueco o una convención en un
  indicador de la empresa.
- **Canal o motivo desconocido.** Aparece con esa etiqueta y sigue en el total. No se omite la
  fila.
- **Carga por ejecutivo.** Solo esa zona desglosa por persona, y lo hace por **clave**, no por
  nombre. Ninguna otra pantalla lista ejecutivos.
- **Sin autoridad.** Operador, Cliente, Partner, Director de Operaciones y Gerente de Cuentas
  Públicas no entran.
- **Dato sensible.** Ninguna de las tres muestra nombre, correo, teléfono, cargo ni notas del
  prospecto, **tampoco al Director de Marketing**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Embudo comercial,
  Captación por canal, Nutrición del prospecto— y MUST NOT añadir tarjetas a los listados
  simples de Ventas y CRM.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los trece informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT inventar un catorce ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**: métrica o contexto arriba a la
  izquierda; período arriba a la derecha; visual principal en la diagonal; lectura o implicación
  abajo a la derecha. MUST NOT ser una grilla de tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques** simultáneos del sistema de
  diseño. En Embudo comercial, carga y pipeline MUST quedar en segundo plano. En Nutrición, las
  reglas de disparo MUST quedar en segundo plano.
- **FR-UI-005**: El período MUST ser la única acción de filtrado de esta capa. Un cambio MUST
  refrescar todas las zonas de la pantalla. MUST NOT inventarse exportación: el backend no la
  ofrece.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de un período con ceros
  reales (backend FR-031).
- **FR-UI-007**: Un denominador ausente o un canal sin prospectos MUST verse **sin dato**, nunca
  como 0 % (backend FR-020, FR-030).
- **FR-UI-008**: En Embudo comercial, convertido y perdido MUST NOT agruparse como «inactivos» ni
  como un solo desenlace (backend FR-006, FR-007).
- **FR-UI-009**: En Embudo comercial, la permanencia MUST incluir el tramo abierto: el estancado
  MUST verse como el más lento de su etapa, no como el más rápido (backend FR-011, FR-012,
  SC-004).
- **FR-UI-010**: En Embudo comercial, los motivos de pérdida MUST mostrarse **con la etapa de
  abandono**. Un motivo ausente MUST leerse «sin motivo registrado», no omitirse (backend
  FR-013, FR-014).
- **FR-UI-011**: En Embudo comercial, el pipeline ponderado MUST llevar la advertencia de que los
  pesos son **una convención del informe** y no una política de la empresa (backend FR-017).
- **FR-UI-012**: En Captación por canal, los prospectos sin canal MUST aparecer como
  **Desconocido** y sumar en el total (backend FR-018, SC-006).
- **FR-UI-013**: En Captación por canal, la lectura de convertidos MUST declarar que es la parte
  medible del indicador BSC y cuál falta. MUST NOT titularse CAC ni mostrar coste, importe ni
  inversión, ni vacíos (backend FR-021, FR-022, FR-023).
- **FR-UI-014**: En Nutrición, «no hubo demos» MUST distinguirse de «hubo demos y no se usaron»
  (backend FR-026, SC-009).
- **FR-UI-015**: En Nutrición, un aviso sin avance posterior MUST contar como **sin reacción** y
  MUST NOT entrar a la mediana de latencia (backend FR-025).
- **FR-UI-016**: Las tres pantallas MUST NOT mostrar nombre, apellidos, correo, teléfono, cargo
  ni notas del prospecto, para ningún rol (backend FR-027, FR-035, SC-007).
- **FR-UI-017**: Solo la zona de carga por ejecutivo MAY desglosar por persona, y MUST hacerlo
  por la **clave del ejecutivo**, no por su nombre. Las otras zonas MUST NOT listar personas
  (backend FR-028).
- **FR-UI-018**: Las tres pantallas MUST NOT dibujar mapas ni pedir posiciones.
- **FR-UI-019**: Las tres pantallas MUST ser visibles y accesibles para el **Director de
  Marketing** (sin acotamiento de titularidad), el **Gerente de Ventas** (acotado a sus
  prospectos) y el **Administrador** (con el acotamiento que ya tiene el backend). Operador,
  Cliente, Partner, Director de Operaciones y Gerente de Cuentas Públicas MUST NOT verlas en el
  menú ni entrar (backend FR-033, FR-034).
- **FR-UI-020**: Cuando el alcance no es el departamento entero, cada pantalla MUST declarar
  **acotado a propios** (o el valor que el backend ya envía) junto al período. MUST NOT dejar
  que director y ejecutivo vean la misma disposición con cifras distintas y sin etiqueta.
- **FR-UI-021**: Ver un informe MUST NOT habilitar asignar, transicionar, disparar avisos ni
  cualquier acción operativa. No hay llamada a la acción de negocio en la esquina inferior
  derecha: hay **lectura**.
- **FR-UI-022**: Si el backend declara cobertura incompleta, convención o un alcance, la
  pantalla MUST mostrarlo junto a la cifra. MUST NOT silenciarlo.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director de Marketing identifica la métrica principal de Embudo comercial en
  **menos de 5 segundos** sin leer un párrafo.
- **SC-F02**: En un período con un prospecto estancado, la permanencia de esa etapa **no** lo
  presenta como el más rápido.
- **SC-F03**: Convertido y perdido no aparecen como un solo grupo de inactivos en ninguna de las
  tres.
- **SC-F04**: Captación por canal no se lee como un CAC completo: la declaración de lo que falta
  está visible junto a los convertidos, y no hay cifra de coste.
- **SC-F05**: Desconocido cuenta en el volumen de captación; un observador que sume los canales
  obtiene el total del período.
- **SC-F06**: Un período sin demos no se parece a un período con demos en cero.
- **SC-F07**: Un aviso ignorado no mejora la latencia visible.
- **SC-F08**: Embudo comercial y Nutrición no presentan cinco bloques del mismo peso; un
  recuento de la vista principal queda en **8 o menos**.
- **SC-F09**: Un Gerente de Ventas ve las tres pantallas con el alcance propios visible. Un
  Operador, un Cliente y un Gerente de Cuentas Públicas **no** acceden a ninguna.
- **SC-F10**: En ninguna de las tres aparecen nombre, correo, teléfono ni mapas de un prospecto.
- **SC-F11**: Un período sin datos no se parece a un período con ceros.
- **SC-F12**: Las tres pantallas se distinguen de los listados simples: no reutilizan su
  disposición ni les añaden tarjetas.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni un tablero de departamento.
- **Zona Z**: métrica, período, visual grande, lectura. Cuatro zonas, no trece tarjetas.
- **Período**: el único filtro; por defecto los últimos 30 días (igual que el backend).
- **Alcance**: todos o propios; viaja visible junto al período cuando no es el departamento
  entero.
- **Lectura**: el texto o bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los trece publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días, como asume el backend.
- El Director de Marketing ve el departamento entero; el Gerente de Ventas y el Administrador
  entran acotados, como ya decide el backend.
- El Gerente de Cuentas Públicas no entra a estos compuestos: el backend no lo admite, y esta
  capa no amplía el acceso.
- El patrón Z ya está demostrado en Emergencias y Red Operativa; esta capa lo copia, no lo
  reinventa. Lo que no se copia es el acotamiento por titularidad, que aquí sí existe.
- Los listados simples de Ventas y CRM no se tocan.
- No hay exportación ni programación de envío en esta pasada.
- OT03 puede llegar vacío en el entorno; eso es dato, no un fallo de pantalla.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Listados simples de Ventas y CRM | Ya tienen (o tendrán) su módulo; no se les añaden tarjetas |
| Un tablero único de trece iguales | Rompe el patrón Z y la Ley de Hick |
| Mapas, coordenadas e identidad del prospecto | Exclusión constitucional; el backend no las entrega |
| Acciones operativas (asignar, transicionar, disparar avisos) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Inventar el coste de adquisición | El sistema no tiene coste por canal |
| Operador, Cliente, Partner, Gerente de Cuentas Públicas | No son la autoridad de estos compuestos |
| Cambiar OpenAPI, consultas o permisos del backend | Depends-on |
| Frontend de Emergencias, Red Operativa u otros departamentos | Mismo patrón, otro módulo |
| Informes estratégicos | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período único, alcance visible. SC-F01. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (estancado lento, Desconocido suma, CAC parcial, vacío ≠ ceros). No inventa métricas. |
| **Security** | Reutiliza quién entra (Director / Gerente de Ventas / Administrador). Exclusión constitucional de dato personal también en pantalla. Alcance declarado para no filtrar a ojo. |
| **Safety** | Un 0 % donde no hubo demos, o un CAC inventado, se lee mal al decidir presupuesto; FR-UI-013 y FR-UI-014 lo impiden. No hay cadena de despacho: Safety se limita a no inducir una decisión comercial falsa. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas copian el patrón Z ya usado. |
| **Performance Efficiency** | Heredada del backend. La pantalla no recalcula. Umbral de esta capa: SC-F01 (reconocer el héroe en menos de 5 s). |
| **Compatibility** | No aplica: no hay intercambio con sistemas externos en esta capa. |
| **Flexibility** | No aplica: no se agrupa por región; el canal llega por nombre. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
