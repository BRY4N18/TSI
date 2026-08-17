# Feature Specification: Informes Compuestos de Red Operativa — Frontend

**Feature Branch / capa**: `002-tactico/Red-Operativa/informes-compuestos-modelo/frontend`

**Created**: 2026-08-16

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que Emergencias) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

---

## Contexto

El backend de este módulo **ya publica los quince informes**. No hay trece vigilados que omitir:
aquí los quince son construcción nueva y los quince se pintan.

Esta capa entrega **tres pantallas nuevas**. No se mezclan con el índice de listados de Red
Operativa: ese índice ya existe y se queda como está.

### La diferencia respecto a Emergencias: no hay un solo jefe

En Emergencias un Director de Operaciones ve las tres historias. Aquí la autoridad **está
repartida** (SRS §5.1, backend FR-025):

| Materia | Quién la gobierna | Qué ve |
|---|---|---|
| **Crecimiento** | Director de Expansión | Flota, cobertura, mercados y retirada |
| **Validación** | Director Tecnológico | Cómo se aprueba o rechaza una región |
| **Ambas** | Administrador | Las tres pantallas, con el acotamiento que ya tiene |

Cada director **MUST NOT** ver la materia del otro. No hay un tablero único «Red Operativa» que
fusione las dos lecturas «porque es el mismo departamento». Eso es exactamente el error que el
backend ya impide: admitir a las dos autoridades y quedarse tranquilo.

La agrupación de pantallas sigue la **materia**, no el número de objetivo (OT11 / OT12 / OT13).
Solo dos informes miden *cómo se valida* una región. El resto —incluida la retirada y el tiempo
de puesta en operación— es de quien decide dónde crecer. «Regiones en riesgo» habla de regiones
y **no** es validación: habla de si el mercado aguanta.

Cada director ve **solo sus enlaces**. Un ítem gris o un acceso denegado después de entrar
descubrirá al otro cargo. El sistema de diseño lo prohíbe: el menú de cada rol contiene únicamente
lo que ese rol puede abrir.

El ojo recorre el **mismo patrón Z** que Emergencias:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que dé de alta o despublique.
   Ver no habilita a decidir.

**No hay mapas.** El backend no entrega coordenadas. El visual grande es una distribución o una
tendencia, nunca un plano.

### Qué entra en cada pantalla

| Pantalla | Audiencia | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|---|
| **Flota y cobertura** | Expansión | ¿Hay quién atienda, y dónde falta? | Condados en cobertura crítica | Unidades por estado | Disponibilidad declarada | Cobertura por región, pendientes de primer acceso, rendimiento por proveedor, rotación, bajas forzadas |
| **Mercados y retirada** | Expansión | ¿Dónde se abre y dónde se sostiene el mercado? | Mercados activos | Tiempo de puesta en operación | Regiones en riesgo | Casos al despublicar, tiempo pérdida → despublicación |
| **Criterios de validación** | Tecnológico | ¿Se aprueba a la primera, y por qué se rechaza? | Tasa al primer intento | Motivos de rechazo | Qué se está contando (intentos, no regiones) | — |

Flota y cobertura tiene ocho informes. Si los ocho salen del mismo tamaño, deja de ser Z y se
vuelve catálogo. Los cinco de apoyo **MUST** quedar en segundo plano (detalle plegable o franja
menor), para no pasar de 6–8 bloques.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Expansión ve el estado real de la flota (Priority: P1) 🎯 MVP

El Director de Expansión abre **Flota y cobertura**, elige un período y ve de inmediato dónde
falta cobertura. El visual grande reparte las unidades por el estado que registró la operación
—incluido «En Misión», que el catálogo operativo no define—. Abajo, la disponibilidad: el
porcentaje de tiempo que cada unidad estuvo activa, o **ausente** si no hay transiciones.

**Why this priority**: es el bloque más grande, el sustrato ya está, y contiene el indicador que
hoy no se ve en ningún listado. Una sola pantalla basta para demostrar el patrón Z **y** que este
director no ve validación.

**Independent Test**: con un período que tenga al menos un condado sin unidades disponibles, el
héroe nombra ese condado y, si no tiene vecinos, lo dice. Un Director Tecnológico **no** ve el
enlace ni entra. Un visitante sin autoridad no entra.

**Acceptance Scenarios**:

1. **Given** un Director de Expansión autenticado, **When** abre Flota y cobertura, **Then** ve
   el patrón Z: métrica a la izquierda, período a la derecha, visual grande en el centro, lectura
   abajo a la derecha.
