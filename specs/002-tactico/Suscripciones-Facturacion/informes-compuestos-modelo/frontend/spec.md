# Feature Specification: Informes Compuestos de Suscripciones y Facturación — Frontend

**Feature Branch / capa**: `002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/frontend`

**Created**: 2026-08-17

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que Emergencias, Red Operativa y Ventas) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

---

## Contexto

El backend de este módulo **ya publica los trece informes** de OT05 a OT07. No hay vigilados que
omitir: los trece se pintan.

Esta capa entrega **tres pantallas nuevas**. No se mezclan con el catálogo de planes ni con los
listados simples del departamento: esos se quedan como están.

### La diferencia: no hay un solo jefe

Como en Red Operativa, la autoridad **está repartida** (SRS §5.1, backend FR-038, FR-039):

| Materia | Quién la gobierna | Qué ve |
|---|---|---|
| **Finanzas** | Director Financiero | Cuánto entra, si se cobra, cómo se mueve la cartera |
| **Catálogo** | Director de Estrategia | Cómo se reparte el catálogo y si se usa lo contratado |
| **Ambas** | Administrador | Las tres pantallas, con el acotamiento operativo que ya tiene |

Cada director **MUST NOT** ver la materia del otro. No hay un tablero único «Suscripciones» que
fusione cobro y catálogo «porque es el mismo departamento». Eso es el error que el backend ya
impide: admitir a las dos autoridades y quedarse tranquilo.

Cada director ve **solo sus enlaces**. Un ítem gris o un acceso denegado después de entrar
descubrirá al otro cargo. El sistema de diseño lo prohíbe: el menú de cada rol contiene únicamente
lo que ese rol puede abrir.

El ojo recorre el **mismo patrón Z**:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que emita una factura o
   cambie un plan. Ver no habilita a decidir.

**No hay fichas de cobro ni de persona.** El backend no entrega token, últimos dígitos, fiscal ni
quién aprobó un cambio. El visual grande es una distribución o una tendencia.

MRR y NRR se miden por **mes natural**. Un rango arbitrario se resuelve al mes que lo contiene, y
la pantalla **lo dice junto a la cifra**. Comparar dos ventanas móviles solapadas no es comparar.

### Qué entra en cada pantalla

| Pantalla | Audiencia | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|---|
| **Cobro e ingreso** | Financiero | ¿Cuánto entra y se cobra? | MRR (y su variación) | Ingresos por plan, con notas de crédito a la vista | Tasa de renovación | Cobro al primer intento, dunning, clientes sin método |
| **Movimientos de cartera** | Financiero | ¿La cartera que ya está se sostiene? | NRR y sus componentes | Upgrades / downgrades con delta | Tiempo de resolución: pendiente **aparte**, rechazada cuenta | Suspensión y reactivación |
| **Catálogo y uso** | Estrategia | ¿Pagan por lo que usan? | Distribución de cartera (clientes e ingreso **por separado**) | Utilización: usado y contratado, ambos números | Severidades habilitadas y no usadas | — |

Cobro e ingreso tiene seis informes. Si los seis salen del mismo tamaño, deja de ser Z y se
vuelve catálogo. Cobro, dunning y sin método **MUST** quedar en segundo plano (detalle plegable o
franja menor), para no pasar de 6–8 bloques.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Financiero ve cuánto entra y si se cobra (Priority: P1) 🎯 MVP

El Director Financiero abre **Cobro e ingreso**, elige un período y ve de inmediato el ingreso
recurrente del mes. El visual grande reparte lo facturado por plan; las notas de crédito se ven
restando, no escondidas. Abajo, quién renovó. Cobro al primer intento, dunning y quién no tiene
método de pago se pueden ver sin competir con el héroe.

**Why this priority**: contiene tres indicadores BSC que el backend acaba de hacer medibles, y
una sola pantalla basta para demostrar el patrón Z **y** que este director no ve el catálogo.

