# Feature Specification: Informes Tácticos Simples de Soporte al Cliente (Frontend)

**Feature Branch / capa**: `002-tactico/Soporte-Cliente/informes-tacticos-simples/frontend`

**Created**: 2026-08-15

**Status**: Implemented

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato OpenAPI. Esta capa
**MUST NOT** redefinir reglas de negocio, filtros ni contratos REST.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

---

## Contexto

Dos listados, y **el motivo de hacerlo ahora**: es el primer departamento cuyo backend emite
`meta.acotado_a`. El piloto de Cuentas y Clientes validó todo lo demás pero **no pudo validar el
aviso de alcance**, porque sus ocho listados son globales.

Aquí sí. `tickets` devuelve `propios` a un reportador y `todos` a quien atiende, así que la garantía
más delicada de la capa compartida —que un resultado vacío no sea ambiguo— se ejercita de punta a
punta contra el backend real.

### El acotamiento se decide por lo que NO se tiene

Es la regla del departamento, y la pantalla **no la reimplementa**: la aplica el backend. Lo único
que la interfaz tiene que hacer es **mostrar el alcance que la respuesta declara**.

| Solicitante | Lo que el backend devuelve |
|---|---|
| Con algún rol de atención | `acotado_a: todos` |
| Sin ningún rol de atención (Cliente, Partner) | `acotado_a: propios` |
| Con roles de ambos tipos | `acotado_a: todos` |

⚠️ **El guard no decide qué filas se ven.** Abre la puerta a los dos grupos en `tickets`; el alcance
lo decide el backend. Un frontend que intentara adivinarlo duplicaría una regla que ya costó una
corrección en el módulo operativo.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Ver la cola de tickets sabiendo qué alcance tiene lo que veo (Priority: P1)

Como Agente de Soporte quiero ver la cola completa; como Cliente quiero ver los míos **y saber que
son solo los míos**.

**Why this priority**: es lo que este módulo viene a cerrar. Sin el aviso, un cliente que no ve
tickets incumplidos no puede distinguir «no hay» de «no hay **míos**».

**Acceptance Scenarios**:

1. **Given** un Agente de Soporte, **When** consulta los tickets, **Then** **no** aparece aviso de
   alcance: ve todo y un cartel permanente sería ruido.
2. **Given** un Cliente, **When** consulta los tickets, **Then** aparece el aviso de que solo ve sus
   registros.
3. **Given** un Cliente **sin tickets**, **When** consulta, **Then** el estado vacío dice que no hay
   resultados **entre los suyos** — no un «no hay tickets» a secas.
4. **Given** un Partner de integración, **When** consulta, **Then** obtiene el mismo trato que el
   Cliente: el acotamiento no depende de ser Cliente.
5. **Given** un filtro de estado, **When** se despliega, **Then** ofrece **solo** los siete estados
   que el backend admite.
6. **Given** un ticket sin agente asignado o sin factura, **When** aparece, **Then** esas celdas se
   ven ausentes y **la fila no se omite**.

---

### US-FE-2 — Revisar los escalados sin confundir el automático con el humano (Priority: P2)

Como Agente o Gerente de Éxito del Cliente quiero ver los escalados del período distinguiendo los que
decidió una persona de los que disparó el sistema.

**Acceptance Scenarios**:

1. **Given** un escalado automático, **When** aparece, **Then** su autor se ve **ausente** y su tipo
   dice `automatico` — no se atribuye a nadie.
2. **Given** un escalado manual, **When** aparece, **Then** muestra el nombre de quien lo decidió.
3. **Given** un reportador —Cliente o Partner—, **When** entra a este listado, **Then** el guard lo
   rechaza: el escalado es proceso interno del equipo de atención.
4. **Given** que es un listado de hechos del período, **When** se abre, **Then** la barra ofrece
   rango de fechas.

---

### Edge Cases

- **Cliente sin cuenta resuelta.** El backend responde `403`; la pantalla lo muestra como negativa,
  **no** como lista vacía.
- **Autor ausente en un escalado.** Es la respuesta correcta, no un dato que falte: se ve ausente y
  **no** se rellena con el destinatario.
- **`sin compromiso`.** Es un valor del filtro como cualquier otro, y el ticket que lo tiene es el
  que ningún vigilante revisa. No se oculta ni se agrupa con `en curso`.

---

## Requirements *(mandatory)*

- **FR-F01**: El sistema MUST ofrecer una pantalla por cada uno de los dos listados y un índice.
- **FR-F02**: Las pantallas MUST consumir la capa compartida y **MUST NOT** implementar tabla,
  paginación ni manejo de error propios.
- **FR-F03**: Las columnas MUST coincidir exactamente con el contrato OpenAPI del backend.
- **FR-F04**: ⚠️ El aviso de `acotado_a` MUST mostrarse cuando la respuesta lo declare distinto de
  `todos`, **y también en el estado vacío**.
- **FR-F05**: `acotado_a: todos` **MUST NOT** producir aviso.
- **FR-F06**: El filtro `estado` MUST ofrecer los siete estados del contrato; `situacion_compromiso`,
  los cinco; `tipo_escalado`, los dos.
- **FR-F07**: El rango de fechas MUST aparecer **solo** en `escalados`.
- **FR-F08**: El guard de `tickets` MUST admitir roles de atención **y** de reporte; el de
  `escalados`, **solo** de atención.
- **FR-F09**: El guard **MUST NOT** decidir qué filas se ven.
- **FR-F10**: Un valor ausente —agente, factura, autor— MUST verse ausente y la fila **MUST NOT**
  omitirse.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Los dos listados se consultan desde la interfaz con las columnas declaradas.
- **SC-F02**: Un Cliente ve el aviso de alcance; un Agente **no** lo ve. Verificable con ambos roles
  sobre los mismos datos.
- **SC-F03**: Un Cliente sin resultados ve un estado vacío que **menciona el acotamiento**.
- **SC-F04**: Un reportador recibe negativa en `escalados`, distinguible de una lista vacía.
- **SC-F05**: **Cero** escalados automáticos aparecen con un autor.
- **SC-F06**: Ninguna pantalla implementa tabla, paginación o manejo de error propio.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Reimplementar el acotamiento en la pantalla | Lo decide el backend; duplicarlo repetiría un defecto ya corregido |
| Exportación, gráficas, filtros guardados | Igual que en el resto de la serie |
| Modificar la capa compartida | Si hace falta, la corrección va a `shared/informes` |