2. **Given** una unidad que pasó por «En Misión», **When** carga el visual de estados, **Then**
   ese estado **aparece**. Omitirlo perdería transiciones reales.
3. **Given** una unidad sin ninguna transición en el período, **When** se muestra la
   disponibilidad, **Then** se lee **ausente**, nunca 0 %. No se sabe en qué estado estuvo.
4. **Given** un condado sin unidades disponibles y sin vecinos declarados, **When** aparece en
   cobertura crítica, **Then** se señala **sin alternativas**. Omitirlo escondería el caso más grave.
5. **Given** un Director Tecnológico, un Cliente, un Proveedor o un Operador, **When** intenta
   entrar, **Then** no ve la pantalla. El listado de flota del proveedor no es esta lectura de
   gestión.

---

### User Story 2 - El Director de Expansión mide dónde se abre y dónde se sostiene el mercado (Priority: P1)

El Director de Expansión abre **Mercados y retirada**. Arriba a la izquierda, cuántos mercados
están activos. El visual grande es el tiempo de puesta en operación —con la advertencia de que
los 30 días son una **convención del informe**, no un plazo que el sistema guarde—. Abajo, las
regiones publicadas bajo el umbral. Los dos informes de despublicación se pueden ver sin competir
con el héroe, y **dicen desde cuándo su medida es exacta**.

**Why this priority**: junta lo que suena a «regiones» y **no** es validación. Sin esta pantalla,
el Tecnológico o el de Expansión acabarían viendo la materia del otro por el nombre.

**Independent Test**: cambiar el período refresca las zonas. Una región que aún no llegó a
producción **no** aparece como 0 días ni como incumplimiento. Un histórico vacío de
despublicación no se lee como «nunca pasó». El Tecnológico no entra.

**Acceptance Scenarios**:

1. **Given** el Director de Expansión, **When** abre Mercados y retirada, **Then** el héroe es
   mercados activos, el visual grande es el tiempo de puesta en operación, y las regiones en
   riesgo están en la lectura de abajo a la derecha.
2. **Given** el tiempo de puesta en operación, **When** se muestra, **Then** la pantalla dice que
   el objetivo en días es una convención del informe y **no** un acuerdo guardado. Pintarlo como
   incumplimiento de un SLA inventaría un plazo.
3. **Given** una región que aún no está en producción, **When** aparece (o no) en esa medida,
   **Then** sus días y su cumplimiento se ven **ausentes**, no como cero ni como fallo.
4. **Given** los informes de despublicación, **When** se muestran, **Then** se ve **desde qué
   fecha la medida es exacta**. Un resultado vacío no se presenta como «nunca ocurrió».
5. **Given** un Director Tecnológico, **When** busca esta pantalla, **Then** no la ve en su menú
   y no entra. Decidir que un mercado se cierra no es un criterio de validación.

---

### User Story 3 - El Director Tecnológico ve cómo se valida, no dónde se crece (Priority: P1)

El Director Tecnológico abre **Criterios de validación**. El héroe es la tasa de aprobación al
primer intento. El visual grande son los motivos de rechazo. Abajo a la derecha se lee que se
cuentan **intentos**, no regiones: una región aprobada a la tercera no aprobó a la primera.

**Why this priority**: son los únicos dos informes de su materia. Si se mezclaran en un tablero
de departamento, esta historia desaparecería o se filtraría al de Expansión.

**Independent Test**: una región rechazada dos veces y aprobada a la tercera **no** sube la tasa
como si hubiera aprobado al primero. El Director de Expansión no ve el enlace ni entra. Un motivo
ausente no aparece como categoría vacía.

**Acceptance Scenarios**:

1. **Given** un Director Tecnológico autenticado, **When** abre Criterios de validación, **Then**
   ve el patrón Z con la tasa al primer intento como héroe y los motivos de rechazo como visual
   grande.
2. **Given** la lectura, **When** se muestra, **Then** declara que el grano son **intentos de
   validación**, no regiones. Un porcentaje sin esa frase se lee como «las regiones se aprueban
   a la primera».
3. **Given** validaciones aprobadas, **When** se muestran los motivos de rechazo, **Then** no
   aparecen: solo se agrupan rechazos, y un motivo ausente no es una categoría.
4. **Given** un Director de Expansión, **When** busca esta pantalla, **Then** no la ve en su menú
   y no entra. El detalle de por qué se rechaza una región no le sirve a quien decide dónde crecer.