**Independent Test**: con un mes que tenga una suscripción cancelada aún marcada activa en el
origen, el héroe **no** incluye su precio. Un Director de Estrategia **no** ve el enlace ni entra.
Un visitante sin autoridad no entra.

**Acceptance Scenarios**:

1. **Given** un Director Financiero autenticado, **When** abre Cobro e ingreso, **Then** ve el
   patrón Z: métrica a la izquierda, período a la derecha, visual grande en el centro, lectura
   abajo a la derecha.
2. **Given** una suscripción cancelada, **When** se muestra el MRR, **Then** **no aporta**. Pintar
   su precio afirmaría ingreso que ya no existe.
3. **Given** una anual y una mensual del mismo precio, **When** se muestra el MRR, **Then** no
   aportan lo mismo: se ve la cifra **mensualizada**. La que no tiene periodicidad **no entra** y
   se cuenta aparte, nunca como cero.
4. **Given** una nota de crédito en el período, **When** se muestran los ingresos, **Then** el
   neto es **menor** que el facturado, y se ve cuánto se restó.
5. **Given** una factura en disputa, **When** se mira cobro o dunning, **Then** **no** aparece
   como impaga ni suma mora.
6. **Given** el MRR, **When** se muestra, **Then** la pantalla declara el **mes natural** aplicado,
   aunque se hayan pedido fechas que no coinciden con un mes cerrado.
7. **Given** un Director de Estrategia, un Cliente o un Operador, **When** intenta entrar,
   **Then** no ve la pantalla.

---

### User Story 2 - El Director Financiero sigue si la cartera se sostiene (Priority: P1)

El Director Financiero abre **Movimientos de cartera**. Arriba a la izquierda, el NRR de quienes
**ya estaban** al inicio del mes —los nuevos no inflan la retención—. El visual grande son las
subidas y bajadas de plan, clasificadas por **precio**, no por el nombre del nivel. Abajo, cuánto
tardan en resolverse las solicitudes: una abierta **no** mejora la mediana; una rechazada sí
cuenta, porque se resolvió.

**Why this priority**: junta los otros dos indicadores BSC. Sin esta pantalla, el de Estrategia o
el Financiero acabarían viendo la materia del otro, o el NRR se leería como crecimiento bruto.

**Independent Test**: un cliente que llegó este mes **no** sube el NRR. Un cambio a un plan de
nivel «superior» más barato se lee como bajada. El de Estrategia no entra.

**Acceptance Scenarios**:

1. **Given** el Director Financiero, **When** abre Movimientos de cartera, **Then** el héroe es el
   NRR, el visual grande son los movimientos con delta, y el tiempo de resolución está abajo a
   la derecha.
2. **Given** el NRR, **When** se muestra, **Then** se ven expansión, contracción y baja, y la
   pantalla declara el mes natural. Un cliente nuevo del mes **no** entra a la cohorte.
3. **Given** un cambio a un plan de nivel superior más barato, **When** aparece el movimiento,
   **Then** se lee como **downgrade**. El nivel del catálogo no manda.
4. **Given** una solicitud pendiente y otra rechazada, **When** se muestra el tiempo, **Then** la
   pendiente queda **fuera** de la mediana y se cuenta aparte; la rechazada **sí** entra como
   resuelta.
5. **Given** un Director de Estrategia, **When** busca esta pantalla, **Then** no la ve en su menú
   y no entra.

---

### User Story 3 - El Director de Estrategia ve si el catálogo se usa (Priority: P1)

El Director de Estrategia abre **Catálogo y uso**. El héroe reparte la cartera por plan: un plan
gratis **cuenta en clientes y aporta cero ingreso**, las dos cifras a la vista. El visual grande
es la utilización: 5 de 25 no se parece a un porcentaje solo. Abajo, las severidades que el
cliente paga y no usa. Junto a la utilización, que **aún no se mide el consumo de API** —y no hay
un hueco que parezca consumo cero—.

**Why this priority**: son los únicos tres informes de su materia. Si se mezclaran en un tablero
de departamento, esta historia desaparecería o se filtraría al Financiero.

