# Feature Specification: Informes Compuestos de Partners y API — Frontend

**Feature Branch / capa**: `002-tactico/Partners-API/informes-compuestos-modelo/frontend`

**Created**: 2026-08-17

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que Emergencias, Red Operativa, Ventas, Suscripciones y
Soporte) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques por vista; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

---

## Contexto

El backend de este módulo **ya publica trece informes** de OT08, OT09 y OT10. El catorceavo del
catálogo —alcance geográfico— **no se pinta**: el log no registra la zona y **no se infiere**.

Esta capa entrega **tres pantallas nuevas**. No se mezclan con los listados simples, con la consola
de logs, ni con las **métricas y el reporte mensual ya construidos** en el portal de partners: esos
se quedan como están. Siguen sirviendo al partner y al gestor operativo. Las cifras de latencia
**difieren a propósito** —el operativo da solo media; esta lectura trae p95 y el tamaño de la
muestra— y las dos superficies MUST distinguirse para que nadie las compare como si midieran lo
mismo.

**La autoridad no está repartida por materia.** El Director Tecnológico cubre las tres historias.
El Administrador también. Un **partner** no entra: son cifras comparadas de todos los partners. El
Desarrollador de APIs sigue en la consola operativa; **no** gana estas lecturas de gestión.

Cada cargo **MUST** ver **solo sus enlaces**. Un ítem gris o un acceso denegado después de entrar
descubrirá al partner (o al gestor operativo) una superficie que no le corresponde. El menú de cada
rol contiene únicamente lo que ese rol puede abrir.

El ojo recorre el **mismo patrón Z**:

1. Arriba a la izquierda: contexto o métrica principal.
2. Arriba a la derecha: el período (la única acción de esta capa).
3. Diagonal: el visual más grande, que baja la mirada.
4. Abajo a la derecha: la lectura — qué implica el número, no un botón que revoque una credencial
   o cambie un cupo. Ver no habilita a decidir.

**No hay fichas de llamada ni de persona.** El backend no entrega IP, secreto, contacto técnico ni
quién ejecutó un cambio. El visual grande es una distribución o una tendencia. Los partners se
nombran por la etiqueta comercial del modelo, no por correo ni por persona de contacto.

### La cifra que no se puede mostrar sola

Hoy hay **dieciocho llamadas** en el detalle. Una p95 sobre un endpoint con dos observaciones
**puede ser literalmente la segunda más lenta**. Mostrar el percentil sin el número de muestras, o
sin decir que aún no es fiable, convierte una anécdota en un indicador de plataforma. El backend ya
devuelve media, p95, muestras y la marca de fiabilidad; esta capa MUST pintarlas juntas. Un héroe
de «p95 = 90 ms» y las muestras en una nota es exactamente el defecto que el backend acaba de
corregir frente al operativo.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual grande | Lectura (abajo derecha) | Apoyo |
|---|---|---|---|---|---|
| **Consumo de la API** | ¿Cuánto se usa y cómo de lenta y errática es? | p95 **y** media **y** muestras, con la marca de si el percentil es fiable | Taxonomía de errores **por clase** (cupo, autorización, servicio) | Comparativa entre partners: volumen, error y latencia — **nunca** un rastro de origen | Métricas por partner, reporte mensual, consumo por endpoint, participación de ingresos (excedente vs base) |
| **Incorporación** | ¿Por qué no llega a producción y qué contrato usa? | Adopción de versiones **por (servicio, versión)**, declarada **derivada** | Motivo de credencial inactiva: revocada, cascada, expirada y suspensión **por separado** | Tiempo de incorporación: en proceso **aparte**, no cero | Tasa de rechazo de producción **por motivo**, nunca por persona |
| **Entrega contratada** | ¿Cuántos clientes ya integran y por qué canal? | % con integración activa frente a la meta ≥70 %, con **todos** los clientes en el denominador | Volumen de expedientes: portal y API **por separado** | Qué implicaría un 100 % (contar solo a quienes ya tienen partner) | — |

Consumo tiene siete informes. Si los siete salen del mismo tamaño, deja de ser Z y se vuelve
catálogo. Métricas, reporte, endpoint e ingresos **MUST** quedar en segundo plano (detalle
plegable o franja menor), para no pasar de 6–8 bloques.