5. **Given** un Administrador, **When** navega, **Then** ve las tres pantallas. Su papel no está
   repartido.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no una métrica en 0 %.
- **Una zona falla y las otras no.** El resto de la pantalla sigue; la zona fallida lo dice.
- **Cifra parcial o convención.** Si el backend declara umbral, objetivo, alcance o que el dato
  no cubre lo que el nombre promete, la pantalla **lo dice junto a la cifra**. Esconderlo convierte
  un hueco o una convención en un indicador de la empresa.
- **Entidad desconocida.** Un condado, proveedor o región sin nombre **aparece como desconocido**
  y sigue en el total.
- **Estado fuera de catálogo.** Un estado de unidad que el catálogo operativo no define se muestra
  con el nombre que registró la operación. Nunca se descarta.
- **Sin autoridad.** Cada director no entra a la materia ajena. Cliente, Proveedor, Operador y
  cualquier rol ajeno no entran a ninguna de las tres.
- **Dato sensible.** Ninguna pantalla muestra coordenadas, identidad de personas (incluido quien
  validó una región) ni contacto de proveedor, **tampoco al director de esa materia**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Flota y cobertura,
  Mercados y retirada, Criterios de validación— y MUST NOT añadir tarjetas al índice de listados
  de Red Operativa.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los quince informes que el backend publica**,
  cada uno en la pantalla de su materia. MUST NOT inventar un dieciséis ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**: métrica o contexto arriba a la
  izquierda; período arriba a la derecha; visual principal en la diagonal; lectura o implicación
  abajo a la derecha. MUST NOT ser una grilla de tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques** simultáneos del sistema de
  diseño. En Flota y cobertura, los cinco informes de apoyo MUST quedar en segundo plano.
- **FR-UI-005**: El período MUST ser la única acción de filtrado de esta capa. Un cambio MUST
  refrescar todas las zonas de la pantalla. MUST NOT inventarse exportación: el backend no la ofrece.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de un período con ceros
  reales (backend FR-023).
- **FR-UI-007**: Un denominador ausente, una referencia que no existe o una unidad sin
  transiciones MUST verse **sin dato** / **ausente**, nunca como 0 (backend FR-008, FR-022).
- **FR-UI-008**: En Flota y cobertura, el visual de estados MUST mostrar el estado **tal como lo
  registró la operación**, incluido uno que el catálogo operativo no defina. MUST NOT unir con
  ese catálogo para decidir qué filas caben (backend FR-006).
- **FR-UI-009**: En Flota y cobertura, un condado en cobertura crítica **sin vecinos** MUST
  leerse como **sin alternativas**, no omitirse (backend FR-014).
- **FR-UI-010**: En Mercados y retirada, el tiempo de puesta en operación MUST llevar la
  advertencia de que el objetivo en días es una **convención del informe** y no un plazo
  guardado. Una región que aún no llegó a producción MUST verse ausente, no como cero días
  (backend FR-016).
- **FR-UI-011**: En Mercados y retirada, los informes de despublicación MUST mostrar **desde qué
  fecha su medida es exacta**. Un resultado vacío MUST NOT leerse como «nunca ocurrió»
  (backend FR-034, FR-035).
- **FR-UI-012**: En Criterios de validación, la lectura MUST declarar que se cuentan **intentos**,
  no regiones (backend FR-017). MUST NOT mostrar solo el porcentaje.
- **FR-UI-013**: Las tres pantallas MUST NOT mostrar coordenadas, identidad de personas ni
  contacto de proveedor, para ningún rol (backend FR-020, FR-021, FR-026).
- **FR-UI-014**: Las tres pantallas MUST NOT dibujar mapas ni pedir posiciones.
- **FR-UI-015**: **Flota y cobertura** y **Mercados y retirada** MUST ser visibles y accesibles
  para el **Director de Expansión** y el **Administrador**. El Director Tecnológico MUST NOT
  verlas en el menú ni entrar (backend FR-025).
- **FR-UI-016**: **Criterios de validación** MUST ser visible y accesible para el **Director
  Tecnológico** y el **Administrador**. El Director de Expansión MUST NOT verla en el menú ni
  entrar (backend FR-025).
- **FR-UI-017**: Cliente, Proveedor, Operador y cualquier rol ajeno MUST NOT entrar a ninguna de
  las tres. El listado acotado de flota del proveedor no es esta lectura.
- **FR-UI-018**: Ver un informe MUST NOT habilitar alta, baja, validar, despublicar ni cualquier
  acción operativa. No hay llamada a la acción de negocio en la esquina inferior derecha: hay
  **lectura**.