**Independent Test**: un plan de precio cero no desaparece. La utilización muestra usado y
contratado. Ninguna zona se titula llamadas ni muestra un consumo de API. El Financiero no entra.

**Acceptance Scenarios**:

1. **Given** un Director de Estrategia autenticado, **When** abre Catálogo y uso, **Then** ve el
   patrón Z con la distribución como héroe, la utilización como visual grande y las severidades
   abajo a la derecha.
2. **Given** un plan de precio cero, **When** aparece la distribución, **Then** cuenta en clientes
   y aporta **cero** ingreso; ambas cifras se ven. Omitirlo haría un demo invisible o un éxito
   falso.
3. **Given** un cliente con 5 unidades de 25 contratadas, **When** se muestra la utilización,
   **Then** se leen **ambos números**, no solo el porcentaje.
4. **Given** la utilización, **When** se muestra, **Then** declara que la dimensión de llamadas
   **falta**. MUST NOT aparecer una columna de llamadas, ni vacía: un vacío se lee como «no
   consume la API».
5. **Given** una severidad habilitada sin casos en el período, **When** se lee el contraste,
   **Then** **aparece**. Es la señal de que se paga por algo que no se usa.
6. **Given** un Director Financiero, **When** busca esta pantalla, **Then** no la ve en su menú
   y no entra. Diseñar el catálogo no es cobrar el mes.
7. **Given** un Administrador, **When** navega, **Then** ve las tres pantallas. Su papel no está
   repartido.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no una métrica en 0 %.
- **Mes natural.** MRR y NRR declaran el mes aplicado; no se presentan como si el rango pedido
  fuera el medido.
- **Una zona falla y las otras no.** El resto de la pantalla sigue; la zona fallida lo dice.
- **Cifra parcial o convención.** Sin periodicidad, dimensión de API pendiente, mes resuelto: la
  pantalla **lo dice junto a la cifra**. Esconderlo convierte un hueco en un indicador de la
  empresa.
- **Plan o cliente desconocido.** Aparece con esa etiqueta y sigue en el total.
- **Vigencia invertida.** No produce una duración negativa en pantalla; si el backend la aísla,
  se lee como dato inconsistente, no como un plazo raro.
- **Sin autoridad.** Cada director no entra a la materia ajena. Cliente, Operador y cualquier
  rol ajeno no entran a ninguna de las tres.
- **Dato sensible.** Ninguna pantalla muestra medio de cobro, fiscal ni quién resolvió una
  solicitud, **tampoco al director de esa materia**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Cobro e ingreso,
  Movimientos de cartera, Catálogo y uso— y MUST NOT añadir tarjetas al catálogo de planes ni a
  los listados simples de Suscripciones.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los trece informes que el backend publica**,
  cada uno en la pantalla de su materia. MUST NOT inventar un catorce ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**: métrica o contexto arriba a la
  izquierda; período arriba a la derecha; visual principal en la diagonal; lectura o implicación
  abajo a la derecha. MUST NOT ser una grilla de tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques** simultáneos del sistema de
  diseño. En Cobro e ingreso, cobro al primer intento, dunning y clientes sin método MUST quedar
  en segundo plano.
- **FR-UI-005**: El período MUST ser la única acción de filtrado de esta capa. Un cambio MUST
  refrescar todas las zonas de la pantalla. MUST NOT inventarse exportación: el backend no la
  ofrece.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de un período con ceros
  reales (backend FR-035).
- **FR-UI-007**: Un denominador ausente o una periodicidad que no se pudo normalizar MUST verse
  **sin dato** / **aparte**, nunca como 0 de ingreso (backend FR-012, FR-035).
- **FR-UI-008**: En Cobro e ingreso, el MRR MUST **no** incluir una suscripción cancelada
  (backend FR-006, SC-002). MUST mostrar la variación en nuevo, expansión, contracción y baja,
  no solo el neto (backend FR-014).