Incorporación tiene cuatro. El rechazo **MUST** quedar en apoyo: el BSC es la adopción, y el
hallazgo diario es el motivo de inactividad.

Entrega tiene dos en alcance. MUST NOT inventar una tercera zona de «fuera de zona».

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director Tecnológico mide el consumo real (Priority: P1) 🎯 MVP

El Director Tecnológico abre **Consumo de la API**, elige un período y ve de inmediato la latencia
p95 **junto** a la media y al número de llamadas. Si la muestra no alcanza el mínimo, se lee que
el percentil **no es fiable** y la fila **sigue a la vista**. El visual grande reparte los
errores por clase: un tope de cupo no se parece a un fallo del servicio. Abajo, qué partner se
desvía. Métricas, reporte, endpoints e ingresos se pueden abrir sin competir con el héroe.

**Why this priority**: contiene dos indicadores BSC y corrige en pantalla el defecto del operativo
(solo media). Una sola vista basta para demostrar el patrón Z, el trío p95/media/muestras y que
esta lectura no es la consola de métricas.

**Independent Test**: un período con pocas llamadas muestra p95, media y muestras **en el mismo
bloque**, con la marca de no fiable visible. Un partner sin tráfico **aparece en cero**. Un
partner autenticado **no** ve el enlace ni entra. Las métricas operativas **siguen existiendo**
y no se confunden con esta pantalla.

**Acceptance Scenarios**:

1. **Given** un Director Tecnológico autenticado, **When** abre Consumo de la API, **Then** ve el
   patrón Z: métrica a la izquierda, período a la derecha, visual grande en el centro, lectura
   abajo a la derecha.
2. **Given** la latencia, **When** se muestra, **Then** p95, media y número de muestras están
   **en el mismo bloque**. MUST NOT haber un héroe de p95 solo y las muestras en una nota, un pie
   u otra pantalla.
3. **Given** un endpoint con menos llamadas que el mínimo declarado, **When** se mira el héroe o
   el desglose, **Then** se lee que el percentil **no es fiable** y la cifra **no desaparece**.
4. **Given** llamadas 429, 403 y 500, **When** se mira la taxonomía, **Then** hay **tres** clases.
   MUST NOT existir un total «errores» que las sume como si fueran el mismo problema.
5. **Given** un partner sin llamadas en el período, **When** se pide la comparativa o las
   métricas, **Then** aparece con **cero**, no omitido.
6. **Given** excedente de API en el período, **When** se abre el apoyo de ingresos, **Then** el
   excedente se ve **aparte** del ingreso base.
7. **Given** las métricas o el reporte mensual que ya existen en el portal, **When** el Director
   navega, **Then** esta pantalla **no** los reemplaza en el menú ni reutiliza su disposición. Se
   distinguen, y se declara que la latencia de esta lectura **no es** la media del operativo.
8. **Given** un Partner, un Desarrollador de APIs, un Cliente o un Operador, **When** intenta
   entrar, **Then** no ve la pantalla.

---

### User Story 2 - El Director Tecnológico vigila la incorporación (Priority: P2)

El Director Tecnológico abre **Incorporación**. Arriba a la izquierda, qué versión del contrato
se usa de verdad —por servicio y versión, no por el nombre `'v1'` solo— y que esa versión **se
derivó del endpoint**. El visual grande es por qué una credencial está inactiva: revocada no es
caducada. Abajo, cuánto tardan en llegar a producción: quien sigue en proceso **no** mejora la
media. El rechazo de solicitudes se puede ver por motivo, nunca por quién lo resolvió.

**Why this priority**: OT08 no tenía pantalla. Junta el BSC de adopción con el hallazgo que el
operativo no puede mostrar (cuatro motivos bajo el mismo «inactiva»).

**Independent Test**: dos servicios que comparten `'v1'` producen **dos** lecturas. Una credencial
revocada y una caducada no se mezclan. Un partner en proceso no aparece como cero días. El
partner no entra.

**Acceptance Scenarios**:

1. **Given** el Director Tecnológico, **When** abre Incorporación, **Then** el héroe es la
   adopción, el visual grande son los motivos de inactividad y el tiempo está abajo a la
   derecha.
2. **Given** llamadas a dos servicios con la misma etiqueta de versión, **When** se muestra la
   adopción, **Then** hay **dos** agrupaciones. MUST NOT colapsarlas en una sola barra `'v1'`.
3. **Given** la adopción, **When** se muestra, **Then** declara que la versión es **derivada**.
   MUST NOT presentarse como un dato que el log registró.
4. **Given** una credencial revocada y otra caducada, **When** se leen los motivos, **Then**
   están en **grupos distintos**. MUST NOT existir un recuento único «inactivas».
5. **Given** una credencial que nunca expira, **When** se mira la incorporación, **Then** **no**
   aparece como próxima a vencer ni infla un promedio de vigencia.
6. **Given** un partner que aún no llegó a producción, **When** se muestra el tiempo, **Then**
   queda **fuera** de la media y se cuenta como en proceso. MUST NOT leerse como cero días.
7. **Given** rechazos de producción, **When** se abre el apoyo, **Then** se agrupan **por
   motivo**. MUST NOT aparecer quién ejecutó el cambio.
8. **Given** un Partner o un Desarrollador de APIs, **When** busca esta pantalla, **Then** no la
   ve en su menú y no entra.

---

### User Story 3 - El Director Tecnológico verifica la entrega (Priority: P3)

El Director Tecnológico abre **Entrega contratada**. El héroe es el porcentaje de clientes con
integración activa **frente a la meta del 70 %**, y el denominador son **todos** los clientes. El
visual grande separa expedientes por portal y por API. Abajo, qué significaría pintar 100 %:
contar solo a quienes ya tienen partner.

**Why this priority**: es el último BSC, barato en modelo, fácil de mentir en pantalla si se
cambia el denominador.

**Independent Test**: con clientes sin partner, el porcentaje es **menor que 100 %**. Portal y
API no se funden. No hay zona de alcance geográfico. El partner no entra.

**Acceptance Scenarios**:

1. **Given** el Director Tecnológico, **When** abre Entrega contratada, **Then** el héroe es el
   porcentaje con meta, el visual grande son los dos canales y la lectura está abajo a la
   derecha.
2. **Given** clientes sin partner en el sistema, **When** se muestra el indicador, **Then** el
   porcentaje es **menor que 100 %** y se ve el total de clientes. MUST NOT calcularse solo
   sobre quienes ya integran.
3. **Given** la meta ≥70 %, **When** se muestra el héroe, **Then** la meta está **a la vista**
   junto al porcentaje, no en un pie.
4. **Given** entregas por portal y por API, **When** se mira el volumen, **Then** hay **dos**
   canales. MUST NOT existir un total único que los mezcle.
5. **Given** esta pantalla, **When** se recorre, **Then** **no** hay una zona de consultas fuera
   de zona ni un mapa. Inventarla acusaría un incumplimiento que el log no registró.
6. **Given** un Partner, **When** busca esta pantalla, **Then** no la ve y no entra.

---

### User Story 4 - El Administrador ve las tres; el partner no (Priority: P1)

El Administrador abre las mismas tres pantallas, con el mismo patrón Z. Un partner autenticado
**no** las ve en su menú. El Desarrollador de APIs sigue en la consola y en las métricas
operativas; **no** hereda esta lectura comparada.

**Why this priority**: el permiso demasiado ancho no produce síntoma hasta que un partner ve la
comparativa de todos. El menú es donde se impide, no un error después de entrar.

**Independent Test**: el Administrador entra a las tres. El Partner y el Desarrollador de APIs
no ven los enlaces. Un Cliente no entra.

**Acceptance Scenarios**:

1. **Given** un Administrador autenticado, **When** navega, **Then** ve las tres pantallas.
2. **Given** un Partner autenticado, **When** mira su menú, **Then** **no** aparecen Consumo,
   Incorporación ni Entrega. MUST NOT haber un ítem gris.
3. **Given** un Desarrollador de APIs, **When** abre la consola o las métricas operativas,
   **Then** esas superficies **siguen**. MUST NOT ganar estas tres lecturas de gestión.