- **FR-UI-019**: Si el backend declara cobertura incompleta, umbral, objetivo o un alcance, la
  pantalla MUST mostrarlo junto a la cifra. MUST NOT silenciarlo. En particular, si la cobertura
  no puede repartirse por región, MUST decirlo junto a esa cifra.
- **FR-UI-020**: MUST NOT existir un tablero o enlace único «Red Operativa (gestión)» que reúna
  las dos materias. Las tres pantallas son historias distintas; las dos primeras comparten
  audiencia, no pantalla.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director de Expansión identifica la métrica principal de Flota y cobertura en
  **menos de 5 segundos** sin leer un párrafo.
- **SC-F02**: Un Director Tecnológico identifica la tasa al primer intento en **menos de 5
  segundos**, y la lectura nombra que se cuentan intentos.
- **SC-F03**: Un Director de Expansión **no** encuentra Criterios de validación en su menú. Un
  Director Tecnológico **no** encuentra Flota y cobertura ni Mercados y retirada en el suyo.
- **SC-F04**: Una unidad sin transiciones se lee **ausente** en disponibilidad; un observador no
  la confunde con 0 %.
- **SC-F05**: Un condado crítico sin vecinos se lee **sin alternativas**; no desaparece.
- **SC-F06**: El tiempo de puesta en operación no se interpreta como incumplimiento de un plazo
  firmado: la convención está visible junto al visual grande.
- **SC-F07**: Los informes de despublicación muestran desde cuándo la medida es exacta; un vacío
  no se lee como «nunca pasó».
- **SC-F08**: Flota y cobertura no presenta ocho bloques del mismo peso; un recuento de la vista
  principal queda en **8 o menos**.
- **SC-F09**: Un Cliente, un Proveedor y un Operador **no** acceden a ninguna de las tres.
- **SC-F10**: En ninguna de las tres aparecen coordenadas, nombres de validadores ni mapas.
- **SC-F11**: Un período sin datos no se parece a un período con ceros.
- **SC-F12**: Las tres pantallas se distinguen del índice de listados: no reutilizan su
  disposición ni le añaden tarjetas.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni un tablero de departamento.
- **Materia**: crecimiento o validación. Decide quién ve la pantalla, no solo quién entra al
  dato.
- **Zona Z**: métrica, período, visual grande, lectura. Cuatro zonas, no quince tarjetas.
- **Período**: el único filtro; por defecto los últimos 30 días (igual que el backend).
- **Lectura**: el texto o bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los quince publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días, como asume el backend.
- El Administrador entra a las tres con el mismo acotamiento que en los listados; cada director
  ve su materia entera, sin acotamiento por titularidad.
- El patrón Z ya está demostrado en Emergencias; esta capa lo copia, no lo reinventa. Lo que no
  se copia es la audiencia única.
- Los listados simples de Red Operativa ya filtran por rol en su índice. Esta capa no los toca.
- No hay exportación ni programación de envío en esta pasada.
- Cliente y Proveedor siguen viendo su flota en los listados; no ganan estas lecturas de gestión.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Índice y páginas de listados de Red Operativa | Ya existen; no se les añaden tarjetas |
| Un tablero único de departamento | La autoridad está repartida; fusionarlo la anularía |
| Mapas y coordenadas | Exclusión constitucional; el backend no las entrega |
| Acciones operativas (alta, baja, validar, despublicar) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Cliente, Proveedor, Operador | No son la autoridad de estos informes compuestos |
| Cambiar OpenAPI, consultas o permisos del backend | Depends-on |
| Frontend de Emergencias u otros departamentos | Mismo patrón, otro módulo |
| Informes estratégicos | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período único, menú por materia. SC-F01, SC-F03. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (ausente ≠ 0 %, sin alternativas, medida exacta desde). No inventa métricas. |
| **Security** | Reparte quién entra **y** quién ve el enlace. Exclusión constitucional de dato sensible también en pantalla. |
| **Safety** | Un 0 % donde no hay transiciones, o un «nunca se despublicó» donde el modelo no observó, se lee mal bajo presión; FR-UI-007 y FR-UI-011 lo impiden. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas comparten el patrón Z; la audiencia no. |
| **Performance Efficiency** | Heredada del backend. La pantalla no recalcula. |
| **Compatibility** | No aplica: no hay intercambio con sistemas externos en esta capa. |
| **Flexibility** | No aplica: no se agrupa por región más allá de lo que el backend ya entrega por nombre. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
