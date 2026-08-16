# Feature Specification: Informes Tácticos Simples de Cuentas y Clientes (Frontend)

**Feature Branch / capa**: `002-tactico/Cuentas-Clientes/informes-tacticos-simples/frontend`

**Created**: 2026-08-15

**Status**: Draft

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y
[`../backend/contracts/informes-tacticos-simples.openapi.yaml`](../backend/contracts/informes-tacticos-simples.openapi.yaml).
Esta capa **MUST NOT** redefinir reglas de negocio, filtros ni contratos REST.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)
— contrato común de frontend. **No se repite aquí.**

---

## Contexto

Es el **piloto** de la capa de frontend de listados tácticos, igual que este mismo departamento fue
el piloto del backend. Su función no es solo entregar ocho pantallas: es **validar que la capa
compartida sirve** antes de repetirla seis veces.

Los ocho endpoints ya están construidos, verdes y documentados. Aquí no se decide nada de negocio.

### Lo que este piloto NO puede validar ⚠️

**Ningún listado de este departamento emite `meta.acotado_a`.** Los ocho son de Administrador y
**globales**: no hay eje de titularidad que acotar, y el backend lo declara así a propósito —
`acotado_a` es opcional y aditivo, y los listados que no acotan no lo emiten.

Consecuencia: **la garantía más delicada de la capa compartida —el aviso de alcance, sobre todo en el
estado vacío— no se ejercita de punta a punta en este piloto.** Está cubierta por las pruebas de
componente de `shared/informes`, pero eso no es lo mismo que verla funcionando contra el backend.

**Se cierra con el siguiente departamento acotado** — Soporte (`propios`) o Emergencias
(`zonas_contratadas`). Queda anotado aquí para que nadie dé por validado lo que no lo está.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Consultar los ocho listados con la capa compartida (Priority: P1)

Como Administrador, quiero consultar cada uno de los ocho informes desde una pantalla, con sus
filtros y su paginación, para no tener que pedirle a nadie una consulta a la base.

**Why this priority**: es el entregable. Y es lo que prueba que declarar columnas y filtros basta
para tener una pantalla, que es la apuesta entera de la capa compartida.

**Independent Test**: abrir cada listado, filtrar, paginar y volver, sin que exista ninguna de las
otras historias.

**Acceptance Scenarios**:

1. **Given** un Administrador autenticado, **When** abre un listado, **Then** ve la tabla con **las
   columnas que el contrato de backend declara y ninguna más**.
2. **Given** un listado con más filas que el tamaño de página, **When** avanza y retrocede, **Then**
   no se repite ni se pierde ninguna fila.
3. **Given** un listado de estado actual, **When** se abre, **Then** la barra de filtros **no
   ofrece** selector de fechas.
4. **Given** el listado de transferencias, que es de hechos del período, **When** se abre, **Then**
   sí lo ofrece.
5. **Given** un filtro de enumeración, **When** se despliega, **Then** ofrece **solo** los valores
   que el backend admite.
6. **Given** cualquier listado, **When** se consulta, **Then** **no** aparece ningún recuento total
   ni número de página distinto del actual.

---

### US-FE-2 — Entender por qué una consulta no devolvió nada (Priority: P1)

Como Administrador, quiero distinguir «no hay registros», «tu filtro está mal» y «no tienes acceso»,
porque las tres se parecen en pantalla y solo una es culpa mía.

**Why this priority**: es la mitad del valor de la capa. Un backend que rechaza con `400` y una
pantalla que lo pinta como tabla vacía **desperdician exactamente el trabajo que costó** rechazar en
vez de recortar.

**Independent Test**: forzar cada caso y comprobar que la pantalla los distingue.

**Acceptance Scenarios**:

1. **Given** un filtro con un valor que el backend no admite, **When** se consulta, **Then** se
   muestra **el mensaje del backend**, que nombra los valores válidos — no un texto genérico.
2. **Given** ese mismo error, **When** se muestra, **Then** **no** se ofrece «Reintentar»: repetir lo
   mismo devuelve lo mismo.
3. **Given** un usuario sin el rol requerido, **When** entra al listado, **Then** ve una negativa,
   **no** una tabla vacía.
4. **Given** un fallo del servidor, **When** ocurre, **Then** sí se ofrece «Reintentar».
5. **Given** una consulta correcta sin resultados, **When** se muestra, **Then** el texto habla del
   dominio —«no hay solicitudes pendientes»— y **no** dice «sin datos».

---

### US-FE-3 — Leer un dato ausente como ausente (Priority: P2)

Como Administrador, quiero que un campo sin valor se vea vacío y no como un cero o una fecha de 1970,
porque tomo decisiones con estas cifras.

**Why this priority**: es la tercera garantía de la capa, y la que más silenciosamente se rompe.

**Acceptance Scenarios**:

1. **Given** una cuenta sin fecha de inicio de contrato, **When** aparece, **Then** la celda se ve
   ausente, **nunca** como una fecha de 1970.
2. **Given** una cuenta sin propietario resuelto, **When** aparece, **Then** la celda se ve ausente y
   **la fila no se omite**.
3. **Given** un valor numérico que **sí** es cero, **When** aparece, **Then** se muestra `0` — no se
   confunde con la ausencia.

---

### Edge Cases