4. **Given** un Cliente, un Operador o un Director Financiero, **When** busca estas pantallas,
   **Then** no las ve y no entra.

---

### Edge Cases

- **Período vacío.** Las tres pantallas muestran vacío explícito, no un p95 en 0 ni un 0 % de
  integración.
- **Dieciocho llamadas.** La pantalla no oculta los denominadores ni la marca de fiabilidad;
  tampoco adorna el número para que parezca un indicador maduro.
- **Partner sin tráfico.** Cero visible, no omitido.
- **Percentil no fiable.** Se lee y la cifra permanece.
- **Cuatro motivos de inactividad.** Juntarlos en «inactivas» esconde cuál hay que arreglar.
- **Centinela de vigencia.** Nunca expira ≠ una fecha lejana; no retirada ≠ 1970.
- **Versión derivada.** Si el path cambia de forma, las cifras se moverán sin que el log haya
  cambiado: la pantalla ya lo dijo.
- **Una zona falla y las otras no.** El resto de la pantalla sigue; la zona fallida lo dice.
- **Cifra parcial o convención.** Fiabilidad, derivación, diferencia con el operativo, meta:
  la pantalla **lo dice junto a la cifra**.
- **Sin autoridad.** Partner, Desarrollador de APIs, Cliente, Operador y cargos ajenos no
  entran.
- **Dato sensible.** Ninguna de las tres muestra IP, secreto, contacto técnico, ejecutor ni
  mapa, **tampoco al Director Tecnológico**.

---

## Functional Requirements (UI)

- **FR-UI-001**: Esta capa MUST entregar **exactamente tres pantallas** —Consumo de la API,
  Incorporación, Entrega contratada— y MUST NOT añadir tarjetas a los listados simples, a la
  consola de logs ni a las métricas y el reporte mensual ya construidos.
- **FR-UI-002**: Las tres pantallas MUST mostrar **los trece informes que el backend publica**,
  cada uno en la pantalla de su historia. MUST NOT inventar un catorceavo (alcance geográfico)
  ni omitir uno publicado.
- **FR-UI-003**: Cada pantalla MUST seguir el **patrón Z**: métrica o contexto arriba a la
  izquierda; período arriba a la derecha; visual principal en la diagonal; lectura o
  implicación abajo a la derecha. MUST NOT ser una grilla de tarjetas del mismo peso.
- **FR-UI-004**: Cada vista MUST respetar el máximo de **6–8 bloques** simultáneos del sistema
  de diseño. En Consumo, métricas por partner, reporte mensual, consumo por endpoint y
  participación de ingresos MUST quedar en segundo plano. En Incorporación, la tasa de rechazo
  MUST quedar en apoyo.
- **FR-UI-005**: El período MUST ser la única acción de filtrado de esta capa. Un cambio MUST
  refrescar todas las zonas de la pantalla. MUST NOT inventarse exportación: el backend no la
  ofrece.
- **FR-UI-006**: Un período sin datos MUST verse como vacío, distinguible de un período con
  ceros reales (partner sin llamadas).
- **FR-UI-007**: Un denominador ausente MUST verse **sin dato**, nunca como 0 % de integración
  o 0 ms de latencia.
- **FR-UI-008**: En Consumo de la API, p95, media y número de muestras MUST mostrarse **en el
  mismo bloque**. MUST NOT separar las muestras a otra zona, pie o pantalla.
- **FR-UI-009**: En Consumo de la API, cuando el backend marca el percentil como no fiable, la
  pantalla MUST declararlo **junto a la cifra** y MUST NOT ocultar la fila.
- **FR-UI-010**: En Consumo de la API, límite de cupo, autorización y fallo de servicio MUST
  verse **por separado**. MUST NOT existir un total «errores» que los sume (backend SC-005).
- **FR-UI-011**: En Consumo de la API, un partner sin llamadas MUST aparecer con **cero**, no
  omitido (backend SC-006).
- **FR-UI-012**: En Consumo de la API, el excedente MUST verse aparte del ingreso base.
- **FR-UI-013**: En Consumo de la API, la pantalla MUST declararse distinta de las métricas y
  el reporte operativo, y MUST decir que la latencia de esta lectura **no es** la media de
  aquellos. MUST NOT reutilizar su disposición ni reemplazarlos en el menú.