- **FR-UI-009**: En Cobro e ingreso, los ingresos MUST hacer visible que las notas de crédito
  **restan**. MUST NOT presentar el facturado sin signo como si fuera el neto (backend FR-015,
  SC-006).
- **FR-UI-010**: En Cobro e ingreso, una factura en disputa MUST NOT leerse como impaga ni como
  mora (backend FR-016, SC-005).
- **FR-UI-011**: En Cobro e ingreso y en Movimientos de cartera, MRR y NRR MUST declarar el **mes
  natural** realmente aplicado, aunque el período pedido no coincida con un mes cerrado.
- **FR-UI-012**: En Movimientos de cartera, el NRR MUST presentar la cohorte de clientes
  **existentes al inicio** y MUST NOT incluir a los nuevos como retención (backend FR-022).
- **FR-UI-013**: En Movimientos de cartera, el tipo de movimiento MUST leerse del **delta de
  precio**, no del nivel del plan (backend FR-020).
- **FR-UI-014**: En Movimientos de cartera, una solicitud pendiente MUST quedar fuera de la
  mediana y verse en **pendientes**. Una rechazada MUST contar como resuelta (backend FR-023,
  FR-024, SC-007). MUST NOT desglosar por quién la resolvió (backend FR-033).
- **FR-UI-015**: En Catálogo y uso, un plan de precio cero MUST contar en clientes y aportar cero
  ingreso, con ambas cifras visibles (backend FR-028, SC-010).
- **FR-UI-016**: En Catálogo y uso, la utilización MUST mostrar **lo usado y lo contratado**, no
  solo el porcentaje (backend FR-027). MUST declarar que la dimensión de llamadas API falta, y
  MUST NOT mostrar ninguna columna de llamadas, ni vacía (backend FR-030).
- **FR-UI-017**: En Catálogo y uso, una severidad habilitada y no usada MUST aparecer (backend
  FR-026).
- **FR-UI-018**: Las tres pantallas MUST NOT mostrar medio de cobro, identificador fiscal ni
  identidad de quien resolvió, para ningún rol (backend FR-032, FR-033, FR-041, SC-009).
- **FR-UI-019**: Las tres pantallas MUST NOT dibujar mapas ni pedir posiciones.
- **FR-UI-020**: **Cobro e ingreso** y **Movimientos de cartera** MUST ser visibles y accesibles
  para el **Director Financiero** y el **Administrador**. El Director de Estrategia MUST NOT
  verlas en el menú ni entrar (backend FR-038).
- **FR-UI-021**: **Catálogo y uso** MUST ser visible y accesible para el **Director de
  Estrategia** y el **Administrador**. El Director Financiero MUST NOT verla en el menú ni entrar
  (backend FR-039).
- **FR-UI-022**: Cliente, Operador y cualquier rol ajeno MUST NOT entrar a ninguna de las tres
  (backend FR-040). El cliente que ve su factura no gana esta lectura de cartera.
- **FR-UI-023**: Ver un informe MUST NOT habilitar emitir factura, cambiar de plan, cobrar ni
  cualquier acción operativa. No hay llamada a la acción de negocio en la esquina inferior
  derecha: hay **lectura**.
- **FR-UI-024**: Si el backend declara cobertura incompleta, mes aplicado, periodicidad o moneda,
  la pantalla MUST mostrarlo junto a la cifra. MUST NOT silenciarlo.
- **FR-UI-025**: MUST NOT existir un tablero o enlace único «Suscripciones (gestión)» que reúna
  las dos materias. Las tres pantallas son historias distintas; las dos primeras comparten
  audiencia, no pantalla.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director Financiero identifica el MRR de Cobro e ingreso en **menos de 5
  segundos** sin leer un párrafo.
- **SC-F02**: Un Director de Estrategia identifica el reparto de cartera en **menos de 5
  segundos**, y ve clientes e ingreso por separado.
- **SC-F03**: Un Director Financiero **no** encuentra Catálogo y uso en su menú. Un Director de
  Estrategia **no** encuentra Cobro e ingreso ni Movimientos de cartera en el suyo.