- **Informe siempre vacío.** ⚠️ `transferencias-propiedad` **devolverá siempre cero filas** mientras
  la decisión **#28** siga abierta: `Fact_HistorialTransferenciaPropiedad` está declarada y **ningún
  código de producción la escribe**. En pantalla eso se lee como un informe roto. El estado vacío de
  ese listado **MUST** decir que la fuente aún no se alimenta, para que nadie pierda el tiempo
  buscando un defecto que no existe.
- **Sesión caducada.** El listado no inventa un manejo propio: se apoya en el que la aplicación ya
  tiene.
- **Pantalla estrecha.** La tabla se sustituye por tarjetas; ninguna columna declarada desaparece sin
  estar marcada como solo-escritorio.
- **Listado sin filtros propios** (`credenciales-temporales`, `accesos-tecnicos`): la barra de
  filtros no se pinta vacía.

---

## Requirements *(mandatory)*

### Funcionales

#### Las ocho pantallas

- **FR-F01**: El sistema MUST ofrecer una pantalla por cada uno de los ocho listados, bajo una ruta
  propia del departamento.
- **FR-F02**: Cada pantalla MUST declarar sus columnas y sus filtros y **MUST NOT** maquetar su
  propia tabla ni su propia paginación.
- **FR-F03**: Las columnas mostradas MUST coincidir **exactamente** con las que el contrato OpenAPI
  del backend declara para ese listado.
- **FR-F04**: Debe existir un índice del departamento desde el que se llegue a los ocho.

#### Filtros

- **FR-F05**: Los filtros de enumeración MUST ofrecer **solo** los valores válidos, tomados del
  contrato — no escritos a mano en la pantalla.
- **FR-F06**: El selector de rango de fechas MUST aparecer **únicamente** en los listados que el
  backend declara de hechos del período. Hoy, solo `transferencias-propiedad`.
- **FR-F07**: Un filtro sin valor **MUST NOT** viajar en la petición.
- **FR-F08**: Cambiar de filtros MUST volver a la primera página.

#### Errores y estados

- **FR-F09**: Un `400` MUST mostrarse con el `detail` del backend, y **MUST NOT** presentarse como
  resultado vacío.
- **FR-F10**: Un `403` MUST distinguirse de un resultado vacío.
- **FR-F11**: Solo los errores reintentables MUST ofrecer «Reintentar».
- **FR-F12**: El estado vacío de cada listado MUST hablar de su dominio.
- **FR-F13**: El estado vacío de `transferencias-propiedad` MUST advertir que la fuente aún no se
  alimenta *(mientras la decisión #28 siga abierta)*.

#### Paginación

- **FR-F14**: La navegación MUST ser siguiente/anterior. **MUST NOT** mostrarse recuento total ni
  navegación por número de página.
- **FR-F15**: Recorrer un listado hacia delante y hacia atrás **MUST NOT** repetir ni perder filas.

#### Acceso

- **FR-F16**: Las rutas MUST estar protegidas por los mismos roles que el permiso de backend declara:
  **Administrador** en siete, y **Administrador o Director Tecnológico** en `accesos-tecnicos`.
- **FR-F17**: El guard **MUST NOT** decidir qué filas se ven. Abre la puerta; el alcance lo decide el
  backend.

#### Presentación del dato

- **FR-F18**: Un valor ausente MUST mostrarse como ausente y **MUST NOT** rellenarse con cero, con
  una fecha de época ni con una cadena vacía.
- **FR-F19**: Las pantallas MUST mostrar nombres, no identificadores internos.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Los **ocho** listados se consultan desde la interfaz y devuelven las columnas
  declaradas.
- **SC-F02**: **Ninguna** de las ocho pantallas implementa su propia tabla, paginación o manejo de
  error: las ocho consumen la capa compartida.
- **SC-F03**: **El 100 %** de los `400` muestra el mensaje del backend; **cero** se presentan como
  tabla vacía.
- **SC-F04**: Un `403` es distinguible de un resultado vacío en **los ocho**.
- **SC-F05**: **Cero** celdas ausentes se muestran como `0` o como fecha de época.
- **SC-F06**: **En ninguna** pantalla aparece un recuento total ni un número de página navegable.
- **SC-F07**: Recorrer cualquier listado por páginas devuelve cada fila exactamente una vez.

---

## Assumptions

- **La capa compartida está construida y probada** (`shared/informes`, 42 pruebas). Esta spec la
  **consume**; si hiciera falta modificarla, es señal de que la generalización quedó incompleta y la
  corrección va allí.
- **El backend no se toca.** Los ocho endpoints están verdes; esta capa solo los consume.
- **Los roles son los que el permiso de backend declara**, no una lista nueva.
- **`acotado_a` no se ejercita aquí**, y está declarado arriba.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Exportación a CSV/Excel | Fuera de alcance en la spec de backend |
| Gráficas | Son de informes agregados, que tienen su propio camino |
| Guardar filtros del usuario | No hay backend que los persista |
| Recuento total de resultados | ⛔ Imposible con cursor opaco |
| Modificar la capa compartida | Si hace falta, la corrección va a `shared/informes`, no aquí |
| Poblar `Fact_HistorialTransferenciaPropiedad` | Es la decisión #28, y es de negocio |