- **FR-UI-014**: En Incorporación, la adopción MUST agruparse por **(servicio, versión)** y
  MUST declarar que la versión es **derivada** (backend SC de adopción).
- **FR-UI-015**: En Incorporación, revocada, cascada, expirada y suspensión manual MUST
  leerse en **grupos distintos**. MUST NOT fundirse en «inactivas» (backend SC-003).
- **FR-UI-016**: En Incorporación, una credencial que nunca expira MUST NOT pintarse como
  próxima a vencer ni entrar a un promedio de vigencia (backend SC-004).
- **FR-UI-017**: En Incorporación, un partner aún en proceso MUST contarse aparte y MUST NOT
  aportar cero días a la media (backend SC-009).
- **FR-UI-018**: En Incorporación, el rechazo MUST agruparse **por motivo**. MUST NOT mostrar
  quién ejecutó el cambio.
- **FR-UI-019**: En Entrega contratada, el porcentaje MUST usar **todos los clientes** como
  denominador y MUST mostrar la meta ≥70 % junto a la cifra (backend SC-007).
- **FR-UI-020**: En Entrega contratada, portal y API MUST verse como **canales distintos**.
- **FR-UI-021**: Las tres pantallas MUST NOT mostrar alcance geográfico, zonas contratadas ni
  mapas, ni inferirlos de un parámetro de consulta (backend FR-025).
- **FR-UI-022**: Las tres pantallas MUST NOT mostrar IP de origen, secreto, contacto técnico
  ni ejecutor de un cambio, para ningún rol (backend SC-008).
- **FR-UI-023**: Las tres pantallas MUST ser visibles y accesibles para el **Director
  Tecnológico** y el **Administrador**. Partner, Desarrollador de APIs, Cliente, Operador y
  cargos ajenos MUST NOT verlas en el menú ni entrar (backend FR-034).
- **FR-UI-024**: Ver un informe MUST NOT habilitar revocar, suspender, emitir credencial ni
  cambiar un cupo. No hay llamada a la acción de negocio en la esquina inferior derecha: hay
  **lectura**.
- **FR-UI-025**: Si el backend declara muestras, fiabilidad, derivación, diferencia con el
  operativo o meta, la pantalla MUST mostrarlo junto a la cifra. MUST NOT silenciarlo.
- **FR-UI-026**: MUST NOT existir un enlace que fusione estas tres historias con la consola, el
  reporte operativo o los listados simples. Son lecturas distintas.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director Tecnológico identifica p95, media y número de muestras de Consumo de
  la API en **menos de 5 segundos** sin leer un párrafo.
- **SC-F02**: No existe un estado de pantalla en el que se vea la p95 y no se vea, en el mismo
  bloque, el número de muestras.
- **SC-F03**: Un percentil marcado como no fiable sigue visible y se lee como no fiable; no
  desaparece la fila.
- **SC-F04**: 429, 403 y fallo de servicio no se suman en ninguna zona de errores.
- **SC-F05**: Un partner sin llamadas en el período aparece; no hay un listado que solo muestre
  a quien consumió.
- **SC-F06**: Consumo de la API se distingue de las métricas y el reporte operativo: no
  reutiliza su disposición y declara que la latencia no es la media de aquellos.
- **SC-F07**: Dos servicios con la misma etiqueta de versión no se colapsan en una sola barra.
- **SC-F08**: Revocada y caducada no comparten recuento. Un partner en proceso no aporta cero
  días a la media visible.
- **SC-F09**: Con clientes sin partner, el porcentaje de integración es menor que 100 % y la
  meta ≥70 % está a la vista.
- **SC-F10**: Portal y API no se funden. No hay zona de alcance geográfico ni mapa.
- **SC-F11**: Un Partner y un Desarrollador de APIs **no** acceden a ninguna de las tres. El
  Administrador sí a las tres.