- **SC-F04**: Una suscripción cancelada no aumenta el MRR visible.
- **SC-F05**: Los ingresos con nota de crédito se leen **menores** que el facturado; un
  observador ve cuánto se restó.
- **SC-F06**: El NRR no se interpreta como crecimiento bruto: los nuevos del mes no están en la
  cohorte, y eso se puede comprobar en pantalla.
- **SC-F07**: Una solicitud pendiente no mejora el tiempo de resolución visible.
- **SC-F08**: Cobro e ingreso no presenta seis bloques del mismo peso; un recuento de la vista
  principal queda en **8 o menos**.
- **SC-F09**: Un Cliente y un Operador **no** acceden a ninguna de las tres.
- **SC-F10**: En ninguna de las tres aparecen medios de cobro, fiscal, identidad de administrador
  ni mapas.
- **SC-F11**: Un período sin datos no se parece a un período con ceros.
- **SC-F12**: Las tres pantallas se distinguen del catálogo de planes y de los listados simples:
  no reutilizan su disposición ni les añaden tarjetas.
- **SC-F13**: La utilización no se lee como consumo de API: no hay columna de llamadas, y la
  nota de dimensión pendiente está visible.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni un tablero de departamento.
- **Materia**: finanzas o catálogo. Decide quién ve la pantalla, no solo quién entra al dato.
- **Zona Z**: métrica, período, visual grande, lectura. Cuatro zonas, no trece tarjetas.
- **Período**: el único filtro; por defecto los últimos 30 días. MRR y NRR se resuelven a mes
  natural y lo declaran.
- **Lectura**: el texto o bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los trece publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días, como asume el backend. MRR y NRR usan mes
  natural y lo declaran en la respuesta.
- El Administrador entra a las tres; cada director ve su materia entera, sin acotamiento por
  cuenta de cliente.
- El patrón Z ya está demostrado; esta capa lo copia, no lo reinventa. Lo que no se copia es la
  audiencia única.
- El catálogo de planes y los listados simples de Suscripciones no se tocan.
- No hay exportación ni programación de envío en esta pasada.
- Las cifras de hoy salen de **cuatro suscripciones**: son correctas y no representativas. La
  pantalla no inventa volumen; muestra lo que hay.
- Cliente sigue viendo su factura y su plan en los flujos operativos; no gana estas lecturas de
  gestión.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Catálogo de planes y listados simples | Ya existen; no se les añaden tarjetas |
| Un tablero único de departamento | La autoridad está repartida; fusionarlo la anularía |
| Medios de cobro, fiscal e identidad de quien resolvió | Exclusión constitucional; el backend no los entrega |
| Columna de llamadas API | Pertenece a Partners; un vacío afirmaría consumo cero |
| Acciones operativas (emitir, cobrar, cambiar plan) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Cliente, Operador | No son la autoridad de estos informes compuestos |
| Cambiar OpenAPI, consultas o permisos del backend | Depends-on |
| Frontend de Emergencias, Red Operativa, Ventas u otros | Mismo patrón, otro módulo |
| Informes estratégicos | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período único, menú por materia. SC-F01, SC-F03. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (cancelada fuera del MRR, notas restan, pendiente fuera de la mediana, plan cero visible). No inventa métricas. |
| **Security** | Reparte quién entra **y** quién ve el enlace. Exclusión constitucional de dato sensible también en pantalla. |
| **Safety** | Un MRR inflado o un NRR con altas nuevas se lee mal al decidir precio o cobro; FR-UI-008 y FR-UI-012 lo impiden. No hay cadena de despacho: Safety se limita a no inducir una decisión financiera falsa. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas copian el patrón Z; la audiencia no. |
| **Performance Efficiency** | Heredada del backend. La pantalla no recalcula. Umbral de esta capa: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio con sistemas externos en esta capa. |
| **Flexibility** | No aplica: no se agrupa más allá de plan y tipo de cliente que el backend ya entrega. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