- **SC-F12**: En ninguna de las tres aparecen IP, secreto, contacto técnico, ejecutor ni mapas.
- **SC-F13**: Un período sin datos no se parece a un período con ceros.
- **SC-F14**: Consumo de la API no presenta siete bloques del mismo peso; un recuento de la
  vista principal queda en **8 o menos**.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las tres; no es un listado ni la consola operativa.
- **Zona Z**: métrica, período, visual grande, lectura. Cuatro zonas, no trece tarjetas.
- **Período**: el único filtro; por defecto los últimos 30 días.
- **Trío p95 / media / muestras**: las tres cifras que MUST viajar juntas; no son tres widgets.
- **Marca de fiabilidad**: declara que el percentil aún no es un indicador.
- **Lectura**: el texto o bloque de abajo a la derecha que dice qué implica el número.

---

## Assumptions

- El backend de los trece publicados está en servicio. Esta capa no calcula cifras.
- El período por defecto son los últimos 30 días, como asume el backend.
- El Director Tecnológico y el Administrador ven las tres historias. El partner no. El
  Desarrollador de APIs permanece en la consola operativa.
- El patrón Z ya está demostrado; esta capa lo copia, no lo reinventa.
- Los listados simples, la consola de logs, las métricas y el reporte mensual operativos no se
  tocan ni se retiran.
- No hay exportación ni programación de envío en esta pasada.
- Las cifras de hoy salen de **dieciocho llamadas** de detalle: son correctas y no
  representativas. La pantalla no inventa volumen; muestra lo que hay y enseña las muestras.
- El mínimo de muestras para marcar el percentil lo resuelve el backend. Esta capa no ofrece un
  control extra de umbral.
- El informe de alcance geográfico sigue fuera; no reaparece por inferencia en esta capa.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Listados simples, consola de logs | Ya existen; no se les añaden tarjetas |
| Retirar métricas y reporte mensual operativos | Siguen sirviendo; la unificación no es de esta capa |
| Un tablero único de trece iguales | Rompe el patrón Z y la Ley de Hick |
| Alcance geográfico / mapas | El log no registra la zona; inferirlo acusaría en silencio |
| IP, secreto, contacto técnico, ejecutor | Exclusión constitucional; el backend no los entrega |
| Acciones operativas (revocar, suspender, emitir, cambiar cupo) | Ver no habilita a decidir |
| Exportar, imprimir, programar envíos | El backend no lo ofrece |
| Partner, Desarrollador de APIs, Cliente, Operador, cargos ajenos | No son la autoridad de estos compuestos |
| Cambiar OpenAPI, consultas o permisos del backend | Depends-on |
| Frontend de Cuentas u otros departamentos | Mismo patrón, otro módulo |
| Informes estratégicos | Otra capa |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Patrón Z, una historia por pantalla, ≤8 bloques, período único, trío p95/media/muestras inseparable, menú por rol. SC-F01, SC-F02, SC-F14. |
| **Functional Suitability** | Muestra las cifras que el backend ya corrige (p95 con muestras, clases de error, motivos distintos, denominador de todos los clientes). No inventa el alcance geográfico. |
| **Security** | Reutiliza quién entra (Director Tecnológico / Administrador). Exclusión constitucional de IP, secreto, contacto y ejecutor también en pantalla. El partner no ve comparativas de todos. |
| **Safety** | Un p95 sobre dos llamadas, o un 100 % de integración sobre quienes ya tienen partner, se lee mal al decidir cupos o plantilla; FR-UI-008, FR-UI-009 y FR-UI-019 lo impiden. No hay cadena de despacho: Safety se limita a no inducir una decisión de plataforma falsa. |
| **Reliability** | Vacío ≠ ceros; fallo de una zona no tumba las otras. |
| **Maintainability** | Capa `frontend/` separada; las tres pantallas copian el patrón Z ya usado. |
| **Performance Efficiency** | Heredada del backend. La pantalla no recalcula. Umbral de esta capa: reconocer el héroe en menos de 5 s. |
| **Compatibility** | No aplica: no hay intercambio con sistemas externos en esta capa. |
| **Flexibility** | No aplica: no se agrupa por región; el alcance geográfico está fuera y se declara. |

**Traceability**: índice [`../informes-compuestos-modelo.md`](../informes-compuestos-modelo.md).
